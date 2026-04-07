import asyncio
from app.services.iiko_service import iiko_service
from datetime import datetime
from app.models.iiko_settings import IikoSettings
from sqlmodel import Session, select
from app.core.database import engine

async def t():
    with Session(engine) as s:
        i = s.exec(select(IikoSettings)).first()
        try:
            res = await iiko_service._resto_request(
                'POST', 
                '/v2/reports/olap', 
                json_data={
                    'reportType': 'SALES', 
                    'groupByRowFields': ['Department', 'OpenDate.Typed'], 
                    'aggregateFields': ['DishDiscountSumInt', 'DiscountSum', 'GuestNum', 'DishAmountInt'], 
                    'filters': {
                        'OpenDate.Typed': {
                            'filterType': 'DateRange', 
                            'periodType': 'CUSTOM', 
                            'from': '2026-04-07T00:00:00.000', 
                            'to': '2026-04-08T00:00:00.000', 
                            'includeLow': True, 
                            'includeHigh': False
                        }, 
                        'OrderDeleted': {
                            'filterType': 'IncludeValues', 
                            'values': ['NOT_DELETED']
                        }
                    }
                }, 
                resto_url=i.resto_url, 
                resto_login=i.resto_login, 
                resto_password=i.resto_password
            )
            print('SUCCESS _resto_request', res.keys() if isinstance(res, dict) else res)
        except Exception as e:
            print('FAIL _resto_request', e)
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(t())
