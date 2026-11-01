import logging
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from app.core.database import engine
from app.models.order import Order
from app.models.tbank_settings import TBankAccountStatement

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill_tbank")

def backfill():
    with Session(engine) as db:
        # Загружаем заказы за последние 3 дня
        date_limit = datetime.now(timezone.utc) - timedelta(days=3)
        query = select(Order).where(
            Order.created_at >= date_limit,
            Order.status != "cancelled"
        )
        orders = db.exec(query).all()
        print(f"Total orders checked for backfill: {len(orders)}")
        
        added_count = 0
        
        for order in orders:
            # Проверяем, есть ли оплата в payments_details
            pay_details = order.payments_details or {}
            items = []
            if isinstance(pay_details, dict):
                items = pay_details.get("items", [])
            elif isinstance(pay_details, list):
                items = pay_details
                
            for p_item in items:
                if not isinstance(p_item, dict):
                    continue
                    
                pn = p_item.get("name") or ""
                pn_lower = pn.lower()
                is_tbank_payment = any(word in pn_lower for word in ["t bank", "t-bank", "тинькофф", "tinkoff", "сбп", "tpay", "t-pay"])
                
                if is_tbank_payment and p_item.get("is_processed") and p_item.get("sum", 0) > 0:
                    pay_sum = float(p_item.get("sum"))
                    
                    # Проверяем, есть ли уже запись в tbank_statements
                    existing = db.exec(
                        select(TBankAccountStatement).where(
                            TBankAccountStatement.matched_order_id == order.id,
                            TBankAccountStatement.amount == pay_sum
                        )
                    ).first()
                    
                    if not existing:
                        # Определение типа и назначения
                        if "сбп" in pn_lower or "qr" in pn_lower:
                            purpose_text = f"Оплата через СБП по заказу #{order.external_number or order.id}"
                            account_num = "СБП (iiko)"
                        elif "tpay" in pn_lower or "t-pay" in pn_lower:
                            purpose_text = f"Оплата через T-Pay по заказу #{order.external_number or order.id}"
                            account_num = "T-Pay (iiko)"
                        else:
                            purpose_text = f"Оплата через Эквайринг по заказу #{order.external_number or order.id}"
                            account_num = "Интернет-эквайринг"
                            
                        db_op = TBankAccountStatement(
                            account_number=account_num,
                            charge_date=order.created_at or datetime.now(),
                            amount=pay_sum,
                            payment_purpose=purpose_text,
                            payer_name=order.customer_name or "Физическое лицо",
                            payer_account="iiko-sync",
                            payer_bank_bic="",
                            payer_inn="",
                            matched_order_id=order.id
                        )
                        db.add(db_op)
                        added_count += 1
                        print(f"Added: Order #{order.id} (Ext: {order.external_number}), Sum: {pay_sum} руб, Method: {pn}")
                        
        if added_count > 0:
            db.commit()
            print(f"Successfully committed {added_count} backfilled T-Bank statements.")
        else:
            print("No new statements were added.")

if __name__ == "__main__":
    backfill()
