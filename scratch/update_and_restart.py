import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def update_env_and_restart(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        print("--- Updating .env to HTTPS ---")
        client.exec_command("sed -i 's|APP_PUBLIC_URL=http://vezuroll.ru|APP_PUBLIC_URL=https://vezuroll.ru|' /root/foodzuka/backend/.env")
        
        print("--- Restarting Backend ---")
        stdin, stdout, stderr = client.exec_command("cd /root/foodzuka && docker compose restart backend")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    update_env_and_restart("178.212.13.48", "12101991Qq")
