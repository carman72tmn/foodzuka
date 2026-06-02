# Руководство по миграции проекта FoodZuka

Это техническое руководство содержит точные команды для переноса проекта с текущего сервера на новый.

## 1. Подготовка нового сервера
Выполните на **новом** сервере:
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install -y docker-compose-v2

# Создание рабочей директории
mkdir -p /root/foodzuka
```

## 2. Экспорт базы данных (на старом сервере)
Выполните на **текущем** сервере:
```bash
cd /root/foodzuka
# Создание дампа
docker exec foodtech-db pg_dump -U foodtech_user foodtech_db > db_backup.sql
```

## 3. Перенос данных (на новом сервере)
Выполните на **новом** сервере (замените `OLD_IP` на адрес текущего сервера):
```bash
# Копирование всех файлов проекта
rsync -avzP root@OLD_IP:/root/foodzuka/ /root/foodzuka/
```

## 4. Развертывание (на новом сервере)
Выполните на **новом** сервере:
```bash
cd /root/foodzuka

# 1. Запуск БД и Redis
docker compose up -d db redis

# 2. Ожидание запуска БД (5-10 сек) и импорт дампа
cat db_backup.sql | docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db

# 3. Запуск всех остальных сервисов
docker compose up -d

# 4. Проверка статуса
docker compose ps
```

## 5. Обновление SSL (Nginx)
Если домен переносится на новый IP:
1. Дождитесь обновления DNS.
2. Перезапустите certbot или выполните получение сертификата заново:
```bash
docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d YOUR_DOMAIN
```

## Важные замечания
- **.env файлы:** Проверьте `APP_URL` и другие IP-зависимые переменные в `/root/foodzuka/.env` и подпапках.
- **iiko API:** Убедитесь, что новый IP сервера добавлен в белый список iiko (если требуется ограничение по IP).
- **Права доступа:** После `rsync` проверьте права на папки (обычно `root` достаточно для Docker, но медиа могут требовать внимания).

---
**Документ создан:** 01.05.2026
**Статус:** Готов к использованию
