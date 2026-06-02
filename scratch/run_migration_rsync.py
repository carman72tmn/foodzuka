import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def run_rsync(new_ip, new_pwd, old_ip):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(new_ip, username="root", password=new_pwd, timeout=30)
        
        cmd = f"rsync -avzP --exclude='node_modules' --exclude='.git' root@{old_ip}:/root/foodzuka/ /root/foodzuka/"
        
        print(f"Starting rsync from {old_ip} to {new_ip}...")
        stdin, stdout, stderr = client.exec_command(cmd)
        
        # Устанавливаем кодировку для stdout
        for line in stdout:
            try:
                print(f"OUT: {line.strip()}")
            except UnicodeEncodeError:
                print(f"OUT: {line.encode('utf-8', errors='replace').decode('ascii', errors='replace')}")
        
        for line in stderr:
            try:
                print(f"ERR: {line.strip()}")
            except UnicodeEncodeError:
                print(f"ERR: {line.encode('utf-8', errors='replace').decode('ascii', errors='replace')}")
            
        client.close()
    except Exception as e:
        print(f"Rsync failed: {e}")

if __name__ == "__main__":
    run_rsync("178.212.13.48", "12101991Qq", "159.194.215.126")
