import os
import random
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlmodel import Session, select
from pydantic import BaseModel

from app.api.deps import get_db, require_permission
from app.models.vk_contest import VkContest, VkContestPlayer, VkContestWinner
from app.models.vk_bot_connection import VkBotConnection
from app.services.vk_contest_service import vk_contest_service
from app.services.vk_birthday_service import vk_birthday_service
from app.core.datetime_utils import utc_now

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Схемы данных Pydantic ---
 
class VkContestCreateSchema(BaseModel):
    vk_bot_connection_id: int
    title: str
    rules_text: str = ""
    game_type: str = "roulette"
    prizes: List[Dict[str, Any]] = []
    start_attempts: int = 3
    max_attempts: int = 10
    delay_between_moves: int = 60
    repost_attempts: int = 3
    subscribe_attempts: int = 0
    like_attempts: int = 1
    safe_code: Optional[str] = None
    msg_miss: Optional[str] = None
    msg_win: Optional[str] = None
    msg_out_of_attempts: Optional[str] = None
    msg_cooldown: Optional[str] = None
    msg_subscribe_needed: Optional[str] = None
    msg_like_needed: Optional[str] = None
    msg_repost_needed: Optional[str] = None
    msg_invalid_format: Optional[str] = None
    msg_pm_congratulations: Optional[str] = None
    can_win_once: Optional[bool] = None
    help_draw_prizes: Optional[bool] = None
    black_list: Optional[List[str]] = None
    white_list: Optional[List[str]] = None
    remind_winner_pm: Optional[bool] = None
    remind_attempts: Optional[bool] = None
    remind_attempts_count: Optional[int] = None
    remind_attempts_quiet_from: Optional[int] = None
    remind_attempts_quiet_to: Optional[int] = None
    anti_prize_hunters: Optional[bool] = None
    draw_probability_interval: Optional[int] = None
    penalty_percent: int = 10
    bonus_percent: int = 20
    vk_bot_token: Optional[str] = None
 
class VkContestUpdateSchema(BaseModel):
    title: Optional[str] = None
    rules_text: Optional[str] = None
    game_type: Optional[str] = None
    prizes: Optional[List[Dict[str, Any]]] = None
    start_attempts: Optional[int] = None
    max_attempts: Optional[int] = None
    delay_between_moves: Optional[int] = None
    repost_attempts: Optional[int] = None
    subscribe_attempts: Optional[int] = None
    like_attempts: Optional[int] = None
    safe_code: Optional[str] = None
    msg_miss: Optional[str] = None
    msg_win: Optional[str] = None
    msg_out_of_attempts: Optional[str] = None
    msg_cooldown: Optional[str] = None
    msg_subscribe_needed: Optional[str] = None
    msg_like_needed: Optional[str] = None
    msg_repost_needed: Optional[str] = None
    msg_invalid_format: Optional[str] = None
    msg_pm_congratulations: Optional[str] = None
    can_win_once: Optional[bool] = None
    help_draw_prizes: Optional[bool] = None
    black_list: Optional[List[str]] = None
    white_list: Optional[List[str]] = None
    remind_winner_pm: Optional[bool] = None
    remind_attempts: Optional[bool] = None
    remind_attempts_count: Optional[int] = None
    remind_attempts_quiet_from: Optional[int] = None
    remind_attempts_quiet_to: Optional[int] = None
    anti_prize_hunters: Optional[bool] = None
    draw_probability_interval: Optional[int] = None
    penalty_percent: Optional[int] = None
    bonus_percent: Optional[int] = None
    vk_bot_token: Optional[str] = None
 
class CodeValidationSchema(BaseModel):
    code: str
    order_id: Optional[str] = None
    mark_activated: bool = False


# --- Эндпоинты ---

