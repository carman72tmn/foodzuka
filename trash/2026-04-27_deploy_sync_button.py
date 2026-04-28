import subprocess
import os
import base64

# Конфигурация файлов (Локальный путь -> Удаленный путь на VPS)
files_to_sync = [
    ('backend/app/services/iiko_service.py', '/root/foodzuka/backend/app/services/iiko_service.py'),
    ('backend/app/services/iiko_sync_service.py', '/root/foodzuka/backend/app/services/iiko_sync_service.py'),
    ('backend/app/api/employees.py', '/root/foodzuka/backend/app/api/employees.py'),
    ('admin/resources/js/Pages/employees.vue', '/root/foodzuka/admin/resources/js/pages/employees.vue'),
    ('Service_info/system_faq.md', '/root/foodzuka/Service_info/system_faq.md'),
]

def sync_file(local_path, remote_path):
    print(f"Выгрузка: {local_path} -> {remote_path}...")
    if not os.path.exists(local_path):
        print(f"Ошибка: Файл {local_path} не найден локально!")
        return False

    with open(local_path, 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode('ascii')
    
    # Создаем директорию на VPS если ее нет
    remote_dir = os.path.dirname(remote_path)
    subprocess.run(["ssh", "foodtech", f"mkdir -p {remote_dir}"], check=True)

    # Записываем содержимое через SSH
    python_code = f"import sys, base64; open('''{remote_path}''', 'wb').write(base64.b64decode(sys.stdin.read()))"
    cmd = ["ssh", "foodtech", f"python3 -c \"{python_code}\""]
    
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate(input=content_b64)
    
    if process.returncode == 0:
        print(f"Успешно выгружен {local_path}")
        return True
    else:
        print(f"Ошибка при выгрузке {local_path}: {stderr}")
        return False

# 1. Выгрузка файлов
print("=== Начало выгрузки файлов на VPS ===")
for lp, rp in files_to_sync:
    if not sync_file(lp, rp):
        print("Критическая ошибка выгрузки. Прерывание.")
        exit(1)

# 2. Сборка фронтенда на VPS
print("\n=== Сборка фронтенда (npm run build) ===")
# Т.к. был изменен .vue файл, нужно пересобрать билд
build_cmd = "cd /root/foodzuka/admin && npm run build"
try:
    subprocess.run(["ssh", "foodtech", build_cmd], check=True)
    print("Фронтенд успешно собран.")
except subprocess.CalledProcessError as e:
    print(f"Ошибка при сборке фронтенда: {e}")

# 3. Перезапуск сервисов
print("\n=== Перезапуск контейнеров backend и worker ===")
restart_cmd = "cd /root/foodzuka && docker-compose restart backend worker"
try:
    subprocess.run(["ssh", "foodtech", restart_cmd], check=True)
    print("Сервисы успешно перезапущены.")
except subprocess.CalledProcessError as e:
    print(f"Ошибка при перезапуске сервисов: {e}")

print("\n=== Деплой завершен успешно! ===")
