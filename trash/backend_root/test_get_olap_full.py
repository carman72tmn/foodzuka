import asyncio
import logging
from app.services.iiko_service import iiko_service
from datetime import datetime
from app.models.iiko_settings import IikoSettings
from sqlmodel import Session, select
from app.core.database import engine

logging.basicConfig(level=logging.WARNING, force=True)

async def t():
    with Session(engine) as s:
        i = s.exec(select(IikoSettings)).first()
        try:
            print("Calling get_olap_report with financial fields...")
            date_from = datetime.now()
            date_to = date_from
            
            res = await iiko_service.get_olap_report(
                date_from=date_from,
                date_to=date_to,
                api_login=i.api_login,
                organization_id=i.organization_id,
                resto_url=i.resto_url,
                resto_login=i.resto_login,
                resto_password=i.resto_password
            )
            if res:
                print("SUCCESS get_olap_report!")
                for row in res:
                    print(f"Org: {row['organization_name']}")
                    print(f"Revenue: {row['revenue']}")
                    print(f"Cost Price: {row['cost_price']} ({row['cost_price_percent']*100:.2f}%)")
                    print(f"Markup: {row['markup']} ({row['markup_percent']*100:.2f}%)")
            else:
                print("No data returned.")
        except Exception as e:
            print("FAIL get_olap_report:")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(t())
