import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def sync_and_rebuild_admin(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=300)
        
        sftp = client.open_sftp()
        
        # 1. Загружаем Dockerfile
        local_dockerfile = r"c:\Users\v_kva\.gemini\antigravity\scratch\foodtech\admin\Dockerfile"
        sftp.put(local_dockerfile, "/root/foodzuka/admin/Dockerfile")
        
        # 2. Загружаем AppServiceProvider.php
        local_provider = r"c:\Users\v_kva\.gemini\antigravity\scratch\foodtech\admin\app\Providers\AppServiceProvider.php"
        sftp.put(local_provider, "/root/foodzuka/admin/app/Providers/AppServiceProvider.php")
        
        sftp.close()
        print("Files uploaded.")
        
        # 3. Пересобираем и перезапускаем админку
        print("Rebuilding admin container with new extensions...")
        cmd = "cd /root/foodzuka && docker compose build admin && docker compose up -d admin"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace'))
        print(stderr.read().decode('utf-8', errors='replace'))
        
        # 4. Очистка кеша
        client.exec_command("docker exec foodtech-admin php artisan config:clear")
        
        print("Admin update complete!")
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    sync_and_rebuild_admin("178.212.13.48", "12101991Qq")
