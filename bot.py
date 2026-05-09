import os
import requests
import random
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

seed = random.randint(1, 100000)

def generate_text():
    prompt = f"""
    哲学者をランダムに1人選んで紹介してください。
    シード値: {seed}

    条件：
    ・毎回違う人物にすること
    ・ソクラテスは禁止
    ・名前
    ・時代
    ・何を考えた人か
    ・現代への意味
    """

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return res.choices[0].message.content.strip()

def send_line(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": LINE_USER_ID,
        "messages": [
            {"type": "text", "text": text}
        ]
    }

    r = requests.post(url, headers=headers, json=body)
    print(r.status_code, r.text)

def main():
    text = generate_text()
    send_line(text)

if __name__ == "__main__":
    main()