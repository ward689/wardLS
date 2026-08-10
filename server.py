import os
import asyncio
import time
import logging
from flask import Flask, jsonify
from pyrogram import Client, filters
from pyrogram.types import Message

# ==================== КОНФИГ ====================
API_ID = 34954014
API_HASH = "303e402252545f252f46402aabf154cc"
MY_USER_ID = 7823802800

# ==================== НАСТРОЙКА ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== КЛИЕНТ (БЕЗ СТРОКИ СЕССИИ) ====================
app = Client(
    "my_session",
    api_id=API_ID,
    api_hash=API_HASH
)

# ==================== КОМАНДЫ ====================
@app.on_message(filters.command("start") & filters.user(MY_USER_ID))
async def start_cmd(client, message: Message):
    await message.reply_text("✅ Бот работает!")

@app.on_message(filters.command("ping") & filters.user(MY_USER_ID))
async def ping_cmd(client, message: Message):
    start = time.time()
    msg = await message.reply_text("🏓...")
    end = time.time()
    await msg.edit_text(f"🏓 {round((end - start) * 1000)} мс")

# ==================== FLASK ====================
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({"status": "Бот работает", "time": time.time()})

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.getenv("PORT", 8080)))

# ==================== ЗАПУСК ====================
async def main():
    await app.start()
    logger.info("✅ Бот запущен!")
    await app.send_message(MY_USER_ID, "🚀 Бот запущен!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())