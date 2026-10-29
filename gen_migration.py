import psycopg2
import sys

# Run directly on VPS through a python script
sql = """
-- VkShopBot
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS trigger_keywords jsonb DEFAULT '["меню", "начать", "start", "каталог", "заказать", "роллы"]'::jsonb;
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS welcome_message_verified text DEFAULT 'Привет, {first_name}! 🍣 Выберите действие в меню ниже:';
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS welcome_message_guest text DEFAULT 'Привет! 🍣 Добро пожаловать в доставку суши и роллов «Везу Ролл»!';
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS welcome_photo_url varchar(255);
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS carousel_source_mode varchar(50) DEFAULT 'auto_top_sales';
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS hide_stop_list_items boolean DEFAULT true;
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS card_button_1_mode varchar(50) DEFAULT 'add_to_vk_cart';
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS enable_repeat_order boolean DEFAULT true;
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS repeat_order_lookback_count integer DEFAULT 3;
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS allow_bonus_payment_in_bot boolean DEFAULT true;
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS order_creation_mode varchar(50) DEFAULT 'direct_iiko_and_db';
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS status_check_template text DEFAULT 'Статус вашего заказа №{order_number}: {status_human}. Курьер: {courier_name}.';
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS test_mode_only_admins boolean DEFAULT false;
ALTER TABLE vk_shop_bots ADD COLUMN IF NOT EXISTS test_admin_vk_ids jsonb DEFAULT '[]'::jsonb;

-- VkRetentionBot
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS newbie_enabled boolean DEFAULT true;
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS sleeping_enabled boolean DEFAULT true;
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS lost_vip_enabled boolean DEFAULT true;
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS newbie_gift_mode varchar(50) DEFAULT 'promo_code';
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS sleeping_gift_mode varchar(50) DEFAULT 'expiring_iiko_points';
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS lost_vip_gift_mode varchar(50) DEFAULT 'both';
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS newbie_promo_code varchar(100) DEFAULT 'VTOROY15';
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS sleeping_promo_code varchar(100) DEFAULT 'MISSYOU';
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS lost_vip_promo_code varchar(100) DEFAULT 'VIPBACK';
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS enable_expiring_bonuses boolean DEFAULT true;
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS send_burn_reminder boolean DEFAULT true;
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS burn_reminder_hours_before integer DEFAULT 24;
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS burn_reminder_template text DEFAULT '⏰ {first_name}, уже завтра в {expire_time} у вас сгорят {bonus_amount} подарочных бонусов!';
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS run_time_local varchar(10) DEFAULT '16:30';
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS min_cooldown_days_between_touches integer DEFAULT 14;
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS test_mode_only_admins boolean DEFAULT false;
ALTER TABLE vk_retention_bots ADD COLUMN IF NOT EXISTS test_admin_vk_ids jsonb DEFAULT '[]'::jsonb;

-- VkReviewNpsBot
ALTER TABLE vk_review_nps_bots ADD COLUMN IF NOT EXISTS min_order_amount_for_nps integer DEFAULT 500;
ALTER TABLE vk_review_nps_bots ADD COLUMN IF NOT EXISTS required_review_hashtag varchar(100) DEFAULT '#отзыв_везуролл';
ALTER TABLE vk_review_nps_bots ADD COLUMN IF NOT EXISTS require_photo_attachment boolean DEFAULT true;
ALTER TABLE vk_review_nps_bots ADD COLUMN IF NOT EXISTS max_paid_reviews_per_month integer DEFAULT 4;
ALTER TABLE vk_review_nps_bots ADD COLUMN IF NOT EXISTS msg_negative_thank_you text DEFAULT 'Спасибо! Ваше обращение передано управляющему.';
ALTER TABLE vk_review_nps_bots ADD COLUMN IF NOT EXISTS auto_tag_multichat boolean DEFAULT true;
ALTER TABLE vk_review_nps_bots ADD COLUMN IF NOT EXISTS alert_admin_vk_ids jsonb DEFAULT '[]'::jsonb;
ALTER TABLE vk_review_nps_bots ADD COLUMN IF NOT EXISTS auto_apology_promo_code varchar(100);
ALTER TABLE vk_review_nps_bots ADD COLUMN IF NOT EXISTS test_mode_only_admins boolean DEFAULT false;
ALTER TABLE vk_review_nps_bots ADD COLUMN IF NOT EXISTS test_admin_vk_ids jsonb DEFAULT '[]'::jsonb;

-- VkWheelOfFortuneBot
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS contest_post_id integer;
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS require_group_member boolean DEFAULT true;
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS require_post_like boolean DEFAULT true;
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS require_messages_allowed boolean DEFAULT true;
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS free_spins_period varchar(50) DEFAULT 'per_day';
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS wheel_bg_image_url varchar(255);
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS draw_user_avatar_in_center boolean DEFAULT true;
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS prize_valid_hours integer DEFAULT 48;
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS remind_unused_prize boolean DEFAULT true;
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS remind_before_expire_hours integer DEFAULT 24;
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS msg_dm_win_template text DEFAULT '🎉 Поздравляем! Ваш выигрыш: {prize_name}. Промокод: {promo_code}. Действует 48 часов!';
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS msg_dm_reminder_template text DEFAULT '🔥 {first_name}, ваш выигрыш «{prize_name}» сгорит через 24 часа! Успейте заказать!';
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS test_mode_only_admins boolean DEFAULT false;
ALTER TABLE vk_wheel_bots ADD COLUMN IF NOT EXISTS test_admin_vk_ids jsonb DEFAULT '[]'::jsonb;

-- VkSmartBroadcastBot
ALTER TABLE vk_smart_broadcasts ADD COLUMN IF NOT EXISTS happy_hours_days_of_week jsonb DEFAULT '["Пн", "Вт", "Ср", "Чт"]'::jsonb;
ALTER TABLE vk_smart_broadcasts ADD COLUMN IF NOT EXISTS happy_hours_check_time varchar(10) DEFAULT '14:00';
ALTER TABLE vk_smart_broadcasts ADD COLUMN IF NOT EXISTS happy_hours_lookback_hours integer DEFAULT 2;
ALTER TABLE vk_smart_broadcasts ADD COLUMN IF NOT EXISTS min_orders_threshold integer DEFAULT 8;
ALTER TABLE vk_smart_broadcasts ADD COLUMN IF NOT EXISTS happy_hours_batch_size integer DEFAULT 150;
ALTER TABLE vk_smart_broadcasts ADD COLUMN IF NOT EXISTS happy_hours_template text DEFAULT '🍣 {first_name}, только сегодня с 14:00 до 17:00 скидка 20% по промокоду ОБЕД!';
ALTER TABLE vk_smart_broadcasts ADD COLUMN IF NOT EXISTS test_mode_only_admins boolean DEFAULT false;
ALTER TABLE vk_smart_broadcasts ADD COLUMN IF NOT EXISTS test_admin_vk_ids jsonb DEFAULT '[]'::jsonb;

-- VkReferralBot
ALTER TABLE vk_referral_programs ADD COLUMN IF NOT EXISTS trigger_command jsonb DEFAULT '["пригласить друга", "рефералка", "друг"]'::jsonb;
ALTER TABLE vk_referral_programs ADD COLUMN IF NOT EXISTS friend_reward_type varchar(50) DEFAULT 'iiko_points';
ALTER TABLE vk_referral_programs ADD COLUMN IF NOT EXISTS max_referrals_per_user_month integer DEFAULT 10;
ALTER TABLE vk_referral_programs ADD COLUMN IF NOT EXISTS antifraud_strict_new_customer boolean DEFAULT true;
ALTER TABLE vk_referral_programs ADD COLUMN IF NOT EXISTS generate_invite_image boolean DEFAULT true;
ALTER TABLE vk_referral_programs ADD COLUMN IF NOT EXISTS msg_ambassador_info text DEFAULT 'Ваша реферальная ссылка: https://vk.com/write-186688777?ref={referral_code}. Вы пригласили: {invited_count} друзей.';
ALTER TABLE vk_referral_programs ADD COLUMN IF NOT EXISTS msg_friend_welcome text DEFAULT 'Привет! Ваш друг дарит вам {friend_bonus_points} бонусов на первый заказ!';
ALTER TABLE vk_referral_programs ADD COLUMN IF NOT EXISTS msg_referrer_reward_paid text DEFAULT '🎉 Ура! Ваш друг {friend_name} получил заказ! Вам начислено +{referrer_reward_points} бонусов!';
ALTER TABLE vk_referral_programs ADD COLUMN IF NOT EXISTS test_mode_only_admins boolean DEFAULT false;
ALTER TABLE vk_referral_programs ADD COLUMN IF NOT EXISTS test_admin_vk_ids jsonb DEFAULT '[]'::jsonb;
"""

with open(r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\migrate_6_bots.sql", "w", encoding="utf-8") as f:
    f.write(sql)

print("Migration SQL generated")
