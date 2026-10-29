# Лог задачи: Выбор бота MAX и каскадная отправка сообщений (Бот -> Личные по номеру)

**Дата и время**: 05.09.2026 01:30  
**Сессия**: loggemini_2026_09_05_0130_max_bot_selection_and_cascade_routing  
**Сервер**: VPS vezuroll (178.212.13.48), проект /root/foodzuka/  
**Статус**: Выполнено успешно  

---

## 1. Постановка задачи
1. В меню «Системные рассылки» (/settings/vk-notifications):
   - Добавить возможность выбора конкретного подключенного бота MAX из базы max_bots для шаблонов, курьерских цепочек и сотрудников.
   - Добавить выбор режима отправки:
     - cascade: сначала бот MAX -> если бот не смог доставить (нет открытого диалога / ошибка), автоматически отправлять через личные сообщения личного аккаунта MAX по номеру телефона (Web Bridge).
     - bot_only: отправка строго через выбранного бота MAX без перехода в личные.
     - bridge_only: отправка строго через личный аккаунт по номеру телефона.
2. В меню «Уведомления и рассылки» (/mailings/notifications-and-mailings):
   - Для шагов каскада с каналом max добавить выбор конкретного бота MAX и выбор режима отправки (Каскад, Только бот, Только личный аккаунт).

---

## 2. Изменения в базе данных (PostgreSQL)
В контейнере foodtech-db добавлены колонки:
- vk_templates: max_bot_id INT, max_send_mode VARCHAR(50) DEFAULT 'cascade'
- vk_bot_accounts: max_bot_id INT, max_send_mode VARCHAR(50) DEFAULT 'cascade'
- mailing_cascade_steps: max_bot_id INT, max_send_mode VARCHAR(50) DEFAULT 'cascade'

---

## 3. Бэкенд (Python / FastAPI)
1. backend/app/models/vk_bot.py: добавлены поля max_bot_id, max_send_mode.
2. backend/app/models/mailing_cascade.py: добавлены поля max_bot_id, max_send_mode.
3. backend/app/schemas/mailing_cascade.py: добавлены поля max_bot_id, max_send_mode.
4. backend/app/services/max_service.py:
   - send_max_message и _do_send_max_message поддерживают bot_id.
   - Поддержаны 3 режима prefer_channel: cascade, bot_only, bridge_only.
   - Устранен логический баг ложного сброса статуса в failed после успешной отправки через Web Bridge.
5. backend/app/services/vk_notification_router.py:
   - send_max_message_helper принимает bot_id и prefer_channel.
   - Для курьеров и сотрудников передаются эффективные eff_bot_id и eff_mode.
6. backend/app/services/mailing_cascade_service.py:
   - has_max теперь проверяет customer.max_user_id or customer.phone.
   - Шаг каскада передает bot_id=step.max_bot_id и prefer_channel=step.max_send_mode.
7. backend/app/api/vk_bot_admin.py:
   - В схемах и роутах добавлены max_bot_id, max_send_mode.
   - Эндпоинт GET /api/v1/vk-bot/max-bots.
   - Эндпоинт POST /api/v1/vk-bot/templates/{template_id}/set-max-bot.

---

## 4. Фронтенд (Vue.js / Vite)
1. admin/resources/js/pages/settings/vk-notifications_utf8.vue:
   - Селекторы выбора конкретного бота MAX и режима отправки в цепочках курьера, системных шаблонах, карточках сотрудников и модальных окнах.
2. admin/resources/js/pages/mailings/notifications-and-mailings.vue:
   - В конструкторе шагов каскада при step.channel === 'max' отображается блок выбора бота MAX и режима отправки.

---

## 5. Сборка и деплой на VPS
1. Выполнена сборка npm run build (20.56s).
2. Обновленные файлы бэкенда и бандла выгружены на VPS.
3. Права доступа на сервере: chmod -R 755 /root/foodzuka/admin/public/build.
4. Перезапущены контейнеры foodtech-backend и foodtech-worker.
5. Хэши MD5 локальных и удаленных файлов проверены и идентичны.
