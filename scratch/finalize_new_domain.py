import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def finalize_deployment(ip, pwd, local_conf_path):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=300)
        
        # 1. Загружаем финальный конфиг Nginx
        sftp = client.open_sftp()
        sftp.put(local_conf_path, "/root/foodzuka/configs/nginx/default.conf")
        sftp.close()
        
        print("Final Nginx config uploaded.")
        
        # 2. Пересобираем фронтенд и админку (так как домен вшит в билд)
        print("Rebuilding containers (frontend, admin)... This may take a while.")
        # Используем --no-cache для надежности если нужно, но попробуем обычный билд сначала
        cmd = "cd /root/foodzuka && docker compose build frontend admin"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace'))
        print(stderr.read().decode('utf-8', errors='replace'))
        
        # 3. Перезапускаем все сервисы
        print("Restarting all services...")
        cmd = "cd /root/foodzuka && docker compose down && docker compose up -d"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        # 4. Чистим кеш Laravel в админке
        print("Clearing Laravel cache...")
        cmd = "docker exec foodtech-admin php artisan config:clear && docker exec foodtech-admin php artisan cache:clear"
        client.exec_command(cmd)
        
        print("Finalization complete!")
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    LOCAL_PATH = r"c:\Users\v_kva\.gemini\antigravity\scratch\foodtech\scratch\vezuroll_ssl.conf"
    finalize_deployment("178.212.13.48", "12101991Qq", LOCAL_PATH)
