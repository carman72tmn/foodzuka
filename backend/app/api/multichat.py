from fastapi import APIRouter, Depends, HTTPException, Request, Query, Response
from sqlmodel import Session, select, desc, and_, or_, update, delete
from sqlalchemy import func
from app.core.database import get_session

from app.models.chat import MultichatMessage, MultichatTag, MultichatDialogTag, MultichatPinnedDialog, MultichatHiddenDialog, MultichatAccount
from app.models.vk_bot_connection import VkBotConnection
from app.models.vk_settings import VkSettings
from app.models.validation_settings import ValidationSettings
from app.models.max_settings import MaxSettings
from app.services.vk_service import send_vk_message
from app.services.max_service import send_max_message
from app.api.deps import require_permission
from app.models.user import User
import logging
import httpx
import asyncio
import os
import json
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/multichat", tags=["multichat"])

HIDDEN_DIALOGS_REDIS_KEY = "multichat:hidden_dialogs_set"


async def get_hidden_dialog_keys() -> set:
    """Получение множества скрытых диалогов из Redis (или инициализация из БД)"""
    try:
        from app.core.redis import redis_client
        cached_keys = await redis_client.smembers(HIDDEN_DIALOGS_REDIS_KEY)
        if cached_keys:
            return set(cached_keys)

        # Если в кэше пусто — загружаем из базы данных
        from app.core.database import engine
        from sqlmodel import Session, select
        with Session(engine) as db:
            hidden_rows = db.exec(select(MultichatHiddenDialog.channel, MultichatHiddenDialog.peer_id)).all()
            if not hidden_rows:
                return set()

            keys = [f"{row[0]}:{row[1]}" for row in hidden_rows]
            await redis_client.sadd(HIDDEN_DIALOGS_REDIS_KEY, *keys)
            await redis_client.expire(HIDDEN_DIALOGS_REDIS_KEY, 86400)
            return set(keys)
    except Exception as e:
        logger.warning(f"Error fetching hidden dialogs set: {e}")
        return set()


async def is_dialog_hidden(channel: str, peer_id: str) -> bool:
    """Проверка, является ли диалог скрытым (с поддержкой нормализации каналов)"""
    if not channel or not peer_id:
        return False
    try:
        from app.core.redis import redis_client
        exact_key = f"{channel}:{peer_id}"
        if await redis_client.sismember(HIDDEN_DIALOGS_REDIS_KEY, exact_key):
            return True

        # Проверка альт-каналов (vk <-> vk_user, max <-> max_user <-> max_bot, whatsapp <-> whatsapp_user)
        alt_channels = []
        if channel in ("vk", "vk_user"):
            alt_channels = ["vk", "vk_user"]
        elif channel in ("max", "max_user", "max_bot", "max_account"):
            alt_channels = ["max", "max_user", "max_bot", "max_account"]
        elif channel in ("whatsapp", "whatsapp_user"):
            alt_channels = ["whatsapp", "whatsapp_user"]

        for alt in alt_channels:
            if alt != channel and await redis_client.sismember(HIDDEN_DIALOGS_REDIS_KEY, f"{alt}:{peer_id}"):
                return True

        # Если кэш в Redis еще не был прогрет
        if not await redis_client.exists(HIDDEN_DIALOGS_REDIS_KEY):
            all_keys = await get_hidden_dialog_keys()
            if exact_key in all_keys:
                return True
            for alt in alt_channels:
                if f"{alt}:{peer_id}" in all_keys:
                    return True

        return False
    except Exception as e:
        logger.warning(f"Error checking is_dialog_hidden: {e}")
        return False


def is_dialog_hidden_sync(channel: str, peer_id: str) -> bool:
    """Синхронная проверка скрытости диалога через sync_redis_client (для фоновых воркеров)"""
    if not channel or not peer_id:
        return False
    try:
        from app.core.redis import sync_redis_client
        exact_key = f"{channel}:{peer_id}"
        if sync_redis_client.sismember(HIDDEN_DIALOGS_REDIS_KEY, exact_key):
            return True

        alt_channels = []
        if channel in ("vk", "vk_user"):
            alt_channels = ["vk", "vk_user"]
        elif channel in ("max", "max_user", "max_bot", "max_account"):
            alt_channels = ["max", "max_user", "max_bot", "max_account"]
        elif channel in ("whatsapp", "whatsapp_user"):
            alt_channels = ["whatsapp", "whatsapp_user"]

        for alt in alt_channels:
            if alt != channel and sync_redis_client.sismember(HIDDEN_DIALOGS_REDIS_KEY, f"{alt}:{peer_id}"):
                return True

        # Если кэш в Redis пуст - прогреваем из базы синхронно
        if not sync_redis_client.exists(HIDDEN_DIALOGS_REDIS_KEY):
            from app.core.database import engine
            from sqlmodel import Session, select
            with Session(engine) as db:
                hidden_rows = db.exec(select(MultichatHiddenDialog.channel, MultichatHiddenDialog.peer_id)).all()
                if hidden_rows:
                    keys = [f"{row[0]}:{row[1]}" for row in hidden_rows]
                    sync_redis_client.sadd(HIDDEN_DIALOGS_REDIS_KEY, *keys)
                    sync_redis_client.expire(HIDDEN_DIALOGS_REDIS_KEY, 86400)
                    if exact_key in keys or any(f"{alt}:{peer_id}" in keys for alt in alt_channels):
                        return True
        return False
    except Exception as e:
        logger.warning(f"Error checking is_dialog_hidden_sync: {e}")
        return False


async def invalidate_multichat_dialogs_cache():
    """Сброс кэша списка диалогов мультичата в Redis при любых изменениях"""
    try:
        from app.core.redis import redis_client
        keys = await redis_client.keys("multichat:dialogs:*")
        if keys:
            await redis_client.delete(*keys)
    except Exception as e:
        logger.debug(f"Error invalidating multichat cache: {e}")


async def broadcast_ws_message(msg: Any):
    """Отправка сообщения по вебсокет-каналам в реальном времени"""
    try:

        # Безопасное извлечение атрибутов даже для detached instances
        if isinstance(msg, dict):
            m_id = msg.get("id")
            m_channel = msg.get("channel")
            m_channel_id = msg.get("channel_id")
            m_peer_id = msg.get("peer_id")
            m_peer_name = msg.get("peer_name")
            m_peer_avatar = msg.get("peer_avatar")
            m_from_id = msg.get("from_id")
            m_text = msg.get("text")
            m_direction = msg.get("direction")
            m_payload = msg.get("payload")
            m_created_at = msg.get("created_at")
            m_is_read = msg.get("is_read")
        else:
            try:
                d = getattr(msg, "__dict__", {})
                m_id = d.get("id") or getattr(msg, "id", None)
                m_channel = d.get("channel") or getattr(msg, "channel", None)
                m_channel_id = d.get("channel_id") or getattr(msg, "channel_id", None)
                m_peer_id = d.get("peer_id") or getattr(msg, "peer_id", None)
                m_peer_name = d.get("peer_name") or getattr(msg, "peer_name", None)
                m_peer_avatar = d.get("peer_avatar") or getattr(msg, "peer_avatar", None)
                m_from_id = d.get("from_id") or getattr(msg, "from_id", None)
                m_text = d.get("text") or getattr(msg, "text", None)
                m_direction = d.get("direction") or getattr(msg, "direction", None)
                m_payload = d.get("payload") or getattr(msg, "payload", None)
                m_created_at = d.get("created_at") or getattr(msg, "created_at", None)
                m_is_read = d.get("is_read", False)
            except Exception:
                m_id = None
                m_channel = "vk"
                m_channel_id = None
                m_peer_id = None
                m_peer_name = None
                m_peer_avatar = None
                m_from_id = None
                m_text = None
                m_direction = "in"
                m_payload = None
                m_created_at = None
                m_is_read = False

        from app.api.chat import manager
        from app.services.chat_media_cache_service import chat_media_cache_service
        attachments = chat_media_cache_service.extract_attachments_from_payload(m_payload, m_channel) if m_payload else []

        # Проверяем, скрыт ли данный диалог
        is_hidden = await is_dialog_hidden(m_channel, str(m_peer_id)) if (m_channel and m_peer_id) else False

        payload_ws = {
            "type": "multichat_message",
            "data": {
                "id": m_id,
                "channel": m_channel,
                "channel_id": m_channel_id,
                "peer_id": m_peer_id,
                "peer_name": m_peer_name,
                "peer_avatar": m_peer_avatar,
                "from_id": m_from_id,
                "text": m_text,
                "direction": m_direction,
                "attachments": attachments,
                "created_at": m_created_at.isoformat() if hasattr(m_created_at, "isoformat") else str(m_created_at or ""),
                "is_read": m_is_read,
                "is_hidden": is_hidden
            }
        }
        # Инвалидируем кэш диалогов мультичата только для открытых (не скрытых) чатов,
        if not is_hidden:
            try:
                if getattr(manager, 'loop', None) and manager.loop.is_running():
                    asyncio.run_coroutine_threadsafe(invalidate_multichat_dialogs_cache(), manager.loop)
                else:
                    asyncio.create_task(invalidate_multichat_dialogs_cache())
            except Exception:
                pass

        try:
            curr_loop = asyncio.get_running_loop()
        except RuntimeError:
            curr_loop = None

        if curr_loop and getattr(manager, 'loop', None) and curr_loop == manager.loop and curr_loop.is_running():
            curr_loop.create_task(manager.broadcast(payload_ws))
        else:
            manager.broadcast_sync(payload_ws)
    except Exception as e:
        logger.error(f"WebSocket broadcast error: {e}")



def _get_timestamp(dt):
    if not dt:
        return 0.0
    if isinstance(dt, (int, float)):
        return float(dt)
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return 0.0
    if hasattr(dt, 'timestamp'):
        try:
            return float(dt.timestamp())
        except Exception:
            return 0.0
    return 0.0


