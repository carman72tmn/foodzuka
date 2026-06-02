import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def fix_iiko_creds(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        # Update both api_login and webhook_url
        cmd = "docker exec foodtech-db psql -U foodtech_user -d foodtech_db -c \"UPDATE iiko_settings SET api_login = '86dfd64bd15c42199b789edf6adcb289', webhook_url = 'https://vezuroll.ru/api/v1/webhooks/iiko';\""
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    fix_iiko_creds("178.212.13.48", "12101991Qq")
