import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def check_customer_count(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        stdin, stdout, stderr = client.exec_command("docker exec foodtech-db psql -U foodtech_user -d foodtech_db -t -c 'SELECT COUNT(*) FROM customers;'")
        count = stdout.read().decode().strip()
        print(f"Total customers: {count}")
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    check_customer_count("178.212.13.48", "12101991Qq")
