-- Обновление значений по умолчанию в UTF-8
ALTER TABLE vk_shop_bots
    ALTER COLUMN max_welcome_message_verified SET DEFAULT 'Привет, {first_name}! 🍣 Добро пожаловать в «Везу Ролл»! Напишите: 1 - Хиты, 2 - Повторить заказ, 3 - Где заказ?, 4 - Бонусы',
    ALTER COLUMN max_welcome_message_guest SET DEFAULT 'Привет! 🍣 Добро пожаловать в доставку суши и роллов «Везу Ролл»! Напишите: 1 - Хиты, 2 - Повторить заказ, 3 - Где заказ?, 4 - Бонусы',
    ALTER COLUMN max_status_check_template SET DEFAULT 'Статус вашего заказа №{order_number}: {status_human}. Курьер: {courier_name}.';

ALTER TABLE vk_retention_bots
    ALTER COLUMN max_newbie_template SET DEFAULT 'Привет, {first_name}! Неделю назад вы заказывали у нас сет. Как всё прошло? Дарим скидку 15% на второй заказ по промокоду {promo_code}!',
    ALTER COLUMN max_sleeping_template SET DEFAULT '{first_name}, мы скучаем! 🥺 Прошло уже 21 день с вашего прошлого заказа. Специально для вас начислили 🎁 300 бонусов! Они сгорят через 72 часа.',
    ALTER COLUMN max_lost_vip_template SET DEFAULT '{first_name}, как наш любимый VIP-гость, при следующем заказе от 1200 ₽ получите ролл «Филадельфия» в подарок по коду {promo_code} + 300 бонусов!',
    ALTER COLUMN max_burn_reminder_template SET DEFAULT '⏰ {first_name}, напоминаем: ваши 300 подарочных бонусов сгорят завтра! Успейте заказать любимые суши.';

ALTER TABLE vk_review_nps_bots
    ALTER COLUMN max_msg_ask_rating SET DEFAULT 'Ваш заказ №{order_number} доставлен! Оцените, пожалуйста, качество блюд и доставку от 1 до 5 (отправьте цифру в ответ):',
    ALTER COLUMN max_msg_positive SET DEFAULT 'Спасибо за высокую оценку! ❤️ Рады стараться для вас!',
    ALTER COLUMN max_msg_negative SET DEFAULT 'Нам очень жаль, что блюда не порадовали 😔 Пожалуйста, напишите в ответ, что именно пошло не так — сообщение сразу передается руководству!';

ALTER TABLE vk_wheel_bots
    ALTER COLUMN max_msg_dm_win_template SET DEFAULT '🎉 Поздравляем! Ваш выигрыш в Колесе Фортуны: «{prize_name}»! Ваш промокод: {promo_code} (действует {valid_until}).',
    ALTER COLUMN max_msg_dm_reminder_template SET DEFAULT '🔥 {first_name}, ваш выигрыш «{prize_name}» сгорит через 24 часа! Успейте заказать!';

ALTER TABLE vk_smart_broadcasts
    ALTER COLUMN max_broadcast_text SET DEFAULT '🍣 {first_name}, соскучились по свежим роллам? Дарим порцию запечённых мидий к заказу от 1100 ₽ по промокоду МИДИИ!',
    ALTER COLUMN max_happy_hours_template SET DEFAULT '🍣 {first_name}, только сегодня с 14:00 до 17:00 скидка 20% на все сеты по промокоду ОБЕД!';

ALTER TABLE vk_referral_programs
    ALTER COLUMN max_msg_ambassador_info SET DEFAULT 'Ваш реферальный промокод: {referral_code}. Поделитесь им с другом: он получит скидку, а вы — {referrer_reward_points} бонусов после его первого заказа!',
    ALTER COLUMN max_msg_friend_welcome SET DEFAULT 'Привет! Ваш друг дарит вам {friend_bonus_points} бонусов на первый заказ от {friend_min_order_sum} ₽! Промокод: {referral_code}',
    ALTER COLUMN max_msg_referrer_reward_paid SET DEFAULT '🎉 Ура! Ваш друг {friend_name} получил свой первый заказ! Вам начислено +{referrer_reward_points} бонусов в iiko!';

UPDATE vk_shop_bots SET 
    max_welcome_message_verified = 'Привет, {first_name}! 🍣 Добро пожаловать в «Везу Ролл»! Напишите: 1 - Хиты, 2 - Повторить заказ, 3 - Где заказ?, 4 - Бонусы' WHERE max_welcome_message_verified LIKE '%?%';
UPDATE vk_shop_bots SET 
    max_welcome_message_guest = 'Привет! 🍣 Добро пожаловать в доставку суши и роллов «Везу Ролл»! Напишите: 1 - Хиты, 2 - Повторить заказ, 3 - Где заказ?, 4 - Бонусы' WHERE max_welcome_message_guest LIKE '%?%';
UPDATE vk_shop_bots SET 
    max_status_check_template = 'Статус вашего заказа №{order_number}: {status_human}. Курьер: {courier_name}.' WHERE max_status_check_template LIKE '%?%';
