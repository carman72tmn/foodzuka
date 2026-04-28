import asyncio
import json
import os
import sys
from datetime import datetime

# Добавляем путь к приложению
sys.path.append(os.getcwd())

from app.services.iiko_service import IikoService

async def test_dashboard_full():
    service = IikoService()
    org_id = "2704eeae-dc5f-4c9f-9b81-375c454dd5bd"
    
    print(f"--- Тестирование ПОЛНОГО Dashboard для организации {org_id} ---")
    
    report = await service.get_organization_report(
        organization_id=org_id,
        date_from="2026-04-21 00:00:00",
        date_to="2026-04-21 23:59:59"
    )
    
    if "error" in report:
        print(f"[ERROR] {report['error']}")
        return

    print("\n[SUCCESS] Отчет получен!")
    print(f"Поля в ответе: {list(report.keys())}")
    
    # Проверка структуры
    for section in ["terminals", "orders", "couriers", "sections", "kpi", "analytics"]:
        if section in report:
            print(f"Секция '{section}': OK")
        else:
            print(f"[MISSING] Секция '{section}' отсутствует!")

    # Проверка вложенности couriers
    if "couriers" in report:
        if "all" in report["couriers"] and "active" in report["couriers"]:
            print("Вложенность 'couriers' (all/active): OK")
        else:
            print(f"[ERROR] В 'couriers' отсутствуют all или active: {list(report['couriers'].keys())}")

    # Печать KPI для наглядности
    print(f"KPI: {json.dumps(report.get('kpi'), indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_dashboard_full())
