import base64
import subprocess
import os

lp = 'configs/nginx/default.conf'
rp = '/root/foodzuka/configs/nginx/default.conf'

with open(lp, 'rb') as f:
    content = base64.b64encode(f.read()).decode('ascii')

python_code = f"import sys, base64; open('{rp}', 'wb').write(base64.b64decode(sys.stdin.read()))"
cmd = ["ssh", "vezuroll", f"python3 -c \"{python_code}\""]

process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
stdout, stderr = process.communicate(input=content)

if process.returncode == 0:
    print("Synced successfully")
else:
    print(f"Error: {stderr}")
