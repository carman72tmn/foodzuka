import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def check_ssh(ip, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {ip} as {username}...")
        client.connect(ip, username=username, password=password, timeout=10)
        print("Successfully connected!")
        
        stdin, stdout, stderr = client.exec_command("uname -a && lsb_release -a && free -h && df -h")
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if output:
            print("Server Info:")
            print(output)
        if error:
            print("Errors:")
            print(error)
            
        client.close()
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    check_ssh("178.212.13.48", "root", "12101991Qq")
