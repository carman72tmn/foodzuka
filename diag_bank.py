import os
import sys
from datetime import date, datetime
from sqlmodel import Session, select

sys.path.append("/root/foodzuka/backend")
from app.core.database import engine
from app.api.bank import get_bank_payments
from app.models.user import User
from app.models.tbank_settings import TBankSettings, TBankAccountStatement
from app.models.order import Order

with Session(engine) as db:
    user = db.exec(select(User)).first()
    settings = db.exec(select(TBankSettings)).first()
    
    print("=== TBANK SETTINGS ===")
    if settings:
        print(f"Active: {settings.is_active}")
        print(f"Terminal Key: {settings.terminal_key}")
        print(f"Terminal Pickup: {settings.terminal_pickup}")
        print(f"Terminal Delivery: {settings.terminal_delivery}")
        print(f"Selected Terminals: {settings.selected_terminals}")
        print(f"Token: {settings.token[:8]}... if token else None")
        print(f"Merchant ID: {settings.merchant_id}")
    else:
        print("No settings found")
        
    print("\n=== RECENT ORDERS WITH PAYMENTS (LAST 10) ===")
    orders = db.exec(select(Order).order_by(Order.created_at.desc()).limit(10)).all()
    for o in orders:
        print(f"Order #{o.id} ({o.external_number}): created={o.created_at}, total={o.total_amount}, paid={o.total_paid}, is_paid={o.is_paid}, method={o.payment_method}, details={o.payments_details}")
        
    print("\n=== RECENT STATEMENTS (LAST 10) ===")
    stmts = db.exec(select(TBankAccountStatement).order_by(TBankAccountStatement.charge_date.desc()).limit(10)).all()
    for s in stmts:
        print(f"Stmt #{s.id}: date={s.charge_date}, amt={s.amount}, acct={s.account_number}, payer={s.payer_name}, inn={s.payer_inn}, purpose='{s.payment_purpose[:60]}', matched_order={s.matched_order_id}")
        
    print("\n=== GET_BANK_PAYMENTS (TODAY: 2026-08-30) ===")
    today = date(2026, 8, 30)
    payments = get_bank_payments(date_from=today, date_to=today, status_filter=None, search=None, session=db, current_user=user)
    print(f"Total payments returned by get_bank_payments for today: {len(payments)}")
    for p in payments:
        print(f"  P: id={p['id']} date={p['date']} method={p['payment_method']} amt={p['bank_amount']} ord_amt={p['order_amount']} status={p['status']} is_real={p['is_real']} cust={p['customer_name']} desc='{p.get('description','')[:50]}'")
