import json
import boto3
import uuid
import urllib.request
import os 

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("users")

def lambda_handler(event, context):

    body = json.loads(event["body"])
    events = body.get("events", [])

    for e in events:
        event_type = e["type"]

        if event_type == "follow":
            user_id = e["source"]["userId"]

            # DBにID保存
            table.put_item(
                Item={
                    "userId": user_id
                }
            )

            # LINEに返信
            reply_token = e["replyToken"]
            reply_message(reply_token, "登録さんきゅ～！")


    return {
        "statusCode": 200,
        "body": "OK"
    }

def reply_message(reply_token, text):
    url = "https://api.line.me/v2/bot/message/reply"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }

    data = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    urllib.request.urlopen(req)