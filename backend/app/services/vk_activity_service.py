"""
Сервис для подсчета баллов активности пользователей ВКонтакте
"""
import logging
import httpx
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from sqlmodel import Session, select, func

from app.models.vk_activity_settings import VkActivitySettings
from app.models.vk_activity import VkActivity, VkActivityPenaltyTimer
from app.models.vk_user import VkUser
from app.models.customer import Customer
from app.models.vk_bot_connection import VkBotConnection
from app.core.datetime_utils import utc_now

logger = logging.getLogger(__name__)

async def call_vk_api(method: str, params: Dict[str, Any], bot_token: str) -> Optional[Dict[str, Any]]:
    """Вспомогательный метод для вызова VK API"""
    params["access_token"] = bot_token
    params["v"] = "5.199"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"https://api.vk.ru/method/{method}", data=params)
            res_data = response.json()
            if "error" in res_data:
                logger.error(f"VK API Error in {method}: {res_data['error']}")
                return None
            return res_data.get("response")
        except Exception as e:
            logger.error(f"Failed to call VK API {method}: {e}")
            return None

async def get_vk_user_profile(vk_id: int, bot_token: str) -> Optional[Dict[str, Any]]:
    """Получает имя, фамилию и аватар пользователя из VK"""
    res = await call_vk_api("users.get", {"user_ids": str(vk_id), "fields": "photo_50,screen_name"}, bot_token)
    if res and len(res) > 0:
        return res[0]
    return None

async def ensure_vk_user(db: Session, vk_id: int, group_id: Optional[int], bot_token: str | None) -> VkUser:
    """Убеждается, что пользователь VK есть в базе, при необходимости создает/обновляет данные"""
    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
    if not vk_user:
        first_name = "Пользователь"
        last_name = "ВКонтакте"
        photo_50 = None
        screen_name = None
        
        if bot_token:
            profile = await get_vk_user_profile(vk_id, bot_token)
            if profile:
                first_name = profile.get("first_name", first_name)
                last_name = profile.get("last_name", last_name)
                photo_50 = profile.get("photo_50")
                screen_name = profile.get("screen_name")
                
        vk_user = VkUser(
            vk_id=vk_id,
            vk_group_id=group_id,
            first_name=first_name,
            last_name=last_name,
            photo_50=photo_50,
            screen_name=screen_name,
            vk_bonus_balance=0,
            is_linked=False,
            is_subscribed=True
        )
        db.add(vk_user)
        db.commit()
        db.refresh(vk_user)
    return vk_user

async def get_post_info(post_id: int, owner_id: int, bot_token: str) -> Optional[Dict[str, Any]]:
    """Возвращает дату (timestamp) и текст поста"""
    user_token = None
    try:
        from app.models.vk_bot_connection import VkBotConnection
        from app.core.database import Session, engine
        from sqlmodel import select
        
        group_id = abs(owner_id)
        with Session(engine) as db_session:
            conn = db_session.exec(select(VkBotConnection).where(VkBotConnection.vk_group_id == group_id)).first()
            if conn and conn.vk_user_token:
                user_token = conn.vk_user_token
            if not user_token:
                from app.models.chat import MultichatAccount
                vk_acc = db_session.exec(select(MultichatAccount).where(MultichatAccount.channel == "vk_user", MultichatAccount.status == "active")).first()
                if vk_acc and vk_acc.token:
                    user_token = vk_acc.token
    except Exception as e:
        logger.error(f"Error fetching vk_user_token in get_post_info: {e}")

    # Перебираем токены: сначала user_token (если есть), затем гарантированный bot_token
    tokens_to_try = [t for t in [user_token, bot_token] if t]
    for current_token in tokens_to_try:
        res = await call_vk_api("wall.getById", {"posts": f"{owner_id}_{post_id}"}, current_token)
        if res and isinstance(res, list) and len(res) > 0:
            return {
                "date": res[0].get("date"),
                "text": res[0].get("text", "")
            }
    return None

async def get_post_publish_date(post_id: int, owner_id: int, bot_token: str) -> Optional[int]:
    """Возвращает timestamp публикации поста"""
    info = await get_post_info(post_id, owner_id, bot_token)
    return info.get("date") if info else None

