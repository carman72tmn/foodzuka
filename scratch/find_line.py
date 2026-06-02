with open('backend/app/services/iiko_sync_service.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'def sync_courier_deliveries' in line:
            print(f"{i+1}: {line.strip()}")
