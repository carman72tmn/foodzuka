import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def check_challenge(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        # Создаем тестовый файл
        client.exec_command("mkdir -p /root/foodzuka/certbot/www/.well-known/acme-challenge")
        client.exec_command("echo 'test' > /root/foodzuka/certbot/www/.well-known/acme-challenge/test")
        
        print("--- Testing challenge URL ---")
        stdin, stdout, stderr = client.exec_command("curl -L -I http://vezuroll.ru/.well-known/acme-challenge/test")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    check_challenge("178.212.13.48", "12101991Qq")
