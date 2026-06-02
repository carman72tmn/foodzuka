from sqlmodel import Session, select, func
from app.core.database import engine
from app.models.employee import Shift
from app.models.olap_revenue import OlapRevenueRecord
import json

def check_db():
    with Session(engine) as session:
        # Check latest shifts
        shifts = session.exec(select(Shift).order_by(Shift.date_open.desc()).limit(10)).all()
        print("--- Latest Shifts ---")
        for s in shifts:
            print(f"ID: {s.id}, Open: {s.date_open}, Close: {s.date_close}, BizDate: {s.business_date}, RevenueAtClose: {s.revenue_at_close}")
        
        # Check latest revenue records
        revenue = session.exec(select(OlapRevenueRecord).order_by(OlapRevenueRecord.business_date.desc()).limit(10)).all()
        print("\n--- Latest OLAP Revenue Records ---")
        for r in revenue:
            print(f"Date: {r.business_date}, Rev: {r.revenue}, Period: {r.period_type}, Updated: {r.updated_at}")

if __name__ == "__main__":
    check_db()
