
import os

filepath = r'c:\Users\v_kva\.gemini\antigravity\scratch\foodtech\Service_info\system_faq.md'
new_content = """

### 50. Исправление открытия карточки заказа и безопасности синхронизации (05.05.2026) [FIXED]
- **Проблема**: Заказы с установленным временем доставки (expected_time) вызывали ошибку `ReferenceError: formatTime is not defined` в административной панели, из-за чего карточка заказа не открывалась (в частности, заказ №178). Также наблюдались ошибки `NoneType` в логах бэкенда при синхронизации.
- **Решение**:
    - **Frontend**: В `OrderDetailModal.vue` добавлен импорт функции `formatTime` из утилит.
    - **Backend**: В `iiko_sync_service.py` внедрена дополнительная проверка `if order:` перед выполнением операций `sql_flag_modified` и сохранением сессии. Вызовы `sql_flag_modified` обернуты в `try...except` с логированием, чтобы ошибки разметки SQLAlchemy не прерывали основной процесс синхронизации заказа.
- **Результат**: Карточки всех заказов открываются корректно. Ошибки синхронизации в `process_iiko_order` устранены.
"""

with open(filepath, 'a', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully updated system_faq.md")
