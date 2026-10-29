"""
API эндпоинты для управления системными процессами и файлами
"""
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import require_permission
from app.models.user import User
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.sync_log import SyncStatus
from app.models.scheduled_task import ScheduledTask
from app.core.celery_app import celery_app
from app.core.scheduler import scheduler, add_scheduled_job
import os
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/tasks", response_model=List[SyncStatus], dependencies=[Depends(require_permission("system_tasks_view"))])
def get_tasks(session: Session = Depends(get_session)):
    """Список всех фоновых задач"""
    return session.exec(select(SyncStatus).order_by(SyncStatus.updated_at.desc())).all()

@router.post("/tasks/stop-all", dependencies=[Depends(require_permission("system_tasks_edit"))])
def stop_all_tasks(session: Session = Depends(get_session)):
    """Остановить все активные задачи"""
    running_tasks = session.exec(select(SyncStatus).where(SyncStatus.status == "running")).all()
    count = 0
    for task in running_tasks:
        if task.task_id and task.task_id != "pending":
            try:
                celery_app.control.revoke(task.task_id, terminate=True)
                count += 1
            except Exception as e:
                logger.error(f"Error revoking task {task.task_id}: {e}")
        task.status = "cancelled"
        session.add(task)
    
    # Также очищаем очередь
    try:
        celery_app.control.purge()
    except:
        pass
        
    session.commit()
    return {"status": "success", "stopped_count": count}

@router.post("/tasks/cleanup", dependencies=[Depends(require_permission("system_tasks_edit"))])
def cleanup_tasks(session: Session = Depends(get_session)):
    """Очистить завершенные и ошибочные задачи"""
    to_delete = session.exec(
        select(SyncStatus).where(SyncStatus.status.in_(["completed", "error", "cancelled"]))
    ).all()
    count = len(to_delete)
    for task in to_delete:
        session.delete(task)
    session.commit()
    return {"status": "success", "deleted_count": count}

@router.post("/tasks/run", dependencies=[Depends(require_permission("system_tasks_edit"))])
def run_task(task_type: str, params: dict = {}, session: Session = Depends(get_session)):
    """Запуск новой задачи вручную"""
    # Создаем запись в SyncStatus
    new_status = SyncStatus(
        task_id="pending",
        sync_type=task_type,
        status="pending",
        details=f"Запуск задачи {task_type} вручную...",
        updated_at=datetime.now(timezone.utc)
    )
    session.add(new_status)
    session.commit()
    session.refresh(new_status)

    task_id = None
    try:
        if task_type == "customers":
            from app.tasks.customer_tasks import sync_customers_batch
            res = sync_customers_batch.apply_async(
                kwargs={"status_id": new_status.id, "force_update": params.get("force_update", False)}
            )
            task_id = res.id
        elif task_type == "menu":
            from app.tasks.general_tasks import sync_menu_task
            res = sync_menu_task.apply_async(kwargs={"status_id": new_status.id})
            task_id = res.id
        elif task_type == "orders":
            from app.tasks.general_tasks import sync_orders_task
            res = sync_orders_task.apply_async(
                kwargs={"status_id": new_status.id, "hours": params.get("hours", 24)}
            )
            task_id = res.id
        else:
            raise HTTPException(status_code=400, detail=f"Unknown task type: {task_type}")

        if task_id:
            new_status.task_id = task_id
            session.add(new_status)
            session.commit()
            return {"status": "success", "task_id": task_id, "sync_id": new_status.id}
        else:
             raise Exception("Failed to start task")
             
    except Exception as e:
        logger.error(f"Error starting task {task_type}: {e}")
        new_status.status = "error"
        new_status.details = str(e)
        session.add(new_status)
        session.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/pause", dependencies=[Depends(require_permission("system_tasks_edit"))])
def toggle_task_pause(task_id: int, session: Session = Depends(get_session)):
    """Переключение паузы задачи"""
    sync_status = session.get(SyncStatus, task_id)
    if not sync_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    sync_status.is_paused = not sync_status.is_paused
    session.add(sync_status)
    session.commit()
    session.refresh(sync_status)
    return sync_status

