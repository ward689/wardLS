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

# ==================== ФИЛЬТР: ОТВЕЧАТЬ ДАЖЕ СЕБЕ ====================
def me_or_self(filter, client, message):
    """Разрешаем отвечать даже на свои сообщения"""
    return message.from_user and message.from_user.id == MY_USER_ID

# ==================== КОМАНДЫ (РАБОТАЮТ И С САМИМ СОБОЙ) ====================

@app_bot.on_message(filters.command("start") & filters.create(me_or_self))
async def start_command(client, message: Message):
    await message.reply_text(
        "✅ **Бот работает!**\n\n"
        "Команды:\n"
        "/status — профиль\n"
        "/ping — задержка\n"
        "/id — ID чата\n"
        "/echo текст — повторить"
    )

@app_bot.on_message(filters.command("status") & filters.create(me_or_self))
async def status_command(client, message: Message):
    me = await client.get_me()
    await message.reply_text(
        f"👤 **Профиль:** {me.first_name}\n"
        f"🆔 **ID:** {me.id}\n"
        f"📛 **Юзернейм:** @{me.username or 'Нет'}"
    )

@app_bot.on_message(filters.command("ping") & filters.create(me_or_self))
async def ping_command(client, message: Message):
    start_time = time.time()
    msg = await message.reply_text("🏓 Измеряю...")
    end_time = time.time()
    await msg.edit_text(f"🏓 **Pong!** `{round((end_time - start_time) * 1000)}` мс")

@app_bot.on_message(filters.command("id") & filters.create(me_or_self))
async def id_command(client, message: Message):
    await message.reply_text(
        f"🆔 **ID чата:** `{message.chat.id}`\n"
        f"👤 **ID пользователя:** `{message.from_user.id}`"
    )

@app_bot.on_message(filters.command("echo") & filters.create(me_or_self))
async def echo_command(client, message: Message):
    if len(message.text.split()) > 1:
        text = message.text.split(maxsplit=1)[1]
        await message.reply_text(f"🔊 {text}")
    else:
        await message.reply_text("❌ Напиши что-то после /echo")

@app_bot.on_message(filters.create(me_or_self))
async def fallback(client, message: Message):
    if not message.text.startswith("/"):
        await message.reply_text(f"📩 Ты написал: {message.text}")

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