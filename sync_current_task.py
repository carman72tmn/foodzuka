import subprocess
import os
import base64

# Files to sync: (local_path, remote_path)
files_to_sync = [
    ('backend/app/services/iiko_sync_service.py', '/root/foodzuka/backend/app/services/iiko_sync_service.py'),
    ('admin/resources/js/utils/date.js', '/root/foodzuka/admin/resources/js/utils/date.js'),
    ('admin/resources/js/pages/orders/index.vue', '/root/foodzuka/admin/resources/js/pages/orders/index.vue'),
]

def sync_file(local_path, remote_path):
    print(f"Syncing {local_path} -> {remote_path}")
    if not os.path.exists(local_path):
        print(f"File {local_path} not found!")
        return False

    with open(local_path, 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode('ascii')
    
    # Ensure directory exists
    remote_dir = os.path.dirname(remote_path)
    subprocess.run(["ssh", "foodtech", f"mkdir -p {remote_dir}"], check=True)

    # Write file using python on remote
    python_code = f"import sys, base64; open('''{remote_path}''', 'wb').write(base64.b64decode(sys.stdin.read()))"
    cmd = ["ssh", "foodtech", f"python3 -c \"{python_code}\""]
    
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate(input=content_b64)
    
    if process.returncode == 0:
        print(f"Successfully synced {local_path}")
        return True
    else:
        print(f"Error syncing {local_path}: {stderr}")
        return False

if __name__ == "__main__":
    success_count = 0
    for lp, rp in files_to_sync:
        if sync_file(lp, rp):
            success_count += 1
    
    print(f"\nSynced {success_count}/{len(files_to_sync)} files.")
