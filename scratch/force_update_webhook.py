import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def force_update_webhook(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        print("--- Updating Webhook URL in DB ---")
        stdin, stdout, stderr = client.exec_command("docker exec foodtech-db psql -U foodtech_user -d foodtech_db -c \"UPDATE iiko_settings SET webhook_url = 'https://vezuroll.ru/api/v1/webhooks/iiko';\"")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    force_update_webhook("178.212.13.48", "12101991Qq")
