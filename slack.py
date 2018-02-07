import requests
import os
import logging
import time


def send_message(text):
    try:
        webhook_url = os.environ['WEBHOOK_URL']
    except KeyError as err:
        logging.exception(err)
        return

    payload = {
        "icon_emoji": ":ice_hockey_stick_and_puck:",
        "username": "Hokejbot",
        "attachments": [
            {
                "fallback": "HELLO WORLD THERE\nTHIS IS PATRICK",
                "color": "#36a64f",
                "text": text,
                "ts": time.time()
            }
        ]
    }

    logging.info(f'Sending slack message: {payload}')

    result = requests.post(webhook_url, json=payload)
    print(result)