@router.post("/tasks/{task_id}/cancel", dependencies=[Depends(require_permission("system_tasks_edit"))])
def cancel_task(task_id: int, session: Session = Depends(get_session)):
    """Отмена задачи"""
    sync_status = session.get(SyncStatus, task_id)
    if not sync_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Отменяем в Celery
    if sync_status.task_id and sync_status.task_id != "pending":
        try:
            celery_app.control.revoke(sync_status.task_id, terminate=True)
        except Exception as e:
            logger.error(f"Error revoking task {sync_status.task_id}: {e}")
    
    sync_status.status = "cancelled"
    sync_status.is_paused = False
    session.add(sync_status)
    session.commit()
    session.refresh(sync_status)
    return sync_status

@router.post("/tasks/{task_id}/refresh", dependencies=[Depends(require_permission("system_tasks_edit"))])
def refresh_task_status(task_id: int, session: Session = Depends(get_session)):
    """Принудительное обновление статуса задачи из Celery"""
    sync_status = session.get(SyncStatus, task_id)
    if not sync_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Если задача в статусе running, проверяем её реальное состояние в Celery
    if sync_status.status == "running" and sync_status.task_id and sync_status.task_id != "pending":
        try:
            res = celery_app.AsyncResult(sync_status.task_id)
            if res.ready():
                if res.successful():
                    sync_status.status = "completed"
                    sync_status.details = "Завершено (обновлено вручную)"
                elif res.failed():
                    sync_status.status = "error"
                    sync_status.details = f"Ошибка: {str(res.result)}"
                
                sync_status.updated_at = datetime.now(timezone.utc)
                session.add(sync_status)
                session.commit()
                session.refresh(sync_status)
        except Exception as e:
            logger.error(f"Error checking status for task {sync_status.task_id}: {e}")
    
    return sync_status

@router.delete("/tasks/{task_id}", dependencies=[Depends(require_permission("system_tasks_edit"))])
def delete_task_record(task_id: int, session: Session = Depends(get_session)):
    """Удаление записи о задаче"""
    sync_status = session.get(SyncStatus, task_id)
    if not sync_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    session.delete(sync_status)
    session.commit()
    return {"status": "success"}

@router.get("/files", dependencies=[Depends(require_permission("system_tasks_view"))])
def list_import_files():
    """Список файлов импорта"""
    temp_dir = "temp_imports"
    if not os.path.exists(temp_dir):
        return []
    
    files = []
    for f in os.listdir(temp_dir):
        path = os.path.join(temp_dir, f)
        if os.path.isfile(path):
            files.append({
                "name": f,
                "size": os.path.getsize(path),
                "created_at": datetime.fromtimestamp(os.path.getctime(path)).isoformat()
            })
    return files

@router.delete("/files/{filename}", dependencies=[Depends(require_permission("system_tasks_edit"))])
def delete_import_file(filename: str):
    """Удаление файла импорта"""
    temp_dir = "temp_imports"
    path = os.path.join(temp_dir, filename)
    
    # Безопасность: не даем выйти за пределы папки
    abs_path = os.path.abspath(path)
    abs_temp_dir = os.path.abspath(temp_dir)
    if not abs_path.startswith(abs_temp_dir):
         raise HTTPException(status_code=400, detail="Invalid path")

    if os.path.exists(path):
        os.remove(path)
        return {"status": "success"}
    else:
        raise HTTPException(status_code=404, detail="File not found")

# --- Управление запланированными задачами (APScheduler) ---

@router.get("/scheduled-tasks", response_model=List[ScheduledTask], dependencies=[Depends(require_permission("system_tasks_view"))])
def get_scheduled_tasks(session: Session = Depends(get_session)):
    """Список всех запланированных задач"""
    return session.exec(select(ScheduledTask).order_by(ScheduledTask.id)).all()

