import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def fix_env_https(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        # Меняем http на https
        client.exec_command("sed -i 's|APP_URL=http://vezuroll.ru|APP_URL=https://vezuroll.ru|g' /root/foodzuka/admin/.env")
        
        # Добавляем FORCE_HTTPS если его нет
        client.exec_command("grep -q 'FORCE_HTTPS' /root/foodzuka/admin/.env || echo 'FORCE_HTTPS=true' >> /root/foodzuka/admin/.env")
        
        # Очистка кеша
        client.exec_command("docker exec foodtech-admin php artisan config:clear")
        client.exec_command("docker exec foodtech-admin php artisan cache:clear")
        
        print("Env updated and cache cleared.")
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    fix_env_https("178.212.13.48", "12101991Qq")
