import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def issue_ssl(ip, pwd, domain):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=60)
        
        print(f"Issuing SSL for {domain}...")
        # Используем существующий контейнер certbot с переопределением entrypoint
        cmd = f"cd /root/foodzuka && docker compose run --rm --entrypoint certbot certbot certonly --webroot --webroot-path /var/www/certbot/ --email admin@{domain} --agree-tos --no-eff-email -d {domain} -d www.{domain}"
        
        stdin, stdout, stderr = client.exec_command(cmd)
        
        # Читаем вывод полностью
        out = stdout.read().decode()
        err = stderr.read().decode()
        
        print("STDOUT:")
        print(out)
        print("STDERR:")
        print(err)
        
        if "Successfully received certificate" in out or "Certificate not yet due for renewal" in out:
            print("SSL Certificate successfully obtained!")
            return True
        else:
            print("SSL Certificate issuance FAILED.")
            return False
            
        client.close()
    except Exception as e:
        print(f"Failed: {e}")
        return False

if __name__ == "__main__":
    issue_ssl("178.212.13.48", "12101991Qq", "vezuroll.ru")
