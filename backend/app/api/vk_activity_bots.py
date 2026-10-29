from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc, func, text
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_session
from app.api.deps import require_permission
from app.models.user import User
from app.models.vk_activity_settings import VkActivitySettings
from app.models.vk_activity import VkActivity
from app.models.vk_user import VkUser
from app.models.customer import Customer
from app.services.vk_activity_service import vk_activity_service
from app.core.datetime_utils import utc_now

router = APIRouter()

class VkActivitySettingsSchema(BaseModel):
    id: Optional[int] = None
    vk_bot_connection_id: int
    is_active: bool = True
    
    points_like: int = 5
    points_like_first_n: int = 10
    like_first_n_count: int = 5
    points_like_fast: int = 8
    like_fast_seconds: int = 900
    
    points_comment: int = 10
    points_comment_first_n: int = 15
    comment_first_n_count: int = 5
    points_comment_fast: int = 12
    comment_fast_seconds: int = 900
    min_comment_length: int = 5
    max_comments_per_post: int = 3
    ignore_consecutive_comments: bool = True
    ignore_stickers: bool = True
    
    points_repost: int = 20
    points_poll: int = 5
    points_join: int = 50
    
    penalty_duration_seconds: int = 3600
    penalty_points: int = 0
    msg_penalty: Optional[str] = None
    
    period_start_date: Optional[datetime] = None
    period_duration_days: int = 7
    ignored_post_ids: Optional[str] = None
    post_max_age_days: int = 7
    override_keywords: Optional[str] = ""

    msg_points_like: Optional[str] = None
    msg_points_comment: Optional[str] = None
    msg_points_repost: Optional[str] = None
    msg_points_poll: Optional[str] = None
    msg_points_join: Optional[str] = None
    msg_balance_info: Optional[str] = None
    msg_unlinked_notice: Optional[str] = None
    
    sync_with_iiko: bool = False
    iiko_conversion_rate: float = 1.0
    iiko_sync_mode: str = "realtime"
    iiko_summing_logic: str = "both"
    sync_on_verification: bool = True
    sync_on_balance_request: bool = True
    last_sync_at: Optional[datetime] = None
    vk_bot_token: Optional[str] = None

class UserPointsUpdateSchema(BaseModel):
    vk_id: int
    points_delta: int

@router.get("/connection/{connection_id}", response_model=Optional[VkActivitySettingsSchema], dependencies=[Depends(require_permission("marketing_vk_bots_view"))])
def get_activity_settings(connection_id: int, db: Session = Depends(get_session)):
    """Получить настройки активности для конкретной группы"""
    settings = db.exec(select(VkActivitySettings).where(VkActivitySettings.vk_bot_connection_id == connection_id)).first()
    if not settings:
        # Возвращаем дефолтные настройки, чтобы фронтенд мог их инициализировать
        return VkActivitySettingsSchema(vk_bot_connection_id=connection_id)
    return settings

