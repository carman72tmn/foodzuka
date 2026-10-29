import os
import re
import httpx
import logging
import asyncio
import tempfile
from datetime import datetime, timedelta, date, time, timezone
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from app.core.datetime_utils import utc_now
from app.models.vk_birthday_bot import VkBirthdayBot, VkBirthdayPost
from app.models.vk_bot_connection import VkBotConnection

logger = logging.getLogger(__name__)

class VkBirthdayService:
    """Сервис для работы с ботами дней рождения ВКонтакте"""

    async def get_group_birthdays_today(self, group_id: int, bot_token: str, local_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Получает именинников среди подписчиков сообщества ВКонтакте"""
        # Определяем текущую дату (день и месяц) по локальному часовому поясу
        if not local_date:
            local_date = date.today()
        today_day = local_date.day
        today_month = local_date.month
        
        url = "https://api.vk.ru/method/groups.getMembers"
        offset = 0
        count = 1000
        birthdays = []
        
        async with httpx.AsyncClient() as client:
            while True:
                params = {
                    "group_id": group_id,
                    "fields": "bdate,first_name,last_name,sex",
                    "offset": offset,
                    "count": count,
                    "access_token": bot_token,
                    "v": "5.199"
                }
                try:
                    resp = await client.get(url, params=params)
                    data = resp.json()
                    if "error" in data:
                        logger.error(f"VK API error in groups.getMembers for group {group_id}: {data['error']}")
                        break
                        
                    response = data.get("response", {})
                    items = response.get("items", [])
                    if not items:
                        break
                        
                    for member in items:
                        bdate_str = member.get("bdate")
                        if bdate_str:
                            # bdate может быть D.M.YYYY или D.M
                            parts = bdate_str.split('.')
                            if len(parts) >= 2:
                                try:
                                    day = int(parts[0])
                                    month = int(parts[1])
                                    if day == today_day and month == today_month:
                                        birthdays.append(member)
                                except ValueError:
                                    continue
                    
                    offset += count
                    if len(items) < count:
                        break
                    await asyncio.sleep(0.2)  # Защита от лимитов запросов VK API
                except Exception as e:
                    logger.error(f"Error fetching members for group {group_id}: {e}")
                    break
                    
        return birthdays

    async def upload_vk_wall_photo(self, bot_token: str, image_path: str, group_id: int) -> Optional[str]:
        """Загружает изображение на стену сообщества ВК и возвращает attachment-строку"""
        temp_file = None
        try:
            # Если это URL, скачиваем во временный файл
            if image_path.startswith("http://") or image_path.startswith("https://"):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(image_path)
                    if resp.status_code == 200:
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                        temp_file.write(resp.content)
                        temp_file.close()
                        image_path = temp_file.name
                    else:
                        logger.error(f"Failed to download image from {image_path}: status {resp.status_code}")
                        return None

            if not os.path.exists(image_path):
                logger.error(f"Image path does not exist: {image_path}")
                return None

            # 1. Получаем upload_url
            url = "https://api.vk.ru/method/photos.getWallUploadServer"
            params = {
                "access_token": bot_token,
                "v": "5.199",
                "group_id": group_id
            }
            async with httpx.AsyncClient() as client:
                res = await client.get(url, params=params)
                data = res.json()
                if "response" not in data:
                    logger.error(f"Failed to get wall upload server: {data}")
                    return None
                upload_url = data["response"]["upload_url"]

                # 2. Загружаем файл
                with open(image_path, "rb") as f:
                    res_upload = await client.post(upload_url, files={"photo": f})
                    try:
                        upload_data = res_upload.json()
                    except Exception as je:
                        logger.error(f"Failed to parse VK upload response as JSON. Status: {res_upload.status_code}, Text: '{res_upload.text[:500]}'")
                        raise je

                # 3. Сохраняем фото
                save_url = "https://api.vk.ru/method/photos.saveWallPhoto"
                save_params = {
                    "access_token": bot_token,
                    "v": "5.199",
                    "group_id": group_id,
                    "photo": upload_data.get("photo"),
                    "server": upload_data.get("server"),
                    "hash": upload_data.get("hash")
                }
                res_save = await client.post(save_url, data=save_params)
                save_data = res_save.json()
                
                if "response" not in save_data or len(save_data["response"]) == 0:
                    logger.error(f"Failed to save wall photo: {save_data}")
                    return None
                
                photo_info = save_data["response"][0]
                return f"photo{photo_info['owner_id']}_{photo_info['id']}"
                
        except Exception as e:
            logger.error(f"Error uploading VK wall photo: {e}", exc_info=True)
            return None
        finally:
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass

    async def publish_birthday_post(self, db: Session, bot: VkBirthdayBot) -> Optional[int]:
        """Выполняет проверку именинников и публикует поздравление на стене группы"""
        # 1. Получаем подключение к ВК
        conn = db.get(VkBotConnection, bot.vk_bot_connection_id)
        if not conn or not conn.is_active:
            logger.warning(f"Connection for bot {bot.id} is inactive or not found")
            return None
            
        group_id = conn.vk_group_id
        bot_token = bot.vk_bot_token or conn.vk_bot_token
        user_auth_token = conn.vk_user_token or bot_token
        
        # Получаем настройки часового пояса и текущее локальное время
        from app.core.datetime_utils import get_tz_name, get_local_now
        from datetime import timezone
        tz_name = get_tz_name(db)
        local_now = get_local_now(tz_name)
        local_date = local_now.date()
        
        # 2. Ищем именинников по локальной дате
        members = await self.get_group_birthdays_today(group_id, bot_token, local_date)
        if not members:
            logger.info(f"No birthdays today in VK group {group_id}. Skipping post.")
            # Все равно обновляем дату последнего запуска, чтобы не проверять повторно в течение дня
            bot.last_run_date = local_date.isoformat()
            db.add(bot)
            db.commit()
            return None
            
        # 3. Формируем список имен
        names_list = []
        for m in members:
            first_name = m.get("first_name", "")
            last_name = m.get("last_name", "")
            
            # Формат имени
            if bot.name_format == "name_only":
                name_text = first_name
            else:
                name_text = f"{first_name} {last_name}".strip()
                
            if not name_text:
                continue
                
            # Ссылка или нет
            if bot.make_links:
                names_list.append(f"[id{m['id']}|{name_text}]")
            else:
                names_list.append(name_text)
                
        names_str = ", ".join(names_list)
        
        # Подставляем имена в шаблон
        message_text = bot.message_template
        if "{names}" in message_text:
            message_text = message_text.replace("{names}", names_str)
        else:
            # Если тега нет, просто допишем в конец
            if bot.include_names:
                message_text += f"\n\nПоздравляем: {names_str}"
                
        # 4. Загружаем картинку, используя токен пользователя (vk_user_token) для обхода ограничений групп
        attachment = None
        if bot.image_url:
            # Относительные пути (например /media/...) превращаем в абсолютные локальные пути
            # На сервере медиа привязана к /app/media
            local_image_path = bot.image_url
            if local_image_path.startswith("/media/"):
                local_image_path = local_image_path.replace("/media/", "/app/media/")
            elif not local_image_path.startswith("http"):
                # На случай если это относительный путь без слэша
                local_image_path = os.path.join("/app/media", local_image_path)
                
            attachment = await self.upload_vk_wall_photo(user_auth_token, local_image_path, group_id)
            if not attachment:
                logger.warning(f"Failed to upload birthday image {bot.image_url} for group {group_id}. Posting text only.")

        # 5. Публикуем запись на стене
        url = "https://api.vk.ru/method/wall.post"
        import random
        params = {
            "owner_id": -group_id, # Минус означает стену сообщества
            "from_group": 1,
            "message": message_text,
            "access_token": user_auth_token, # Публикуем с тем же токеном, который загрузил картинку
            "v": "5.199"
        }
        if attachment:
            params["attachments"] = attachment
            
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, data=params)
                res_data = resp.json()
                if "error" in res_data:
                    logger.error(f"VK API wall.post error: {res_data['error']}")
                    return None
                    
                post_id = res_data["response"]["post_id"]
                logger.info(f"Birthday post published successfully. Group: {group_id}, Post ID: {post_id}")
                
                # Рассчитываем время автоудаления
                if bot.delete_mode == "exact_time" and bot.delete_time:
                    try:
                        t_parts = bot.delete_time.split(":")
                        del_hour = int(t_parts[0])
                        del_minute = int(t_parts[1])
                        # Удаление в тот же локальный день
                        import zoneinfo
                        delete_at_local = datetime.combine(local_date, time(del_hour, del_minute), tzinfo=zoneinfo.ZoneInfo(tz_name))
                        # Если время удаления уже прошло, переносим на завтра или удаляем через 10 минут
                        if delete_at_local <= local_now:
                            delete_at_local = local_now + timedelta(minutes=10)
                    except Exception as te:
                        logger.error(f"Error parsing delete_time {bot.delete_time}: {te}")
                        delete_at_local = local_now + timedelta(hours=12) # фолбэк
                else:
                    # По умолчанию интервал (в минутах)
                    interval = bot.delete_interval_minutes or 720
                    delete_at_local = local_now + timedelta(minutes=interval)
                
                # Сохраняем в БД в UTC-времени
                delete_at = delete_at_local.astimezone(timezone.utc).replace(tzinfo=None)
                created_at_utc = local_now.astimezone(timezone.utc).replace(tzinfo=None)
                
                # Создаем лог-запись поста
                new_post = VkBirthdayPost(
                    birthday_bot_id=bot.id,
                    vk_group_id=group_id,
                    post_id=post_id,
                    created_at=created_at_utc,
                    delete_at=delete_at,
                    is_deleted=False
                )
                db.add(new_post)
                
                # Обновляем состояние бота
                bot.last_run_date = local_date.isoformat()
                db.add(bot)
                
                db.commit()
                return post_id
                
            except Exception as e:
                logger.error(f"Failed to publish birthday post: {e}")
                return None

    async def delete_birthday_post(self, bot_token: str, group_id: int, post_id: int) -> bool:
        """Удаляет пост со стены сообщества ВКонтакте"""
        url = "https://api.vk.ru/method/wall.delete"
        params = {
            "owner_id": -group_id,
            "post_id": post_id,
            "access_token": bot_token,
            "v": "5.199"
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, data=params)
                res_data = resp.json()
                if "error" in res_data:
                    # Если пост уже был удален вручную, это не считается ошибкой для нас
                    err_code = res_data["error"].get("error_code")
                    if err_code in (15, 210, 212): # Access denied, post not found
                        logger.warning(f"Post {post_id} already deleted or inaccessible (VK code {err_code})")
                        return True
                    logger.error(f"VK API wall.delete error: {res_data['error']}")
                    return False
                return True
            except Exception as e:
                logger.error(f"Failed to delete wall post {post_id} in group {group_id}: {e}")
                return False

    async def run_birthday_bots_autopublish(self, db: Session):
        """Проверяет всех активных ботов именинников и публикует поздравления, если подошло время"""
        from app.core.datetime_utils import get_tz_name, get_local_now
        tz_name = get_tz_name(db)
        local_now = get_local_now(tz_name)
        today_str = local_now.date().isoformat()
        now = local_now  # Используем локальное время
        
        # Получаем всех активных ботов
        bots = db.exec(select(VkBirthdayBot).where(VkBirthdayBot.is_active == True)).all()
        
        for bot in bots:
            # Проверяем, не запускался ли уже сегодня
            if bot.last_run_date == today_str:
                continue
                
            # Проверяем время публикации
            if not bot.publish_time:
                continue
                
            try:
                t_parts = bot.publish_time.split(":")
                pub_hour = int(t_parts[0])
                pub_minute = int(t_parts[1])
                
                # Если текущее время на сервере прошло запланированное время публикации
                if now.hour > pub_hour or (now.hour == pub_hour and now.minute >= pub_minute):
                    logger.info(f"Triggering auto-publish for birthday bot {bot.id}")
                    # Запускаем публикацию
                    await self.publish_birthday_post(db, bot)
            except Exception as e:
                logger.error(f"Error checking publish time for bot {bot.id}: {e}")

    async def run_birthday_posts_autodelete(self, db: Session):
        """Проверяет опубликованные посты поздравлений и удаляет их, если наступило время удаления"""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Находим неделегированные посты, время удаления которых наступило
        posts = db.exec(
            select(VkBirthdayPost)
            .where(VkBirthdayPost.is_deleted == False)
            .where(VkBirthdayPost.delete_at <= now)
        ).all()
        
        for post in posts:
            # Находим токен подключения к группе
            bot = db.get(VkBirthdayBot, post.birthday_bot_id)
            if not bot:
                # Если бота удалили, просто пометим пост как удаленный в БД
                post.is_deleted = True
                db.add(post)
                db.commit()
                continue
                
            conn = db.get(VkBotConnection, bot.vk_bot_connection_id)
            if not conn:
                logger.error(f"No connection found for bot {bot.id} to delete post {post.post_id}")
                continue
                
            bot_token = bot.vk_bot_token or conn.vk_bot_token
            # Для удаления wall.delete нужен токен пользователя, так как токен группы возвращает ошибку 27
            user_auth_token = conn.vk_user_token or bot_token
            
            logger.info(f"Triggering auto-delete for birthday post {post.post_id} in group {post.vk_group_id}")
            success = await self.delete_birthday_post(user_auth_token, post.vk_group_id, post.post_id)
            if success:
                post.is_deleted = True
                db.add(post)
                db.commit()
                logger.info(f"Post {post.post_id} successfully marked as deleted in DB")

vk_birthday_service = VkBirthdayService()
