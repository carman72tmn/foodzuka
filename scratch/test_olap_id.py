#!/usr/bin/env python3
"""Тест получения ID курьера из OLAP"""
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
        
        payload = {
            "reportType": "DELIVERIES",
            "groupByRowFields": [
                "Delivery.Number",
                "Delivery.Courier",
                "Delivery.Courier.Id"
            ],
            "aggregateFields": ["fullSum"],
            "filters": {
                "OpenDate.Typed": {
                    "filterType": "DateRange",
                    "periodType": "CUSTOM",
                    "from": date_from.strftime("%Y-%m-%d"),
                    "to": now.strftime("%Y-%m-%d"),
                    "includeLow": True,
                    "includeHigh": True
                }
            }
        }
        
        try:
            print(f"Requesting OLAP with columns: {payload['groupByRowFields']}")
            data = await iiko_service._resto_request(
                "POST", "/v2/reports/olap",
                resto_url=settings.resto_url,
                resto_login=settings.resto_login,
                resto_password=settings.resto_password,
                json_data=payload
            )
            
            if isinstance(data, dict) and "data" in data:
                rows = data["data"]
                print(f"SUCCESS! Received {len(rows)} rows")
                # Находим Эльнура
                found = False
                for d in rows:
                    if d.get('Delivery.Courier') == "Эльнур":
                        print("Sample item:", json.dumps(d, indent=2, ensure_ascii=False))
                        found = True
                        break
                if not found and len(rows) > 0:
                    print("Эльнур not found in this response, sample of first item:")
                    print(json.dumps(rows[0], indent=2, ensure_ascii=False))
            else:
                print(f"Unexpected response format: {type(data)}")
                print(json.dumps(data, indent=2, ensure_ascii=False))

        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
