import subprocess
import os

files = [
    "admin/resources/js/utils/date.js",
    "admin/resources/js/App.vue",
    "admin/resources/js/pages/orders/index.vue",
    "admin/resources/js/pages/system/logs.vue"
]

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(f"Success: {result.stdout}")
    return result

# 1. Загрузка файлов
for f in files:
    local_path = os.path.join(r"c:\Users\v_kva\.gemini\antigravity\scratch\foodtech", f)
    remote_path = f"/root/foodzuka/{f}"
    run_cmd(f"scp {local_path} foodtech:{remote_path}")

# 2. Пересборка фронтенда на сервере
# Мы знаем, что фронтенд находится в контейнере foodtech-frontend
# Но нам нужно запустить сборку внутри контейнера или пересобрать образ.
# Обычно в таких проектах используется npm run build.
print("Rebuilding frontend...")
run_cmd('ssh foodtech "docker exec foodtech-frontend npm run build"')

print("Deployment finished.")
