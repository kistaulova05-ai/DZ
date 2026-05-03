#!/bin/bash

# Скрипт для развертывания приложения Task Tracker


echo "РАЗВЕРТЫВАНИЕ ПРИЛОЖЕНИЯ Task Tracker"

# 1. Проверка наличия Python
echo "1. Проверка Python..."
if command -v python3 &>/dev/null; then
    echo "  Python установлен: $(python3 --version)"
else
    echo "  Python не найден! Установите Python 3.8+"
    exit 1
fi

# 2. Установка Django
echo "2. Установка Django..."
pip install django --quiet
echo "  Django установлен"

# 3. Проверка наличия файла manage.py
echo "3. Проверка структуры проекта..."
if [ -f "manage.py" ]; then
    echo "  Проект Django найден"
else
    echo "  Файл manage.py не найден!"
    exit 1
fi

# 4. Выполнение миграций
echo "4. Выполнение миграций базы данных..."
python3 manage.py migrate --noinput
echo "   Миграции выполнены"

# 5. Запуск сервера
echo "5. Запуск сервера..."
echo "   Приложение доступно по адресу:"
echo "   http://0.0.0.0:8080"
python3 manage.py runserver 0.0.0.0:8080