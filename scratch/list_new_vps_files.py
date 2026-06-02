import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def list_files(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        stdin, stdout, stderr = client.exec_command("ls -F /root/foodzuka/")
        print("Files in /root/foodzuka/:")
        out = stdout.read().decode('utf-8', errors='replace')
        print(out.encode('utf-8', errors='replace').decode('ascii', errors='replace'))
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    list_files("178.212.13.48", "12101991Qq")
