from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Optional

from app.core.database import get_session
from app.models.employee import Employee, Shift
from app.services.iiko_sync_service import iiko_sync_service

router = APIRouter()

@router.get("/")
def get_employees(
    status: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Получение списка сотрудников
    """
    query = select(Employee)
    if status is not None:
        query = query.where(Employee.status == status)
        
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
        raise HTTPException(status_code=404, detail="Employee not found")
        
    shifts = session.exec(select(Shift).where(Shift.employee_id == employee_id).order_by(Shift.date_open.desc())).all()
    return {"status": "success", "data": shifts}

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

@router.post("/sync")
def sync_employees(background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    Запуск фоновой синхронизации списка сотрудников и смен (по умолчанию за последние 7 дней)
    """
    async def run_sync():
        with Session(session.bind) as sync_session:
            await iiko_sync_service.sync_employees_and_shifts(sync_session, days=7)
            
    background_tasks.add_task(run_sync)
    return {"status": "accepted", "message": "Employees synchronization started"}
