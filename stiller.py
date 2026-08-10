import os
import json
import asyncio
from datetime import datetime
from pyrogram import Client
from pyrogram.types import Message
import aiofiles

class Stiller:
    def __init__(self, data_path, settings):
        self.data_path = data_path
        self.settings = settings
        os.makedirs(data_path, exist_ok=True)

    async def collect_chat(self, client: Client, chat_id) -> dict:
        chat_dir = os.path.join(self.data_path, str(chat_id))
        os.makedirs(chat_dir, exist_ok=True)
        msg_count = 0
        media_count = 0
        messages_data = []

        async for message in client.get_chat_history(chat_id, limit=10000):
            msg_count += 1
            msg_dict = {
                "id": message.id,
                "date": str(message.date),
                "from": message.from_user.id if message.from_user else None,
                "text": message.text or message.caption or "",
                "media": None
            }
            if self.settings["save_media"] and message.media:
                media_type = str(message.media).split(".")[-1]
                if media_type in self.settings["media_types"]:
                    media_path = os.path.join(chat_dir, f"{message.id}_{media_type}.bin")
                    await client.download_media(message, file_name=media_path)
                    msg_dict["media"] = media_path
                    media_count += 1
            if self.settings["save_messages"]:
                messages_data.append(msg_dict)

        # сохраняем JSON с сообщениями
        json_path = os.path.join(chat_dir, "messages.json")
        async with aiofiles.open(json_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(messages_data, ensure_ascii=False, indent=2))

        return {"messages": msg_count, "media": media_count}

    def create_archive(self):
        import shutil
        archive_name = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.make_archive(archive_name, 'zip', self.data_path)
        return f"{archive_name}.zip"