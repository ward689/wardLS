import os
import asyncio
import threading
import time
import logging
from flask import Flask, jsonify
from pyrogram import Client

# ==================== НАСТРОЙКА ЛОГОВ ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== СОЗДАЁМ ПАПКУ ДЛЯ СЕССИИ ====================
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session")
os.makedirs(SESSION_DIR, exist_ok=True)
logger.info(f"📁 Папка для сессии: {SESSION_DIR}")

# ==================== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ====================
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("SESSION_NAME", "my_session")
MY_USER_ID = int(os.getenv("MY_USER_ID", 0))

if not API_ID or not API_HASH:
    logger.error("❌ API_ID или API_HASH не заданы в переменных окружения!")
    exit(1)

# ==================== КЛИЕНТ PYROGRAM ====================
app_bot = Client(
    name=SESSION_NAME,
    api_id=API_ID,
    api_hash=API_HASH,
    workdir=SESSION_DIR
)

# ==================== FLASK ДЛЯ KEEP-ALIVE ====================
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return jsonify({
        "status": "Бот работает",
        "time": time.time(),
        "session_dir": SESSION_DIR
    })

@app_web.route('/ping')
def ping():
    return "pong"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🌐 Запуск Flask на порту {port}")
    app_web.run(host='0.0.0.0', port=port)

# ==================== ЗАПУСК БОТА ====================
async def start_bot():
    try:
        async with app_bot:
            await app_bot.start()
            logger.info("✅ Бот успешно запущен и готов к работе!")
            
            # Отправляем приветствие в личку (если есть MY_USER_ID)
            if MY_USER_ID:
                try:
                    await app_bot.send_message(MY_USER_ID, "🚀 Бот запущен на Render!")
                except Exception as e:
                    logger.warning(f"Не удалось отправить приветствие: {e}")
            
            # Бесконечное ожидание
            await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        raise

def run_bot():
    asyncio.run(start_bot())

# ==================== ТОЧКА ВХОДА ====================
if __name__ == "__main__":
    logger.info("🚀 Запуск сервера...")
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем бота (основной поток)
    run_bot()