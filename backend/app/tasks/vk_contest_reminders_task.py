import asyncio
import logging
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.core.celery_app import celery_app
from app.core.database import engine
from app.models.vk_contest import VkContest, VkContestPlayer
from app.models.vk_bot_connection import VkBotConnection
from app.services.vk_contest_service import vk_contest_service

logger = logging.getLogger(__name__)

def is_quiet_hour(hour: int, quiet_from: int, quiet_to: int) -> bool:
    """Проверяет, попадает ли текущий час в интервал тихого часа"""
    if quiet_from == quiet_to:
        return False
    if quiet_from < quiet_to:
        return quiet_from <= hour < quiet_to
    else:
        return hour >= quiet_from or hour < quiet_to

def get_attempts_text(n: int) -> str:
    """Возвращает правильное склонение слова 'попытка'"""
    if n % 10 == 1 and n % 100 != 11:
        return "попытка"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return "попытки"
    else:
        return "попыток"

def get_game_keyword(game_type: str) -> str:
    """Возвращает ключевое слово для напоминания в зависимости от типа игры"""
    if game_type == "roulette":
        return "крутить"
    elif game_type == "safe":
        return "4-значный код"
    elif game_type == "chests":
        return "номер сундука (1-16)"
    elif game_type == "seabattle":
        return "координаты (например, А5)"
    elif game_type == "knb":
        return "камень, ножницы или бумага"
    return "ход"

async def send_contest_reminders():
    """Асинхронная логика рассылки напоминаний о неиспользованных попытках"""
    with Session(engine) as session:
        # Находим все активные конкурсы, в которых включены напоминания
        contests = session.exec(
            select(VkContest)
            .where(VkContest.is_active == True)
            .where(VkContest.remind_attempts == True)
        ).all()
        
        if not contests:
            return
            
        now = datetime.utcnow()
        # Московское время (UTC + 3) для тихого часа
        msk_now = now + timedelta(hours=3)
        msk_hour = msk_now.hour
        
        for contest in contests:
            # Проверяем тихий час по московскому времени
            q_from = contest.remind_attempts_quiet_from
            q_to = contest.remind_attempts_quiet_to
            if is_quiet_hour(msk_hour, q_from, q_to):
                logger.info(f"Contest {contest.id} is in quiet hour (MSK hour: {msk_hour}, quiet: {q_from}-{q_to}). Skipping reminders.")
                continue
                
            # Получаем подключение ВК для этого бота
            conn = session.get(VkBotConnection, contest.vk_bot_connection_id)
            if not conn or not conn.is_active:
                continue
                
            # Ищем игроков, которые:
            # 1. Имеют неиспользованные попытки (attempts_left > 0)
            # 2. Уже делали ходы (attempts_used > 0)
            # 3. Ещё не исчерпали лимит напоминаний (reminders_sent < remind_attempts_count)
            # 4. Сделали последний ход достаточно давно
            players = session.exec(
                select(VkContestPlayer)
                .where(VkContestPlayer.contest_id == contest.id)
                .where(VkContestPlayer.attempts_left > 0)
                .where(VkContestPlayer.attempts_used > 0)
                .where(VkContestPlayer.reminders_sent < contest.remind_attempts_count)
            ).all()
            
            for player in players:
                if not player.last_move_at:
                    continue
                    
                elapsed_minutes = (now - player.last_move_at).total_seconds() / 60.0
                
                # Логика интервалов напоминаний:
                # 1-е напоминание: через 10 минут
                # 2-е напоминание: через 30 минут
                # 3-е напоминание: через 3 часа (180 минут)
                should_remind = False
                if player.reminders_sent == 0 and elapsed_minutes >= 10:
                    should_remind = True
                elif player.reminders_sent == 1 and elapsed_minutes >= 30:
                    should_remind = True
                elif player.reminders_sent == 2 and elapsed_minutes >= 180:
                    should_remind = True
                    
                if should_remind:
                    # Отправляем напоминание
                    keyword = get_game_keyword(contest.game_type)
                    attempts_text = get_attempts_text(player.attempts_left)
                    
                    msg = f"🔔 @id{player.vk_user_id} ({player.first_name}), напоминаем: у вас осталось {player.attempts_left} {attempts_text}! Напишите «{keyword}», чтобы продолжить игру!"
                    
                    try:
                        logger.info(f"Sending attempt reminder ({player.reminders_sent + 1}) to user {player.vk_user_id} for contest {contest.id}")
                        
                        # В ВК комментируем под постом (wall.createComment). 
                        # Так как мы отвечаем под пост конкурса, мы не привязываем коммент к конкретной ветке (reply_to_comment = None),
                        # но тегаем игрока через @idXXXX.
                        await vk_contest_service.reply_to_vk_comment(
                            bot_token=conn.vk_bot_token,
                            group_id=conn.vk_group_id,
                            post_id=contest.post_id,
                            comment_id=0, # 0 означает комментарий первого уровня
                            message=msg
                        )
                        
                        # Обновляем счетчик отправленных напоминаний
                        player.reminders_sent += 1
                        session.add(player)
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        logger.error(f"Failed to send VK contest reminder to user {player.vk_user_id}: {e}")

@celery_app.task(name="app.tasks.vk_contest_reminders_task.vk_contest_reminders_task")
def vk_contest_reminders_task():
    """Периодическая Celery-задача для отправки напоминаний игрокам о попытках"""
    logger.info("Starting VK contest reminders task...")
    
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        loop.run_until_complete(send_contest_reminders())
        return {"status": "success"}
    except Exception as e:
        logger.error(f"VK contest reminders task failed: {e}", exc_info=True)
        raise e
