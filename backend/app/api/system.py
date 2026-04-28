"""
API эндпоинты для управления системными процессами и файлами
"""
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
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

@router.get("/tasks", response_model=List[SyncStatus])
async def get_tasks(session: Session = Depends(get_session)):
    """Список всех фоновых задач"""
    return session.exec(select(SyncStatus).order_by(SyncStatus.updated_at.desc())).all()

@router.post("/tasks/stop-all")
async def stop_all_tasks(session: Session = Depends(get_session)):
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

@router.post("/tasks/cleanup")
async def cleanup_tasks(session: Session = Depends(get_session)):
    """Очистить завершенные и ошибочные задачи"""
    to_delete = session.exec(
        select(SyncStatus).where(SyncStatus.status.in_(["completed", "error", "cancelled"]))
    ).all()
    count = len(to_delete)
    for task in to_delete:
        session.delete(task)
    session.commit()
    return {"status": "success", "deleted_count": count}

@router.post("/tasks/run")
async def run_task(task_type: str, params: dict = {}, session: Session = Depends(get_session)):
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


@router.post("/tasks/{task_id}/pause")
async def toggle_task_pause(task_id: int, session: Session = Depends(get_session)):
    """Переключение паузы задачи"""
    sync_status = session.get(SyncStatus, task_id)
    if not sync_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    sync_status.is_paused = not sync_status.is_paused
    session.add(sync_status)
    session.commit()
    session.refresh(sync_status)
    return sync_status

@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: int, session: Session = Depends(get_session)):
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

@router.post("/tasks/{task_id}/refresh")
async def refresh_task_status(task_id: int, session: Session = Depends(get_session)):
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

@router.delete("/tasks/{task_id}")
async def delete_task_record(task_id: int, session: Session = Depends(get_session)):
    """Удаление записи о задаче"""
    sync_status = session.get(SyncStatus, task_id)
    if not sync_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    session.delete(sync_status)
    session.commit()
    return {"status": "success"}

@router.get("/files")
async def list_import_files():
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

@router.delete("/files/{filename}")
async def delete_import_file(filename: str):
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

@router.get("/scheduled-tasks", response_model=List[ScheduledTask])
async def get_scheduled_tasks(session: Session = Depends(get_session)):
    """Список всех запланированных задач"""
    return session.exec(select(ScheduledTask).order_by(ScheduledTask.id)).all()

@router.post("/scheduled-tasks", response_model=ScheduledTask)
async def create_scheduled_task(task: ScheduledTask, session: Session = Depends(get_session)):
    """Создание новой запланированной задачи"""
    session.add(task)
    session.commit()
    session.refresh(task)
    
    if task.is_active and task.trigger_type != "dependency":
        add_scheduled_job(task)
        
    return task

@router.put("/scheduled-tasks/{task_id}", response_model=ScheduledTask)
async def update_scheduled_task(task_id: int, updated_task: dict, session: Session = Depends(get_session)):
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

@router.post("/scheduled-tasks/{task_id}/toggle")
async def toggle_scheduled_task(task_id: int, session: Session = Depends(get_session)):
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

@router.post("/scheduled-tasks/{task_id}/run")
async def run_scheduled_task_now(task_id: int, session: Session = Depends(get_session)):
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

@router.delete("/scheduled-tasks/{task_id}")
async def delete_scheduled_task(task_id: int, session: Session = Depends(get_session)):
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
