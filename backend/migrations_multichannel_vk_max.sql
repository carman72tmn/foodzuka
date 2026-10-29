-- Миграция: Добавление мультиканальности (ВК + MAX от личного номера) для 6 маркетинговых ботов
-- Дата: 2026-10-25

-- 1. vk_shop_bots
ALTER TABLE vk_shop_bots
    ADD COLUMN IF NOT EXISTS vk_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS max_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS max_send_mode VARCHAR(32) DEFAULT 'bridge_only',
    ADD COLUMN IF NOT EXISTS max_daily_limit INTEGER DEFAULT 100,
    ADD COLUMN IF NOT EXISTS max_delay_seconds INTEGER DEFAULT 15,
    ADD COLUMN IF NOT EXISTS test_admin_phones JSONB DEFAULT '["79220079019"]'::jsonb,
    ADD COLUMN IF NOT EXISTS max_welcome_message_verified TEXT DEFAULT 'Привет, {first_name}! 🍣 Добро пожаловать в «Везу Ролл»! Напишите: 1 - Хиты, 2 - Повторить заказ, 3 - Где заказ?, 4 - Бонусы',
    ADD COLUMN IF NOT EXISTS max_welcome_message_guest TEXT DEFAULT 'Привет! 🍣 Добро пожаловать в доставку суши и роллов «Везу Ролл»! Напишите: 1 - Хиты, 2 - Повторить заказ, 3 - Где заказ?, 4 - Бонусы',
    ADD COLUMN IF NOT EXISTS max_status_check_template TEXT DEFAULT 'Статус вашего заказа №{order_number}: {status_human}. Курьер: {courier_name}.';

-- 2. vk_retention_bots
ALTER TABLE vk_retention_bots
    ADD COLUMN IF NOT EXISTS vk_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS max_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS max_send_mode VARCHAR(32) DEFAULT 'bridge_only',
    ADD COLUMN IF NOT EXISTS max_daily_limit INTEGER DEFAULT 100,
    ADD COLUMN IF NOT EXISTS max_delay_seconds INTEGER DEFAULT 15,
    ADD COLUMN IF NOT EXISTS test_admin_phones JSONB DEFAULT '["79220079019"]'::jsonb,
    ADD COLUMN IF NOT EXISTS max_newbie_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS max_newbie_template TEXT DEFAULT 'Привет, {first_name}! Неделю назад вы заказывали у нас сет. Как всё прошло? Дарим скидку 15% на второй заказ по промокоду {promo_code}!',
    ADD COLUMN IF NOT EXISTS max_sleeping_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS max_sleeping_template TEXT DEFAULT '{first_name}, мы скучаем! 🥺 Прошло уже 21 день с вашего прошлого заказа. Специально для вас начислили 🎁 300 бонусов! Они сгорят через 72 часа.',
    ADD COLUMN IF NOT EXISTS max_lost_vip_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS max_lost_vip_template TEXT DEFAULT '{first_name}, как наш любимый VIP-гость, при следующем заказе от 1200 ₽ получите ролл «Филадельфия» в подарок по коду {promo_code} + 300 бонусов!',
    ADD COLUMN IF NOT EXISTS max_burn_reminder_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS max_burn_reminder_template TEXT DEFAULT '⏰ {first_name}, напоминаем: ваши 300 подарочных бонусов сгорят завтра! Успейте заказать любимые суши.';

-- 3. vk_review_nps_bots
ALTER TABLE vk_review_nps_bots
    ADD COLUMN IF NOT EXISTS vk_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS max_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS max_send_mode VARCHAR(32) DEFAULT 'bridge_only',
    ADD COLUMN IF NOT EXISTS max_daily_limit INTEGER DEFAULT 100,
    ADD COLUMN IF NOT EXISTS max_delay_seconds INTEGER DEFAULT 15,
    ADD COLUMN IF NOT EXISTS test_admin_phones JSONB DEFAULT '["79220079019"]'::jsonb,
    ADD COLUMN IF NOT EXISTS max_msg_ask_rating TEXT DEFAULT 'Ваш заказ №{order_number} доставлен! Оцените, пожалуйста, качество блюд и доставку от 1 до 5 (отправьте цифру в ответ):',
    ADD COLUMN IF NOT EXISTS max_msg_positive TEXT DEFAULT 'Спасибо за высокую оценку! ❤️ Рады стараться для вас!',
    ADD COLUMN IF NOT EXISTS max_msg_negative TEXT DEFAULT 'Нам очень жаль, что блюда не порадовали 😔 Пожалуйста, напишите в ответ, что именно пошло не так — сообщение сразу передается руководству!',
    ADD COLUMN IF NOT EXISTS max_alert_admin_phones JSONB DEFAULT '[]'::jsonb;

