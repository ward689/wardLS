import asyncio
import json
import os
import time
import logging
import sqlite3
import datetime
import requests
import platform
import psutil
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

# ======================== ТВОЙ ID ========================
MY_USER_ID = 7823802800  # Только этот ID получает ответы

# ======================== НАСТРОЙКА ЛОГИРОВАНИЯ ========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ======================== ОТКЛЮЧАЕМ ШУМНЫЕ ЛОГИ PYROGRAM ========================
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pyrogram.session.internals").setLevel(logging.ERROR)

# ======================== ЗАГРУЗКА КОНФИГА ========================
with open("config.json", "r") as f:
    config = json.load(f)

# ======================== СОЗДАНИЕ КЛИЕНТА ========================
app = Client(
    config["session_name"],
    api_id=config["api_id"],
    api_hash=config["api_hash"],
    workdir="./session"
)

# ======================== РАБОТА С БАЗОЙ ДАННЫХ ========================

def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            phone_number TEXT,
            added_date TEXT,
            notes TEXT,
            tags TEXT,
            warns INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_user_to_db(user_id, username, first_name, last_name, phone_number):
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, phone_number, added_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name, phone_number, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user_from_db_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

def get_user_from_db_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def update_user_notes(user_id, notes):
    conn = get_db_connection()
    conn.execute('UPDATE users SET notes = ? WHERE user_id = ?', (notes, user_id))
    conn.commit()
    conn.close()

def update_user_tags(user_id, tags):
    conn = get_db_connection()
    conn.execute('UPDATE users SET tags = ? WHERE user_id = ?', (tags, user_id))
    conn.commit()
    conn.close()

