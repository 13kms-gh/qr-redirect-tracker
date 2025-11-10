import os
import sqlite3
import requests
from flask import Flask, redirect, request
from datetime import datetime, timezone

app = Flask(__name__)

# Переменные окружения Render
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
FINAL_URL = os.environ.get("FINAL_URL", "https://www.instagram.com/smartfood.marbella")

if not BOT_TOKEN or not CHAT_ID:
    print("ERROR: BOT_TOKEN or CHAT_ID not set. Messages will not be sent.")

# SQLite база для хранения переходов
DB_FILE = "tracker.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            user_agent TEXT,
            geo TEXT,
            ref TEXT,
            ts TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_geo(ip: str):
    """Определение города и страны по IP через бесплатный API ip-api.com"""
    try:
        resp = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city", timeout=5)
        data = resp.json()
        if data.get("status") == "success":
            return f"{data.get('city', 'unknown')}, {data.get('country', 'unknown')}"
    except Exception as e:
        print("Geo lookup error:", e)
    return "unknown"

def save_visit(ip, user_agent, geo, ref, ts):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO visits (ip, user_agent, geo, ref, ts) VALUES (?, ?, ?, ?, ?)",
              (ip, user_agent, geo, ref, ts))
    conn.commit()
    conn.close()

def count_visits_by_ip(ip):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM visits WHERE ip=?", (ip,))
    count = c.fetchone()[0]
    conn.close()
    return count

def send_telegram(text: str):
    """Отправка сообщения в Telegram с логированием"""
    if not BOT_TOKEN or not CHAT_ID:
        print("send_telegram skipped: BOT_TOKEN/CHAT_ID not configured")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": int(CHAT_ID), "text": text}, timeout=5)
        print("Telegram send status:", resp.status_code, resp.text)
    except Exception as e:
        print("Telegram send error:", e)

@app.route("/go")
def go():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "unknown")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    ref = request.args.get("ref", "qr")
    geo = get_geo(ip)

    save_visit(ip, user_agent, geo, ref, ts)
    visits_count = count_visits_by_ip(ip)

    text = (
        f"🔥 Переход!\n"
        f"Источник: {ref}\n"
        f"IP: {ip}\n"
        f"Локация: {geo}\n"
        f"UA: {user_agent}\n"
        f"Время: {ts}\n"
        f"Переходов с этого IP: {visits_count}"
    )

    send_telegram(text)
    return redirect(FINAL_URL, code=302)

@app.route("/")
def home():
    return "✅ Tracker работает"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
