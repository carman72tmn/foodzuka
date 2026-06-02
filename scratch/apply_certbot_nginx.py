import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def apply_certbot_nginx(ip, pwd, local_conf_path):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        # Загружаем файл
        sftp = client.open_sftp()
        sftp.put(local_conf_path, "/root/foodzuka/configs/nginx/default.conf")
        sftp.close()
        
        # Создаем директорию для certbot если нет
        client.exec_command("mkdir -p /root/foodzuka/certbot/www")
        
        # Перезапускаем Nginx
        stdin, stdout, stderr = client.exec_command("docker restart foodtech-nginx")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    LOCAL_PATH = r"c:\Users\v_kva\.gemini\antigravity\scratch\foodtech\scratch\certbot_nginx.conf"
    apply_certbot_nginx("178.212.13.48", "12101991Qq", LOCAL_PATH)
