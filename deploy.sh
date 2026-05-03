#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
info() { echo -e "${YELLOW}>>>${NC} $1"; }

PORT=${PORT:-5000}

echo ""
echo "  WPS Attack Detector — Развёртывание"
echo "======================================"

info "Установка зависимостей..."
pip install --quiet django pandas numpy matplotlib
ok "Зависимости установлены"

info "Применение миграций..."
python manage.py migrate --no-input
ok "Миграции применены"

info "Проверка конфигурации..."
python manage.py check
ok "Конфигурация в порядке"

echo ""
echo -e "  Адрес: ${GREEN}http://0.0.0.0:${PORT}/${NC}"
echo "======================================"
echo ""

info "Запуск сервера на порту $PORT..."
exec python manage.py runserver "0.0.0.0:$PORT"
