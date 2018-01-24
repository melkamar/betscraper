import json
import time
import os
import logging

MODULE_PATH = os.path.dirname(__file__)
MATCH_REPORTS_FN = os.path.join(MODULE_PATH, 'persistent/match_reports.json')


def json_encode_status(match_report_status):
    return {
        'sent_56_mark': match_report_status.sent_56_mark,
        'sent_60_mark': match_report_status.sent_60_mark,
        'sent_overtime_pause_mark': match_report_status.sent_overtime_pause_mark,
        'last_updated': match_report_status.last_updated,
    }


class MatchReportStatus:
    def __init__(self, sent_56_mark=False, sent_60_mark=False, sent_overtime_pause_mark=False,
                 last_updated=time.time()):
        self._sent_56_mark = sent_56_mark
        self._sent_60_mark = sent_60_mark
        self._sent_overtime_pause_mark = sent_overtime_pause_mark
        self._last_updated = last_updated

    @property
    def sent_56_mark(self):
        return self._sent_56_mark

    @property
    def sent_60_mark(self):
        return self._sent_60_mark

    @property
    def sent_overtime_pause_mark(self):
        return self._sent_overtime_pause_mark

    @property
    def last_updated(self):
        return self._last_updated

    @sent_56_mark.setter
    def sent_56_mark(self, value):
        self._sent_56_mark = value
        self._last_updated = time.time()

    @sent_60_mark.setter
    def sent_60_mark(self, value):
        self._sent_60_mark = value
        self._last_updated = time.time()

    @sent_overtime_pause_mark.setter
    def sent_overtime_pause_mark(self, value):
        self._sent_overtime_pause_mark = value
        self._last_updated = time.time()

    @staticmethod
    def from_dict(dict_from_json):
        return MatchReportStatus(
            dict_from_json['sent_56_mark'],
            dict_from_json['sent_60_mark'],
            dict_from_json['sent_overtime_pause_mark'],
            dict_from_json['last_updated'],
        )


def _filter_old_match_reports(match_reports):
    return {
        match_id: match_report
        for match_id, match_report in match_reports.items()
        if time.time() - match_report.last_updated < 5 * 60 * 60  # Remove entries older than 5 hours
    }


def save_match_reports(match_reports):
    """
    Expect a dictionary:
    { match_id: MatchReportStatus, ...}
    """
    logging.info(f'Saving match reports to {MATCH_REPORTS_FN}')
    os.makedirs(os.path.dirname(MATCH_REPORTS_FN), exist_ok=True)
    match_reports = _filter_old_match_reports(match_reports)
    with open(MATCH_REPORTS_FN, 'w', encoding='utf-8') as f:
        json.dump(match_reports, f, ensure_ascii=False, indent=2, default=json_encode_status)


def load_match_reports():
    """
    Return a dictionary:
    { match_id: MatchReportStatus, ...}
    """
    logging.info(f'Loading match reports from {MATCH_REPORTS_FN}')

    if not os.path.exists(MATCH_REPORTS_FN):
        return {}

    with open(MATCH_REPORTS_FN, encoding='utf-8') as f:
        match_reports_dict = json.load(f)

    return {
        match_id: MatchReportStatus.from_dict(match_dict)
        for match_id, match_dict in match_reports_dict.items()
    }
