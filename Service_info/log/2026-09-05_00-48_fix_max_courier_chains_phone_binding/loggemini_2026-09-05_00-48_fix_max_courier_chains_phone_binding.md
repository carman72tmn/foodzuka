# Лог сессии: Исправление настройки системной рассылки MAX и привязки по номеру телефона
Дата: 2026-09-05 00:48

## 1. Проблема и задачи
1. Ошибка 422 missing allow_courier_chains при вызове `POST /api/v1/vk-bot/accounts/{account_id}/toggle-courier-chains`.
2. В интерфейсе и API замена неинтуитивного `MAX ID` на номер телефона для привязки (с автоподстановкой основного телефона сотрудника).
3. Fallback на личный аккаунт MAX Web Bridge по номеру телефона при отправке проверочных сообщений и рассылок, если сотрудник не открыл диалог с официальным ботом.

## 2. Внесенные изменения
1. **backend/app/api/vk_bot_admin.py**:
   - `CourierChainsToggleRequest`: сделано `allow_courier_chains: Optional[bool] = None`, добавлены `channel: Optional[str] = None`, `enabled: Optional[bool] = None`.
   - `toggle_account_courier_chains`: поддержано независимое включение/выключение каналов (`max`, `vk`, `tg`, `sms`) и синхронизация подписок курьера без обязательного `allow_courier_chains`.
   - `create_account` и `update_account`: реализована автоматическая подстановка основного телефона в `max_user_id`, если поле не заполнено вручную.
   - `verify_account_max`: извлечение и нормализация телефона сотрудника (`account.max_user_id` или `account.phone`), вызов `send_max_message` с режимом `prefer_channel="auto"`.
2. **backend/app/services/max_bridge_service.py**:
   - В `send_bridge_message` добавлен автоматический резолвинг номера телефона сотрудника в внутренний `user_id` через `pymax.search_by_phone` перед вызовом отправки `send_message(chat_id=...)`.
3. **backend/app/services/max_service.py**:
   - В `_do_send_max_message` обеспечен автоматический поиск пользователя по номеру телефона в Web Bridge при отсутствии сохраненного `target_user_id`, а также fallback на `send_bridge_message` в случае ошибки официального Bot API (например, если пользователь еще не нажимал Start у бота).
4. **admin/resources/js/pages/settings/vk-notifications_utf8.vue**:
   - В диалогах добавления и редактирования получателя лейбл заменен на «Телефон для привязки в MAX Messenger» с подсказкой «Если не указан, используется основной номер телефона».
   - В методах `addAccount`, `openEditAccount`, `saveAccount` добавлена автоподстановка номера телефона.
   - В блоке настройки курьерских цепочек рядом с переключателями каналов добавлены кнопки «Тест TG» и «Тест MAX».

## 3. Сборка и верификация
1. Локальная сборка фронтенда: `npm run build` выполнена за 31.47s, сгенерирован бандл `vk-notifications_utf8-CFtHth2M.js`.
2. Выгрузка файлов бэкенда и `public/build` на VPS: `scp` выполнен успешно, права `chmod -R 755 /root/foodzuka/admin/public/build` установлены.
3. Перезапуск контейнеров на VPS: `docker compose restart backend worker` — оба сервиса запущены и находятся в статусе Up.
4. Тест Pydantic-валидации:
   - Входящий payload `{"channel": "max", "enabled": true}` успешно валидируется и переключает канал курьера без ошибки 422.
   - Входящий payload `{"allow_courier_chains": true}` переключает общий флаг цепочек курьера.
5. Тест проверки связи MAX (`verify_account_max`):
   - Проверен аккаунт 7 (Супер СисАдминистратор, телефон 89220079019).
   - Сообщение успешно доставлено: `{'status': 'success', 'message': 'Проверочное сообщение в MAX успешно отправлено (через официального бота)', 'via': 'bot'}`.
   - Флаг `is_max_verified` выставлен в `True`, телефон сохранен в `account.max_user_id`.
6. Тест Fallback на личный аккаунт Web Bridge:
   - При отсутствии диалога с ботом отработал поиск и fallback через Web Bridge (`pymax client profile=138113613`).

