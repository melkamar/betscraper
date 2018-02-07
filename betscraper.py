import logging
import datetime
import os
import time
from typing import List
import persistence

from selenium import webdriver

import slack

NEWLINE = "\n"
ESCAPED_NEWLINE = "\\n"


class MatchResult:
    STATE_UNKNOWN = 1
    STATE_NOT_STARTED = 2
    STATE_LIVE = 3
    STATE_PERIOD_PAUSE = 4
    STATE_ENDED = 5

    PERIOD_OVERTIME = 4
    PERIOD_PENALTIES = 5

    def __init__(self, match_id):
        self.state = MatchResult.STATE_UNKNOWN
        self.minute = None
        self.period = None
        self.home_name = None
        self.home_score = None
        self.away_name = None
        self.away_score = None
        self.link = None
        self.third_period_filled_in = False
        self.id = match_id

    def _time_to_str(self):
        if self.state == MatchResult.STATE_UNKNOWN:
            return "???"
        elif self.state == MatchResult.STATE_NOT_STARTED:
            return "Nezačalo"
        elif self.state == MatchResult.STATE_LIVE:
            return f"{self.period}. třetina {self.minute}. minuta"
        elif self.state == MatchResult.STATE_PERIOD_PAUSE:
            return "Přestávka"
        elif self.state == MatchResult.STATE_ENDED:
            return "Konec"

    def __repr__(self):
        return f'({self._time_to_str()}) {self.home_name} ({self.home_score}-{self.away_score}) {self.away_name}'


def init_driver():
    try:
        driver_path = os.environ['PHANTOMJS_PATH']
    except KeyError:
        driver_path = "phantomjs"

    logging.debug(f'Using phantomjs at path "{driver_path}"')
    driver = webdriver.PhantomJS(driver_path)
    driver.get(r'https://www.livesport.cz/hokej/')
    return driver


def parse_element(score_elm, scores_dict):
    elm_id_full = score_elm.get_attribute('id')
    elm_type, elm_id = elm_id_full.split('_', 1)
    logging.debug(f'Found match {elm_id_full} of id {elm_id}')

    if elm_id not in scores_dict:
        scores_dict[elm_id] = MatchResult(elm_id)
        logging.debug(f'Creating new MatchResult under id {elm_id}')

    match_result = scores_dict[elm_id]
    if elm_type == 'g':
        logging.debug(f'Match is type "g"')
        timer_text = score_elm.find_element_by_css_selector(r'td.timer span').text
        logging.debug(f'timer_text: {timer_text.replace(NEWLINE, ESCAPED_NEWLINE)}')
        if timer_text == 'Přestávka':
            match_result.state = MatchResult.STATE_PERIOD_PAUSE
        elif timer_text.replace("\n", " ") in ["Konec", "Po prodloužení", "Po nájezdech"]:
            match_result.state = MatchResult.STATE_ENDED
        elif timer_text == "Nájezdy":
            match_result.state = MatchResult.STATE_LIVE
            match_result.period = MatchResult.PERIOD_OVERTIME
        elif timer_text.find("Prodloužení") != -1:
            lines = timer_text.split('\n')
            minute = int(lines[1].strip("'").strip())
            match_result.period = MatchResult.PERIOD_OVERTIME
            match_result.minute = minute
            match_result.state = MatchResult.STATE_LIVE
        else:  # Parse period and time
            lines = timer_text.split('\n')
            period = int(lines[0].split('.')[0].strip())
            minute = int(lines[1].strip("'").strip())
            match_result.period = period
            match_result.minute = minute
            match_result.state = MatchResult.STATE_LIVE

        home_name = score_elm.find_element_by_css_selector(r'td.team-home span').text
        home_score = int(score_elm.find_element_by_css_selector(r'td.score-home').text)
        match_result.home_name = home_name
        match_result.home_score = home_score
        match_result.third_period_filled_in = score_elm.find_element_by_css_selector('td.cell_sf').text.strip() != ''

        logging.debug(f'Setting properties on match: state {match_result.state} | period {match_result.period} | '
                      f'minute {match_result.minute} | home_name {match_result.home_name} | '
                      f'home_score {match_result.home_score}')
    elif elm_type == 'x':
        logging.debug(f'Match is type "x"')
        away_name = score_elm.find_element_by_css_selector(r'td.team-away span').text
        away_score = int(score_elm.find_element_by_css_selector(r'td.score-away').text)
        scores_dict[elm_id].away_name = away_name
        scores_dict[elm_id].away_score = away_score
        logging.debug(f'Setting properties on match: away_name {away_name} | away_score {away_score}')
    else:
        raise NotImplementedError


