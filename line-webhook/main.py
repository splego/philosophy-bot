import json
import boto3
import uuid
import urllib.request

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("users")

def lambda_handler(event, context):

    body = json.loads(event["body"])
    events = body.get("events", [])

    for e in events:
        user_id = e["source"]["userId"]
        event_type = e["type"]

        table.put_item(Item={
        "userId": user_id
        })

        if "replyToken" in e:
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