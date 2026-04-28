import logging
import traceback
import asyncio
from typing import Any, Optional
from datetime import datetime, timezone
from fastapi import Request
from sqlmodel import Session
from app.core.database import SessionLocal
from app.models.system_log import SystemLog
from app.models.audit_log import AuditLog
from app.core.config import settings
logger = logging.getLogger(__name__)

class DatabaseLogHandler(logging.Handler):
    """Обработчик логов для записи в БД"""
    def emit(self, record):
        try:
            # Предотвращаем рекурсию: если ошибка возникла при записи в БД или от SQLAlchemy, не пишем в БД
            if (record.name.startswith("sqlalchemy") or 
                record.name.startswith("app.core.logging_utils") or 
                record.name.startswith("uvicorn.access")):
                return

            # Логируем в БД только WARNING и выше (чтобы не забивать базу INFO логами)
            if record.levelno < logging.WARNING:
                return

            stack_trace = None
            if record.exc_info:
                stack_trace = "".join(traceback.format_exception(*record.exc_info))
            elif record.levelname in ["ERROR", "CRITICAL"]:
                # Если это ошибка, но exc_info нет, попробуем взять текущий стек
                stack_trace = traceback.format_exc()
                if stack_trace == "NoneType: None\n":
                    stack_trace = None

            log_entry = {
                "level": record.levelname,
                "module": record.name,
                "message": record.getMessage(),
                "stack_trace": stack_trace
            }
            
            # Запись в БД
            self._write_to_db(log_entry)
        except Exception as e:
            # Если запись в БД упала, пишем в консоль
            print(f"CRITICAL: Error writing log to DB: {e}")

    def _write_to_db(self, log_entry: dict):
        try:
            with SessionLocal() as session:
                log = SystemLog(**log_entry)
                session.add(log)
                session.commit()
        except Exception:
            # Игнорируем ошибки записи логов в БД, чтобы не создавать бесконечный цикл
            pass

def log_audit(
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    changes: Optional[dict] = None,
    user_id: Optional[int] = None,
    message: Optional[str] = None
):
    """Функция для ручного создания записи аудита"""
    try:
        with SessionLocal() as session:
            audit = AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                changes=changes or {},
                user_id=user_id,
                message=message
            )
            session.add(audit)
            session.commit()
    except Exception as e:
        logger.error(f"Audit logging failed: {e}")

async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений для записи 500 ошибок в БД"""
    error_msg = str(exc)
    stack_trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    
    # Записываем в БД
    try:
        with SessionLocal() as session:
            log = SystemLog(
                level="CRITICAL",
                module="GlobalExceptionHandler",
                message=f"Unhandled exception: {error_msg}",
                stack_trace=stack_trace
            )
            session.add(log)
            session.commit()
    except Exception as e:
        print(f"Failed to log unhandled exception: {e}")
    
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "message": error_msg if settings.DEBUG else "Произошла внутренняя ошибка сервера"
        }
    )
