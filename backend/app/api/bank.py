"""
API эндпоинты для банковских операций и сверки платежей
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from app.core.database import get_session
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.models.tbank_settings import TBankSettings, TBankAccountStatement
from app.api import deps
from app.core.datetime_utils import get_tz_name, to_local, get_day_boundaries
from app.core.tbank_utils import get_terminal_display_name

router = APIRouter(prefix="/bank", tags=["Bank Operations"])


def parse_date_param(val: Any) -> Optional[date]:
    """Безопасный парсер даты из строки, date или None"""
    if not val:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        val = val.strip()
        if not val or val.lower() in ("none", "null", "undefined", ""):
            return None
        try:
            return datetime.strptime(val[:10], "%Y-%m-%d").date()
        except Exception:
            try:
                return datetime.fromisoformat(val).date()
            except Exception:
                return None
    return None


class ManualMatchRequest(BaseModel):
    statement_id: int
    order_id: int


class UnmatchRequest(BaseModel):
    statement_id: int


class UpdatePaymentMethodRequest(BaseModel):
    payment_method: str


@router.get("/payments", response_model=List[Dict[str, Any]])
def get_bank_payments(
    date_from: Optional[str] = Query(None, description="Начало периода (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Конец периода (YYYY-MM-DD)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Статус сверки: matched, discrepancy, unmatched_bank, unmatched_order"),
    search: Optional[str] = Query(None, description="Поиск по клиенту, заказу или транзакции"),
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_payments_view", "bank_tbank_payments_view")),
):
    """
    Получить абсолютно все входящие банковские и наличные платежи с результатами автоматической сверки с iiko.
    """
    payments = []

    # Получаем локальный часовой пояс организации
    tz_name = get_tz_name(session)
    tbank_settings = session.exec(select(TBankSettings)).first()

    parsed_date_from = parse_date_param(date_from)
    parsed_date_to = parse_date_param(date_to)

    # 1. Загружаем реальные выписки из tbank_statements с фильтрацией по дате
    stmt_query = select(TBankAccountStatement)
    if parsed_date_from:
        start_utc, _ = get_day_boundaries(parsed_date_from.strftime("%Y-%m-%d"), tz_name)
        stmt_query = stmt_query.where(TBankAccountStatement.charge_date >= start_utc)
    if parsed_date_to:
        _, end_utc = get_day_boundaries(parsed_date_to.strftime("%Y-%m-%d"), tz_name)
        stmt_query = stmt_query.where(TBankAccountStatement.charge_date <= end_utc)
        
    statements = session.exec(stmt_query).all()
    
    # Приоритет сортировки: реальные проводки POS-терминалов и транзакции с реальным RRN идут первыми
    def _statement_priority(s):
        acc = (s.account_number or "").strip()
        is_pos = acc.isdigit() and len(acc) >= 8
        has_real_rrn = s.payer_account and str(s.payer_account).strip().isdigit() and len(str(s.payer_account).strip()) >= 10
        if is_pos or has_real_rrn:
            return 0
        return 1

    sorted_statements = sorted(statements, key=_statement_priority)
    seen_matched_statement_orders = set()
    
    for stmt in sorted_statements:
        # Для входящих платежей (amount > 0)
        if stmt.amount <= 0:
            continue
            
        # Строгая дедупликация: для одного заказа iiko выводим только одну наиболее приоритетную проводку
        if stmt.matched_order_id:
            if stmt.matched_order_id in seen_matched_statement_orders:
                continue
            seen_matched_statement_orders.add(stmt.matched_order_id)
            
        payer = (stmt.payer_name or "").lower()
        purpose = (stmt.payment_purpose or "").lower()
        inn = (stmt.payer_inn or "").strip()
        
        # 1. Зачисления от самого Банка (выплаты эквайринга, реестры, проценты, комиссии)
        is_bank_sender = (
            any(word in payer for word in ["т-банк", "тбанк", "t-bank", "tbank", "тинькофф", "tinkoff"])
            or inn == "7710140679"
        )

        # Чисто служебные операции банка
        is_bank_service = any(word in purpose for word in [
            "реестр выплат", "реестр договоров", "реестр операций", "реестр за",
            "комиссия за", "комиссионное вознаграждение", "удержание комиссии", "списание комиссии",
            "проценты по счету", "проценты на остаток", "плата за обслуживание", "абонентская плата"
        ])
        
        # Зачисление реестра по терминалам эквайринга от банка (сводные выплаты)
        is_acquiring_settlement = any(word in purpose for word in [
            "зачисление средств по терминалам", "зачисление средств по операциям", "выплата по терминалам",
            "выплата по операциям эквайринга", "выплата возмещения", "возмещение по торговому эквайрингу",
            "возмещение по эквайрингу", "перечисление выручки", "перечисление возмещения", "зачисление выручки",
            "по договору эквайринга", "по договору интернет-эквайринга", "по операциям с использованием карт",
            "зачисление средств по договору"
        ])

        # 2. Признаки возвратов
        is_refund = "возврат" in purpose or "refund" in purpose

        # 3. Признаки B2B (другие юрлица и ИП)
        is_b2b = False
        has_corp_keywords = any(word in payer for word in [
            "ооо", "пао", "зао", "ао ", " лтд", " ltd", "ип ", "ип.", "и.п.", "индивидуальный предприниматель"
        ])
        
        if inn:
            if len(inn) == 10 and inn != "7710140679":
                is_b2b = True
            elif len(inn) == 12 and has_corp_keywords and not is_bank_sender:
                is_b2b = True
        else:
            if has_corp_keywords and not is_bank_sender:
                is_b2b = True

        # Проверка назначения платежа на явный заказ
        has_order_phrase = False
        if any(word in purpose for word in ["заказ", "заказа", "доставк", "foodzuka", "фудзука", "оплата заказа", "оплата по сбп"]):
            has_order_phrase = True

        # Признаки платежа физического лица
        is_retail_payment = any(word in purpose for word in [
            "сбп", "qr", "tpay", "t-pay", "перевод от физ", "оплата"
        ])

        # Сводим все правила сокрытия служебных зачислений (сводные реестры банка)
        should_hide = False
        if is_refund:
            should_hide = True
        elif is_bank_service:
            should_hide = True
        elif is_acquiring_settlement:
            should_hide = True
        elif is_bank_sender:
            if not (is_retail_payment or has_order_phrase or stmt.matched_order_id):
                should_hide = True
        elif is_b2b:
            if not (has_order_phrase or is_retail_payment or stmt.matched_order_id):
                should_hide = True

        if should_hide:
            continue
            
        acc_str = (stmt.account_number or "").lower()
        purpose_lower = purpose
        
        # Точное определение метода оплаты из выписки Т-Банка
        if any(w in purpose_lower for w in ["сбп", "qr", "dovezuka"]) or "сбп" in acc_str or "пополнение по операции сбп" in purpose_lower:
            method = "СБП"
        elif "tpay" in purpose_lower or "t-pay" in purpose_lower or "tpay" in acc_str:
            method = "T-Pay"
        elif any(w in purpose_lower or w in acc_str for w in ["эквайринг", "карт", "терминал", "pos", "t bank", "t-bank", "т-банк", "т банк", "tbank", "42734785", "онлайн"]) or ((stmt.account_number or "").strip().isdigit() and len((stmt.account_number or "").strip()) <= 12):
            method = "Эквайринг"
        else:
            method = "Перевод"
        
        # Находим сопоставленный заказ
        order_amount = 0.0
        order_number = "-"
        order_phone = ""
        status = "unmatched_bank"
        order_obj = None
        
        if stmt.matched_order_id:
            order_obj = session.get(Order, stmt.matched_order_id)
            if order_obj:
                order_amount = float(order_obj.total_with_discount if order_obj.total_with_discount is not None and order_obj.total_with_discount > 0 else order_obj.total_amount)
                order_number = order_obj.external_number or f"№{order_obj.id}"
                order_phone = order_obj.customer_phone or ""
                
                # Если в заказе зафиксирован уточненный способ оплаты (например СБП или T-Pay), берем его
                if isinstance(order_obj.payments_details, dict) and order_obj.payments_details.get("actual_payment_method"):
                    method = order_obj.payments_details["actual_payment_method"]
                
                # Проверяем совпадение сумм
                if abs(float(stmt.amount) - order_amount) < 0.01:
                    status = "matched"
                else:
                    status = "discrepancy"
                
        # Переводим дату операции в локальное время организации
        stmt_local_dt = to_local(stmt.charge_date, tz_name) if stmt.charge_date else to_local(datetime.now(timezone.utc), tz_name)
                
        # Извлечение и нормализация РЕАЛЬНОГО RRN из выписки / транзакции Т-Банка
        import re
        stmt_rrn = "-"
        sbp_match = re.search(r'СБП\s+(\d+)', stmt.payment_purpose or "", re.IGNORECASE)
        raw_rrn = (stmt.payer_account or "").strip()
        
        if sbp_match:
            stmt_rrn = sbp_match.group(1)
        elif raw_rrn and raw_rrn.lower() not in ["iiko-sync", "-", "none", "null", "онлайн", "online", "undefined", "30232810600003197537"] and not raw_rrn.startswith("427347852") and not raw_rrn.startswith("427347850"):
            stmt_rrn = raw_rrn

        acc_num = (stmt.account_number or "").strip()
        terminal_label = get_terminal_display_name(acc_num, sbp_acc=purpose_lower, settings=tbank_settings)

        payments.append({
            "id": f"stmt_{stmt.id}",
            "statement_id": stmt.id,
            "date": stmt_local_dt.isoformat(),
            "order_id": stmt.matched_order_id,
            "order_number": order_number,
            "customer_name": (order_obj.customer_name if order_obj and order_obj.customer_name else stmt.payer_name) or "Клиент",
            "customer_phone": order_phone,
            "bank_amount": float(stmt.amount),
            "order_amount": order_amount,
            "payment_method": method,
            "terminal_label": terminal_label,
            "bank_name": "Т-Банк",
            "transaction_id": f"STMT{stmt.id:06d}",
            "rrn": stmt_rrn,
            "status": status,
            "is_real": True,
            "description": f"Операция банка ({terminal_label}, {method}). Назначение: {stmt.payment_purpose or 'Оплата'}",
            "source_type": "bank_statement",
            "payment_purpose": stmt.payment_purpose or "",
            "payer_account": stmt.payer_account or "",
            "payer_inn": stmt.payer_inn or "",
            "delivery_address": order_obj.delivery_address if order_obj else "",
            "courier_name": order_obj.courier_name if order_obj else ""
        })

    # 2. Загружаем заказы из iiko: СТРОГО только переводы и наличные на кассе!
    query = select(Order).order_by(Order.created_at.desc())
    
    # Фильтрация по датам создания заказов
    if parsed_date_from:
        start_utc, _ = get_day_boundaries(parsed_date_from.strftime("%Y-%m-%d"), tz_name)
        query = query.where(Order.created_at >= start_utc)
    if parsed_date_to:
        _, end_utc = get_day_boundaries(parsed_date_to.strftime("%Y-%m-%d"), tz_name)
        query = query.where(Order.created_at <= end_utc)
        
    orders = session.exec(query).all()
    
    for order in orders:
        order_amount = float(order.total_with_discount if order.total_with_discount is not None and order.total_with_discount > 0 else order.total_amount)
        order_local_dt = to_local(order.created_at, tz_name) if order.created_at else to_local(datetime.now(timezone.utc), tz_name)
        
        # Если этот заказ уже сопоставлен с реальным банковским платежом Т-Банка, пропускаем дубль
        if order.id in seen_matched_statement_orders:
            continue
            
        # Пропускаем отмененные заказы
        if order.status == "cancelled":
            continue

        pm_lower = (order.payment_method or "").lower()
        is_cash = "налич" in pm_lower
        is_transfer = "перевод" in pm_lower
        is_paid_val = float(order.total_paid or 0.0)
        
        # Заказ считается оплаченным ТОЛЬКО ЕСЛИ он явно закрыт или оплачен в iiko
        order_is_paid_in_iiko = bool(order.is_paid or order.status in [OrderStatus.closed, "closed"] or is_paid_val > 0)
        
        # Если заказ еще НЕ оплачен в iiko - он ни в коем случае не может считаться завершенным поступлением!
        if not order_is_paid_in_iiko:
            if status_filter == "unmatched_order":
                payments.append({
                    "id": f"unmatched_ord_{order.id}",
                    "statement_id": None,
                    "date": order_local_dt.isoformat(),
                    "order_id": order.id,
                    "order_number": order.external_number or f"№{order.id}",
                    "customer_name": order.customer_name or "Гость",
                    "customer_phone": order.customer_phone or "",
                    "bank_amount": 0.0,
                    "order_amount": order_amount,
                    "payment_method": order.payment_method or "Не указан",
                    "terminal_label": "Ожидает оплату",
                    "bank_name": "-",
                    "transaction_id": "-",
                    "rrn": "-",
                    "status": "unmatched_order",
                    "is_real": False,
                    "description": f"Заказ iiko (#{order.external_number or order.id}), ожидает поступления оплаты",
                    "source_type": "iiko_order",
                    "payment_purpose": f"Заказ iiko #{order.external_number or order.id}",
                    "payer_account": "",
                    "payer_inn": "",
                    "delivery_address": order.delivery_address or "",
                    "courier_name": order.courier_name or ""
                })
            continue

        is_card_tbank = (
            is_paid_val > 0 and 
            pm_lower not in ["", "не указан", "none", "null"] and 
            any(w in pm_lower for w in ["t bank", "t-bank", "т-банк", "т банк", "tbank", "картой", "карта", "сбп", "qr", "эквайринг"])
        )
        
        if is_cash:
            # Наличные на кассе / курьеру из iiko
            payments.append({
                "id": f"cash_{order.id}",
                "statement_id": None,
                "date": order_local_dt.isoformat(),
                "order_id": order.id,
                "order_number": order.external_number or f"№{order.id}",
                "customer_name": order.customer_name or "Гость",
                "customer_phone": order.customer_phone or "",
                "bank_amount": order_amount,
                "order_amount": order_amount,
                "payment_method": "Наличные",
                "terminal_label": "Касса (Наличные)",
                "bank_name": "Касса iiko",
                "transaction_id": f"CASH{order.id:06d}",
                "rrn": "-",
                "status": "matched",
                "is_real": True,
                "description": f"Оплата наличными по заказу iiko #{order.external_number or order.id} ({order.customer_name or 'Гость'})",
                "source_type": "iiko_order",
                "payment_purpose": f"Оплата наличными по заказу iiko #{order.external_number or order.id}",
                "payer_account": "",
                "payer_inn": "",
                "delivery_address": order.delivery_address or "",
                "courier_name": order.courier_name or ""
            })
        elif is_transfer:
            # Оплата переводом от клиента из iiko
            payments.append({
                "id": f"tr_{order.id}",
                "statement_id": None,
                "date": order_local_dt.isoformat(),
                "order_id": order.id,
                "order_number": order.external_number or f"№{order.id}",
                "customer_name": order.customer_name or "Гость",
                "customer_phone": order.customer_phone or "",
                "bank_amount": order_amount,
                "order_amount": order_amount,
                "payment_method": "Перевод",
                "terminal_label": "Перевод клиентом",
                "bank_name": "Перевод (iiko)",
                "transaction_id": f"TR{order.id:06d}",
                "rrn": "-",
                "status": "matched",
                "is_real": True,
                "description": f"Оплата переводом по заказу iiko #{order.external_number or order.id} ({order.customer_name or 'Гость'})",
                "source_type": "iiko_order",
                "payment_purpose": f"Оплата переводом по заказу iiko #{order.external_number or order.id}",
                "payer_account": "",
                "payer_inn": "",
                "delivery_address": order.delivery_address or "",
                "courier_name": order.courier_name or ""
            })
        elif is_card_tbank:
            # Подтвержденная оплата картой / эквайрингом Т-Банка (например, в приложении)
            actual_pm = None
            if isinstance(order.payments_details, dict):
                actual_pm = order.payments_details.get("actual_payment_method")

            comment_lower = (order.comment or "").lower()
            if actual_pm:
                ord_method = actual_pm
            elif any(w in pm_lower for w in ["сбп", "qr"]) or any(w in comment_lower for w in ["сбп", "sbp"]):
                ord_method = "СБП"
            elif any(w in pm_lower for w in ["tpay", "t-pay"]) or any(w in comment_lower for w in ["tpay", "t-pay", "t pay"]):
                ord_method = "T-Pay"
            else:
                ord_method = "Эквайринг"

            payments.append({
                "id": f"card_ord_{order.id}",
                "statement_id": None,
                "date": order_local_dt.isoformat(),
                "order_id": order.id,
                "order_number": order.external_number or f"№{order.id}",
                "customer_name": order.customer_name or "Гость",
                "customer_phone": order.customer_phone or "",
                "bank_amount": is_paid_val,
                "order_amount": order_amount,
                "payment_method": ord_method,
                "terminal_label": f"Т-Банк ({ord_method})" if ord_method in ["СБП", "T-Pay"] else (order.payment_method or f"Т-Банк ({ord_method})"),
                "bank_name": "Т-Банк" if ord_method in ["СБП", "T-Pay"] else "Т-Банк (Эквайринг)",
                "transaction_id": f"ORD{order.id:06d}",
                "rrn": "-",
                "status": "matched",
                "is_real": True,
                "description": f"Оплата через {ord_method} по заказу iiko #{order.external_number or order.id} ({order.customer_name or 'Гость'})",
                "source_type": "iiko_order",
                "payment_purpose": f"Оплата {ord_method} по заказу iiko #{order.external_number or order.id}",
                "payer_account": "",
                "payer_inn": "",
                "delivery_address": order.delivery_address or "",
                "courier_name": order.courier_name or ""
            })
        elif status_filter == "unmatched_order":
            # Для остальных несопоставленных заказов iiko отображаем только при явном фильтре "unmatched_order" в реестре сверки
            payments.append({
                "id": f"unmatched_ord_{order.id}",
                "statement_id": None,
                "date": order_local_dt.isoformat(),
                "order_id": order.id,
                "order_number": order.external_number or f"№{order.id}",
                "customer_name": order.customer_name or "Гость",
                "customer_phone": order.customer_phone or "",
                "bank_amount": 0.0,
                "order_amount": order_amount,
                "payment_method": order.payment_method or "Безналичный",
                "terminal_label": "Ожидает банк",
                "bank_name": "-",
                "transaction_id": "-",
                "rrn": "-",
                "status": "unmatched_order",
                "is_real": False,
                "description": f"Заказ iiko (#{order.external_number or order.id}), ожидается проводка Т-Банка",
                "source_type": "iiko_order",
                "payment_purpose": f"Заказ iiko #{order.external_number or order.id}",
                "payer_account": "",
                "payer_inn": "",
                "delivery_address": order.delivery_address or "",
                "courier_name": order.courier_name or ""
            })
        
    # Сортировка по дате (новые вверху)
    payments.sort(key=lambda x: x["date"], reverse=True)
    
    # Фильтрация по статусу
    if status_filter and isinstance(status_filter, str) and status_filter.lower() != "all":
        payments = [p for p in payments if p.get("status") == status_filter]
        
    # Поиск по текстовому запросу
    if search and isinstance(search, str) and search.strip():
        s = search.strip().lower()
        payments = [
            p for p in payments
            if (p.get("customer_name") and s in p["customer_name"].lower()) or
               (p.get("customer_phone") and s in p["customer_phone"].lower()) or
               (p.get("order_number") and s in p["order_number"].lower()) or
               (p.get("transaction_id") and s in p["transaction_id"].lower()) or
               (p.get("rrn") and s in p["rrn"].lower()) or
               (p.get("bank_name") and s in p["bank_name"].lower()) or
               (p.get("payment_method") and s in p["payment_method"].lower()) or
               (p.get("payment_purpose") and s in p["payment_purpose"].lower()) or
               (str(p.get("bank_amount", "")) and s in str(p["bank_amount"])) or
               (str(p.get("order_amount", "")) and s in str(p["order_amount"]))
        ]
        
    return payments


@router.post("/manual-match", response_model=Dict[str, Any])
def manual_match_payment(
    data: ManualMatchRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_payments_edit", "bank_tbank_payments_edit")),
):
    """
    Ручная привязка банковской транзакции выписки к конкретному заказу iiko.
    """
    stmt = session.get(TBankAccountStatement, data.statement_id)
    if not stmt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Банковская транзакция не найдена")
        
    order = session.get(Order, data.order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
        
    stmt.matched_order_id = order.id
    session.add(stmt)
    session.commit()
    
    return {
        "success": True,
        "message": f"Транзакция #{stmt.id} успешно привязана к заказу #{order.external_number or order.id}"
    }


@router.post("/unmatch", response_model=Dict[str, Any])
def unmatch_payment(
    data: UnmatchRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_payments_edit", "bank_tbank_payments_edit")),
):
    """
    Отвязать банковскую транзакцию от заказа.
    """
    stmt = session.get(TBankAccountStatement, data.statement_id)
    if not stmt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Банковская транзакция не найдена")
        
    old_order_id = stmt.matched_order_id
    stmt.matched_order_id = None
    session.add(stmt)
    session.commit()
    
    return {
        "success": True,
        "message": f"Транзакция #{stmt.id} успешно отвязана от заказа #{old_order_id or '-'}"
    }


@router.get("/search-orders-for-match", response_model=List[Dict[str, Any]])
def search_orders_for_match(
    query: Optional[str] = Query(None, description="Номер заказа, телефон или имя"),
    amount: Optional[float] = Query(None, description="Сумма для поиска"),
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_payments_view", "bank_tbank_payments_view")),
):
    """
    Поиск заказов для модального окна ручной привязки.
    """
    tz_name = get_tz_name(session)
    stmt = select(Order).order_by(Order.created_at.desc()).limit(30)
    
    if query and query.strip():
        q = query.strip()
        stmt = stmt.where(
            (Order.external_number.ilike(f"%{q}%")) |
            (Order.customer_name.ilike(f"%{q}%")) |
            (Order.customer_phone.ilike(f"%{q}%"))
        )
    elif amount and amount > 0:
        min_a = amount * 0.9
        max_a = amount * 1.1
        stmt = stmt.where(
            ((Order.total_with_discount >= min_a) & (Order.total_with_discount <= max_a)) |
            ((Order.total_amount >= min_a) & (Order.total_amount <= max_a))
        )
        
    orders = session.exec(stmt).all()
    result = []
    for ord in orders:
        ord_amt = float(ord.total_with_discount if ord.total_with_discount is not None and ord.total_with_discount > 0 else ord.total_amount)
        ord_local_dt = to_local(ord.created_at, tz_name) if ord.created_at else to_local(datetime.now(timezone.utc), tz_name)
        result.append({
            "id": ord.id,
            "external_number": ord.external_number or f"№{ord.id}",
            "customer_name": ord.customer_name or "Гость",
            "customer_phone": ord.customer_phone or "",
            "total_amount": ord_amt,
            "total_paid": float(ord.total_paid) if ord.total_paid else 0.0,
            "payment_method": ord.payment_method or "Не указан",
            "is_paid": bool(ord.is_paid),
            "status": ord.status,
            "created_at": ord_local_dt.strftime("%d.%m.%Y %H:%M"),
            "delivery_address": ord.delivery_address or ""
        })
    return result


@router.post("/auto-match", response_model=Dict[str, Any])
def auto_match_payments(
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_payments_edit", "bank_tbank_payments_edit")),
):
    """
    Запустить автоматическое связывание несвязанных входящих банковских платежей с заказами iiko.
    """
    # 1. Находим несвязанные входящие операции (amount > 0 и matched_order_id IS NULL)
    stmt_query = select(TBankAccountStatement).where(
        TBankAccountStatement.amount > 0,
        TBankAccountStatement.matched_order_id == None
    )
    unmatched_statements = session.exec(stmt_query).all()
    
    matched_count = 0
    
    # 2. Для каждой несвязанной транзакции ищем подходящий заказ
    for stmt in unmatched_statements:
        payer = (stmt.payer_name or "").lower()
        purpose = (stmt.payment_purpose or "").lower()
        inn = (stmt.payer_inn or "").strip()
        
        # Исключаем системные и B2B транзакции из автоматического сопоставления
        has_delivery_phrase = False
        delivery_keywords = ["доставк"]
        payment_keywords = ["плат", "оплат", "отплат"]
        if any(dk in purpose for dk in delivery_keywords) and any(pk in purpose for pk in payment_keywords):
            has_delivery_phrase = True

        is_retail_payment = any(word in purpose for word in [
            "сбп", "qr", "tpay", "t-pay", "эквайринг", "перевод от физ", "наличн", "пополнение", "взнос", "банкомат", "через atm", "vsp", "оплата"
        ])

        is_tbank = any(word in payer for word in ["т-банк", "t-bank", "тинькофф", "tinkoff"])
        is_b2b = (len(inn) == 10) or any(word in payer for word in ["ооо", "ао ", "пао ", "зао ", " лтд", " ltd", "ип ", "ип.", "и.п.", "индивидуальный предприниматель"])
        is_refund = "возврат" in purpose or "refund" in purpose
        is_bank_service = any(word in purpose for word in ["процент на остаток", "комисси", "плата за обслуживание", "плата за пополнение", "реестр выплат", "реестр договоров", "комиссионное вознаграждение", "абонентская плата"])
        
        should_skip = False
        if is_refund or is_bank_service:
            should_skip = True
        elif is_tbank and not (is_retail_payment or has_delivery_phrase):
            should_skip = True
        elif is_b2b and not (is_retail_payment or has_delivery_phrase):
            should_skip = True

        if should_skip:
            continue
            
        # Запускаем интеллектуальный матчинг по сумме и времени
        from app.api.tbank_webhooks import find_best_matching_order, process_order_payment
        matched_order = find_best_matching_order(
            db=session,
            amount=float(stmt.amount),
            tx_date=stmt.charge_date,
            terminal_key=stmt.account_number,
            purpose=stmt.payment_purpose
        )
        
        if matched_order:
            stmt.matched_order_id = matched_order.id
            session.add(stmt)
            matched_count += 1
                
    if matched_count > 0:
        session.commit()
        
    return {
        "success": True,
        "checked_unmatched": len(unmatched_statements),
        "matched_count": matched_count
    }


@router.patch("/payments/{payment_id}/method", response_model=Dict[str, Any])
def update_payment_method(
    payment_id: str,
    data: UpdatePaymentMethodRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_payments_edit", "bank_tbank_payments_edit")),
):
    """
    Уточнение / переключение метода оплаты (СБП, T-Pay, Эквайринг, Перевод)
    с автоматическим сохранением и WebSocket-оповещением.
    """
    new_method = data.payment_method.strip()
    updated_order_id = None
    
    # 1. Если это заказ (card_ord_123, tr_123, cash_123, ORD000123 или просто число)
    order_id_cand = None
    if payment_id.startswith("card_ord_"):
        order_id_cand = int(payment_id.replace("card_ord_", ""))
    elif payment_id.startswith("tr_"):
        order_id_cand = int(payment_id.replace("tr_", ""))
    elif payment_id.startswith("cash_"):
        order_id_cand = int(payment_id.replace("cash_", ""))
    elif payment_id.startswith("ORD") and payment_id[3:].isdigit():
        order_id_cand = int(payment_id[3:])
    elif payment_id.startswith("stmt_"):
        stmt_id = int(payment_id.replace("stmt_", ""))
        stmt = session.get(TBankAccountStatement, stmt_id)
        if stmt:
            stmt.payment_purpose = f"Оплата {new_method} (уточнено вручную)"
            if new_method in ["СБП", "T-Pay"]:
                stmt.account_number = f"{new_method} (T-API)"
            session.add(stmt)
            if stmt.matched_order_id:
                order_id_cand = stmt.matched_order_id
    elif payment_id.isdigit():
        order_id_cand = int(payment_id)
        
    if order_id_cand:
        order = session.get(Order, order_id_cand)
        if order:
            updated_order_id = order.id
            pd = order.payments_details or {}
            if isinstance(pd, dict):
                pd_copy = dict(pd)
            else:
                pd_copy = {"items": pd} if isinstance(pd, list) else {}
            pd_copy["actual_payment_method"] = new_method
            order.payments_details = pd_copy
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(order, "payments_details")
            session.add(order)
            
            # Проверяем, есть ли запись в tbank_statements
            stmt = session.exec(select(TBankAccountStatement).where(TBankAccountStatement.matched_order_id == order.id)).first()
            if stmt:
                stmt.payment_purpose = f"Оплата {new_method} по заказу iiko #{order.external_number or order.id}"
                if new_method in ["СБП", "T-Pay"]:
                    stmt.account_number = f"{new_method} (T-API)"
                session.add(stmt)
            else:
                # Создаем запись в tbank_statements
                tx_date = order.created_at or datetime.now(timezone.utc).replace(tzinfo=None)
                pay_amt = float(order.total_paid if order.total_paid else (order.total_with_discount or order.total_amount))
                acc_name = f"{new_method} (T-API)" if new_method in ["СБП", "T-Pay"] else "Т-Банк (Эквайринг)"
                new_stmt = TBankAccountStatement(
                    account_number=acc_name,
                    charge_date=tx_date,
                    amount=pay_amt,
                    payment_purpose=f"Оплата {new_method} по заказу iiko #{order.external_number or order.id}",
                    payer_name=order.customer_name or f"Физическое лицо ({new_method})",
                    payer_account=f"ORD{order.id:06d}",
                    payer_bank_bic="",
                    payer_inn="",
                    matched_order_id=order.id
                )
                session.add(new_stmt)

    session.commit()
    
    # WebSocket broadcast
    try:
        from app.api.chat import manager
        manager.broadcast_sync({
            "type": "new_bank_payment",
            "method": new_method,
            "order_id": updated_order_id,
            "amount": float(order.total_paid if order and order.total_paid else 0.0)
        })
    except Exception as ws_err:
        pass
        
    return {
        "success": True,
        "payment_method": new_method,
        "order_id": updated_order_id
    }

