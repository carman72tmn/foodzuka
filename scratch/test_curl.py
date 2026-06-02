import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def test_curl(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        print("--- Curl Frontend from Host ---")
        stdin, stdout, stderr = client.exec_command("curl -I http://172.18.0.5") # Assuming 172.18.0.5 from previous logs
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        print("--- Curl Frontend by Name ---")
        stdin, stdout, stderr = client.exec_command("docker exec foodtech-nginx curl -I http://frontend")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_curl("178.212.13.48", "12101991Qq")
