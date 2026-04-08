from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime
from sqlmodel import Session, select
from typing import List, Optional

from app.core.database import get_session, engine
from app.models.employee import Employee, Shift, Schedule
from app.services.iiko_sync_service import iiko_sync_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
@router.get("")
def get_employees(
    status: Optional[str] = None,
    role: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Получение списка сотрудников
    """
    query = select(Employee)
    if status is not None:
        query = query.where(Employee.status == status)
    if role is not None:
        query = query.where(Employee.role == role)
        
    employees = session.exec(query).all()
    return {"status": "success", "data": employees}

@router.get("/{employee_id}/shifts")
def get_employee_shifts(
    employee_id: int,
    session: Session = Depends(get_session)
):
    """
    Получение смен сотрудника
    """
    employee = session.exec(select(Employee).where(Employee.id == employee_id)).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
        
    shifts = session.exec(select(Shift).where(Shift.employee_id == employee_id).order_by(Shift.date_open.desc())).all()
    return {"status": "success", "data": shifts}

@router.get("/{employee_id}/stats")
async def get_employee_stats(
    employee_id: int,
    mode: str = "calendar", # calendar or sliding
    session: Session = Depends(get_session)
):
    """
    Получение статистики сотрудника (режимы: календарная неделя или последние 7 дней)
    """
    stats = await iiko_sync_service.get_employee_stats(session, employee_id, mode)
    return {"status": "success", "data": stats}

@router.get("/shifts/open")
def get_open_shifts(
    session: Session = Depends(get_session)
):
    """
    Получение всех текущих открытых смен
    """
    shifts = session.exec(select(Shift).where(Shift.status == "OPEN").order_by(Shift.date_open.desc())).all()
    # Подгружаем данные сотрудников для удобства
    result = []
    for s in shifts:
        shift_dict = s.model_dump()
        shift_dict["employee_name"] = s.employee.name if s.employee else "Unknown"
        result.append(shift_dict)
        
    return {"status": "success", "data": result}

@router.get("/schedules")
def get_schedules(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Получение графика смен за период
    """
    query = select(Schedule)
    
    if date_from:
        df = datetime.fromisoformat(date_from)
        query = query.where(Schedule.date_from >= df)
    if date_to:
        dt = datetime.fromisoformat(date_to)
        query = query.where(Schedule.date_to <= dt)
        
    schedules = session.exec(query.order_by(Schedule.date_from.asc())).all()
    
    result = []
    for sc in schedules:
        sc_dict = sc.model_dump()
        sc_dict["employee_name"] = sc.employee.name if sc.employee else "Unknown"
        result.append(sc_dict)
        
    return {"status": "success", "data": result}

@router.post("/sync/")
@router.post("/sync")
def sync_employees(background_tasks: BackgroundTasks):
    """
    Запуск фоновой синхронизации списка сотрудников и смен (по умолчанию за последние 7 дней)
    """
    async def run_sync():
        try:
            with Session(engine) as sync_session:
                await iiko_sync_service.sync_employees_full(sync_session, days=7)
                logger.info("Background employee full sync completed successfully")
        except Exception as e:
            logger.error(f"Fatal error in background employee sync: {e}")
            
    background_tasks.add_task(run_sync)
    return {"status": "success", "message": "Синхронизация сотрудников запущена"}

@router.get("/reports/couriers")
async def get_courier_report(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Отчет по курьерам (количество доставок) за период
    """
    # Если даты не указаны, берем сегодня
    df = datetime.fromisoformat(date_from) if date_from else datetime.utcnow().replace(hour=0, minute=0, second=0)
    dt = datetime.fromisoformat(date_to) if date_to else datetime.utcnow()
    
    # Получаем всех курьеров (фильтруем по ролям, содержащим "курьер 2000")
    # Это универсальный фильтр по просьбе пользователя
    employees = session.exec(select(Employee)).all()
    couriers = [e for e in employees if e.role and "курьер 2000" in e.role.lower()]
    
    report = []
    for courier in couriers:
        # Считаем доставки из смен за период
        shifts = session.exec(
            select(Shift).where(
                Shift.employee_id == courier.id,
                Shift.date_open >= df,
                Shift.date_open <= dt
            )
        ).all()
        
        total_deliveries = sum(s.deliveries_count or 0 for s in shifts)
        total_hours = sum(s.work_hours or 0.0 for s in shifts)
        total_revenue = sum(getattr(s, "deliveries_revenue", 0.0) or 0.0 for s in shifts)
        
        report.append({
            "id": courier.id,
            "name": courier.name,
            "deliveries": total_deliveries,
            "revenue": round(total_revenue, 2),
            "hours": round(total_hours, 2),
            "shifts_count": len(shifts)
        })
        
    return {"status": "success", "data": report}
