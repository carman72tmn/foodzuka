"""
Входящие вебхуки Т-Банка (T-API Webhooks)
"""
from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import PlainTextResponse
from datetime import datetime
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.order import Order, OrderStatus
from app.models.tbank_settings import TBankAccountStatement
import logging
from pydantic import BaseModel
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def send_admin_telegram_notification(message_text: str, db: Session):
    """
    Отправка Telegram-уведомления администратору о новом платеже СБП/T-Pay
    """
    try:
        from app.models.bot_settings import BotSettings
        from app.models.iiko_settings import IikoSettings
        import os
        import httpx
        
        # 1. Получаем токен бота
        bot_settings = db.exec(select(BotSettings)).first()
        token = bot_settings.telegram_bot_token if (bot_settings and bot_settings.telegram_bot_token) else os.getenv("TELEGRAM_BOT_TOKEN")
        
        # 2. Получаем ID чата администратора
        iiko_settings = db.exec(select(IikoSettings)).first()
        chat_id = iiko_settings.fallback_telegram_id if (iiko_settings and iiko_settings.fallback_telegram_id) else os.getenv("TELEGRAM_ADMIN_CHAT_ID")
        
        if not token or not chat_id:
            logger.warning(f"Propagating notification skipped: token or admin chat_id is missing (token: {'exists' if token else 'none'}, chat_id: {chat_id or 'none'})")
            return False
            
        logger.info(f"Sending Telegram notification to admin {chat_id}...")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message_text,
            "parse_mode": "HTML"
        }
        
        response = httpx.post(url, json=payload, timeout=5.0)
        if response.status_code == 200:
            logger.info("Telegram notification sent successfully to admin")
            return True
        else:
            logger.error(f"Failed to send Telegram notification: status {response.status_code}, response: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Telegram notification to admin: {str(e)}")
    return False

router = APIRouter(prefix="/tbank/webhooks", tags=["T-Bank Webhooks"])

# --- Schemas ---

class TBankPaymentWebhookSchema(BaseModel):
    TerminalKey: str
    OrderId: str
    Success: bool
    Status: str
    PaymentId: str
    Amount: int  # Сумма в копейках
    CardId: Optional[int] = None
    Pan: Optional[str] = None
    Token: Optional[str] = None
    ErrorCode: Optional[str] = None
    Message: Optional[str] = None
    Rrn: Optional[str] = None
    PaymentType: Optional[str] = None

class TBankSbpWebhookSchema(BaseModel):
    id: str  # ID QR-кода
    orderId: str
    status: str  # PAID, REJECTED, etc
    amount: float  # Сумма в рублях
    paymentDate: Optional[str] = None
    rrn: Optional[str] = None

class TBankAccountWebhookSchema(BaseModel):
    accountNumber: str
    chargeDate: str
    amount: float  # Сумма в рублях (положительная для прихода)
    paymentPurpose: str
    payerName: Optional[str] = None
    payerInn: Optional[str] = None
    payerAccount: Optional[str] = None
    payerBankBic: Optional[str] = None

# --- Helpers ---

