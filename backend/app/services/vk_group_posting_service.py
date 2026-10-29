"""
Сервис постинга на стенах групп ВКонтакте от имени личного аккаунта
Включает:
- Умный парсинг ссылок и идентификаторов групп
- Проверку открытости стены сообщества (can_post == 1)
- Загрузку фотографий в ВК
- Публикацию постов на стене (wall.post от имени пользователя)
- Отслеживание статистики (просмотры, лайки, репосты) через wall.getById
"""
import os
import re
import httpx
import logging
import tempfile
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session, select
from app.core.datetime_utils import utc_now
from app.models.vk_group_posting import VkGroupPostingHistory, VkGroupPostCampaign

logger = logging.getLogger(__name__)


class VkGroupPostingService:
    """Сервис для постинга в группах ВК от личного аккаунта"""

    @staticmethod
    def parse_group_identifiers(raw_input: str) -> List[str]:
        """
        Извлекает уникальные идентификаторы или короткие адреса групп из текста.
        Поддерживает:
        - https://vk.com/club12345
        - https://vk.com/public12345
        - https://vk.com/baraholka_samara
        - vk.com/group_alias
        - club12345 / public12345
        - 12345 / -12345
        """
        if not raw_input:
            return []

        # Разбиваем по строкам, запятым, пробелам и точке с запятой
        tokens = re.split(r'[\r\n,;\s]+', raw_input.strip())
        results = []
        seen = set()

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            # Очищаем протокол и домен vk.com
            token = re.sub(r'^https?:\/\/(?:www\.)?vk\.(?:com|ru)\/', '', token, flags=re.IGNORECASE)
            # Очищаем от query параметров / хэшей
            token = token.split('?')[0].split('#')[0].strip('/')

            # Очищаем отрицательный знак для id сообществ
            if token.startswith('-'):
                token = token[1:]

            if token and token not in seen:
                seen.add(token)
                results.append(token)

        return results

    @staticmethod
    async def check_groups_info(
        account_token: str,
        identifiers: List[str],
        fallback_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Запрашивает данные о сообществах в VK API и проверяет открытость стены (can_post).
        Если у токена аккаунта сработал Flood control (код 9) или ошибка авторизации (код 5),
        автоматически использует системный fallback токен сообщества, чтобы не блокировать интерфейс.
        """
        if not identifiers:
            return {"groups": [], "account_flood_control": False, "warning": None}

        cleaned_ids = identifiers[:500]
        # Используем надежный хост api.vk.com с фоллбэком на api.vk.ru
        api_host = "https://api.vk.com/method/groups.getById"
        
        token_to_use = account_token
        is_using_fallback = False
        account_flood_control = False
        account_warning = None

        params = {
            "group_ids": ",".join(cleaned_ids),
            "fields": "wall,can_post,is_closed,type,members_count,photo_100,description",
            "access_token": token_to_use,
            "v": "5.199"
        }

        data = None
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(api_host, params=params)
                data = res.json()
        except Exception as net_err:
            logger.warning(f"Network error on primary VK host: {net_err}")
            # Пробуем резервный хост api.vk.ru
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    res = await client.get("https://api.vk.ru/method/groups.getById", params=params)
                    data = res.json()
            except Exception:
                pass

        # Если токен аккаунта выдал ошибку (например код 9 Flood control или код 5 Token invalid)
        if not data or "error" in data:
            err = data.get("error", {}) if data else {}
            err_code = err.get("error_code")
            logger.warning(f"VK groups.getById error with user token: {err}")

            if err_code == 9:
                account_flood_control = True
                account_warning = "ВКонтакте временно включил Flood Control (ограничение частоты запросов) для этого личного аккаунта. Стена проверена через резервный канал."
            elif err_code == 5:
                account_warning = "Токен личного аккаунта недействителен или истек. Рекомендуется обновить аккаунт."

            # Пробуем fallback токен
            if fallback_token and fallback_token != account_token:
                logger.info("Attempting groups check using fallback system token...")
                try:
                    params["access_token"] = fallback_token
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        res = await client.get(api_host, params=params)
                        data = res.json()
                        if "response" in data:
                            is_using_fallback = True
                except Exception as fb_err:
                    logger.warning(f"Fallback token error: {fb_err}")

        if not data or "error" in data:
            err = data.get("error", {}) if data else {}
            err_code = err.get("error_code", "Unknown")
            err_msg = err.get("error_msg", "Не удалось получить ответ от VK API")
            raise Exception(f"Ошибка VK API ({err_code}): {err_msg}")

        items = data.get("response", [])
        output = []

        for g in items:
            g_id = g.get("id")
            g_type = g.get("type", "group")  # group, page, event
            wall = g.get("wall", 0)          # 0=disabled, 1=open, 2=limited, 3=closed
            is_closed = g.get("is_closed", 0)# 0=open, 1=closed, 2=private

            if is_using_fallback:
                # Если используется fallback токен бота:
                # В открытой группе (type == 'group', wall == 1, is_closed == 0) любой пользователь может писать на стене!
                can_post = 1 if (wall == 1 and g_type == "group" and is_closed == 0) else 0
                can_publish = (can_post == 1)
            else:
                can_post = g.get("can_post", 0)
                can_publish = (can_post == 1)

            if can_publish:
                status_type = "open"
                status_text = "Стена открыта (публикация без одобрения)"
            elif g_type == "page":
                status_type = "page_suggest"
                status_text = "Паблик (только «Предложить новость»)"
            elif wall == 2:
                status_type = "limited"
                status_text = "Ограниченная стена (только администрация)"
            elif wall in (0, 3):
                status_type = "disabled"
                status_text = "Стена выключена"
            elif is_closed in (1, 2):
                status_type = "closed_group"
                status_text = "Закрытая/частная группа"
            else:
                status_type = "forbidden"
                status_text = "Публикация недоступна"

            screen_name = g.get("screen_name") or f"club{g_id}"
            output.append({
                "id": g_id,
                "name": g.get("name", f"Группа {g_id}"),
                "screen_name": screen_name,
                "type": g_type,
                "wall": wall,
                "can_post": can_post,
                "can_publish": can_publish,
                "status_type": status_type,
                "status_text": status_text,
                "is_closed": is_closed,
                "members_count": g.get("members_count", 0),
                "photo": g.get("photo_100", ""),
                "url": f"https://vk.com/{screen_name}"
            })

        return {
            "groups": output,
            "account_flood_control": account_flood_control,
            "account_warning": account_warning,
            "is_using_fallback": is_using_fallback
        }

    @staticmethod
    async def upload_wall_photo_from_account(account_token: str, image_path: str) -> str:
        """
        Загружает изображение от имени личного аккаунта для прикрепления к посту на стене.
        Возвращает VK attachment: photo{owner_id}_{photo_id}
        """
        temp_file = None
        try:
            # Если это веб-URL или относительный путь
            if image_path.startswith("http://") or image_path.startswith("https://"):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(image_path)
                    if resp.status_code == 200:
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                        temp_file.write(resp.content)
                        temp_file.close()
                        local_path = temp_file.name
                    else:
                        raise Exception(f"Не удалось скачать изображение по ссылке ({resp.status_code})")
            else:
                # Локальный путь к медиа
                if image_path.startswith("/media/"):
                    local_path = image_path.replace("/media/", "/app/media/")
                elif not os.path.isabs(image_path):
                    local_path = os.path.join("/app/media", image_path)
                else:
                    local_path = image_path

                if not os.path.exists(local_path):
                    # Пробуем путь относительно проекта, если запускается локально
                    alt_path = os.path.join(os.getcwd(), "media", image_path.lstrip("/media/").lstrip("/"))
                    if os.path.exists(alt_path):
                        local_path = alt_path
                    else:
                        raise Exception(f"Файл изображения не найден: {local_path}")

            # 1. Получаем upload_url для фото на стену пользователя
            url = "https://api.vk.ru/method/photos.getWallUploadServer"
            params = {
                "access_token": account_token,
                "v": "5.199"
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(url, params=params)
                data = res.json()
                if "response" not in data or "upload_url" not in data["response"]:
                    raise Exception(f"Ошибка получения сервера загрузки фото VK: {data}")
                upload_url = data["response"]["upload_url"]

                # 2. Загружаем файл фото
                with open(local_path, "rb") as f:
                    res_upload = await client.post(upload_url, files={"photo": f})
                    upload_data = res_upload.json()

                # 3. Сохраняем фото
                save_url = "https://api.vk.ru/method/photos.saveWallPhoto"
                save_params = {
                    "access_token": account_token,
                    "v": "5.199",
                    "photo": upload_data.get("photo"),
                    "server": upload_data.get("server"),
                    "hash": upload_data.get("hash")
                }
                res_save = await client.post(save_url, data=save_params)
                save_data = res_save.json()

                if "response" not in save_data or len(save_data["response"]) == 0:
                    raise Exception(f"Ошибка сохранения фото в VK: {save_data}")

                photo_info = save_data["response"][0]
                return f"photo{photo_info['owner_id']}_{photo_info['id']}"

        finally:
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass

    @staticmethod
    async def publish_post_to_group(
        account_token: str,
        group_id: int,
        message: str,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Публикует запись на стене группы от имени личного аккаунта (from_group=0).
        Возвращает post_id и ссылку на созданный пост.
        """
        url = "https://api.vk.ru/method/wall.post"
        # Для сообществ owner_id всегда отрицательный
        target_owner_id = -abs(group_id)

        params = {
            "owner_id": target_owner_id,
            "from_group": 0,  # строго от имени личного аккаунта пользователя!
            "message": message or "",
            "access_token": account_token,
            "v": "5.199"
        }

        if attachments:
            params["attachments"] = ",".join(attachments)

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(url, data=params)
                res_json = resp.json()

            if "error" in res_json:
                err = res_json["error"]
                code = err.get("error_code")
                msg = err.get("error_msg", "Неизвестная ошибка")

                if code == 214:
                    err_desc = "Стена сообщества ограничена или закрыта для публикаций (Код 214)"
                elif code == 14:
                    err_desc = f"ВКонтакте запросил капчу (Код 14): {msg}"
                elif code == 15:
                    err_desc = f"Доступ запрещен (Код 15): {msg}"
                elif code == 9:
                    err_desc = "Слишком много однотипных действий за короткое время (Код 9, антиспам VK)"
                elif code == 5:
                    err_desc = "Авторизация не удалась: недействительный токен аккаунта (Код 5)"
                else:
                    err_desc = f"Ошибка VK ({code}): {msg}"

                return {
                    "success": False,
                    "error_code": code,
                    "error_message": err_desc
                }

            post_id = res_json["response"]["post_id"]
            post_url = f"https://vk.com/wall{target_owner_id}_{post_id}"

            return {
                "success": True,
                "post_id": post_id,
                "post_url": post_url
            }

        except Exception as e:
            logger.error(f"HTTP error during wall.post to group {group_id}: {e}")
            return {
                "success": False,
                "error_code": -1,
                "error_message": f"Сетевая ошибка при отправке: {str(e)}"
            }

    @staticmethod
    async def refresh_posts_metrics(
        account_token: str,
        history_items: List[VkGroupPostingHistory],
        db: Session
    ) -> Dict[str, Any]:
        """
        Пакетно опрашивает VK API wall.getById и обновляет метрики просмотров, лайков и репостов.
        """
        if not history_items or not account_token:
            return {"updated": 0, "deleted": 0}

        # Фильтруем только посты с post_id
        valid_items = [item for item in history_items if item.post_id and item.group_id]
        if not valid_items:
            return {"updated": 0, "deleted": 0}

        updated_count = 0
        deleted_count = 0

        # VK API wall.getById поддерживает до 100 постов за 1 вызов
        batch_size = 100
        for i in range(0, len(valid_items), batch_size):
            batch = valid_items[i:i + batch_size]
            post_keys = [f"-{abs(item.group_id)}_{item.post_id}" for item in batch]

            url = "https://api.vk.ru/method/wall.getById"
            params = {
                "posts": ",".join(post_keys),
                "extended": 0,
                "access_token": account_token,
                "v": "5.199"
            }

            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.get(url, params=params)
                    data = resp.json()

                if "error" in data:
                    logger.warning(f"wall.getById error: {data['error']}")
                    continue

                returned_posts = data.get("response", [])
                
                # Создаем мапу найденных постов: key = (group_id, post_id)
                post_map = {}
                for p in returned_posts:
                    p_id = p.get("id")
                    owner_id = abs(p.get("owner_id", 0))
                    post_map[(owner_id, p_id)] = p

                now = utc_now()
                for item in batch:
                    key = (abs(item.group_id), item.post_id)
                    if key in post_map:
                        p_data = post_map[key]
                        item.views_count = p_data.get("views", {}).get("count", 0)
                        item.likes_count = p_data.get("likes", {}).get("count", 0)
                        item.reposts_count = p_data.get("reposts", {}).get("count", 0)
                        item.comments_count = p_data.get("comments", {}).get("count", 0)
                        item.status = "published"
                        item.last_checked_at = now
                        item.updated_at = now
                        db.add(item)
                        updated_count += 1
                    else:
                        # Пост не вернулся из API (удален админом группы или автором)
                        if item.status == "published":
                            item.status = "deleted"
                            item.last_checked_at = now
                            item.updated_at = now
                            db.add(item)
                            deleted_count += 1

                db.commit()

            except Exception as e:
                logger.error(f"Error refreshing batch of wall posts: {e}")

        return {"updated": updated_count, "deleted": deleted_count}


vk_group_posting_service = VkGroupPostingService()
