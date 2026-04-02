#!/bin/bash

# Скрипт очистки для сервера FoodTech
# Рекомендуется запускать через crontab:
# 0 4 * * * /root/foodzuka/scripts/cleanup.sh >> /root/foodzuka/logs/cleanup.log 2>&1

echo "--- Starting cleanup: $(date) ---"

# 1. Очистка Docker ресурсов
echo "Cleaning up Docker..."
docker system prune -f --volumes

# 2. Очистка старых логов (если они не в Docker)
# find /root/foodzuka/logs -name "*.log" -mtime +7 -delete

# 3. Проверка места на диске
echo "Disk usage after cleanup:"
df -h /

echo "--- Cleanup finished: $(date) ---"
