import subprocess
import os
import base64

files_to_sync = [
    ('backend/app/services/iiko_sync_service.py', '/root/foodzuka/backend/app/services/iiko_sync_service.py'),
    ('backend/app/api/webhooks.py', '/root/foodzuka/backend/app/api/webhooks.py'),
]

for local_path, remote_path in files_to_sync:
    print(f"Syncing {local_path} -> {remote_path}")
    if not os.path.exists(local_path):
        print(f"File {local_path} not found!")
        continue

    with open(local_path, 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode('ascii')
    
    # Use python3 on remote to decode and write. 
    # Use triple quotes for paths to avoid middle-quoting issues.
    python_code = f"import sys, base64; open('''{remote_path}''', 'wb').write(base64.b64decode(sys.stdin.read()))"
    cmd = ["ssh", "foodtech", f"python3 -c \"{python_code}\""]
    
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate(input=content_b64)
    
    if process.returncode == 0:
        print(f"Successfully synced {local_path}")
    else:
        print(f"Error syncing {local_path}: {stderr}")

print("Done.")
