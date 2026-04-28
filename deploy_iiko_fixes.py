import subprocess
import os
import base64

# Files to sync
files_to_sync = [
    ('backend/app/models/payment_type.py', '/root/foodzuka/backend/app/models/payment_type.py'),
    ('backend/app/models/company.py', '/root/foodzuka/backend/app/models/company.py'),
    ('backend/app/services/iiko_sync_service.py', '/root/foodzuka/backend/app/services/iiko_sync_service.py'),
    ('backend/app/services/iiko_service.py', '/root/foodzuka/backend/app/services/iiko_service.py'),
    ('backend/app/api/iiko.py', '/root/foodzuka/backend/app/api/iiko.py'),
    ('backend/requirements.txt', '/root/foodzuka/backend/requirements.txt'),
    ('admin/resources/js/pages/settings/iiko.vue', '/root/foodzuka/admin/resources/js/pages/settings/iiko.vue'),
    ('migrate_iiko_v2.sql', '/root/foodzuka/migrate_iiko_v2.sql'),
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

    # Write file
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

# 1. Sync files
for lp, rp in files_to_sync:
    sync_file(lp, rp)

# 2. Run migrations
print("Running database migrations on VPS...")
migrate_cmd = "docker exec -i f79cf995da66_foodtech-db psql -U foodtech_user -d foodtech_db < /root/foodzuka/migrate_iiko_v2.sql"
subprocess.run(["ssh", "foodtech", migrate_cmd], check=True)


# 3. Build admin on VPS
print("Building admin frontend on VPS...")
build_cmd = "cd /root/foodzuka/admin && npm install && npm run build"
subprocess.run(["ssh", "foodtech", build_cmd], check=True)

# 4. Restart services
print("Restarting services on VPS...")
restart_cmd = "cd /root/foodzuka && docker-compose restart backend admin"
subprocess.run(["ssh", "foodtech", restart_cmd], check=True)

print("Deployment finished!")
