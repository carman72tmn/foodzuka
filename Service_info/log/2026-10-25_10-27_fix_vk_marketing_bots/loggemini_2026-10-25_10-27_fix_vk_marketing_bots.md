# Лог сессии: Исправление и доработка 6 Маркетинговых Ботов ВКонтакте
**Дата и время**: 25.10.2026 12:50 (UTC+5)  
**Сессия**: `2026-10-25_10-27_fix_vk_marketing_bots`  
**Исполнитель**: AI Агент (Antigravity)  
**URL**: `vezuroll.ru/admin` -> `/marketing/vk-bots`

---

## 1. Исходная проблема и ревизия ошибок
По результатам инспекции были зафиксированы 5 корневых проблем:
1. **Ошибка сохранения `invalid input syntax for type json`**:
   - В PostgreSQL поля `trigger_keywords` и `trigger_command` имеют тип `jsonb`. Фронтенд отправлял строковое значение `"меню, начать"`, из-за чего SQL-запрос `SET trigger_keywords = 'меню, начать'` падал с `500 Internal Server Error`.
2. **Бот рассылок (`broadcast`) всегда активен**:
   - В таблице `vk_smart_broadcasts` отсутствовала колонка `is_active`. Значение отбрасывалось при валидации колонок, а бэкенд возвращал дефолтное `True`.
3. **Не переключались вкладки в модальном окне настроек**:
   - Директива `v-show` конфликтовала с классом Vuetify `.d-flex`, содержащим `display: flex !important;`, перебивающим инлайновый стиль скрытия.
4. **Неполнота полей ТЗ**:
   - Во многих ботах отсутствовали поля (загрузка картинок, выбор типов подарков, антифрод, фильтрация аудитории, живая аналитика).
5. **Хуки сообщений ВК**:
   - Отсутствовала маршрутизация реферальных переходов (`ref=VR-XXXXX`), команд Колеса фортуны (`"крутить"`), реферальных команд (`"пригласить друга"`) и интерактивного меню каталога.

---

## 2. Выполненные работы по ТЗ

### Шаг 1. База данных PostgreSQL (`foodtech-db`)
- В таблицу `vk_smart_broadcasts` добавлена колонка `is_active BOOLEAN DEFAULT TRUE`.
- Проверены и актуализированы все недостающие колонки в таблицах:
  - `vk_shop_bots`: `welcome_message_guest`, `repeat_order_lookback_count`, `allow_bonus_payment_in_bot`, `max_bonus_payment_percent`, `order_creation_mode`.
  - `vk_retention_bots`: `newbie_gift_mode`, `sleeping_gift_mode`, `lost_vip_gift_mode`, `newbie_photo_url`, `sleeping_photo_url`, `lost_vip_photo_url`, `burn_reminder_hours_before`.
  - `vk_review_nps_bots`: `positive_rating_threshold`, `max_paid_reviews_per_month`, `msg_negative_thank_you`, `alert_admin_vk_ids`, `auto_apology_promo_code`.
  - `vk_wheel_bots`: `contest_post_id`, `require_messages_allowed`, `free_spins_period`, `wheel_bg_image_url`, `draw_user_avatar_in_center`, `msg_dm_win_template`, `msg_dm_reminder_template`, `remind_before_expire_hours`.
  - `vk_smart_broadcasts`: `segment_bonus_min`, `segment_avg_check_min`, `exclude_last_touched_days`, `happy_hours_days_of_week`, `happy_hours_lookback_hours`, `happy_hours_batch_size`.
  - `vk_referral_programs`: `trigger_command`, `friend_reward_type`, `friend_gift_product_id`, `antifraud_prevent_same_phone_address`, `antifraud_max_friends_per_month`, `antifraud_auto_ban_suspicious`, `msg_friend_reward_template`, `msg_referrer_reward_template`.

### Шаг 2 и 4. Фронтенд (`VkMarketingBotModal.vue`, `vk-bots.vue`)
- Вкладки переведены на связку `VBtn` + `v-if` / `v-else-if`, что полностью устранило конфликт со стилями `.d-flex`.
- Для всех полей картинок (`banner_url`, `photo_url`, `bg_image_url`) реализован `VFileInput` с мгновенной выгрузкой через эндпоинт `/api/v1/vk/marketing-bots/upload-media/{connection_id}`.
- Внедрены все поля для всех 6 ботов во всех 4 вкладках модального окна.
- Интегрированы живые данные аналитики и истории логов для вкладки 4 каждого бота.
- Сборка фронтенда (`npm run build`) на VPS завершилась успешно (`vk-bots-B2_eZrPc.js`).

### Шаг 3. Бэкенд (`vk_marketing_endpoints.py`, `vk_marketing_bots_service.py`)
- Реализована строгая типизация значений перед сохранением в PostgreSQL:
  - Проверка схемы таблицы по `information_schema.columns`.
  - Автоматическое преобразование строковых списков с запятыми и массивов в JSON (`json.dumps`) для полей `jsonb`/`json`.
- Эндпоинты `/config/{connection_id}` и `/toggle-active/{bot_type}/{connection_id}` синхронизированы с полем `is_active` всех 6 таблиц.
- Эндпоинт `/analytics/{bot_type}/{connection_id}` агрегирует живые метрики из таблиц `orders`, `vk_retention_logs`, `vk_order_reviews`, `vk_wheel_spins`, `vk_broadcast_logs`, `vk_referrals`.

### Шаг 5. Маршрутизация хуков ВК (`vk_service.py`)
- Добавлен перехват реферального параметра `ref=VR-XXXXX` / `start=VR-XXXXX` в `vk_service.py`.
- Добавлен перехват реферальных команд (`"пригласить друга"`, `"рефералка"`).
- Добавлен перехват команд Колеса фортуны (`"крутить"`, `"рулетка"`).
- Добавлен перехват ключевых слов бота каталога (`"меню"`, `"начать"`, `"каталог"`).

### Шаг 6. Тестирование и деплой
- Все изменения синхронизированы на VPS (`/root/foodzuka/`).
- Контейнеры `backend`, `worker`, `admin`, `nginx` перезапущены.
- Тест сохранения `save_bot_config` и переключения `toggle_bot_active` для всех 6 ботов возвращает `HTTP 200 OK`.
- Все 6 ботов активны в базе данных.

---

## 3. Документация
- `Service_info/sql_faq.md` обновлен (описаны все поля 6 таблиц маркетинговых ботов).
- `Service_info/system_faq.md` дополнен разделом №8.
- `Service_info/sitenav.md` дополнен описанием раздела `/marketing/vk-bots`.
