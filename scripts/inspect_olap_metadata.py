import asyncio
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
from app.services.iiko_service import iiko_service
from datetime import datetime

async def test_deliveries_years():
    with Session(engine) as db:
        settings = db.exec(select(IikoSettings)).first()
        org_id = settings.organization_id
        
        years = [2021, 2024, 2026]
        for y in years:
            try:
                res = await iiko_service.get_custom_olap_report(
                    report_type="DELIVERIES",
                    group_by_fields=[
                        "OpenDate.Typed",
                        "Delivery.Courier",
                        "Delivery.Zone",
                        "Delivery.Region"
                    ],
                    aggregate_fields=["fullSum", "UniqOrderId"],
                    date_from=datetime(y, 5, 1),
                    date_to=datetime(y, 5, 3),
                    organization_id=org_id,
                    log_error=False
                )
                print(f"DELIVERIES {y}: {len(res)} rows. Sample: {res[0] if res else 'None'}")
            except Exception as e:
                print(f"DELIVERIES {y}: Error {e}")

if __name__ == "__main__":
    asyncio.run(test_deliveries_years())
