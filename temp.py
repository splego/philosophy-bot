from flask import Flask, request

app = Flask(__name__)

@app.route("/callback", methods=["POST"])
def callback():
    data = request.json
    print(data)  # ←ここにuserId出る
    return "OK"

app.run(port=5000)