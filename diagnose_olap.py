import asyncio
import httpx
from sqlmodel import Session, select
from app.core.database import engine
from app.models.iiko_settings import IikoSettings
from app.services.iiko_service import iiko_service
from datetime import datetime, timedelta

async def diagnose_olap():
    print("--- Диагностика iiko RESTO OLAP ---")
    
    with Session(engine) as db:
        settings = db.exec(select(IikoSettings)).first()
        if not settings:
            print("ОШИБКА: Настройки iiko не найдены в базе данных!")
            return
            
        print(f"Cloud API Login: {settings.api_login[:4]}... (ID: {settings.organization_id})")
        print(f"Resto URL: {settings.resto_url}")
        print(f"Resto Login: {settings.resto_login}")
        print(f"Resto Password: {'*' * len(settings.resto_password) if settings.resto_password else 'MISSING'}")
        
        if not settings.resto_url or not settings.resto_login:
            print("ПРЕДУПРЕЖДЕНИЕ: Данные iiko Resto (URL/Login) не заполнены. Будет использоваться Cloud API (fallback).")
        
        # Пробуем получить отчет
        date_from = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = date_from
        
        print("\n--- Попытка получения отчета через iiko_service.get_olap_report ---")
        try:
            # Мы вызываем метод напрямую, чтобы увидеть логи
            rows = await iiko_service.get_olap_report(
                date_from=date_from,
                date_to=date_to,
                api_login=settings.api_login,
                organization_id=settings.organization_id,
                resto_url=settings.resto_url,
                resto_login=settings.resto_login,
                resto_password=settings.resto_password
            )
            print(f"УСПЕХ: Получено строк: {len(rows)}")
            if rows:
                print(f"Первая строка: {rows[0]}")
        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnose_olap())
