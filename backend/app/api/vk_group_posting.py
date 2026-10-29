"""
API контроллер для постинга на стенах групп ВКонтакте от имени личного аккаунта
"""
import os
import uuid
import asyncio
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from pydantic import BaseModel
from sqlmodel import Session, select, func, desc

from app.core.database import get_session
from app.core.datetime_utils import utc_now
from app.models.user import User
from app.models.chat import MultichatAccount
from app.models.vk_group_posting import VkGroupPreset, VkGroupPostCampaign, VkGroupPostHistory
from app.services.vk_group_posting_service import vk_group_posting_service
from app.api import deps

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vk-group-posting", tags=["VK Group Posting"])


# --- Pydantic Схемы ---

class GroupCheckRequest(BaseModel):
    account_id: int
    raw_input: Optional[str] = None
    identifiers: Optional[List[str]] = None


class PresetCreateUpdate(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    groups_data: List[Dict[str, Any]] = []


class PublishTargetGroup(BaseModel):
    id: int
    name: Optional[str] = None
    screen_name: Optional[str] = None
    photo: Optional[str] = None


class PublishRequest(BaseModel):
    account_id: int
    text: str
    media_urls: List[str] = []
    groups: List[PublishTargetGroup]
    delay_seconds: int = 20
    preset_id: Optional[int] = None
    title: Optional[str] = None


class RefreshStatsRequest(BaseModel):
    account_id: Optional[int] = None
    history_ids: Optional[List[int]] = None


# --- Эндпоинты ---

@router.get("/accounts")
def get_available_vk_accounts(
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Получение списка доступных личных аккаунтов ВКонтакте, подключенных в Мультичате
    """
    accounts = db.exec(
        select(MultichatAccount)
        .where(MultichatAccount.channel == "vk_user")
        .where(MultichatAccount.status == "active")
        .order_by(MultichatAccount.created_at.desc())
    ).all()

    result = []
    for acc in accounts:
        result.append({
            "id": acc.id,
            "name": acc.name,
            "phone": acc.phone,
            "has_token": bool(acc.token),
            "status": acc.status,
            "created_at": acc.created_at
        })
    return result


class LinkTokenRequest(BaseModel):
    token: str
    name: Optional[str] = None


@router.post("/accounts/link-token")
async def link_vk_user_token(
    payload: LinkTokenRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Привязка или обновление личного токена ВКонтакте
    """
    token = payload.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Укажите токен доступа ВКонтакте")

    # Проверяем токен через VK API users.get
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://api.vk.com/method/users.get", params={
                "access_token": token,
                "v": "5.199",
                "fields": "photo_100"
            })
            data = resp.json()

        if "error" in data:
            err = data["error"]
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка проверки токена ВКонтакте ({err.get('error_code')}): {err.get('error_msg')}"
            )

        users_list = data.get("response", [])
        if not users_list:
            raise HTTPException(status_code=400, detail="Не удалось получить профиль пользователя ВКонтакте")

        u = users_list[0]
        user_name = payload.name or f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or f"VK {u.get('id')}"
        user_id = u.get("id")
        avatar = u.get("photo_100")

        # Сохраняем/обновляем в multichat_accounts
        from app.services.multichat_user_service import multichat_user_service
        account = multichat_user_service.create_or_update_account(
            channel="vk_user",
            name=user_name,
            phone=None,
            token=token,
            status="active"
        )
        return {
            "status": "success",
            "account": {
                "id": account.id,
                "name": account.name,
                "status": account.status
            },
            "message": f"Аккаунт «{user_name}» успешно подключен!"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking VK user token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/check")
async def check_groups(
    payload: GroupCheckRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Проверка списка сообществ на открытость стены (can_post == 1) от имени выбранного личного аккаунта
    """
    account = db.get(MultichatAccount, payload.account_id)
    if not account or not account.token:
        raise HTTPException(
            status_code=400,
            detail="Выбранный личный аккаунт ВК не найден или у него отсутствует токен"
        )

    identifiers = payload.identifiers or []
    if payload.raw_input:
        parsed = vk_group_posting_service.parse_group_identifiers(payload.raw_input)
        identifiers.extend(parsed)

    # Убираем дубликаты
    identifiers = list(dict.fromkeys([str(x).strip() for x in identifiers if str(x).strip()]))
    if not identifiers:
        return {"groups": [], "total": 0, "open_count": 0}

    # Резервный токен бота для гарантированной проверки открытости стен
    from app.models.vk_bot_connection import VkBotConnection
    fallback_conn = db.exec(
        select(VkBotConnection)
        .where(VkBotConnection.is_active == True)
        .where(VkBotConnection.vk_bot_token.isnot(None))
    ).first()
    fallback_token = fallback_conn.vk_bot_token if fallback_conn else None

    try:
        check_res = await vk_group_posting_service.check_groups_info(
            account_token=account.token,
            identifiers=identifiers,
            fallback_token=fallback_token
        )
        checked_groups = check_res.get("groups", [])
        open_count = sum(1 for g in checked_groups if g.get("can_publish"))
        return {
            "groups": checked_groups,
            "total": len(checked_groups),
            "open_count": open_count,
            "account_flood_control": check_res.get("account_flood_control", False),
            "account_warning": check_res.get("account_warning"),
            "is_using_fallback": check_res.get("is_using_fallback", False)
        }
    except Exception as e:
        logger.error(f"Error checking VK groups: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Загрузка изображения для поста на сервер
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Разрешена загрузка только изображений")

    ext = os.path.splitext(file.filename)[1] or ".jpg"
    unique_filename = f"{uuid.uuid4().hex[:12]}_{int(utc_now().timestamp())}{ext}"
    
    # Сохраняем в media/img/vk_group_posts
    target_dir = "/app/media/img/vk_group_posts"
    if not os.path.exists(target_dir):
        # Локальный фоллбэк
        target_dir = os.path.join(os.getcwd(), "media", "img", "vk_group_posts")
        os.makedirs(target_dir, exist_ok=True)

    file_path = os.path.join(target_dir, unique_filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    public_url = f"/media/img/vk_group_posts/{unique_filename}"
    return {"url": public_url, "filename": unique_filename}


# --- Пресеты (Блоки списков групп) ---

@router.get("/presets")
def get_presets(
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """Получение всех сохраненных блоков (пресетов) групп"""
    presets = db.exec(
        select(VkGroupPreset).order_by(VkGroupPreset.updated_at.desc())
    ).all()
    return presets


@router.post("/presets")
def save_preset(
    payload: PresetCreateUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """Создание или обновление блока групп"""
    if payload.id:
        preset = db.get(VkGroupPreset, payload.id)
        if not preset:
            raise HTTPException(status_code=404, detail="Пресет не найден")
        preset.name = payload.name
        preset.description = payload.description
        preset.groups_data = payload.groups_data
        preset.updated_at = utc_now()
    else:
        preset = VkGroupPreset(
            name=payload.name,
            description=payload.description,
            groups_data=payload.groups_data,
            created_at=utc_now(),
            updated_at=utc_now()
        )
        db.add(preset)

    db.commit()
    db.refresh(preset)
    return preset


@router.delete("/presets/{preset_id}")
def delete_preset(
    preset_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """Удаление блока групп"""
    preset = db.get(VkGroupPreset, preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Пресет не найден")
    db.delete(preset)
    db.commit()
    return {"status": "success", "message": "Блок групп успешно удален"}


# --- Публикация и рассылка ---

@router.post("/publish")
async def publish_posts(
    payload: PublishRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Запуск постинга записей на стенах сообществ ВКонтакте от имени личного аккаунта
    """
    account = db.get(MultichatAccount, payload.account_id)
    if not account or not account.token:
        raise HTTPException(status_code=400, detail="Личный аккаунт ВК не найден или не авторизован")

    if not payload.groups:
        raise HTTPException(status_code=400, detail="Не выбрано ни одного сообщества для публикации")

    if not payload.text and not payload.media_urls:
        raise HTTPException(status_code=400, detail="Укажите текст публикации или прикрепите изображение")

    # 1. Загружаем фото в ВК от имени аккаунта (если прикреплены)
    vk_attachments = []
    for media_url in payload.media_urls:
        try:
            att = await vk_group_posting_service.upload_wall_photo_from_account(account.token, media_url)
            vk_attachments.append(att)
        except Exception as e:
            logger.error(f"Failed to upload media to VK wall photo: {e}")
            raise HTTPException(status_code=400, detail=f"Ошибка загрузки фото в ВК: {str(e)}")

    # 2. Создаем запись кампании
    campaign_title = payload.title or (payload.text[:50] + "..." if len(payload.text) > 50 else payload.text) or "Рассылка постов"
    campaign = VkGroupPostCampaign(
        title=campaign_title,
        text=payload.text,
        media_urls=payload.media_urls,
        account_id=account.id,
        account_name=account.name,
        preset_id=payload.preset_id,
        delay_seconds=max(5, payload.delay_seconds),
        total_count=len(payload.groups),
        success_count=0,
        failed_count=0,
        status="in_progress",
        created_at=utc_now(),
        updated_at=utc_now()
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    # 3. Последовательная публикация постов с задержкой антиспама
    results = []
    success_count = 0
    failed_count = 0

    for idx, grp in enumerate(payload.groups):
        grp_id = grp.id
        now = utc_now()

        # Отправляем пост
        post_res = await vk_group_posting_service.publish_post_to_group(
            account_token=account.token,
            group_id=grp_id,
            message=payload.text,
            attachments=vk_attachments
        )

        if post_res.get("success"):
            success_count += 1
            hist_item = VkGroupPostHistory(
                campaign_id=campaign.id,
                account_id=account.id,
                account_name=account.name,
                group_id=grp_id,
                group_name=grp.name,
                group_screen_name=grp.screen_name,
                group_photo=grp.photo,
                post_id=post_res.get("post_id"),
                post_url=post_res.get("post_url"),
                text=payload.text,
                media_urls=payload.media_urls,
                status="published",
                error_message=None,
                views_count=0,
                likes_count=0,
                published_at=now,
                last_checked_at=now,
                created_at=now,
                updated_at=now
            )
            db.add(hist_item)
            results.append({
                "group_id": grp_id,
                "group_name": grp.name,
                "status": "published",
                "post_url": post_res.get("post_url"),
                "post_id": post_res.get("post_id")
            })
        else:
            failed_count += 1
            hist_item = VkGroupPostHistory(
                campaign_id=campaign.id,
                account_id=account.id,
                account_name=account.name,
                group_id=grp_id,
                group_name=grp.name,
                group_screen_name=grp.screen_name,
                group_photo=grp.photo,
                post_id=None,
                post_url=None,
                text=payload.text,
                media_urls=payload.media_urls,
                status="failed",
                error_message=post_res.get("error_message"),
                published_at=None,
                created_at=now,
                updated_at=now
            )
            db.add(hist_item)
            results.append({
                "group_id": grp_id,
                "group_name": grp.name,
                "status": "failed",
                "error": post_res.get("error_message")
            })

        db.commit()

        # Задержка между постами (не ждем после последнего)
        if idx < len(payload.groups) - 1:
            delay = max(5, payload.delay_seconds)
            await asyncio.sleep(delay)

    # Финализируем статус кампании
    campaign.success_count = success_count
    campaign.failed_count = failed_count
    campaign.status = "completed" if success_count > 0 else "failed"
    campaign.updated_at = utc_now()
    db.add(campaign)
    db.commit()

    return {
        "status": "success",
        "campaign_id": campaign.id,
        "total": len(payload.groups),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }


# --- История и Метрики ---

@router.get("/history")
def get_post_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = None,
    account_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Получение истории опубликованных постов с пагинацией и суммарной аналитикой
    """
    query = select(VkGroupPostHistory)

    if status and status != "all":
        query = query.where(VkGroupPostHistory.status == status)

    if account_id:
        query = query.where(VkGroupPostHistory.account_id == account_id)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            (VkGroupPostHistory.group_name.ilike(search_pattern)) |
            (VkGroupPostHistory.text.ilike(search_pattern)) |
            (VkGroupPostHistory.account_name.ilike(search_pattern))
        )

    # Подсчет общего количества
    total_query = select(func.count(VkGroupPostHistory.id))
    if status and status != "all":
        total_query = total_query.where(VkGroupPostHistory.status == status)
    if account_id:
        total_query = total_query.where(VkGroupPostHistory.account_id == account_id)
    if search:
        total_query = total_query.where(
            (VkGroupPostHistory.group_name.ilike(search_pattern)) |
            (VkGroupPostHistory.text.ilike(search_pattern)) |
            (VkGroupPostHistory.account_name.ilike(search_pattern))
        )
    total_count = db.exec(total_query).one()

    # Сводные агрегированные счетчики
    stats_query = select(
        func.count(VkGroupPostHistory.id).label("total"),
        func.coalesce(func.sum(VkGroupPostHistory.views_count), 0).label("views"),
        func.coalesce(func.sum(VkGroupPostHistory.likes_count), 0).label("likes"),
        func.coalesce(func.sum(VkGroupPostHistory.reposts_count), 0).label("reposts"),
    ).where(VkGroupPostHistory.status == "published")
    stats_res = db.exec(stats_query).first()

    summary_stats = {
        "published_posts": stats_res[0] if stats_res else 0,
        "total_views": int(stats_res[1]) if stats_res else 0,
        "total_likes": int(stats_res[2]) if stats_res else 0,
        "total_reposts": int(stats_res[3]) if stats_res else 0,
    }

    # Постраничная выборка
    offset = (page - 1) * page_size
    items = db.exec(
        query.order_by(desc(VkGroupPostHistory.created_at))
        .offset(offset)
        .limit(page_size)
    ).all()

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "summary": summary_stats
    }


@router.post("/history/refresh-stats")
async def refresh_stats(
    payload: RefreshStatsRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Обновление метрик просмотров, лайков и репостов из VK API
    """
    # Выбираем активный аккаунт для выполнения запроса
    account = None
    if payload.account_id:
        account = db.get(MultichatAccount, payload.account_id)
    
    if not account or not account.token:
        # Берем любой первый активный аккаунт ВК
        account = db.exec(
            select(MultichatAccount)
            .where(MultichatAccount.channel == "vk_user")
            .where(MultichatAccount.status == "active")
            .where(MultichatAccount.token.isnot(None))
        ).first()

    if not account or not account.token:
        raise HTTPException(
            status_code=400,
            detail="Не найден активный личный аккаунт ВК с токеном для опроса статистики"
        )

    # Выбираем посты
    query = select(VkGroupPostHistory).where(VkGroupPostHistory.post_id.isnot(None))
    if payload.history_ids:
        query = query.where(VkGroupPostHistory.id.in_(payload.history_ids))
    else:
        # Проверяем опубликованные за последние 30 дней
        query = query.where(VkGroupPostHistory.status.in_(["published", "deleted"])).limit(300)

    items = db.exec(query).all()
    if not items:
        return {"status": "success", "updated": 0, "message": "Нет постов для проверки"}

    res = await vk_group_posting_service.refresh_posts_metrics(account.token, items, db)
    return {
        "status": "success",
        "updated": res.get("updated", 0),
        "deleted": res.get("deleted", 0),
        "message": f"Статистика обновлена: {res.get('updated', 0)} постов актуализировано, {res.get('deleted', 0)} удалено"
    }


@router.delete("/history/{history_id}")
def delete_history_item(
    history_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.get_current_user)
):
    """Удаление записи из истории"""
    item = db.get(VkGroupPostHistory, history_id)
    if not item:
        raise HTTPException(status_code=404, detail="Запись истории не найдена")
    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Запись удалена"}
