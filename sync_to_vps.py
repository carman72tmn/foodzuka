import subprocess
import os
import base64

# Files to sync: (local_path, remote_path)
files_to_sync = [
    ('backend/app/services/iiko_service.py', '/root/foodzuka/backend/app/services/iiko_service.py'),
    ('backend/app/services/iiko_sync_service.py', '/root/foodzuka/backend/app/services/iiko_sync_service.py'),
    ('backend/app/core/scheduler.py', '/root/foodzuka/backend/app/core/scheduler.py'),
    ('backend/app/core/logging_utils.py', '/root/foodzuka/backend/app/core/logging_utils.py'),
    ('backend/app/tasks/customer_tasks.py', '/root/foodzuka/backend/app/tasks/customer_tasks.py'),
    ('backend/app/api/webhooks.py', '/root/foodzuka/backend/app/api/webhooks.py'),
    ('backend/app/api/customers.py', '/root/foodzuka/backend/app/api/customers.py'),
    ('backend/app/api/loyalty.py', '/root/foodzuka/backend/app/api/loyalty.py'),
    ('backend/app/api/vk_bot_admin.py', '/root/foodzuka/backend/app/api/vk_bot_admin.py'),
    ('backend/main.py', '/root/foodzuka/backend/main.py'),
    ('backend/trigger_sync_vps.py', '/root/foodzuka/backend/trigger_sync_vps.py'),
    ('backend/test_customer_sync_vps.py', '/root/foodzuka/backend/test_customer_sync_vps.py'),
    ('cleanup_phones.py', '/root/foodzuka/backend/cleanup_phones.py'),
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
    
    if success_count == len(files_to_sync):
        print("Restarting backend service...")
        subprocess.run(["ssh", "foodtech", "cd /root/foodzuka && docker-compose restart backend"], check=True)
        print("Done!")
    else:
        print("Some files failed to sync. Not restarting.")