@router.get("/", response_model=List[VkContest], dependencies=[Depends(require_permission("marketing_vk_bots_view"))])
def get_contests(vk_bot_connection_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Получить список конкурсов"""
    query = select(VkContest)
    if vk_bot_connection_id is not None:
        query = query.where(VkContest.vk_bot_connection_id == vk_bot_connection_id)
    return db.exec(query.order_by(VkContest.created_at.desc())).all()


@router.post("/", response_model=VkContest, dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def create_contest(data: VkContestCreateSchema, db: Session = Depends(get_db)):
    """Создать новый конкурс (черновик)"""
    conn = db.get(VkBotConnection, data.vk_bot_connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Подключение ВК не найдено")

    # Инициализируем призы с won_count = 0
    prizes_formatted = []
    for idx, p in enumerate(data.prizes):
        prizes_formatted.append({
            "id": p.get("id") or (idx + 1),
            "name": p.get("name", "Приз"),
            "qty": int(p.get("qty", 1)),
            "won_count": 0
        })

    contest_data = {
        "vk_bot_connection_id": data.vk_bot_connection_id,
        "title": data.title,
        "rules_text": data.rules_text,
        "game_type": data.game_type,
        "prizes": prizes_formatted,
        "start_attempts": data.start_attempts,
        "max_attempts": data.max_attempts,
        "delay_between_moves": data.delay_between_moves,
        "repost_attempts": data.repost_attempts,
        "subscribe_attempts": data.subscribe_attempts,
        "like_attempts": data.like_attempts,
        "safe_code": data.safe_code
    }
    
    # Записываем новые поля сообщений и продвинутые настройки, если они переданы
    all_optional_fields = [
        "msg_miss", "msg_win", "msg_out_of_attempts", "msg_cooldown", 
        "msg_subscribe_needed", "msg_like_needed", "msg_repost_needed", 
        "msg_invalid_format", "msg_pm_congratulations",
        "can_win_once", "help_draw_prizes", "black_list", "white_list",
        "remind_winner_pm", "remind_attempts", "remind_attempts_count",
        "remind_attempts_quiet_from", "remind_attempts_quiet_to",
        "anti_prize_hunters", "draw_type", "draw_probability_interval",
        "penalty_percent", "bonus_percent"
    ]
    for field in all_optional_fields:
        val = getattr(data, field)
        if val is not None:
            contest_data[field] = val

    contest = VkContest(**contest_data)
    db.add(contest)
    db.commit()
    db.refresh(contest)
    return contest


@router.patch("/{contest_id}", response_model=VkContest, dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def update_contest(contest_id: int, data: VkContestUpdateSchema, db: Session = Depends(get_db)):
    """Обновить настройки конкурса"""
    contest = db.get(VkContest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Конкурс не найден")

    if contest.is_active:
        raise HTTPException(status_code=400, detail="Нельзя редактировать параметры запущенного конкурса!")

    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "prizes" and value is not None:
            # Обновляем призы, с сохранением won_count
            prizes_formatted = []
            for idx, p in enumerate(value):
                prizes_formatted.append({
                    "id": p.get("id") or (idx + 1),
                    "name": p.get("name", "Приз"),
                    "qty": int(p.get("qty", 1)),
                    "won_count": p.get("won_count", 0)
                })
            setattr(contest, key, prizes_formatted)
        else:
            setattr(contest, key, value)

    contest.updated_at = utc_now()
    db.add(contest)
    db.commit()
    db.refresh(contest)
    return contest


@router.delete("/{contest_id}", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def delete_contest(contest_id: int, db: Session = Depends(get_db)):
    """Удалить конкурс"""
    contest = db.get(VkContest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Конкурс не найден")

    # Сначала удалим игроков и победителей
    players = db.exec(select(VkContestPlayer).where(VkContestPlayer.contest_id == contest_id)).all()
    for p in players:
        db.delete(p)
    winners = db.exec(select(VkContestWinner).where(VkContestWinner.contest_id == contest_id)).all()
    for w in winners:
        db.delete(w)

    db.delete(contest)
    db.commit()
    return {"status": "success", "message": "Конкурс успешно удален"}


@router.post("/{contest_id}/launch", response_model=VkContest, dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
async def launch_contest(contest_id: int, db: Session = Depends(get_db)):
    """Опубликовать конкурс на стене группы ВК и запустить игру"""
    contest = db.get(VkContest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Конкурс не найден")

    if contest.is_active:
        return contest

    conn = db.get(VkBotConnection, contest.vk_bot_connection_id)
    if not conn or not conn.is_active:
        raise HTTPException(status_code=400, detail="Подключение ВК неактивно")

    bot_token = conn.vk_bot_token
    group_id = conn.vk_group_id

    # 1. Инициализируем игровое поле
    vk_contest_service.initialize_game_field(contest)

    # 2. Рендерим стартовую картинку для сундуков/морского боя
    attachment = None
    if contest.game_type in ("chests", "seabattle"):
        import tempfile
        # Отрисовка
        if contest.game_type == "chests":
            img = vk_contest_service.generate_chests_image(contest.game_field_data)
        else:
            img = vk_contest_service.generate_seabattle_image(contest.game_field_data)
            
        buf = BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        
        # Временный файл
        temp_f = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_f.write(img_bytes)
        temp_f.close()
        
        # Аплоад в ВК
        attachment = await vk_birthday_service.upload_vk_wall_photo(bot_token, temp_f.name, group_id)
        try:
            os.unlink(temp_f.name)
        except Exception:
            pass

    # 3. Публикуем пост в ВК
    import httpx
    url = "https://api.vk.ru/method/wall.post"
    params = {
        "owner_id": -group_id,
        "from_group": 1,
        "message": f"🏆 {contest.title} 🏆\n\n{contest.rules_text}",
        "access_token": bot_token,
        "v": "5.199"
    }
    if attachment:
        params["attachments"] = attachment
        
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=params)
            res_data = resp.json()
            if "error" in res_data:
                raise HTTPException(status_code=500, detail=f"Ошибка VK API при публикации поста: {res_data['error']}")
            
            post_id = res_data["response"]["post_id"]
            contest.post_id = post_id
    except Exception as e:
        logger.error(f"Failed to post contest wall message: {e}")
        raise HTTPException(status_code=500, detail=f"Не удалось опубликовать пост в группе ВК: {str(e)}")

    contest.is_active = True
    contest.updated_at = utc_now()
    db.add(contest)
    db.commit()
    db.refresh(contest)
    return contest


@router.post("/{contest_id}/stop", response_model=VkContest, dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def stop_contest(contest_id: int, db: Session = Depends(get_db)):
    """Остановить конкурс"""
    contest = db.get(VkContest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Конкурс не найден")

    contest.is_active = False
    contest.updated_at = utc_now()
    db.add(contest)
    db.commit()
    db.refresh(contest)
    return contest


@router.get("/{contest_id}/players", response_model=List[VkContestPlayer], dependencies=[Depends(require_permission("marketing_vk_bots_view"))])
def get_contest_players(contest_id: int, db: Session = Depends(get_db)):
    """Получить участников конкурса"""
    return db.exec(select(VkContestPlayer).where(VkContestPlayer.contest_id == contest_id).order_by(VkContestPlayer.attempts_used.desc())).all()


@router.get("/{contest_id}/winners", response_model=List[VkContestWinner], dependencies=[Depends(require_permission("marketing_vk_bots_view"))])
def get_contest_winners(contest_id: int, db: Session = Depends(get_db)):
    """Получить список победителей конкурса"""
    return db.exec(select(VkContestWinner).where(VkContestWinner.contest_id == contest_id).order_by(VkContestWinner.won_at.desc())).all()


@router.get("/{contest_id}/actions", dependencies=[Depends(require_permission("marketing_vk_bots_view"))])
def get_contest_actions(contest_id: int, db: Session = Depends(get_db)):
    """Получить историю действий и ходов участников конкурса"""
    from app.models.vk_contest import VkContestAction
    return db.exec(
        select(VkContestAction)
        .where(VkContestAction.contest_id == contest_id)
        .order_by(VkContestAction.created_at.desc())
    ).all()


@router.post("/validate-code")
def validate_win_code(data: CodeValidationSchema, db: Session = Depends(get_db)):
    """Сквозная проверка промокода выигранного в конкурсе для применения в корзине"""
    winner = db.exec(
        select(VkContestWinner).where(VkContestWinner.win_code == data.code.strip().upper())
    ).first()
    
    if not winner:
        raise HTTPException(status_code=404, detail="Промокод не найден или недействителен")
        
    if data.mark_activated:
        if winner.is_activated:
            raise HTTPException(status_code=400, detail=f"Промокод {winner.win_code} уже активирован в заказе {winner.order_id}")
        
        winner.is_activated = True
        winner.activated_at = utc_now()
        winner.order_id = data.order_id
        db.add(winner)
        
        # Логируем активацию промокода в историю действий
        vk_contest_service.log_action(
            db, 
            winner.contest_id, 
            winner.vk_user_id, 
            winner.first_name, 
            winner.last_name, 
            "system", 
            f"Активирован промокод {winner.win_code} для заказа {data.order_id or '—'}"
        )
        db.commit()
        db.refresh(winner)

    return {
        "status": "success",
        "win_code": winner.win_code,
        "prize_name": winner.prize_name,
        "winner_name": f"{winner.first_name} {winner.last_name}",
        "won_at": winner.won_at,
        "is_activated": winner.is_activated,
        "activated_at": winner.activated_at,
        "order_id": winner.order_id
    }


@router.post("/{contest_id}/finish", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
def finish_contest(contest_id: int, db: Session = Depends(get_db)):
    """Принудительно подвести итоги конкурса типа battle и закрыть его"""
    from app.services.vk_contest_service import vk_contest_service
    try:
        result = vk_contest_service.finish_battle_contest(db, contest_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prizes/upload", dependencies=[Depends(require_permission("marketing_vk_bots_edit"))])
async def upload_prize_image(file: UploadFile = File(...)):
    """Загрузка изображения приза для конкурса на сервер"""
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.webp'):
            raise HTTPException(status_code=400, detail="Разрешены только файлы изображений (png, jpg, jpeg, gif, webp)")

        media_dir = "/app/media/img/contests"
        os.makedirs(media_dir, exist_ok=True)

        filename = f"prize_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}{ext}"
        file_path = os.path.join(media_dir, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        relative_url = f"/media/img/contests/{filename}"
        return {"status": "success", "image_url": relative_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения картинки приза: {str(e)}")
