import asyncio
import sys
import os

# Add backend to path if needed (though inside container it should be fine)
sys.path.append('/app')

from app.services.iiko_service import iiko_service
from app.core.database import Session, engine
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

async def main():
    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if not settings:
            print('No settings found')
            return
            
        new_token = 'db7400a687d6febf36a896672c6318d9'
        url = 'https://vezuroll.ru/api/v1/webhooks/iiko'
        org_id = settings.organization_id
        
        print(f'Attempting to register webhook with token: {new_token}')
        
        payload = {
            'organizationId': str(org_id),
            'webHooksUri': url,
            'authToken': new_token,
            'webHooksFilter': {
                'deliveryOrderFilter': {
                    'orderStatuses': [
                        'Unconfirmed', 'WaitCooking', 'ReadyForCooking', 
                        'CookingStarted', 'CookingCompleted', 'Waiting', 
                        'OnWay', 'Delivered', 'Closed', 'Cancelled'
                    ],
                    'errors': True
                }
            }
        }
        
        # Clear cooling period to be sure
        iiko_service._cooling_endpoints.clear() 
        
        try:
            response = await iiko_service._request(
                'POST',
                '/api/1/webhooks/update_settings',
                json_data=payload,
                log_error=True
            )
            
            if isinstance(response, dict) and response.get('error'):
                print(f'Registration failed (API returned error): {response}')
            elif isinstance(response, dict) and response.get('correlationId'):
                print(f'Registration successful! Correlation ID: {response.get("correlationId")}')
                # NOW we update the DB
                settings.webhook_auth_token = new_token
                settings.webhook_url = url
                session.add(settings)
                session.commit()
                print(f'DB updated successfully with token: {new_token}')
            else:
                print(f'Unexpected response structure: {response}')
        except Exception as e:
            print(f'Registration error: {e}')

if __name__ == '__main__':
    asyncio.run(main())
