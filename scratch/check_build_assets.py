import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def check_build_assets(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        print("--- Public Build Assets ---")
        stdin, stdout, stderr = client.exec_command("ls -lh /root/foodzuka/admin/public/build/assets/")
        print(stdout.read().decode())
        
        stdin, stdout, stderr = client.exec_command("ls -lh /root/foodzuka/admin/resources/js/plugins/iconify/icons.css")
        print("--- Icons CSS ---")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    check_build_assets("178.212.13.48", "12101991Qq")
