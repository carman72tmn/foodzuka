import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def fast_update_admin(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        sftp = client.open_sftp()
        local_provider = r"c:\Users\v_kva\.gemini\antigravity\scratch\foodtech\admin\app\Providers\AppServiceProvider.php"
        sftp.put(local_provider, "/tmp/AppServiceProvider.php")
        sftp.close()
        
        # Копируем в контейнер
        client.exec_command("docker cp /tmp/AppServiceProvider.php foodtech-admin:/var/www/html/app/Providers/AppServiceProvider.php")
        
        # Очистка кеша
        client.exec_command("docker exec foodtech-admin php artisan config:clear")
        client.exec_command("docker exec foodtech-admin php artisan view:clear")
        
        print("Fast update complete!")
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    fast_update_admin("178.212.13.48", "12101991Qq")
