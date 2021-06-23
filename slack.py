import requests

def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
                             headers={"Authorization": "Bearer " + token},
                             data={"channel": channel, "text": text}
                             )
    print(response)


myToken = "xoxb-1900700483344-2180727387815-Sx2FyOMPU7QQn5rpCVXsFlKc"
post_message(myToken, "#boksl", "안녕~")
