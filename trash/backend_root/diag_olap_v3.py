
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
        
        # Группировки для теста
        test_groupings = ["Department", "Terminal", "TerminalGroup", "CashRegister", "OpenDate.Typed"]
        # Агрегаты для теста (из ТЗ и альтернативы)
        test_aggregates = [
            "UniqOrderId", "DishDiscountSumInt", "FullSum", "fullSum", "OrderSum", 
            "CostPercent", "CostSum", "DiscountSum",
            "ProductCostBase.ProductCost", "ProductCostBase.MarkUp", "ProductCostBase.Percent"
        ]
        
        print("\n--- Testing Grouping Fields ---")
        valid_groupings = []
        for g in test_groupings:
            try:
                await iiko_service.get_custom_olap_report(
                    "SALES", [g], ["UniqOrderId"], 
                    date_from, date_to, settings.organization_id
                )
                print(f"Grouping '{g}': OK")
                valid_groupings.append(g)
            except Exception as e:
                print(f"Grouping '{g}': FAILED - {e}")

        print("\n--- Testing Aggregate Fields ---")
        valid_aggregates = []
        for a in test_aggregates:
            try:
                await iiko_service.get_custom_olap_report(
                    "SALES", ["OpenDate.Typed"], [a, "UniqOrderId"], 
                    date_from, date_to, settings.organization_id
                )
                print(f"Aggregate '{a}': OK")
                valid_aggregates.append(a)
            except Exception as e:
                print(f"Aggregate '{a}': FAILED - {e}")

        if valid_groupings and valid_aggregates:
            print("\n--- Running Final Report with Best Fields ---")
            try:
                rows = await iiko_service.get_custom_olap_report(
                    "SALES", valid_groupings[:3], valid_aggregates[:8],
                    date_from, date_to, settings.organization_id
                )
                print(f"Final Success! Rows: {len(rows)}")
                if rows:
                    print("Example data:", rows[0])
            except Exception as e:
                print(f"Final combined report failed: {e}")

if __name__ == "__main__":
    asyncio.run(diag_revenue_fields())
