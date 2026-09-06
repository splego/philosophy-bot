import json
import boto3
import urllib.request
import os
import random

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

    topics = [
        "動物",
        "宇宙",
        "歴史",
        "人体",
        "科学",
        "食べ物",
        "地理",
        "言語",
        "植物",
        "建築"
    ]

    topic = random.choice(topics)

    payload = {
        "model": "gpt-5.6",
        "input": f"""
        "古今東西の哲学者・思想家から一人を選び、その人物の思想を短く紹介してください。

        選ぶ人物について：
        - 有名・無名を問わず、できるだけ幅広い時代・地域・思想伝統から選ぶこと
        - 西洋近代哲学の著名人ばかりに偏らないこと
        - 古代、中世、近代、現代、西洋、東洋などを幅広く候補として考えること
        - 「代表的で説明しやすい人物」を優先するのではなく、候補を広く想定した上で一人を選ぶこと

        出力はLINEで気軽に読める長さにしてください。

        【哲学者】
        人物名（生没年・地域）

        【今日の思想】
        その人物の中心的な考えを、専門知識がなくても分かるように100〜150字程度で説明。

        【ひとこと】
        その思想について考えるための短い問いを一つ。
        """
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

        user_id = item["userId"]
        print("ゆーざあいでぃ", user_id)

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

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": message
        }, ensure_ascii=False)
    }