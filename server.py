import os
import asyncio
import threading
import time
import logging
from flask import Flask, jsonify
from pyrogram import Client, filters
from pyrogram.types import Message

# ==================== НАСТРОЙКА ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== ПЕРЕМЕННЫЕ (ЗАХАРДКОЖЕНЫ) ====================
API_ID = 1234567  # ВСТАВЬ СВОЙ
API_HASH = "твой_хэш"  # ВСТАВЬ СВОЙ
SESSION_STRING = "BAIVWl4Axm2K9id56nuMBu9wpovDnl_dW8TrmE6auNHoC2ONl2pEDtyht21nX0qL-4L1fC7dEVOhoeSpjgM1ZrB2dR6Ewi9vCNLLvRo_Rj07gEpVGupQVB7ttX_9GltXa3WxlWypU-xz-RvEQ_iWJjr8AXzpRRTyusEDRSb_8zhAwgCAbcluJ5LcSwJVIm_2WQZu4b5QIkR_zeAhGWdyFKlJn0fdzwPdascBuRXUtaPuaPm4Ot_WSWk-OZfvqhL_vexNBJfr6xef6G03tx2vijwHv_2EdThc0F36Ju8P8kJzYllWtlbH4MKu3Ftm36cYJ2ttAXF-Q-uCo_fho62iwMGEYpUm8gAAAAHSVcGwAA"
MY_USER_ID = 7823802800

# ==================== КЛИЕНТ ====================
app_bot = Client(
    name="session",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# ==================== КОМАНДЫ БОТА ====================

@app_bot.on_message(filters.command("start") & filters.user(MY_USER_ID))
async def start_command(client, message: Message):
    await message.reply_text("✅ Бот работает! Команды:\n/status - проверить\n/ping - задержка")

@app_bot.on_message(filters.command("status") & filters.user(MY_USER_ID))
async def status_command(client, message: Message):
    me = await client.get_me()
    await message.reply_text(f"👤 {me.first_name}\n🆔 {me.id}\n📛 @{me.username or 'Нет'}")

@app_bot.on_message(filters.command("ping") & filters.user(MY_USER_ID))
async def ping_command(client, message: Message):
    start = time.time()
    msg = await message.reply_text("🏓 Измеряю...")
    end = time.time()
    await msg.edit_text(f"🏓 Pong! {round((end - start) * 1000)} мс")

@app_bot.on_message(filters.command("id") & filters.user(MY_USER_ID))
async def id_command(client, message: Message):
    await message.reply_text(f"🆔 ID чата: {message.chat.id}\n👤 ID пользователя: {message.from_user.id}")

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
        logger.info("🔄 Подключение к Telegram...")
        await app_bot.start()
        logger.info("✅ Бот успешно запущен на Render!")
        
        if MY_USER_ID:
            try:
                await app_bot.send_message(MY_USER_ID, "🚀 Бот запущен!")
            except:
                pass
        
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")

def run_bot():
    asyncio.run(start_bot())

if __name__ == "__main__":
    logger.info("🚀 Запуск сервера...")
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(2)
    run_bot()