import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def fix_frontend_urls(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        # Меняем https://72roll.ru/api/v1 на /api/v1
        cmd = (
            "sed -i \"s|'https://72roll.ru/api/v1'|'/api/v1'|g\" /root/foodzuka/frontend/src/api/catalog.js && "
            "sed -i \"s|'https://72roll.ru/api/v1'|'/api/v1'|g\" /root/foodzuka/frontend/src/api/order.js"
        )
        stdin, stdout, stderr = client.exec_command(cmd)
        print("Updated frontend URLs.")
        
        # Пересобираем фронтенд
        print("Rebuilding frontend...")
        stdin, stdout, stderr = client.exec_command("cd /root/foodzuka && docker compose build frontend && docker compose up -d frontend")
        
        for line in stdout:
            try:
                print(f"OUT: {line.strip()}")
            except:
                pass
                
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    fix_frontend_urls("178.212.13.48", "12101991Qq")
