# Dockerfile для aiogram-бота с поддержкой async SQLAlchemy
FROM python:3.12-slim

# Установка зависимостей системы
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копируем зависимости
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Переменные окружения (можно переопределить через docker-compose)
ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python", "main.py"]
