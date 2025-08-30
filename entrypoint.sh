#!/bin/bash
set -e

# Ожидание базы данных (если используется Postgres)
if [ -n "$DB_HOST" ]; then
  echo "Ожидание готовности базы данных..."
  for i in {1..30}; do
    nc -z $DB_HOST $DB_PORT && break
    echo "Ожидание... ($i)"
    sleep 1
  done
fi

# Применение миграций Alembic
alembic upgrade head

# Запуск бота
exec python main.py