import subprocess
import os
import base64

files = [
    ('backend/app/api/courier.py', '/root/foodzuka/backend/app/api/courier.py'),
    ('backend/app/services/iiko_service.py', '/root/foodzuka/backend/app/services/iiko_service.py'),
    ('admin/resources/js/pages/employee/courier.vue', '/root/foodzuka/admin/resources/js/pages/employee/courier.vue'),
]

def sync(local, remote):
    print(f"Syncing {local} -> {remote}")
    with open(local, 'rb') as f:
        content = base64.b64encode(f.read()).decode('ascii')
    
    # Ensure dir
    remote_dir = os.path.dirname(remote)
    subprocess.run(["ssh", "vezuroll", f"mkdir -p {remote_dir}"], check=True)
    
    # Write
    python_code = f"import sys, base64; open('''{remote}''', 'wb').write(base64.b64decode(sys.stdin.read()))"
    cmd = ["ssh", "vezuroll", f"python3 -c \"{python_code}\""]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
    p.communicate(input=content)
    return p.returncode == 0

if __name__ == "__main__":
    for l, r in files:
        if sync(l, r):
            print(f"Done: {l}")
        else:
            print(f"Failed: {l}")
    
    print("\nRestarting backend...")
    subprocess.run(["ssh", "vezuroll", "cd /root/foodzuka && docker compose -f docker-compose.prod.yml restart backend worker"], check=True)
    
    print("\nRebuilding frontend (admin)...")
    # Usually we need to run npm run build inside the container
    # Or outside if node is available.
    # Looking at docker-compose, 'admin' is the service name.
    subprocess.run(["ssh", "vezuroll", "docker exec foodtech-admin npm run build"], check=True)
    
    print("\nAll done!")