def is_post_eligible_by_age_and_keywords(
    post_info: Optional[Dict[str, Any]], 
    settings: VkActivitySettings,
    now_dt: datetime
) -> bool:
    """
    Проверяет, подходит ли пост по сроку давности и ключевым словам.
    1. Если у поста есть хотя бы одно из ключевых слов-исключений (override_keywords), 
       он участвует НЕЗАВИСИМО от срока давности!
    2. Иначе проверяется post_max_age_days (если > 0). Посты старше указанного кол-ва дней отклоняются.
    """
    if not post_info:
        return True
        
    post_text = (post_info.get("text") or "").lower()
    post_date_ts = post_info.get("date")
    
    # 1. Проверяем исключения по ключевым словам
    override_keywords = getattr(settings, "override_keywords", None)
    if override_keywords:
        kw_list = [k.strip().lower() for k in override_keywords.split(",") if k.strip()]
        for kw in kw_list:
            if kw in post_text:
                logger.info(f"Post matches override keyword '{kw}', age check skipped.")
                return True

    # 2. Проверяем срок давности постов в днях
    post_max_age_days = getattr(settings, "post_max_age_days", 0)
    if post_max_age_days and post_max_age_days > 0 and post_date_ts:
        post_dt = datetime.fromtimestamp(post_date_ts, tz=timezone.utc)
        age_days = (now_dt - post_dt).total_seconds() / 86400.0
        if age_days > post_max_age_days:
            logger.info(f"Post is {age_days:.1f} days old (max allowed: {post_max_age_days} days). Ignored.")
            return False

    return True

def is_post_ignored(post_id: Optional[int], settings: VkActivitySettings) -> bool:
    if not post_id or not settings.ignored_post_ids:
        return False
    try:
        ignored_ids = [int(x.strip()) for x in settings.ignored_post_ids.split(",") if x.strip().isdigit()]
        return post_id in ignored_ids
    except Exception as e:
        logger.error(f"Error parsing ignored_post_ids: {e}")
        return False

