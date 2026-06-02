import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def verify_icons_in_bundle(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        # Checking for common icons from different sets
        tests = [
            (".bx-home", "Boxicons"),
            (".mdi-account", "MDI"),
            (".ri-home-line", "Remix"),
            (".tabler-home", "Tabler")
        ]
        
        bundle_path = "/root/foodzuka/admin/public/build/assets/main-DPq03eRN.css"
        
        print(f"--- Verifying Icons in {bundle_path} ---")
        for selector, name in tests:
            stdin, stdout, stderr = client.exec_command(f"grep -o '{selector}' {bundle_path} | head -n 1")
            found = stdout.read().decode().strip()
            if found:
                print(f"[OK] {name} icons found ({selector})")
            else:
                print(f"[FAIL] {name} icons NOT found ({selector})")
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    verify_icons_in_bundle("178.212.13.48", "12101991Qq")
