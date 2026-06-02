import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def check_db_data(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        print("--- Database Tables and Counts ---")
        tables = ["clients", "orders", "users", "sync_logs"]
        for table in tables:
            cmd = f"docker exec foodtech-db psql -U foodtech_user -d foodtech_db -t -c 'SELECT COUNT(*) FROM {table};'"
            stdin, stdout, stderr = client.exec_command(cmd)
            count = stdout.read().decode().strip()
            if count:
                print(f"Table {table}: {count} rows")
            else:
                err = stderr.read().decode().strip()
                print(f"Table {table}: Error or missing ({err})")
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    check_db_data("178.212.13.48", "12101991Qq")
