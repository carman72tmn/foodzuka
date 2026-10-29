# Лог сессии: Подключение интернет-эквайринга Т-Банка и Webhook-уведомления (СБП, T-Pay)
Дата: 16.09.2026 22:50
Задача: Добавление в настройки T-API подключения интернет-эквайринга от Т-Банка, получение вебхук-уведомлений о платежах и их статусе через интернет-эквайринг (в т.ч. по СБП и T-Pay) с отображением в Мониторе Т-Банка в режиме реального времени.

## 1. Выполненные действия:
1. База данных PostgreSQL (VPS):
   - В таблицу `tbank_settings` добавлены колонки:
     * `acquiring_terminal_key VARCHAR`
     * `acquiring_password VARCHAR`
     * `acquiring_is_active BOOLEAN DEFAULT TRUE`
     * `webhook_secret VARCHAR`
2. Модели и схемы бэкенда:
   - `backend/app/models/tbank_settings.py`: расширена модель `TBankSettings`.
   - `backend/app/api/tbank.py`: обновлены `TBankSettingsSchema`, сохранение настроек, автоматическое тестирование подключения через `https://securepay.tinkoff.ru/v2/Init`, проверка статуса платежа через интернет-эквайринг `GetState`.
3. Вебхуки Т-Банка:
   - `backend/app/api/tbank_webhooks.py`:
     * Добавлена SHA-256 валидация токена `Token` по паролю интернет-эквайринга.
     * Реализовано точное определение методов оплаты (СБП, T-Pay, Эквайринг картой).
     * Автоматическая запись подтвержденных транзакций в `tbank_statements`.
     * Внедрена потокобезопасная отправка через `manager.broadcast_sync(ws_payload)` по межпроцессной шине Redis Pub/Sub `foodtech:ws_broadcast`.
     * Возврат строгого текстового ответа `OK` (200 OK) Т-Банку.
4. Интерфейс панели управления:
   - `admin/resources/js/pages/settings/tbank.vue`:
     * Добавлена секция настроек «Интернет-эквайринг Т-Банк (Онлайн-оплаты картами, СБП и T-Pay)» с полями TerminalKey, Password (с кнопкой скрытия), переключателем активности.
     * Размещен блок «URL для получения уведомлений об оплатах (Вебхуки)» со ссылками `https://vezuroll.ru/api/v1/tbank/webhooks/payment-status` и `https://vezuroll.ru/api/v1/tbank/webhooks/sbp-qr` и кнопками быстрого копирования в буфер обмена.
5. Деплой и тестирование на боевом сервере (VPS):
   - Все файлы переданы на сервер (`ssh vezuroll`), хэши MD5 проверены и полностью совпадают:
     * `backend/app/models/tbank_settings.py`: `a4b9a5c566db5a316190fc7cb13a2222`
     * `backend/app/api/tbank.py`: `3edf02bf2e2f06e43da0721b91a1b922`
     * `backend/app/api/tbank_webhooks.py`: `72a98c145a7366d40f0208512cf698cd`
     * `admin/resources/js/pages/settings/tbank.vue`: `d0c4b2541f705f3f9858ad9323415104`
   - Выполнена сборка Vite: `npm run build` завершена успешно за 1m 31s.
   - Контейнеры `foodtech-backend` и `foodtech-worker` перезапущены.
   - Проведен контрольный тест вебхука: эндпоинт вернул `200 OK`, запись создана в `tbank_statements`, WebSocket-уведомление успешно доставлено в браузер.
6. Документация:
   - Обновлены `system_faq.md`, `sql_faq.md`, `sitenav.md`.
