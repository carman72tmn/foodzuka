import os
import time
import logging
import hashlib
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

# Папка для локального кэширования медиа/изображений сообщений
CHAT_CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../media/chat_cache"))
# Регламент хранения кэша изображений сообщений: 48 дней
CACHE_RETENTION_DAYS = 48
CACHE_RETENTION_SECONDS = CACHE_RETENTION_DAYS * 86400

os.makedirs(CHAT_CACHE_DIR, exist_ok=True)


class ChatMediaCacheService:
    """Сервис кэширования и управления медиафайлами и изображениями чатов"""

    @staticmethod
    def extract_attachments_from_payload(payload: Optional[Dict[str, Any]], channel: str) -> List[Dict[str, Any]]:
        """Извлечение списка вложений (изображений) из raw payload сообщения"""
        if not payload or not isinstance(payload, dict):
            return []

        attachments: List[Dict[str, Any]] = []

        # 1. Формат ВКонтакте (VK API)
        vk_attachments = payload.get("attachments") or []
        if isinstance(vk_attachments, list):
            for att in vk_attachments:
                if not isinstance(att, dict):
                    continue
                att_type = att.get("type")
                if att_type == "photo":
                    photo = att.get("photo", {})
                    sizes = photo.get("sizes", [])
                    url = None
                    if sizes and isinstance(sizes, list):
                        # Выбираем наибольший размер по площади или типу
                        best_size = max(
                            sizes, 
                            key=lambda s: (s.get("width", 0) * s.get("height", 0)) if (s.get("width") and s.get("height")) else (100 if s.get("type") in ["w", "z", "y", "x", "m"] else 10)
                        )
                        url = best_size.get("url")
                    if not url:
                        url = photo.get("orig_photo", {}).get("url") or photo.get("url")
                    if url:
                        attachments.append({
                            "type": "image",
                            "url": url,
                            "preview_url": url,
                            "title": photo.get("text") or "Фото ВКонтакте"
                        })
                elif att_type == "sticker":
                    sticker = att.get("sticker", {})
                    images = sticker.get("images", []) or sticker.get("images_with_background", [])
                    if images and isinstance(images, list):
                        best = images[-1].get("url")
                        if best:
                            attachments.append({
                                "type": "image",
                                "url": best,
                                "preview_url": best,
                                "title": "Стикер ВКонтакте"
                            })
                elif att_type == "gift":
                    gift = att.get("gift", {})
                    thumb = gift.get("thumb_512") or gift.get("thumb_256") or gift.get("thumb_96") or gift.get("thumb_48")
                    if thumb:
                        attachments.append({
                            "type": "image",
                            "url": thumb,
                            "preview_url": thumb,
                            "title": "Подарок ВКонтакте"
                        })
                elif att_type == "doc":
                    doc = att.get("doc", {})
                    if doc.get("ext") in ["jpg", "jpeg", "png", "gif", "webp"] or doc.get("type") in [4, 3, "image"]:
                        url = doc.get("url")
                        preview = doc.get("preview", {}).get("photo", {}).get("sizes", [{}])[-1].get("src") or url
                        if url:
                            attachments.append({
                                "type": "image",
                                "url": url,
                                "preview_url": preview,
                                "title": doc.get("title") or "Изображение"
                            })

        # 2. Формат MAX Messenger / PyMax
        max_attaches = payload.get("attaches") or payload.get("attachments") or payload.get("files") or []
        if isinstance(max_attaches, list):
            for att in max_attaches:
                if not isinstance(att, dict):
                    continue
                url = att.get("url") or att.get("image_url") or att.get("download_url") or att.get("preview_url") or att.get("src")
                if url:
                    attachments.append({
                        "type": "image",
                        "url": url,
                        "preview_url": att.get("preview_url") or url,
                        "title": att.get("name") or "Изображение MAX"
                    })
        elif payload.get("image_url") or payload.get("photo_url") or payload.get("download_url"):
            url = payload.get("image_url") or payload.get("photo_url") or payload.get("download_url")
            attachments.append({
                "type": "image",
                "url": url,
                "preview_url": url,
                "title": "Изображение MAX"
            })

        # 3. Формат Telegram
        if payload.get("photo"):
            tg_photos = payload.get("photo")
            if isinstance(tg_photos, list) and len(tg_photos) > 0:
                largest = tg_photos[-1]
                url = largest.get("url") or largest.get("file_path")
                if url:
                    attachments.append({
                        "type": "image",
                        "url": url,
                        "preview_url": url,
                        "title": "Фото Telegram"
                    })

        # 4. Пересланные сообщения с вложениями (VK / MAX)
        fwd = payload.get("fwd_messages") or payload.get("reply_message")
        if fwd:
            fwd_list = fwd if isinstance(fwd, list) else [fwd]
            for f in fwd_list:
                if isinstance(f, dict):
                    sub_att = ChatMediaCacheService.extract_attachments_from_payload(f, channel)
                    attachments.extend(sub_att)

        return attachments


    @staticmethod
    def cleanup_expired_cache(days: int = CACHE_RETENTION_DAYS) -> Dict[str, Any]:
        """
        Удаление кэшированных файлов изображений старше 48 дней.
        Запускается регулярно воркером или по требованию.
        """
        retention_seconds = days * 86400
        now = time.time()
        deleted_files = 0
        freed_bytes = 0

        if not os.path.exists(CHAT_CACHE_DIR):
            return {"deleted_files": 0, "freed_bytes": 0}

        try:
            for root, _, files in os.walk(CHAT_CACHE_DIR):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    try:
                        stat = os.stat(filepath)
                        file_age = now - stat.st_mtime
                        if file_age > retention_seconds:
                            file_size = stat.st_size
                            os.remove(filepath)
                            deleted_files += 1
                            freed_bytes += file_size
                    except Exception as fe:
                        logger.warning(f"Error checking cache file {filepath}: {fe}")

            logger.info(f"Chat media cache cleanup: removed {deleted_files} files older than {days} days ({freed_bytes / (1024*1024):.2f} MB freed).")
        except Exception as e:
            logger.error(f"Error during chat media cache cleanup: {e}")

        return {
            "deleted_files": deleted_files,
            "freed_bytes": freed_bytes,
            "retention_days": days
        }


chat_media_cache_service = ChatMediaCacheService()
