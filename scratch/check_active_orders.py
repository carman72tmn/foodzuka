import requests
import json
from datetime import datetime, timedelta

API_LOGIN = "86dfd64bd15c42199b789edf6adcb289"
ORG_ID = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
BASE_URL = "https://api-ru.iiko.services"

def get_token():
    resp = requests.post(f"{BASE_URL}/api/1/access_token", json={"apiLogin": API_LOGIN})
    resp.raise_for_status()
    return resp.json()["token"]

def check_orders():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Сегодня
    now = datetime.utcnow()
    date_from = (now - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00.000")
    date_to = (now + timedelta(days=1)).strftime("%Y-%m-%d 23:59:59.000")
    
    print(f"Querying from {date_from} to {date_to} (UTC)...")
    
    payload = {
        "organizationIds": [ORG_ID],
        "deliveryDateFrom": date_from,
        "deliveryDateTo": date_to,
        # НЕ указываем статусы, чтобы получить ВСЕ
    }
    
    resp = requests.post(f"{BASE_URL}/api/1/deliveries/by_delivery_date_and_status", headers=headers, json=payload)
    if not resp.ok:
        print(f"Error: {resp.status_code} - {resp.text}")
        return

    data = resp.json()
    orders = data.get("orders", [])
    print(f"Total orders found: {len(orders)}")
    
    for order in orders:
        ord_info = order.get("order", {})
        ext_num = ord_info.get("externalNumber")
        status = order.get("status")
        service_type = ord_info.get("orderServiceType")
        delivery_date = ord_info.get("whenBillIsPrepared") or ord_info.get("deliveryDate")
        
        print(f"Order #{ext_num} | Status: {status} | Type: {service_type} | Date: {delivery_date}")

if __name__ == "__main__":
    check_orders()
