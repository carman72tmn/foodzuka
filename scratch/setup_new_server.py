import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def execute_remote(ip, username, password, commands):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=username, password=password, timeout=30)
        
        for cmd in commands:
            print(f"Executing: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            
            # Читаем вывод в реальном времени
            for line in stdout:
                print(f"OUT: {line.strip()}")
            
            for line in stderr:
                print(f"ERR: {line.strip()}")
                
        client.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    NEW_IP = "178.212.13.48"
    PWD = "12101991Qq"
    
    # Список команд для установки базы
    setup_commands = [
        "apt-get update",
        "apt-get install -y curl git rsync htop python3-pip",
        # Установка Docker
        "curl -fsSL https://get.docker.com -o get-docker.sh",
        "sh get-docker.sh",
        "apt-get install -y docker-compose-v2",
        # Установка Node.js v20
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs",
        # Проверка версий
        "docker --version && docker compose version && node -v && npm -v && python3 --version"
    ]
    
    execute_remote(NEW_IP, "root", PWD, setup_commands)
