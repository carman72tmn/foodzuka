import os
import re

def update_file_regex(path, pattern, replacement_line):
    if not os.path.exists(path):
        print(f"File {path} not found")
        return False
    
    with open(path, 'rb') as f:
        content = f.read().decode('utf-8', 'ignore')
    
    # Try to find the line containing the pattern
    lines = content.split('\n')
    found = False
    for i, line in enumerate(lines):
        if pattern in line:
            # If we find the pattern, we either replace or append after
            lines[i] = line + replacement_line
            found = True
            break
    
    if found:
        with open(path, 'wb') as f:
            f.write('\n'.join(lines).encode('utf-8'))
        print(f"Updated {path}")
        return True
    else:
        print(f"Pattern {pattern} not found in {path}")
        return False

# sql_faq.md
path_sql = r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\Service_info\sql_faq.md'
# Use just the field name as pattern
replacement_sql = """
| `first_order_date`         | Первый заказ   | Дата самого первого заказа | **[NEW 30.04]** Из OLAP аналитики                            |
| `total_discount`           | Всего скидок   | Общая сумма скидок        | **[NEW 30.04]** Decimal(12,2)                                |
| `total_items`              | Всего товаров  | Общее кол-во товаров      | **[NEW 30.04]** float                                        |
| `average_check`            | Средний чек    | Средний чек клиента       | **[NEW 30.04]** Decimal(12,2)                                |
| `frequency_days`           | Частота        | Частота заказов (дни)     | **[NEW 30.04]** float                                        |
| `days_since_last_order`    | Дней с посл.   | Дней с последнего заказа  | **[NEW 30.04]** int                                          |"""

update_file_regex(path_sql, 'registered_organization', replacement_sql)

# sitenav.md
path_site = r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\Service_info\sitenav.md'
target_site = 'OLAP' # Safer pattern
replacement_site = '- **4. Аналитика**: [NEW] Выгрузка статистики из iiko Server (OLAP): LTV, средний чек, частота и др. **[UPDATE 30.04]**: Данные кэшируются в БД. Добавлены индикаторы загрузки (`VProgressCircular`) для полей во время синхронизации.'

with open(path_site, 'rb') as f:
    site_content = f.read().decode('utf-8', 'ignore')

lines = site_content.split('\n')
for i, line in enumerate(lines):
    if 'OLAP' in line and '4.' in line:
        lines[i] = replacement_site
        break
with open(path_site, 'wb') as f:
    f.write('\n'.join(lines).encode('utf-8'))
print(f"Updated {path_site}")
