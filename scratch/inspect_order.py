#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '/app')

async def main():
    from app.core.database import SessionLocal
    from app.services.iiko_service import iiko_service
    from sqlmodel import select
    from app.models import IikoSettings
    from datetime import datetime, timedelta
    import zoneinfo
    import json

    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        tz = zoneinfo.ZoneInfo("Asia/Yekaterinburg")
        now = datetime.now(tz)
        date_from = now - timedelta(days=1)
        
        deliveries = await iiko_service.get_resto_detailed_deliveries(
            date_from=date_from,
            date_to=now,
            organization_id=settings.organization_id or "",
            resto_url=settings.resto_url,
            resto_login=settings.resto_login,
            resto_password=settings.resto_password
        )
        
        if deliveries:
            # Находим заказ с Эльнуром
            for d in deliveries:
                c_name = d.get('courierInfo', {}).get('courier', {}).get('name')
                if c_name == "Эльнур":
                    print(json.dumps(d, indent=2, ensure_ascii=False))
                    break

if __name__ == "__main__":
    asyncio.run(main())
