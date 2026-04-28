from app.services.iiko_sync_service import IikoSyncService

s = IikoSyncService()
addr = {
    'city': {'name': 'Тюмень'},
    'street': 'Ленина',
    'house': '10'
}
print(f"Components: {s.format_address(addr, city='Тюмень', fmt='components')}")
print(f"Line1: {s.format_address({'line1': 'г. Тюмень, ул. Ленина, д. 10', 'flat': '5'}, city='Тюмень', fmt='line1')}")
