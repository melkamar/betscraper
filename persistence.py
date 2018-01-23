import json
import time
import os

MATCH_REPORTS_FN = 'persistent/match_reports.json'


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
        self.sent_56_mark = sent_56_mark
        self.sent_60_mark = sent_60_mark
        self.sent_overtime_pause_mark = sent_overtime_pause_mark
        self.last_updated = last_updated

    @staticmethod
    def from_dict(dict_from_json):
        return MatchReportStatus(
            dict_from_json['sent_56_mark'],
            dict_from_json['sent_60_mark'],
            dict_from_json['sent_overtime_pause_mark'],
            dict_from_json['last_updated'],
        )


def save_match_reports(match_reports):
    """
    Expect a dictionary:
    { match_id: MatchReportStatus, ...}
    """
    with open(MATCH_REPORTS_FN, 'w', encoding='utf-8') as f:
        json.dump(match_reports, f, ensure_ascii=False, indent=2, default=json_encode_status)


def load_match_reports():
    """
    Return a dictionary:
    { match_id: MatchReportStatus, ...}
    """
    if not os.path.exists(MATCH_REPORTS_FN):
        return {}

    with open(MATCH_REPORTS_FN, encoding='utf-8') as f:
        match_reports_dict = json.load(f)

    return {
        match_id: MatchReportStatus.from_dict(match_dict)
        for match_id, match_dict in match_reports_dict.items()
    }
