import os

def update_file(path, target_snippet, replacement_snippet):
    if not os.path.exists(path):
        print(f"File {path} not found")
        return False
    
    with open(path, 'rb') as f:
        content = f.read().decode('utf-8', 'ignore')
    
    if target_snippet in content:
        new_content = content.replace(target_snippet, replacement_snippet)
        with open(path, 'wb') as f:
            f.write(new_content.encode('utf-8'))
        print(f"Updated {path}")
        return True
    else:
        print(f"Target snippet not found in {path}")
        return False

# sql_faq.md
path_sql = r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\Service_info\sql_faq.md'
target_sql = '| `registered_organization`   | Рег. орг.      | ID регистрирующей орг.   | **[NEW 29.04]** UUID организации                             |'
# Try without spaces if needed, but let's try exact first
replacement_sql = target_sql + """
| `first_order_date`         | Первый заказ   | Дата самого первого заказа | **[NEW 30.04]** Из OLAP аналитики                            |
| `total_discount`           | Всего скидок   | Общая сумма скидок        | **[NEW 30.04]** Decimal(12,2)                                |
| `total_items`              | Всего товаров  | Общее кол-во товаров      | **[NEW 30.04]** float                                        |
| `average_check`            | Средний чек    | Средний чек клиента       | **[NEW 30.04]** Decimal(12,2)                                |
| `frequency_days`           | Частота        | Частота заказов (дни)     | **[NEW 30.04]** float                                        |
| `days_since_last_order`    | Дней с посл.   | Дней с последнего заказа  | **[NEW 30.04]** int                                          |"""

update_file(path_sql, target_sql, replacement_sql)

# system_faq.md
path_sys = r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\Service_info\system_faq.md'
new_section_sys = """
## Персистентная аналитика клиентов (OLAP) [NEW 30.04.2026]

Для ускорения работы интерфейса и снижения нагрузки на iiko API, данные OLAP-аналитики (LTV, средний чек и др.) теперь сохраняются в базу данных (таблица `customers`).

**Логика работы:**
1. **При открытии карточки гостя:** Фронтенд сразу получает "быстрые" данные из БД.
2. **Фоновое обновление:** Одновременно запускается запрос к эндпоинту `/olap-stats`, который тянет свежие данные из iiko.
3. **Кэширование:** Полученные из iiko данные автоматически обновляют запись в БД `customers`.
4. **Индикация:** Во время фонового обновления в UI отображаются спиннеры (`VProgressCircular`) рядом с полями.

**Обновляемые поля:**
- `first_order_date` (Дата первого заказа)
- `total_discount` (Сумма всех скидок)
- `total_items` (Общее количество купленных товаров)
- `average_check` (Средний чек)
- `frequency_days` (Средняя частота заказов в днях)
- `days_since_last_order` (Дней с последнего заказа)
"""
# Just append if not exists
with open(path_sys, 'rb') as f:
    sys_content = f.read().decode('utf-8', 'ignore')
if "Персистентная аналитика клиентов (OLAP)" not in sys_content:
    with open(path_sys, 'ab') as f:
        f.write(new_section_sys.encode('utf-8'))
    print(f"Updated {path_sys}")

# sitenav.md
path_site = r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\Service_info\sitenav.md'
# Use a shorter snippet for target to be safer
target_site = '- **4. Аналитика**: [NEW] Выгрузка статистики из iiko Server (OLAP)'
replacement_site = '- **4. Аналитика**: [NEW] Выгрузка статистики из iiko Server (OLAP): LTV, средний чек, частота и др. **[UPDATE 30.04]**: Данные кэшируются в БД. Добавлены индикаторы загрузки (`VProgressCircular`) для полей во время синхронизации.'

# Read first 1000 chars to find it
with open(path_site, 'rb') as f:
    site_content = f.read().decode('utf-8', 'ignore')

if target_site in site_content:
    # Find the whole line
    lines = site_content.split('\n')
    for i, line in enumerate(lines):
        if target_site in line:
            lines[i] = replacement_site
            break
    with open(path_site, 'wb') as f:
        f.write('\n'.join(lines).encode('utf-8'))
    print(f"Updated {path_site}")
else:
    print(f"Target snippet not found in {path_site}")
