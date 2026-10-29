#!/bin/bash
# Автоматическая регламентная очистка сервера FoodZuka (vezuroll.ru)
DATE=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$DATE] Запуск регламентной очистки сервера..." >> /var/log/foodzuka_cleanup.log

# 1. Очистка старых логов в БД (старше 30 дней)
docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db -c "DELETE FROM system_logs WHERE created_at < NOW() - INTERVAL '30 days' AND level IN ('INFO', 'WARNING'); DELETE FROM vk_webhook_logs WHERE created_at < NOW() - INTERVAL '30 days'; VACUUM ANALYZE system_logs; VACUUM ANALYZE vk_webhook_logs; VACUUM ANALYZE multichat_messages;" >> /var/log/foodzuka_cleanup.log 2>&1

# 2. Очистка Docker build cache и временных образов
docker builder prune -f --keep-storage 500MB >> /var/log/foodzuka_cleanup.log 2>&1
docker image prune -f >> /var/log/foodzuka_cleanup.log 2>&1

# 3. Очистка системных журналов ОС (journald)
journalctl --vacuum-size=100M >> /var/log/foodzuka_cleanup.log 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Регламентная очистка успешно завершена." >> /var/log/foodzuka_cleanup.log
