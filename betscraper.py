import time
from typing import List
import logging

from selenium import webdriver

import slack


class MatchResult:
    STATE_UNKNOWN = 1
    STATE_NOT_STARTED = 2
    STATE_LIVE = 3
    STATE_PERIOD_PAUSE = 4
    STATE_ENDED = 5

    PERIOD_OVERTIME = 4
    PERIOD_PENALTIES = 5

    def __init__(self):
        self.state = MatchResult.STATE_UNKNOWN
        self.minute = None
        self.period = None
        self.home_name = None
        self.home_score = None
        self.away_name = None
        self.away_score = None
        self.link = None

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
    import os
    try:
        driver_path = os.environ['PHANTOMJS_PATH']
    except KeyError:
        driver_path = "phantomjs"

    logging.debug(f'Using phantomjs at path "{driver_path}"')
    driver = webdriver.PhantomJS(driver_path)
    driver.get(r'https://www.livesport.cz/hokej/')
    return driver


def parse_match_results(driver):
    score_elms = driver.find_elements_by_css_selector('tr.stage-live')
    scores_dict = {}
    for score_elm in score_elms:
        elm_id = score_elm.get_attribute('id')
        elm_type, elm_id = elm_id.split('_', 1)
        if elm_id not in scores_dict:
            scores_dict[elm_id] = MatchResult()

        match_result = scores_dict[elm_id]
        if elm_type == 'g':
            timer_text = score_elm.find_element_by_css_selector(r'td.timer span').text
            if timer_text == 'Přestávka':
                match_result.state = MatchResult.STATE_PERIOD_PAUSE
            elif timer_text.replace("\n", " ") in ["Konec", "Po prodloužení", "Po nájezdech"]:
                match_result.state = MatchResult.STATE_ENDED
            elif timer_text == "TODO":  # TODO
                match_result.state = MatchResult.STATE_NOT_STARTED
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
        elif elm_type == 'x':
            away_name = score_elm.find_element_by_css_selector(r'td.team-away span').text
            away_score = int(score_elm.find_element_by_css_selector(r'td.score-away').text)
            scores_dict[elm_id].away_name = away_name
            scores_dict[elm_id].away_score = away_score
        else:
            raise NotImplementedError

    return scores_dict


def filter_almost_finished_draws(match_results: List[MatchResult]):
    result = []
    for match_result in match_results:
        if not match_result.state == MatchResult.STATE_LIVE:
            continue

        if not match_result.period in [3, MatchResult.PERIOD_OVERTIME]:
            continue

        if match_result.minute < 19:
            continue

        # TODO check jestli je remíza

        result.append(match_result)

    return result


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.WARNING)

    time_start = time.time()
    driver = init_driver()
    res = parse_match_results(driver)
    report_matches = filter_almost_finished_draws(list(res.values()))

    if report_matches:
        newline = "\n"
        message = f'*Zápasy splňující podmínky:*\n\n' \
                  f'{newline.join(["  • "+str(report_match) for report_match in report_matches])}'
        slack.send_message(message)

    time_duration = time.time() - time_start
    logging.info(f'Took {time_duration:.2f} seconds')
    logging.info(res)


if __name__ == '__main__':
    main()
