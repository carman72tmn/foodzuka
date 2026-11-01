import sys
from datetime import datetime
from sqlmodel import Session, select

sys.path.append("/root/foodzuka/backend")
from app.core.database import engine
from app.models.tbank_settings import TBankAccountStatement
from app.models.order import Order

with Session(engine) as db:
    # Ищем последний заказ
    order = db.exec(select(Order).order_by(Order.id.desc())).first()
    print(f"Testing with order #{order.id} ({order.customer_name})")
    
    test_out_trade_no = f"TEST_SBP_{int(datetime.now().timestamp())}"
    test_amount = 155.0
    
    # 1. Проверяем регистрацию транзакции СБП
    db_op = TBankAccountStatement(
        account_number="СБП (T-API)",
        charge_date=datetime.now(),
        amount=float(test_amount),
        payment_purpose=f"Оплата СБП QR по заказу #{order.external_number or order.id} (T-Pay/СБП)",
        payer_name=order.customer_name or "Физическое лицо (СБП)",
        payer_inn="",
        payer_account=test_out_trade_no,
        payer_bank_bic="",
        matched_order_id=order.id
    )
    db.add(db_op)
    db.commit()
    db.refresh(db_op)
    print(f"Created SBP statement #{db_op.id} with matched_order_id={db_op.matched_order_id}")
    
    # 2. Проверяем выборку через get_bank_payments
    from app.api.bank import get_bank_payments
    from app.models.user import User
    user = db.exec(select(User)).first()
    
    payments = get_bank_payments(date_from=datetime.now().date(), date_to=datetime.now().date(), session=db, current_user=user)
    sbp_payments = [p for p in payments if p['id'] == f"stmt_{db_op.id}"]
    print(f"Found created statement in get_bank_payments: {len(sbp_payments) == 1}")
    if sbp_payments:
        p = sbp_payments[0]
        print(f"  Statement data: id={p['id']} method={p['payment_method']} amt={p['bank_amount']} status={p['status']} is_real={p['is_real']}")
        
    # Чистим тестовую запись
    db.delete(db_op)
    db.commit()
    print("Test SBP statement cleaned up successfully.")
