import asyncio
import logging
from app.services.iiko_service import iiko_service
from datetime import datetime, timedelta
from app.models.iiko_settings import IikoSettings
from sqlmodel import Session, select
from app.core.database import engine

logging.basicConfig(level=logging.WARNING, force=True)

async def t():
    with Session(engine) as s:
        i = s.exec(select(IikoSettings)).first()
        try:
            print("Calling get_olap_report...")
            date_from = datetime.now()
            date_to = datetime.now()
            
            res = await iiko_service.get_olap_report(
                date_from=date_from,
                date_to=date_to,
                api_login=i.api_login,
                organization_id=i.organization_id,
                resto_url=i.resto_url,
                resto_login=i.resto_login,
                resto_password=i.resto_password
            )
            print("SUCCESS get_olap_report:", len(res))
        except Exception as e:
            print("FAIL get_olap_report:")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(t())
