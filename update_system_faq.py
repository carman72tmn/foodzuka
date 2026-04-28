import os

path = r"C:\Users\v_kva\.gemini\antigravity\brain\49e1c72c-07e0-4f1a-ab21-9bf774ea6593\system_faq.md"
if not os.path.exists(path):
    print(f"File not found: {path}")
    exit(1)

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

update = """
---
*Последнее обновление: 24.04.2026 01:00 (UTC+5)*

### Синхронизация полных адресов (24.04.2026)
В систему внесено важное улучшение для решения проблемы "неполных адресов" из iiko:
1. **Объединение полей**: Теперь `IikoSyncService` ищет компоненты адреса (дом, квартира, подъезд, этаж, домофон) одновременно в объектах `address` и `deliveryPoint` ответа iiko. Это исключает потерю данных, если iiko заполнила квартиру в одном месте, а улицу в другом.
2. **Умный формат Line1**: Даже если в настройках выбран формат "Одной строкой", система теперь проверяет, содержит ли эта строка упоминание квартиры, подъезда и т.д. Если данные есть в отдельных полях, но отсутствуют в строке `line1`, они автоматически дописываются в конец через запятую.
3. **Сохранение в БД**: Все компоненты адреса теперь гарантированно сохраняются в соответствующие колонки таблицы `orders` (`flat`, `entrance`, `floor`, `doorphone`), что позволяет фронтенду корректно отображать их в деталях заказа.
"""

# Append to the end or replace the last update line
if "Последнее обновление: 23.04.2026 21:35" in content:
    content = content.replace("*Последнее обновление: 23.04.2026 21:35 (UTC+5)*", update)
else:
    content += update

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated system_faq.md")
