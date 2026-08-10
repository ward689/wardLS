# Используем официальный образ с Python 3.11
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код
COPY . .

# Указываем Render порт, который будет слушать наш Flask-сервер
ENV PORT=8080

# Команда для запуска бота
CMD ["python", "server.py"]