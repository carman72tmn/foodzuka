import os
import subprocess

files_to_deploy = [
    {"local": "backend/app/services/iiko_service.py", "remote": "/root/foodzuka/backend/app/services/iiko_service.py"},
    {"local": "backend/app/services/iiko_sync_service.py", "remote": "/root/foodzuka/backend/app/services/iiko_sync_service.py"},
    {"local": "backend/app/tasks/customer_tasks.py", "remote": "/root/foodzuka/backend/app/tasks/customer_tasks.py"},
    {"local": "backend/app/api/customers.py", "remote": "/root/foodzuka/backend/app/api/customers.py"},
    {"local": "backend/app/models/customer.py", "remote": "/root/foodzuka/backend/app/models/customer.py"},
    {"local": "admin/resources/js/components/CustomerDetailModal.vue", "remote": "/root/foodzuka/admin/resources/js/components/CustomerDetailModal.vue"},
    {"local": "system_faq.md", "remote": "/root/foodzuka/system_faq.md"},
    {"local": "sql_faq.md", "remote": "/root/foodzuka/sql_faq.md"},
    {"local": "sitenav.md", "remote": "/root/foodzuka/sitenav.md"},
    {"local": "backend/app/schemas/__init__.py", "remote": "/root/foodzuka/backend/app/schemas/__init__.py"},
    {"local": "migrate_vps_customers.sql", "remote": "/root/foodzuka/migrate_vps_customers.sql"}
]

def run_ssh_command(cmd):
    full_cmd = ["ssh", "foodtech", cmd]
    try:
        result = subprocess.run(full_cmd, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command '{cmd}': {e.stderr}")
        return None

def deploy():
    # 1. Upload files
    for f in files_to_deploy:
        if not os.path.exists(f["local"]):
            print(f"File {f['local']} not found locally!")
            continue
            
        print(f"Deploying {f['local']} to {f['remote']}...")
        with open(f["local"], "rb") as file:
            content = file.read()
            
        ssh_cmd = ["ssh", "foodtech", f"cat > '{f['remote']}'"]
        try:
            subprocess.run(ssh_cmd, input=content, check=True)
            print(f"Successfully deployed {f['local']}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to deploy {f['local']}: {e}")

    # 2. Run SQL migration
    print("Running SQL migration...")
    sql_cmd = "docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db < /root/foodzuka/migrate_vps_customers.sql"
    run_ssh_command(sql_cmd)
    print("SQL migration finished.")

    # 3. Restart backend and worker
    print("Restarting containers...")
    run_ssh_command("cd /root/foodzuka && docker-compose restart backend worker")
    print("Containers restarted.")

    # 4. Final check
    print("Checking logs...")
    logs = run_ssh_command("docker logs --tail 20 foodtech-backend")
    print("Last backend logs:")
    print(logs)

if __name__ == "__main__":
    deploy()
