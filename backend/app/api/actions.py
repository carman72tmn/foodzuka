"""
API эндпоинты для управления Акциями (Маркетинговыми кампаниями)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.action import Action
from app.schemas import ActionCreate, ActionUpdate, ActionResponse

router = APIRouter(prefix="/actions", tags=["Actions"])

@router.get("/", response_model=List[ActionResponse])
def get_actions(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    session: Session = Depends(get_session)
):
    """Список маркетинговых акций"""
    query = select(Action).order_by(Action.priority.desc(), Action.created_at.desc()).offset(skip).limit(limit)
    
    if is_active is not None:
        query = query.where(Action.is_active == is_active)
        
    actions = session.exec(query).all()
    return actions

@router.get("/{action_id}", response_model=ActionResponse)
def get_action(action_id: int, session: Session = Depends(get_session)):
    """Детали акции"""
    action = session.get(Action, action_id)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")
    return action

@router.post("/", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
def create_action(
    action_data: ActionCreate,
    session: Session = Depends(get_session)
):
    """Создать новую маркетинговую акцию"""
    action = Action(**action_data.model_dump())
    session.add(action)
    session.commit()
    session.refresh(action)
    return action

@router.patch("/{action_id}", response_model=ActionResponse)
def update_action(
    action_id: int,
    action_data: ActionUpdate,
    session: Session = Depends(get_session)
):
    """Обновление акции"""
    action = session.get(Action, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    update_data = action_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(action, key, value)

    session.add(action)
    session.commit()
    session.refresh(action)
    return action

@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_action(action_id: int, session: Session = Depends(get_session)):
    """Удаление акции"""
    action = session.get(Action, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    session.delete(action)
    session.commit()
