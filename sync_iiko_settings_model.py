import sys
path = "/root/foodzuka/backend/app/models/iiko_settings.py"
with open(path, "rb") as f:
    data = f.read()

content = None
for enc in ['utf-8', 'cp1251', 'latin-1']:
    try:
        content = data.decode(enc)
        break
    except:
        continue

if content is None:
    sys.exit(1)

# Add missing fields before meta-data fields
missing_fields = """
    # Настройки адреса и локации
    address_format: str = Field(default="standard", description="Формат адреса для iiko")
    city_name: Optional[str] = Field(default=None, max_length=255, description="Город по умолчанию")
    
    # Таймзоны
    manual_timezone: Optional[str] = Field(default=None, max_length=100, description="Ручная настройка часового пояса")
    timezone_name: Optional[str] = Field(default=None, max_length=255, description="Имя часового пояса (Europe/Moscow)")

    # Лояльность iiko POS
    pos_loyalty_name: Optional[str] = Field(default=None, max_length=255)
    pos_loyalty_login: Optional[str] = Field(default=None, max_length=255)
    pos_loyalty_password: Optional[str] = Field(default=None, max_length=255)
    pos_loyalty_channel: Optional[str] = Field(default=None, max_length=255)

    # Карты
    delivery_zones_map_url: Optional[str] = Field(default=None, max_length=1000)

    # Метаданные"""

if "address_format" not in content:
    content = content.replace("    # Метаданные", missing_fields)

with open(path, "wb") as f:
    f.write(content.encode('utf-8'))
