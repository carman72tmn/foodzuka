import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def test_internal_ssh(new_ip, new_pwd, old_ip):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(new_ip, username="root", password=new_pwd, timeout=30)
        
        # Пробуем подключиться с нового сервера на старый
        cmd = f"ssh -o StrictHostKeyChecking=no root@{old_ip} 'uname -a'"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        print(f"Result from old server: {output}")
        if error:
            print(f"Error: {error}")
            
        client.close()
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_internal_ssh("178.212.13.48", "12101991Qq", "159.194.215.126")