@router.post("/", response_model=VkActivitySettingsSchema, dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def save_activity_settings(data: VkActivitySettingsSchema, db: Session = Depends(get_session)):
    """Сохранить или обновить настройки активности"""
    settings = db.exec(select(VkActivitySettings).where(VkActivitySettings.vk_bot_connection_id == data.vk_bot_connection_id)).first()
    
    if settings:
        # Обновляем существующие настройки
        for key, val in data.model_dump(exclude_unset=True).items():
            if hasattr(settings, key):
                setattr(settings, key, val)
        settings.updated_at = utc_now()
        db.add(settings)
    else:
        # Создаем новые
        settings = VkActivitySettings(**data.model_dump())
        db.add(settings)
        
    db.commit()
    db.refresh(settings)
    return settings

@router.get("/connection/{connection_id}/ranking", dependencies=[Depends(require_permission("marketing_vk_bots_view"))])
def get_activity_ranking(connection_id: int, db: Session = Depends(get_session)):
    """Получить рейтинг топ активных участников для группы"""
    # Выбираем всех пользователей VK, у которых баланс > 0, упорядочиваем по убыванию баллов
    # Поскольку у нас мультиботность, мы привязываем пользователей к группе
    from app.models.vk_bot_connection import VkBotConnection
    
    conn = db.get(VkBotConnection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение бота не найдено")
        
    # Запрашиваем пользователей этой группы
    users = db.exec(
        select(VkUser, Customer)
        .join(Customer, VkUser.phone == Customer.phone, isouter=True)
        .where(VkUser.vk_group_id == conn.vk_group_id)
        .order_by(desc(VkUser.vk_bonus_balance), desc(VkUser.is_linked))
    ).all()
    
    ranking = []
    for vk_user, customer in users:
        # Посчитаем детальную статистику по типам активностей в БД для пользователя
        # (лайки, комментарии, репосты)
        likes_count = db.exec(
            select(func.count(VkActivity.id))
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "like_add")
        ).one() or 0
        
        comments_count = db.exec(
            select(func.count(VkActivity.id))
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "wall_reply_new")
        ).one() or 0

        reposts_count = db.exec(
            select(func.count(VkActivity.id))
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "wall_repost")
        ).one() or 0

        iiko_balance = customer.bonus_points if (customer and customer.bonus_points is not None) else 0.0
        vk_points = vk_user.vk_bonus_balance if vk_user.vk_bonus_balance is not None else 0
        synced_points = vk_user.vk_bonus_balance_synced if vk_user.vk_bonus_balance_synced is not None else 0
        rate = 1.0
        act_settings = db.exec(select(VkActivitySettings).where(VkActivitySettings.vk_bot_connection_id == conn.id)).first()
        if act_settings and act_settings.iiko_conversion_rate is not None:
            rate = act_settings.iiko_conversion_rate
            
        total_balance = float(iiko_balance) + (vk_points - synced_points) * rate
        is_synced = vk_user.is_linked and (vk_points == synced_points)

        ranking.append({
            "vk_id": vk_user.vk_id,
            "first_name": vk_user.first_name,
            "last_name": vk_user.last_name,
            "photo_50": vk_user.photo_50,
            "screen_name": vk_user.screen_name,
            "points": vk_points,
            "likes": likes_count,
            "comments": comments_count,
            "reposts": reposts_count,
            "is_linked": vk_user.is_linked,
            "phone": vk_user.phone,
            "customer_name": f"{customer.name} {customer.surname or ''}".strip() if customer else None,
            "iiko_balance": iiko_balance,
            "synced_points": synced_points,
            "total_balance": total_balance,
            "is_synced_to_iiko": is_synced,
            "iiko_conversion_rate": rate
        })
        
    return ranking