def process_order_payment(db: Session, order_id_str: str, amount_rub: float, rrn: Optional[str] = None, method: str = "Card"):
    """Вспомогательная функция для обновления статуса оплаты заказа в БД"""
    try:
        # Пробуем найти заказ по ID (первичный ключ или номер заказа)
        order = None
        if order_id_str.isdigit():
            order = db.get(Order, int(order_id_str))
            
        if not order:
            # Ищем по номеру заказа, если в таблице есть поле order_number
            order = db.exec(select(Order).where(Order.id == int(order_id_str) if order_id_str.isdigit() else Order.id == 0)).first()
            
        if order:
            logger.info(f"Найден заказ #{order.id} для обновления оплаты на сумму {amount_rub} руб. через {method}")
            
            # Обновляем поля оплаты
            from decimal import Decimal
            current_paid = Decimal(str(getattr(order, "total_paid", 0.0) or 0.0))
            new_paid = current_paid + Decimal(str(amount_rub))
            
            setattr(order, "total_paid", new_paid)
            
            # Рассчитываем остаток к оплате
            total_with_discount = getattr(order, "total_with_discount", order.total_amount)
            left_to_pay = max(0.0, float(total_with_discount) - float(new_paid))
            setattr(order, "left_to_pay", left_to_pay)
            setattr(order, "is_paid", left_to_pay <= 0)
            
            # Добавляем инфо в payments_details
            pay_details = getattr(order, "payments_details", []) or []
            if not isinstance(pay_details, list):
                pay_details = []
            
            pay_details.append({
                "method": method,
                "amount": amount_rub,
                "rrn": rrn,
                "status": "CONFIRMED"
            })
            setattr(order, "payments_details", pay_details)
            
            # Логируем в комментарии к заказу
            comment = getattr(order, "comment", "") or ""
            new_comment = f"{comment}\n[T-API] Авто-оплата {amount_rub}₽ через {method}. RRN: {rrn or '-'}"
            setattr(order, "comment", new_comment.strip())
            
            db.add(order)
            db.commit()
            logger.info(f"Заказ #{order.id} успешно помечен как оплаченный. Итого оплачено: {new_paid} руб.")

            # Логируем оплату в Центр уведомлений
            try:
                from app.api.notifications import log_system_notification
                log_system_notification(
                    db=db,
                    title=f"Оплата заказа #{order.id}: +{amount_rub:,.0f} ₽".replace(",", " "),
                    subtitle=f"{method} • RRN: {rrn or '-'}",
                    body=f"Клиент: {order.customer_name or 'Гость'} ({order.customer_phone or '-'}) • Заказ #{order.id} оплачен",
                    event_type="tbank_payment",
                    category="tbank_payment",
                    url=f"/orders?order_id={order.id}",
                    badge_text=f"Т-Банк {method}",
                    badge_color="info",
                    amount=float(amount_rub),
                    order_id=order.id,
                    external_key=f"tbank_pay_{order.id}_{rrn or amount_rub}"
                )
            except Exception as notif_err:
                logger.warning(f"Error logging tbank payment notification: {notif_err}")
            
            # Запускаем фоновую задачу удаления сообщений с QR СБП в соцсетях
            try:
                from app.tasks.mailing_tasks import delete_shared_payment_qrs_task
                delete_shared_payment_qrs_task.delay(order.id)
            except Exception as e:
                logger.error(f"Failed to trigger delete_shared_payment_qrs_task: {e}")
                
            return True
        else:
            logger.warning(f"Заказ с ID {order_id_str} не найден в БД при обработке вебхука оплаты")
    except Exception as e:
        logger.error(f"Ошибка при обработке оплаты заказа #{order_id_str}: {str(e)}")
        db.rollback()
    return False

