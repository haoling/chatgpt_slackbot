import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import openai

# Slackbotの応答を定義する
app = App(token=os.environ["SLACK_BOT_TOKEN"])
openai.api_key = os.environ["OPENAI_API_KEY"]

model_engine = "gpt-3.5-turbo"

def generate_response_chatGPT(user_input):
    system_message = """あなたの名前は「はおっこ」です。あなたは女の子です。あなたの肌は褐色です。あなたの髪はピンク色で、ボブカットです。あなたはギャル語を使います。あなたは優しいです。あなたは自分が頭が悪いことを知っています。"""
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ]
    )
    return response["choices"][0]["message"]["content"]

@app.event("app_mention")
def handle_app_mention_events(event, say):
    input_message = event["text"]
    input_message = input_message.replace("<@U04SMEAAB6Y> ", "")
    channel = event["channel"]
    thread_ts = event.get("thread_ts") or None

    print("prompt: " + input_message)

    if "bot_id" in event:
        return

    if thread_ts is not None:
        parent_thread_ts = event["thread_ts"]
        say(text=generate_response_chatGPT(input_message), thread_ts=parent_thread_ts, channel=channel)

    else:
        say(text=generate_response_chatGPT(input_message), channel=channel)


# Slackbotを開始する
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
