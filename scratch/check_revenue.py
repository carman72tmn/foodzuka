
from sqlmodel import Session, select, func
from app.core.database import engine
from app.models.olap_revenue import OlapRevenueRecord
import json

def check_revenue():
    biz_date = "2026-04-20"
    with Session(engine) as session:
        statement = select(OlapRevenueRecord).where(OlapRevenueRecord.business_date == biz_date)
        results = session.exec(statement).all()
        
        output = []
        for r in results:
            output.append({
                "id": r.id,
                "terminal": r.terminal_name,
                "revenue": r.revenue,
                "period": r.period_type,
                "updated_at": r.updated_at.isoformat()
            })
        
        print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    check_revenue()
