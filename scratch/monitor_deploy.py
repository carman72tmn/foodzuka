import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def check_docker_status(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        print("--- Docker PS ---")
        stdin, stdout, stderr = client.exec_command("docker ps")
        print(stdout.read().decode())
        
        print("--- Docker Images ---")
        stdin, stdout, stderr = client.exec_command("docker images")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    check_docker_status("178.212.13.48", "12101991Qq")