@router.post("/scheduled-tasks", response_model=ScheduledTask, dependencies=[Depends(require_permission("system_tasks_edit"))])
def create_scheduled_task(task: ScheduledTask, session: Session = Depends(get_session)):
    """Создание новой запланированной задачи"""
    session.add(task)
    session.commit()
    session.refresh(task)
    
    if task.is_active and task.trigger_type != "dependency":
        add_scheduled_job(task)
        
    return task

@router.put("/scheduled-tasks/{task_id}", response_model=ScheduledTask, dependencies=[Depends(require_permission("system_tasks_edit"))])
def update_scheduled_task(task_id: int, updated_task: dict, session: Session = Depends(get_session)):
    """Обновление запланированной задачи"""
    task = session.get(ScheduledTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Запоминаем старый job_id для удаления если он изменился
    old_job_id = task.job_id
    
    for key, value in updated_task.items():
        if hasattr(task, key):
            setattr(task, key, value)
    
    task.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(task)
    session.commit()
    session.refresh(task)
    
    # Обновляем в планировщике
    if old_job_id:
        try:
            scheduler.remove_job(old_job_id)
        except:
            pass
            
    if task.is_active and task.trigger_type != "dependency":
        add_scheduled_job(task)
        
    return task

@router.post("/scheduled-tasks/{task_id}/toggle", dependencies=[Depends(require_permission("system_tasks_edit"))])
def toggle_scheduled_task(task_id: int, session: Session = Depends(get_session)):
    """Включение/выключение задачи"""
    task = session.get(ScheduledTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.is_active = not task.is_active
    session.add(task)
    session.commit()
    
    if task.is_active:
        if task.trigger_type != "dependency":
            add_scheduled_job(task)
    else:
        if task.job_id:
            try:
                scheduler.remove_job(task.job_id)
            except:
                pass
                
    return {"status": "success", "is_active": task.is_active}

@router.post("/scheduled-tasks/{task_id}/run", dependencies=[Depends(require_permission("system_tasks_edit"))])
def run_scheduled_task_now(task_id: int, session: Session = Depends(get_session)):
    """Мгновенный запуск задачи"""
    task = session.get(ScheduledTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        import importlib
        module_path, func_name = task.task_name.rsplit('.', 1)
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        
        # Запускаем как разовую задачу в APScheduler
        scheduler.add_job(func, args=task.get_args(), kwargs=task.get_kwargs())
        return {"status": "success", "message": f"Задача {task.name} запущена"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/scheduled-tasks/{task_id}", dependencies=[Depends(require_permission("system_tasks_edit"))])
def delete_scheduled_task(task_id: int, session: Session = Depends(get_session)):
    """Удаление запланированной задачи"""
    task = session.get(ScheduledTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.job_id:
        try:
            scheduler.remove_job(task.job_id)
        except:
            pass
            
    session.delete(task)
    session.commit()
    return {"status": "success"}

def _docker_api(method: str, path: str, body=None):
    """Вспомогательный метод для выполнения запросов к Docker API через unix socket"""
    socket_path = "/var/run/docker.sock"
    if not os.path.exists(socket_path):
        return 503, {"error": "Docker socket not available"}

    import http.client
    import socket

    class UnixConn(http.client.HTTPConnection):
        def connect(self):
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.settimeout(20)
            self.sock.connect(socket_path)

    try:
        conn = UnixConn("localhost")
        headers = {"Host": "localhost"}
        payload = json.dumps(body) if body else None
        if payload:
            headers["Content-Type"] = "application/json"
        conn.request(method, path, body=payload, headers=headers)
        res = conn.getresponse()
        raw = res.read().decode("utf-8")
        conn.close()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return res.status, parsed
    except Exception as e:
        logger.error(f"Docker API error: {e}")
        return 500, {"error": str(e)}


@router.get("/server-status", dependencies=[Depends(require_permission("system_server_view"))])
def get_server_status():
    """Возвращает метрики нагрузки сервера: CPU, RAM, Swap, Disk и размер базы данных"""
    try:
        import psutil
    except ImportError:
        raise HTTPException(status_code=500, detail="psutil is not installed")
        
    try:
        # Процессор
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Оперативная память
        mem = psutil.virtual_memory()

        # Файл подкачки (SWAP)
        swap = psutil.swap_memory()
        
        # Диск (корневой каталог)
        disk = psutil.disk_usage('/')

        # Размер БД PostgreSQL
        db_size = "N/A"
        try:
            from app.core.database import engine
            from sqlalchemy import text
            with engine.connect() as conn:
                row = conn.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()));")).fetchone()
                if row:
                    db_size = row[0]
        except Exception as e:
            logger.warning(f"Could not get db_size: {e}")
        
        return {
            "status": "success",
            "cpu": {
                "percent": cpu_percent
            },
            "ram": {
                "total": mem.total,
                "used": mem.used,
                "free": mem.available,
                "percent": mem.percent
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "db_size": db_size
        }
    except Exception as e:
        logger.error(f"Error getting server status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/server-containers", dependencies=[Depends(require_permission("system_server_view"))])
def get_server_containers():
    """Возвращает список запущенных Docker контейнеров с их статусами"""
    status_code, data = _docker_api("GET", "/containers/json?all=1")
    if status_code != 200 or not isinstance(data, list):
        return {"status": "warning", "message": "Docker socket недоступен", "containers": []}

    containers = []
    for item in data:
        name = item.get("Names", [""])[0].lstrip("/") if item.get("Names") else "unknown"
        # Фильтруем служебные контейнеры проекта
        containers.append({
            "id": item.get("Id", "")[:12],
            "name": name,
            "image": item.get("Image", ""),
            "state": item.get("State", ""),
            "status": item.get("Status", ""),
            "created": item.get("Created", 0)
        })
    # Сортируем: сначала running, затем по имени
    containers.sort(key=lambda c: (0 if c["state"] == "running" else 1, c["name"]))
    return {"status": "success", "containers": containers}


@router.post("/server/cleanup-disk", dependencies=[Depends(require_permission("system_server_view"))])
def cleanup_disk(session: Session = Depends(get_session)):
    """Освобождение лишнего места: удаление старых логов в БД (>30 дней), очистка build cache Docker и временных образов"""
    details = []
    try:
        import psutil
        disk_before = psutil.disk_usage('/')
    except Exception:
        disk_before = None

    # 1. Очистка старых логов в БД (> 30 дней)
    try:
        from sqlalchemy import text
        res_logs = session.execute(text("DELETE FROM system_logs WHERE created_at < NOW() - INTERVAL '30 days' AND level IN ('INFO', 'WARNING');"))
        res_vk = session.execute(text("DELETE FROM vk_webhook_logs WHERE created_at < NOW() - INTERVAL '30 days';"))
        session.commit()
        deleted_logs = (res_logs.rowcount or 0) + (res_vk.rowcount or 0)
        details.append(f"Удалено {deleted_logs} устаревших логов из БД")
    except Exception as e:
        logger.error(f"Cleanup DB logs error: {e}")
        details.append(f"Логи БД: {e}")

    # 2. Очистка build cache Docker
    try:
        s, d = _docker_api("POST", "/build/prune?keep-storage=524288000")
        if s == 200 and isinstance(d, dict):
            reclaimed = d.get("SpaceReclaimed", 0)
            details.append(f"Очищен кэш сборки Docker: {round(reclaimed / (1024 * 1024), 1)} МБ")
        else:
            s2, d2 = _docker_api("POST", "/build/prune")
            if s2 == 200 and isinstance(d2, dict):
                reclaimed = d2.get("SpaceReclaimed", 0)
                details.append(f"Очищен кэш сборки Docker: {round(reclaimed / (1024 * 1024), 1)} МБ")
    except Exception as e:
        logger.error(f"Cleanup Docker build error: {e}")

    # 3. Очистка dangling образов
    try:
        s_img, d_img = _docker_api("POST", "/images/prune?filters=%7B%22dangling%22%3A%5B%22true%22%5D%7D")
        if s_img == 200 and isinstance(d_img, dict):
            reclaimed_img = d_img.get("SpaceReclaimed", 0)
            if reclaimed_img > 0:
                details.append(f"Удалены временные образы Docker: {round(reclaimed_img / (1024 * 1024), 1)} МБ")
    except Exception as e:
        logger.error(f"Cleanup Docker images error: {e}")

    try:
        disk_after = psutil.disk_usage('/')
        freed_mb = round((disk_after.free - disk_before.free) / (1024 * 1024), 1) if disk_before else 0
    except Exception:
        freed_mb = 0

    return {
        "status": "success",
        "freed_mb": freed_mb,
        "details": details,
        "disk": {
            "total": disk_after.total if disk_after else 0,
            "free": disk_after.free if disk_after else 0,
            "percent": disk_after.percent if disk_after else 0
        }
    }


@router.post("/server/vacuum-db", dependencies=[Depends(require_permission("system_server_view"))])
def vacuum_database():
    """Глубокая оптимизация базы данных: сжатие раздутых таблиц и дефрагментация индексов (VACUUM FULL, REINDEX)"""
    from app.core.database import engine
    from sqlalchemy import text
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("VACUUM FULL multichat_messages;"))
            conn.execute(text("VACUUM FULL system_logs;"))
            conn.execute(text("REINDEX TABLE multichat_messages;"))
            row = conn.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()));")).fetchone()
            new_size = row[0] if row else "N/A"

        return {
            "status": "success",
            "message": f"Сжатие и оптимизация базы данных успешно выполнены. Текущий размер БД: {new_size}",
            "db_size": new_size
        }
    except Exception as e:
        logger.error(f"Error during VACUUM: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сжатия БД: {str(e)}")


@router.post("/server/restart-services", dependencies=[Depends(require_permission("system_server_view"))])
def restart_app_services():
    """Перезапуск служб приложения (worker, bot) для освобождения памяти и сброса зависших задач"""
    results = {}
    for container in ["foodtech-worker", "foodtech-bot"]:
        status, res = _docker_api("POST", f"/containers/{container}/restart?t=5")
        results[container] = "Успешно перезапущен" if status == 204 else f"Код: {status}"
    
    return {
        "status": "success",
        "message": "Фоновые службы приложения успешно перезапущены",
        "details": results
    }


@router.post("/server/restart-web", dependencies=[Depends(require_permission("system_server_view"))])
def restart_web_services():
    """Перезапуск веб-серверов (nginx, admin, frontend)"""
    results = {}
    for container in ["foodtech-nginx", "foodtech-admin", "foodtech-frontend"]:
        status, res = _docker_api("POST", f"/containers/{container}/restart?t=5")
        results[container] = "Успешно перезапущен" if status == 204 else f"Код: {status}"

    return {
        "status": "success",
        "message": "Веб-серверы успешно перезапущены",
        "details": results
    }


@router.post("/server/reboot", dependencies=[Depends(require_permission("system_server_view"))])
def reboot_server():
    """Инициирует безопасную перезагрузку операционной системы VPS сервера"""
    trigger_paths = ["/host_foodzuka/trigger_reboot", "/root/foodzuka/trigger_reboot"]
    triggered = False
    for p in trigger_paths:
        dir_name = os.path.dirname(p)
        if os.path.exists(dir_name):
            try:
                with open(p, "w") as f:
                    f.write(f"reboot requested at {datetime.now().isoformat()}")
                triggered = True
                break
            except Exception as e:
                logger.error(f"Failed to write reboot trigger to {p}: {e}")

    if not triggered:
        raise HTTPException(status_code=500, detail="Триггер перезагрузки хоста недоступен из контейнера")

    return {
        "status": "success",
        "message": "Команда перезагрузки принята операционной системой. Сервер перезагружается (доступ восстановится через 1-2 минуты)."
    }

