import sys
from datetime import date
from sqlmodel import Session, select

sys.path.append("/root/foodzuka/backend")
from app.core.database import engine
from app.api.bank import get_bank_payments
from app.models.user import User

with Session(engine) as db:
    user = db.exec(select(User)).first()
    
    # Проверяем исторический период, где раньше появлялись зачисления реестров на 26 000 - 37 000 руб.
    d_from = date(2026, 6, 14)
    d_to = date(2026, 6, 18)
    payments = get_bank_payments(date_from=d_from, date_to=d_to, status_filter=None, search=None, session=db, current_user=user)
    
    print(f"Total payments in period {d_from} - {d_to}: {len(payments)}")
    
    large_payments = [p for p in payments if p['bank_amount'] > 10000]
    print(f"Large payments (>10000 rub): {len(large_payments)}")
    for p in large_payments:
        print(f"  P: id={p['id']} date={p['date']} method={p['payment_method']} amt={p['bank_amount']} ord_amt={p['order_amount']} status={p['status']} cust={p['customer_name']} desc='{p.get('description','')[:60]}'")
