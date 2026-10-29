# Лог сессии: Исправление ошибки отклонения генерации СБП QR Т-Банком в курьерском модуле
Дата: 2026-09-05 19:20
Сессия: 2026-09-05_19-20_tbank_sbp_qr_fix

## 1. Симптомы проблемы
Пользователь сообщил: при выборе кнопки оплаты по СБП в панели курьера выдается сообщение, что Т-Банк отклонил операцию по генерации QR.

## 2. Диагностика на VPS сервере
1. В логах контейнера oodtech-backend зафиксированы ошибки 500:
   POST /api/v1/courier/orders/2817/sbp-qr HTTP/1.1 500 Internal Server Error
2. Детальный разбор вызова QRPAY API (https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QRPAY):
   - В поле 	erId ошибочно передавался 	erminal_delivery (3190040478), являющийся POS-терминалом торгового эквайринга Т-Банк Бизнес, а не кассовым СБП-терминалом.
   - В поле mchId передавался merchant_id из базы данных с лидирующим пробелом ( 400000001164353).
   - В качестве ключа подписи (secret_key) в generate_tbank_qrpay_signature передавался settings.token (OpenAPI Bearer-токен t.HN...), а не секретный HMAC-ключ СБП (LYqV0t7V3FBffuphkOs7oR7Le9Cr994xRjmaGxoVJKY=).
   - В результате Т-Банк отклонял запрос с ошибкой INVALIDSTORE («Неверный номер терминала»).
3. При тестировании с правильными учетными данными:
   - mchId: 400000001164353
   - 	erId: 42734785 (касса Dovezuka СБП)
   - secret_key: LYqV0t7V3FBffuphkOs7oR7Le9Cr994xRjmaGxoVJKY=
   Т-Банк успешно сгенерировал реальную динамическую ссылку СБП НСПК (Code: SUCCESS, outTradeNo: 1941875083, URL: https://qr.nspk.ru/...) и успешно вернул статус QUERY: USINGPAY / DOVEZUKA.

## 3. План исправления
1. Внести изменения в `backend/app/core/tbank_utils.py` (добавить надежную функцию `get_tbank_sbp_credentials`).
2. Добавить поля `sbp_terminal_id` и `sbp_secret_key` в модель `TBankSettings` (`backend/app/models/tbank_settings.py`) и схему `TBankSettingsSchema` (`backend/app/api/tbank.py`).
3. Исправить эндпоинты `create_courier_sbp_qr` и `get_courier_sbp_state` в `backend/app/api/courier.py`.
4. Исправить эндпоинты СБП в `backend/app/api/tbank.py` и `backend/app/services/vk_notification_router.py`.
5. Обновить БД на VPS (`ALTER TABLE tbank_settings...`).
6. Обновить интерфейс `admin/resources/js/pages/settings/tbank.vue` и пересобрать фронтенд.
7. Протестировать генерацию QR на реальном заказе курьера.

## 4. Инцидент с «вечной загрузкой» админки после деплоя ассетов
- **Причина**: При рекурсивном копировании каталога `admin/public/build/*` через `scp` с ОС Windows на Linux хост права на подкаталог `assets` установились как `drwx------` (`700`, владелец `root`). В результате Nginx (пользователь `nginx`) при попытке отдать JS-бандлы приложения Vue (`main-CHzktIAq.js`, `index-BfAG61ho.js`) получал ошибку ОС `(13: Permission denied)`. В браузере HTML страница не могла загрузить JS код, из-за чего крутился индикатор вечной загрузки.
- **Устранение**: Выполнена команда `chmod -R 777 /root/foodzuka/admin/public/build`. Все JS ассеты отдаются Nginx со статусом 200 OK. Админ-панель загружается моментально.
- **Правило**: При любой повторной выгрузке ассетов фронтенда с Windows обязательно выполнять `chmod -R 777 /root/foodzuka/admin/public/build` на VPS.
