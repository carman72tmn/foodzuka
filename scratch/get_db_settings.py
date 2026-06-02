import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def get_db_settings(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        stdin, stdout, stderr = client.exec_command("docker exec foodtech-db psql -U foodtech_user -d foodtech_db -c 'SELECT api_login, organization_id, webhook_url FROM iiko_settings;'")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    get_db_settings("178.212.13.48", "12101991Qq")