def find_best_matching_order(
    db: Session,
    amount: float,
    tx_date: datetime,
    terminal_key: Optional[str] = None,
    purpose: Optional[str] = None
) -> Optional[Order]:
    """
    Интеллектуальный поиск наиболее подходящего заказа iiko для автоматической привязки платежа.
    Сверка идет по сумме, времени проведения платежа/закрытия заказа и типу оплат.
    """
    import re
    from decimal import Decimal
    from datetime import timedelta, timezone
    from app.models.tbank_settings import TBankSettings
    
    # 1. Приводим дату транзакции к naive UTC для корректного сравнения с Order.created_at
    if tx_date.tzinfo is not None:
        tx_date_utc = tx_date.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        tx_date_utc = tx_date
        
    # 2. Ищем номера заказов в назначении платежа (если есть явное указание № заказа)
    if purpose:
        purpose_lower = purpose.lower()
        order_id_match = re.search(r'(?:заказ|заказа|№|\b)\s*#?(\d+)\b', purpose_lower)
        if order_id_match:
            order_id_str = order_id_match.group(1)
            if order_id_str.isdigit():
                order_id = int(order_id_str)
                order = db.get(Order, order_id)
                if order:
                    logger.info(f"Найдено явное указание заказа #{order.id} в назначении платежа: '{purpose}'")
                    return order

    # 3. Если явного номера нет, ищем заказы за диапазон времени
    # Ищем заказы от (tx_date - 3 часа) до (tx_date + 1 час)
    time_start = tx_date_utc - timedelta(hours=3)
    time_end = tx_date_utc + timedelta(hours=1)
    
    # Загружаем все потенциальные заказы за этот период
    orders_query = select(Order).where(
        Order.created_at >= time_start,
        Order.created_at <= time_end,
        Order.status != OrderStatus.cancelled
    )
    possible_orders = db.exec(orders_query).all()
    
    best_order = None
    max_score = -999.0
    
    # Получаем настройки терминалов из БД
    settings = db.exec(select(TBankSettings)).first()
    term_pickup = getattr(settings, "terminal_pickup", None) if settings else None
    term_delivery = getattr(settings, "terminal_delivery", None) if settings else None
    
    for order in possible_orders:
        # Исключаем заказы наличными
        is_cash = order.payment_method and "налич" in order.payment_method.lower()
        if is_cash:
            continue
            
        # Сумма заказа к оплате
        ord_sum = float(order.total_with_discount if order.total_with_discount is not None and order.total_with_discount > 0 else order.total_amount)
        
        # Разница сумм (допускаем только абсолютно точное совпадение до копейки)
        if abs(ord_sum - amount) >= 0.01:
            continue
            
        # Базовый приоритет
        score = 100.0
        
        # Разница во времени создания заказа и транзакции в секундах
        time_diff = abs((order.created_at - tx_date_utc).total_seconds())
        
        # Вычитаем 0.5 балла за каждую минуту разницы
        score -= (time_diff / 60.0) * 0.5
        
        # Приоритет заказам, которые еще не оплачены полностью
        current_paid = float(getattr(order, "total_paid", 0.0) or 0.0)
        if current_paid >= ord_sum:
            score -= 60.0  # сильный штраф, если уже оплачен, но все еще теоретически возможно
            
        # Привязка по типам оплат/терминалам (доставка vs самовывоз)
        if terminal_key:
            if term_pickup and terminal_key == term_pickup:
                if order.order_type == "Самовывоз":
                    score += 40.0
                elif order.order_type == "Доставка":
                    score -= 40.0
            elif term_delivery and terminal_key == term_delivery:
                if order.order_type == "Доставка":
                    score += 40.0
                elif order.order_type == "Самовывоз":
                    score -= 40.0
                    
        # Приоритет статусам заказа (уже закрытые или доставляемые заказы более вероятны)
        if order.status in [OrderStatus.closed, OrderStatus.delivered]:
            score += 15.0
        elif order.status == OrderStatus.new:
            score += 5.0
            
        if score > max_score and score > 0:
            max_score = score
            best_order = order
            
    if best_order:
        logger.info(f"Интеллектуальная сверка нашла лучший заказ #{best_order.id} (Сумма: {amount}₽, тип: {best_order.order_type}, статус: {best_order.status}, время: {best_order.created_at}, разница времени: {abs((best_order.created_at - tx_date_utc).total_seconds())/60:.1f} мин, Score: {max_score:.2f})")
        
    return best_order

# --- Webhook Endpoints ---

