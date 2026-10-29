import os
import re
import random
import httpx
import logging
import asyncio
import tempfile
from io import BytesIO
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from sqlmodel import Session, select
from app.core.database import engine
from app.core.datetime_utils import utc_now
from app.models.vk_contest import VkContest, VkContestPlayer, VkContestWinner
from app.models.vk_bot_connection import VkBotConnection
from app.services.vk_birthday_service import vk_birthday_service

logger = logging.getLogger(__name__)

# Буквы для морского боя
RU_LETTERS = ["А", "Б", "В", "Г", "Д", "Е", "Ж", "З", "И", "К"]
LAT_TO_RU = {
    "A": "А", "B": "Б", "C": "В", "D": "Г", "E": "Д", 
    "F": "Е", "G": "Ж", "H": "З", "I": "И", "K": "К"
}

class VkContestService:
    """Сервис для управления конкурсами геймификации ВКонтакте"""

    def __init__(self):
        self.api_url = "https://api.vk.ru/method/"
        self.api_version = "5.199"
        self.font_path = "/app/media/fonts/Roboto-Bold.ttf" if os.path.exists("/app/media") else "./media/fonts/Roboto-Bold.ttf"

    def format_msg(self, template: str, **kwargs) -> str:
        """Безопасно форматирует шаблон, заменяя переданные ключи в фигурных скобках"""
        res = template
        for k, v in kwargs.items():
            res = res.replace(f"{{{k}}}", str(v))
        return res

    def normalize_coordinate(self, text: str) -> Optional[str]:
        """Парсит координату типа 'А5' или 'b10' для морского боя"""
        text = text.strip().upper()
        # Ищем совпадения с координатой
        match = re.search(r'([А-КA-K])\s*(\d{1,2})', text)
        if not match:
            return None
        
        letter = match.group(1)
        number_str = match.group(2)
        
        # Переводим латинскую букву в русскую
        if letter in LAT_TO_RU:
            letter = LAT_TO_RU[letter]
            
        number = int(number_str)
        if letter in RU_LETTERS and 1 <= number <= 10:
            return f"{letter}{number}"
            
        return None

    async def is_prize_hunter(self, bot_token: str, user_id: int) -> bool:
        """Базовая проверка аккаунта на призолова через VK API"""
        try:
            url = f"{self.api_url}users.get"
            params = {
                "user_ids": user_id,
                "fields": "counters,verified,has_photo",
                "access_token": bot_token,
                "v": self.api_version
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if "response" in data and len(data["response"]) > 0:
                        user_data = data["response"][0]
                        if user_data.get("verified"):
                            return False
                        if not user_data.get("has_photo"):
                            return True
                        counters = user_data.get("counters", {})
                        if "friends" in counters and counters["friends"] < 10:
                            return True
        except Exception as e:
            logger.error(f"Error checking prize hunter for user {user_id}: {e}")
        return False

    def initialize_game_field(self, contest: VkContest):
        """Инициализирует игровое поле (сетку) призами в зависимости от типа игры"""
        prizes_flat = []
        for p in contest.prizes:
            p_id = p["id"]
            qty = p.get("qty", 0)
            prizes_flat.extend([p_id] * qty)
            
        field_data = {}
        
        if contest.game_type == "seabattle":
            # Поле 10x10 = 100 ячеек
            all_coords = [f"{l}{n}" for l in RU_LETTERS for n in range(1, 11)]
            random.shuffle(all_coords)
            
            # Размещаем призы по случайным ячейкам
            for i, p_id in enumerate(prizes_flat):
                if i < len(all_coords):
                    coord = all_coords[i]
                    field_data[coord] = {"prize_id": p_id, "hit": False}
                    
        elif contest.game_type == "chests":
            # Поле 4x4 = 16 сундуков
            all_chests = [str(n) for n in range(1, 17)]
            random.shuffle(all_chests)
            
            for i, p_id in enumerate(prizes_flat):
                if i < len(all_chests):
                    chest = all_chests[i]
                    field_data[chest] = {"prize_id": p_id, "hit": False}
                    
        elif contest.game_type == "battle":
            # Поле 10x10 = 100 ячеек
            all_coords = [f"{l}{n}" for l in RU_LETTERS for n in range(1, 11)]
            random.shuffle(all_coords)
            
            num_penalties = int(100 * (contest.penalty_percent or 10) / 100.0)
            num_bonuses = int(100 * (contest.bonus_percent or 20) / 100.0)
            
            for i, coord in enumerate(all_coords):
                if i < num_penalties:
                    field_data[coord] = {"type": "penalty", "owner_id": None, "first_name": "", "last_name": ""}
                elif i < num_penalties + num_bonuses:
                    field_data[coord] = {"type": "bonus", "owner_id": None, "first_name": "", "last_name": ""}
                else:
                    field_data[coord] = {"type": "empty", "owner_id": None, "first_name": "", "last_name": ""}
                    
        contest.game_field_data = field_data

    def generate_seabattle_image(self, field_data: Dict[str, Any]) -> Image.Image:
        """Отрисовывает динамическое поле морского боя 10x10"""
        cell_size = 50
        offset_x, offset_y = 60, 60
        width, height = offset_x + 10 * cell_size + 20, offset_y + 10 * cell_size + 20
        
        img = Image.new("RGBA", (width, height), (18, 18, 30, 255))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(self.font_path, 20)
            font_small = ImageFont.truetype(self.font_path, 14)
        except Exception:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()
            
        # Рисуем буквы сверху
        for idx, l in enumerate(RU_LETTERS):
            cx = offset_x + idx * cell_size + cell_size // 2 - 8
            draw.text((cx, 20), l, fill=(255, 255, 255, 255), font=font)
            
        # Рисуем цифры слева
        for idx in range(1, 11):
            cy = offset_y + (idx - 1) * cell_size + cell_size // 2 - 10
            draw.text((20, cy), str(idx), fill=(255, 255, 255, 255), font=font)

        # Рисуем сетку
        for x in range(11):
            lx = offset_x + x * cell_size
            draw.line([(lx, offset_y), (lx, offset_y + 10 * cell_size)], fill=(60, 60, 90, 255), width=2)
        for y in range(11):
            ly = offset_y + y * cell_size
            draw.line([(offset_x, ly), (offset_x + 10 * cell_size, ly)], fill=(60, 60, 90, 255), width=2)

        # Рисуем выстрелы
        for coord, info in field_data.items():
            if not info.get("hit"):
                continue
            
            # Извлекаем ячейку
            match = re.match(r'([А-К])(\d+)', coord)
            if not match:
                continue
                
            let_idx = RU_LETTERS.index(match.group(1))
            num_idx = int(match.group(2)) - 1
            
            cx = offset_x + let_idx * cell_size
            cy = offset_y + num_idx * cell_size
            
            if info.get("prize_id") is not None:
                # Взрыв (Попал!)
                draw.rectangle([cx+4, cy+4, cx+cell_size-4, cy+cell_size-4], fill=(220, 50, 80, 100), outline=(220, 50, 80, 255), width=2)
                draw.line([(cx+10, cy+10), (cx+cell_size-10, cy+cell_size-10)], fill=(255, 255, 255, 255), width=4)
                draw.line([(cx+cell_size-10, cy+10), (cx+10, cy+cell_size-10)], fill=(255, 255, 255, 255), width=4)
            else:
                # Промах
                draw.ellipse([cx+cell_size//2 - 6, cy+cell_size//2 - 6, cx+cell_size//2 + 6, cy+cell_size//2 + 6], fill=(120, 120, 150, 255))
                
        return img

    def generate_battle_image(self, field_data: Dict[str, Any]) -> Image.Image:
        """Отрисовывает динамическое поле пляжной битвы 10x10"""
        cell_size = 50
        offset_x, offset_y = 60, 60
        width, height = offset_x + 10 * cell_size + 20, offset_y + 10 * cell_size + 20
        
        # Песочный/пляжный фон: (255, 199, 128)
        img = Image.new("RGBA", (width, height), (255, 199, 128, 255))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(self.font_path, 20)
            font_small = ImageFont.truetype(self.font_path, 11)
        except Exception:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()
            
        # Рисуем буквы сверху (темно-коричневые)
        for idx, l in enumerate(RU_LETTERS):
            cx = offset_x + idx * cell_size + cell_size // 2 - 8
            draw.text((cx, 20), l, fill=(90, 60, 40, 255), font=font)
            
        # Рисуем цифры слева
        for idx in range(1, 11):
            cy = offset_y + (idx - 1) * cell_size + cell_size // 2 - 10
            draw.text((20, cy), str(idx), fill=(90, 60, 40, 255), font=font)

        # Рисуем сетку (коричневая)
        for x in range(11):
            lx = offset_x + x * cell_size
            draw.line([(lx, offset_y), (lx, offset_y + 10 * cell_size)], fill=(130, 95, 65, 255), width=2)
        for y in range(11):
            ly = offset_y + y * cell_size
            draw.line([(offset_x, ly), (offset_x + 10 * cell_size, ly)], fill=(130, 95, 65, 255), width=2)

        # Отрисовываем занятые ячейки
        for coord, info in field_data.items():
            owner_id = info.get("owner_id")
            if owner_id is None:
                continue
                
            match = re.match(r'([А-К])(\d+)', coord)
            if not match:
                continue
                
            let_idx = RU_LETTERS.index(match.group(1))
            num_idx = int(match.group(2)) - 1
            
            cx = offset_x + let_idx * cell_size
            cy = offset_y + num_idx * cell_size
            
            c_type = info.get("type", "empty")
            if c_type == "penalty":
                # Мина (красный крестик / штраф)
                draw.rectangle([cx+3, cy+3, cx+cell_size-3, cy+cell_size-3], fill=(220, 70, 70, 180), outline=(220, 50, 50, 255), width=2)
                draw.line([(cx+10, cy+10), (cx+cell_size-10, cy+cell_size-10)], fill=(255, 255, 255, 255), width=3)
                draw.line([(cx+cell_size-10, cy+10), (cx+10, cy+cell_size-10)], fill=(255, 255, 255, 255), width=3)
                draw.text((cx+6, cy+cell_size-15), "Штраф", fill=(255, 255, 255, 255), font=font_small)
            elif c_type == "bonus":
                # Бонус (зеленый / подарок)
                draw.rectangle([cx+3, cy+3, cx+cell_size-3, cy+cell_size-3], fill=(50, 200, 100, 180), outline=(40, 170, 80, 255), width=2)
                draw.ellipse([cx+12, cy+12, cx+cell_size-12, cy+cell_size-12], fill=(255, 255, 255, 255))
                draw.text((cx+18, cy+16), "+2", fill=(40, 170, 80, 255), font=font_small)
            else:
                # Обычная захваченная ячейка (нежно-синий)
                draw.rectangle([cx+3, cy+3, cx+cell_size-3, cy+cell_size-3], fill=(100, 180, 240, 180), outline=(70, 150, 210, 255), width=2)
                # Пишем первые 4 буквы имени игрока
                name_chunk = info.get("first_name", "Игрок")[:4]
                draw.text((cx+8, cy+18), name_chunk, fill=(40, 70, 110, 255), font=font_small)
                
        return img

    def generate_chests_image(self, field_data: Dict[str, Any]) -> Image.Image:
        """Отрисовывает поле сундуков 4x4 (1..16)"""
        cell_size = 120
        gap = 15
        offset = 20
        width, height = 4 * cell_size + 3 * gap + 2 * offset, 4 * cell_size + 3 * gap + 2 * offset
        
        img = Image.new("RGBA", (width, height), (18, 18, 30, 255))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(self.font_path, 32)
            font_small = ImageFont.truetype(self.font_path, 16)
        except Exception:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()

        for idx in range(1, 17):
            row = (idx - 1) // 4
            col = (idx - 1) % 4
            
            x1 = offset + col * (cell_size + gap)
            y1 = offset + row * (cell_size + gap)
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            
            info = field_data.get(str(idx), {})
            
            if info.get("hit"):
                if info.get("prize_id") is not None:
                    # Выигрыш
                    draw.rounded_rectangle([x1, y1, x2, y2], radius=10, fill=(40, 167, 69, 200), outline=(40, 167, 69, 255), width=3)
                    draw.text((x1 + 45, y1 + 30), "🎁", fill=(255, 255, 255, 255), font=font)
                    draw.text((x1 + 32, y1 + 80), "Приз!", fill=(255, 255, 255, 255), font=font_small)
                else:
                    # Пусто
                    draw.rounded_rectangle([x1, y1, x2, y2], radius=10, fill=(108, 117, 125, 100), outline=(108, 117, 125, 255), width=3)
                    draw.text((x1 + 42, y1 + 40), "💨", fill=(255, 255, 255, 255), font=font)
            else:
                # Закрытый сундук
                draw.rounded_rectangle([x1, y1, x2, y2], radius=10, fill=(44, 30, 77, 255), outline=(90, 60, 150, 255), width=3)
                draw.text((x1 + 45, y1 + 30), str(idx), fill=(255, 255, 255, 255), font=font)
                draw.text((x1 + 38, y1 + 80), "Открыть", fill=(170, 150, 220, 255), font=font_small)
                
        return img

    async def check_vk_subscription(self, bot_token: str, group_id: int, user_id: int) -> bool:
        """Проверяет подписку пользователя на сообщество ВК"""
        url = "https://api.vk.ru/method/groups.isMember"
        params = {
            "group_id": group_id,
            "user_id": user_id,
            "access_token": bot_token,
            "v": self.api_version
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params)
                data = resp.json()
                return data.get("response") == 1
        except Exception as e:
            logger.error(f"Error checking VK membership: {e}")
            return True # Фолбэк в пользу игрока

    async def get_post_reposters(self, bot_token: str, group_id: int, post_id: int) -> List[int]:
        """Возвращает список ID пользователей, поделившихся записью"""
        url = "https://api.vk.ru/method/wall.getReposts"
        params = {
            "owner_id": -group_id,
            "post_id": post_id,
            "count": 1000,
            "access_token": bot_token,
            "v": self.api_version
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params)
                data = resp.json()
                items = data.get("response", {}).get("items", [])
                return [item.get("from_id") for item in items if item.get("from_id", 0) > 0]
        except Exception as e:
            logger.error(f"Error fetching reposts: {e}")
            return []

    async def get_post_likers(self, bot_token: str, group_id: int, post_id: int) -> List[int]:
        """Возвращает список ID пользователей, поставивших лайк"""
        url = "https://api.vk.ru/method/likes.getList"
        params = {
            "type": "post",
            "owner_id": -group_id,
            "item_id": post_id,
            "filter": "likes",
            "count": 1000,
            "access_token": bot_token,
            "v": self.api_version
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params)
                data = resp.json()
                return data.get("response", {}).get("items", [])
        except Exception as e:
            logger.error(f"Error fetching likers: {e}")
            return []

    async def reply_to_vk_comment(self, bot_token: str, group_id: int, post_id: int, comment_id: int, message: str, attachment: Optional[str] = None):
        """Отправляет ответный комментарий в ветку ВК"""
        url = "https://api.vk.ru/method/wall.createComment"
        params = {
            "owner_id": -group_id,
            "post_id": post_id,
            "reply_to_comment": comment_id,
            "message": message,
            "access_token": bot_token,
            "v": self.api_version
        }
        if attachment:
            params["attachments"] = attachment
            
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, data=params)
                data = resp.json()
                if "error" in data:
                    logger.error(f"Failed to reply to comment: {data['error']}")
        except Exception as e:
            logger.error(f"Error replying to VK comment: {e}")

    async def process_contest_move(self, db: Session, payload: Dict[str, Any], bot_token: str, group_id: int):
        """Основной метод обработки входящего хода (комментария) по Callback API"""
        post_id = payload.get("post_id")
        comment_id = payload.get("id")
        user_id = payload.get("from_id")
        text = payload.get("text", "").strip()

        # Игнорируем комментарии от групп и пустые
        if not user_id or user_id < 0 or not text:
            return

        # 1. Находим активный конкурс для данного поста
        contest = db.exec(
            select(VkContest)
            .where(VkContest.post_id == post_id)
            .where(VkContest.is_active == True)
        ).first()

        if not contest:
            return

        # Переопределяем токен, если он задан в настройках конкурса
        if contest.vk_bot_token:
            bot_token = contest.vk_bot_token

        # Запрашиваем инфо о пользователе
        from app.services.vk_service import fetch_vk_user_info
        vk_profile = await fetch_vk_user_info(user_id, bot_token)
        first_name = vk_profile.get("first_name", "Игрок")
        last_name = vk_profile.get("last_name", "")

        # 1.5. Проверяем черный и белый списки
        user_str = str(user_id)
        if contest.black_list and user_str in contest.black_list:
            logger.info(f"User {user_id} is in black list for contest {contest.id}. Ignoring.")
            return

        if contest.white_list and len(contest.white_list) > 0 and user_str not in contest.white_list:
            logger.info(f"User {user_id} is not in white list for contest {contest.id}. Ignoring.")
            return

        # 1.6. Проверяем ограничение на выигрыш (можно выиграть только один раз)
        if contest.can_win_once:
            winner_exists = db.exec(
                select(VkContestWinner)
                .where(VkContestWinner.contest_id == contest.id)
                .where(VkContestWinner.vk_user_id == user_id)
            ).first()
            if winner_exists:
                msg = f"{first_name}, вы уже выиграли приз «{winner_exists.prize_name}» в этом конкурсе! Повторное участие невозможно 😊"
                await self.reply_to_vk_comment(bot_token, group_id, post_id, comment_id, msg)
                return

        # 2. Проверяем подписку
        is_sub = await self.check_vk_subscription(bot_token, group_id, user_id)
        if not is_sub:
            msg = self.format_msg(contest.msg_subscribe_needed, name=first_name)
            await self.reply_to_vk_comment(bot_token, group_id, post_id, comment_id, msg)
            return

        # 3. Находим или создаем игрока
        player = db.exec(
            select(VkContestPlayer)
            .where(VkContestPlayer.contest_id == contest.id)
            .where(VkContestPlayer.vk_user_id == user_id)
        ).first()

        if not player:
            player = VkContestPlayer(
                contest_id=contest.id,
                vk_user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                attempts_left=contest.start_attempts,
                attempts_used=0
            )
            db.add(player)
            db.commit()
            db.refresh(player)

        # 3.5. Проверяем GAME OVER
        if player.is_game_over:
            msg = f"💥 {first_name}, для вас эта игра окончена! Вы натолкнулись на две штрафные ячейки 🛑"
            await self.reply_to_vk_comment(bot_token, group_id, post_id, comment_id, msg)
            return

        # 4. Проверяем кулдаун (КД) ходов
        now = datetime.utcnow()
        if player.last_move_at:
            delta = (now - player.last_move_at).total_seconds()
            if delta < contest.delay_between_moves:
                wait_sec = int(contest.delay_between_moves - delta)
                msg = self.format_msg(contest.msg_cooldown, name=first_name, cooldown=wait_sec)
                self.log_action(db, contest.id, user_id, first_name, last_name, "system", f"Ход отклонен: кулдаун ({wait_sec} сек)")
                await self.reply_to_vk_comment(bot_token, group_id, post_id, comment_id, msg)
                return

        # 5. Проверка наличия попыток + начисление бонусов при 0 попыток
        if player.attempts_left <= 0:
            # Пробуем начислить за лайк/репост
            bonus_added = False
            bonus_msg = []
            
            # Проверка репоста
            if contest.repost_attempts > 0 and not player.repost_done:
                reposters = await self.get_post_reposters(bot_token, group_id, post_id)
                if user_id in reposters:
                    player.attempts_left += contest.repost_attempts
                    player.repost_done = True
                    bonus_added = True
                    bonus_msg.append(f"+{contest.repost_attempts} попыток за репост")
            
            # Проверка лайка
            if contest.like_attempts > 0 and not player.like_done:
                likers = await self.get_post_likers(bot_token, group_id, post_id)
                if user_id in likers:
                    player.attempts_left += contest.like_attempts
                    player.like_done = True
                    bonus_added = True
                    bonus_msg.append(f"+{contest.like_attempts} попыток за лайк")
                    
            if bonus_added:
                db.add(player)
                db.commit()
                self.log_action(db, contest.id, user_id, first_name, last_name, "reward", f"Начислен бонус: {', '.join(bonus_msg)}")
                # Продолжаем обработку хода, так как попытки появились!
            else:
                # Попыток действительно нет
                msg = self.format_msg(contest.msg_out_of_attempts, name=first_name)
                cond = []
                if contest.repost_attempts > 0 and not player.repost_done:
                    cond.append("сделайте репост этой записи")
                if contest.like_attempts > 0 and not player.like_done:
                    cond.append("поставьте лайк этому посту")
                
                if cond:
                    msg += " Чтобы получить новые попытки, " + " и ".join(cond) + "."
                else:
                    msg += " Спасибо за участие!"
                    
                self.log_action(db, contest.id, user_id, first_name, last_name, "system", "Ход отклонен: закончились попытки")
                await self.reply_to_vk_comment(bot_token, group_id, post_id, comment_id, msg)
                return

        # 6. Обрабатываем ход по типу игры
        game_type = contest.game_type
        is_hit = False
        won_prize = None
        reply_text = ""
        attachment = None

        if game_type == "roulette":
            # Рулетка (крутить)
            if "крутить" in text.lower() or "рулетка" in text.lower():
                # Рассчитываем шанс на основе draw_probability_interval
                interval = contest.draw_probability_interval or 100
                base_chance = 1.0 / interval
                
                # Если включена защита от призоловов
                if contest.anti_prize_hunters:
                    is_hunter = await self.is_prize_hunter(bot_token, user_id)
                    if is_hunter:
                        logger.info(f"User {user_id} detected as prize hunter. Chance forced to 0%.")
                        base_chance = 0.0
                
                # Если включена помощь в розыгрыше призов при затягивании
                if contest.help_draw_prizes and base_chance > 0.0:
                    from sqlmodel import text as sql_text
                    total_moves_res = db.execute(
                        sql_text("SELECT SUM(attempts_used) FROM vk_contest_players WHERE contest_id = :cid"),
                        {"cid": contest.id}
                    ).fetchone()
                    total_moves = total_moves_res[0] or 0 if total_moves_res else 0
                    
                    # За каждые 100 попыток увеличиваем шанс выигрыша на +1%
                    bonus_chance = (total_moves // 100) * 0.01
                    final_chance = min(base_chance + bonus_chance, 0.5)
                else:
                    final_chance = base_chance
                
                # Генерируем случайное число
                is_win = random.random() <= final_chance
                
                if is_win:
                    # Ищем доступный приз
                    available_prizes = [p for p in contest.prizes if p.get("won_count", 0) < p.get("qty", 0)]
                    if available_prizes:
                        won_prize = random.choice(available_prizes)
                        is_hit = True
                
                if is_hit and won_prize:
                    reply_text = self.format_msg(contest.msg_win, name=first_name, prize=won_prize['name'])
                    self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Рулетка: выиграл приз '{won_prize['name']}'")
                else:
                    reply_text = self.format_msg(contest.msg_miss, name=first_name)
                    self.log_action(db, contest.id, user_id, first_name, last_name, "move", "Рулетка: промах")
            else:
                # Неверный формат команды
                return

        elif game_type == "safe":
            # Угадай код / Сейф (ищем 4-значное число)
            match_code = re.search(r'\b\d{4}\b', text)
            if not match_code:
                # Пропускаем комментарии, не содержащие 4-значный код
                return
                
            guessed_code = match_code.group(0)
            if guessed_code == contest.safe_code:
                # Угадал! Ищем доступные призы
                available_prizes = [p for p in contest.prizes if p.get("won_count", 0) < p.get("qty", 0)]
                if available_prizes:
                    won_prize = available_prizes[0] # Выдаем первый доступный суперприз
                    is_hit = True
                    reply_text = self.format_msg(contest.msg_win, name=first_name, prize=won_prize['name'], cell=guessed_code)
                    self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Сейф: угадал код {guessed_code} и выиграл приз '{won_prize['name']}'")
                else:
                    reply_text = f"🔓 {first_name}, вы угадали код {guessed_code}, но все призы в сейфе уже выиграны!"
                    self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Сейф: угадал код {guessed_code}, но призы закончились")
            else:
                reply_text = self.format_msg(contest.msg_miss, name=first_name, cell=guessed_code)
                self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Сейф: не угадал код (ввод: {guessed_code})")

        elif game_type == "knb":
            # Камень-ножницы-бумага
            user_choice = None
            for choice in ["камень", "ножницы", "бумага"]:
                if choice in text.lower():
                    user_choice = choice
                    break
                    
            if not user_choice:
                return # Не игра
                
            bot_choice = random.choice(["камень", "ножницы", "бумага"])
            emojis = {"камень": "✊ Камень", "ножницы": "✌️ Ножницы", "бумага": "✋ Бумага"}
            
            # Определяем раунд
            if user_choice == bot_choice:
                reply_text = f"🤝 Ничья! Вы выбрали {emojis[user_choice]}, я тоже выбрал {emojis[bot_choice]}. Давайте еще раз!"
                self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"КНБ: ничья ({user_choice} vs {bot_choice})")
            elif (user_choice == "камень" and bot_choice == "ножницы") or \
                 (user_choice == "ножницы" and bot_choice == "бумага") or \
                 (user_choice == "бумага" and bot_choice == "камень"):
                
                # Игрок победил раунд. Проверим шанс на выигрыш приза (35% шанс)
                is_win = random.randint(1, 100) <= 35
                if is_win:
                    available_prizes = [p for p in contest.prizes if p.get("won_count", 0) < p.get("qty", 0)]
                    if available_prizes:
                        won_prize = random.choice(available_prizes)
                        is_hit = True
                        
                if is_hit and won_prize:
                    reply_text = self.format_msg(contest.msg_win, name=first_name, prize=won_prize['name'])
                    self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"КНБ: выиграл у бота ({user_choice} vs {bot_choice}) и забрал приз '{won_prize['name']}'")
                else:
                    reply_text = f"👊 Победа! Вы выбрали {emojis[user_choice]}, а я {emojis[bot_choice]}. Вы победили меня в этом раунде, но приз не выпал. Попробуйте еще!"
                    self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"КНБ: выиграл у бота ({user_choice} vs {bot_choice}) - без приза")
            else:
                reply_text = f"😜 Ха-ха! Я победил! Вы выбрали {emojis[user_choice]}, а я {emojis[bot_choice]}. Не расстраивайтесь, сделайте еще один ход!"
                self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"КНБ: проиграл боту ({user_choice} vs {bot_choice})")

        elif game_type == "chests":
            # Сундуки (1..16)
            match_num = re.search(r'\b(1[0-6]|[1-9])\b', text)
            if not match_num:
                return # Нет цифры 1..16
                
            chest_num = match_num.group(0)
            field_data = contest.game_field_data or {}
            
            cell_info = field_data.get(chest_num, {})
            if cell_info.get("hit"):
                await self.reply_to_vk_comment(
                    bot_token, group_id, post_id, comment_id,
                    f"📦 {first_name}, сундук №{chest_num} уже открыт другим игроком! Пожалуйста, выберите другой сундук."
                )
                return
            
            # Открываем сундук
            cell_info["hit"] = True
            field_data[chest_num] = cell_info
            
            # Применяем изменения к полю
            contest.game_field_data = field_data
            db.add(contest)
            
            prize_id = cell_info.get("prize_id")
            if prize_id is not None:
                # Нашли приз!
                won_prize = next((p for p in contest.prizes if p["id"] == prize_id), None)
                if won_prize and won_prize.get("won_count", 0) < won_prize.get("qty", 0):
                    is_hit = True
                    reply_text = self.format_msg(contest.msg_win, name=first_name, prize=won_prize['name'], cell=chest_num)
                    self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Открыл сундук №{chest_num} и выиграл приз '{won_prize['name']}'")
                else:
                    reply_text = f"📦 {first_name}, вы открыли сундук №{chest_num}, но приз в нем уже закончился!"
                    self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Открыл сундук №{chest_num}, но приз уже забрали")
            else:
                reply_text = self.format_msg(contest.msg_miss, name=first_name, cell=chest_num)
                self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Открыл пустой сундук №{chest_num}")
                
            # Рисуем карту
            img = self.generate_chests_image(field_data)
            buf = BytesIO()
            img.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            
            # Сохраняем во временный файл для аплоада
            temp_f = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_f.write(img_bytes)
            temp_f.close()
            
            attachment = await vk_birthday_service.upload_vk_wall_photo(bot_token, temp_f.name, group_id)
            try:
                os.unlink(temp_f.name)
            except Exception:
                pass

        elif game_type == "seabattle":
            # Морской бой (А1-К10)
            coord = self.normalize_coordinate(text)
            if not coord:
                return # Не ход
                
            field_data = contest.game_field_data or {}
            cell_info = field_data.get(coord, {"prize_id": None, "hit": False})
            
            if cell_info.get("hit"):
                await self.reply_to_vk_comment(
                    bot_token, group_id, post_id, comment_id,
                    f"⚓ {first_name}, в сектор {coord} уже стреляли! Пожалуйста, выберите другие координаты."
                )
                return
                
            # Делаем выстрел
            cell_info["hit"] = True
            field_data[coord] = cell_info
            
            # Применяем изменения
            contest.game_field_data = field_data
            db.add(contest)
            
            prize_id = cell_info.get("prize_id")
            if prize_id is not None:
                # Попал!
                won_prize = next((p for p in contest.prizes if p["id"] == prize_id), None)
                if won_prize and won_prize.get("won_count", 0) < won_prize.get("qty", 0):
                    is_hit = True
                    reply_text = self.format_msg(contest.msg_win, name=first_name, prize=won_prize['name'], cell=coord)
                    self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Морской бой: выстрел в {coord} - попал и выиграл приз '{won_prize['name']}'")
                else:
                    reply_text = f"💥 Попадание в {coord}, но приз в этом секторе уже закончился!"
                    self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Морской бой: выстрел в {coord} - попал, но приз уже закончился")
            else:
                reply_text = self.format_msg(contest.msg_miss, name=first_name, cell=coord)
                self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Морской бой: выстрел в {coord} - промах")
                
            # Рисуем карту
            img = self.generate_seabattle_image(field_data)
            buf = BytesIO()
            img.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            
            # Сохраняем
            temp_f = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_f.write(img_bytes)
            temp_f.close()
            
            attachment = await vk_birthday_service.upload_vk_wall_photo(bot_token, temp_f.name, group_id)
            try:
                os.unlink(temp_f.name)
            except Exception:
                pass

        elif game_type == "battle":
            # Битва за поле (А1-К10)
            coord = self.normalize_coordinate(text)
            if not coord:
                return # Не ход
                
            field_data = contest.game_field_data or {}
            cell_info = field_data.get(coord, {"type": "empty", "owner_id": None, "first_name": "", "last_name": ""})
            
            if cell_info.get("owner_id") is not None:
                owner_name = cell_info.get("first_name", "Игрок")
                await self.reply_to_vk_comment(
                    bot_token, group_id, post_id, comment_id,
                    f"🏖️ {first_name}, ячейка {coord} уже занята участником {owner_name}! Выберите свободную ячейку."
                )
                return
                
            # Захватываем ячейку
            cell_info["owner_id"] = user_id
            cell_info["first_name"] = first_name
            cell_info["last_name"] = last_name
            field_data[coord] = cell_info
            
            # Применяем изменения
            contest.game_field_data = field_data
            db.add(contest)
            
            # Проверяем тип ячейки
            c_type = cell_info.get("type", "empty")
            if c_type == "penalty":
                player.penalties_hit += 1
                if player.penalties_hit >= 2:
                    player.is_game_over = True
                    player.attempts_left = 0
                    reply_text = f"💥 Штрафная ячейка {coord}! Это ваш второй штраф. Игра для вас окончена 🛑"
                    self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Битва за поле: занял ячейку {coord} - Мина 💥 (Второй штраф, GAME OVER)")
                else:
                    reply_text = f"⚠️ Внимание, {first_name}! Вы попали на штрафную ячейку {coord}. При повторном попадании игра для вас завершится!"
                    self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Битва за поле: занял ячейку {coord} - Мина 💥 (Первый штраф)")
            elif c_type == "bonus":
                player.attempts_left += 2
                reply_text = f"🎁 Бонус! Вы нашли бонусную ячейку {coord} и получаете +2 дополнительных хода! 🎉"
                self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Битва за поле: занял ячейку {coord} - Бонус +2 хода 🎁")
            else:
                reply_text = f"⚓ Отлично, {first_name}! Вы успешно заняли свободную ячейку {coord}."
                self.log_action(db, contest.id, user_id, first_name, last_name, "move", f"Битва за поле: занял свободную ячейку {coord} ⚓")
                
            # Рисуем карту пляжного боя
            img = self.generate_battle_image(field_data)
            buf = BytesIO()
            img.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            
            # Сохраняем во временный файл
            temp_f = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_f.write(img_bytes)
            temp_f.close()
            
            attachment = await vk_birthday_service.upload_vk_wall_photo(bot_token, temp_f.name, group_id)
            try:
                os.unlink(temp_f.name)
            except Exception:
                pass

        # 7. Записываем ход, списываем попытку
        player.attempts_left -= 1
        player.attempts_used += 1
        player.last_move_at = now
        db.add(player)
        
        # Информируем о количестве оставшихся попыток в конце сообщения
        if player.attempts_left > 0:
            reply_text += f"\n(У вас осталось попыток: {player.attempts_left})"
        else:
            reply_text += f"\n(У вас закончились попытки!)"

        # 8. Запись выигрыша приза
        if is_hit and won_prize:
            # Обновляем won_count приза в конкурсе
            prizes_updated = []
            for p in contest.prizes:
                if p["id"] == won_prize["id"]:
                     p["won_count"] = p.get("won_count", 0) + 1
                prizes_updated.append(p)
            contest.prizes = prizes_updated
            db.add(contest)
            
            # Генерируем уникальный промокод
            win_code = f"WIN-{random.randint(100000, 999999)}"
            
            # Запись победителя
            winner = VkContestWinner(
                contest_id=contest.id,
                vk_user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                prize_name=won_prize["name"],
                win_code=win_code,
                won_at=now
            )
            db.add(winner)
            
            # Отправка ЛС победителю
            try:
                from app.services.vk_bot_service import vk_bot_service
                msg_ls = self.format_msg(
                    contest.msg_pm_congratulations,
                    name=first_name,
                    title=contest.title,
                    prize=won_prize["name"],
                    code=win_code
                )
                # Отправляем сообщение через API ВК
                await vk_bot_service.send_message(user_id, msg_ls, account_id=None, bot_token_override=bot_token)
            except Exception as e:
                logger.error(f"Failed to send VK win PM: {e}")
                
        db.commit()

        # 9. Отправляем комментарий в ВК
        await self.reply_to_vk_comment(bot_token, group_id, post_id, comment_id, reply_text, attachment)

    def finish_battle_contest(self, db: Session, contest_id: int) -> Dict[str, Any]:
        """Подводит итоги пляжного боя, выявляет лидеров по ячейкам и раздает призы"""
        from app.models.vk_bot import VkBotConnection
        
        contest = db.get(VkContest, contest_id)
        if not contest:
            raise ValueError("Конкурс не найден")
            
        field_data = contest.game_field_data or {}
        
        # 1. Считаем ячейки для каждого vk_user_id
        user_scores = {}
        for coord, info in field_data.items():
            u_id = info.get("owner_id")
            if u_id is not None:
                user_scores[u_id] = user_scores.get(u_id, 0) + 1
                
        # 2. Сортируем пользователей по убыванию очков
        sorted_users = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 3. Собираем плоский список призов
        prizes_flat = []
        for p in contest.prizes:
            qty = p.get("qty", 1) - p.get("won_count", 0)
            if qty > 0:
                prizes_flat.extend([p] * qty)
                
        # 4. Распределяем призы победителям
        winners_list = []
        from app.services.vk_bot_service import vk_bot_service
        import random
        import asyncio
        
        # Получаем данные игроков для имен
        players_map = {}
        players = db.exec(select(VkContestPlayer).where(VkContestPlayer.contest_id == contest_id)).all()
        for pl in players:
            players_map[pl.vk_user_id] = pl
            
        now = datetime.utcnow()
        
        for idx, (u_id, score) in enumerate(sorted_users):
            if idx >= len(prizes_flat):
                break # Призы кончились
                
            prize_item = prizes_flat[idx]
            pl_info = players_map.get(u_id)
            f_name = pl_info.first_name if pl_info else "Игрок"
            l_name = pl_info.last_name if pl_info else ""
            
            win_code = f"WIN-{random.randint(100000, 999999)}"
            
            # Сохраняем победителя
            winner = VkContestWinner(
                contest_id=contest.id,
                vk_user_id=u_id,
                first_name=f_name,
                last_name=l_name,
                prize_name=prize_item["name"],
                win_code=win_code,
                won_at=now
            )
            db.add(winner)
            
            # Обновляем won_count в призе
            prizes_updated = []
            for p in contest.prizes:
                if p["id"] == prize_item["id"]:
                    p["won_count"] = p.get("won_count", 0) + 1
                prizes_updated.append(p)
            contest.prizes = prizes_updated
            db.add(contest)
            
            # Отправляем сообщение в ЛС победителю
            conn = db.get(VkBotConnection, contest.vk_bot_connection_id)
            if conn and conn.is_active:
                try:
                    msg_ls = self.format_msg(
                        contest.msg_pm_congratulations,
                        name=f_name,
                        title=contest.title,
                        prize=prize_item["name"],
                        code=win_code
                    )
                    # Вызываем отправку ЛС
                    asyncio.create_task(vk_bot_service.send_message(u_id, msg_ls, account_id=None, bot_token_override=contest.vk_bot_token or conn.vk_bot_token))
                except Exception as e:
                    logger.error(f"Error sending finish PM to {u_id}: {e}")
                    
            winners_list.append({
                "vk_user_id": u_id,
                "name": f"{f_name} {l_name}",
                "score": score,
                "prize": prize_item["name"]
            })
            
        # Деактивируем конкурс
        contest.is_active = False
        db.add(contest)
        db.commit()
        
        return {
            "status": "success",
            "winners": winners_list
        }

    def log_action(self, db: Session, contest_id: int, vk_user_id: int, first_name: str, last_name: str, action_type: str, detail: str):
        """Записывает действие участника в историю конкурса"""
        try:
            from app.models.vk_contest import VkContestAction
            action = VkContestAction(
                contest_id=contest_id,
                vk_user_id=vk_user_id,
                first_name=first_name,
                last_name=last_name,
                action_type=action_type,
                detail=detail
            )
            db.add(action)
        except Exception as e:
            logger.error(f"Error logging contest action: {e}")

vk_contest_service = VkContestService()
