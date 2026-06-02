import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def update_bootstrap_app(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        sftp = client.open_sftp()
        local_app = r"c:\Users\v_kva\.gemini\antigravity\scratch\foodtech\admin\bootstrap\app.php"
        sftp.put(local_app, "/root/foodzuka/admin/bootstrap/app.php")
        sftp.close()
        
        # Очистка кеша
        client.exec_command("docker exec foodtech-admin php artisan config:clear")
        client.exec_command("docker exec foodtech-admin php artisan cache:clear")
        client.exec_command("docker exec foodtech-admin php artisan view:clear")
        
        print("Bootstrap/app.php updated and cache cleared.")
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    update_bootstrap_app("178.212.13.48", "12101991Qq")
