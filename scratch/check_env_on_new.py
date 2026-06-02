import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def check_env(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        print("--- Admin .env ---")
        stdin, stdout, stderr = client.exec_command("cat /root/foodzuka/admin/.env")
        print(stdout.read().decode())
        
        print("--- Root .env ---")
        stdin, stdout, stderr = client.exec_command("cat /root/foodzuka/.env")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    check_env("178.212.13.48", "12101991Qq")
