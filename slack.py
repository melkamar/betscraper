import requests
import os
import logging


def send_message(text):
    try:
        webhook_url = os.environ['WEBHOOK_URL']
    except KeyError as err:
        logging.exception(err)
        return

    payload = {
        "text": text,
        "icon_emoji": ':ice_hockey_stick_and_puck:',
        "username": "Hokejbot"
    }

    logging.info(f'Sending slack message: {payload}')

    result = requests.post(webhook_url, json=payload)
    print(result)
