# Лог задачи: Исправление белого экрана в админ-панели
Дата: 2026-05-03
Время: 10:30

## Проблема
Пользователь сообщил о белом экране по адресу https://vezuroll.ru/admin/.

## Исследование
1. Браузер показывает ошибки 404 для ассетов:
   - /build/assets/main-BlPDfJ_I.js
   - /build/assets/main-B4NHxNyQ.css
   - /favicon.ico
   - /loader.css
2. Файлы на VPS физически существуют в `/root/foodzuka/admin/public/`.
3. Конфигурация Nginx проксирует все запросы от корня `/` на контейнер `frontend`.
4. В `admin/.env` параметр `ASSET_URL` установлен в `https://vezuroll.ru`, что заставляет Laravel генерировать пути от корня.

## План действий
1. Добавить в `configs/nginx/default.conf` блоки для `/build/`, `/favicon.ico` и `/loader.css`.
2. Синхронизировать конфиг с VPS.
3. Перезапустить Nginx.
4. Проверить работоспособность.
