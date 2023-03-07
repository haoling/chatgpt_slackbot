import os, re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import openai

# Slackbotの応答を定義する
app = App(token=os.environ["SLACK_BOT_TOKEN"])
openai.api_key = os.environ["OPENAI_API_KEY"]

model_engine = "gpt-3.5-turbo"

bot_user_id = app.client.auth_test()['user_id']

def generate_response_chatGPT(user_input):
    messages = []
    messages.append({
        "role": "system",
        "content": os.environ["SYSTEM_MESSAGE"]
    })
    if isinstance(user_input, list):
        messages.extend(user_input)
    else:
        messages.append({
            "role": "user",
            "content": user_input
        })
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=messages
    )
    return response["choices"][0]["message"]["content"]

@app.event("app_mention")
def handle_app_mention_events(event, say):
    input_message = event["text"]
    input_message = input_message.replace("<@U04SMEAAB6Y> ", "")
    channel = event["channel"]
    thread_ts = event.get("thread_ts") or None
    user_name = app.client.users_info(user=event["user"])["user"]["profile"]["display_name"]

    print("prompt: " + input_message)

    if "bot_id" in event:
        return

    context = [
        {"role": "system", "content": "* Userの名前は " + user_name + " です。"},
        {"role": "user", "content": input_message}
    ]
    if thread_ts is not None:
        parent_thread_ts = event["thread_ts"]
        say(text=generate_response_chatGPT(context), thread_ts=parent_thread_ts, channel=channel)

    else:
        say(text=generate_response_chatGPT(context), thread_ts=event["ts"], channel=channel)

@app.message(re.compile("."))
def handle_message_events(event, say):
    input_message = event["text"]
    input_message = input_message.replace(f"<@{bot_user_id}> ", "")
    channel = event["channel"]
    channel_name = app.client.conversations_info(channel=channel)['channel']['name']
    thread_ts = event.get("thread_ts") or None
    user_name = app.client.users_info(user=event["user"])["user"]["profile"]["display_name"]

    print("prompt: " + input_message)

    if "bot_id" in event:
        return

    if thread_ts is None:
        if channel in (os.environ["RESIDENT_CHANNELS"] or "").split(',') or channel_name in (os.environ["RESIDENT_CHANNELS"] or "").split(','):
            context = [
                {"role": "system", "content": "* Userの名前は " + user_name + " です。"},
                {"role": "user", "content": input_message}
            ]
            say(text=generate_response_chatGPT(context), thread_ts=event["ts"], channel=channel)
        return

    # 親スレッドの情報を取得する
    conversation_history = app.client.conversations_history(
        channel=channel,
        latest=thread_ts,
        inclusive=True,
        limit=1,
    )

    # conversation_historyに親スレッドの情報が含まれます
    messages = conversation_history["messages"]
    if len(messages) == 0:
        # 親スレッドのメッセージが見つからなかった
        return

    parent_message = messages[0]
    # blockに自分宛てのメンションが含まれているかを確認する
    found = False
    for block in parent_message['blocks']:
        for element1 in block['elements']:
            for element2 in element1['elements']:
                if element2['type'] == 'user' and element2['user_id'] == bot_user_id:
                    found = True

    if not found:
        return

    # 最新から10件、履歴を取得する
    conversations_replies = app.client.conversations_replies(
        channel=channel,
        ts=thread_ts,
        latest=event['ts'],
        inclusive=True,
        limit=10,
    )

    # スレッドのリプライを、コンテキストに変換
    contexts = [
        {"role": "system", "content": "* Userの名前は " + user_name + " です。"}
    ]
    print("context:")
    for reply in conversations_replies["messages"]:
        context = {
            "role": "assistant" if reply['user'] == bot_user_id else "user",
            "content": reply['text'].replace(f"<@{bot_user_id}> ", "")
        }
        print("  " + context['role'] + ': ' + context['content'])
        contexts.append(context)

    say(text=generate_response_chatGPT(contexts), thread_ts=thread_ts, channel=channel)


# Slackbotを開始する
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
