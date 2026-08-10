import os
import subprocess
import asyncio

class SoftManager:
    def __init__(self, softs_path):
        self.softs_path = softs_path
        os.makedirs(softs_path, exist_ok=True)

    def list_softs(self):
        files = os.listdir(self.softs_path)
        return [f for f in files if os.path.isfile(os.path.join(self.softs_path, f)) and not f.startswith(".")]

    async def run_soft(self, soft_name):
        soft_path = os.path.join(self.softs_path, soft_name)
        if not os.path.exists(soft_path):
            return f"❌ Софт '{soft_name}' не найден."
        try:
            if soft_name.endswith(".py"):
                process = await asyncio.create_subprocess_exec("python", soft_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif soft_name.endswith(".exe") or soft_name.endswith(".bat"):
                process = await asyncio.create_subprocess_exec(soft_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                return "⚠️ Неподдерживаемый тип файла. Используйте .py, .exe, .bat"
            stdout, stderr = await process.communicate()
            return stdout.decode() + stderr.decode()
        except Exception as e:
            return f"Ошибка запуска: {str(e)}"