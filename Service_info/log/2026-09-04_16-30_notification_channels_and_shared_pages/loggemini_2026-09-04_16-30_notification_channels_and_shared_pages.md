# Лог сессии: Выбор каналов для рассылок пользователям/сотрудникам и одинаковые страницы для уведомлений

**Дата и время**: 2026-09-04 16:30  
**Сессия**: loggemini_2026-09-04_16-30_notification_channels_and_shared_pages  
**Задача**:
1. В раздел «Рассылки -> Системные рассылки» (/settings/vk-notifications) добавить возможность выбора каналов рассылок для каждого сотрудника и пользователя системы.
2. Реализовать настройку каналов (ВКонтакте, Telegram, MAX, SMS) для каждого сотрудника с быстрыми переключателями на карточках и в модальных окнах.
3. Разрешить добавление одинаковых страниц (профилей ВК, Telegram) для разных пользователей и получателей, сняв ограничение UNIQUE в базе данных и убрав блокирующие проверки в API.
4. Добавить защиту от дублирования сообщений при рассылках, если у нескольких получателей одна страница.
5. Добавить возможность привязки системных пользователей админки (users) в качестве получателей системных рассылок.

---

## 1. Запланированные этапы

1. Создание миграционного скрипта migrate_allow_duplicate_vk_pages_and_user_links.py.
2. Обновление модели VkBotAccount в backend/app/models/vk_bot.py.
3. Модернизация API backend/app/api/vk_bot_admin.py (снятие уникальности страниц, эндпоинты каналов, выбор пользователей, автосинхронизация подписок).
4. Обновление службы backend/app/services/vk_notification_router.py (дедупликация физической отправки при одинаковых страницах).
5. Обновление интерфейса Vue.js в admin/resources/js/pages/settings/vk-notifications_utf8.vue.
6. Сборка фронтенда (npm run build).
7. Применение миграции на VPS (vezuroll.ru), выгрузка файлов по SCP, перезапуск бэкенда и воркера.
8. Тестирование и верификация функционала на боевом сервере.
9. Обновление документации в system_faq.md, sql_faq.md, sitenav.md.

---

## 2. Результаты выполнения

### 2.1. База данных PostgreSQL (VPS)
- Миграция `backend/app/scripts/migrate_allow_duplicate_vk_pages_and_user_links.py` выполнена успешно.
- Удален уникальный индекс `ix_vk_bot_accounts_vk_user_id` и констрейнт `vk_bot_accounts_vk_user_id_key`.
- Создан обычный индекс `CREATE INDEX ix_vk_bot_accounts_vk_user_id ON vk_bot_accounts (vk_user_id)`.
- Добавлено внешнее поле `user_id INTEGER DEFAULT NULL REFERENCES users(id) ON DELETE SET NULL` с индексом `ix_vk_bot_accounts_user_id`.

### 2.2. Бэкенд
- В `backend/app/models/vk_bot.py`:
  - `vk_user_id` переведен в `unique=False, index=True`.
  - Добавлено поле `user_id: Optional[int] = Field(default=None, foreign_key="users.id")`.
- В `backend/app/api/vk_bot_admin.py`:
  - Добавлен роут `GET /api/v1/vk-bot/users/search` для поиска пользователей админки.
  - Добавлен роут `POST /api/v1/vk-bot/accounts/{account_id}/toggle-channel` для переключения каналов в 1 клик.
  - Добавлен роут `POST /api/v1/vk-bot/accounts/{account_id}/bulk-toggle-subscriptions` для пакетного управления каналами подписок во всех событиях.
  - В `add_account` и `update_account` сняты проверки уникальности ВК страниц, добавлена автоинициализация подписок.
- В `backend/app/services/vk_notification_router.py`:
  - Функция `is_admin_or_manager` дополнена поддержкой прав через `acc.user_id`.
  - В `dispatch_event` внедрена дедупликация отправки (`sent_vk_results`, `sent_tg_results`, `sent_max_results`) внутри контекста события. Физическое сообщение отправляется в API соцсети ровно один раз, предотвращая спам дублями, при этом отчетность (`courier_order_notifications`, `vk_bot_message_logs`) сохраняется для каждого подписанного аккаунта.

### 2.3. Фронтенд (Vue.js)
- В `admin/resources/js/pages/settings/vk-notifications_utf8.vue`:
  - На карточках получателей выведены интерактивные чипсы `[VK]`, `[TG]`, `[MAX]`, `[SMS]` с переключением в 1 клик.
  - Добавлен бейдж `Общая VK страница (ID: ...)` для визуализации общих страниц.
  - Добавлено отображение привязанного пользователя админки.
  - В диалоге добавления добавлена вкладка `Пользователь системы` с живым автодополнением.
  - В диалоге редактирования добавлено поле привязки к пользователю админки.
  - В окне подписок добавлена панель кнопок пакетного включения/отключения каждого канала во всех событиях.
- Сборка фронтенда `npm run build` выполнена успешно (`public/build/assets/vk-notifications_utf8-CdQ03SFr.js`).

### 2.4. Выгрузка на VPS и верификация
- Все измененные файлы бэкенда, фронтенда и собранный билд выгружены на VPS (`vezuroll.ru:/root/foodzuka/`).
- Выставлены права 755 на `admin/public/build`.
- Перезапущены контейнеры `docker compose restart backend worker`.
- Сверка контрольных сумм SHA256 подтвердила 100% идентичность локальных файлов и файлов на сервере.
- Тест базы данных подтвердил создание и чтение получателей с одинаковыми `vk_user_id`.
- Тест API подтвердил корректную работу `/users/search`, `/toggle-channel` и `/bulk-toggle-subscriptions`.
- Документация в `system_faq.md`, `sql_faq.md`, `sitenav.md` обновлена.

