import requests


def post_message(token, channel, text):
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer " + token},
        data={"channel": channel, "text": text},
    )
    print(response)


myToken = "xoxb-xxxxxx"
post_message(myToken, "#boksl-trade", "안녕~")