-- 4. vk_wheel_bots
ALTER TABLE vk_wheel_bots
    ADD COLUMN IF NOT EXISTS vk_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS max_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS max_send_mode VARCHAR(32) DEFAULT 'bridge_only',
    ADD COLUMN IF NOT EXISTS max_daily_limit INTEGER DEFAULT 100,
    ADD COLUMN IF NOT EXISTS max_delay_seconds INTEGER DEFAULT 15,
    ADD COLUMN IF NOT EXISTS test_admin_phones JSONB DEFAULT '["79220079019"]'::jsonb,
    ADD COLUMN IF NOT EXISTS max_msg_dm_win_template TEXT DEFAULT '🎉 Поздравляем! Ваш выигрыш в Колесе Фортуны: «{prize_name}»! Ваш промокод: {promo_code} (действует {valid_until}).',
    ADD COLUMN IF NOT EXISTS max_msg_dm_reminder_template TEXT DEFAULT '🔥 {first_name}, ваш выигрыш «{prize_name}» сгорит через 24 часа! Успейте заказать!';

-- 5. vk_smart_broadcasts
ALTER TABLE vk_smart_broadcasts
    ADD COLUMN IF NOT EXISTS vk_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS max_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS max_send_mode VARCHAR(32) DEFAULT 'bridge_only',
    ADD COLUMN IF NOT EXISTS max_daily_limit INTEGER DEFAULT 100,
    ADD COLUMN IF NOT EXISTS max_delay_seconds INTEGER DEFAULT 15,
    ADD COLUMN IF NOT EXISTS test_admin_phones JSONB DEFAULT '["79220079019"]'::jsonb,
    ADD COLUMN IF NOT EXISTS max_broadcast_text TEXT DEFAULT '🍣 {first_name}, соскучились по свежим роллам? Дарим порцию запечённых мидий к заказу от 1100 ₽ по промокоду МИДИИ!',
    ADD COLUMN IF NOT EXISTS max_happy_hours_template TEXT DEFAULT '🍣 {first_name}, только сегодня с 14:00 до 17:00 скидка 20% на все сеты по промокоду ОБЕД!',
    ADD COLUMN IF NOT EXISTS channel_target VARCHAR(20) DEFAULT 'vk',
    ADD COLUMN IF NOT EXISTS vk_sent_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS vk_error_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS max_sent_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS max_error_count INTEGER DEFAULT 0;

-- 6. vk_referral_programs
ALTER TABLE vk_referral_programs
    ADD COLUMN IF NOT EXISTS vk_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS max_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS max_send_mode VARCHAR(32) DEFAULT 'bridge_only',
    ADD COLUMN IF NOT EXISTS max_daily_limit INTEGER DEFAULT 100,
    ADD COLUMN IF NOT EXISTS max_delay_seconds INTEGER DEFAULT 15,
    ADD COLUMN IF NOT EXISTS test_admin_phones JSONB DEFAULT '["79220079019"]'::jsonb,
    ADD COLUMN IF NOT EXISTS max_msg_ambassador_info TEXT DEFAULT 'Ваш реферальный промокод: {referral_code}. Поделитесь им с другом: он получит скидку, а вы — {referrer_reward_points} бонусов после его первого заказа!',
    ADD COLUMN IF NOT EXISTS max_msg_friend_welcome TEXT DEFAULT 'Привет! Ваш друг дарит вам {friend_bonus_points} бонусов на первый заказ от {friend_min_order_sum} ₽! Промокод: {referral_code}',
    ADD COLUMN IF NOT EXISTS max_msg_referrer_reward_paid TEXT DEFAULT '🎉 Ура! Ваш друг {friend_name} получил свой первый заказ! Вам начислено +{referrer_reward_points} бонусов в iiko!';

-- Логи и отзывы
ALTER TABLE vk_bot_message_logs
    ADD COLUMN IF NOT EXISTS channel VARCHAR(16) DEFAULT 'vk',
    ADD COLUMN IF NOT EXISTS customer_phone VARCHAR(32);

ALTER TABLE vk_retention_logs
    ADD COLUMN IF NOT EXISTS channel VARCHAR(16) DEFAULT 'vk',
    ADD COLUMN IF NOT EXISTS customer_phone VARCHAR(32);

ALTER TABLE vk_order_nps_reviews
    ALTER COLUMN vk_id DROP NOT NULL,
    ADD COLUMN IF NOT EXISTS channel VARCHAR(16) DEFAULT 'vk',
    ADD COLUMN IF NOT EXISTS customer_phone VARCHAR(32),
    ADD COLUMN IF NOT EXISTS customer_id INTEGER;

ALTER TABLE vk_wheel_spins
    ALTER COLUMN vk_id DROP NOT NULL,
    ADD COLUMN IF NOT EXISTS channel VARCHAR(16) DEFAULT 'vk',
    ADD COLUMN IF NOT EXISTS customer_phone VARCHAR(32),
    ADD COLUMN IF NOT EXISTS customer_id INTEGER;

ALTER TABLE vk_referral_links
    ALTER COLUMN referrer_vk_id DROP NOT NULL,
    ADD COLUMN IF NOT EXISTS channel VARCHAR(16) DEFAULT 'vk',
    ADD COLUMN IF NOT EXISTS referrer_phone VARCHAR(32),
    ADD COLUMN IF NOT EXISTS invited_phone VARCHAR(32);
