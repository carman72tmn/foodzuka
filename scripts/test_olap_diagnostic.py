import asyncio
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
from app.services.iiko_service import iiko_service
from datetime import datetime

async def main():
    with Session(engine) as db:
        settings = db.exec(select(IikoSettings)).first()
        if not settings:
            print("No iiko settings")
            return
        print(f"Org: {settings.organization_id}")
        print(f"Resto URL: {settings.resto_url}")
        print(f"Has resto user: {bool(settings.resto_login)}")
        
        # Тестируем получение OLAP отчета
        try:
            # Возьмем период за 1-2 апреля 2026 или октябрь 2026
            rows = await iiko_service.get_olap_report(
                date_from=datetime(2026, 10, 1),
                date_to=datetime(2026, 10, 2),
                organization_id=settings.organization_id,
                resto_url=settings.resto_url,
                resto_login=settings.resto_login,
                resto_password=settings.resto_password
            )
            print(f"OLAP Revenue rows count: {len(rows)}")
            if rows:
                print(f"Sample row: {rows[0]}")
        except Exception as e:
            print(f"Error fetching revenue OLAP: {e}")

        # Проверим доступность отчета DELIVERIES (курьеры, зоны, улицы, подзоны)
        try:
            deliv_rows = await iiko_service.get_custom_olap_report(
                report_type="DELIVERIES",
                group_by_fields=[
                    "OpenDate.Typed",
                    "Delivery.Courier",
                    "Delivery.Zone",
                    "Delivery.Region"
                ],
                aggregate_fields=[
                    "fullSum",
                    "UniqOrderId"
                ],
                date_from=datetime(2026, 10, 1),
                date_to=datetime(2026, 10, 2),
                organization_id=settings.organization_id
            )
            print(f"OLAP DELIVERIES rows count: {len(deliv_rows)}")
            if deliv_rows:
                print(f"Sample delivery row: {deliv_rows[0]}")
        except Exception as e:
            print(f"Error fetching deliveries OLAP: {e}")

if __name__ == "__main__":
    asyncio.run(main())