@router.post("/payment-status")
def handle_payment_status_webhook(
    data: TBankPaymentWebhookSchema,
    db: Session = Depends(get_session)
):
    """
    Вебхук статуса платежа эквайринга (Merchant API)
    Т-Банк шлет его при смене статуса транзакции.
    Сумма передается в копейках.
    """
    logger.info(f"Получен вебхук Merchant API: Терминал={data.TerminalKey}, Заказ={data.OrderId}, Статус={data.Status}, Сумма={data.Amount}коп.")
    
    # 1. Проверка цифровой подписи (Token), если задан пароль в настройках интернет-эквайринга
    if data.Token:
        try:
            from app.models.tbank_settings import TBankSettings
            settings = db.exec(select(TBankSettings)).first()
            if settings and settings.acquiring_password:
                raw_dict = data.model_dump() if hasattr(data, "model_dump") else data.dict()
                items = {k: v for k, v in raw_dict.items() if k not in ["Token", "token"] and v is not None and not isinstance(v, (dict, list))}
                items["Password"] = settings.acquiring_password
                sorted_str = "".join(str(items[k]) for k in sorted(items.keys()))
                import hashlib
                expected_token = hashlib.sha256(sorted_str.encode("utf-8")).hexdigest()
                if expected_token.lower() != data.Token.lower():
                    logger.warning(f"Внимание: не совпала SHA-256 подпись вебхука Т-Банка (получено: {data.Token}, вычислено: {expected_token})")
                else:
                    logger.info("Цифровая подпись вебхука Т-Банка (SHA-256 Token) успешно подтверждена")
        except Exception as e:
            logger.warning(f"Ошибка проверки подписи вебхука Т-Банка: {e}")

    if data.Success and data.Status == "CONFIRMED":
        # Переводим копейки в рубли
        amount_rub = data.Amount / 100.0
        real_rrn = data.Rrn or data.PaymentId or "-"
        
        # Определение точного метода оплаты (СБП, T-Pay, Карта)
        data_str = str(data.model_dump() if hasattr(data, "model_dump") else data.dict()).lower()
        if data.PaymentType == "QR" or "qr" in data_str or "sbp" in data_str:
            pm_title = "СБП"
            payer_name = f"СБП (QR {data.Pan or 'Оплата'})"
        elif "tpay" in data_str or "t-pay" in data_str:
            pm_title = "T-Pay"
            payer_name = f"T-Pay (Карта {data.Pan or '---'})"
        else:
            pm_title = "Эквайринг Т-Банк"
            payer_name = f"Карта {data.Pan or '---'}"
        
        # Обновляем статус оплаты в заказе
        process_order_payment(
            db=db,
            order_id_str=data.OrderId,
            amount_rub=amount_rub,
            rrn=real_rrn,
            method=pm_title
        )
        
        # Авто-регистрация реальной входящей транзакции в tbank_statements
        from datetime import datetime
        try:
            matched_id = int(data.OrderId) if data.OrderId.isdigit() else None
            
            # Проверяем на дубликаты по ID платежа или RRN
            existing = db.exec(
                select(TBankAccountStatement).where(
                    (TBankAccountStatement.payer_account == data.PaymentId) | (TBankAccountStatement.payer_account == real_rrn),
                    TBankAccountStatement.amount == float(amount_rub)
                )
            ).first()
            
            if not existing:
                db_op = TBankAccountStatement(
                    account_number=data.TerminalKey or "42734785",
                    charge_date=datetime.now(),
                    amount=float(amount_rub),
                    payment_purpose=f"Оплата {pm_title} по заказу #{data.OrderId}",
                    payer_name=payer_name,
                    payer_inn="",
                    payer_account=real_rrn,
                    payer_bank_bic="",
                    matched_order_id=matched_id
                )
                db.add(db_op)
                db.commit()
                logger.info(f"Реальный платеж эквайринга {amount_rub}руб. ({pm_title}, RRN: {real_rrn}) автоматически сохранен в tbank_statements")
                
                # Уведомление администратору в Telegram о новом платеже
                msg = (
                    f"💳 <b>Новый платеж ({pm_title})</b>\n"
                    f"💰 Сумма: <b>{amount_rub:.2f} ₽</b>\n"
                    f"📝 Заказ: <b>#{data.OrderId}</b>\n"
                    f"👤 Способ: {payer_name}\n"
                    f"🆔 Транзакция: {data.PaymentId}\n"
                    f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                )
                send_admin_telegram_notification(msg, db)
                
                # Мгновенная отправка WebSocket broadcast_sync в монитор Т-Банка
                try:
                    from app.api.chat import manager
                    ws_payload = {
                        "type": "new_bank_payment",
                        "amount": float(amount_rub),
                        "method": pm_title,
                        "customer": payer_name,
                        "order_id": matched_id,
                        "rrn": real_rrn
                    }
                    manager.broadcast_sync(ws_payload)
                    logger.info(f"WS broadcast_sync успешно отправлен: {ws_payload}")
                    
                    from app.services.iiko_sync_service import iiko_sync_service
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(iiko_sync_service.send_admin_push_notification(
                                session=db,
                                title="Поступление оплаты!",
                                body=f"Сумма: {amount_rub:.2f} ₽ ({pm_title}) | {payer_name}",
                                url="/admin/bank/tbank-payments",
                                event_type="new_payment",
                                tag=f"payment-{data.PaymentId}"
                            ))
                    except Exception:
                        pass
                except Exception as e:
                    logger.error(f"Failed to send websocket payment notification: {e}")
        except Exception as e:
            logger.error(f"Ошибка при авто-сохранении транзакции эквайринга по вебхуку: {str(e)}")
            db.rollback()
        
    # Ответ Т-Банку: строго текстовый "OK" для подтверждения успешного приема вебхука
    return PlainTextResponse("OK")

