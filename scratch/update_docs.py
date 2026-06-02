import os

def update_sql_faq():
    path = r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\Service_info\sql_faq.md'
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    new_fields = """| `registered_organization`   | Рег. орг.      | ID регистрирующей орг.   | **[NEW 29.04]** UUID организации                             |
| `first_order_date`         | Первый заказ   | Дата самого первого заказа | **[NEW 30.04]** Из OLAP аналитики                            |
| `total_discount`           | Всего скидок   | Общая сумма скидок        | **[NEW 30.04]** Decimal(12,2)                                |
| `total_items`              | Всего товаров  | Общее кол-во товаров      | **[NEW 30.04]** float                                        |
| `average_check`            | Средний чек    | Средний чек клиента       | **[NEW 30.04]** Decimal(12,2)                                |
| `frequency_days`           | Частота        | Частота заказов (дни)     | **[NEW 30.04]** float                                        |
| `days_since_last_order`    | Дней с посл.   | Дней с последнего заказа  | **[NEW 30.04]** int                                          |
| `updated_at`               | Обновлено      | Время посл. изм. записи   |                                                              |"""
    
    target = r'| `registered_organization`   | Рег. орг.      | ID регистрирующей орг.   | **[NEW 29.04]** UUID организации                             |'
    # Since we have encoding issues, let's look for part of it
    if '| `registered_organization`   |' in content:
        # Replace the line and add new ones
        content = content.replace(target, new_fields)
    else:
        print("Target not found in sql_faq.md")
        # Fallback: try to find updated_at
        if '| `updated_at` |' in content:
             content = content.replace('| `updated_at` |', new_fields.split('\n')[-1]) # This is tricky
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated sql_faq.md")

def update_system_faq():
    path = r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\Service_info\system_faq.md'
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    new_section = """
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
    content += new_section
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated system_faq.md")

def update_sitenav():
    path = r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\Service_info\sitenav.md'
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    target = '- **4. Аналитика**: [NEW] Выгрузка статистики из iiko Server (OLAP): LTV, средний чек, частота, и другие метрики (графики/сводные данные). Работает асинхронно.'
    replacement = '- **4. Аналитика**: [NEW] Выгрузка статистики из iiko Server (OLAP): LTV, средний чек, частота и др. **[UPDATE 30.04]**: Данные кэшируются в БД. Добавлены индикаторы загрузки (`VProgressCircular`) для полей во время синхронизации.'
    
    if target in content:
        content = content.replace(target, replacement)
    else:
        print("Target not found in sitenav.md")
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated sitenav.md")

if __name__ == "__main__":
    update_sql_faq()
    update_system_faq()
    update_sitenav()
