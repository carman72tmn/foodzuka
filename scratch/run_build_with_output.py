import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def run_build_and_get_output(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=60)
        
        print("--- Running Docker Build Command ---")
        # I'll use a shorter command first to see if it works
        stdin, stdout, stderr = client.exec_command("cd /root/foodzuka/admin && docker run --rm -v $(pwd):/app -w /app node:20-alpine node -v")
        print(f"Node Version Check: {stdout.read().decode().strip()}")
        
        print("--- Starting npm install & build ---")
        stdin, stdout, stderr = client.exec_command("cd /root/foodzuka/admin && docker run --rm -v $(pwd):/app -w /app node:20-alpine sh -c 'npm install --no-audit && npm run build'")
        
        # Read output line by line
        for line in stdout:
            print(line, end="")
        for line in stderr:
            print(line, end="")
            
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    run_build_and_get_output("178.212.13.48", "12101991Qq")
