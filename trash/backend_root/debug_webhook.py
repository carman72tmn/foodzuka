import httpx
import asyncio
import json

async def debug_webhook():
    api_url = "https://api-ru.iiko.services"
    api_login = "86dfd64bd15c42199b789edf6adcb289"
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    
    # URL MUST BE HTTPS for iiko!
    # Mocking an HTTPS URL to see if it accepts it
    webhook_url = "https://example.com/api/v1/webhook/iiko" 
    auth_token = "debug_token_123"

    async with httpx.AsyncClient() as client:
        # 1. Get Token
        print(f"Step 1: Getting token...")
        resp = await client.post(f"{api_url}/api/1/access_token", json={"apiLogin": api_login})
        token = resp.json().get("token")
        
        # 2. Try Update Settings
        print(f"\nStep 2: Registering webhook {webhook_url}...")
        payload = {
            "organizationId": org_id,
            "webHooksUri": webhook_url,
            "authToken": auth_token,
            "webHooksFilter": {
                "deliveryOrderFilter": {
                    "orderStatuses": [
                        "Unconfirmed", "WaitCooking", "ReadyForCooking", 
                        "CookingStarted", "CookingCompleted", "Waiting", 
                        "OnWay", "Delivered", "Cancelled"
                    ],
                    "errors": True
                },
                "stopListUpdateFilter": {
                    "updates": True
                }
            }
        }
        
        resp = await client.post(
            f"{api_url}/api/1/webhooks/update_settings",
            headers={"Authorization": f"Bearer {token}"},
            json=payload
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(debug_webhook())
