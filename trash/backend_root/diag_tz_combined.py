
import asyncio
import logging
from datetime import datetime, timedelta
from app.core.database import Session, engine
from app.models.iiko_settings import IikoSettings
from app.services.iiko_service import iiko_service
from sqlmodel import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diag_revenue_fields():
    with Session(engine) as db:
        settings = db.exec(select(IikoSettings)).first()
        if not settings:
            print("Settings not found")
            return

        date_to = datetime.now()
        date_from = date_to - timedelta(days=3)

        print(f"Testing TZ fields for {settings.organization_id}...")
        
        # Поля из ТЗ
        fields = ["UniqOrderId", "DishDiscountSumInt", "FullSum", "CostPercent", "CostSum", "DiscountSum"]
        groupings = ["Department", "OpenDate.Typed"]
        
        try:
            rows = await iiko_service.get_custom_olap_report(
                report_type="SALES",
                group_by_fields=groupings,
                aggregate_fields=fields,
                date_from=date_from,
                date_to=date_to,
                organization_id=settings.organization_id
            )
            print(f"Success! Received {len(rows)} rows.")
            if rows:
                print("Sample row:", rows[0])
        except Exception as e:
            print(f"Failed with combined TZ fields: {e}")

if __name__ == "__main__":
    asyncio.run(diag_revenue_fields())
