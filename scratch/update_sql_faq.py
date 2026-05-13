
import os

file_path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\Service_info\sql_faq.md"

encodings = ['utf-8', 'windows-1251', 'iso-8859-5']
content = None

for enc in encodings:
    try:
        with open(file_path, 'r', encoding=enc) as f:
            content = f.read()
        print(f"Read successfully with {enc}")
        break
    except:
        continue

if content:
    target = '| `registration_source`       | Источник рег.    | Где зарегистрирован    | **[NEW 29.04]** Напр. "Сайт", "Мобильное приложение"         |'
    replacement = (
        '| `registration_source`       | Источник рег.    | Где зарегистрирован    | **[NEW 29.04]** Напр. "Сайт", "Мобильное приложение"         |\n'
        '| `registration_date`         | Дата регистрации | Когда зарегистрирован  | **[NEW 30.04]** Из XLSX импорта                              |\n'
        '| `is_high_risk`              | Высокий риск     | Флаг опасного клиента  | **[NEW 30.04]**                                              |\n'
        '| `is_synced_to_iiko_cards`   | Синхр. iiko.cards | Флаг синхронизации     | **[NEW 30.04]**                                              |\n'
        '| `is_system_notifications_consented` | Увед. системы | Согласие на системные  | **[NEW 30.04]**                                              |\n'
        '| `is_loyalty_messages_consented` | Увед. лояльности | Согласие на лояльность | **[NEW 30.04]**                                              |\n'
        '| `last_order_date`           | Дата посл. заказа| Когда был посл. заказ  | **[NEW 30.04]**                                              |'
    )

    if target in content:
        new_content = content.replace(target, replacement)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Updated and converted to UTF-8")
    else:
        print("Target not found")
else:
    print("Could not read file with any encoding")
