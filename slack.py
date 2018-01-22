import requests


def send_message(text):
    webhook_url = r'https://hooks.slack.com/services/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'

    payload = {
        "text": text,
        "icon_emoji": ':ice_hockey_stick_and_puck:',
        "username": "Hokejbot"
    }

    result = requests.post(webhook_url, json=payload)
    print(result)
