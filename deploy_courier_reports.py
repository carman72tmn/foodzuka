import os
import sys
import subprocess

def run_command(command, description):
    print(f"--- {description} ---")
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении: {e}")
        sys.exit(1)

def main():
    # 1. Синхронизация файлов на VPS
    # Предполагаем, что пользователь запускает это из корня проекта
    print("Подготовка к деплою на VPS foodtech...")
    
    # Файлы для выгрузки
    files_to_upload = [
        "backend/app/models/employee.py",
        "backend/app/services/iiko_service.py",
        "backend/app/services/iiko_sync_service.py",
        "backend/app/api/employees.py"
    ]
    
    for file in files_to_upload:
        run_command(f"scp {file} foodtech:/root/foodzuka/{file}", f"Выгрузка {file}")

    # 2. Перезапуск контейнера для применения изменений
    run_command("ssh foodtech 'cd /root/foodzuka && docker compose restart foodtech-backend'", "Перезапуск бэкенда")

    # 3. Принудительная синхронизация за последние 2 дня для заполнения новых полей
    print("\n--- Запуск синхронизации для заполнения новых полей адреса ---")
    run_command("ssh foodtech 'docker exec foodtech-backend python3 -c \"from app.core.database import engine; from sqlmodel import Session; from app.services import iiko_sync_service; import asyncio; async def run():\n    with Session(engine) as session:\n        await iiko_sync_service.sync_courier_deliveries(session, days=2)\nasyncio.run(run())\"'", "Синхронизация данных")

    print("\nДеплой успешно завершен! Отчеты теперь должны отображать корректный формат адреса.")

if __name__ == "__main__":
    main()
