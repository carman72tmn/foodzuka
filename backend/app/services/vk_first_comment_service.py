import re
import logging
import random
import httpx
from sqlmodel import Session, select
from app.models.vk_first_comment_settings import VkFirstCommentSettings
from app.models.vk_bot_connection import VkBotConnection

logger = logging.getLogger(__name__)

class VkFirstCommentService:
    """Сервис для автокомментирования новых постов ВКонтакте (первокоммент)"""

    def parse_attachments_from_comment(self, comment_text: str, post_text: str) -> tuple[str, str | None]:
        """
        Парсит теги вложений из текста комментария, сопоставляет их с текстом поста
        и возвращает очищенный текст комментария и строку вложений для VK API.
        """
        attachments = []
        cleaned_comment = comment_text
        
        post_text_lower = post_text.lower()
        # Разделяем пост на слова для точного совпадения (полные слова)
        post_words = set(re.findall(r'\b[a-zA-Z0-9а-яА-ЯёЁ]+\b', post_text_lower))

        # 1. Случайное вложение: [rand]photo-XXX_XX|photo-XXX_XX[/rand]
        rand_pattern = re.compile(r'\[rand\](.*?)\[/rand\]', re.IGNORECASE)
        for match in rand_pattern.finditer(comment_text):
            content = match.group(1)
            if content:
                options = [opt.strip() for opt in content.split('|') if opt.strip()]
                if options:
                    attachments.append(random.choice(options))
        cleaned_comment = rand_pattern.sub('', cleaned_comment)

        # 2. Вложение по ключевым словам (полные слова): [keyText]photo-XXX_XX|прикол,смешно[/keyText]
        keytext_pattern = re.compile(r'\[keyText\](.*?)\[/keyText\]', re.IGNORECASE)
        for match in keytext_pattern.finditer(comment_text):
            content = match.group(1)
            if '|' in content:
                attachment, keywords_str = content.split('|', 1)
                keywords = [kw.strip().lower() for kw in keywords_str.split(',') if kw.strip()]
                if any(kw in post_words for kw in keywords):
                    attachments.append(attachment.strip())
        cleaned_comment = keytext_pattern.sub('', cleaned_comment)

        # 3. Вложение по ключевым словам (по вхождению): [keyTextEntry]photo-XXX_XX|прикол,смеш[/keyTextEntry]
        keytext_entry_pattern = re.compile(r'\[keyTextEntry\](.*?)\[/keyTextEntry\]', re.IGNORECASE)
        for match in keytext_entry_pattern.finditer(comment_text):
            content = match.group(1)
            if '|' in content:
                attachment, keywords_str = content.split('|', 1)
                keywords = [kw.strip().lower() for kw in keywords_str.split(',') if kw.strip()]
                if any(kw in post_text_lower for kw in keywords):
                    attachments.append(attachment.strip())
        cleaned_comment = keytext_entry_pattern.sub('', cleaned_comment)

        # Убираем лишние пробелы, которые могли остаться после удаления тегов
        cleaned_comment = re.sub(r'[ \t]+', ' ', cleaned_comment).strip()
        
        attachments_str = ','.join(attachments) if attachments else None
        return cleaned_comment, attachments_str

    async def process_new_post(self, db: Session, obj: dict, bot_token: str | None, group_id: int | None):
        """Обрабатывает событие wall_post_new и оставляет первый комментарий с учетом детальных настроек"""
        if not group_id:
            logger.warning("FirstCommentBot: group_id is missing in event")
            return

        post_id = obj.get("id")
        owner_id = obj.get("owner_id")  # для сообщества отрицательный, например, -group_id
        from_id = obj.get("from_id")
        post_text = obj.get("text", "")

        if not post_id or owner_id is None:
            logger.warning("FirstCommentBot: post_id or owner_id is missing in event object")
            return

        # Ищем настройки первокоммента для данной группы ВК.
        connection = db.exec(
            select(VkBotConnection).where(VkBotConnection.vk_group_id == group_id, VkBotConnection.is_active == True)
        ).first()

        if not connection:
            logger.warning(f"FirstCommentBot: No active VkBotConnection found for group {group_id}")
            return

        # Ищем настройки бота
        settings = db.exec(
            select(VkFirstCommentSettings).where(VkFirstCommentSettings.vk_bot_connection_id == connection.id)
        ).first()

        if not settings or not settings.is_active:
            logger.info(f"FirstCommentBot: Bot is disabled or not configured for connection {connection.name} (ID: {connection.id})")
            return

        # 1. Фильтр: Исключить репосты
        if settings.exclude_reposts and obj.get("copy_history"):
            logger.info(f"FirstCommentBot: Post {post_id} is a repost (copy_history is present), but exclude_reposts is active. Skipping.")
            return

        # 2. Фильтр: Игнорировать посты без текста
        if settings.ignore_empty_text and not post_text.strip():
            logger.info(f"FirstCommentBot: Post {post_id} has empty text (ignore_empty_text is True). Skipping.")
            return

        # 3. Фильтр по автору поста (post_type_filter)
        is_from_group = (from_id == owner_id)
        
        if settings.post_type_filter == "only_group" and not is_from_group:
            logger.info(f"FirstCommentBot: Post {post_id} author from_id={from_id} is not equal to owner_id={owner_id} (only_group filter active). Skipping.")
            return
        elif settings.post_type_filter == "only_users" and is_from_group:
            logger.info(f"FirstCommentBot: Post {post_id} author is group (from_id={from_id} == owner_id={owner_id}), but only_users filter active. Skipping.")
            return

        # 4. Фильтр по ключевым словам (должны содержать)
        if settings.include_keywords:
            keywords = [k.strip().lower() for k in settings.include_keywords.split(",") if k.strip()]
            if keywords:
                text_lower = post_text.lower()
                if not any(kw in text_lower for kw in keywords):
                    logger.info(f"FirstCommentBot: Post {post_id} text '{post_text[:50]}...' does not contain any of required keywords {keywords}. Skipping.")
                    return

        # 5. Фильтр по стоп-словам (не должны содержать)
        if settings.exclude_keywords:
            stop_words = [w.strip().lower() for w in settings.exclude_keywords.split(",") if w.strip()]
            if stop_words:
                text_lower = post_text.lower()
                found_stop_words = [sw for sw in stop_words if sw in text_lower]
                if found_stop_words:
                    logger.info(f"FirstCommentBot: Post {post_id} contains exclude keywords {found_stop_words} (stop words). Skipping.")
                    return

        # Проверка списка комментариев
        comments = settings.comments
        if not comments:
            logger.info(f"FirstCommentBot: Comments list is empty for connection {connection.name}")
            return

        # Выбираем случайный комментарий
        random_comment = random.choice(comments)
        if not random_comment or not random_comment.strip():
            logger.info("FirstCommentBot: Selected random comment is empty")
            return

        # Парсим вложения и очищаем текст от вложений
        cleaned_comment, attachments_str = self.parse_attachments_from_comment(random_comment, post_text)

        # Токен
        token = settings.vk_bot_token or connection.vk_bot_token or bot_token
        if not token:
            logger.error(f"FirstCommentBot: No bot token found for connection {connection.name}")
            return

        # 6. Задержка публикации
        delay = settings.delay_seconds
        if settings.delay_max > settings.delay_min and settings.delay_max > 0:
            delay = random.randint(settings.delay_min, settings.delay_max)

        if delay > 0:
            logger.info(f"FirstCommentBot: Delaying comment for {delay} seconds...")
            import asyncio
            await asyncio.sleep(delay)

        # Оставляем комментарий через VK API
        url = "https://api.vk.ru/method/wall.createComment"
        params = {
            "owner_id": owner_id,
            "post_id": post_id,
            "from_group": group_id,  # Оставляем от имени группы
            "message": cleaned_comment,
            "access_token": token,
            "v": "5.199"
        }
        if attachments_str:
            params["attachments"] = attachments_str

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, data=params)
                data = resp.json()
                if "error" in data:
                    logger.error(f"FirstCommentBot: VK API error in wall.createComment: {data['error']}")
                else:
                    comment_id = data.get("response", {}).get("comment_id")
                    logger.info(f"FirstCommentBot: Successfully commented post {post_id} in group {group_id}. Comment ID: {comment_id}")
            except Exception as e:
                logger.error(f"FirstCommentBot: Exception while calling wall.createComment: {e}")

vk_first_comment_service = VkFirstCommentService()