@router.post("/sbp-qr")
def handle_sbp_qr_webhook(
    data: TBankSbpWebhookSchema,
    db: Session = Depends(get_session)
):
    """
    Вебхук оплаты динамического QR СБП
    """
    logger.info(f"Получен вебхук СБП QR: ID={data.id}, Заказ={data.orderId}, Статус={data.status}, Сумма={data.amount}руб.")
    
    if data.status == "PAID":
        # Обновляем статус оплаты в заказе
        process_order_payment(
            db=db,
            order_id_str=data.orderId,
            amount_rub=data.amount,
            rrn=data.rrn,
            method="СБП (QR-код)"
        )
        
        # Авто-регистрация реальной входящей транзакции в tbank_statements
        from datetime import datetime
        try:
            matched_id = int(data.orderId) if data.orderId.isdigit() else None
            
            # Проверяем на дубликаты по ID QR-кода
            existing = db.exec(
                select(TBankAccountStatement).where(
                    TBankAccountStatement.payer_account == data.id,
                    TBankAccountStatement.amount == float(data.amount)
                )
            ).first()
            
            if not existing:
                db_op = TBankAccountStatement(
                    account_number="СБП (T-API)",
                    charge_date=datetime.now(),
                    amount=float(data.amount),
                    payment_purpose=f"Оплата СБП QR по заказу #{data.orderId} (T-Pay/СБП)",
                    payer_name="Физическое лицо (СБП)",
                    payer_inn="",
                    payer_account=data.id,  # ID QR-кода Т-Банка
                    payer_bank_bic="",
                    matched_order_id=matched_id
                )
                db.add(db_op)
                db.commit()
                logger.info(f"Реальный платеж СБП {data.amount}руб. по вебхуку автоматически сохранен в tbank_statements")
                
                # Уведомление администратору о новом платеже СБП
                msg = (
                    f"⚡️ <b>Новый платеж по СБП (T-Pay)</b>\n"
                    f"💰 Сумма: <b>{data.amount:.2f} ₽</b>\n"
                    f"📝 Заказ: <b>#{data.orderId}</b>\n"
                    f"👤 Способ: СБП (QR-код)\n"
                    f"🆔 QR ID: {data.id}\n"
                    f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                )
                send_admin_telegram_notification(msg, db)
                
                # Уведомление на WebSocket в админку в реальном времени
                try:
                    from app.api.chat import manager
                    ws_payload = {
                        "type": "new_bank_payment",
                        "amount": float(data.amount),
                        "method": "СБП (T-Pay)",
                        "customer": "Физическое лицо (СБП)",
                        "order_id": matched_id,
                        "rrn": data.rrn or data.id
                    }
                    manager.broadcast_sync(ws_payload)
                    logger.info(f"WS broadcast_sync СБП QR успешно отправлен: {ws_payload}")
                    
                    from app.services.iiko_sync_service import iiko_sync_service
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(iiko_sync_service.send_admin_push_notification(
                                session=db,
                                title="Поступление оплаты!",
                                body=f"Сумма: {data.amount:.2f} ₽ (СБП T-Pay) | Заказ #{matched_id or '---'}",
                                url="/admin/bank/tbank-payments",
                                event_type="new_payment",
                                tag=f"payment-sbp-{data.id}"
                            ))
                    except Exception:
                        pass
                except Exception as e:
                    logger.error(f"Failed to send websocket payment notification: {e}")
        except Exception as e:
            logger.error(f"Ошибка при авто-сохранении транзакции СБП по вебхуку: {str(e)}")
            db.rollback()
        
    return PlainTextResponse("OK")

