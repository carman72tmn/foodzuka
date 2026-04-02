"""
API эндпоинты для управления Филиалами и Зонами доставки
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.company import Company, Branch, DeliveryZone
from app.models.iiko_settings import IikoSettings
from app.services.iiko_service import iiko_service
from app.schemas import (
    BranchCreate, BranchUpdate, BranchResponse,
    DeliveryZoneCreate, DeliveryZoneUpdate, DeliveryZoneResponse
)

router = APIRouter(prefix="/branches", tags=["Branches"])

# ============= Синхронизация =============

@router.post("/sync", response_model=dict)
async def sync_iiko_branches(session: Session = Depends(get_session)):
    """Синхронизация организаций и филиалов из iiko"""
    try:
        # Получаем настройки iiko из БД
        settings_db = session.exec(select(IikoSettings)).first()
        api_login = settings_db.api_login if settings_db else None
        organization_id = settings_db.organization_id if settings_db else None

        # 1. Получаем организации (Company)
        organizations = await iiko_service.get_organizations(api_login=api_login)
        
        # Если список пуст, но есть organization_id в настройках - попробуем получить инфо об одной
        if not organizations and organization_id:
            try:
                org_info = await iiko_service.get_organization_info(
                    api_login=api_login, 
                    organization_id=organization_id
                )
                if org_info:
                    organizations = [org_info]
            except Exception as e:
                # Не критично, попробуем продолжить
                pass

        synced_companies = 0
        synced_branches = 0
        
        for org in organizations:
            org_id = org.get("id")
            org_name = org.get("name")
            
            if not org_id or not org_name:
                continue
                
            # Ищем компанию по iiko_organization_id
            company = session.exec(select(Company).where(Company.iiko_organization_id == org_id)).first()
            if not company:
                # Попробуем по имени
                company = session.exec(select(Company).where(Company.name == org_name)).first()
                if company:
                    company.iiko_organization_id = org_id
                else:
                    company = Company(name=org_name, iiko_organization_id=org_id)
                    session.add(company)
            else:
                company.name = org_name
            
            session.commit()
            session.refresh(company)
            synced_companies += 1

        # 2. Получаем терминальные группы (Branch)
        terminal_groups = await iiko_service.get_terminal_groups(
            api_login=api_login, 
            organization_id=organization_id
        )
        
        for tg in terminal_groups:
            tg_id = tg.get("id")
            tg_name = tg.get("name")
            tg_org_id = tg.get("organizationId")
            
            if not tg_id or not tg_org_id or not tg_name:
                continue
                
            # Ищем к какой компании относится филиал
            company = session.exec(select(Company).where(Company.iiko_organization_id == tg_org_id)).first()
            if not company:
                continue
                
            # Ищем филиал по iiko_terminal_id
            branch = session.exec(select(Branch).where(Branch.iiko_terminal_id == tg_id)).first()
            if not branch:
                # Пробуем по имени для текущей компании
                branch = session.exec(select(Branch).where(Branch.name == tg_name, Branch.company_id == company.id)).first()
                if branch:
                    branch.iiko_terminal_id = tg_id
                else:
                    # Создаем новый филиал, берем address из поля, либо используем название как запасной вариант
                    address = tg.get("address") or tg_name
                    branch = Branch(
                        name=tg_name, 
                        address=address,
                        company_id=company.id,
                        iiko_terminal_id=tg_id
                    )
                    session.add(branch)
            else:
                branch.name = tg_name
                
            session.commit()
            session.refresh(branch)
            synced_branches += 1
            
        return {
            "success": True, 
            "message": f"Синхронизировано компаний: {synced_companies}, филиалов: {synced_branches}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка синхронизации с iiko: {str(e)}")

# ============= Филиалы =============

@router.get("/", response_model=List[BranchResponse])
async def get_branches(
    company_id: int = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Список всех филиалов (с возможностью фильтрации по компании)"""
    query = select(Branch).offset(skip).limit(limit)
    if company_id:
        query = query.where(Branch.company_id == company_id)
        
    branches = session.exec(query).all()
    return branches


@router.get("/{branch_id}", response_model=BranchResponse)
async def get_branch(branch_id: int, session: Session = Depends(get_session)):
    """Детали одного филиала"""
    branch = session.get(Branch, branch_id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Branch with id {branch_id} not found"
        )
    return branch


@router.post("/", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    branch_data: BranchCreate,
    session: Session = Depends(get_session)
):
    """Создание нового филиала"""
    branch = Branch(**branch_data.model_dump())
    session.add(branch)
    session.commit()
    session.refresh(branch)
    return branch


@router.patch("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: int,
    branch_data: BranchUpdate,
    session: Session = Depends(get_session)
):
    """Обновление данных филиала"""
    branch = session.get(Branch, branch_id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Branch with id {branch_id} not found"
        )

    update_data = branch_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(branch, key, value)

    session.add(branch)
    session.commit()
    session.refresh(branch)
    return branch


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(branch_id: int, session: Session = Depends(get_session)):
    """Удаление филиала"""
    branch = session.get(Branch, branch_id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Branch with id {branch_id} not found"
        )

    session.delete(branch)
    session.commit()


# ============= Зоны доставки =============

@router.get("/{branch_id}/zones", response_model=List[DeliveryZoneResponse])
async def get_delivery_zones(
    branch_id: int,
    session: Session = Depends(get_session)
):
    """Списки зон доставки для конкретного филиала"""
    query = select(DeliveryZone).where(DeliveryZone.branch_id == branch_id)
    zones = session.exec(query).all()
    return zones


@router.post("/{branch_id}/zones", response_model=DeliveryZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_zone(
    branch_id: int,
    zone_data: DeliveryZoneCreate,
    session: Session = Depends(get_session)
):
    """Создание новой зоны доставки"""
    if zone_data.branch_id != branch_id:
        raise HTTPException(status_code=400, detail="Branch ID mismatch")
        
    zone = DeliveryZone(**zone_data.model_dump())
    session.add(zone)
    session.commit()
    session.refresh(zone)
    return zone

@router.patch("/zones/{zone_id}", response_model=DeliveryZoneResponse)
async def update_delivery_zone(
    zone_id: int,
    zone_data: DeliveryZoneUpdate,
    session: Session = Depends(get_session)
):
    """Обновление зоны доставки"""
    zone = session.get(DeliveryZone, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    update_data = zone_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(zone, key, value)

    session.add(zone)
    session.commit()
    session.refresh(zone)
    return zone

@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_delivery_zone(zone_id: int, session: Session = Depends(get_session)):
    """Удаление зоны доставки"""
    zone = session.get(DeliveryZone, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    session.delete(zone)
    session.commit()
