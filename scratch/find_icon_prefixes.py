import sys
import os

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def find_icon_prefixes(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        print("--- Icon prefixes found in .vue files ---")
        cmd = "grep -r 'icon=' /root/foodzuka/admin/resources/js/ | grep -oP 'icon=\"[^\"]+\"' | cut -d'\"' -f2 | cut -d'-' -f1 | sort | uniq"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    find_icon_prefixes("178.212.13.48", "12101991Qq")