@router.post("/account-info")
def handle_account_info_webhook(
    data: TBankAccountWebhookSchema,
    db: Session = Depends(get_session)
):
    """
    Вебхук движения по расчетным счетам (T-API Бизнес)
    Срабатывает при поступлении или списании со счета.
    Сумма положительная для входящего платежа.
    """
    logger.info(f"Получен вебхук Счета: Счет={data.accountNumber}, Сумма={data.amount}руб., Назначение='{data.paymentPurpose}'")
    
    # Обрабатываем только входящие переводы (сумма больше 0)
    if data.amount > 0:
        payer = (data.payerName or "").lower()
        purpose = data.paymentPurpose.lower()
        inn = (data.payerInn or "").strip()
        
        # 1. Зачисления от самого Банка (выплаты эквайринга, реестры, проценты, комиссии)
        is_bank_sender = (
            any(word in payer for word in ["т-банк", "тбанк", "t-bank", "tbank", "тинькофф", "tinkoff", "t-pay", "tpay"])
            or inn == "7710140679"
        ) and "физическое лицо" not in payer

        # Чисто служебные операции банка
        is_bank_service = any(word in purpose for word in [
            "реестр выплат", "реестр договоров", "комиссия за", "комиссионное вознаграждение", 
            "проценты по счету", "проценты на остаток", "плата за обслуживание", "абонентская плата"
        ])
        
        # Зачисление реестра по терминалам эквайринга от банка
        is_acquiring_settlement = "зачисление средств по терминалам" in purpose or "зачисление средств по операциям" in purpose or "выплата по терминалам" in purpose

        # 2. Признаки возвратов
        is_refund = "возврат" in purpose or "refund" in purpose

        # 3. Признаки B2B (другие юрлица и ИП)
        is_b2b = False
        has_corp_keywords = any(word in payer for word in [
            "ооо", "пао", "зао", " лтд", " ltd", "ип ", "ип.", "и.п.", "индивидуальный предприниматель"
        ])
        
        if inn:
            if len(inn) == 10 and inn != "7710140679":
                is_b2b = True
            elif len(inn) == 12 and has_corp_keywords and not is_bank_sender:
                is_b2b = True
        else:
            if has_corp_keywords and not is_bank_sender:
                is_b2b = True

        # Проверка назначения платежа на наличие фразы про доставку
        has_delivery_phrase = False
        delivery_keywords = ["доставк"]
        payment_keywords = ["плат", "оплат", "отплат"]
        if any(dk in purpose for dk in delivery_keywords) and any(pk in purpose for pk in payment_keywords):
            has_delivery_phrase = True

        # Признаки платежа физического лица (СБП, T-Pay, взносы наличных, пополнения через банкомат/кассу)
        is_retail_payment = any(word in purpose for word in [
            "сбп", "qr", "tpay", "t-pay", "эквайринг", "перевод от физ", "наличн", "пополнение", "взнос", "банкомат", "через atm", "vsp"
        ])

        # Сводим все правила сокрытия
        should_hide = False
        reason = ""
        if is_refund:
            should_hide = True
            reason = "возврат"
        elif is_bank_service:
            should_hide = True
            reason = "служебная операция банка"
        elif is_acquiring_settlement:
            should_hide = True
            reason = "зачисление реестра эквайринга"
        elif is_bank_sender:
            # Скрываем зачисления от самого банка, только если это не розничный платеж физлица и не оплата доставки
            if not (is_retail_payment or has_delivery_phrase):
                should_hide = True
                reason = "зачисление от банка (не розничный платеж)"
        elif is_b2b:
            # Скрываем переводы от юрлиц/ИП, только если это не розничный платеж и не доставка
            if not (is_retail_payment or has_delivery_phrase):
                should_hide = True
                reason = "B2B перевод от юрлица/ИП"

        if should_hide:
            logger.info(f"Вебхук движения по счету пропущен: {reason} | Назначение: '{purpose}' | Плательщик: '{payer}'")
            return PlainTextResponse("OK")

        is_payment = True
                
        # Форматируем имя плательщика
        p_name = data.payerName
        if is_payment and any(word in (p_name or "").lower() for word in ["т-банк", "тбанк", "t-bank", "tbank", "тинькофф", "tinkoff"]):
            if "сбп" in purpose or "qr" in purpose:
                p_name = "Физическое лицо (СБП)"
            elif "tpay" in purpose or "t-pay" in purpose:
                p_name = "Физическое лицо (T-Pay)"
            else:
                p_name = "Физическое лицо (Эквайринг)"

        # Авто-регистрация реальной входящей транзакции расчетного счета в tbank_statements
        from datetime import datetime
        try:
            charge_dt = datetime.fromisoformat(data.chargeDate.replace("Z", "+00:00"))
        except Exception:
            charge_dt = datetime.now()

        # Интеллектуальный поиск наилучшего заказа iiko по сумме, времени и назначению
        matched_order = find_best_matching_order(
            db=db,
            amount=data.amount,
            tx_date=charge_dt,
            terminal_key=None,
            purpose=data.paymentPurpose
        )
        
        matched_id = None
        if matched_order:
            matched_id = matched_order.id
            logger.info(f"Входящий платеж по расчетному счету {data.amount}₽ сопоставлен с заказом #{matched_order.id}")
        else:
            logger.info(f"Не удалось сопоставить платеж {data.amount}₽ от {p_name} по сумме/времени с заказами iiko")
            
        try:
            # Проверяем на дубликаты (счет, дата, сумма)
            existing = db.exec(
                select(TBankAccountStatement).where(
                    TBankAccountStatement.account_number == data.accountNumber,
                    TBankAccountStatement.charge_date == charge_dt,
                    TBankAccountStatement.amount == float(data.amount)
                )
            ).first()
            
            if not existing:
                db_op = TBankAccountStatement(
                    account_number=data.accountNumber,
                    charge_date=charge_dt,
                    amount=float(data.amount),
                    payment_purpose=data.paymentPurpose,
                    payer_name=p_name,
                    payer_inn=data.payerInn,
                    payer_account=data.payerAccount,
                    payer_bank_bic=data.payerBankBic,
                    matched_order_id=matched_id
                )
                db.add(db_op)
                db.commit()
                logger.info(f"Реальный платеж по счету {data.amount}руб. по вебхуку автоматически сохранен в tbank_statements")
                
                # Уведомление администратору о новом платеже по счету
                method_txt = "СБП" if ("сбп" in data.paymentPurpose.lower() or "qr" in data.paymentPurpose.lower()) else "T-Pay" if ("tpay" in data.paymentPurpose.lower() or "t-pay" in data.paymentPurpose.lower()) else "Перевод на счет"
                msg = (
                    f"🏦 <b>Новое поступление на расчетный счет</b>\n"
                    f"💰 Сумма: <b>{data.amount:.2f} ₽</b>\n"
                    f"👤 Плательщик: {p_name or 'Физическое лицо'}\n"
                    f"📝 Назначение: {data.paymentPurpose}\n"
                    f"💳 Способ: {method_txt}\n"
                    f"⏰ Время: {charge_dt.strftime('%d.%m.%Y %H:%M:%S')}"
                )
                send_admin_telegram_notification(msg, db)
                
                # Уведомление на WebSocket в админку в реальном времени
                try:
                    from app.api.chat import manager
                    import asyncio
                    ws_payload = {
                        "type": "new_bank_payment",
                        "amount": float(data.amount),
                        "method": method_txt,
                        "customer": p_name or "Физическое лицо",
                        "order_id": matched_id,
                        "rrn": data.payerAccount or (f"42734785{matched_id:04d}" if matched_id else "427347850000")
                    }
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(manager.broadcast(ws_payload))
                        from app.services.iiko_sync_service import iiko_sync_service
                        loop.create_task(iiko_sync_service.send_admin_push_notification(
                            session=db,
                            title="Поступление оплаты!",
                            body=f"Сумма: {data.amount:.2f} ₽ ({method_txt}) | {p_name or 'Физическое лицо'}",
                            url="/admin/bank/tbank-payments",
                            event_type="new_payment",
                            tag=f"payment-bank-{data.accountNumber}-{data.amount}-{data.chargeDate}"
                        ))
                except Exception as e:
                    logger.error(f"Failed to send websocket payment notification: {e}")
        except Exception as e:
            logger.error(f"Ошибка при авто-сохранении транзакции счета по вебхуку: {str(e)}")
            db.rollback()
            
    return PlainTextResponse("OK")
