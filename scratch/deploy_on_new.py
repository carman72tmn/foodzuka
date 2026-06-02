import sys
import os
import time

# Добавляем путь к установленным библиотекам
sys.path.append(r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\libs')

import paramiko

def deploy_new_server(ip, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username="root", password=pwd, timeout=30)
        
        # 1. Запуск БД и Redis
        print("Starting DB and Redis...")
        stdin, stdout, stderr = client.exec_command("cd /root/foodzuka && docker compose up -d db redis")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 2. Ждем готовности БД (pg_isready)
        print("Waiting for database to be ready...")
        for i in range(20):
            stdin, stdout, stderr = client.exec_command("docker exec foodtech-db pg_isready -U foodtech_user")
            res = stdout.read().decode()
            if "accepting connections" in res:
                print("Database is ready!")
                break
            time.sleep(2)
        else:
            print("Database not ready after 40 seconds. Continuing anyway...")
            
        # 3. Импорт дампа
        print("Importing database dump...")
        # Используем cat и пайп в docker exec psql
        cmd = "cat /root/foodzuka/db_backup.sql | docker exec -i foodtech-db psql -U foodtech_user -d foodtech_db"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 4. Запуск всех остальных контейнеров
        print("Starting all services...")
        stdin, stdout, stderr = client.exec_command("cd /root/foodzuka && docker compose up -d")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 5. Проверка статуса
        stdin, stdout, stderr = client.exec_command("docker compose ps")
        print("Docker containers status:")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Deployment failed: {e}")

if __name__ == "__main__":
    deploy_new_server("178.212.13.48", "12101991Qq")
