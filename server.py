import os
import asyncio
import threading
import time
from flask import Flask, jsonify
from pyrogram import Client

# ========== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ==========
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("SESSION_NAME", "my_session")
MY_USER_ID = int(os.getenv("MY_USER_ID", 0))

# ========== КЛИЕНТ ==========
app_bot = Client(
    name=SESSION_NAME,                     # <--- ИСПРАВЛЕНО
    api_id=API_ID,
    api_hash=API_HASH,
    workdir="./session"
)

# ========== FLASK ==========
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return jsonify({"status": "Бот работает", "time": time.time()})

@app_web.route('/ping')
def ping():
    return "pong"

def run_flask():
    app_web.run(host='0.0.0.0', port=int(os.getenv("PORT", 8080)))

# ========== ЗАПУСК БОТА ==========
async def start_bot():
    async with app_bot:
        await app_bot.start()
        print("✅ Бот запущен и готов к работе!")
        await asyncio.Event().wait()

def run_bot():
    asyncio.run(start_bot())

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    
    # Запускаем бота
    run_bot()