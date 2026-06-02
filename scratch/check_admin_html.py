import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def check_admin_html(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        print("--- Testing Admin Login HTML ---")
        # Проверяем через домен (чтобы увидеть что видит пользователь)
        stdin, stdout, stderr = client.exec_command("curl -k -L https://vezuroll.ru/admin/login")
        html = stdout.read().decode('utf-8', errors='replace')
        print(html[:2000]) # Печатаем первые 2000 символов
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    check_admin_html("178.212.13.48", "12101991Qq")
