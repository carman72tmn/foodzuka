import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def migrate_to_new_domain(ip, pwd, new_domain):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        # Список файлов и замен
        replacements = [
            # Админка .env
            (f"/root/foodzuka/admin/.env", "72roll.ru", new_domain),
            (f"/root/foodzuka/admin/.env", "178.212.13.48", new_domain),
            # Бэкенд .env
            (f"/root/foodzuka/backend/.env", "72roll.ru", new_domain),
            (f"/root/foodzuka/backend/.env", "178.212.13.48", new_domain),
            # Бэкенд main.py (CORS)
            (f"/root/foodzuka/backend/main.py", "72roll.ru", new_domain),
            (f"/root/foodzuka/backend/main.py", "178.212.13.48", new_domain),
            # Фронтенд vite.config.js
            (f"/root/foodzuka/frontend/vite.config.js", "72roll.ru", new_domain),
            (f"/root/foodzuka/frontend/vite.config.js", "178.212.13.48", new_domain),
        ]
        
        for file_path, old, new in replacements:
            print(f"Replacing '{old}' with '{new}' in {file_path}...")
            cmd = f"sed -i 's|{old}|{new}|g' {file_path}"
            client.exec_command(cmd)
            
        print("Domain migration in configs completed.")
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    migrate_to_new_domain("178.212.13.48", "12101991Qq", "vezuroll.ru")
