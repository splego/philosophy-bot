import json
import boto3
import urllib.request
import os

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("users")

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

def lambda_handler(event, context):
    response = table.scan()
    items = response.get("Items", [])

    # OpenAI API

    url = "https://api.openai.com/v1/responses"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    payload = {
        "model": "gpt-5.6",
        "input": "労いつつ、何か豆知識をランダムで一つ披露して。毎回必ず前回とは異なる内容にすること。"
    }

    req = urllib.request.Request(
        url,
        data = json.dumps(payload).encode("utf-8"),
        headers = headers,
        method = "POST"
    )

    with urllib.request.urlopen(req) as res:
        response_data = json.loads(res.read().decode("utf-8"))

    message = ""

    for output in response_data["output"]:
        if output["type"] == "message":
            for content in output["content"]:
                if content["type"] == "output_text":
                    message = content["text"]
                    break

    # LINEへPUSH

    for item in items:

        user_id = items[0]["userId"]

        url = "https://api.line.me/v2/bot/message/push"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
        }

        payload = {
            "to": user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req) as res:
            print("LINE STATUS:", res.status)
            print("OPENAI:", message)

    for item in items:
        user_id = item["userId"]
        print("ゆーざあいでぃ", user_id)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": message
        }, ensure_ascii=False)
    }