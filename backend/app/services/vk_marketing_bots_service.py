import os
import random
import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlmodel import Session, select, text
import httpx

from app.models.order import Order
from app.models.customer import Customer
from app.models.vk_user import VkUser
from app.models.vk_bot_connection import VkBotConnection
from app.services.vk_service import send_vk_message
from app.services.max_service import send_max_message

logger = logging.getLogger(__name__)


class VkMarketingBotsService:
    """Сервис для работы 6 маркетинговых ботов (ВКонтакте + Мессенджер MAX от личного номера)"""

    # =========================================================================
    # 0. ОБЩИЙ ХЕЛПЕР ОТПРАВКИ В MAX ОТ ЛИЧНОГО НОМЕРА
    # =========================================================================

    @staticmethod
    async def send_marketing_max_personal(
        db: Session,
        phone: str,
        text_message: str,
        bot_type: str,
        customer_id: Optional[int] = None
    ) -> bool:
        """
        Отправляет маркетинговое сообщение клиенту в MAX СТРОГО от личного номера (Web Bridge)
        по номеру телефона и сохраняет запись в vk_bot_message_logs с channel='max'.
        """
        if not phone:
            return False

        try:
            res = await send_max_message(
                phone=phone,
                text=text_message,
                session=db,
                prefer_channel="bridge_only"
            )
            is_success = bool(res.get("success", False)) if isinstance(res, dict) else bool(res)

            status_enum = "SENT" if is_success else "FAILED"
            # Сохраняем в лог сообщений ботов с указанием канала 'max'
            db.execute(text(f"""
                INSERT INTO vk_bot_message_logs (account_id, event_type, text, status, channel, customer_phone, created_at, sent_at)
                VALUES (
                    (SELECT id FROM vk_bot_accounts LIMIT 1),
                    '{bot_type}',
                    '{text_message.replace("'", "''")[:250]}',
                    '{status_enum}',
                    'max',
                    '{phone}',
                    NOW(),
                    NOW()
                );
            """))
            db.commit()
            return is_success
        except Exception as e:
            logger.error(f"Ошибка отправки маркетингового сообщения в MAX от личного номера на {phone}: {e}")
            return False

    # =========================================================================
    # 1. VK & MAX SHOP BOT (КАТАЛОГ И ПОВТОР ЗАКАЗА)
    # =========================================================================

    @staticmethod
    def get_shop_keyboard(buttons_config: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Возвращает Reply-клавиатуру главного меню магазина для ВКонтакте"""
        if not buttons_config:
            return {
                "one_time": False,
                "inline": False,
                "buttons": [
                    [
                        {"action": {"type": "text", "label": "🍣 Хиты и Сеты", "payload": "{\"cmd\": \"shop_hits\"}"}, "color": "primary"},
                        {"action": {"type": "text", "label": "🔁 Повторить заказ", "payload": "{\"cmd\": \"repeat_order\"}"}, "color": "positive"}
                    ],
                    [
                        {"action": {"type": "text", "label": "🛵 Где мой заказ?", "payload": "{\"cmd\": \"order_status\"}"}, "color": "secondary"},
                        {"action": {"type": "text", "label": "💰 Мои бонусы", "payload": "{\"cmd\": \"my_bonuses\"}"}, "color": "secondary"}
                    ],
                    [
                        {"action": {"type": "text", "label": "🔥 Акции сегодня", "payload": "{\"cmd\": \"shop_promos\"}"}, "color": "secondary"},
                        {"action": {"type": "text", "label": "👨‍💼 Позвать оператора", "payload": "{\"cmd\": \"call_manager\"}"}, "color": "negative"}
                    ]
                ]
            }

        grid = []
        row = []
        for b in buttons_config:
            if not b.get("active", True):
                continue
            row.append({
                "action": {"type": "text", "label": b["text"], "payload": f"{{\"cmd\": \"{b['action']}\"}}"},
                "color": b.get("color", "secondary")
            })
            if len(row) == 2:
                grid.append(row)
                row = []
        if row:
            grid.append(row)
        return {"one_time": False, "inline": False, "buttons": grid}

    @staticmethod
    async def send_shop_main_menu(db: Session, conn: VkBotConnection, vk_id: int) -> bool:
        """Отправляет приветственное главное меню магазина в ВК"""
        token = conn.vk_bot_token or conn.bot_token
        if not token:
            return False

        cfg = db.execute(text(f"SELECT * FROM vk_shop_bots WHERE vk_bot_connection_id = {conn.id} LIMIT 1")).mappings().first()
        if not cfg or not cfg.get("is_active"):
            return False

        if not cfg.get("vk_enabled", True):
            return False

        if cfg.get("test_mode_only_admins"):
            admin_ids = cfg.get("test_admin_vk_ids") or []
            if vk_id not in admin_ids:
                return False

        cust = db.execute(text(f"SELECT * FROM customers WHERE vk_user_id = {vk_id} LIMIT 1")).mappings().first()
        keyboard = VkMarketingBotsService.get_shop_keyboard(cfg.get("menu_buttons"))

        if cust and cust.get("phone"):
            fname = cust.get("first_name") or cust.get("name") or "друг"
            lname = cust.get("last_name") or cust.get("surname") or ""
            bonuses = int(cust.get("bonus_points") or 0)
            tmpl = cfg.get("welcome_message_verified") or "Привет, {first_name}! 🍣 Выберите действие в меню ниже:"
            msg = tmpl.replace("{first_name}", fname).replace("{last_name}", lname).replace("{bonus_balance}", str(bonuses))
        else:
            msg = cfg.get("welcome_message_guest") or "Привет! 🍣 Добро пожаловать в доставку суши и роллов «Везу Ролл»!"

        attachment = cfg.get("welcome_photo_vk_id")
        return await send_vk_message(vk_id, msg, token, keyboard=keyboard, attachment=attachment)

    @staticmethod
    async def handle_shop_command(
        db: Session,
        conn: VkBotConnection,
        vk_id: int,
        cmd: str,
        user_name: str = "Гость"
    ) -> bool:
        """Обрабатывает команды интерактивного меню VkShopBot в ВК"""
        token = conn.vk_bot_token or conn.bot_token
        if not token:
            return False

        cfg = db.execute(text(f"SELECT * FROM vk_shop_bots WHERE vk_bot_connection_id = {conn.id} LIMIT 1")).mappings().first()
        if not cfg or not cfg.get("is_active"):
            return False

        if not cfg.get("vk_enabled", True):
            return False

        if cfg.get("test_mode_only_admins"):
            admin_ids = cfg.get("test_admin_vk_ids") or []
            if vk_id not in admin_ids:
                return False

        keyboard = VkMarketingBotsService.get_shop_keyboard(cfg.get("menu_buttons"))

        if cmd in ("shop_hits", "carousel"):
            prods = db.execute(text("SELECT id, name, price FROM products WHERE is_available = true ORDER BY id DESC LIMIT 5")).mappings().all()
            if prods:
                lines = ["🍣 ТОП ПОПУЛЯРНЫХ БЛЮД:\n"]
                for i, p in enumerate(prods, 1):
                    lines.append(f"{i}. {p['name']} — {int(p['price'])} ₽")
                lines.append("\n👉 Оформить заказ: https://vezuroll.ru")
                text_msg = "\n".join(lines)
            else:
                text_msg = "🍣 Ознакомьтесь с нашим меню на сайте: https://vezuroll.ru"
            await send_vk_message(vk_id, text_msg, token, keyboard=keyboard)
            return True

        elif cmd == "repeat_order":
            order = db.execute(text(f"""
                SELECT o.id, o.external_number, o.total_amount, o.created_at
                FROM orders o
                JOIN customers c ON c.id = o.customer_id
                WHERE c.vk_user_id = {vk_id}
                ORDER BY o.created_at DESC LIMIT 1
            """)).mappings().first()

            if order:
                num = order.get("external_number") or order["id"]
                amt = int(order.get("total_amount") or 0)
                dt = order["created_at"].strftime("%d.%m.%Y")
                msg = f"🔁 Ваш предыдущий заказ №{num} от {dt} на сумму {amt} ₽.\n\nПовторить его с доставкой на тот же адрес?"
                inline_kb = {
                    "inline": True,
                    "buttons": [[
                        {"action": {"type": "text", "label": "✅ Да, повторить заказ", "payload": f"{{\"cmd\":\"confirm_repeat\",\"order_id\":{order['id']}}}"}, "color": "positive"},
                        {"action": {"type": "text", "label": "❌ Другие блюда", "payload": "{\"cmd\":\"shop_hits\"}"}, "color": "secondary"}
                    ]]
                }
                await send_vk_message(vk_id, msg, token, keyboard=inline_kb)
            else:
                msg = "У вас пока не было завершенных заказов. Попробуйте наши популярные сеты из меню:"
                await send_vk_message(vk_id, msg, token, keyboard=keyboard)
            return True

        elif cmd in ("order_status", "status_iiko"):
            order = db.execute(text(f"""
                SELECT o.id, o.external_number, o.status, o.created_at
                FROM orders o
                JOIN customers c ON c.id = o.customer_id
                WHERE c.vk_user_id = {vk_id}
                ORDER BY o.created_at DESC LIMIT 1
            """)).mappings().first()

            if order:
                num = order.get("external_number") or order["id"]
                st = order.get("status") or "В обработке"
                template = cfg.get("status_check_template") or "Статус вашего заказа №{order_number}: {status_human}. Курьер: {courier_name}."
                msg = template.replace("{order_number}", str(num)).replace("{status_human}", st).replace("{courier_name}", "Назначен")
            else:
                msg = "Активных заказов не найдено. Вы можете оформить заказ прямо сейчас на сайте vezuroll.ru!"
            await send_vk_message(vk_id, msg, token, keyboard=keyboard)
            return True

        elif cmd in ("my_bonuses", "bonus_balance"):
            cust = db.execute(text(f"SELECT bonus_points FROM customers WHERE vk_user_id = {vk_id} LIMIT 1")).mappings().first()
            pts = int(cust.get("bonus_points") or 0) if cust else 0
            max_pct = cfg.get("max_bonus_payment_percent", 30) or 30
            msg = f"💰 На вашем бонусном балансе: {pts} баллов!\n1 бонус = 1 рубль скидки. Вы можете оплатить бонусами до {max_pct}% суммы заказа."
            await send_vk_message(vk_id, msg, token, keyboard=keyboard)
            return True

        elif cmd == "shop_promos":
            msg = "🔥 Акции сегодня:\n- Скидка 10% на первый заказ из ВК!\n- Сет «Филадельфия Микс» всего 1190 ₽ вместо 1490 ₽.\n- Бонусы за каждый заказ!"
            await send_vk_message(vk_id, msg, token, keyboard=keyboard)
            return True

        elif cmd in ("call_manager", "operator"):
            msg = "👨‍💼 Мы уведомили администратора! Скоро оператор подключится к диалогу и ответит на все вопросы."
            await send_vk_message(vk_id, msg, token, keyboard=keyboard)
            return True

        return False

    @staticmethod
    async def handle_max_shop_command(
        db: Session,
        phone: str,
        cmd: str,
        user_name: str = "Гость"
    ) -> bool:
        """
        Обрабатывает текстовые команды магазина от пользователя в мессенджере MAX
        и отвечает СТРОГО от личного номера Web Bridge.
        """
        cfg = db.execute(text("SELECT * FROM vk_shop_bots WHERE is_active = true AND max_enabled = true LIMIT 1")).mappings().first()
        if not cfg:
            return False

        clean_cmd = cmd.strip().lower()

        # Меню / Старт
        if clean_cmd in ("меню", "начать", "start", "привет", "заказ", "роллы", "суши"):
            cust = db.execute(text(f"SELECT * FROM customers WHERE phone LIKE '%{phone[-10:]}%' LIMIT 1")).mappings().first()
            if cust:
                fname = cust.get("first_name") or cust.get("name") or "друг"
                tmpl = cfg.get("max_welcome_message_verified") or "Привет, {first_name}! 🍣 Добро пожаловать в «Везу Ролл»!\nНапишите:\n1 - Хиты и сеты\n2 - Повторить заказ\n3 - Где мой заказ?\n4 - Мои бонусы"
                msg = tmpl.replace("{first_name}", fname)
            else:
                msg = cfg.get("max_welcome_message_guest") or "Привет! 🍣 Добро пожаловать в доставку суши и роллов «Везу Ролл»!\nНапишите:\n1 - Хиты и сеты\n2 - Повторить заказ\n3 - Где мой заказ?\n4 - Мои бонусы"
            return await VkMarketingBotsService.send_marketing_max_personal(db, phone, msg, "shop")

        # 1 - Хиты
        elif clean_cmd in ("1", "хиты", "сеты", "меню роллов"):
            prods = db.execute(text("SELECT id, name, price FROM products WHERE is_available = true ORDER BY id DESC LIMIT 5")).mappings().all()
            if prods:
                lines = ["🍣 ТОП ПОПУЛЯРНЫХ БЛЮД:\n"]
                for i, p in enumerate(prods, 1):
                    lines.append(f"{i}. {p['name']} — {int(p['price'])} ₽")
                lines.append("\n👉 Оформить заказ с доставкой: https://vezuroll.ru")
                text_msg = "\n".join(lines)
            else:
                text_msg = "🍣 Ознакомьтесь с нашим меню на сайте: https://vezuroll.ru"
            return await VkMarketingBotsService.send_marketing_max_personal(db, phone, text_msg, "shop")

        # 2 - Повторить заказ
        elif clean_cmd in ("2", "повторить", "повтор", "повторить заказ"):
            order = db.execute(text(f"""
                SELECT o.id, o.external_number, o.total_amount, o.created_at
                FROM orders o
                JOIN customers c ON c.id = o.customer_id
                WHERE c.phone LIKE '%{phone[-10:]}%'
                ORDER BY o.created_at DESC LIMIT 1
            """)).mappings().first()
            if order:
                num = order.get("external_number") or order["id"]
                amt = int(order.get("total_amount") or 0)
                dt = order["created_at"].strftime("%d.%m.%Y")
                msg = f"🔁 Ваш прошлый заказ №{num} от {dt} на сумму {amt} ₽.\nДля быстрого повтора перейдите на сайт https://vezuroll.ru или напишите нашему оператору!"
            else:
                msg = "У вас пока не было завершенных заказов. Ознакомьтесь с нашими сетами на сайте vezuroll.ru!"
            return await VkMarketingBotsService.send_marketing_max_personal(db, phone, msg, "shop")

        # 3 - Статус заказа
        elif clean_cmd in ("3", "статус", "где заказ", "где мой заказ"):
            order = db.execute(text(f"""
                SELECT o.id, o.external_number, o.status, o.created_at
                FROM orders o
                JOIN customers c ON c.id = o.customer_id
                WHERE c.phone LIKE '%{phone[-10:]}%'
                ORDER BY o.created_at DESC LIMIT 1
            """)).mappings().first()
            if order:
                num = order.get("external_number") or order["id"]
                st = order.get("status") or "В обработке"
                template = cfg.get("max_status_check_template") or "Статус вашего заказа №{order_number}: {status_human}. Курьер: {courier_name}."
                msg = template.replace("{order_number}", str(num)).replace("{status_human}", st).replace("{courier_name}", "Назначен")
            else:
                msg = "Активных заказов не найдено. Вы можете оформить заказ прямо сейчас на сайте vezuroll.ru!"
            return await VkMarketingBotsService.send_marketing_max_personal(db, phone, msg, "shop")

        # 4 - Баланс бонусов
        elif clean_cmd in ("4", "бонусы", "мой баланс", "баллы"):
            cust = db.execute(text(f"SELECT bonus_points FROM customers WHERE phone LIKE '%{phone[-10:]}%' LIMIT 1")).mappings().first()
            pts = int(cust.get("bonus_points") or 0) if cust else 0
            msg = f"💰 На вашем бонусном балансе: {pts} баллов! (1 бонус = 1 рубль скидки при заказе на vezuroll.ru)"
            return await VkMarketingBotsService.send_marketing_max_personal(db, phone, msg, "shop")

        return False

    # =========================================================================
    # 2. VK & MAX REVIEW NPS BOT (КОНТРОЛЬ КАЧЕСТВА И ОТЗЫВЫ)
    # =========================================================================

    @staticmethod
    async def handle_nps_rating(
        db: Session,
        conn: VkBotConnection,
        vk_id: int,
        rating: int,
        order_id: Optional[int] = None
    ) -> bool:
        """Обрабатывает нажатие кнопки оценки ⭐ 1-5 в ВКонтакте"""
        token = conn.vk_bot_token or conn.bot_token
        if not token:
            return False

        cfg = db.execute(text(f"SELECT * FROM vk_review_nps_bots WHERE vk_bot_connection_id = {conn.id} LIMIT 1")).mappings().first()
        if not cfg or not cfg.get("is_active"):
            return False

        threshold = int(cfg.get("positive_rating_threshold", 4) or 4)

        db.execute(text(f"""
            INSERT INTO vk_order_nps_reviews (order_id, vk_id, rating, channel, created_at)
            VALUES ({order_id or 'NULL'}, {vk_id}, {rating}, 'vk', NOW());
        """))
        db.commit()

        if rating >= threshold:
            msg = cfg.get("msg_positive") or "Спасибо за высокую оценку! ❤️ Опубликуйте фото заказа на стене с #отзыв_везуролл и получите +100 бонусов!"
            await send_vk_message(vk_id, msg, token)
        else:
            msg = cfg.get("msg_negative") or "Нам очень жаль, что блюда не порадовали 😔 Пожалуйста, напишите, что именно пошло не так (можно прикрепить фото) — сообщение сразу передается руководству!"
            db.execute(text(f"""
                INSERT INTO vk_bot_user_states (vk_id, state, current_step, updated_at)
                VALUES ({vk_id}, 'awaiting_nps_feedback', {rating}, NOW())
                ON CONFLICT (vk_id) DO UPDATE SET state = 'awaiting_nps_feedback', current_step = {rating}, updated_at = NOW();
            """))
            db.commit()
            await send_vk_message(vk_id, msg, token)

        return True

    @staticmethod
    async def handle_nps_text_feedback(
        db: Session,
        conn: VkBotConnection,
        vk_id: int,
        feedback_text: str
    ) -> bool:
        """Перехватывает текст жалобы клиента при низкой оценке в ВК"""
        token = conn.vk_bot_token or conn.bot_token
        if not token:
            return False

        cfg = db.execute(text(f"SELECT * FROM vk_review_nps_bots WHERE vk_bot_connection_id = {conn.id} LIMIT 1")).mappings().first()

        db.execute(text(f"""
            UPDATE vk_order_nps_reviews
            SET feedback_text = '{feedback_text.replace("'", "''")}', is_resolved = false
            WHERE vk_id = {vk_id} AND feedback_text IS NULL;
        """))
        db.execute(text(f"DELETE FROM vk_bot_user_states WHERE vk_id = {vk_id};"))
        db.commit()

        thank_you = cfg.get("msg_negative_thank_you") if cfg else "Спасибо за сигнал! Управляющий уже разбирается в ситуации."
        await send_vk_message(vk_id, thank_you, token)

        if cfg and cfg.get("alert_admin_vk_ids"):
            alert_msg = f"🚨 СРОЧНО! Негативный отзыв от VK ID {vk_id}:\n«{feedback_text}»\nПроверьте в админ-панели!"
            for admin_id in cfg["alert_admin_vk_ids"]:
                try:
                    await send_vk_message(int(admin_id), alert_msg, token)
                except Exception as e:
                    logger.warning(f"Не удалось отправить алерт админу {admin_id}: {e}")

        return True

    @staticmethod
    async def handle_max_nps_rating(
        db: Session,
        phone: str,
        rating: int,
        order_id: Optional[int] = None
    ) -> bool:
        """Обрабатывает оценку 1-5, присланную клиентом в мессенджере MAX от личного номера"""
        cfg = db.execute(text("SELECT * FROM vk_review_nps_bots WHERE is_active = true AND max_enabled = true LIMIT 1")).mappings().first()
        if not cfg:
            return False

        threshold = int(cfg.get("positive_rating_threshold", 4) or 4)

        # Привязываем к клиенту
        cust = db.execute(text(f"SELECT id FROM customers WHERE phone LIKE '%{phone[-10:]}%' LIMIT 1")).mappings().first()
        c_id = cust["id"] if cust else "NULL"

        db.execute(text(f"""
            INSERT INTO vk_order_nps_reviews (order_id, rating, channel, customer_phone, customer_id, created_at)
            VALUES ({order_id or 'NULL'}, {rating}, 'max', '{phone}', {c_id}, NOW());
        """))
        db.commit()

        if rating >= threshold:
            msg = cfg.get("max_msg_positive") or "Спасибо за высокую оценку! ❤️ Рады стараться для вас!"
            await VkMarketingBotsService.send_marketing_max_personal(db, phone, msg, "nps")
        else:
            msg = cfg.get("max_msg_negative") or "Нам очень жаль, что блюда не порадовали 😔 Пожалуйста, напишите в ответ, что именно пошло не так — сообщение сразу передается руководству!"
            await VkMarketingBotsService.send_marketing_max_personal(db, phone, msg, "nps")

            # Алерт управляющим в MAX
            alert_phones = cfg.get("max_alert_admin_phones") or []
            if isinstance(alert_phones, list) and len(alert_phones) > 0:
                alert_text = f"🚨 ВНИМАНИЕ! Низкая оценка ({rating} ⭐) от клиента {phone} в MAX. Проверьте карточку в CRM!"
                for ap in alert_phones:
                    await VkMarketingBotsService.send_marketing_max_personal(db, str(ap), alert_text, "nps")

        return True

    # =========================================================================
    # 3. VK & MAX WHEEL OF FORTUNE BOT (КОЛЕСО ФОРТУНЫ)
    # =========================================================================

    @staticmethod
    def spin_wheel(sectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Определяет сектор выигрыша по весам вероятности (%)"""
        if not sectors:
            return {"title": "Скидка 10%", "val": "FORTUNA10", "type": "promo"}
        weights = [float(s.get("weight", 10) or 10) for s in sectors]
        chosen = random.choices(sectors, weights=weights, k=1)[0]
        return chosen

    @staticmethod
    async def spin_wheel_for_user(
        db: Session,
        conn: VkBotConnection,
        vk_id: int,
        source: str = "dm"
    ) -> bool:
        """Запуск Колеса Фортуны для гостя (в ЛС или комментарии)"""
        token = conn.vk_bot_token or conn.bot_token
        if not token:
            return False

        cfg = db.execute(text(f"SELECT * FROM vk_wheel_bots WHERE vk_bot_connection_id = {conn.id} LIMIT 1")).mappings().first()
        if not cfg or not cfg.get("is_active"):
            return False

        # Проверка лимита прокруток за сегодня
        today_spins = db.execute(text(f"""
            SELECT COUNT(id) FROM vk_wheel_spins
            WHERE vk_id = {vk_id} AND created_at >= NOW() - INTERVAL '24 hours'
        """)).scalar() or 0

        free_spins = int(cfg.get("daily_free_spins", 1) or 1)
        if today_spins >= free_spins:
            msg = f"Вы уже использовали свои бесплатные попытки на сегодня ({free_spins}/{free_spins}). Возвращайтесь завтра или сделайте заказ от {cfg.get('extra_spin_order_sum', 1200)} ₽, чтобы получить VIP-спин!"
            await send_vk_message(vk_id, msg, token)
            return True

        sectors = cfg.get("sectors_config") or []
        prize = VkMarketingBotsService.spin_wheel(sectors)

        expires_at = datetime.utcnow() + timedelta(hours=int(cfg.get("prize_valid_hours", 48) or 48))
        
        db.execute(text(f"""
            INSERT INTO vk_wheel_spins (wheel_bot_id, vk_id, prize_name, promo_code, is_used, channel, expires_at, created_at)
            VALUES ({cfg['id']}, {vk_id}, '{prize.get("title", "Приз").replace("'", "''")}', '{prize.get("val", "PROMO").replace("'", "''")}', false, 'vk', '{expires_at.strftime("%Y-%m-%d %H:%M:%S")}', NOW());
        """))
        db.commit()

        template = cfg.get("msg_dm_win_template") or "🎉 Поздравляем! Вы выиграли «{prize_name}»! Ваш промокод: {promo_code} (действует 48ч)."
        win_msg = template.replace("{prize_name}", prize.get("title", "Приз")).replace("{promo_code}", prize.get("val", "PROMO")).replace("{valid_until}", "48 часов")
        await send_vk_message(vk_id, win_msg, token)

        # Если включен MAX и у гостя есть телефон — дублируем выигрыш в MAX от личного номера
        if cfg.get("max_enabled", False):
            cust = db.execute(text(f"SELECT phone FROM customers WHERE vk_user_id = {vk_id} LIMIT 1")).mappings().first()
            if cust and cust.get("phone"):
                max_tmpl = cfg.get("max_msg_dm_win_template") or "🎉 Поздравляем! Ваш выигрыш в Колесе: «{prize_name}»! Промокод: {promo_code} на vezuroll.ru"
                max_msg = max_tmpl.replace("{prize_name}", prize.get("title", "Приз")).replace("{promo_code}", prize.get("val", "PROMO")).replace("{valid_until}", "48ч")
                await VkMarketingBotsService.send_marketing_max_personal(db, cust["phone"], max_msg, "wheel")

        return True

    # =========================================================================
    # 4. VK & MAX REFERRAL BOT (ПРИВЕДИ ДРУГА)
    # =========================================================================

    @staticmethod
    def get_referral_code(vk_id: int) -> str:
        """Генерирует персональный код амбассадора"""
        return f"VR-{abs(vk_id) % 90000 + 10000}"

    @staticmethod
    async def handle_referral_command(
        db: Session,
        conn: VkBotConnection,
        vk_id: int,
        ref_param: Optional[str] = None
    ) -> bool:
        """Обрабатывает выдачу реферальной ссылки или переход по ссылке друга"""
        token = conn.vk_bot_token or conn.bot_token
        if not token:
            return False

        cfg = db.execute(text(f"SELECT * FROM vk_referral_programs WHERE vk_bot_connection_id = {conn.id} LIMIT 1")).mappings().first()
        if not cfg or not cfg.get("is_active"):
            return False

        group_id = abs(int(conn.vk_group_id))

        # А. Если пользователь пришел по реферальной ссылке (ref=VR-XXXXX)
        if ref_param and ref_param.startswith("VR-"):
            code = ref_param.strip()
            referrer = db.execute(text(f"SELECT referrer_vk_id FROM vk_referral_links WHERE referral_code = '{code}' LIMIT 1")).mappings().first()
            if referrer and referrer["referrer_vk_id"] != vk_id:
                # Фиксируем связку
                db.execute(text(f"""
                    INSERT INTO vk_referral_links (referrer_vk_id, referral_code, invited_vk_id, status, reward_granted, channel, created_at)
                    VALUES ({referrer['referrer_vk_id']}, '{code}', {vk_id}, 'registered', false, 'vk', NOW())
                    ON CONFLICT DO NOTHING;
                """))
                db.commit()

            friend_bonus = cfg.get("friend_bonus_points", 250)
            friend_min_sum = cfg.get("friend_min_order_sum", 1000)
            template = cfg.get("msg_friend_welcome") or "Привет! Ваш друг дарит вам {friend_bonus_points} бонусов на первый заказ от {friend_min_order_sum} ₽! 🎁"
            msg = template.replace("{friend_bonus_points}", str(friend_bonus)).replace("{friend_min_order_sum}", str(friend_min_sum))
            await send_vk_message(vk_id, msg, token)
            return True

        # Б. Пользователь запросил свою ссылку амбассадора
        ref_code = VkMarketingBotsService.get_referral_code(vk_id)
        # Сохраняем в базу код амбассадора
        existing = db.execute(text(f"SELECT id FROM vk_referral_links WHERE referrer_vk_id = {vk_id} LIMIT 1")).scalar()
        if not existing:
            db.execute(text(f"""
                INSERT INTO vk_referral_links (referrer_vk_id, referral_code, status, reward_granted, channel, created_at)
                VALUES ({vk_id}, '{ref_code}', 'created', false, 'vk', NOW());
            """))
            db.commit()

        friend_bonus = cfg.get("friend_bonus_points", 250)
        ref_reward = cfg.get("referrer_reward_points", 300)
        template = cfg.get("msg_ambassador_info") or "Ваша реферальная ссылка: https://vk.com/write-{group_id}?ref={referral_code}.\nПригласите друзей — они получат {friend_bonus_points} бонусов, а вы получите {referrer_reward_points} бонусов за их первый заказ!"
        msg = template.replace("{referral_code}", ref_code).replace("{friend_bonus_points}", str(friend_bonus)).replace("{referrer_reward_points}", str(ref_reward)).replace("{group_id}", str(group_id))
        await send_vk_message(vk_id, msg, token)

        # Если включен MAX, информируем амбассадора также в MAX
        if cfg.get("max_enabled", False):
            cust = db.execute(text(f"SELECT phone FROM customers WHERE vk_user_id = {vk_id} LIMIT 1")).mappings().first()
            if cust and cust.get("phone"):
                max_tmpl = cfg.get("max_msg_ambassador_info") or "Ваш промокод амбассадора: {referral_code}. Пригласите друзей и получите +{referrer_reward_points} бонусов!"
                max_msg = max_tmpl.replace("{referral_code}", ref_code).replace("{referrer_reward_points}", str(ref_reward))
                await VkMarketingBotsService.send_marketing_max_personal(db, cust["phone"], max_msg, "referral")

        return True

    # =========================================================================
    # 5. МАРШРУТИЗАЦИЯ ВХОДЯЩИХ СООБЩЕНИЙ ИЗ MAX (ЛИЧНЫЙ НОМЕР)
    # =========================================================================

    @staticmethod
    async def handle_max_incoming_message(
        db: Session,
        peer_id: str,
        text_message: str,
        user_name: str = "Гость"
    ) -> bool:
        """
        Главный маршрутизатор входящих сообщений в мессенджере MAX от личного номера:
        1. Проверяет, не является ли текст числовой оценкой 1..5 для NPS.
        2. Проверяет, не является ли текст запросом меню / каталога (1..4, 'меню').
        """
        if not text_message:
            return False

        stripped = text_message.strip()

        # 1. Проверка оценки NPS (1, 2, 3, 4, 5 или ⭐1..⭐5)
        clean_num = stripped.replace("⭐", "").replace("звезд", "").replace("баллов", "").strip()
        if clean_num in ("1", "2", "3", "4", "5"):
            try:
                rate = int(clean_num)
                handled = await VkMarketingBotsService.handle_max_nps_rating(db, peer_id, rate)
                if handled:
                    return True
            except Exception as e:
                logger.error(f"Error handling MAX NPS number: {e}")

        # 2. Проверка команд меню магазина
        return await VkMarketingBotsService.handle_max_shop_command(db, peer_id, stripped, user_name)
