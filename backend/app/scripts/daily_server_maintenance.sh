#!/bin/bash
# ==============================================================================
# Ежедневное автоматическое техническое обслуживание сервера FoodZuka (04:00)
# Хост: vezuroll.ru (VPS 178.212.13.48)
# Безопасная очистка кэшей, оптимизация PostgreSQL, сжатие логов без простоя админки
# ==============================================================================

LOG_FILE="/var/log/foodzuka_daily_maintenance.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')
DAY_OF_WEEK=$(date +%u) # 1 = Понедельник, 7 = Воскресенье

echo "=========================================================" >> "$LOG_FILE"
echo "[$DATE] Запуск ежедневного обслуживания сервера..." >> "$LOG_FILE"

# 1. Очистка устаревших логов из базы данных PostgreSQL
echo "[$DATE] Очистка логов БД старше 14 дней..." >> "$LOG_FILE"
docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db << 'EOSQL' >> "$LOG_FILE" 2>&1
-- Удаление рутинных логов старше 14 дней
DELETE FROM system_logs 
WHERE created_at < NOW() - INTERVAL '14 days' 
  AND level IN ('INFO', 'WARNING');

-- Удаление рутинных записей Celery INFO старше 3 дней
DELETE FROM system_logs 
WHERE module LIKE 'Celery:%' 
  AND level = 'INFO' 
  AND created_at < NOW() - INTERVAL '3 days';

-- Удаление webhook логов старше 14 дней
DELETE FROM vk_webhook_logs 
WHERE created_at < NOW() - INTERVAL '14 days';

-- Удаление временных логов ботов старше 30 дней
DELETE FROM vk_bot_message_logs 
WHERE created_at < NOW() - INTERVAL '30 days';
EOSQL

# 2. Оптимизация и сжатие PostgreSQL
# По воскресеньям (DAY_OF_WEEK=7) в 04:00 делаем глубокий VACUUM FULL multichat_messages
# В остальные дни — быстрый VACUUM ANALYZE (занимает 1-2 секунды, 0 простоя)
if [ "$DAY_OF_WEEK" -eq 7 ]; then
    echo "[$DATE] Воскресенье: выполнение глубокого сжатия VACUUM FULL multichat_messages..." >> "$LOG_FILE"
    docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db -c "VACUUM FULL multichat_messages;" >> "$LOG_FILE" 2>&1
    docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db -c "VACUUM FULL system_logs;" >> "$LOG_FILE" 2>&1
    docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db -c "REINDEX TABLE multichat_messages;" >> "$LOG_FILE" 2>&1
else
    echo "[$DATE] Будний день: выполнение регламентного VACUUM ANALYZE..." >> "$LOG_FILE"
    docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db -c "VACUUM ANALYZE multichat_messages;" >> "$LOG_FILE" 2>&1
    docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db -c "VACUUM ANALYZE system_logs;" >> "$LOG_FILE" 2>&1
    docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db -c "VACUUM ANALYZE vk_webhook_logs;" >> "$LOG_FILE" 2>&1
    docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db -c "VACUUM ANALYZE orders;" >> "$LOG_FILE" 2>&1
    docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db -c "VACUUM ANALYZE customers;" >> "$LOG_FILE" 2>&1
fi

# Сброс буферов WAL
docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db -c "CHECKPOINT;" >> "$LOG_FILE" 2>&1

# 3. Очистка кэшей сборки Docker и dangling-образов
echo "[$DATE] Очистка Docker build cache и неиспользуемых слоев..." >> "$LOG_FILE"
docker builder prune -f --reserved-space 200MB >> "$LOG_FILE" 2>&1
docker image prune -f >> "$LOG_FILE" 2>&1

# 4. Усечение логов Docker контейнеров (если превышают 15 МБ)
echo "[$DATE] Проверка и усечение логов контейнеров..." >> "$LOG_FILE"
find /var/lib/docker/containers/ -name "*-json.log*" -size +15M -exec truncate -s 2M {} + >> "$LOG_FILE" 2>&1

# 5. Очистка системных логов и кэшей хоста Linux
echo "[$DATE] Очистка системных кэшей хоста (btmp, journald, apt)..." >> "$LOG_FILE"
truncate -s 0 /var/log/btmp 2>/dev/null
apt-get clean 2>/dev/null
journalctl --vacuum-size=50M >> "$LOG_FILE" 2>&1
rm -rf /root/.npm 2>/dev/null
find /tmp -type f -atime +2 -delete 2>/dev/null

# 6. Освежение оперативной памяти (сброс кэша диска в RAM)
sync
echo 3 > /proc/sys/vm/drop_caches

END_DATE=$(date '+%Y-%m-%d %H:%M:%S')
FREE_DISK=$(df -h / | awk 'NR==2 {print $4}')
FREE_MEM=$(free -h | awk 'NR==2 {print $7}')
SWAP_USED=$(free -h | awk 'NR==3 {print $3}')

echo "[$END_DATE] Ежедневное обслуживание успешно завершено!" >> "$LOG_FILE"
echo "[$END_DATE] Свободно на диске: $FREE_DISK | Доступно RAM: $FREE_MEM | SWAP занято: $SWAP_USED" >> "$LOG_FILE"
echo "=========================================================" >> "$LOG_FILE"
