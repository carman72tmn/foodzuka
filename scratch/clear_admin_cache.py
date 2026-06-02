import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def clear_laravel_cache(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        print("Clearing Laravel cache...")
        cmd = "docker exec foodtech-admin php artisan config:clear && docker exec foodtech-admin php artisan cache:clear && docker exec foodtech-admin php artisan route:clear"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    clear_laravel_cache("178.212.13.48", "12101991Qq")
