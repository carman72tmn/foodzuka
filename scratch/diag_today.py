#!/usr/bin/env python3
"""Диагностика синхронизации доставок за сегодня"""
import asyncio
import sys
sys.path.insert(0, '/app')

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def main():
    from app.core.database import SessionLocal
    from app.services.iiko_service import iiko_service
    from sqlmodel import select
    from app.models import IikoSettings
    from datetime import datetime, timedelta
    import zoneinfo

    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        tz = zoneinfo.ZoneInfo("Asia/Yekaterinburg")
        now = datetime.now(tz)
        
        # Проверяем за вчера и сегодня
        date_from = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        
        print(f"Checking deliveries from {date_from} to {now}")
        
        try:
            deliveries = await iiko_service.get_resto_detailed_deliveries(
                date_from=date_from,
                date_to=now,
                organization_id=settings.organization_id or "",
                resto_url=settings.resto_url,
                resto_login=settings.resto_login,
                resto_password=settings.resto_password
            )
            print(f"OK: Received {len(deliveries)} deliveries")
            
            # Считаем по дням
            stats = {}
            for d in deliveries:
                dt_str = d.get('whenDelivered') or d.get('expectedDeliveryTime') or d.get('whenCookingCompleted')
                if dt_str:
                    date_part = dt_str.split('T')[0]
                    stats[date_part] = stats.get(date_part, 0) + 1
            
            for date, count in sorted(stats.items()):
                print(f"  {date}: {count} orders")
                
            if deliveries:
                print("\nLast 5 orders details:")
                for d in deliveries[-5:]:
                    print(f"  Num: {d.get('id')}, Delivered: {d.get('whenDelivered')}, Sum: {d.get('sum')}, Courier: {d.get('courierInfo', {}).get('courier', {}).get('name')}")

        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")

async def run():
    await main()

if __name__ == "__main__":
    asyncio.run(run())
