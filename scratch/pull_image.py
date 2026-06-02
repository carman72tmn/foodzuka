import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def pull_image(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        print("--- Pulling node:20-alpine ---")
        stdin, stdout, stderr = client.exec_command("docker pull node:20-alpine")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    pull_image("178.212.13.48", "12101991Qq")
