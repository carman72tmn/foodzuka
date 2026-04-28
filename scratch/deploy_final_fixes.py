import subprocess
import os

FILES_TO_SYNC = [
    ('backend/app/schemas/__init__.py', '/root/foodzuka/backend/app/schemas/__init__.py'),
    ('admin/resources/js/main.js', '/root/foodzuka/admin/resources/js/main.js'),
    ('admin/resources/js/components/CustomerDetailModal.vue', '/root/foodzuka/admin/resources/js/components/CustomerDetailModal.vue')
]

def deploy():
    print("Deploying final fixes to VPS...")
    for local_path, remote_path in FILES_TO_SYNC:
        print(f"Syncing {local_path}...")
        cmd = f"scp {local_path} foodtech:{remote_path}"
        subprocess.run(cmd, shell=True)

    print("Restarting Backend and Rebuilding Frontend...")
    remote_cmd = "cd /root/foodzuka && docker-compose restart backend && docker exec -it foodtech-admin npm run build"
    # Using non-interactive exec for npm run build
    remote_cmd_safe = "cd /root/foodzuka && docker-compose restart backend && docker exec foodtech-admin npm run build"
    
    subprocess.run(f"ssh foodtech \"{remote_cmd_safe}\"", shell=True)
    print("Deployment complete.")

if __name__ == "__main__":
    deploy()
