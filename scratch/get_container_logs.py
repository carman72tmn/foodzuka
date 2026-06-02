import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def get_container_logs(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        print("--- Docker Container Logs ---")
        stdin, stdout, stderr = client.exec_command("docker ps -a --filter 'ancestor=node:20-alpine' --format '{{.ID}}' | head -n 1")
        container_id = stdout.read().decode().strip()
        if container_id:
            print(f"Container ID: {container_id}")
            stdin, stdout, stderr = client.exec_command(f"docker logs {container_id}")
            print(stdout.read().decode())
            print(stderr.read().decode())
        else:
            print("No node:20-alpine container found.")
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    get_container_logs("178.212.13.48", "12101991Qq")
