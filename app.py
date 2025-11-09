import requests
from flask import Flask, redirect, request
from datetime import datetime
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
FINAL_URL = os.environ.get("FINAL_URL", "https://www.instagram.com/smartfood.marbella")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": text})

@app.route("/go")
def go():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    ref = request.args.get("ref", "qr")

    text = f"🔥 Переход!\nИсточник: {ref}\nIP: {ip}\nВремя: {ts}"
    send_telegram(text)
    return redirect(FINAL_URL)

@app.route("/")
def home():
    return "✅ Tracker работает"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
