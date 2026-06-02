import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def check_prefixes_in_bundle(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        bundle_path = "/root/foodzuka/admin/public/build/assets/main-DPq03eRN.css"
        
        print(f"--- Prefixes in {bundle_path} ---")
        prefixes = ["bx-", "mdi-", "ri-", "tabler-"]
        for p in prefixes:
            stdin, stdout, stderr = client.exec_command(f"grep -o '.{p}' {bundle_path} | head -n 1")
            found = stdout.read().decode().strip()
            if found:
                print(f"[OK] Prefix {p} found")
            else:
                print(f"[MISSING] Prefix {p} NOT found")
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    check_prefixes_in_bundle("178.212.13.48", "12101991Qq")
