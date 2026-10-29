import logging
from typing import Optional, Dict, Any
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import httpx
from app.models.vk_bot_connection import VkBotConnection
from app.models.vk_settings import VkSettings
from app.models.chat import MultichatAccount
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

VK_API_VERSION = "5.199"

async def get_valid_user_token(db: AsyncSession, conn: Optional[VkBotConnection] = None) -> Optional[str]:
    """
    Возвращает гарантированно валидный токен пользователя ВКонтакте с умным каскадным переключением (Fallback).
    Используется для методов стены (wall.*), фотографий на стену (photos.getWallUploadServer) и получения лайков (likes.getList).
    """
    candidate_tokens = []
    
    # 1. Токен пользователя из подключения группы
    if conn and conn.vk_user_token and conn.vk_user_token.strip():
        candidate_tokens.append(("conn_user_token", conn.vk_user_token.strip()))
        
    # 2. Токен пользователя из VkSettings
    stmt_settings = select(VkSettings).limit(1)
    res_settings = db.exec(stmt_settings)
    vk_sett = res_settings.first()
    if vk_sett and getattr(vk_sett, 'vk_user_token', None) and vk_sett.vk_user_token.strip():
        candidate_tokens.append(("vk_settings_token", vk_sett.vk_user_token.strip()))
        
    # 3. Живой токен пользователя из Мультичата (channel='vk_user')
    stmt_mc = select(MultichatAccount).where(
        MultichatAccount.channel == "vk_user",
        MultichatAccount.status == 'active'
    )
    res_mc = db.exec(stmt_mc)
    for mc_acc in res_mc.all():
        token = getattr(mc_acc, 'token', None) or getattr(mc_acc, 'access_token', None)
        if token and token.strip():
            candidate_tokens.append((f"multichat_{mc_acc.id}", token.strip()))
            
    # Проверяем кандидатов
    for source, token in candidate_tokens:
        cache_key = f"vk:token_status:{token[:15]}"
        cached_status = None
        if redis_client:
            try:
                cached_status = await redis_client.get(cache_key)
            except Exception:
                pass
                
        if cached_status == "valid":
            return token
        if cached_status == "invalid":
            continue
            
        # Проверяем через users.get
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.vk.ru/method/users.get",
                    params={"access_token": token, "v": VK_API_VERSION}
                )
                data = resp.json()
                if "response" in data:
                    if redis_client:
                        try:
                            await redis_client.setex(cache_key, 3600, "valid")
                        except Exception:
                            pass
                    return token
                else:
                    err = data.get("error", {})
                    err_code = err.get("error_code")
                    logger.warning(f"Token from {source} failed verification: {err}")
                    if err_code in (5, 4, 27):
                        if redis_client:
                            try:
                                await redis_client.setex(cache_key, 86400, "invalid")
                            except Exception:
                                pass
        except Exception as e:
            logger.error(f"Error checking token from {source}: {e}")
            
    logger.error("No valid VK user token found in any source (conn, settings, multichat)!")
    return None

async def get_vk_token_permissions_diagnostic(bot_token: str, user_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Проверяет маски прав токена группы и токена пользователя для админ-панели
    """
    result = {
        "group_token": {"is_valid": False, "mask": 0, "permissions": {}, "error": None},
        "user_token": {"is_valid": False, "mask": 0, "permissions": {}, "error": None}
    }
    
    # 1. Проверка bot_token
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.vk.ru/method/groups.getTokenPermissions",
                params={"access_token": bot_token, "v": VK_API_VERSION}
            )
            data = resp.json()
            if "response" in data:
                mask = data["response"].get("mask", 0)
                perms = data["response"].get("permissions", [])
                perm_names = {p.get("name"): True for p in perms if isinstance(p, dict)}
                
                # Проверка ключевых прав
                has_manage = bool(mask & 262144) or perm_names.get("manage", False)
                has_messages = bool(mask & 4096) or perm_names.get("messages", False)
                has_photos = bool(mask & 4) or perm_names.get("photos", False)
                has_wall = bool(mask & 8192) or perm_names.get("wall", False)
                
                result["group_token"] = {
                    "is_valid": True,
                    "mask": mask,
                    "permissions": {
                        "manage": has_manage,
                        "messages": has_messages,
                        "photos": has_photos,
                        "wall": has_wall,
                        "docs": bool(mask & 131072)
                    },
                    "missing_critical": [name for name, val in [("manage", has_manage), ("messages", has_messages), ("photos", has_photos), ("wall", has_wall)] if not val],
                    "error": None
                }
            else:
                result["group_token"]["error"] = data.get("error", {}).get("error_msg", "Unknown error")
    except Exception as e:
        result["group_token"]["error"] = str(e)
        
    # 2. Проверка user_token
    if user_token:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.vk.ru/method/account.getAppPermissions",
                    params={"access_token": user_token, "v": VK_API_VERSION}
                )
                data = resp.json()
                if "response" in data:
                    mask = data["response"]
                    has_wall = bool(mask & 8192)
                    has_photos = bool(mask & 4)
                    has_offline = bool(mask & 65536)
                    result["user_token"] = {
                        "is_valid": True,
                        "mask": mask,
                        "permissions": {
                            "wall": has_wall,
                            "photos": has_photos,
                            "offline": has_offline,
                            "messages": bool(mask & 4096)
                        },
                        "missing_critical": [name for name, val in [("wall", has_wall), ("photos", has_photos), ("offline", has_offline)] if not val],
                        "error": None
                    }
                else:
                    result["user_token"]["error"] = data.get("error", {}).get("error_msg", "Unknown error")
        except Exception as e:
            result["user_token"]["error"] = str(e)
            
    return result
