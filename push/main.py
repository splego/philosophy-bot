import json
import boto3
import urllib.request
import urllib.parse
import os
import random

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("users")
philosophers_table = dynamodb.Table("philosophers")

s3 = boto3.client("s3")

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

def lambda_handler(event, context):

    response = philosophers_table.scan()
    published_items = response.get("Items", [])

    published_names = [
        item["name"] for item in published_items
    ]

    print("配信済:", published_names)

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
        - すでに選出済の人物：{published_names}の中からは選ばないでください。

        回答は次のJSON形式だけで回答すること。JSON以外の文章は出力禁止。

        {{
            "name": "人物名",
            "wikipedia_title": "日本語Wikipediaで検索するための一般的なページ名",
            "slug": "人物名を英字小文字とハイフンだけで表したURL用の名前",
            "birth_death": "生没年",
            "region": "地域",
            "summary": "中心的な思想を100〜150字程度で説明",
            "question": "その思想について考えるための短い問い"
        }}
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
    
    # 哲学者名をタイトルに
    result = json.loads(message)
    title = result["name"]
    wiki_title = result["wikipedia_title"]
    slug = result["slug"]
    birth_death = result["birth_death"]
    region = result["region"]
    summary = result["summary"]
    question = result["question"]

    file_key = f"philosophers/{slug}.html"
    detail_url = f"https://dk0brv3hfi7uc.cloudfront.net/{file_key}"

    # LINE配信文
    message = f"""【今日の哲学者】

    {title}
    {birth_death}｜{region}

    【今日の思想】
    {summary}

    【今日の問い】
    {question}

    ▼ もう少し詳しく
    {detail_url}
    """
    
    # Wikipedia記事取得
    params = urllib.parse.urlencode({
        "action": "query",
        "prop": "extracts",
        "explaintext": "1",
        "titles": wiki_title,
        "format": "json",
        "formatversion": "2"
    })

    url = "https://ja.wikipedia.org/w/api.php?" + params

    req = urllib.request.Request (
        url,
        headers = {
            "User-Agent": "PhilosopherLINEBot/1.0"
        }
    )

    with urllib.request.urlopen(req) as res:
        wiki_data = json.loads(res.read().decode("utf-8"))

    print("今回のtitle:", title)
    print("Wikipediaレスポンス:", wiki_data)
    article = wiki_data["query"]["pages"][0]["extract"]
    # print(article[:1000])

    # Wikipedia本文から詳細記事を生成
    url = "https://api.openai.com/v1/responses"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    payload = {
        "model": "gpt-5.6",
        "input": f"""
    以下はWikipediaから取得した「{title}」の記事です。

    この内容をもとに、哲学に詳しくない人でも読める
    「{title}とはどんな思想家なのか」を紹介する記事を書いてください。

    条件：
    - 日本語で書く
    - 1000〜1500字程度
    - 人物の生涯を簡潔に説明する
    - 中心的な思想をわかりやすく説明する
    - 専門用語を使う場合は意味も説明する
    - Wikipedia本文にない事実を勝手に追加しない
    - 元の文章をそのまま長く引用せず、自分の言葉で要約する
    - HTMLタグは使わない

    Wikipedia本文：
    {article}
    """
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    with urllib.request.urlopen(req) as res:
        detail_response = json.loads(res.read().decode("utf-8"))

    detail_article = ""

    for output in detail_response["output"]:
        if output["type"] == "message":
            for content in output["content"]:
                if content["type"] == "output_text":
                    detail_article = content["text"]
                    break

    # 記事生成
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
    </head>
    <body>
        <h1>{title}</h1>
        <pre>{detail_article}</pre>
    </body>
    </html>
    """
    s3.put_object(
        Bucket="philosopher-pages-2026",
        Key=file_key,
        Body=html.encode("utf-8"),
        ContentType="text/html; charset=utf-8"
    )

    # print("生成された詳細記事:")
    # print(detail_article)

    # 取得した哲学者をDBに登録
    philosophers_table.put_item (
        Item = {
            "name": title,
            "publishedAt": "2026-09-18",
            "articleUrl": detail_url
        }
    )

    response = table.scan()
    items = response.get("Items", [])

    # LINEへPUSH
    for item in items:

        user_id = items[0]["userId"]
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