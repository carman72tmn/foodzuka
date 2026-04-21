import subprocess
import os
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select, desc
from app.core.database import get_session
from app.models.system_log import SystemLog
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/logs", tags=["Logs & History"])

@router.get("/system/")
async def get_system_logs(
    limit: int = Query(50, le=500),
    level: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Получить системные логи ошибок"""
    query = select(SystemLog).order_by(desc(SystemLog.created_at))
    if level:
        query = query.where(SystemLog.level == level)
    
    return session.exec(query.limit(limit)).all()

@router.get("/audit/")
async def get_audit_logs(
    limit: int = Query(50, le=500),
    resource_type: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Получить логи аудита изменений"""
    query = select(AuditLog).order_by(desc(AuditLog.created_at))
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    
    return session.exec(query.limit(limit)).all()

@router.get("/code-history/")
async def get_code_history(limit: int = Query(20, le=100)):
    """Получить историю коммитов из Git"""
    try:
        # Пытаемся получить git log
        result = subprocess.run(
            ["git", "log", f"-n {limit}", "--pretty=format:%h|%an|%at|%s"],
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                h, an, at, s = line.split("|", 3)
                commits.append({
                    "hash": h,
                    "author": an,
                    "date": int(at),
                    "message": s
                })
        return commits
    except Exception:
        # Fallback: попытаться прочитать из файла git_history.json
        try:
            history_file = os.path.join(os.getcwd(), "git_history.json")
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as file_err:
            return {"error": f"Failed to fetch git history: {str(file_err)}"}
        
        return {"error": "Git not available and no history file found"}