class VkActivityService:
    """Сервис управления баллами активности"""
    
    async def process_activity_event(
        self, 
        db: Session, 
        event_type: str, 
        obj: Dict[str, Any], 
        bot_token: str | None, 
        group_id: Optional[int]
    ):
        """Основной обработчик входящих Callback-событий для начисления/вычитания баллов"""
        if not group_id or not bot_token:
            return

        # 1. Загружаем настройки активности для этого сообщества
        settings = db.exec(
            select(VkActivitySettings)
            .join(VkBotConnection, VkBotConnection.id == VkActivitySettings.vk_bot_connection_id)
            .where(VkBotConnection.vk_group_id == group_id)
        ).first()

        if not settings or not settings.is_active:
            return

        if settings.vk_bot_token:
            bot_token = settings.vk_bot_token

        # 2. Проверяем глобальный период конкурса
        now = utc_now()
        if settings.period_start_date:
            # Принудительно приводим к timezone-aware UTC для сравнения
            start_dt = settings.period_start_date.replace(tzinfo=timezone.utc) if settings.period_start_date.tzinfo is None else settings.period_start_date
            if now < start_dt:
                logger.info(f"Activity event ignored: contest hasn't started yet (start: {start_dt})")
                return
            if settings.period_duration_days > 0:
                end_dt = start_dt + timedelta(days=settings.period_duration_days)
                if now > end_dt:
                    logger.info(f"Activity event ignored: contest has ended (end: {end_dt})")
                    return

        # 3. Извлекаем vk_id и объект
        vk_id = None
        action_user_field = {
            "like_add": "liker_id",
            "like_remove": "liker_id",
            "wall_reply_new": "from_id",
            "wall_reply_delete": "from_id",  # При удалении коммента ID пользователя может отсутствовать в from_id, но быть в user_id
            "wall_repost": "from_id",
            "poll_vote_new": "user_id",
            "group_join": "user_id",
            "group_leave": "user_id"
        }
        
        vk_id = obj.get(action_user_field.get(event_type, ""))
        if not vk_id and event_type in ["wall_reply_delete", "group_leave"]:
            vk_id = obj.get("user_id")

        if not vk_id or vk_id < 0: # Игнорируем действия от имени групп (отрицательные ID)
            return

        # 4. Проверяем и создаем VkUser
        vk_user = await ensure_vk_user(db, vk_id, group_id, bot_token)

        # 5. Обработка событий
        if event_type == "like_add":
            await self._handle_like_add(db, vk_user, obj, settings, bot_token, group_id)
        elif event_type == "like_remove":
            await self._handle_like_remove(db, vk_user, obj, settings, bot_token)
        elif event_type == "wall_reply_new":
            await self._handle_comment_add(db, vk_user, obj, settings, bot_token, group_id)
        elif event_type == "wall_reply_delete":
            await self._handle_comment_delete(db, vk_user, obj, settings, bot_token)
        elif event_type == "wall_repost":
            await self._handle_repost_add(db, vk_user, obj, settings, bot_token, group_id)
        elif event_type == "poll_vote_new":
            await self._handle_poll_vote_add(db, vk_user, obj, settings, bot_token, group_id)
        elif event_type == "group_join":
            await self._handle_group_join(db, vk_user, obj, settings, bot_token, group_id)
        elif event_type == "group_leave":
            await self._handle_group_leave(db, vk_user, obj, settings, bot_token)

    def _trigger_penalty_timer(self, db: Session, vk_user: VkUser, target_type: str, target_id: str, settings: VkActivitySettings, connection_id: int):
        """Запускает или обновляет штрафной таймер для пользователя"""
        # Ищем старый таймер для этой цели
        existing_timer = db.exec(
            select(VkActivityPenaltyTimer)
            .where(VkActivityPenaltyTimer.vk_id == vk_user.vk_id)
            .where(VkActivityPenaltyTimer.vk_bot_connection_id == connection_id)
            .where(VkActivityPenaltyTimer.target_type == target_type)
            .where(VkActivityPenaltyTimer.target_id == target_id)
        ).first()

        duration = getattr(settings, "penalty_duration_seconds", 3600)
        expires_at = utc_now() + timedelta(seconds=duration)

        if existing_timer:
            existing_timer.expires_at = expires_at
            db.add(existing_timer)
        else:
            new_timer = VkActivityPenaltyTimer(
                vk_id=vk_user.vk_id,
                vk_bot_connection_id=connection_id,
                target_type=target_type,
                target_id=target_id,
                expires_at=expires_at
            )
            db.add(new_timer)
        db.commit()
        logger.info(f"Penalty timer triggered for user {vk_user.vk_id} on {target_type} {target_id} (expires at {expires_at})")

    async def _check_and_apply_penalty(
        self, 
        db: Session, 
        vk_user: VkUser, 
        target_type: str, 
        target_id: str, 
        settings: VkActivitySettings, 
        bot_token: str,
        action_type: str,
        item_id: str
    ) -> bool:
        """
        Проверяет наличие активного штрафного таймера.
        Если активен, начисляет penalty_points, создает запись VkActivity и отправляет штрафное уведомление.
        Возвращает True, если штраф применен, иначе False.
        """
        # Ищем активный таймер штрафа
        timer = db.exec(
            select(VkActivityPenaltyTimer)
            .where(VkActivityPenaltyTimer.vk_id == vk_user.vk_id)
            .where(VkActivityPenaltyTimer.vk_bot_connection_id == settings.vk_bot_connection_id)
            .where(VkActivityPenaltyTimer.target_type == target_type)
            .where(VkActivityPenaltyTimer.target_id == target_id)
            .where(VkActivityPenaltyTimer.expires_at > utc_now())
        ).first()

        if not timer:
            return False

        # Штраф активен!
        penalty_pts = getattr(settings, "penalty_points", 0)
        
        # Записываем активность
        activity = VkActivity(
            vk_id=vk_user.vk_id,
            action_type=action_type,
            item_id=item_id,
            points=penalty_pts,
            is_synced=False
        )
        db.add(activity)
        
        vk_user.vk_bonus_balance += penalty_pts
        db.add(vk_user)
        db.commit()

        # Отправляем текстовое уведомление о штрафном времени и баллах
        template = getattr(settings, "msg_penalty", None) or "⚠️ Вы совершили повторное действие во время действия штрафа. Начислено баллов: {points}."
        msg_text = template.replace("{points}", str(penalty_pts))
        
        await self._send_notification(vk_user.vk_id, msg_text, bot_token)
        logger.info(f"Applied penalty of {penalty_pts} points for user {vk_user.vk_id} (action {action_type} on {target_type} {target_id})")
        return True

    async def _send_notification(self, vk_id: int, message: str, bot_token: str):
        """Отправляет уведомление пользователю в ЛС"""
        # Сначала проверим, разрешил ли пользователь сообщения от сообщества
        # (Обычно если не разрешил, API вернет ошибку 901, мы ее просто перехватим)
        try:
            from app.services.vk_service import send_vk_message
            await send_vk_message(vk_id=vk_id, message=message, bot_token=bot_token)
        except Exception as e:
            logger.debug(f"Could not send VK notification to user {vk_id}: {e}")

    async def _handle_like_add(self, db: Session, vk_user: VkUser, obj: Dict[str, Any], settings: VkActivitySettings, bot_token: str, group_id: int):
        post_id = obj.get("object_id")
        object_type = obj.get("object_type")
        if object_type != "post" or not post_id:
            return  # Считаем баллы только за лайки постов на стене

        if is_post_ignored(post_id, settings):
            logger.info(f"Like ignored: post {post_id} is in the ignored list")
            return

        item_id = f"like_{post_id}"
        
        # Проверяем на дубли
        existing = db.exec(
            select(VkActivity)
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "like_add")
            .where(VkActivity.item_id == item_id)
        ).first()
        if existing:
            return

        # Проверка и применение штрафа
        if await self._check_and_apply_penalty(
            db=db, 
            vk_user=vk_user, 
            target_type="post", 
            target_id=str(post_id), 
            settings=settings, 
            bot_token=bot_token,
            action_type="like_add",
            item_id=item_id
        ):
            return

        # Получаем информацию о посте (дату и текст)
        post_info = await get_post_info(post_id, -group_id, bot_token)
        post_date_ts = post_info.get("date") if post_info else None

        # 1. Проверяем, что пост опубликован ПОСЛЕ начала конкурса
        if post_date_ts and settings.period_start_date:
            post_dt = datetime.fromtimestamp(post_date_ts, tz=timezone.utc)
            start_dt = settings.period_start_date.replace(tzinfo=timezone.utc) if settings.period_start_date.tzinfo is None else settings.period_start_date
            if post_dt < start_dt:
                logger.info(f"Like ignored: post {post_id} published before contest start date")
                return

        # 2. Проверяем срок давности постов и ключевые слова-исключения
        if not is_post_eligible_by_age_and_keywords(post_info, settings, utc_now()):
            return

        points = settings.points_like
        reasons = []

        if post_date_ts:
            current_ts = int(utc_now().timestamp())
            # 1. Быстрый лайк
            if current_ts - post_date_ts < settings.like_fast_seconds:
                points = settings.points_like_fast
                reasons.append("быстрый лайк")
            
            # 2. В числе первых N лайкнувших
            likes_res = await call_vk_api(
                "likes.getList", 
                {"type": "post", "owner_id": f"-{group_id}", "item_id": str(post_id), "count": str(settings.like_first_n_count)}, 
                bot_token
            )
            if likes_res and "items" in likes_res:
                if vk_user.vk_id in likes_res["items"]:
                    points = max(points, settings.points_like_first_n)
                    reasons.append("в числе первых")

        # Создаем активность
        activity = VkActivity(
            vk_id=vk_user.vk_id,
            action_type="like_add",
            item_id=item_id,
            points=points,
            is_synced=False
        )
        db.add(activity)
        
        vk_user.vk_bonus_balance += points
        db.add(vk_user)
        db.commit()

        reason_str = f" ({', '.join(reasons)})" if reasons else ""
        template = getattr(settings, "msg_points_like", None) or "❤️ Вам начислено {points} баллов за лайк к посту{reason}! Ваш баланс активности: {balance} баллов."
        msg_text = template.replace("{points}", str(points)).replace("{reason}", reason_str).replace("{balance}", str(vk_user.vk_bonus_balance))
        
        await self._send_notification(vk_user.vk_id, msg_text, bot_token)
        
        # Авто-синхронизация отключена по требованию (делается вручную или через бота)
        # if settings.sync_with_iiko and getattr(settings, "iiko_sync_mode", "realtime") == "realtime":
        #     await self.sync_vk_user_points_to_iiko(db, vk_user, settings)

    async def _handle_like_remove(self, db: Session, vk_user: VkUser, obj: Dict[str, Any], settings: VkActivitySettings, bot_token: str):
        post_id = obj.get("object_id")
        object_type = obj.get("object_type")
        if object_type != "post" or not post_id:
            return

        item_id = f"like_{post_id}"
        
        # Ищем начисление
        existing = db.exec(
            select(VkActivity)
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "like_add")
            .where(VkActivity.item_id == item_id)
        ).first()
        
        if not existing:
            return

        points_to_remove = existing.points
        
        # Удаляем запись об активности
        db.delete(existing)
        
        # Вычитаем баллы (баланс не ниже 0)
        old_balance = vk_user.vk_bonus_balance
        vk_user.vk_bonus_balance = max(0, vk_user.vk_bonus_balance - points_to_remove)
        db.add(vk_user)
        db.commit()

        # Запускаем штрафной таймер
        self._trigger_penalty_timer(db, vk_user, "post", str(post_id), settings, settings.vk_bot_connection_id)

        # Авто-синхронизация отключена по требованию (делается вручную или через бота)
        # if settings.sync_with_iiko and getattr(settings, "iiko_sync_mode", "realtime") == "realtime":
        #     await self.sync_vk_user_points_to_iiko(db, vk_user, settings)

        await self._send_notification(
            vk_user.vk_id, 
            f"💔 Вы убрали лайк. Снято {points_to_remove} баллов. Ваш баланс активности: {vk_user.vk_bonus_balance} баллов.", 
            bot_token
        )

    async def _handle_comment_add(self, db: Session, vk_user: VkUser, obj: Dict[str, Any], settings: VkActivitySettings, bot_token: str, group_id: int):
        post_id = obj.get("post_id")
        comment_id = obj.get("id")
        text_content = obj.get("text", "").strip()
        
        if not post_id or not comment_id:
            return

        if is_post_ignored(post_id, settings):
            logger.info(f"Comment ignored: post {post_id} is in the ignored list")
            return

        item_id = f"comment_{comment_id}"

        # 1. Проверяем на дубли
        existing = db.exec(
            select(VkActivity)
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "wall_reply_new")
            .where(VkActivity.item_id == item_id)
        ).first()
        if existing:
            return

        # Проверка и применение штрафа
        if await self._check_and_apply_penalty(
            db=db, 
            vk_user=vk_user, 
            target_type="post", 
            target_id=str(post_id), 
            settings=settings, 
            bot_token=bot_token,
            action_type="wall_reply_new",
            item_id=f"comment_{post_id}_{comment_id}" # используем новый формат
        ):
            return

        # Получаем информацию о посте (дату и текст)
        post_info = await get_post_info(post_id, -group_id, bot_token)
        post_date_ts = post_info.get("date") if post_info else None

        # Проверяем, что пост опубликован ПОСЛЕ начала конкурса
        if post_date_ts and settings.period_start_date:
            post_dt = datetime.fromtimestamp(post_date_ts, tz=timezone.utc)
            start_dt = settings.period_start_date.replace(tzinfo=timezone.utc) if settings.period_start_date.tzinfo is None else settings.period_start_date
            if post_dt < start_dt:
                logger.info(f"Comment ignored: post {post_id} published before contest start date")
                return

        # Проверяем срок давности постов и ключевые слова-исключения
        if not is_post_eligible_by_age_and_keywords(post_info, settings, utc_now()):
            return

        # 2. Валидация спама: минимальная длина
        if len(text_content) < settings.min_comment_length:
            logger.info(f"Comment ignored: length {len(text_content)} is shorter than min {settings.min_comment_length}")
            return

        # 3. Валидация спама: стикеры
        attachments = obj.get("attachments", [])
        if settings.ignore_stickers:
            has_sticker = any(att.get("type") == "sticker" for att in attachments)
            if has_sticker or (not text_content and len(attachments) == 0):
                logger.info("Comment ignored: contains sticker or no text")
                return

        # 4. Валидация спама: лимит комментариев под постом
        # Считаем, сколько начислили баллов этому пользователю под этим постом
        # item_id для комментариев имеет формат comment_{comment_id}, поэтому мы ищем по маске или по связке с post_id
        # Для этого мы можем сделать запрос к БД:
        comments_count = db.exec(
            select(func.count(VkActivity.id))
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "wall_reply_new")
            .where(VkActivity.item_id.like("comment_%"))
        ).one() or 0
        
        # Чтобы точно отфильтровать по посту, мы можем выгрузить все комментарии пользователя и проверить их привязку к посту через API,
        # либо мы можем сохранять post_id в дополнительное поле. Но так как у нас в модели VkActivity нет поля post_id (только item_id),
        # мы можем кодировать item_id как f"comment_{post_id}_{comment_id}".
        # Это гениально! Давайте перекодируем item_id в comment_postID_commentID.
        # Для обратной совместимости будем поддерживать оба формата.
        post_item_prefix = f"comment_{post_id}_"
        comments_under_this_post = db.exec(
            select(func.count(VkActivity.id))
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "wall_reply_new")
            .where(VkActivity.item_id.like(f"{post_item_prefix}%"))
        ).one() or 0

        if comments_under_this_post >= settings.max_comments_per_post:
            logger.info(f"Comment ignored: user {vk_user.vk_id} exceeded max comments {settings.max_comments_per_post} for post {post_id}")
            return

        # 5. Валидация спама: идущие подряд комментарии
        if settings.ignore_consecutive_comments:
            # Получаем последнюю активность по комментариям под этим постом в БД
            last_activity = db.exec(
                select(VkActivity)
                .where(VkActivity.action_type == "wall_reply_new")
                .where(VkActivity.item_id.like(f"{post_item_prefix}%"))
                .order_by(VkActivity.created_at.desc())
                .limit(1)
            ).first()
            if last_activity and last_activity.vk_id == vk_user.vk_id:
                logger.info(f"Comment ignored: user {vk_user.vk_id} commented consecutively")
                return

        # Рассчитываем баллы
        points = settings.points_comment
        reasons = []

        if post_date_ts:
            current_ts = int(utc_now().timestamp())
            # Быстрый комментарий
            if current_ts - post_date_ts < settings.comment_fast_seconds:
                points = settings.points_comment_fast
                reasons.append("быстрый комментарий")

            # В числе первых N комментаторов
            # Запросим список комментариев к посту через API
            comments_res = await call_vk_api(
                "wall.getComments", 
                {"owner_id": f"-{group_id}", "post_id": str(post_id), "count": str(settings.comment_first_n_count), "sort": "asc"}, 
                bot_token
            )
            if comments_res and "items" in comments_res:
                first_commenters = [c.get("from_id") for c in comments_res["items"] if c.get("from_id")]
                if vk_user.vk_id in first_commenters:
                    points = max(points, settings.points_comment_first_n)
                    reasons.append("в числе первых")

        # Создаем активность с новым форматом item_id
        activity = VkActivity(
            vk_id=vk_user.vk_id,
            action_type="wall_reply_new",
            item_id=f"comment_{post_id}_{comment_id}",
            points=points,
            is_synced=False
        )
        db.add(activity)
        
        vk_user.vk_bonus_balance += points
        db.add(vk_user)
        db.commit()

        reason_str = f" ({', '.join(reasons)})" if reasons else ""
        template = getattr(settings, "msg_points_comment", None) or "💬 Вам начислено {points} баллов за комментарий к посту{reason}! Ваш баланс активности: {balance} баллов."
        msg_text = template.replace("{points}", str(points)).replace("{reason}", reason_str).replace("{balance}", str(vk_user.vk_bonus_balance))
        
        await self._send_notification(vk_user.vk_id, msg_text, bot_token)
        
        # if settings.sync_with_iiko and getattr(settings, "iiko_sync_mode", "realtime") == "realtime":
        #     await self.sync_vk_user_points_to_iiko(db, vk_user, settings)

    async def _handle_comment_delete(self, db: Session, vk_user: VkUser, obj: Dict[str, Any], settings: VkActivitySettings, bot_token: str):
        comment_id = obj.get("id")
        post_id = obj.get("post_id")
        if not comment_id:
            return

        # Ищем по обоим форматам item_id
        existing = db.exec(
            select(VkActivity)
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "wall_reply_new")
            .where((VkActivity.item_id == f"comment_{post_id}_{comment_id}") | (VkActivity.item_id == f"comment_{post_id}_{comment_id}"))
        ).first()

        if not existing:
            return

        points_to_remove = existing.points
        db.delete(existing)
        
        old_balance = vk_user.vk_bonus_balance
        vk_user.vk_bonus_balance = max(0, vk_user.vk_bonus_balance - points_to_remove)
        db.add(vk_user)
        db.commit()

        # Попытка вытащить post_id из item_id, если его нет в ответе
        final_post_id = post_id
        if not final_post_id and existing.item_id:
            parts = existing.item_id.split("_")
            if len(parts) == 3:
                final_post_id = parts[1]
        
        if final_post_id:
            self._trigger_penalty_timer(db, vk_user, "post", str(final_post_id), settings, settings.vk_bot_connection_id)

        # if settings.sync_with_iiko and getattr(settings, "iiko_sync_mode", "realtime") == "realtime":
        #     await self.sync_vk_user_points_to_iiko(db, vk_user, settings)

        await self._send_notification(
            vk_user.vk_id, 
            f"🗑 Вы удалили комментарий. Снято {points_to_remove} баллов. Ваш баланс активности: {vk_user.vk_bonus_balance} баллов.", 
            bot_token
        )

    async def _handle_repost_add(self, db: Session, vk_user: VkUser, obj: Dict[str, Any], settings: VkActivitySettings, bot_token: str, group_id: int):
        # wall_repost Callback-событие содержит объект записи на стене пользователя
        # У репоста есть id и copy_history, где первый элемент - оригинальный пост
        copy_history = obj.get("copy_history", [])
        if not copy_history:
            return
            
        orig_post = copy_history[0]
        orig_post_id = orig_post.get("id")
        orig_owner_id = orig_post.get("owner_id")
        
        # Проверяем, что репост сделан именно из нашей группы
        if orig_owner_id != -group_id:
            return

        if is_post_ignored(orig_post_id, settings):
            logger.info(f"Repost ignored: post {orig_post_id} is in the ignored list")
            return

        item_id = f"repost_{orig_post_id}"

        # Проверяем на дубли
        existing = db.exec(
            select(VkActivity)
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "wall_repost")
            .where(VkActivity.item_id == item_id)
        ).first()
        if existing:
            return

        # Проверка и применение штрафа
        if await self._check_and_apply_penalty(
            db=db, 
            vk_user=vk_user, 
            target_type="post", 
            target_id=str(orig_post_id), 
            settings=settings, 
            bot_token=bot_token,
            action_type="wall_repost",
            item_id=item_id
        ):
            return

        # Получаем информацию о посте (дату и текст)
        post_info = await get_post_info(orig_post_id, -group_id, bot_token)
        if not post_info:
            post_info = {"date": orig_post.get("date"), "text": orig_post.get("text", "")}

        post_date_ts = post_info.get("date")
        if post_date_ts and settings.period_start_date:
            post_dt = datetime.fromtimestamp(post_date_ts, tz=timezone.utc)
            start_dt = settings.period_start_date.replace(tzinfo=timezone.utc) if settings.period_start_date.tzinfo is None else settings.period_start_date
            if post_dt < start_dt:
                logger.info(f"Repost ignored: original post {orig_post_id} published before contest start date")
                return

        # Проверяем срок давности постов и ключевые слова-исключения
        if not is_post_eligible_by_age_and_keywords(post_info, settings, utc_now()):
            return

        points = settings.points_repost

        activity = VkActivity(
            vk_id=vk_user.vk_id,
            action_type="wall_repost",
            item_id=item_id,
            points=points,
            is_synced=False
        )
        db.add(activity)
        
        vk_user.vk_bonus_balance += points
        db.add(vk_user)
        db.commit()

        template = getattr(settings, "msg_points_repost", None) or "📢 Вам начислено {points} баллов за репост нашей записи! Ваш баланс активности: {balance} баллов."
        msg_text = template.replace("{points}", str(points)).replace("{balance}", str(vk_user.vk_bonus_balance))
        
        await self._send_notification(vk_user.vk_id, msg_text, bot_token)
        
        # if settings.sync_with_iiko and getattr(settings, "iiko_sync_mode", "realtime") == "realtime":
        #     await self.sync_vk_user_points_to_iiko(db, vk_user, settings)

    async def _handle_poll_vote_add(self, db: Session, vk_user: VkUser, obj: Dict[str, Any], settings: VkActivitySettings, bot_token: str, group_id: int):
        poll_id = obj.get("poll_id")
        option_id = obj.get("option_id")
        if not poll_id:
            return

        item_id = f"poll_{poll_id}"

        # Проверяем на дубли (голос в этом опросе)
        existing = db.exec(
            select(VkActivity)
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "poll_vote_new")
            .where(VkActivity.item_id == item_id)
        ).first()
        if existing:
            return

        points = settings.points_poll

        activity = VkActivity(
            vk_id=vk_user.vk_id,
            action_type="poll_vote_new",
            item_id=item_id,
            points=points,
            is_synced=False
        )
        db.add(activity)
        
        vk_user.vk_bonus_balance += points
        db.add(vk_user)
        db.commit()

        template = getattr(settings, "msg_points_poll", None) or "📊 Вам начислено {points} баллов за участие в нашем опросе! Ваш баланс активности: {balance} баллов."
        msg_text = template.replace("{points}", str(points)).replace("{balance}", str(vk_user.vk_bonus_balance))
        
        await self._send_notification(vk_user.vk_id, msg_text, bot_token)
        
        # if settings.sync_with_iiko and getattr(settings, "iiko_sync_mode", "realtime") == "realtime":
        #     await self.sync_vk_user_points_to_iiko(db, vk_user, settings)

    async def _handle_group_join(self, db: Session, vk_user: VkUser, obj: Dict[str, Any], settings: VkActivitySettings, bot_token: str, group_id: int):
        item_id = f"join_{group_id}"

        # Проверяем, вступал ли ранее (чтобы не накручивали выход-вход)
        existing = db.exec(
            select(VkActivity)
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "group_join")
            .where(VkActivity.item_id == item_id)
        ).first()
        if existing:
            return

        # Проверка и применение штрафа
        if await self._check_and_apply_penalty(
            db=db, 
            vk_user=vk_user, 
            target_type="group", 
            target_id="group", 
            settings=settings, 
            bot_token=bot_token,
            action_type="group_join",
            item_id=item_id
        ):
            return

        points = settings.points_join

        activity = VkActivity(
            vk_id=vk_user.vk_id,
            action_type="group_join",
            item_id=item_id,
            points=points,
            is_synced=False
        )
        db.add(activity)
        
        vk_user.vk_bonus_balance += points
        db.add(vk_user)
        db.commit()

        template = getattr(settings, "msg_points_join", None) or "🤝 Добро пожаловать в наше сообщество! Вам начислено приветственных {points} баллов активности! Ваш баланс: {balance} баллов."
        msg_text = template.replace("{points}", str(points)).replace("{balance}", str(vk_user.vk_bonus_balance))
        
        await self._send_notification(vk_user.vk_id, msg_text, bot_token)
        
        # if settings.sync_with_iiko and getattr(settings, "iiko_sync_mode", "realtime") == "realtime":
        #     await self.sync_vk_user_points_to_iiko(db, vk_user, settings)

    async def _handle_group_leave(self, db: Session, vk_user: VkUser, obj: Dict[str, Any], settings: VkActivitySettings, bot_token: str):
        # group_leave присылает событие при выходе
        # Списываем баллы за вступление
        group_id = obj.get("group_id")
        item_id = f"join_{group_id}"

        existing = db.exec(
            select(VkActivity)
            .where(VkActivity.vk_id == vk_user.vk_id)
            .where(VkActivity.action_type == "group_join")
            .where(VkActivity.item_id == item_id)
        ).first()
        
        if not existing:
            return

        points_to_remove = existing.points
        db.delete(existing)
        
        old_balance = vk_user.vk_bonus_balance
        vk_user.vk_bonus_balance = max(0, vk_user.vk_bonus_balance - points_to_remove)
        db.add(vk_user)
        db.commit()

        # Запускаем штрафной таймер на группу
        self._trigger_penalty_timer(db, vk_user, "group", "group", settings, settings.vk_bot_connection_id)

        # if settings.sync_with_iiko and getattr(settings, "iiko_sync_mode", "realtime") == "realtime":
        #     await self.sync_vk_user_points_to_iiko(db, vk_user, settings)

        # Сообщение не шлем, так как пользователь вышел из группы и сообщения могут быть заблокированы API

    async def sync_vk_user_points_to_iiko(self, db: Session, vk_user: VkUser, settings: VkActivitySettings, error_details: Optional[dict] = None) -> bool:
        """
        Интеграция с iikoCard: синхронизирует баллы активности ВК с iikoCard
        на основе разницы (дельты) между текущим балансом vk_bonus_balance
        и уже синхронизированным балансом vk_bonus_balance_synced.
        """
        if not vk_user.is_linked or not vk_user.phone:
            if error_details is not None:
                error_details["message"] = "Профиль не привязан к телефону"
            return False

        # Находим клиента в нашей БД
        customer = db.exec(select(Customer).where(Customer.phone == vk_user.phone)).first()
        if not customer or not customer.iiko_customer_id:
            if error_details is not None:
                error_details["message"] = "Карта гостя не найдена в базе данных"
            return False

        if vk_user.vk_bonus_balance_synced is None:
            vk_user.vk_bonus_balance_synced = 0

        # Вычисляем разницу (дельту)
        diff_points = vk_user.vk_bonus_balance - vk_user.vk_bonus_balance_synced
        if diff_points == 0:
            return True

        # Вычисляем сумму бонуса iiko на основе курса конвертации
        bonus_value = round(diff_points * settings.iiko_conversion_rate, 2)
        if bonus_value == 0:
            # Если разница слишком мала для изменения, не шлем запросы
            return True

        try:
            from app.services.iiko_service import iiko_service
            logger.info(f"Auto-syncing {bonus_value} bonuses to iiko for Customer {customer.phone} (VK: {vk_user.vk_id}, diff: {diff_points})")
            
            await iiko_service.add_customer_bonuses(
                customer.iiko_customer_id, 
                bonus_value, 
                f"Синхронизация баллов активности ВК ({vk_user.vk_id})"
            )
            
            # Обновляем синхронизированный баланс
            vk_user.vk_bonus_balance_synced = vk_user.vk_bonus_balance
            db.add(vk_user)
            db.commit()
            return True
        except Exception as e:
            err_msg = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    err_msg += " " + e.response.text
                except:
                    pass
            
            if "Customer_CustomerIsDeleted" in err_msg or "is deleted" in err_msg:
                msg = "Гость удален в iiko"
            elif "Wallet with id" in err_msg or "Wallet" in err_msg:
                msg = "Кошелек не найден в iiko"
            else:
                msg = f"Ошибка API iiko: {err_msg[:60]}"
                
            logger.error(f"Failed to sync bonuses to iikoCard for customer {customer.phone}: {e}")
            if error_details is not None:
                error_details["message"] = msg
            return False

    async def run_manual_iiko_sync(self, db: Session, connection_id: int) -> Dict[str, Any]:
        """Запускает полную ручную синхронизацию баллов активности с iikoCard для связанных пользователей"""
        settings = db.exec(select(VkActivitySettings).where(VkActivitySettings.vk_bot_connection_id == connection_id)).first()
        if not settings:
            return {"status": "error", "message": "Настройки активности для этого подключения не найдены"}

        # Находим всех связанных пользователей VK
        vk_users = db.exec(select(VkUser).where(VkUser.is_linked == True)).all()
        synced_count = 0
        total_bonuses_synced = 0.0
        failed_details = []

        for vk_user in vk_users:
            if vk_user.vk_bonus_balance_synced is None:
                vk_user.vk_bonus_balance_synced = 0

            diff_points = vk_user.vk_bonus_balance - vk_user.vk_bonus_balance_synced
            if diff_points == 0:
                continue

            err_det = {}
            success = await self.sync_vk_user_points_to_iiko(db, vk_user, settings, error_details=err_det)
            if success:
                # Помечаем активности как синхронизированные
                unsynced_activities = db.exec(
                    select(VkActivity)
                    .where(VkActivity.vk_id == vk_user.vk_id)
                    .where(VkActivity.is_synced == False)
                ).all()
                for act in unsynced_activities:
                    act.is_synced = True
                    db.add(act)
                synced_count += 1
                total_bonuses_synced += diff_points * settings.iiko_conversion_rate
            else:
                user_name = f"{vk_user.first_name or ''} {vk_user.last_name or ''}".strip() or f"ID {vk_user.vk_id}"
                reason = err_det.get("message", "Неизвестная ошибка")
                failed_details.append(f"{user_name} ({vk_user.phone}): {reason}")

        if synced_count > 0:
            settings.last_sync_at = utc_now()
            db.add(settings)
            db.commit()

        msg = f"Синхронизация завершена. Успешно синхронизировано пользователей: {synced_count}."
        if failed_details:
            msg += "\n\nНекоторые пользователи пропущены из-за ошибок данных в iiko:\n" + "\n".join([f"• {fd}" for fd in failed_details])

        return {
            "status": "success",
            "message": msg,
            "synced_users": synced_count,
            "failed_users": len(failed_details),
            "total_bonuses": total_bonuses_synced
        }

vk_activity_service = VkActivityService()
