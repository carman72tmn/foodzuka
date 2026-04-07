#!/bin/bash
# Скрипт для создания сертификатов Let's Encrypt для 72roll.ru
# Запускайте этот скрипт на вашем сервере (VPS)

echo "⏳ Шаг 1: Проверка состояния Nginx..."
# Убеждаемся, что используется временная конфигурация без SSL
docker compose restart nginx

echo "📡 Шаг 2: Запрос сертификатов у Let's Encrypt..."
docker compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot/ --email admin@72roll.ru --agree-tos --no-eff-email -d 72roll.ru -d www.72roll.ru

if [ $? -eq 0 ]; then
    echo "✅ Сертификаты успешно выпущены!"
    echo "🔄 Шаг 3: Переключение на конфигурацию SSL..."
    cp configs/nginx/default.ssl.conf configs/nginx/default.conf
    docker compose restart nginx
    echo "🚀 Все системы запущены! Зайдите на https://72roll.ru/admin"
else
    echo "❌ Ошибка при выпуске сертификатов. Проверьте логи выше."
fi