def parse_match_results(driver):
    match_rows_selector = r'tr.stage-live'
    score_elms = driver.find_elements_by_css_selector(match_rows_selector)
    logging.debug(f'Found {len(score_elms)} elements matching {match_rows_selector}')
    scores_dict = {}
    for score_elm in score_elms:
        try:
            parse_element(score_elm, scores_dict)
        except Exception as err:
            logging.exception(err)

    return scores_dict


def filter_almost_finished_draws(match_results: List[MatchResult], match_reports):
    """match_reports is a dict of {match_id: MatchReport}"""
    result = []
    for match_result in match_results:
        try:
            match_report = match_reports[match_result.id]
        except KeyError:
            match_report = persistence.MatchReportStatus()
            match_reports[match_result.id] = match_report

        logging.debug(f'Filtering match result {match_result}')
        if match_result.home_score != match_result.away_score:
            logging.debug(f'  > match scores do not match, discarding')
            continue

        if match_result.state == MatchResult.STATE_LIVE:
            if match_result.period == 3:
                if match_result.minute == 15:
                    if not match_report.sent_56_mark:
                        logging.debug('  > adding match, 55th minute mark')
                        result.append(match_result)
                        match_report.sent_56_mark = True
                    else:
                        logging.debug('  > discarding match, 55th minute mark already set')
                    continue

                if match_result.minute == 20:
                    if not match_report.sent_60_mark:
                        logging.debug('  > adding match, 60th minute mark')
                        result.append(match_result)
                        match_report.sent_60_mark = True
                    else:
                        logging.debug('  > discarding match, 60th minute mark already set')
                    continue

            if match_result.period == MatchResult.PERIOD_OVERTIME:
                if match_result.minute == 1:
                    if not match_report.sent_overtime_pause_mark:
                        logging.debug('  > adding match, pre-overtime')
                        result.append(match_result)
                        match_report.sent_overtime_pause_mark = True
                    else:
                        logging.debug('  > discarding match, pre-overtime mark already set')
                    continue

        if match_result.state == MatchResult.STATE_PERIOD_PAUSE and match_result.third_period_filled_in:
            if not match_report.sent_overtime_pause_mark:
                logging.debug('  > adding match, pre-overtime')
                result.append(match_result)
                match_report.sent_overtime_pause_mark = True
            else:
                logging.debug('  > discarding match, pre-overtime mark already set')
            continue

        if match_result.state == MatchResult.STATE_ENDED:
            if not match_report.sent_56_mark:
                logging.debug('  > adding match, test minute mark')
                result.append(match_result)
                match_report.sent_56_mark = True
            else:
                logging.debug('  > discarding match, test minute mark already set')
            continue

        logging.debug('  > no add-condition met, discarding')

    return result


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.WARNING)

    time_start = time.time()
    driver = init_driver()
    res = parse_match_results(driver)

    match_reports = persistence.load_match_reports()
    report_matches = filter_almost_finished_draws(list(res.values()), match_reports)

    persistence.save_match_reports(match_reports)

    if report_matches:
        logging.info('Sending message to Slack')
        newline = "\n"
        message = f'*Zápasy splňující podmínky:*\n\n' \
                  f'{newline.join(["  • "+str(report_match) for report_match in report_matches])}'
        slack.send_message(message)
    else:
        logging.info('Nothing to send')

    time_duration = time.time() - time_start
    logging.info(f'Took {time_duration:.2f} seconds')
    logging.info(f'All live matches: {res}')
    logging.info(f'Filtered matches: {report_matches}')


if __name__ == '__main__':
    main()
