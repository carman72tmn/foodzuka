import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def update_admin_env(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        # Обновляем APP_URL и ASSET_URL на IP
        cmd = (
            "sed -i 's|APP_URL=https://72roll.ru/admin|APP_URL=http://178.212.13.48/admin|' /root/foodzuka/admin/.env && "
            "sed -i 's|ASSET_URL=https://72roll.ru/admin|ASSET_URL=http://178.212.13.48/admin|' /root/foodzuka/admin/.env"
        )
        stdin, stdout, stderr = client.exec_command(cmd)
        print("Updated .env")
        
        # Пересобираем админку
        print("Rebuilding admin panel...")
        stdin, stdout, stderr = client.exec_command("cd /root/foodzuka && docker compose build admin && docker compose up -d admin")
        
        # Читаем вывод по мере поступления, чтобы избежать проблем с кодировкой и видеть прогресс
        for line in stdout:
            try:
                print(f"OUT: {line.strip()}")
            except:
                pass
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    update_admin_env("178.212.13.48", "12101991Qq")
