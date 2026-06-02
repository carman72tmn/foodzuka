import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def fix_asset_url(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        # Добавляем ASSET_URL если его нет или обновляем
        client.exec_command("grep -q 'ASSET_URL' /root/foodzuka/admin/.env && sed -i 's|ASSET_URL=.*|ASSET_URL=https://vezuroll.ru/admin|g' /root/foodzuka/admin/.env || echo 'ASSET_URL=https://vezuroll.ru/admin' >> /root/foodzuka/admin/.env")
        
        # Очистка кеша
        client.exec_command("docker exec foodtech-admin php artisan config:clear")
        
        print("ASSET_URL updated.")
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    fix_asset_url("178.212.13.48", "12101991Qq")
