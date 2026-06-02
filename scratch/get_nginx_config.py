import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def get_nginx_config(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        # Поиск конфига
        cmds = [
            "cat /etc/nginx/sites-enabled/default",
            "cat /etc/nginx/conf.d/default.conf",
            "cat /etc/nginx/sites-available/foodtech.conf",
            "ls /etc/nginx/sites-enabled/"
        ]
        
        for cmd in cmds:
            print(f"--- Running: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode())
            print(stderr.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    get_nginx_config("178.212.13.48", "12101991Qq")
