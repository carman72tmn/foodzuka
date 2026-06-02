import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def check_dirs(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        paths = [
            "/root/foodzuka/admin/node_modules/@iconify-json/tabler",
            "/root/foodzuka/admin/node_modules/@iconify-json/mdi",
            "/root/foodzuka/admin/node_modules/@iconify/tools"
        ]
        
        for path in paths:
            print(f"--- Checking {path} ---")
            stdin, stdout, stderr = client.exec_command(f"ls -d {path}")
            print(stdout.read().decode())
            print(stderr.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    check_dirs("178.212.13.48", "12101991Qq")
