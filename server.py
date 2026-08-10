# server.py
import threading
import time
from flask import Flask, jsonify
from pyrogram import Client

# Твой основной код бота
app_bot = Client(...)  # твой клиент

# Flask для Keep-Alive
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return jsonify({"status": "Бот работает", "time": time.time()})

@app_web.route('/ping')
def ping():
    return "pong"

def run_bot():
    # тут твой app_bot.run() или запуск через asyncio
    app_bot.run()

def run_flask():
    app_web.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    # Запускаем Flask в фоновом потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # Запускаем бота (основной поток)
    run_bot()