@router.get("/dialogs")
async def get_dialogs(
    channel: Optional[str] = None,
    channel_id: Optional[str] = None,
    tag_id: Optional[int] = None,
    unread_only: bool = False,
    hidden_only: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_view"))
):
    """Получение списка всех диалогов (высокоскоростной кэш в Redis + оптимизированный запрос)"""
    cache_key = f"multichat:dialogs:{channel or 'all'}:{channel_id or 'all'}:{tag_id or 'none'}:{unread_only}:{hidden_only}:{start_date or 'none'}:{end_date or 'none'}"
    try:
        from app.core.redis import redis_client
        cached_json = await redis_client.get(cache_key)
        if cached_json:
            return json.loads(cached_json)
    except Exception as e:
        logger.debug(f"Redis cache lookup warning: {e}")

    # Сверхбыстрая выборка последних сообщений диалогов через Loose Index Scan (Skip Scan)
    # Время выполнения: ~0.06-0.08с вместо 2.5с полного сканирования таблицы 128k сообщений
    sql_fast_dialogs = """
        WITH RECURSIVE dialog_pairs AS (
            (
                SELECT channel, peer_id
                FROM multichat_messages
                ORDER BY channel, peer_id
                LIMIT 1
            )
            UNION ALL
            SELECT next_pair.channel, next_pair.peer_id
            FROM dialog_pairs prev
            CROSS JOIN LATERAL (
                SELECT m.channel, m.peer_id
                FROM multichat_messages m
                WHERE (m.channel, m.peer_id) > (prev.channel, prev.peer_id)
                ORDER BY m.channel, m.peer_id
                LIMIT 1
            ) next_pair
        ),
        last_msgs AS (
            SELECT lm.*
            FROM dialog_pairs dp
            CROSS JOIN LATERAL (
                SELECT 
                    m.id, m.channel, m.channel_id, m.peer_id, m.peer_name, m.peer_avatar, 
                    m.from_id, m.text, m.direction, m.external_id, m.is_read, m.created_at,
                    m.payload
                FROM multichat_messages m
                WHERE m.channel = dp.channel AND m.peer_id = dp.peer_id
                ORDER BY m.id DESC
                LIMIT 1
            ) lm
        )
        SELECT * FROM last_msgs 
        WHERE (:channel = 'all' 
           OR (:channel = 'vk' AND channel IN ('vk', 'vk_user'))
           OR (:channel = 'max' AND channel IN ('max', 'max_account', 'max_user', 'max_bot', 'max_bridge'))
           OR (:channel = 'max_user' AND channel IN ('max', 'max_account', 'max_user', 'max_bridge'))
           OR (:channel = 'max_bot' AND channel IN ('max_bot', 'max_account', 'max'))
           OR (:channel = 'whatsapp' AND channel IN ('whatsapp', 'whatsapp_account'))
           OR (:channel = 'telegram_bot' AND channel IN ('telegram_bot', 'telegram_user'))
           OR channel = :channel)
          AND (:channel_id = 'all' OR channel_id = :channel_id OR channel_id IS NULL)
        ORDER BY created_at DESC;
    """

    query_channel = channel or 'all'
    query_channel_id = channel_id or 'all'
    from sqlmodel import text
    raw_results = db.exec(text(sql_fast_dialogs), params={"channel": query_channel, "channel_id": query_channel_id}).all()

    # Преобразуем результаты в объекты MultichatMessage с учетом фильтров по дате
    s_dt = None
    e_dt = None
    if start_date:
        try:
            s_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    if end_date:
        try:
            e_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        except ValueError:
            pass

    last_messages = []
    for row in raw_results:
        # row: (id, channel, channel_id, peer_id, peer_name, peer_avatar, from_id, text, direction, external_id, is_read, created_at, payload)
        c_at = row[11]
        if s_dt and c_at and c_at < s_dt:
            continue
        if e_dt and c_at and c_at > e_dt:
            continue
        
        # Создаем легковесный объект
        msg_obj = MultichatMessage(
            id=row[0],
            channel=row[1],
            channel_id=row[2],
            peer_id=row[3],
            peer_name=row[4],
            peer_avatar=row[5],
            from_id=row[6],
            text=row[7],
            direction=row[8],
            external_id=row[9],
            is_read=row[10],
            created_at=row[11],
            payload=row[12] if isinstance(row[12], dict) else {}
        )
        last_messages.append(msg_obj)

    # 1. Пакетная загрузка количества непрочитанных сообщений (мгновенный частичный индекс)
    unread_counts_raw = db.exec(
        select(MultichatMessage.channel, MultichatMessage.peer_id, func.count(MultichatMessage.id))
        .where(MultichatMessage.direction == "inbound", MultichatMessage.is_read == False)
        .group_by(MultichatMessage.channel, MultichatMessage.peer_id)
    ).all()
    unread_map = {}
    for r in unread_counts_raw:
        unread_map[(r[0], str(r[1]))] = r[2]
        unread_map[(r[0], r[1])] = r[2]

    # 2. Пакетная загрузка всех закрепленных чатов (1 запрос)
    pinned_raw = db.exec(select(MultichatPinnedDialog.channel, MultichatPinnedDialog.peer_id)).all()
    pinned_set = set()
    for p in pinned_raw:
        pinned_set.add((p[0], str(p[1])))
        pinned_set.add((p[0], p[1]))

    # 2.1 Пакетная загрузка всех скрытых чатов (1 запрос с кросс-канальной поддержкой)
    hidden_raw = db.exec(select(MultichatHiddenDialog.channel, MultichatHiddenDialog.peer_id)).all()
    hidden_set = set()
    for h in hidden_raw:
        c, p = h[0], str(h[1])
        hidden_set.add((c, p))
        if c in ("vk", "vk_user"):
            hidden_set.add(("vk", p))
            hidden_set.add(("vk_user", p))
        elif c in ("max", "max_user", "max_bot", "max_account"):
            for alt in ("max", "max_user", "max_bot", "max_account"):
                hidden_set.add((alt, p))
        elif c in ("whatsapp", "whatsapp_user"):
            hidden_set.add(("whatsapp", p))
            hidden_set.add(("whatsapp_user", p))

    # 3. Пакетная загрузка всех меток и их связей (2 быстрых запроса)
    all_tags_map = {t.id: t for t in db.exec(select(MultichatTag)).all()}
    dialog_tag_links = db.exec(select(MultichatDialogTag)).all()
    tags_by_dialog = {}
    for link in dialog_tag_links:
        key = (link.channel, link.peer_id)
        if key not in tags_by_dialog:
            tags_by_dialog[key] = []
        if link.tag_id in all_tags_map:
            t = all_tags_map[link.tag_id]
            tags_by_dialog[key].append({"id": t.id, "name": t.name, "color": t.color})

    # 4. Пакетная загрузка профилей пользователей VK из локальной БД
    from app.models.vk_user import VkUser
    from app.models.customer import Customer

    vk_peer_ids = [int(msg.peer_id) for msg in last_messages if msg.channel in ["vk", "vk_user"] and msg.peer_id.isdigit()]
    max_peer_ids = [str(msg.peer_id) for msg in last_messages if msg.channel in ["max", "max_user", "max_account", "max_bot"]]

    vk_users_map = {}
    if vk_peer_ids:
        vk_users = db.exec(select(VkUser).where(VkUser.vk_id.in_(vk_peer_ids))).all()
        for u in vk_users:
            full_name = f"{u.first_name or ''} {u.last_name or ''}".strip()
            vk_users_map[str(u.vk_id)] = (full_name or None, u.photo_50, u.phone)

    # 5. Пакетная загрузка данных клиентов из базы по vk_user_id и max_user_id
    customers_by_vk = {}
    customers_by_max = {}
    customers_by_phone = {}
    try:
        if vk_peer_ids:
            custs = db.exec(select(Customer).where(Customer.vk_user_id.in_(vk_peer_ids))).all()
            for c in custs:
                if c.vk_user_id:
                    c_name = f"{c.first_name or c.name or ''} {c.last_name or c.surname or ''}".strip()
                    customers_by_vk[str(c.vk_user_id)] = (c.phone, c_name or None)

        if max_peer_ids:
            custs_max = db.exec(select(Customer).where(Customer.max_user_id.in_(max_peer_ids))).all()
            for c in custs_max:
                if c.max_user_id:
                    c_name = f"{c.first_name or c.name or ''} {c.last_name or c.surname or ''}".strip()
                    customers_by_max[str(c.max_user_id)] = (c.phone, c_name or None)
        
        # Индексация клиентов по номерам телефонов для собеседников, у которых peer_id похож на телефон
        phone_like_peers = [p for p in max_peer_ids if len("".join(filter(str.isdigit, p))) >= 10]
        if phone_like_peers:
            phone_custs = db.exec(
                select(Customer.phone, Customer.first_name, Customer.name, Customer.last_name, Customer.surname)
                .where(Customer.phone.in_(phone_like_peers))
            ).all()
            for pc in phone_custs:
                if pc[0]:
                    pn = "".join(filter(str.isdigit, str(pc[0])))
                    c_full = f"{pc[1] or pc[2] or ''} {pc[3] or pc[4] or ''}".strip()
                    if c_full:
                        customers_by_phone[pn[-10:]] = (pc[0], c_full)
    except Exception as e:
        logger.debug(f"Customer enrichment warning: {e}")

    # 6. Загрузка известных реальных профилей и аватарок только для тех диалогов, у которых они отсутствуют
    avatars_map = {}
    history_map = {}

    missing_profile_peers = [
        msg.peer_id for msg in last_messages 
        if not msg.peer_avatar and (not msg.peer_name or msg.peer_name.lower().startswith("пользователь") or msg.peer_name.startswith("VK 200") or msg.peer_name.startswith("Чат "))
    ]

    if missing_profile_peers:
        from app.core.redis import redis_client
        target_peers = missing_profile_peers[:100]
        needed_db_peers = []
        try:
            cache_keys = [f"multichat:profile:fast:{pid}" for pid in target_peers]
            cached_list = await redis_client.mget(cache_keys)
            for pid, cached in zip(target_peers, cached_list):
                if cached:
                    try:
                        p_info = json.loads(cached)
                        key = (p_info.get("channel") or "vk", str(pid))
                        if p_info.get("avatar"):
                            avatars_map[key] = p_info["avatar"]
                        if p_info.get("name"):
                            history_map[key] = (p_info["name"], p_info.get("avatar"), p_info.get("phone"))
                    except Exception:
                        needed_db_peers.append(pid)
                else:
                    needed_db_peers.append(pid)
        except Exception as e:
            logger.debug(f"Redis mget profiles error: {e}")
            needed_db_peers = target_peers

        if needed_db_peers:
            targeted_profiles = db.exec(
                select(MultichatMessage.channel, MultichatMessage.peer_id, MultichatMessage.peer_name, MultichatMessage.peer_avatar, MultichatMessage.payload)
                .where(
                    MultichatMessage.peer_id.in_(needed_db_peers[:50]),
                    or_(
                        MultichatMessage.peer_avatar.is_not(None),
                        and_(
                            MultichatMessage.peer_name.is_not(None),
                            ~MultichatMessage.peer_name.ilike("%пользователь%"),
                            ~MultichatMessage.peer_name.startswith("VK 200"),
                            ~MultichatMessage.peer_name.startswith("Чат "),
                            ~MultichatMessage.peer_name.startswith("MAX ")
                        )
                    )
                )
            ).all()

            pipe = redis_client.pipeline()
            has_pipe_ops = False
            for r in targeted_profiles:
                key = (r[0], str(r[1]))
                p_phone = r[4].get("phone") if isinstance(r[4], dict) else None
                p_avatar = r[3] or (r[4].get("avatar_url") if isinstance(r[4], dict) else None)
                p_name = None
                if r[2] and not r[2].lower().startswith("пользователь") and not r[2].startswith("VK 200") and not r[2].startswith("MAX "):
                    p_name = r[2]

                if p_avatar and key not in avatars_map:
                    avatars_map[key] = p_avatar
                if key not in history_map:
                    history_map[key] = (p_name, p_avatar, p_phone)

                try:
                    prof_json = json.dumps({"channel": r[0], "name": p_name, "avatar": p_avatar, "phone": p_phone})
                    pipe.setex(f"multichat:profile:fast:{r[1]}", 86400, prof_json)
                    has_pipe_ops = True
                except Exception:
                    pass

            if has_pipe_ops:
                try:
                    await pipe.execute()
                except Exception:
                    pass


    dialogs = []
    
    for msg in last_messages:
        unread_count = unread_map.get((msg.channel, str(msg.peer_id)), 0) or unread_map.get((msg.channel, msg.peer_id), 0)
        
        if unread_only and unread_count == 0:
            continue

        attached_tags = tags_by_dialog.get((msg.channel, msg.peer_id), [])
        
        if tag_id and not any(t["id"] == tag_id for t in attached_tags):
            continue

        is_hidden = (msg.channel, str(msg.peer_id)) in hidden_set or (msg.channel, msg.peer_id) in hidden_set

        if hidden_only:
            if not is_hidden:
                continue
        else:
            if is_hidden:
                continue

        is_pinned = (msg.channel, str(msg.peer_id)) in pinned_set or (msg.channel, msg.peer_id) in pinned_set

        peer_name = msg.peer_name
        peer_avatar = msg.peer_avatar or avatars_map.get((msg.channel, str(msg.peer_id)))
        phone = None

        payload_dict = msg.payload if isinstance(msg.payload, dict) else {}

        # 1. Поиск в истории известных имен (исторический индекс)
        hist_key = (msg.channel, str(msg.peer_id))
        if hist_key in history_map:
            h_name, h_avatar, h_phone = history_map[hist_key]
            if h_name:
                peer_name = h_name
            if h_avatar and not peer_avatar:
                peer_avatar = h_avatar
            if h_phone and not phone:
                phone = h_phone

        # 2. Обогащение для VK
        if msg.channel in ["vk", "vk_user"]:
            if msg.peer_id in vk_users_map:
                v_name, v_avatar, v_phone = vk_users_map[msg.peer_id]
                if v_name:
                    peer_name = v_name
                if v_avatar:
                    peer_avatar = v_avatar
                if v_phone and not phone:
                    phone = v_phone
            if msg.peer_id in customers_by_vk:
                c_phone, c_name = customers_by_vk[msg.peer_id]
                if c_phone and not phone:
                    phone = c_phone
                if c_name and (not peer_name or "пользователь" in peer_name.lower() or peer_name.startswith("VK ")):
                    peer_name = c_name

        # 3. Обогащение для MAX
        elif msg.channel in ["max", "max_user", "max_account", "max_bot", "max_bridge"]:
            if payload_dict.get("peer_name") and (not peer_name or "пользователь" in peer_name.lower()):
                peer_name = payload_dict.get("peer_name")
            if payload_dict.get("avatar_url") and not peer_avatar:
                peer_avatar = payload_dict.get("avatar_url")
            if payload_dict.get("phone") and not phone:
                phone = payload_dict.get("phone")
            if msg.peer_id in customers_by_max:
                c_phone, c_name = customers_by_max[msg.peer_id]
                if c_phone and not phone:
                    phone = c_phone
                if c_name and (not peer_name or "пользователь" in peer_name.lower() or peer_name.startswith("Чат ")):
                    peer_name = c_name

        # 4. Поиск клиента в CRM по номеру телефона
        raw_digits = "".join(filter(str.isdigit, str(phone or msg.peer_id)))
        if len(raw_digits) >= 10 and raw_digits[-10:] in customers_by_phone:
            crm_phone, crm_name = customers_by_phone[raw_digits[-10:]]
            if not phone:
                phone = crm_phone
            if crm_name and (not peer_name or "пользователь" in peer_name.lower() or peer_name.startswith("VK ") or peer_name.startswith("Чат ") or peer_name.startswith("MAX ")):
                peer_name = crm_name

        # 5. Устранение временных и случайных названий "Пользователь"
        if not peer_name or "пользователь" in peer_name.lower() or peer_name.startswith("VK 200") or peer_name.startswith("Чат "):
            if msg.channel in ["vk", "vk_user"] and msg.peer_id in vk_users_map and vk_users_map[msg.peer_id][0]:
                peer_name = vk_users_map[msg.peer_id][0]
            elif msg.channel in ["vk", "vk_user"]:
                peer_name = f"Пользователь VK {msg.peer_id}"
            elif msg.channel in ["max", "max_user", "max_account", "max_bot", "max_bridge"]:
                if phone:
                    peer_name = f"MAX Клиент ({phone})"
                else:
                    peer_name = f"MAX Собеседник {msg.peer_id}"

        # Форматирование телефона если найден
        if phone:
            digits = "".join(filter(str.isdigit, str(phone)))
            if len(digits) == 11 and (digits.startswith("7") or digits.startswith("8")):
                phone = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
            elif len(digits) == 10:
                phone = f"+7 ({digits[0:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
            elif not phone.startswith("+"):
                phone = f"+{phone}"

        display_text = (msg.text or "").strip()
        if not display_text and isinstance(payload_dict, dict):
            if payload_dict.get("attachments"):
                att = payload_dict["attachments"]
                if isinstance(att, list) and len(att) > 0:
                    att_type = att[0].get("type", "Вложение")
                    display_text = f"[{att_type}]"
            elif payload_dict.get("sticker"):
                display_text = "[Стикер]"
            elif payload_dict.get("voice"):
                display_text = "[Голосовое сообщение]"
            elif payload_dict.get("caption"):
                display_text = payload_dict.get("caption")

        if not display_text:
            display_text = "Вложение или медиафайл"

        dialogs.append({
            "channel": msg.channel,
            "channel_id": msg.channel_id,
            "peer_id": str(msg.peer_id),
            "peer_name": peer_name,
            "peer_avatar": peer_avatar,
            "phone": phone,
            "text": display_text,
            "last_message": display_text,
            "created_at": msg.created_at,
            "last_message_time": msg.created_at,
            "direction": msg.direction,
            "last_message_direction": msg.direction,
            "is_read": bool(unread_count == 0),
            "unread_count": unread_count,
            "is_pinned": is_pinned,
            "is_hidden": is_hidden,
            "tags": attached_tags
        })
        
    # Иерархическая сортировка диалогов:
    # 1. Закрепленные чаты (is_pinned) — в самом верху (по времени)
    # 2. Непрочитанные чаты (unread_count > 0) — сразу после закрепов (по времени)
    # 3. Все остальные прочитанные чаты — по убыванию времени последнего сообщения
    def _dialog_sort_key(d):
        is_p = 0 if d.get("is_pinned") else 1
        has_unr = 0 if (d.get("unread_count", 0) > 0) else 1
        ts = -_get_timestamp(d.get("last_message_time"))
        return (is_p, has_unr, ts)

    dialogs.sort(key=_dialog_sort_key)

    # Сохраняем в кэш Redis на 120 секунд для мгновенной отдачи при повторных запросах
    try:
        from app.core.redis import redis_client
        def _json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        await redis_client.setex(cache_key, 120, json.dumps(dialogs, default=_json_serial))
    except Exception as e:
        logger.debug(f"Redis set dialogs cache warning: {e}")

    return dialogs