@router.post("/connection/{connection_id}/reset", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def reset_activity_ranking(connection_id: int, db: Session = Depends(get_session)):
    """Сбросить рейтинг активности (обнулить баланс баллов активности участников)"""
    from app.models.vk_bot_connection import VkBotConnection
    
    conn = db.get(VkBotConnection, connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение бота не найдено")

    # Обнуляем баланс баллов активности у пользователей группы (включая синхронизированный баланс)
    db.execute(
        text("UPDATE vk_users SET vk_bonus_balance = 0, vk_bonus_balance_synced = 0 WHERE vk_group_id = :group_id"),
        {"group_id": conn.vk_group_id}
    )
    # Очищаем историю активностей для этой группы
    # Так как в vk_activities нет прямой связи с группой, мы можем удалить по vk_id пользователей этой группы
    db.execute(
        text("DELETE FROM vk_activities WHERE vk_id IN (SELECT vk_id FROM vk_users WHERE vk_group_id = :group_id)"),
        {"group_id": conn.vk_group_id}
    )
    db.commit()
    
    return {"status": "success", "message": "Рейтинг активности успешно сброшен"}

@router.post("/connection/{connection_id}/sync-iiko", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
async def sync_activity_to_iiko(connection_id: int, db: Session = Depends(get_session)):
    """Запустить ручную синхронизацию баллов с iikoCard"""
    res = await vk_activity_service.run_manual_iiko_sync(db, connection_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/users/{vk_id}/sync-iiko", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
async def sync_single_user_iiko(vk_id: int, db: Session = Depends(get_session)):
    """Вручную синхронизировать дельту баллов конкретного пользователя с iikoCard"""
    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
    if not vk_user:
        raise HTTPException(status_code=404, detail="Пользователь VK не найден")
        
    from app.models.vk_bot_connection import VkBotConnection
    conn = db.exec(select(VkBotConnection).where(VkBotConnection.vk_group_id == vk_user.vk_group_id)).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение бота для группы не найдено")
        
    settings = db.exec(select(VkActivitySettings).where(VkActivitySettings.vk_bot_connection_id == conn.id)).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Настройки активности не найдены")
        
    # Синхронизируем баллы
    success = await vk_activity_service.sync_vk_user_points_to_iiko(db, vk_user, settings)
    if not success:
        raise HTTPException(status_code=400, detail="Ошибка при синхронизации с iikoCard (возможно, недостаточно средств для списания)")
        
    # Получаем актуальный баланс iiko
    from app.services.iiko_service import iiko_service
    from app.models.customer import Customer
    try:
        if vk_user.phone:
            balance_info = await iiko_service.get_customer_balance(vk_user.phone)
            iiko_balance = balance_info.get("balance", 0)
            customer = db.exec(select(Customer).where(Customer.phone == vk_user.phone)).first()
            if customer:
                customer.bonus_points = iiko_balance
                db.add(customer)
                db.commit()
    except Exception as ex:
        pass
        
    return {"status": "success", "message": "Синхронизация с iikoCard успешно выполнена"}

@router.post("/update-points", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
async def update_user_points(data: UserPointsUpdateSchema, db: Session = Depends(get_session)):
    """Ручная корректировка баллов пользователя администратором"""
    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == data.vk_id)).first()
    if not vk_user:
        raise HTTPException(status_code=404, detail="Пользователь VK не найден")
        
    old_balance = vk_user.vk_bonus_balance
    vk_user.vk_bonus_balance = max(0, vk_user.vk_bonus_balance + data.points_delta)
    
    # Записываем корректировку в историю активностей
    activity = VkActivity(
        vk_id=vk_user.vk_id,
        action_type="manual_adjustment",
        item_id=f"manual_{int(utc_now().timestamp())}",
        points=data.points_delta,
        is_synced=False
    )
    db.add(activity)
    db.add(vk_user)
    db.commit()
    
    return {
        "status": "success", 
        "message": f"Баланс изменен на {data.points_delta} баллов", 
        "new_balance": vk_user.vk_bonus_balance
    }

@router.get("/users/{vk_id}/history", dependencies=[Depends(require_permission("marketing_vk_bots_view"))])
def get_user_activity_history(vk_id: int, db: Session = Depends(get_session)):
    """Получить детализированную историю начислений и активностей участника"""
    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
    if not vk_user:
        raise HTTPException(status_code=404, detail="Пользователь VK не найден")
        
    activities = db.exec(
        select(VkActivity)
        .where(VkActivity.vk_id == vk_id)
        .order_by(desc(VkActivity.created_at))
    ).all()
    
    ACTION_NAMES = {
        "like_add": "Лайк на публикацию",
        "like_remove": "Снятие лайка",
        "wall_reply_new": "Комментарий к посту",
        "wall_reply_delete": "Удаление комментария",
        "wall_repost": "Репост записи",
        "poll_vote": "Участие в опросе",
        "group_join": "Вступление в группу",
        "manual_adjustment": "Ручная корректировка администратора",
        "manual_adjust": "Ручная корректировка администратора",
        "points_transfer": "Перевод баллов в бонусы iikoCard",
    }
    
    history_list = []
    for act in activities:
        title = ACTION_NAMES.get(act.action_type, act.action_type)
        history_list.append({
            "id": act.id,
            "action_type": act.action_type,
            "title": title,
            "item_id": act.item_id,
            "points": act.points,
            "is_synced": act.is_synced,
            "created_at": act.created_at.isoformat()
        })
        
    customer = db.exec(select(Customer).where(Customer.phone == vk_user.phone)).first() if vk_user.phone else None
    
    return {
        "vk_id": vk_user.vk_id,
        "first_name": vk_user.first_name,
        "last_name": vk_user.last_name,
        "phone": vk_user.phone,
        "photo_50": vk_user.photo_50,
        "vk_bonus_balance": vk_user.vk_bonus_balance,
        "vk_bonus_balance_synced": vk_user.vk_bonus_balance_synced,
        "is_linked": vk_user.is_linked,
        "customer_name": f"{customer.name} {customer.surname or ''}".strip() if customer else None,
        "iiko_balance": customer.bonus_points if customer else 0,
        "history": history_list
    }

@router.post("/users/{vk_id}/transfer-to-iiko", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
async def force_transfer_single_user_points(vk_id: int, db: Session = Depends(get_session)):
    """Принудительно перевести все накопленные баллы активности ВК в бонусы iikoCard (с обнулением локального баланса ВК)"""
    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
    if not vk_user:
        raise HTTPException(status_code=404, detail="Пользователь VK не найден")
        
    if not vk_user.is_linked or not vk_user.phone:
        raise HTTPException(status_code=400, detail="Пользователь не привязан к карте гостя iikoCard")
        
    if vk_user.vk_bonus_balance <= 0:
        raise HTTPException(status_code=400, detail="У пользователя нет баллов для перевода")
        
    from app.services.vk_service import transfer_vk_points_to_iiko
    
    # Получаем group_id
    group_id = vk_user.vk_group_id
    if not group_id:
        raise HTTPException(status_code=400, detail="Пользователь не связан ни с одной группой ВК")
        
    from app.models.vk_bot_connection import VkBotConnection
    bot_conn = db.exec(select(VkBotConnection).where(VkBotConnection.vk_group_id == group_id, VkBotConnection.is_active == True)).first()
    bot_token = bot_conn.vk_bot_token if bot_conn else None
    
    msg_text = await transfer_vk_points_to_iiko(db, vk_user, group_id, bot_token)
    
    return {"status": "success", "message": msg_text}
