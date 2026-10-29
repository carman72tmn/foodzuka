import os
import httpx
import pytz
import logging
import asyncio
from io import BytesIO
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageOps
from sqlmodel import Session, select
from app.core.database import engine
from app.core.datetime_utils import utc_now
from app.models.vk_cover_bot import VkCoverBot, VkCoverSubscriberActivity
from app.models.vk_bot_connection import VkBotConnection

logger = logging.getLogger(__name__)

# Глобальный кэш для погоды и геокодинга
WEATHER_CACHE = {}  # city_name -> (temp_str, expire_time)
GEO_CACHE = {}      # city_name -> (lat, lon)

class VkCoverService:
    """Сервис генерации динамических обложек ВКонтакте"""

    def __init__(self):
        self.api_url = "https://api.vk.ru/method/"
        self.api_version = "5.199"
        self.font_path = "/app/media/fonts/Roboto-Bold.ttf" if os.path.exists("/app/media") else "./app/media/fonts/Roboto-Bold.ttf"
        if not os.path.exists(self.font_path):
            self.font_path = "./media/fonts/Roboto-Bold.ttf"
        
        # Убедимся, что директория для шрифта существует
        os.makedirs(os.path.dirname(self.font_path), exist_ok=True)

    async def download_font_if_not_exists(self):
        """Скачивает шрифт Roboto-Bold, если его нет в проекте"""
        if not os.path.exists(self.font_path):
            logger.info(f"Font file {self.font_path} not found. Downloading from GitHub...")
            url = "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.ttf"
            try:
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        with open(self.font_path, "wb") as f:
                            f.write(resp.content)
                        logger.info("Font downloaded successfully.")
                    else:
                        logger.error(f"Failed to download font: status {resp.status_code}")
            except Exception as e:
                logger.error(f"Error downloading font: {e}")

    async def get_coordinates(self, city_name: str) -> Optional[Tuple[float, float]]:
        """Преобразует название города в координаты lat/lon через Open-Meteo Geocoding API"""
        if city_name in GEO_CACHE:
            return GEO_CACHE[city_name]

        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": city_name, "count": 1, "language": "ru"}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    if results:
                        lat = results[0]["latitude"]
                        lon = results[0]["longitude"]
                        GEO_CACHE[city_name] = (lat, lon)
                        return lat, lon
        except Exception as e:
            logger.error(f"Geocoding error for city '{city_name}': {e}")
        
        return None

    async def get_weather(self, city_name: str) -> str:
        """Получает текущую погоду для города через Open-Meteo API"""
        now = datetime.now()
        if city_name in WEATHER_CACHE:
            temp_str, expire = WEATHER_CACHE[city_name]
            if now < expire:
                return temp_str

        # 1. Получаем координаты города
        coords = await self.get_coordinates(city_name)
        if not coords:
            return f"{city_name}: ?°C"

        lat, lon = coords
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    current = data.get("current_weather", {})
                    temp = current.get("temperature")
                    if temp is not None:
                        # Форматируем знак
                        sign = "+" if temp > 0 else ""
                        temp_str = f"{city_name}: {sign}{int(temp)}°C"
                        # Кэшируем на 15 минут
                        WEATHER_CACHE[city_name] = (temp_str, now + timedelta(minutes=15))
                        return temp_str
        except Exception as e:
            logger.error(f"Weather fetch error for {city_name} (coords: {lat}, {lon}): {e}")

        return f"{city_name}: ?°C"

    async def update_subscriber_activity(self, db: Session, group_id: int, bot_token: str):
        """Сканирует стену группы, считает лайки и комментарии за 7 дней, кэширует топ-1 активного подписчика"""
        logger.info(f"Starting activity calculation for group {group_id}")
        
        # ????? wall.get ??????? ???????????????? ????? (? ????????? ??????? VK ?????????? Error 27)
        user_token = None
        try:
            from app.models.chat import MultichatAccount
            from app.models.vk_bot_connection import VkBotConnection
            conn = db.exec(select(VkBotConnection).where(VkBotConnection.vk_group_id == group_id)).first()
            if conn and conn.vk_user_token:
                user_token = conn.vk_user_token
            if not user_token:
                vk_acc = db.exec(select(MultichatAccount).where(MultichatAccount.channel == "vk_user", MultichatAccount.status == "active")).first()
                if vk_acc and vk_acc.token:
                    user_token = vk_acc.token
        except Exception as e:
            logger.debug(f"Error fetching user token for cover activity: {e}")

        # ??????? ????????? ?????????? ?? ????????? ??????? vk_activities (??????? ??? ??????? VK API)
        try:
            from app.models.vk_activity import VkActivity
            from app.models.vk_user import VkUser
            from sqlmodel import func
            cutoff = datetime.utcnow() - timedelta(days=7)
            local_top = db.exec(
                select(VkActivity.vk_id, func.sum(VkActivity.points).label("total_pts"))
                .where(VkActivity.created_at >= cutoff)
                .group_by(VkActivity.vk_id)
                .order_by(func.sum(VkActivity.points).desc())
                .limit(5)
            ).all()

            if local_top and len(local_top) > 0:
                user_ids_str = ",".join(str(row[0]) for row in local_top if row[0] > 0)
                if user_ids_str:
                    async with httpx.AsyncClient() as u_client:
                        resp_u = await u_client.get(
                            "https://api.vk.ru/method/users.get",
                            params={"user_ids": user_ids_str, "fields": "photo_100,first_name,last_name", "access_token": bot_token, "v": self.api_version}
                        )
                        u_data = resp_u.json().get("response", [])
                        if u_data:
                            # ??????? ?????? ?????????? ??? ??????
                            old_acts = db.exec(select(VkCoverSubscriberActivity).where(VkCoverSubscriberActivity.vk_group_id == group_id)).all()
                            for old in old_acts:
                                db.delete(old)
                            db.commit()

                            pts_map = {row[0]: int(row[1] or 0) for row in local_top}
                            for u in u_data:
                                uid = u["id"]
                                db.add(VkCoverSubscriberActivity(
                                    vk_group_id=group_id,
                                    vk_user_id=uid,
                                    first_name=u.get("first_name", ""),
                                    last_name=u.get("last_name", ""),
                                    avatar_url=u.get("photo_100"),
                                    score=pts_map.get(uid, 0),
                                    updated_at=datetime.utcnow()
                                ))
                            db.commit()
                            logger.info(f"Successfully cached top active subscribers for group {group_id} from local vk_activities ({len(u_data)} users)")
                            return
        except Exception as local_err:
            logger.debug(f"Local vk_activities check skipped: {local_err}")

        token_to_use = user_token or bot_token
        url_posts = "https://api.vk.ru/method/wall.get"
        params_posts = {
            "owner_id": -group_id,
            "count": 25,
            "access_token": token_to_use,
            "v": self.api_version
        }
        
        scores = {}  # vk_user_id -> score
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # 1. Получаем последние посты
                resp = await client.get(url_posts, params=params_posts)
                data = resp.json()
                if "error" in data:
                    logger.error(f"VK API error in wall.get: {data['error']}")
                    return
                
                posts = data.get("response", {}).get("items", [])
                
                # 2. Обрабатываем каждый пост
                for post in posts:
                    # Проверяем дату поста (если он старше 7 дней, пропускаем)
                    post_date = datetime.utcfromtimestamp(post.get("date", 0))
                    if post_date < seven_days_ago:
                        continue
                    
                    post_id = post["id"]
                    
                    # Получаем лайки поста
                    url_likes = "https://api.vk.ru/method/likes.getList"
                    params_likes = {
                        "type": "post",
                        "owner_id": -group_id,
                        "item_id": post_id,
                        "filter": "likes",
                        "count": 100,
                        "access_token": bot_token,
                        "v": self.api_version
                    }
                    resp_likes = await client.get(url_likes, params=params_likes)
                    likes_data = resp_likes.json()
                    if "response" in likes_data:
                        for user_id in likes_data["response"].get("items", []):
                            if user_id > 0:  # Игнорируем группы
                                scores[user_id] = scores.get(user_id, 0) + 1
                    
                    # Получаем комментарии поста
                    url_comments = "https://api.vk.ru/method/wall.getComments"
                    params_comments = {
                        "owner_id": -group_id,
                        "post_id": post_id,
                        "count": 100,
                        "access_token": bot_token,
                        "v": self.api_version
                    }
                    resp_comments = await client.get(url_comments, params=params_comments)
                    comments_data = resp_comments.json()
                    if "response" in comments_data:
                        for comment in comments_data["response"].get("items", []):
                            user_id = comment.get("from_id", 0)
                            if user_id > 0:
                                scores[user_id] = scores.get(user_id, 0) + 2
                    
                    await asyncio.sleep(0.1) # Защита от лимитов

                if not scores:
                    logger.info("No subscriber activity detected.")
                    return

                # Сортируем пользователей по баллам
                top_users = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
                if not top_users:
                    return

                # 3. Запрашиваем информацию по топ-пользователям (имя, фамилия, аватар)
                user_ids_str = ",".join(str(uid) for uid, _ in top_users)
                url_users = "https://api.vk.ru/method/users.get"
                params_users = {
                    "user_ids": user_ids_str,
                    "fields": "photo_100,first_name,last_name",
                    "access_token": bot_token,
                    "v": self.api_version
                }
                resp_users = await client.get(url_users, params=params_users)
                users_data = resp_users.json()
                users_info = users_data.get("response", [])
                
                # Очищаем старую активность для этой группы
                db.exec(
                    select(VkCoverSubscriberActivity)
                    .where(VkCoverSubscriberActivity.vk_group_id == group_id)
                ).all()
                
                # Удаляем все старые записи для этой группы
                old_activities = db.exec(
                    select(VkCoverSubscriberActivity)
                    .where(VkCoverSubscriberActivity.vk_group_id == group_id)
                ).all()
                for old in old_activities:
                    db.delete(old)
                db.commit()

                # Сохраняем новые данные о топ-пользователях
                for u in users_info:
                    uid = u["id"]
                    score = scores.get(uid, 0)
                    activity = VkCoverSubscriberActivity(
                        vk_group_id=group_id,
                        vk_user_id=uid,
                        first_name=u.get("first_name", ""),
                        last_name=u.get("last_name", ""),
                        avatar_url=u.get("photo_100"),
                        score=score,
                        updated_at=datetime.utcnow()
                    )
                    db.add(activity)
                
                db.commit()
                logger.info(f"Successfully cached top active subscribers for group {group_id}")

            except Exception as e:
                logger.error(f"Error calculating subscriber activity for group {group_id}: {e}", exc_info=True)

    async def get_round_avatar(self, avatar_url: str, size: Tuple[int, int] = (80, 80)) -> Optional[Image.Image]:
        """Скачивает аватарку и обрезает её в круг"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(avatar_url)
                if resp.status_code == 200:
                    img = Image.open(BytesIO(resp.content)).convert("RGBA")
                    img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
                    
                    # Создаем маску для круга
                    mask = Image.new("L", size, 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0) + size, fill=255)
                    
                    # Применяем маску
                    result = Image.new("RGBA", size, (0, 0, 0, 0))
                    result.paste(img, (0, 0), mask=mask)
                    return result
        except Exception as e:
            logger.error(f"Error making round avatar from {avatar_url}: {e}")
        return None

    def sanitize_text_for_font(self, text: str, font: ImageFont.FreeTypeFont) -> str:
        """Заменяет цветные эмодзи на строгие векторные иконки-символы и удаляет неверные глифы, гарантируя отстутствие ???? в FreeType"""
        emoji_map = {
            "👑": "★", "⏰": "•", "🌤": "☀", "⏱": "•", "🚚": "▶", 
            "🎉": "✦", "🎁": "★", "🍕": "●", "⭐️": "★", "🔥": "▲", "📝": "◆",
            "🏆": "★", "🥇": "★", "🥈": "★", "🥉": "★", "👤": "●", "💬": "◆",
            "❤️": "★", "👍": "★", "⚡️": "⚡", "⚡": "⚡", "🚀": "▲",
            "💥": "✦", "✨": "✦", "☀️": "☀", "📅": "•"
        }
        
        for emoji, rep in emoji_map.items():
            text = text.replace(emoji, rep)
            
        cleaned = []
        for char in text:
            code = ord(char)
            # Разрешаем латиницу (U+0000..U+007F), доп. Latin-1 (U+0080..U+00FF), кириллицу (U+0400..U+04FF)
            # и проверенные символы шрифта (★, •, ☀, ▶, ✦, ●, ▲, ◆, ⚡)
            if code <= 0x04FF or code in (0x2605, 0x2022, 0x2600, 0x25B6, 0x2721, 0x25CF, 0x25B2, 0x25C6, 0x26A1):
                cleaned.append(char)
            else:
                cleaned.append(" ")

        res = "".join(cleaned)
        while "  " in res:
            res = res.replace("  ", " ")
        return res.strip()

    def calculate_work_status(
        self, 
        now: datetime, 
        open_time_str: str, 
        close_time_str: str, 
        work_days: List[int], 
        open_soon_min: int = 60, 
        close_soon_min: int = 60
    ) -> Dict[str, str]:
        """
        Вычисляет статус работы с поддержкой ночных смен и временных порогов.
        """
        try:
            oh, om = map(int, open_time_str.split(":"))
            ch, cm = map(int, close_time_str.split(":"))
        except Exception:
            oh, om, ch, cm = 10, 0, 22, 0

        open_min = oh * 60 + om
        close_min = ch * 60 + cm
        now_min = now.hour * 60 + now.minute
        weekday = now.isoweekday()

        is_working_day = weekday in work_days
        is_overnight = close_min <= open_min

        is_open = False
        minutes_left = 0

        if not is_overnight:
            if is_working_day and open_min <= now_min < close_min:
                is_open = True
                minutes_left = close_min - now_min
            else:
                is_open = False
                if now_min < open_min:
                    minutes_left = open_min - now_min
                else:
                    minutes_left = (1440 - now_min) + open_min
        else:
            yesterday_weekday = 7 if weekday == 1 else weekday - 1
            is_yesterday_working = yesterday_weekday in work_days

            if now_min < close_min:
                if is_yesterday_working:
                    is_open = True
                    minutes_left = close_min - now_min
                else:
                    is_open = False
                    minutes_left = open_min - now_min
            elif now_min >= open_min:
                if is_working_day:
                    is_open = True
                    minutes_left = (1440 - now_min) + close_min
                else:
                    is_open = False
                    minutes_left = (1440 - now_min) + open_min
            else:
                is_open = False
                minutes_left = open_min - now_min

        h = minutes_left // 60
        m = minutes_left % 60
        time_left_str = f"{m} мин" if h == 0 else f"{h} ч {m} мин"

        if is_open:
            status = "closing_soon" if minutes_left <= close_soon_min else "open"
        else:
            status = "opening_soon" if minutes_left <= open_soon_min else "closed"

        return {
            "status": status,
            "time_left_str": time_left_str,
            "next_open_time": f"{oh:02d}:{om:02d}"
        }

    def get_app_timezone(self, db: Session) -> pytz.BaseTzInfo:
        """Получает часовой пояс из системных настроек БД (IikoSettings / Настройки админки)"""
        try:
            from app.core.datetime_utils import get_tz_name
            tz_name = get_tz_name(db)
            return pytz.timezone(tz_name)
        except Exception as e:
            logger.error(f"Error getting app timezone: {e}")
            return pytz.timezone("Asia/Yekaterinburg")

    def get_top_active_subscriber(self, db: Session, group_id: int, period: str = "week") -> Tuple[str, str, int, Optional[str]]:
        """
        Получает рейтинг активных подписчиков за выбранный период (day, week, month, all_time)
        Возвращает (first_name, last_name, score, avatar_url).
        """
        app_tz = self.get_app_timezone(db)
        now_local = datetime.now(app_tz)
        
        if period == "day":
            start_dt = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            start_dt = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "all_time":
            start_dt = datetime(2020, 1, 1, tzinfo=app_tz)
        else: # week
            start_dt = (now_local - timedelta(days=now_local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            
        start_dt_utc = start_dt.astimezone(pytz.utc).replace(tzinfo=None)

        try:
            from app.models.vk_activity import VkActivity
            from app.models.vk_user import VkUser
            from sqlalchemy import func

            stmt = (
                select(VkActivity.vk_id, func.sum(VkActivity.points).label("total_score"))
                .where(VkActivity.created_at >= start_dt_utc)
                .group_by(VkActivity.vk_id)
                .order_by(func.sum(VkActivity.points).desc())
            )
            top_row = db.exec(stmt).first()

            if top_row and top_row[1] and top_row[1] > 0:
                vk_id, score = top_row[0], int(top_row[1])
                vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
                if vk_user:
                    return (vk_user.first_name, vk_user.last_name, score, getattr(vk_user, 'photo_100', None) or vk_user.photo_50)
        except Exception as e:
            logger.error(f"Error fetching top active subscriber for period {period}: {e}")

        # Фоллбэк 1: Кэш таблица VkCoverSubscriberActivity
        top_act = db.exec(
            select(VkCoverSubscriberActivity)
            .where(VkCoverSubscriberActivity.vk_group_id == group_id)
            .order_by(VkCoverSubscriberActivity.score.desc())
        ).first()
        if top_act:
            return (top_act.first_name, top_act.last_name, top_act.score, top_act.avatar_url)

        # Фоллбэк 2: Таблица пользователей VkUser (общий баланс баллов)
        try:
            from app.models.vk_user import VkUser
            top_user = db.exec(
                select(VkUser)
                .where(VkUser.vk_group_id == group_id)
                .order_by(VkUser.vk_bonus_balance.desc())
            ).first()
            if top_user and top_user.vk_bonus_balance > 0:
                return (top_user.first_name, top_user.last_name, top_user.vk_bonus_balance, top_user.photo_100 or top_user.photo_50)
        except Exception as e:
            logger.error(f"Fallback VkUser query error: {e}")

        return ("Скоро", "определится", 0, None)

    def draw_3d_status_dot(self, overlay: Image.Image, center_x: int, center_y: int, radius: int, color_type: str):
        """Отрисовывает 3D глянцевую статусный сферу с эффектом свечения"""
        draw = ImageDraw.Draw(overlay)
        if color_type == "green":
            glow_c = (0, 230, 118, 80)
            main_c = (0, 230, 118, 255)
        elif color_type == "yellow":
            glow_c = (255, 214, 0, 80)
            main_c = (255, 214, 0, 255)
        else:
            glow_c = (255, 23, 68, 80)
            main_c = (255, 23, 68, 255)

        # 1. Внешнее неоновое свечение (Aura)
        draw.ellipse((center_x - radius - 5, center_y - radius - 5, center_x + radius + 5, center_y + radius + 5), fill=glow_c)
        # 2. Основная яркая сфера
        draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius), fill=main_c)
        # 3. 3D Блик света (Highlight)
        hl_r = max(2, radius // 3)
        draw.ellipse((center_x - radius // 3, center_y - radius // 3, center_x - radius // 3 + hl_r, center_y - radius // 3 + hl_r), fill=(255, 255, 255, 230))

    def render_container_box(
        self,
        bg_image: Image.Image,
        box: Tuple[int, int, int, int],
        bg_style: str = "none",
        radius: int = 12,
        custom_bg_color: Optional[str] = None,
        custom_bg_opacity: int = 75,
        custom_border_color: Optional[str] = None,
        custom_border_width: int = 1
    ) -> Image.Image:
        """Отрисовывает закругленный контейнер с идеальным альфа-смешиванием и поддержкой кастомной настройки"""
        if bg_style == "none" or not bg_style:
            return bg_image

        x1, y1, x2, y2 = box

        overlay = Image.new("RGBA", bg_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Мягкая внешняя тень под контейнером
        shadow_overlay = Image.new("RGBA", bg_image.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_overlay)
        shadow_draw.rounded_rectangle(
            (x1 + 2, y1 + 3, x2 + 2, y2 + 3),
            radius=radius,
            fill=(0, 0, 0, 90)
        )
        bg_image = Image.alpha_composite(bg_image, shadow_overlay)

        alpha = max(0, min(255, int(255 * (custom_bg_opacity / 100.0))))
        fill_color = (20, 20, 30, alpha)
        border_color = (255, 255, 255, 100)
        border_width = max(0, custom_border_width)

        if bg_style == "glass":
            # Эффектное матовое стекло (Glassmorphism как в веб-редакторе)
            fill_color = (255, 255, 255, 45)
            border_color = (130, 170, 255, 210)
            border_width = 2
        elif bg_style == "solid":
            fill_color = (18, 20, 32, 245)
            border_color = (60, 65, 90, 255)
            border_width = 1
        elif bg_style == "neon":
            fill_color = (18, 14, 32, 220)
            border_color = (255, 215, 0, 240)
            border_width = 2
        elif bg_style == "pill":
            fill_color = (28, 30, 48, 225)
            border_color = (255, 255, 255, 70)
            border_width = 1
            radius = max(1, min(radius, (y2 - y1) // 2))
        elif bg_style == "gradient":
            fill_color = (44, 30, 77, 210)
            border_color = (130, 90, 220, 200)
            border_width = 2
        elif bg_style == "custom":
            if custom_bg_color:
                hex_c = custom_bg_color.lstrip('#')
                if len(hex_c) == 6:
                    r, g, b = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
                    fill_color = (r, g, b, alpha)
            if custom_border_color:
                hex_b = custom_border_color.lstrip('#')
                if len(hex_b) == 6:
                    r, g, b = tuple(int(hex_b[i:i+2], 16) for i in (0, 2, 4))
                    border_color = (r, g, b, 240)

        draw.rounded_rectangle(
            (x1, y1, x2, y2),
            radius=radius,
            fill=fill_color,
            outline=border_color if border_width > 0 else None,
            width=border_width
        )

        return Image.alpha_composite(bg_image, overlay)

    def get_today_orders_count(self, db: Session) -> int:
        """Считает количество доставок/заказов за текущий день из базы данных с учетом системного часового пояса"""
        try:
            from app.models.order import Order
            app_tz = self.get_app_timezone(db)
            now_local = datetime.now(app_tz)
            today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
            today_start_utc = today_start_local.astimezone(pytz.utc).replace(tzinfo=None)
            orders = db.exec(
                select(Order).where(Order.created_at >= today_start_utc)
            ).all()
            return len(orders)
        except Exception as e:
            logger.error(f"Error fetching today orders count: {e}")
            return 0

    def get_last_contest_winner(self, db: Session) -> str:
        """Получает последнего победителя из конкурсов ВК"""
        try:
            from app.models.vk_contest import VkContestWinner
            winner = db.exec(
                select(VkContestWinner).order_by(VkContestWinner.won_at.desc())
            ).first()
            if winner:
                return f"{winner.first_name} {winner.last_name[:1]}. ({winner.prize_name})"
        except Exception as e:
            logger.error(f"Error fetching last contest winner: {e}")
        return "Анна С. (Сет Роллов)"

    async def format_dynamic_text(self, text_template: str, db: Session, city_weather: str = "Тюмень") -> str:
        """Форматирует динамический текст с заменой плейсхолдеров в соответствии с системным часовым поясом"""
        app_tz = self.get_app_timezone(db)
        now_local = datetime.now(app_tz)
        time_str = now_local.strftime("%H:%M")
        
        weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
        date_str = f"{now_local.day} {months[now_local.month - 1]}, {weekdays[now_local.weekday()]}"
        
        formatted = text_template.replace("{time}", time_str)
        formatted = formatted.replace("{date}", date_str)

        if "{weather}" in formatted:
            w_str = await self.get_weather(city_weather)
            formatted = formatted.replace("{weather}", w_str)

        if "{today_orders}" in formatted:
            cnt = self.get_today_orders_count(db)
            formatted = formatted.replace("{today_orders}", str(cnt))

        if "{last_winner}" in formatted:
            win_str = self.get_last_contest_winner(db)
            formatted = formatted.replace("{last_winner}", win_str)

        return formatted

    async def generate_cover_image(self, db: Session, bot: VkCoverBot) -> Image.Image:
        """Генерирует изображение обложки Pillow на основе настроек бота, виджетов и системного часового пояса"""
        await self.download_font_if_not_exists()

        app_tz = self.get_app_timezone(db)
        now_local = datetime.now(app_tz)

        width, height = 1590, 530
        
        # 1. Загружаем фон (с поддержкой слайд-шоу)
        selected_bg_url = bot.background_image_url
        if bot.slideshow_images and len(bot.slideshow_images) > 0:
            interval = max(1, bot.slideshow_interval_minutes or 5)
            now_ts = int(now_local.timestamp()) // 60
            
            if bot.slideshow_mode == "random":
                import random
                rng = random.Random(now_ts // interval)
                idx = rng.randint(0, len(bot.slideshow_images) - 1)
            else:
                idx = (now_ts // interval) % len(bot.slideshow_images)
                
            selected_bg_url = bot.slideshow_images[idx]

        bg_image = None
        if selected_bg_url:
            local_path = selected_bg_url
            if local_path.startswith("/media/"):
                local_path = local_path.replace("/media/", "/app/media/")
            elif not local_path.startswith("http"):
                local_path = os.path.join("/app/media", local_path)
            
            if os.path.exists(local_path):
                try:
                    bg_image = Image.open(local_path).convert("RGBA")
                    bg_image = ImageOps.fit(bg_image, (width, height), Image.Resampling.LANCZOS)
                except Exception as e:
                    logger.error(f"Error opening background image {local_path}: {e}")

        if not bg_image:
            bg_image = Image.new("RGBA", (width, height), (22, 22, 38, 255))
            draw = ImageDraw.Draw(bg_image)
            draw.rectangle([0, 0, width, height], fill=(18, 18, 30, 255))
            draw.ellipse([width - 300, -100, width + 100, 300], fill=(44, 30, 77, 80))
            draw.ellipse([-100, height - 200, 300, height + 200], fill=(30, 50, 77, 80))

        # 2. Рендерим виджеты
        for widget in bot.widgets:
            w_type = widget.get("type")
            x = int(widget.get("x", 0))
            y = int(widget.get("y", 0))
            font_size = int(widget.get("font_size", 24))
            color_hex = widget.get("color", "#ffffff")
            
            bg_style = widget.get("bg_style", "none")
            custom_bg_color = widget.get("custom_bg_color", "#12121e")
            custom_bg_opacity = int(widget.get("custom_bg_opacity", 75))
            custom_border_color = widget.get("custom_border_color", "#ffffff")
            custom_border_width = int(widget.get("custom_border_width", 1))

            padding = int(widget.get("container_padding", 12))
            radius = int(widget.get("container_radius", 12))
            text_shadow = widget.get("text_shadow", False)
            text_stroke = widget.get("text_stroke", True)
            icon = widget.get("icon", "")

            # Превращаем HEX в RGBA
            color_hex = color_hex.lstrip('#')
            if len(color_hex) == 6:
                r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
                color = (r, g, b, 255)
            elif len(color_hex) == 8:
                r, g, b, a = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4, 6))
                color = (r, g, b, a)
            else:
                color = (255, 255, 255, 255)

            # Масштабируем размер шрифта для соответствия редактору (1590x530)
            effective_font_size = max(24, int(font_size * 1.4))
            try:
                font = ImageFont.truetype(self.font_path, effective_font_size)
            except Exception:
                font = ImageFont.load_default()

            # Формируем текст в зависимости от типа виджета
            full_text = ""
            avatar_img = None
            avatar_size = int(widget.get("avatar_size", 60))
            status_dot_color = None

            if w_type == "clock":
                time_str = now_local.strftime("%H:%M")
                show_date = widget.get("show_date", False)
                
                if show_date:
                    weekdays = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
                    months = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
                    date_str = f"{now_local.day} {months[now_local.month - 1]}, {weekdays[now_local.weekday()]}"
                    full_text = f"{icon or '★'} {time_str} ({date_str})"
                else:
                    full_text = f"{icon or '★'} {time_str}"
                
            elif w_type == "weather":
                city = widget.get("city", bot.city_weather or "Москва")
                weather_str = await self.get_weather(city)
                full_text = f"{icon or '☀'} {weather_str}"

            elif w_type == "work_hours":
                open_time_str = widget.get("open_time", "10:00")
                close_time_str = widget.get("close_time", "22:00")
                work_days = widget.get("work_days", [1, 2, 3, 4, 5, 6, 7])
                text_open = widget.get("text_open", "🟢 Открыты до {close_time}")
                text_closed = widget.get("text_closed", "🔴 Закрыто! Откроемся в {next_open_time}")
                text_opening_soon = widget.get("text_opening_soon", "🟡 Откроемся через {time_left}")
                text_closing_soon = widget.get("text_closing_soon", "🟡 Закрываемся через {time_left}")
                open_soon_min = int(widget.get("opening_soon_threshold", 60))
                close_soon_min = int(widget.get("closing_soon_threshold", 60))

                status_info = self.calculate_work_status(
                    now_local, open_time_str, close_time_str, work_days, open_soon_min, close_soon_min
                )
                
                status = status_info["status"]
                time_left_str = status_info["time_left_str"]
                next_open_time = status_info["next_open_time"]

                if status == "open":
                    raw_text = text_open.format(open_time=open_time_str, close_time=close_time_str, time_left=time_left_str, next_open_time=next_open_time)
                    status_dot_color = "green"
                elif status == "closing_soon":
                    raw_text = text_closing_soon.format(open_time=open_time_str, close_time=close_time_str, time_left=time_left_str, next_open_time=next_open_time)
                    status_dot_color = "yellow"
                elif status == "opening_soon":
                    raw_text = text_opening_soon.format(open_time=open_time_str, close_time=close_time_str, time_left=time_left_str, next_open_time=next_open_time)
                    status_dot_color = "yellow"
                else:
                    raw_text = text_closed.format(open_time=open_time_str, close_time=close_time_str, time_left=time_left_str, next_open_time=next_open_time)
                    status_dot_color = "red"

                # Удаляем текстовые маркеры эмодзи из строки для отрисовки красивой 3D сферы
                raw_text = raw_text.replace("🟢", "").replace("🔴", "").replace("🟡", "").strip()
                full_text = f"{icon} {raw_text}".strip() if icon else raw_text

            elif w_type == "timer":
                target_str = widget.get("target_date")
                timer_text = "00:00"
                if target_str:
                    try:
                        target_str = target_str.replace("T", " ")
                        if len(target_str) > 16:
                            target_str = target_str[:16]
                        target_dt = datetime.strptime(target_str, "%Y-%m-%d %H:%M")
                        now = datetime.now()
                        diff = target_dt - now
                        
                        if diff.total_seconds() > 0:
                            days = diff.days
                            hours, remainder = divmod(diff.seconds, 3600)
                            minutes, _ = divmod(remainder, 60)
                            timer_text = f"{days}д. " if days > 0 else ""
                            timer_text += f"{hours:02d}:{minutes:02d}"
                        else:
                            timer_text = widget.get("expired_text", "Акция завершена!")
                    except Exception as te:
                        logger.error(f"Error parsing timer date {target_str}: {te}")

                label = widget.get("label", "До конца акции:")
                full_text = f"{icon or '⏱'} {label} {timer_text}"

            elif w_type == "orders_counter":
                cnt = self.get_today_orders_count(db)
                label = widget.get("label", "Сегодня доставлено:")
                full_text = f"{icon or '▶'} {label} {cnt} заказов"

            elif w_type == "last_winner":
                winner_str = self.get_last_contest_winner(db)
                label = widget.get("label", "Победитель рулетки:")
                full_text = f"{icon or '✦'} {label} {winner_str}"

            elif w_type == "promo_code":
                code = widget.get("code", "VK2026")
                label = widget.get("label", "Промокод дня:")
                full_text = f"{icon or '★'} {label} {code}"
                
            elif w_type == "text":
                text_content = widget.get("text", "")
                full_text = await self.format_dynamic_text(text_content, db, bot.city_weather or "Москва")
                if icon:
                    full_text = f"{icon} {full_text}"
                
            elif w_type == "active_subscriber":
                conn = db.get(VkBotConnection, bot.vk_bot_connection_id)
                period = widget.get("period", "week")
                period_labels = {
                    "day": "Лидер дня:",
                    "week": "Лидер недели:",
                    "month": "Лидер месяца:",
                    "all_time": "Лидер активности:"
                }
                default_label = period_labels.get(period, "Лидер недели:")
                label = widget.get("label") or default_label

                if conn:
                    first_name, last_name, score, avatar_url = self.get_top_active_subscriber(db, conn.vk_group_id, period)
                    sub_name = f"{first_name} {last_name}".strip()
                    if score > 0:
                        full_text = f"{icon or '★'} {label} {sub_name} ({score} б.)"
                    else:
                        full_text = f"{icon or '★'} {label} {sub_name}"

                    if avatar_url:
                        avatar_img = await self.get_round_avatar(avatar_url, (avatar_size, avatar_size))
                else:
                    full_text = f"{icon or '★'} {label} Скоро определится"

            # Очищаем текст от неверных глифов/эмодзи, гарантируя отстутствие ????
            full_text = self.sanitize_text_for_font(full_text, font)

            # 3. Измеряем габариты текста для подложки
            draw_temp = ImageDraw.Draw(bg_image)
            bbox = draw_temp.textbbox((0, 0), full_text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            dot_radius = max(8, int(text_h * 0.38)) if status_dot_color else 0
            dot_width = (dot_radius * 2 + 14) if status_dot_color else 0

            total_w = text_w + dot_width
            if avatar_img:
                total_w += avatar_size + 15

            total_h = max(text_h, avatar_size if avatar_img else text_h)

            # 4. Рендерим стильный контейнер через Alpha Composite
            if bg_style != "none":
                box_x1 = x - padding
                box_y1 = y - padding
                box_x2 = x + total_w + padding
                box_y2 = y + total_h + padding
                bg_image = self.render_container_box(
                    bg_image,
                    (box_x1, box_y1, box_x2, box_y2),
                    bg_style=bg_style,
                    radius=radius,
                    custom_bg_color=custom_bg_color,
                    custom_bg_opacity=custom_bg_opacity,
                    custom_border_color=custom_border_color,
                    custom_border_width=custom_border_width
                )

            draw = ImageDraw.Draw(bg_image)

            # 5. Отрисовываем аватар, 3D сферу статуса и текст
            text_pos_x = x - bbox[0]
            text_pos_y = y - bbox[1] + ((total_h - text_h) // 2)

            if avatar_img:
                bg_image.paste(avatar_img, (x, y), mask=avatar_img)
                text_pos_x = x + avatar_size + 15 - bbox[0]
                draw = ImageDraw.Draw(bg_image)

            if status_dot_color:
                dot_overlay = Image.new("RGBA", bg_image.size, (0, 0, 0, 0))
                dot_cx = text_pos_x + bbox[0] + dot_radius + 2
                dot_cy = y + (total_h // 2)
                self.draw_3d_status_dot(dot_overlay, dot_cx, dot_cy, dot_radius, status_dot_color)
                bg_image = Image.alpha_composite(bg_image, dot_overlay)
                draw = ImageDraw.Draw(bg_image)
                text_pos_x += dot_width

            if text_shadow:
                draw.text((text_pos_x + 2, text_pos_y + 2), full_text, fill=(0, 0, 0, 180), font=font)

            stroke_kwargs = {}
            if text_stroke:
                stroke_kwargs = {"stroke_width": 2, "stroke_fill": (0, 0, 0, 255)}

            draw.text((text_pos_x, text_pos_y), full_text, fill=color, font=font, **stroke_kwargs)

        # Конвертируем в чистый 24-битный RGB для исключения артефактов при загрузке в ВК
        final_image = Image.new("RGB", bg_image.size, (22, 22, 38))
        final_image.paste(bg_image, mask=bg_image.split()[3])
        return final_image

    async def upload_cover_to_vk(self, bot_token: str, group_id: int, image_bytes: bytes) -> bool:
        """Загружает обложку в сообщество ВК"""
        # 1. Получаем сервер загрузки
        url_server = "https://api.vk.ru/method/photos.getOwnerCoverPhotoUploadServer"
        params_server = {
            "group_id": group_id,
            "crop_x": 0,
            "crop_y": 0,
            "crop_x2": 1590,
            "crop_y2": 530,
            "access_token": bot_token,
            "v": self.api_version
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(url_server, params=params_server)
                data = resp.json()
                if "error" in data:
                    logger.error(f"VK API getOwnerCoverPhotoUploadServer error: {data['error']}")
                    return False
                
                upload_url = data["response"]["upload_url"]
                
                # 2. POST запрос файла (ВК требует строго JPEG для обложек сообществ)
                files = {"photo": ("cover.jpg", image_bytes, "image/jpeg")}
                resp_upload = await client.post(upload_url, files=files)
                upload_data = resp_upload.json()
                
                if "error" in upload_data:
                    logger.error(f"VK Cover upload error: {upload_data['error']}")
                    return False
                
                # 3. Сохраняем обложку
                url_save = "https://api.vk.ru/method/photos.saveOwnerCoverPhoto"
                params_save = {
                    "hash": upload_data.get("hash"),
                    "photo": upload_data.get("photo"),
                    "access_token": bot_token,
                    "v": self.api_version
                }
                
                resp_save = await client.post(url_save, data=params_save)
                save_data = resp_save.json()
                
                if "error" in save_data:
                    logger.error(f"VK API saveOwnerCoverPhoto error: {save_data['error']}")
                    return False
                
                logger.info(f"VK Cover successfully updated for group {group_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to upload VK cover for group {group_id}: {e}", exc_info=True)
                return False

    async def publish_cover(self, db: Session, bot: VkCoverBot) -> bool:
        """Полный цикл: генерация и обновление обложки в ВК"""
        conn = db.get(VkBotConnection, bot.vk_bot_connection_id)
        if not conn or not conn.is_active:
            logger.warning(f"Active connection not found for cover bot {bot.id}")
            return False
            
        # Приоритет токенов: bot_token бота -> bot_token подключения -> user_token
        candidate_tokens = []
        for t in [bot.vk_bot_token, conn.vk_bot_token, conn.vk_user_token]:
            if t and t not in candidate_tokens:
                candidate_tokens.append(t)

        group_id = conn.vk_group_id
        
        # Генерируем изображение
        img = await self.generate_cover_image(db, bot)
        
        # Сохраняем в байты в формате JPEG (требование VK API)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=95)
        img_bytes = buf.getvalue()
        
        # Загружаем в ВК с фоллбэком токенов при ошибках
        success = False
        for token_to_try in candidate_tokens:
            success = await self.upload_cover_to_vk(token_to_try, group_id, img_bytes)
            if success:
                break
        if success:
            bot.last_published_at = datetime.utcnow()
            db.add(bot)
            db.commit()
            
        return success

vk_cover_service = VkCoverService()
