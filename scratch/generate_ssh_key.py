import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def setup_ssh_key(ip, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=username, password=password, timeout=30)
        
        # Генерируем ключ, если его нет
        cmd = "ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_ed25519"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # Читаем публичный ключ
        stdin, stdout, stderr = client.exec_command("cat ~/.ssh/id_ed25519.pub")
        pub_key = stdout.read().decode().strip()
        print(f"PUBLIC_KEY:{pub_key}")
        
        client.close()
        return pub_key
    except Exception as e:
        print(f"SSH Setup failed: {e}")
        return None

if __name__ == "__main__":
    NEW_IP = "178.212.13.48"
    PWD = "12101991Qq"
    setup_ssh_key(NEW_IP, "root", PWD)
