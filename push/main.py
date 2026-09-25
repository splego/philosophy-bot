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
            "name_en": "英語Wikipediaで使われる一般的な英語表記",
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
    name_en = result["name_en"]
    wiki_title = result["wikipedia_title"]
    slug = result["slug"]
    birth_death = result["birth_death"]
    region = result["region"]
    summary = result["summary"]
    question = result["question"]

    file_key = f"philosophers/{slug}.html"
    detail_url = f"https://dk0brv3hfi7uc.cloudfront.net/{file_key}"

    # LINE配信文
    message = {
        "type": "flex",
        "altText": f"今日の哲学者：{title}",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": "DAILY PHILOSOPHY",
                        "size": "xs",
                        "color": "#888888"
                    },
                    {
                        "type": "text",
                        "text": title,
                        "weight": "bold",
                        "size": "xl",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": f"{birth_death}｜{region}",
                        "size": "sm",
                        "color": "#888888",
                        "wrap": True
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": "今日の思想",
                        "weight": "bold",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": summary,
                        "wrap": True,
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": "今日の問い",
                        "weight": "bold",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": question,
                        "wrap": True,
                        "size": "sm"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "uri",
                            "label": "もっと詳しく読む",
                            "uri": detail_url
                        }
                    }
                ]
            }
        }
    }
    
    # Wikipediaでまず人物名検索
    search_params = urllib.parse.urlencode({
        "action": "opensearch",
        "search": title,
        "limit": "10",
        "namespace": "0",
        "format": "json"
    })

    search_url = "https://ja.wikipedia.org/w/api.php?" + search_params

    search_req = urllib.request.Request (
        search_url,
        headers = {
            "User-Agent": "PhilosopherLINEBot/1.0"
        }
    )

    with urllib.request.urlopen(search_req) as res:
        search_data = json.loads(res.read().decode("utf-8"))

    print("Wikipedia検索結果:", search_data)

    if search_data[1]:
        wiki_title = search_data[1][0]
        wiki_lang = "ja"
    else:
        print("日本語のWikipedia記事が見つからないため英語版を検索:", name_en)

        # 英語版Wikipediaで再検索
        en_search_params = urllib.parse.urlencode({
            "action": "opensearch",
            "search": name_en,
            "limit": "10",
            "namespace": "0",
            "format": "json"
        })

        en_search_url = (
            "https://en.wikipedia.org/w/api.php?"
            + en_search_params
        )

        en_search_req = urllib.request.Request(
            en_search_url,
            headers={"User-Agent": "PhilosopherLINEBot/1.0"}
        )
        
        with urllib.request.urlopen(en_search_req) as res:
            en_search_data = json.loads(res.read().decode("utf-8"))

        print("英語版検索結果:", en_search_data)

        if not en_search_data[1]:
            print("英語版でも見つかりませんでした:", name_en)
            return {
                "statusCode": 200,
                "body": "Wikipedia記事が見つかりませんでした"
            }

        wiki_title = en_search_data[1][0]
        wiki_lang = "en"

    print("Wikipedia確定タイトル:", wiki_title)
    print("検索元の言語:", wiki_lang)

    # 他言語のWikipdeiaページ名を取得
    lang_params = urllib.parse.urlencode({
        "action": "query",
        "prop": "langlinks",
        "titles": wiki_title,
        "lllimit": "max",
        "format": "json",
        "formatversion": "2"
    })

    lang_url = f"https://{wiki_lang}.wikipedia.org/w/api.php?" + lang_params

    lang_req = urllib.request.Request (
        lang_url,
        headers = {
            "User-Agent": "PhilosopherLINEBot/1.0"
        }
    )

    with urllib.request.urlopen(lang_req, timeout = 10) as res:
        lang_data = json.loads(res.read().decode("utf-8"))

    print("他言語版:", lang_data)

    langlinks = lang_data["query"]["pages"][0].get("langlinks", [])

    if wiki_lang == "en":
        en_title = wiki_title
    else:
        en_title = None

        for link in langlinks:
            if link["lang"] == "en":
                en_title = link["title"]
                break

    # 英語版Wikipediaの本文を取得
    en_article = ""
    print("英語版取得タイトル:", en_title)

    if en_title is not None:
        en_params = urllib.parse.urlencode({
            "action": "query",
            "prop": "extracts",
            "explaintext": "1",
            "titles": en_title,
            "format": "json",
            "formatversion": "2"
        })

        en_url = "https://en.wikipedia.org/w/api.php?" + en_params

        en_req = urllib.request.Request(
            en_url,
            headers={"User-Agent": "PhilosopherLINEBot/1.0"}
        )

        with urllib.request.urlopen(en_req) as res:
            en_data = json.loads(res.read().decode("utf-8"))

        en_article = en_data["query"]["pages"][0].get("extract", "")

    print("英語版Wikipedia本文:", en_article[:1000])

    # 今までのWikipedia本文取得
    params = urllib.parse.urlencode({
        "action": "query",
        "prop": "extracts",
        "explaintext": "1",
        "titles": wiki_title,
        "format": "json",
        "formatversion": "2"
    })

    url = f"https://{wiki_lang}.wikipedia.org/w/api.php?" + params
    req = urllib.request.Request (
        url,
        headers = {
            "User-Agent": "PhilosopherLINEBot/1.0"
        }
    )

    with urllib.request.urlopen(req) as res:
        wiki_data = json.loads(res.read().decode("utf-8"))

    article = wiki_data["query"]["pages"][0]["extract"]

    # 画像検索
    image_params = urllib.parse.urlencode({
    "action": "query",
    "prop": "pageimages",
    "titles": wiki_title,
    "pithumbsize": 600,
    "format": "json",
    "formatversion": "2"
    })

    image_url = (
        f"https://{wiki_lang}.wikipedia.org/w/api.php?"
        + image_params
    )

    req = urllib.request.Request(
        image_url,
        headers={"User-Agent": "PhilosopherLINEBot/1.0"}
    )

    with urllib.request.urlopen(req) as res:
        image_data = json.loads(res.read().decode("utf-8"))

    image = (
        image_data["query"]["pages"][0]
        .get("thumbnail", {})
        .get("source")
    )

    print("画像URL:", image)




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

    以下のJSON形式だけで返してください。

    {{
    "intro": "この人物がどんな思想家なのかを簡潔に紹介",
    "life": "生涯と時代背景",
    "thought": "中心的な思想をわかりやすく説明",
    "influence": "後世への影響や思想史上の位置づけ",
    "related": [
        {{
        "name": "関連する思想家の名前",
        "relation": "この人物との関係を簡潔に説明"
        }}
    ]
    }}

    条件：
    【文章の目的】
    哲学に詳しくない読者が、人物の人生や思想に
    興味を持てる教養記事を書く。

    【文体】
    - 上質な教養雑誌の特集記事を思わせる、落ち着いた文体にする。
    - 単なる事実の羅列ではなく、背景、出来事、思想のつながりを描く。
    - 「〜した。〜した。〜した。」のような単調な文末の連続を避ける。
    - 「〜である」「〜だった」「〜と考えた」などを自然に使い分ける。
    - 短い文章と長い文章を組み合わせ、読み心地に緩急をつける。
    - 段落ごとに話題を展開し、文章全体に流れをつくる。
    - 必要に応じて読者への問いかけを交えてもよい。

    【構成】
    - intro：人物の思想的特徴や興味深い問題意識から始める。
    - life：年表的な説明ではなく、時代背景と人生の関係を描く。
    - thought：思想がどのような問題意識から生まれたのかを説明する。
    - influence：その思想が後世にどのように受け継がれたかを描く。

    【重要】
    - 情緒的な文章にするために、架空の逸話や心理描写を創作しない。
    - 人物の感情や動機を、資料に根拠なく断定しない。
    - Wikipedia本文にない歴史的事実を追加しない。
    - 元の文章を長く引用せず、自分の言葉で表現する。
    - 日本語で1000〜1500字程度。
    - HTMLタグは使わない。
    - 指定されたJSON形式だけで回答する。
    - 原文が日本語以外の場合も、内容を理解して自然な日本語の記事を作成すること。
    - Wikipedia本文と英語版Wikipedia本文が同じ場合は、同一資料として扱うこと。
    - Wikipediaなどの資料を参照していることを読者に意識させない。
    - 「本文によると」「資料では」「Wikipediaには」「提供された情報からは」などのメタ的な表現を使わない。

    Wikipedia本文(取得言語：{wiki_lang}):{article}
    英語版Wikipedia本文（参考資料）：{en_article}
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

    detail = json.loads(detail_article)

    intro = detail["intro"]
    life = detail["life"]
    thought = detail["thought"]
    influence = detail["influence"]
    related = detail["related"]

    # 記事生成

    related_html = ""

    for person in related:
        related_html += f"""
        <div class="related-person">
        <h3>{person["name"]}</h3>
        <p>{person["relation"]}</p>
        </div>
        """

    portrait_html = (
        f'<img src="{image}" class="portrait" alt="{title}の肖像">'
    if image else ""
    )

    html = f"""

    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <link rel="stylesheet" href="/philosophers/assets/style.css">
    </head>
    <body>

        <header>
            <p>DAILY PHILOSOPHER</p>
            <div class="profile-header">
                <div class="profile-info">
                    <h1>{title}</h1>
                    <p>{birth_death}｜{region}</p>
                </div>

            {portrait_html}

            </div>
        </header>

        <main>

            <section>
                <h2>{title}とは</h2>
                <p>{intro}</p>
            </section>

            <section>
                <h2>生涯と時代</h2>
                <p>{life}</p>
            </section>

            <section>
                <h2>思想</h2>
                <p>{thought}</p>
            </section>

            <section>
                <h2>後世への影響</h2>
                <p>{influence}</p>
            </section>

            <section>
                <h2>関連する思想家</h2>
                {related_html}
            </section>

        </main>

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
            "messages": [message]
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