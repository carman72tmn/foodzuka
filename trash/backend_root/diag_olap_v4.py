
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
        date_from = date_to - timedelta(days=7)

        print(f"Testing OLAP fields for {settings.organization_id}...")
        
        test_groupings = ["Department", "Terminal", "TerminalGroup", "CashRegister", "OpenDate.Typed"]
        test_aggregates = [
            "UniqOrderId", "DishDiscountSumInt", "FullSum", "fullSum", "OrderSum", 
            "CostPercent", "CostSum", "DiscountSum",
            "ProductCostBase.ProductCost", "ProductCostBase.MarkUp", "ProductCostBase.Percent"
        ]
        
        print("\n--- Testing Grouping Fields ---")
        valid_groupings = []
        for g in test_groupings:
            rows = await iiko_service.get_custom_olap_report(
                "SALES", [g], ["UniqOrderId"], 
                date_from, date_to, settings.organization_id
            )
            if rows:
                print(f"Grouping '{g}': OK (Rows: {len(rows)})")
                valid_groupings.append(g)
            else:
                print(f"Grouping '{g}': FAILED or EMPTY")

        print("\n--- Testing Aggregate Fields ---")
        valid_aggregates = []
        for a in test_aggregates:
            rows = await iiko_service.get_custom_olap_report(
                "SALES", ["OpenDate.Typed"], [a, "UniqOrderId"], 
                date_from, date_to, settings.organization_id
            )
            if rows:
                print(f"Aggregate '{a}': OK (Rows: {len(rows)})")
                valid_aggregates.append(a)
            else:
                print(f"Aggregate '{a}': FAILED or EMPTY")

if __name__ == "__main__":
    asyncio.run(diag_revenue_fields())