def search_users(query):
    conn = get_db_connection()
    users = conn.execute('''
        SELECT * FROM users 
        WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR notes LIKE ? OR tags LIKE ?
    ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    return users

def get_user_warns(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT warns FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return user['warns'] if user else 0

def update_user_warns(user_id, warns):
    conn = get_db_connection()
    conn.execute('UPDATE users SET warns = ? WHERE user_id = ?', (warns, user_id))
    conn.commit()
    conn.close()

def reset_user_warns(user_id):
    conn = get_db_connection()
    conn.execute('UPDATE users SET warns = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# Инициализация базы данных при старте
init_db()
logger.info("База данных инициализирована")

# ======================== ФИЛЬТР ДОСТУПА ========================
def me_only(func):
    async def wrapper(client, message):
        if message.from_user and message.from_user.id == MY_USER_ID:
            logger.info(f"Команда {message.text} от {message.from_user.id}")
            return await func(client, message)
        else:
            logger.warning(f"Неавторизованный доступ от {message.from_user.id if message.from_user else 'Unknown'}")
            return
    return wrapper

# ======================== ОТПРАВКА ТОЛЬКО В ЛИЧКУ ========================
async def send_to_me(client, text):
    try:
        await client.send_message(MY_USER_ID, text)
    except Exception as e:
        logger.error(f"Ошибка отправки в личку: {e}")

# ======================== ПРОВЕРКА АДМИН-ПРАВ (ОБНОВЛЁННАЯ) ========================
async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        logger.info(f"Статус пользователя {user_id} в чате {chat_id}: {member.status}")
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        logger.error(f"Ошибка проверки прав: {e}")
        return False

# ======================== КОМАНДЫ ========================

@app.on_message(filters.command("start") & filters.user(MY_USER_ID))
@me_only
async def start(client, message):
    await send_to_me(client,
        "✅ **Бот работает!**\n\n"
        "📋 **Доступные команды:**\n\n"
        "🔹 **Информация:**\n"
        "/status - Информация о профиле\n"
        "/id - ID чата и пользователя\n"
        "/info @username - Данные о пользователе (с БД)\n"
        "/search текст - Поиск в БД\n"
        "/system - Информация о системе\n\n"
        "🔹 **Управление чатами (Админ):**\n"
        "/kick @username - Кикнуть\n"
        "/ban @username - Забанить\n"
        "/unban @username - Разбанить\n"
        "/mute @username - Заглушить\n"
        "/unmute @username - Разглушить\n"
        "/warn @username - Предупреждение\n"
        "/warns @username - Кол-во предупреждений\n"
        "/reset_warns @username - Сбросить предупреждения\n"
        "/check_admin - Проверить свои права\n\n"
        "🔹 **Утилиты:**\n"
        "/join ссылка - Вступить в чат/канал\n"
        "/leave - Выйти из текущего чата\n"
        "/ping - Задержка бота\n"
        "/whois домен - IP и геолокация\n"
        "/download - Скачать медиа (ответом)\n"
        "/screenshot - Скриншот экрана\n"
        "/purge N - Удалить N сообщений (админ)"
    )

@app.on_message(filters.command("status") & filters.user(MY_USER_ID))
@me_only
async def status(client, message):
    me = await client.get_me()
    await send_to_me(client,
        f"👤 **Профиль:** {me.first_name} {me.last_name or ''}\n"
        f"🆔 **ID:** {me.id}\n"
        f"📛 **Юзернейм:** @{me.username or 'Нет'}\n"
        f"📱 **Номер:** {me.phone_number or 'Скрыт'}"
    )

@app.on_message(filters.command("id") & filters.user(MY_USER_ID))
@me_only
async def get_id(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    await send_to_me(client,
        f"🆔 **ID чата:** `{chat_id}`\n"
        f"👤 **ID пользователя:** `{user_id}`"
    )

@app.on_message(filters.command("check_admin") & filters.user(MY_USER_ID))
@me_only
async def check_admin(client, message):
    try:
        member = await client.get_chat_member(message.chat.id, MY_USER_ID)
        status = member.status
        rights = member.privileges
        
        text = f"👤 **Твой статус в этом чате:** `{status}`\n\n"
        
        if rights:
            text += "🔹 **Твои права:**\n"
            text += f"  - Удалять сообщения: `{rights.can_delete_messages}`\n"
            text += f"  - Кикать/банить: `{rights.can_restrict_members}`\n"
            text += f"  - Назначать админов: `{rights.can_promote_members}`\n"
            text += f"  - Менять инфо: `{rights.can_change_info}`\n"
            text += f"  - Приглашать: `{rights.can_invite_users}`\n"
            text += f"  - Пинать: `{rights.can_pin_messages}`\n"
        else:
            text += "⚠️ У тебя нет прав администратора в этом чате."
        
        await send_to_me(client, text)
        
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}\n\nВозможно, бот не имеет доступа к информации о чате.")

@app.on_message(filters.command("system") & filters.user(MY_USER_ID))
@me_only
async def system_info(client, message):
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime = time.time() - psutil.boot_time()
        days = int(uptime // 86400)
        hours = int((uptime % 86400) // 3600)
        minutes = int((uptime % 3600) // 60)
        
        text = (
            f"🖥️ **Информация о системе**\n\n"
            f"💻 **ОС:** {platform.system()} {platform.release()}\n"
            f"🧠 **CPU:** {cpu}%\n"
            f"📊 **RAM:** {ram.used // (1024**3)}GB / {ram.total // (1024**3)}GB ({ram.percent}%)\n"
            f"💾 **Диск:** {disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB ({disk.percent}%)\n"
            f"⏰ **Аптайм:** {days}д {hours}ч {minutes}м"
        )
        await send_to_me(client, text)
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("screenshot") & filters.user(MY_USER_ID))
@me_only
async def screenshot(client, message):
    try:
        await send_to_me(client, "📸 Делаю скриншот...")
        if platform.system() == "Windows":
            import pyautogui
            screenshot_path = "screenshot.png"
            pyautogui.screenshot(screenshot_path)
        else:
            screenshot_path = "screenshot.png"
            subprocess.run(["gnome-screenshot", "-f", screenshot_path])
        
        await client.send_document(MY_USER_ID, screenshot_path, caption="📸 Скриншот экрана")
        os.remove(screenshot_path)
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("info") & filters.user(MY_USER_ID))
@me_only
async def get_info_with_db(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи юзернейм, например: `/info @durov`")
        return

    username = message.command[1].replace('@', '')

    try:
        user = await client.get_users(username)
        add_user_to_db(
            user.id,
            user.username or username,
            user.first_name,
            user.last_name or '',
            user.phone_number or 'Скрыт'
        )
        db_user = get_user_from_db_by_username(user.username or username)
        
        response = (
            f"👤 **Информация о пользователе**\n\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"📛 **Юзернейм:** @{user.username or 'Нет'}\n"
            f"👤 **Имя:** {user.first_name}\n"
            f"👥 **Фамилия:** {user.last_name or 'Не указана'}\n"
            f"📱 **Номер:** {user.phone_number or 'Скрыт'}\n"
            f"📅 **Дата добавления в БД:** {db_user['added_date'] if db_user else 'Неизвестно'}\n"
        )
        if db_user and db_user['notes']:
            response += f"\n📝 **Заметки:** {db_user['notes']}\n"
        if db_user and db_user['tags']:
            response += f"🏷️ **Теги:** {db_user['tags']}\n"
        response += (
            f"\n💡 **Чтобы добавить заметку:**\n"
            f"`/addnote {user.username or username} Текст заметки`\n"
            f"💡 **Чтобы добавить тег:**\n"
            f"`/addtag {user.username or username} важный, друг, коллега`"
        )
        await send_to_me(client, response)
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("search") & filters.user(MY_USER_ID))
@me_only
async def search(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи текст для поиска: `/search текст`")
        return
    
    query = ' '.join(message.command[1:])
    results = search_users(query)
    
    if not results:
        await send_to_me(client, f"❌ По запросу `{query}` ничего не найдено")
        return
    
    text = f"🔍 **Результаты поиска по запросу:** `{query}`\n\n"
    for user in results:
        text += f"👤 {user['first_name']} {user['last_name'] or ''} (@{user['username'] or 'нет'})\n"
        if user['notes']:
            text += f"📝 {user['notes'][:50]}\n"
        if user['tags']:
            text += f"🏷️ {user['tags']}\n"
        text += f"🆔 `{user['user_id']}`\n\n"
    
    await send_to_me(client, text[:4000])

@app.on_message(filters.command("addnote") & filters.user(MY_USER_ID))
@me_only
async def add_note(client, message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await send_to_me(client, "❌ Пример: `/addnote @username Текст заметки`")
        return
    username = parts[1].replace('@', '')
    note_text = parts[2]
    try:
        user = await client.get_users(username)
        update_user_notes(user.id, note_text)
        await send_to_me(client, f"✅ Заметка для @{username} сохранена:\n`{note_text}`")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("addtag") & filters.user(MY_USER_ID))
@me_only
async def add_tag(client, message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await send_to_me(client, "❌ Пример: `/addtag @username важный, друг`")
        return
    username = parts[1].replace('@', '')
    tags = parts[2]
    try:
        user = await client.get_users(username)
        update_user_tags(user.id, tags)
        await send_to_me(client, f"✅ Теги для @{username} сохранены:\n`{tags}`")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

# ======================== УПРАВЛЕНИЕ ЧАТАМИ (АДМИН) ========================

@app.on_message(filters.command("kick") & filters.user(MY_USER_ID))
@me_only
async def kick_user(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи пользователя: `/kick @username`")
        return
    
    if message.chat.type == "private":
        await send_to_me(client, "❌ Эта команда работает только в группах/каналах")
        return
    
    if not await is_admin(client, message.chat.id, MY_USER_ID):
        await send_to_me(client, "❌ Ты не админ в этом чате")
        return
    
    try:
        user = await client.get_users(message.command[1])
        await client.ban_chat_member(message.chat.id, user.id)
        await client.unban_chat_member(message.chat.id, user.id)
        await send_to_me(client, f"✅ {user.first_name} кикнут")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("ban") & filters.user(MY_USER_ID))
@me_only
async def ban_user(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи пользователя: `/ban @username`")
        return
    
    if message.chat.type == "private":
        await send_to_me(client, "❌ Эта команда работает только в группах/каналах")
        return
    
    if not await is_admin(client, message.chat.id, MY_USER_ID):
        await send_to_me(client, "❌ Ты не админ в этом чате")
        return
    
    try:
        user = await client.get_users(message.command[1])
        await client.ban_chat_member(message.chat.id, user.id)
        await send_to_me(client, f"✅ {user.first_name} забанен")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("unban") & filters.user(MY_USER_ID))
@me_only
async def unban_user(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи пользователя: `/unban @username`")
        return
    
    if message.chat.type == "private":
        await send_to_me(client, "❌ Эта команда работает только в группах/каналах")
        return
    
    if not await is_admin(client, message.chat.id, MY_USER_ID):
        await send_to_me(client, "❌ Ты не админ в этом чате")
        return
    
    try:
        user = await client.get_users(message.command[1])
        await client.unban_chat_member(message.chat.id, user.id)
        await send_to_me(client, f"✅ {user.first_name} разбанен")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("mute") & filters.user(MY_USER_ID))
@me_only
async def mute_user(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи пользователя: `/mute @username`")
        return
    
    if message.chat.type == "private":
        await send_to_me(client, "❌ Эта команда работает только в группах/каналах")
        return
    
    if not await is_admin(client, message.chat.id, MY_USER_ID):
        await send_to_me(client, "❌ Ты не админ в этом чате")
        return
    
    try:
        user = await client.get_users(message.command[1])
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions={"can_send_messages": False}
        )
        await send_to_me(client, f"🔇 {user.first_name} заглушен")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("unmute") & filters.user(MY_USER_ID))
@me_only
async def unmute_user(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи пользователя: `/unmute @username`")
        return
    
    if message.chat.type == "private":
        await send_to_me(client, "❌ Эта команда работает только в группах/каналах")
        return
    
    if not await is_admin(client, message.chat.id, MY_USER_ID):
        await send_to_me(client, "❌ Ты не админ в этом чате")
        return
    
    try:
        user = await client.get_users(message.command[1])
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions={"can_send_messages": True}
        )
        await send_to_me(client, f"🔊 {user.first_name} разглушен")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("warn") & filters.user(MY_USER_ID))
@me_only
async def warn_user(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи пользователя: `/warn @username`")
        return
    
    if message.chat.type == "private":
        await send_to_me(client, "❌ Эта команда работает только в группах/каналах")
        return
    
    if not await is_admin(client, message.chat.id, MY_USER_ID):
        await send_to_me(client, "❌ Ты не админ в этом чате")
        return
    
    try:
        user = await client.get_users(message.command[1])
        warns = get_user_warns(user.id) + 1
        update_user_warns(user.id, warns)
        await send_to_me(client, f"⚠️ {user.first_name} получил предупреждение ({warns}/3)")
        
        if warns >= 3:
            await client.ban_chat_member(message.chat.id, user.id)
            reset_user_warns(user.id)
            await send_to_me(client, f"🚫 {user.first_name} забанен за 3 предупреждения")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("warns") & filters.user(MY_USER_ID))
@me_only
async def get_warns(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи пользователя: `/warns @username`")
        return
    
    try:
        user = await client.get_users(message.command[1])
        warns = get_user_warns(user.id)
        await send_to_me(client, f"⚠️ {user.first_name} имеет {warns} предупреждений")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("reset_warns") & filters.user(MY_USER_ID))
@me_only
async def reset_warns(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи пользователя: `/reset_warns @username`")
        return
    
    if message.chat.type == "private":
        await send_to_me(client, "❌ Эта команда работает только в группах/каналах")
        return
    
    if not await is_admin(client, message.chat.id, MY_USER_ID):
        await send_to_me(client, "❌ Ты не админ в этом чате")
        return
    
    try:
        user = await client.get_users(message.command[1])
        reset_user_warns(user.id)
        await send_to_me(client, f"✅ Предупреждения для {user.first_name} сброшены")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

# ======================== ОСТАЛЬНЫЕ КОМАНДЫ ========================

@app.on_message(filters.command("join") & filters.user(MY_USER_ID))
@me_only
async def join_chat(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи ссылку или юзернейм: `/join https://t.me/example`")
        return
    target = message.command[1]
    try:
        await client.join_chat(target)
        await send_to_me(client, f"✅ Вступил в {target}")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("leave") & filters.user(MY_USER_ID))
@me_only
async def leave_chat(client, message):
    chat_id = message.chat.id
    try:
        await client.leave_chat(chat_id)
        await send_to_me(client, "✅ Покинул чат")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("ping") & filters.user(MY_USER_ID))
@me_only
async def ping(client, message):
    start = time.time()
    await send_to_me(client, "🏓 Измеряю задержку...")
    end = time.time()
    await send_to_me(client, f"🏓 **Pong!** `{round((end - start) * 1000)}` мс")

@app.on_message(filters.command("whois") & filters.user(MY_USER_ID))
@me_only
async def whois(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи домен: `/whois example.com`")
        return
    domain = message.command[1]
    try:
        r = requests.get(f"http://ip-api.com/json/{domain}", timeout=10)
        data = r.json()
        if data.get("status") == "fail":
            await send_to_me(client, "❌ Не удалось определить IP")
            return
        text = (
            f"🌍 **IP:** {data['query']}\n"
            f"📍 **Страна:** {data['country']}\n"
            f"🏙 **Город:** {data['city']}\n"
            f"📡 **Провайдер:** {data['isp']}"
        )
        await send_to_me(client, text)
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("download") & filters.user(MY_USER_ID))
@me_only
async def download_file(client, message):
    if not message.reply_to_message or not message.reply_to_message.media:
        await send_to_me(client, "❌ Ответь на сообщение с медиа")
        return
    try:
        file_path = await client.download_media(message.reply_to_message)
        await send_to_me(client, f"✅ Файл сохранён: `{file_path}`")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

@app.on_message(filters.command("purge") & filters.user(MY_USER_ID))
@me_only
async def purge_messages(client, message):
    if len(message.command) < 2:
        await send_to_me(client, "❌ Укажи количество: `/purge 10`")
        return
    
    if message.chat.type == "private":
        await send_to_me(client, "❌ Эта команда работает только в группах/каналах")
        return
    
    if not await is_admin(client, message.chat.id, MY_USER_ID):
        await send_to_me(client, "❌ Ты не админ в этом чате")
        return
    
    try:
        count = int(message.command[1])
        if count > 100:
            await send_to_me(client, "⚠️ Не более 100 сообщений за раз")
            return
        deleted = 0
        async for msg in client.get_chat_history(message.chat.id, limit=count):
            try:
                await msg.delete()
                deleted += 1
            except:
                pass
        await send_to_me(client, f"✅ Удалено `{deleted}` сообщений")
    except Exception as e:
        await send_to_me(client, f"❌ Ошибка: {str(e)}")

# ======================== ЗАПУСК БОТА ========================

if __name__ == "__main__":
    logger.info("🚀 Бот запущен. Ожидание команд...")
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")