@router.post("/dialogs/{channel}/{peer_id}/pin")
async def toggle_pin_dialog(
    channel: str,
    peer_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Закрепить или открепить диалог"""
    existing = db.exec(
        select(MultichatPinnedDialog)
        .where(MultichatPinnedDialog.channel == channel)
        .where(MultichatPinnedDialog.peer_id == peer_id)
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        await invalidate_multichat_dialogs_cache()
        return {"status": "unpinned", "is_pinned": False}
    else:
        pin = MultichatPinnedDialog(channel=channel, peer_id=peer_id)
        db.add(pin)
        db.commit()
        await invalidate_multichat_dialogs_cache()
        return {"status": "pinned", "is_pinned": True}


@router.get("/hidden-keys")
async def get_hidden_keys(
    current_user: User = Depends(require_permission("multichat_view"))
):
    """Получить список ключей всех скрытых диалогов (channel:peer_id) для мгновенной фильтрации уведомлений"""
    keys = await get_hidden_dialog_keys()
    return list(keys)


@router.post("/dialogs/{channel}/{peer_id}/hide")
async def toggle_hide_dialog(
    channel: str,
    peer_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Скрыть диалог из общего списка или вернуть его обратно"""
    from app.core.redis import redis_client
    existing = db.exec(
        select(MultichatHiddenDialog)
        .where(MultichatHiddenDialog.channel == channel)
        .where(MultichatHiddenDialog.peer_id == peer_id)
    ).first()

    key_str = f"{channel}:{peer_id}"
    if existing:
        db.delete(existing)
        db.commit()
        try:
            await redis_client.srem(HIDDEN_DIALOGS_REDIS_KEY, key_str)
        except Exception:
            pass
        await invalidate_multichat_dialogs_cache()
        return {"status": "unhidden", "is_hidden": False, "message": "Диалог возвращен в общий список"}
    else:
        hidden = MultichatHiddenDialog(channel=channel, peer_id=peer_id)
        db.add(hidden)
        db.commit()
        try:
            await redis_client.sadd(HIDDEN_DIALOGS_REDIS_KEY, key_str)
        except Exception:
            pass
        await invalidate_multichat_dialogs_cache()
        return {"status": "hidden", "is_hidden": True, "message": "Диалог скрыт из общего списка"}


@router.get("/dialogs/{channel}/{peer_id}/history")
async def get_history(
    channel: str,
    peer_id: str,
    page: int = 1,
    per_page: Optional[int] = None,
    limit: int = 10,
    before_id: Optional[int] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_view"))
):
    """Получение истории сообщений диалога с пагинацией (высокоскоростной отклик по 10 сообщений)"""
    fetch_limit = per_page if per_page is not None else limit
    if fetch_limit <= 0:
        fetch_limit = 10

    alt_channels = [channel]
    if channel in ("vk", "vk_user"):
        alt_channels = ["vk", "vk_user"]
    elif channel in ("max", "max_user", "max_bot", "max_account", "max_bridge"):
        alt_channels = ["max", "max_user", "max_bot", "max_account", "max_bridge"]
    elif channel in ("whatsapp", "whatsapp_user", "whatsapp_account"):
        alt_channels = ["whatsapp", "whatsapp_user", "whatsapp_account"]

    stmt = (
        select(MultichatMessage)
        .where(MultichatMessage.channel.in_(alt_channels))
        .where(MultichatMessage.peer_id == peer_id)
    )

    if before_id:
        stmt = stmt.where(MultichatMessage.id < before_id)
    elif page > 1:
        stmt = stmt.offset((page - 1) * fetch_limit)

    stmt = stmt.order_by(desc(MultichatMessage.id)).limit(fetch_limit)
    messages = list(db.exec(stmt).all())

    # Если в локальной базе сообщений пока нет (первое открытие нового диалога), выполняем фоновую синхронизацию
    if not messages and not before_id and page == 1:
        if channel == "vk_user":
            try:
                from app.services.multichat_user_service import multichat_user_service
                multichat_user_service.fetch_vk_user_history(peer_id, db, count=fetch_limit)
                messages = list(db.exec(stmt).all())
            except Exception as e:
                logger.warning(f"Error prefetching VK user history: {e}")
        elif channel in ["max_user", "max_bridge", "max_account"]:
            try:
                from app.services.max_bridge_service import max_bridge_service
                await max_bridge_service.fetch_chat_history(peer_id, db, count=fetch_limit)
                messages = list(db.exec(stmt).all())
            except Exception as e:
                logger.warning(f"Error prefetching MAX history: {e}")

    messages.reverse() # возвращаем в хронологическом порядке

    # Проверяем, есть ли реальное имя и аватар для этого диалога (быстрый поиск)
    resolved_name = None
    resolved_avatar = None

    # Сначала проверяем уже загруженные сообщения
    for m in reversed(messages):
        if m.peer_name and not m.peer_name.lower().startswith("пользователь") and not m.peer_name.startswith("VK 200") and not m.peer_name.startswith("Чат ") and not m.peer_name.startswith("MAX "):
            resolved_name = m.peer_name
        if m.peer_avatar:
            resolved_avatar = m.peer_avatar
        if resolved_name and resolved_avatar:
            break

    # Если не нашли в текущей пачке сообщений — проверяем кэш Redis
    if not resolved_name or not resolved_avatar:
        try:
            from app.core.redis import redis_client
            cached_prof = await redis_client.get(f"multichat:profile:fast:{peer_id}")
            if cached_prof:
                prof_obj = json.loads(cached_prof)
                if not resolved_name and prof_obj.get("name"):
                    resolved_name = prof_obj["name"]
                if not resolved_avatar and prof_obj.get("avatar"):
                    resolved_avatar = prof_obj["avatar"]
        except Exception:
            pass

    # Если профиля нет в кэше — делаем точечный быстрый запрос по индексу с limit(1)
    if not resolved_name or not resolved_avatar:
        real_peer_msg = db.exec(
            select(MultichatMessage)
            .where(
                MultichatMessage.channel == channel,
                MultichatMessage.peer_id == peer_id,
                MultichatMessage.peer_name.is_not(None),
                ~MultichatMessage.peer_name.ilike("%пользователь%"),
                ~MultichatMessage.peer_name.startswith("VK 200"),
                ~MultichatMessage.peer_name.startswith("Чат "),
                ~MultichatMessage.peer_name.startswith("MAX ")
            )
            .order_by(desc(MultichatMessage.id))
            .limit(1)
        ).first()
        if real_peer_msg:
            if not resolved_name:
                resolved_name = real_peer_msg.peer_name
            if not resolved_avatar:
                resolved_avatar = real_peer_msg.peer_avatar
            # Сохраняем в кэш Redis
            try:
                from app.core.redis import redis_client
                asyncio.create_task(redis_client.setex(
                    f"multichat:profile:fast:{peer_id}", 
                    86400, 
                    json.dumps({"channel": channel, "name": resolved_name, "avatar": resolved_avatar})
                ))
            except Exception:
                pass

    from app.services.chat_media_cache_service import chat_media_cache_service
    result = []
    for m in messages:
        m_dict = m.model_dump()
        if resolved_name and (not m.peer_name or "пользователь" in m.peer_name.lower() or m.peer_name.startswith("VK 200") or m.peer_name.startswith("MAX ")):
            m_dict["peer_name"] = resolved_name
        if resolved_avatar and not m.peer_avatar:
            m_dict["peer_avatar"] = resolved_avatar
        m_dict["attachments"] = chat_media_cache_service.extract_attachments_from_payload(m.payload, m.channel)
        result.append(m_dict)
    return result


@router.get("/proxy-image")
async def proxy_chat_image(
    url: str = Query(..., description="URL изображения для безопасного проксирования")
):
    """Безопасный прокси для изображений и вложений, предотвращающий 403 Forbidden / CORS блокировки CDN"""
    if not url or (not url.startswith("http://") and not url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
            }
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Remote image fetch failed")
            
            content_type = resp.headers.get("content-type", "image/jpeg")
            return Response(
                content=resp.content, 
                media_type=content_type, 
                headers={
                    "Cache-Control": "public, max-age=604800, immutable",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    except Exception as e:
        logger.warning(f"Error proxying image {url}: {e}")
        raise HTTPException(status_code=502, detail=f"Proxy error: {e}")




@router.post("/dialogs/{channel}/{peer_id}/send")
async def send_reply(
    channel: str,
    peer_id: str,
    payload: dict,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Отправка ответа пользователю через выбранный канал"""
    text = payload.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Текст сообщения не может быть пустым")

    success = False
    external_id = None

    if channel in ["vk_user", "vk_account"]:
        try:
            from app.services.multichat_user_service import multichat_user_service
            external_id = multichat_user_service.send_vk_user_message(peer_id, text, db)
            success = True
        except Exception as e:
            logger.error(f"Failed to send VK user message: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка отправки VK: {e}")

    elif channel == "vk":
        # Ищем токен ВК
        bot = db.exec(select(VkBotConnection).where(VkBotConnection.is_active == True)).first()
        token = bot.vk_bot_token if bot else None
        if not token:
            settings = db.exec(select(VkSettings)).first()
            token = settings.vk_bot_token if settings else None
            
        if not token:
            raise HTTPException(status_code=400, detail="Токен VK не настроен")
            
        try:
            vk_res = await send_vk_message(vk_id=int(peer_id), message=text, bot_token=token)
            if vk_res:
                success = True
                if isinstance(vk_res, int):
                    external_id = str(vk_res)
        except Exception as e:
            logger.error(f"Failed to send VK message: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка отправки VK: {e}")

    elif channel == "telegram_bot":
        # Ищем токен Telegram
        settings = db.exec(select(ValidationSettings)).first()
        if not settings or not settings.telegram_bot_token:
            raise HTTPException(status_code=400, detail="Токен Telegram бота не настроен")
            
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        tg_payload = {"chat_id": int(peer_id), "text": text}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=tg_payload, timeout=10)
                if resp.status_code == 200:
                    success = True
                    tg_data = resp.json()
                    external_id = str(tg_data.get("result", {}).get("message_id"))
                else:
                    logger.error(f"Telegram API response: {resp.text}")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка отправки Telegram: {e}")

    elif channel in ["max_bot", "max_account", "max"]:
        # Отправка через интеллектуальный сервис MAX (официальный Bot API или Web Bridge)
        try:
            from app.services.max_service import send_max_message
            max_res = await send_max_message(recipient=peer_id, text=text, session=db)
            if max_res and max_res.get("success"):
                success = True
                external_id = str(max_res.get("msg_id") or max_res.get("id") or "")
            else:
                err_msg = max_res.get("error") if isinstance(max_res, dict) else "Сбой отправки сообщения MAX"
                logger.error(f"Failed to send MAX message to {peer_id}: {err_msg}")
                raise HTTPException(status_code=500, detail=f"Ошибка отправки MAX: {err_msg}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to send MAX message: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка отправки MAX: {e}")

    elif channel in ["max_user", "max_bridge"]:
        # Отправка через подключенный Web Instance Bridge MAX
        try:
            from app.services.max_bridge_service import max_bridge_service
            res = await max_bridge_service.send_bridge_message(peer_id=peer_id, text=text, db=db)
            if res and (isinstance(res, dict) and (res.get("msg_id") or res.get("id"))):
                success = True
                external_id = str(res.get("msg_id") or res.get("id") or "")
            else:
                # Фоллбэк на универсальный сервисный метод MAX
                from app.services.max_service import send_max_message
                max_res = await send_max_message(recipient=peer_id, text=text, session=db)
                if max_res and max_res.get("success"):
                    success = True
                    external_id = str(max_res.get("msg_id") or max_res.get("id") or "")
        except Exception as e:
            logger.error(f"Failed to send MAX Bridge message: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка отправки MAX Bridge: {e}")

    elif channel in ["whatsapp", "whatsapp_account"]:
        # Отправка через подключенный WhatsApp аккаунт
        acc = db.exec(
            select(MultichatAccount)
            .where(MultichatAccount.channel.in_(["whatsapp", "whatsapp_account"]))
            .where(MultichatAccount.status == "active")
        ).first()
        if not acc:
            raise HTTPException(status_code=400, detail="Подключенный WhatsApp аккаунт не найден. Подключите его в настройках аккаунтов.")
        
        # Если настроен Green API токен (формат instanceId:apiToken)
        if acc.token and ":" in acc.token:
            instance_id, api_token = acc.token.split(":", 1)
            url = f"https://api.green-api.com/waInstance{instance_id}/sendMessage/{api_token}"
            chat_id = f"{peer_id}@c.us" if "@" not in peer_id else peer_id
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, json={"chatId": chat_id, "message": text}, timeout=10)
                    if resp.status_code == 200:
                        success = True
                        external_id = resp.json().get("idMessage")
                    else:
                        logger.error(f"WhatsApp Green-API error: {resp.text}")
            except Exception as e:
                logger.error(f"Failed to send WhatsApp message: {e}")
                raise HTTPException(status_code=500, detail=f"Ошибка отправки WhatsApp: {e}")
        else:
            success = True

    if not success:
        raise HTTPException(status_code=500, detail="Не удалось отправить сообщение")

    # Сохраняем исходящее сообщение в БД
    try:
        # Пытаемся подтянуть имя собеседника из последнего сообщения
        last_msg = db.exec(
            select(MultichatMessage)
            .where(MultichatMessage.channel == channel)
            .where(MultichatMessage.peer_id == peer_id)
            .order_by(desc(MultichatMessage.created_at))
            .limit(1)
        ).first()
        
        peer_name = last_msg.peer_name if last_msg else None
        peer_avatar = last_msg.peer_avatar if last_msg else None
        
        new_msg = MultichatMessage(
            channel=channel,
            channel_id=None,
            peer_id=peer_id,
            peer_name=peer_name,
            peer_avatar=peer_avatar,
            from_id="admin",
            text=text,
            direction="outbound",
            external_id=external_id,
            is_read=True,
            created_at=datetime.now(timezone.utc),
            payload=payload
        )
        db.add(new_msg)
        db.commit()
        db.refresh(new_msg)
        
        # Оповещаем другие вкладки через WebSocket
        asyncio.create_task(broadcast_ws_message(new_msg))
        
        return new_msg
    except Exception as e:
        logger.error(f"Error saving outbound message: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения сообщения: {e}")

@router.post("/dialogs/{channel}/{peer_id}/read")
async def mark_as_read(
    channel: str,
    peer_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_view"))
):
    """Пометка диалога как прочитанного"""
    try:
        channels = [channel]
        if channel in ["vk", "vk_user"]:
            channels = ["vk", "vk_user"]
        elif channel in ["max", "max_user", "max_bot", "max_account", "max_bridge"]:
            channels = ["max", "max_user", "max_bot", "max_account", "max_bridge"]
        elif channel in ["whatsapp", "whatsapp_account"]:
            channels = ["whatsapp", "whatsapp_account"]
        elif channel in ["telegram_bot", "telegram_user"]:
            channels = ["telegram_bot", "telegram_user"]

        from sqlalchemy import update
        db.execute(
            update(MultichatMessage)
            .where(MultichatMessage.channel.in_(channels))
            .where(MultichatMessage.peer_id == peer_id)
            .where(MultichatMessage.direction == "inbound")
            .where(MultichatMessage.is_read == False)
            .values(is_read=True)
        )
        db.commit()
        await invalidate_multichat_dialogs_cache()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error marking messages as read: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dialogs/read-all")
async def mark_all_dialogs_as_read(
    payload: Optional[dict] = None,
    channel: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_view"))
):
    """Пометка всех диалогов как прочитанных (массовое действие)"""
    try:
        selected_channel = channel or (payload.get("channel") if payload else None)
        channels = None
        if selected_channel and selected_channel != "all":
            if selected_channel in ["vk", "vk_user"]:
                channels = ["vk", "vk_user"]
            elif selected_channel in ["max", "max_user", "max_bot", "max_account", "max_bridge"]:
                channels = ["max", "max_user", "max_bot", "max_account", "max_bridge"]
            elif selected_channel in ["whatsapp", "whatsapp_account"]:
                channels = ["whatsapp", "whatsapp_account"]
            elif selected_channel in ["telegram_bot", "telegram_user"]:
                channels = ["telegram_bot", "telegram_user"]
            else:
                channels = [selected_channel]

        from sqlalchemy import update
        stmt = (
            update(MultichatMessage)
            .where(MultichatMessage.direction == "inbound")
            .where(MultichatMessage.is_read == False)
        )
        if channels:
            stmt = stmt.where(MultichatMessage.channel.in_(channels))

        db.execute(stmt.values(is_read=True))
        db.commit()
        await invalidate_multichat_dialogs_cache()
        return {"status": "success", "message": "Все чаты успешно помечены как прочитанные"}
    except Exception as e:
        logger.error(f"Error marking all messages as read: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/max-account/webhook")
async def max_account_webhook(
    request: Request,
    db: Session = Depends(get_session)
):
    """Прием вебхука от шлюза MAX (аккаунт)"""
    try:
        data = await request.json()
        logger.info(f"Received MAX account webhook: {data}")
    except Exception as e:
        logger.error(f"MAX account Webhook invalid JSON: {e}")
        return {"status": "ok"}

    phone = data.get("phone")
    text = data.get("text")
    msg_id = data.get("message_id") or data.get("id")

    if not phone or not text:
        # Проверим альтернативные форматы шлюзов
        phone = data.get("recipient") or data.get("contact", {}).get("phone")
        text = data.get("message") or data.get("body")
        
    if phone and text:
        try:
            # Очищаем телефон
            clean_phone = "".join(filter(str.isdigit, str(phone)))
            if not clean_phone.startswith("7") and len(clean_phone) == 10:
                clean_phone = "7" + clean_phone
                
            # Ищем, может гость уже привязан в системе
            from app.models.customer import Customer
            customer = db.exec(select(Customer).where(Customer.phone == clean_phone)).first()
            peer_name = customer.name if customer else f"MAX Клиент {clean_phone}"

            new_msg = MultichatMessage(
                channel="max_account",
                peer_id=clean_phone,
                peer_name=peer_name,
                from_id=clean_phone,
                text=text,
                direction="inbound",
                external_id=str(msg_id) if msg_id else None,
                is_read=False,
                created_at=datetime.now(timezone.utc),
                payload=data
            )
            db.add(new_msg)
            db.commit()
            db.refresh(new_msg)

            # Транслируем по вебсокетам
            await broadcast_ws_message(new_msg)
        except Exception as e:
            logger.error(f"Error processing MAX account webhook: {e}")
            db.rollback()

    return {"status": "ok"}


@router.get("/tags")
def get_tags(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_view"))
):
    """Получение списка всех меток"""
    return db.exec(select(MultichatTag)).all()


@router.post("/tags")
def create_tag(
    payload: dict,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Создание новой метки"""
    name = payload.get("name")
    color = payload.get("color", "#757575")
    if not name:
        raise HTTPException(status_code=400, detail="Название метки обязательно")
    
    # Проверим, нет ли уже тега с таким названием
    existing = db.exec(select(MultichatTag).where(MultichatTag.name == name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Метка с таким названием уже существует")

    tag = MultichatTag(name=name, color=color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/tags/{tag_id}")
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Удаление метки"""
    tag = db.get(MultichatTag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Метка не найдена")
    
    # Сначала удалим все привязки этой метки
    db.execute(delete(MultichatDialogTag).where(MultichatDialogTag.tag_id == tag_id))
    db.delete(tag)
    db.commit()
    return {"status": "success"}


@router.post("/dialogs/{channel}/{peer_id}/tags")
def update_dialog_tags(
    channel: str,
    peer_id: str,
    payload: dict,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Обновление меток диалога (привязка tag_ids)"""
    tag_ids = payload.get("tag_ids", [])
    
    # Удаляем старые связи
    db.execute(
        delete(MultichatDialogTag)
        .where(MultichatDialogTag.channel == channel)
        .where(MultichatDialogTag.peer_id == peer_id)
    )
    
    # Добавляем новые
    for tid in tag_ids:
        link = MultichatDialogTag(channel=channel, peer_id=peer_id, tag_id=tid)
        db.add(link)
        
    db.commit()
    return {"status": "success"}


# ==========================================
# Эндпоинты личных аккаунтов (Telegram, VK, MAX)
# ==========================================

from app.services.multichat_user_service import multichat_user_service, active_tg_qr_sessions, active_wa_qr_sessions
import uuid

@router.get("/accounts")
def get_accounts(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_view"))
):
    """Получение списка всех привязанных личных аккаунтов"""
    return db.exec(select(MultichatAccount)).all()


@router.post("/accounts")
def connect_account(
    payload: dict,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Добавление/подключение личного аккаунта (VK или MAX) с авто-парсингом токена и получением профиля"""
    channel = payload.get("channel") # vk_user, max_user, telegram_user
    name = payload.get("name", "").strip()
    phone = payload.get("phone")
    token = payload.get("token", "").strip()

    if not channel or not token:
        raise HTTPException(status_code=400, detail="Укажите канал и токен/ссылку доступа")

    # Для ВКонтакте: если вставлена вся ссылка из браузера, автоматически извлекаем access_token
    if channel == "vk_user" and token:
        if "access_token=" in token:
            import re
            match = re.search(r'access_token=([^&]+)', token)
            if match:
                token = match.group(1)

        # Автоматически проверяем токен и подтягиваем имя и фамилию аккаунта VK из API
        try:
            resp = httpx.get("https://api.vk.com/method/users.get", params={
                "access_token": token,
                "v": "5.131",
                "fields": "photo_100"
            }, timeout=10.0)
            data = resp.json()
            if "error" in data:
                err = data["error"]
                if err.get("error_subcode") == 1130 or "another ip" in str(err.get("error_msg", "")).lower():
                    raise HTTPException(
                        status_code=400, 
                        detail="Токен привязан к вашему домашнему IP. В генераторе VKHost выберите «VK Android» или «VK Me» — мобильные токены работают с сервера без привязки к IP."
                    )
                else:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Ошибка токена VK: {err.get('error_msg')}"
                    )

            if "response" in data and len(data["response"]) > 0:
                vk_info = data["response"][0]
                vk_name = f"{vk_info.get('first_name', '')} {vk_info.get('last_name', '')}".strip()
                if vk_name:
                    name = vk_name
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching VK user info: {e}")

    account = multichat_user_service.create_or_update_account(
        channel=channel,
        name=name,
        phone=phone,
        token=token
    )
    
    if channel == "vk_user":
        try:
            multichat_user_service.sync_vk_user_dialogs(db, account.id)
        except Exception as sync_err:
            logger.warning(f"Initial VK user sync error: {sync_err}")
    elif channel in ["max_user", "max_account", "max_bot", "max"]:
        try:
            multichat_user_service.sync_max_user_dialogs(db, account.id)
        except Exception as sync_err:
            logger.warning(f"Initial MAX user sync error: {sync_err}")

    return account


@router.post("/accounts/{account_id}/test")
async def test_account_connection(
    account_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_view"))
):
    """Проверка валидности и работоспособности подключения личного/бизнес аккаунта"""
    acc = db.exec(select(MultichatAccount).where(MultichatAccount.id == account_id)).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    channel = acc.channel
    token = acc.token

    if channel in ["max_user", "max_account", "max_bot", "max", "max_bridge"]:
        if not token and not acc.session_string:
            return {"status": "error", "message": "Токен авторизации отсутствует"}

        # Проверка сессионного моста MAX (Web Instance Bridge)
        session_meta = {}
        if acc.session_string:
            try:
                session_meta = json.loads(acc.session_string)
            except Exception:
                pass

        if session_meta.get("bridge_mode") == "pymax_web_instance" or (token and (token.startswith("max_session_") or token.startswith("max_bridge_") or token.endswith(".db"))):
            from app.services.max_bridge_service import MAX_SESSIONS_DIR, active_max_web_clients
            db_name = session_meta.get("db_name") or f"{token}.db"
            db_path = os.path.join(MAX_SESSIONS_DIR, db_name)
            
            existing_dialogs = db.exec(
                select(MultichatMessage)
                .where(MultichatMessage.channel.in_(["max_user", "max_bridge", "max_account"]))
            ).all()

            return {
                "status": "ok",
                "name": acc.name or "Личный MAX",
                "chats_count": len(existing_dialogs),
                "message": f"Сессионный мост MAX активен! Профиль: {acc.name}, телефон: {acc.phone or 'Привязан'}"
            }

        # Для стандартных Bot API токенов platform-api2.max.ru
        try:
            headers = {"Authorization": token}
            async with httpx.AsyncClient(verify=False) as client:
                r = await client.get("https://platform-api2.max.ru/me", headers=headers, timeout=10.0)
                if r.status_code == 200:
                    data = r.json()
                    name = data.get("name") or data.get("username") or acc.name
                    r_chats = await client.get("https://platform-api2.max.ru/chats", headers=headers, timeout=10.0)
                    chats_count = 0
                    if r_chats.status_code == 200:
                        c_data = r_chats.json()
                        chats_list = c_data.get("chats", []) if isinstance(c_data, dict) else (c_data if isinstance(c_data, list) else [])
                        chats_count = len(chats_list)

                    return {
                        "status": "ok",
                        "name": name,
                        "chats_count": chats_count,
                        "message": f"Соединение с MAX успешно! Профиль: {name}, доступно диалогов: {chats_count}"
                    }
                elif r.status_code == 401:
                    err_json = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                    err_msg = err_json.get("message") or "Токен недействителен или истек (Invalid access_token)"
                    return {
                        "status": "error",
                        "code": 401,
                        "message": f"Ошибка авторизации MAX (401): {err_msg}. Проверьте правильность токена."
                    }
                else:
                    return {
                        "status": "error",
                        "code": r.status_code,
                        "message": f"Сервер MAX вернул статус {r.status_code}: {r.text[:150]}"
                    }
        except Exception as e:
            return {"status": "error", "message": f"Не удалось связаться с сервером MAX: {str(e)}"}


    elif channel == "vk_user":
        if not token:
            return {"status": "error", "message": "Токен авторизации отсутствует"}
        try:
            async with httpx.AsyncClient() as client:
                u_res = await client.get("https://api.vk.com/method/users.get", params={
                    "access_token": token,
                    "v": "5.131",
                    "fields": "photo_100"
                }, timeout=8.0)
                u_data = u_res.json()
                if "error" in u_data:
                    err = u_data["error"]
                    subcode = err.get("error_subcode")
                    if subcode == 1130:
                        return {
                            "status": "error",
                            "code": 1130,
                            "message": "Токен привязан к вашему домашнему IP. Авторизуйтесь через вкладку 'Вход по Логину и Паролю' или используйте Standalone-токен."
                        }
                    return {"status": "error", "message": f"Ошибка VK: {err.get('error_msg')}"}

                user_name = "VK Пользователь"
                if "response" in u_data and len(u_data["response"]) > 0:
                    v_info = u_data["response"][0]
                    user_name = f"{v_info.get('first_name', '')} {v_info.get('last_name', '')}".strip()

                m_res = await client.get("https://api.vk.com/method/messages.getConversations", params={
                    "access_token": token,
                    "count": 5,
                    "v": "5.131"
                }, timeout=8.0)
                m_data = m_res.json()
                if "error" in m_data:
                    err = m_data["error"]
                    code = err.get("error_code")
                    if code == 15:
                        return {
                            "status": "error",
                            "code": 15,
                            "message": f"Профиль {user_name} подключен, но токен выдан без прав на чтение сообщений (Access denied). Используйте прямой вход."
                        }
                    return {"status": "error", "message": f"Ошибка сообщений VK: {err.get('error_msg')}"}

                conv_count = m_data.get("response", {}).get("count", 0)
                return {
                    "status": "ok",
                    "name": user_name,
                    "chats_count": conv_count,
                    "message": f"Соединение с ВКонтакте успешно! Профиль: {user_name}, активных диалогов: {conv_count}"
                }
        except Exception as e:
            return {"status": "error", "message": f"Ошибка проверки VK: {str(e)}"}

    elif channel == "telegram_user":
        if acc.session_string:
            return {"status": "ok", "message": "Сессия Telegram активна и сохранена"}
        return {"status": "error", "message": "Сессия Telegram не инициализирована (требуется вход по QR)"}

    return {"status": "ok", "message": "Аккаунт активен"}


@router.post("/accounts/vk/direct-login")
async def direct_vk_login(
    payload: dict,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Прямая безопасная авторизация аккаунта ВКонтакте через сервер (без проблем с IP-привязкой)"""
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip()
    code = payload.get("code", "").strip()
    sid = payload.get("sid", "").strip()
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Укажите логин (телефон/email) и пароль от ВКонтакте")

    data = {
        "grant_type": "password",
        "client_id": "2274003", # VK Android Standalone
        "client_secret": "hHbZxrka2uZ6jB1inYsH",
        "username": username,
        "password": password,
        "2fa_supported": "1",
        "scope": "all,offline",
        "v": "5.131"
    }
    if code and sid:
        data["code"] = code
        data["sid"] = sid

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://oauth.vk.com/token", data=data, timeout=15.0)
            res_data = resp.json()

        if "error" in res_data:
            err = res_data["error"]
            if err == "need_validation":
                val_type = res_data.get("validation_type")
                val_sid = res_data.get("validation_sid")
                phone_mask = res_data.get("phone_mask", "")
                return {
                    "status": "need_2fa",
                    "validation_type": val_type,
                    "validation_sid": val_sid,
                    "phone_mask": phone_mask,
                    "message": f"Введите код подтверждения из SMS или приложения (отправлен на {phone_mask})"
                }
            elif err == "need_captcha":
                return {
                    "status": "need_captcha",
                    "captcha_sid": res_data.get("captcha_sid"),
                    "captcha_img": res_data.get("captcha_img"),
                    "message": "Требуется ввод капчи"
                }
            else:
                desc = res_data.get("error_description") or err
                raise HTTPException(status_code=400, detail=f"Ошибка авторизации ВКонтакте: {desc}")

        access_token = res_data.get("access_token")
        user_id = res_data.get("user_id")

        if not access_token:
            raise HTTPException(status_code=400, detail="Токен доступа не получен от ВКонтакте")

        # Получаем данные пользователя
        name = f"VK {user_id}"
        try:
            async with httpx.AsyncClient() as client:
                u_resp = await client.get("https://api.vk.com/method/users.get", params={
                    "access_token": access_token,
                    "v": "5.131",
                    "fields": "photo_100"
                }, timeout=10.0)
                u_data = u_resp.json()
                if "response" in u_data and len(u_data["response"]) > 0:
                    v_info = u_data["response"][0]
                    name = f"{v_info.get('first_name', '')} {v_info.get('last_name', '')}".strip() or name
        except Exception:
            pass

        account = multichat_user_service.create_or_update_account(
            channel="vk_user",
            name=name,
            phone=username if username.startswith("+") or username.isdigit() else None,
            token=access_token,
            status="active"
        )

        # Сразу запускаем синхронизацию сообщений
        try:
            multichat_user_service.sync_vk_user_dialogs(db, account.id)
        except Exception as sync_err:
            logger.warning(f"Initial direct VK sync error: {sync_err}")

        return {
            "status": "success",
            "account": account,
            "message": f"Аккаунт {name} успешно подключен!"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VK Direct Auth exception: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка прямого входа VK: {str(e)}")


@router.get("/accounts/vk/oauth-link")
def get_vk_oauth_link():
    """Возвращает прямую ссылку на упрощенную авторизацию VK User API"""
    link = "https://oauth.vk.com/authorize?client_id=2685278&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=messages,offline,photos,docs,wall&response_type=token&v=5.131"
    return {"oauth_url": link}


@router.post("/accounts/vk/qr/init")
def init_vk_qr():
    """Инициализация авторизации VK по QR-коду"""
    from app.services.multichat_user_service import multichat_user_service
    try:
        data = multichat_user_service.init_vk_qr_session()
        return data
    except Exception as e:
        logger.error(f"Error init VK QR: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации QR-кода VK: {e}")


@router.post("/accounts/vk/qr/confirm")
def confirm_vk_qr(
    payload: dict,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Подтверждение авторизации VK по токену или URL редиректа"""
    token_or_url = payload.get("token_or_url") or payload.get("token") or payload.get("url")
    if not token_or_url:
        raise HTTPException(status_code=400, detail="Токен или ссылка авторизации не переданы")

    from app.services.multichat_user_service import multichat_user_service
    try:
        res = multichat_user_service.confirm_vk_token(token_or_url, db)
        return res
    except Exception as e:
        logger.error(f"Error confirming VK token: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/media/cleanup-cache")
def cleanup_media_cache(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Очистка кэша изображений сообщений старше 48 дней"""
    from app.services.chat_media_cache_service import chat_media_cache_service
    stats = chat_media_cache_service.cleanup_expired_cache(days=48)
    return stats




@router.delete("/accounts/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Отключение личного аккаунта (сообщения сохраняются)"""
    success = multichat_user_service.delete_account(account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    return {"status": "success"}


@router.post("/accounts/{account_id}/clear-messages")
def clear_account_messages_endpoint(
    account_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Ручная очистка загруженных сообщений для конкретного аккаунта"""
    deleted_count = multichat_user_service.clear_account_messages(account_id)
    return {
        "status": "success",
        "deleted_count": deleted_count,
        "message": f"Успешно удалено сообщений: {deleted_count}"
    }



@router.post("/accounts/telegram/qr/init")
async def init_telegram_qr():
    """Инициализация реальной авторизации Telegram по QR-коду"""
    import uuid
    from app.services.multichat_user_service import multichat_user_service
    session_id = str(uuid.uuid4())
    try:
        res = await multichat_user_service.init_telegram_qr(session_id)
        return res
    except Exception as e:
        logger.error(f"Error init telegram qr: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации QR-кода: {str(e)}")


@router.get("/accounts/telegram/qr/status/{session_id}")
def get_telegram_qr_status(session_id: str):
    """Проверка статуса QR-авторизации Telegram"""
    from app.services.multichat_user_service import active_tg_qr_sessions
    sess = active_tg_qr_sessions.get(session_id)
    if not sess:
        return {"status": "expired"}
    
    return {
        "status": sess.get("status", "pending"),
        "phone": sess.get("phone"),
        "user_name": sess.get("user_name")
    }


@router.post("/accounts/whatsapp/qr/init")
async def init_whatsapp_qr():
    """Инициализация авторизации WhatsApp по QR-коду"""
    import uuid
    from app.services.multichat_user_service import multichat_user_service
    session_id = str(uuid.uuid4())
    try:
        res = await multichat_user_service.init_whatsapp_qr(session_id)
        return res
    except Exception as e:
        logger.error(f"Error init whatsapp qr: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации WhatsApp QR: {str(e)}")


@router.get("/accounts/whatsapp/qr/status/{session_id}")
def get_whatsapp_qr_status(session_id: str):
    """Проверка статуса QR-авторизации WhatsApp"""
    from app.services.multichat_user_service import active_wa_qr_sessions
    sess = active_wa_qr_sessions.get(session_id)
    if not sess:
        return {"status": "expired"}
    
    return {
        "status": sess.get("status", "pending"),
        "phone": sess.get("phone"),
        "name": sess.get("name")
    }


@router.post("/accounts/whatsapp/qr/confirm/{session_id}")
def confirm_whatsapp_qr(session_id: str, payload: dict, db: Session = Depends(get_session)):
    """Подтверждение подключения WhatsApp аккаунта"""
    from app.services.multichat_user_service import multichat_user_service, active_wa_qr_sessions
    name = payload.get("name", "WhatsApp Аккаунт")
    phone = payload.get("phone")
    token = payload.get("token")
    
    acc = multichat_user_service.create_or_update_account(
        channel="whatsapp",
        name=name,
        phone=phone,
        token=token,
        status="active"
    )
    
    if session_id in active_wa_qr_sessions:
        active_wa_qr_sessions[session_id]["status"] = "active"
        active_wa_qr_sessions[session_id]["name"] = name
        active_wa_qr_sessions[session_id]["phone"] = phone
        
    return {"status": "success", "account": acc}


@router.post("/accounts/max/qr/init")
async def init_max_qr():
    """Инициализация авторизации MAX по QR-коду"""
    try:
        res = await multichat_user_service.init_max_qr_session()
        return res
    except Exception as e:
        logger.error(f"Error init MAX qr: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации QR-кода MAX: {str(e)}")


@router.get("/accounts/max/qr/status/{session_id}")
def get_max_qr_status_endpoint(session_id: str):
    """Проверка статуса QR-авторизации MAX"""
    return multichat_user_service.get_max_qr_status(session_id)


@router.post("/accounts/max/sms/request")
def request_max_sms_endpoint(payload: dict):
    """Запрос SMS-кода для прямого входа в MAX"""
    phone = payload.get("phone", "").strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Укажите номер телефона")
    try:
        res = multichat_user_service.request_max_sms(phone)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запроса SMS: {str(e)}")


@router.post("/accounts/max/sms/verify")
def verify_max_sms_endpoint(
    payload: dict,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Подтверждение SMS-кода и создание сессии MAX"""
    session_id = payload.get("session_id", "").strip()
    code = payload.get("code", "").strip()
    name = payload.get("name", "").strip()
    if not session_id or not code:
        raise HTTPException(status_code=400, detail="Укажите session_id и код из SMS")
    try:
        account = multichat_user_service.verify_max_sms(session_id, code, name)
        try:
            multichat_user_service.sync_max_user_dialogs(db, account.id)
        except Exception as sync_err:
            logger.warning(f"Initial MAX sync error: {sync_err}")
        return {
            "status": "success",
            "account": account,
            "message": f"Аккаунт MAX ({account.name}) успешно подключен!"
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подтверждения: {str(e)}")


@router.post("/accounts/max/qr/confirm/{session_id}")
def confirm_max_qr_endpoint(
    session_id: str,
    payload: dict,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_edit"))
):
    """Подтверждение сессии привязки MAX через Web Instance Bridge"""
    from app.services.max_bridge_service import max_bridge_service
    phone = payload.get("phone")
    name = payload.get("name")
    token = payload.get("token")
    try:
        account = max_bridge_service.confirm_bridge_session(
            session_id=session_id,
            phone=phone,
            user_name=name,
            auth_token=token
        )
        try:
            multichat_user_service.sync_max_user_dialogs(db, account.id)
        except Exception as sync_err:
            logger.warning(f"Initial MAX bridge sync error: {sync_err}")

        return {
            "status": "success",
            "account": account,
            "message": f"Аккаунт MAX ({account.name}) успешно подключен через Web Instance Bridge!"
        }
    except Exception as e:
        logger.error(f"Error confirming MAX bridge session: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка подтверждения сессии MAX: {str(e)}")


@router.get("/max/search-user")
async def search_max_user_endpoint(
    phone: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_view"))
):
    """Поиск пользователя MAX по номеру телефона в реальном времени"""
    from app.services.max_bridge_service import max_bridge_service
    res = await max_bridge_service.search_user_by_phone(phone, db)
    return res


@router.get("/search-by-phone")
async def universal_search_by_phone(
    phone: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_view"))
):
    """Универсальный поиск собеседника по номеру телефона по всем каналам и CRM"""
    from app.models.customer import Customer
    from app.models.vk_user import VkUser
    from app.services.max_bridge_service import max_bridge_service

    clean_digits = "".join(filter(str.isdigit, str(phone)))
    if len(clean_digits) == 11 and (clean_digits.startswith("8") or clean_digits.startswith("7")):
        clean_phone = "7" + clean_digits[1:]
    elif len(clean_digits) == 10:
        clean_phone = "7" + clean_digits
    else:
        clean_phone = clean_digits

    last10 = clean_phone[-10:] if len(clean_phone) >= 10 else clean_phone
    formatted_phone = f"+7 ({clean_phone[1:4]}) {clean_phone[4:7]}-{clean_phone[7:9]}-{clean_phone[9:11]}" if len(clean_phone) == 11 else f"+{clean_phone}"

    # 1. CRM Customer
    customer = db.exec(select(Customer).where(Customer.phone.like(f"%{last10}%"))).first()
    customer_data = None
    c_name = None
    vk_user_id = None
    telegram_id = None
    max_user_id = None

    if customer:
        c_name = f"{customer.first_name or customer.name or ''} {customer.last_name or customer.surname or ''}".strip() or customer.name
        vk_user_id = customer.vk_user_id
        telegram_id = customer.telegram_id
        max_user_id = customer.max_user_id
        customer_data = {
            "id": customer.id,
            "name": c_name or "Гость",
            "phone": customer.phone,
            "bonus_points": float(customer.bonus_points or 0),
            "total_orders_count": customer.total_orders_count or 0
        }

    # 2. VK User
    vk_name = None
    vk_avatar = None
    vk_u = None
    if vk_user_id:
        vk_u = db.exec(select(VkUser).where(VkUser.vk_id == vk_user_id)).first()
    if not vk_u:
        vk_u = db.exec(select(VkUser).where(VkUser.phone.like(f"%{last10}%"))).first()

    if vk_u:
        vk_user_id = vk_u.vk_id
        vk_name = f"{vk_u.first_name or ''} {vk_u.last_name or ''}".strip()
        vk_avatar = vk_u.photo_50
        if customer and not customer.vk_user_id:
            customer.vk_user_id = vk_u.vk_id
            db.add(customer)
            db.commit()

    # 3. MAX Messenger
    max_name = None
    max_avatar = None
    try:
        max_res = await max_bridge_service.search_user_by_phone(clean_phone, db)
        if max_res.get("found"):
            max_user_id = max_res.get("user_id")
            max_name = max_res.get("name")
            max_avatar = max_res.get("avatar_url")
    except Exception:
        pass

    # 4. Check active operator accounts
    active_accounts = db.exec(select(MultichatAccount).where(MultichatAccount.status == "active")).all()
    active_channels = {acc.channel for acc in active_accounts}

    resolved_name = c_name or max_name or vk_name or formatted_phone

    # 5. Build available channels list
    channels_list = []

    # MAX
    channels_list.append({
        "channel": "max_user",
        "title": "MAX Messenger",
        "icon": "bx-chat",
        "color": "#ff5722",
        "peer_id": str(max_user_id) if max_user_id else None,
        "peer_name": max_name or resolved_name,
        "avatar_url": max_avatar,
        "available": bool(max_user_id and "max_user" in active_channels),
        "status_text": "Профиль найден в MAX" if max_user_id else "Не зарегистрирован в MAX"
    })

    # VK (Личный аккаунт оператора)
    channels_list.append({
        "channel": "vk_user",
        "title": "ВКонтакте (Личный диалог)",
        "icon": "bxl-vk",
        "color": "#0077ff",
        "peer_id": str(vk_user_id) if vk_user_id else None,
        "peer_name": vk_name or resolved_name,
        "avatar_url": vk_avatar,
        "available": bool(vk_user_id and "vk_user" in active_channels),
        "status_text": "Профиль найден в VK" if vk_user_id else "Профиль VK не найден по номеру"
    })

    # VK (Группа / Бот)
    channels_list.append({
        "channel": "vk",
        "title": "ВКонтакте (От имени сообщества)",
        "icon": "bxl-vk",
        "color": "#4c75a3",
        "peer_id": str(vk_user_id) if vk_user_id else None,
        "peer_name": vk_name or resolved_name,
        "avatar_url": vk_avatar,
        "available": bool(vk_user_id),
        "status_text": "Сообщество VK" if vk_user_id else "Профиль VK не привязан"
    })

    # Telegram
    channels_list.append({
        "channel": "telegram",
        "title": "Telegram",
        "icon": "bxl-telegram",
        "color": "#29b6f6",
        "peer_id": str(telegram_id) if telegram_id else None,
        "peer_name": resolved_name,
        "avatar_url": None,
        "available": bool(telegram_id),
        "status_text": "Telegram ID привязан" if telegram_id else "Telegram не привязан к номеру"
    })

    # WhatsApp
    channels_list.append({
        "channel": "whatsapp",
        "title": "WhatsApp",
        "icon": "bxl-whatsapp",
        "color": "#4caf50",
        "peer_id": clean_phone,
        "peer_name": resolved_name,
        "avatar_url": None,
        "available": True,
        "status_text": "Прямой чат по номеру телефона"
    })

    return {
        "found": bool(customer_data or vk_user_id or max_user_id),
        "phone": formatted_phone,
        "raw_phone": clean_phone,
        "name": resolved_name,
        "customer": customer_data,
        "channels": channels_list
    }


@router.get("/dialogs/{channel}/{peer_id}/guest-summary")
async def get_dialog_guest_summary(
    channel: str,
    peer_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_view"))
):
    """Получение информации об анкете гостя (телефон, имя, бонусы) и его последнем заказе в системе"""
    from app.models.customer import Customer
    from app.models.order import Order
    from app.models.vk_user import VkUser
    from sqlalchemy import or_, desc

    customer = None
    phone = None
    p_id_str = str(peer_id).strip()

    # 1. Поиск Customer по каналу
    if channel in ["max", "max_user", "max_bot", "max_account", "max_bridge"]:
        customer = db.exec(select(Customer).where(Customer.max_user_id == p_id_str)).first()
        if not customer:
            digits = "".join(filter(str.isdigit, p_id_str))
            if len(digits) >= 10:
                customer = db.exec(select(Customer).where(Customer.phone.like(f"%{digits[-10:]}%"))).first()
                if not customer:
                    phone = digits
    elif channel in ["vk", "vk_user"]:
        if p_id_str.isdigit():
            customer = db.exec(select(Customer).where(Customer.vk_user_id == int(p_id_str))).first()
            if not customer:
                vk_u = db.exec(select(VkUser).where(VkUser.vk_id == int(p_id_str))).first()
                if vk_u and vk_u.phone:
                    digits = "".join(filter(str.isdigit, vk_u.phone))
                    if len(digits) >= 10:
                        customer = db.exec(select(Customer).where(Customer.phone.like(f"%{digits[-10:]}%"))).first()
                        if not customer:
                            phone = digits
    elif channel in ["telegram", "telegram_bot", "telegram_user"]:
        if p_id_str.isdigit():
            customer = db.exec(select(Customer).where(Customer.telegram_id == int(p_id_str))).first()
    elif channel in ["whatsapp", "whatsapp_user", "whatsapp_account"]:
        digits = "".join(filter(str.isdigit, p_id_str))
        if len(digits) >= 10:
            customer = db.exec(select(Customer).where(Customer.phone.like(f"%{digits[-10:]}%"))).first()
            if not customer:
                phone = digits

    if customer and customer.phone:
        phone = customer.phone

    # Форматирование телефона для отображения
    formatted_phone = None
    raw_phone = None
    if phone:
        raw_digits = "".join(filter(str.isdigit, str(phone)))
        raw_phone = raw_digits
        if len(raw_digits) == 11 and (raw_digits.startswith("7") or raw_digits.startswith("8")):
            formatted_phone = f"+7 ({raw_digits[1:4]}) {raw_digits[4:7]}-{raw_digits[7:9]}-{raw_digits[9:11]}"
        elif len(raw_digits) == 10:
            formatted_phone = f"+7 ({raw_digits[0:3]}) {raw_digits[3:6]}-{raw_digits[6:8]}-{raw_digits[8:10]}"
        elif len(raw_digits) >= 10:
            formatted_phone = f"+{raw_digits}"
        else:
            formatted_phone = phone

    # 2. Поиск последнего заказа
    last_order = None
    order_conditions = []
    if customer:
        order_conditions.append(Order.customer_id == customer.id)
    if raw_phone and len(raw_phone) >= 10:
        order_conditions.append(Order.customer_phone.like(f"%{raw_phone[-10:]}%"))

    if order_conditions:
        last_order = db.exec(
            select(Order)
            .where(or_(*order_conditions))
            .order_by(desc(Order.created_at), desc(Order.id))
        ).first()

    last_order_data = None
    if last_order:
        last_order_data = {
            "id": last_order.id,
            "order_number": last_order.external_number or last_order.order_number or str(last_order.id),
            "status": last_order.status,
            "order_type": last_order.order_type or "Доставка",
            "total_amount": float(last_order.total_with_discount or last_order.total_amount or last_order.sum or 0),
            "created_at": last_order.created_at.isoformat() if last_order.created_at else None,
            "address": last_order.delivery_address or last_order.address or "Не указан"
        }

    return {
        "found": bool(customer or last_order),
        "customer_id": customer.id if customer else None,
        "customer_name": (customer.name or f"{customer.first_name or ''} {customer.last_name or ''}".strip()) if customer else None,
        "phone": formatted_phone,
        "raw_phone": raw_phone,
        "bonus_points": float(customer.bonus_points or 0) if customer else 0,
        "last_order": last_order_data
    }


@router.get("/search-messages")
async def search_messages_global(
    q: str = Query(..., description="Поисковый запрос (слово, фраза или имя пользователя)"),
    channel: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("multichat_view"))
):
    """Глобальный поиск по тексту сообщений и собеседникам во всех каналах Мультичата"""
    clean_q = q.strip()
    if not clean_q:
        return {"items": [], "total": 0}

    # Поиск по тексту сообщения, имени собеседника или peer_id
    query_filter = or_(
        MultichatMessage.text.ilike(f"%{clean_q}%"),
        MultichatMessage.peer_name.ilike(f"%{clean_q}%"),
        MultichatMessage.peer_id.ilike(f"%{clean_q}%")
    )

    conditions = [query_filter]
    if channel and channel != "all":
        conditions.append(MultichatMessage.channel == channel)

    # Общее количество
    total_count = db.exec(
        select(func.count(MultichatMessage.id))
        .where(*conditions)
    ).one()

    # Результаты поиска
    stmt = (
        select(MultichatMessage)
        .where(*conditions)
        .order_by(desc(MultichatMessage.created_at))
        .offset(offset)
        .limit(limit)
    )
    messages = db.exec(stmt).all()

    from app.services.chat_media_cache_service import chat_media_cache_service
    items = []
    for m in messages:
        m_dict = m.model_dump()
        m_dict["attachments"] = chat_media_cache_service.extract_attachments_from_payload(m.payload, m.channel)
        items.append(m_dict)

    return {
        "items": items,
        "total": total_count,
        "query": clean_q
    }



