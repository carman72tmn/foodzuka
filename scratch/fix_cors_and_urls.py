import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def fix_backend_urls(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        # 1. backend/.env
        cmd = "sed -i 's|APP_PUBLIC_URL=https://72roll.ru|APP_PUBLIC_URL=http://178.212.13.48|' /root/foodzuka/backend/.env"
        client.exec_command(cmd)
        
        # 2. backend/main.py (CORS)
        # Добавляем IP в разрешенные источники
        cmd = "sed -i \"s|'https://72roll.ru'|'http://178.212.13.48', 'https://72roll.ru'|g\" /root/foodzuka/backend/main.py"
        client.exec_command(cmd)
        
        # 3. frontend/vite.config.js
        cmd = "sed -i \"s|'72roll.ru'|'178.212.13.48', '72roll.ru'|g\" /root/foodzuka/frontend/vite.config.js"
        client.exec_command(cmd)
        
        print("Updated backend and frontend configs.")
        
        # Перезапускаем все для верности (кроме БД)
        print("Restarting services...")
        stdin, stdout, stderr = client.exec_command("cd /root/foodzuka && docker compose restart backend worker bot admin frontend nginx")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    fix_backend_urls("178.212.13.48", "12101991Qq")
