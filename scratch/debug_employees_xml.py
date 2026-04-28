#!/usr/bin/env python3
"""Сохранение XML сотрудников из iiko Resto"""
import asyncio
import sys
sys.path.insert(0, '/app')

async def main():
    from app.core.database import SessionLocal
    from app.services.iiko_service import iiko_service
    from sqlmodel import select
    from app.models import IikoSettings

    with SessionLocal() as session:
        settings = session.exec(select(IikoSettings)).first()
        
        try:
            # iiko Resto возвращает XML по умолчанию
            data = await iiko_service._resto_request(
                "GET", "/employees", 
                resto_url=settings.resto_url,
                resto_login=settings.resto_login,
                resto_password=settings.resto_password
            )
            
            if isinstance(data, str):
                with open("/app/employees_debug.xml", "w", encoding="utf-8") as f:
                    f.write(data)
                print(f"XML saved to /app/employees_debug.xml (Length: {len(data)})")
                
                # Поищем Эльнура в сыром тексте
                if "Эльнур" in data:
                    print("Found 'Эльнур' in raw XML!")
                else:
                    print("'Эльнур' NOT found in raw XML.")
            else:
                print(f"Data is not a string: {type(data)}")

        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
