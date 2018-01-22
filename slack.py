import requests


def send_message(text, webhook_url):
    payload = {
        "text": text,
        "icon_emoji": ':ice_hockey_stick_and_puck:',
        "username": "Hokejbot"
    }

    result = requests.post(webhook_url, json=payload)
    print(result)
