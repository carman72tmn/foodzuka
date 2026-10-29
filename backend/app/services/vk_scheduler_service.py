import os
import httpx
import logging
import tempfile
import asyncio
from datetime import datetime
from sqlmodel import Session, select
from app.models.vk_post_scheduler import VkPostScheduler
from app.models.vk_bot_connection import VkBotConnection

logger = logging.getLogger(__name__)

class VkSchedulerService:
    """Сервис для управления и выполнения отложенных публикаций ВК"""

    async def upload_vk_wall_photo(self, bot_token: str, image_path: str, group_id: int) -> str:
        """Загружает картинку на стену сообщества ВК и возвращает attachment-строку"""
        temp_file = None
        try:
            if image_path.startswith("http://") or image_path.startswith("https://"):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(image_path)
                    if resp.status_code == 200:
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                        temp_file.write(resp.content)
                        temp_file.close()
                        image_path = temp_file.name
                    else:
                        raise Exception(f"Failed to download image: {resp.status_code}")

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
                    raise Exception(f"Failed to get wall upload server: {data}")
                upload_url = data["response"]["upload_url"]

                # 2. Загружаем файл
                with open(image_path, "rb") as f:
                    res_upload = await client.post(upload_url, files={"photo": f})
                    upload_data = res_upload.json()

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
                    raise Exception(f"Failed to save wall photo: {save_data}")
                
                photo_info = save_data["response"][0]
                return f"photo{photo_info['owner_id']}_{photo_info['id']}"
        finally:
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass

    async def upload_vk_story_photo(self, bot_token: str, image_path: str, group_id: int, link_text: str = None, link_url: str = None) -> str:
        """Загружает картинку в истории группы ВК"""
        temp_file = None
        try:
            if image_path.startswith("http://") or image_path.startswith("https://"):
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(image_path)
                    if resp.status_code == 200:
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                        temp_file.write(resp.content)
                        temp_file.close()
                        image_path = temp_file.name
                    else:
                        raise Exception(f"Failed to download story image: {resp.status_code}")

            # 1. Получаем upload_url для историй
            url = "https://api.vk.ru/method/stories.getPhotoUploadServer"
            params = {
                "access_token": bot_token,
                "v": "5.199",
                "group_id": group_id,
                "add_to_news": 1
            }
            # Поддерживаем стикеры со ссылками на истории
            if link_url:
                params["link_text"] = link_text or "more"
                params["link_url"] = link_url

            async with httpx.AsyncClient() as client:
                res = await client.get(url, params=params)
                data = res.json()
                if "response" not in data:
                    raise Exception(f"Failed to get story upload server: {data}")
                upload_url = data["response"]["upload_url"]

                # 2. Загружаем файл истории (ВК требует ключ 'file' для историй!)
                with open(image_path, "rb") as f:
                    res_upload = await client.post(upload_url, files={"file": f})
                    upload_data = res_upload.text

                # 3. Сохраняем историю
                save_url = "https://api.vk.ru/method/stories.save"
                save_params = {
                    "access_token": bot_token,
                    "v": "5.199",
                    "upload_results": upload_data
                }
                res_save = await client.post(save_url, data=save_params)
                save_data = res_save.json()
                
                if "response" not in save_data:
                    raise Exception(f"Failed to save VK story: {save_data}")
                
                return "story"
        finally:
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass

    async def execute_publication(self, db: Session, job: VkPostScheduler) -> bool:
        """Публикует пост или историю согласно настройкам"""
        try:
            conn = db.get(VkBotConnection, job.vk_bot_connection_id)
            if not conn or not conn.is_active:
                raise Exception("Active connection not found for publication job")

            group_id = conn.vk_group_id
            bot_token = conn.vk_bot_token
            user_auth_token = conn.vk_user_token or bot_token

            local_image_path = job.media_url
            if local_image_path and not local_image_path.startswith("http"):
                if local_image_path.startswith("/media/"):
                    local_image_path = local_image_path.replace("/media/", "/app/media/")
                else:
                    local_image_path = os.path.join("/app/media", local_image_path)

            if job.type == "story":
                if not local_image_path:
                    raise Exception("Media is required for stories")
                
                logger.info(f"Publishing VK story for connection {conn.name}...")
                await self.upload_vk_story_photo(
                    user_auth_token,
                    local_image_path,
                    group_id,
                    link_text=job.button_text,
                    link_url=job.link_url
                )
                logger.info(f"VK story successfully published for connection {conn.name}")
            else:
                logger.info(f"Publishing VK wall post for connection {conn.name}...")
                attachments = []
                
                # Загружаем картинку, если она есть
                if local_image_path:
                    photo_attachment = await self.upload_vk_wall_photo(user_auth_token, local_image_path, group_id)
                    attachments.append(photo_attachment)

                # Добавляем ссылку-кнопку/сниппет, если есть
                if job.link_url:
                    attachments.append(job.link_url)

                # Публикуем запись на стене группы
                url = "https://api.vk.ru/method/wall.post"
                params = {
                    "owner_id": -group_id,
                    "from_group": 1,
                    "message": job.content_text or "",
                    "access_token": user_auth_token,
                    "v": "5.199"
                }
                if attachments:
                    params["attachments"] = ",".join(attachments)

                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, data=params)
                    res_json = resp.json()
                    if "error" in res_json:
                        raise Exception(f"VK API wall.post error: {res_json['error']}")
                    
                    post_id = res_json["response"]["post_id"]
                    logger.info(f"VK wall post successfully published: post_id={post_id}")

            job.status = "published"
            job.error_message = None
            db.add(job)
            db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to publish VK postponed job {job.id}: {e}", exc_info=True)
            job.status = "failed"
            job.error_message = str(e)
            db.add(job)
            db.commit()
            return False

    async def check_and_publish_pending(self, db: Session):
        """Сканирует и отправляет все запланированные публикации, время которых подошло"""
        now = datetime.utcnow()
        jobs = db.exec(
            select(VkPostScheduler)
            .where(VkPostScheduler.status == "pending")
            .where(VkPostScheduler.publish_at <= now)
        ).all()
        
        logger.info(f"VK Scheduler: Found {len(jobs)} pending publications to execute.")
        for job in jobs:
            await self.execute_publication(db, job)

vk_scheduler_service = VkSchedulerService()
