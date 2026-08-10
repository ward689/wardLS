import os
import asyncio
import threading
import time
import logging
from flask import Flask, jsonify
from pyrogram import Client

# ==================== НАСТРОЙКА ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ====================
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("BAIVWl4Axm2K9id56nuMBu9wpovDnl_dW8TrmE6auNHoC2ONl2pEDtyht21nX0qL-4L1fC7dEVOhoeSpjgM1ZrB2dR6Ewi9vCNLLvRo_Rj07gEpVGupQVB7ttX_9GltXa3WxlWypU-xz-RvEQ_iWJjr8AXzpRRTyusEDRSb_8zhAwgCAbcluJ5LcSwJVIm_2WQZu4b5QIkR_zeAhGWdyFKlJn0fdzwPdascBuRXUtaPuaPm4Ot_WSWk-OZfvqhL_vexNBJfr6xef6G03tx2vijwHv_2EdThc0F36Ju8P8kJzYllWtlbH4MKu3Ftm36cYJ2ttAXF-Q-uCo_fho62iwMGEYpUm8gAAAAHSVcGwAA", "")  # <--- ГЛАВНОЕ
MY_USER_ID = int(os.getenv("MY_USER_ID", 0))

if not API_ID or not API_HASH:
    logger.error("❌ API_ID или API_HASH не заданы!")
    exit(1)


# ==================== КЛИЕНТ ЧЕРЕЗ СТРОКУ СЕССИИ ====================
app_bot = Client(
    name="session",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING  # <--- ВМЕСТО НОМЕРА
)

# ==================== FLASK ====================
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return jsonify({"status": "Бот работает", "time": time.time()})

@app_web.route('/ping')
def ping():
    return "pong"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# ==================== ЗАПУСК БОТА ====================
async def start_bot():
    try:
        async with app_bot:
            await app_bot.start()
            logger.info("✅ Бот успешно запущен!")
            
            if MY_USER_ID:
                try:
                    await app_bot.send_message(MY_USER_ID, "🚀 Бот запущен на Render!")
                except:
                    pass
            
            await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        raise

def run_bot():
    asyncio.run(start_bot())

if __name__ == "__main__":
    logger.info("🚀 Запуск сервера...")
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()