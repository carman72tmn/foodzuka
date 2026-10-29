import asyncio
import logging
import httpx
from sqlmodel import Session, select
from app.core.database import engine
from app.models.vk_bot_connection import VkBotConnection
from app.models.vk_webhook_log import VkWebhookLog
from app.services.vk_service import process_vk_event

logger = logging.getLogger(__name__)

class VkLongPollManager:
    def __init__(self):
        self.active_tasks: dict[int, asyncio.Task] = {}

    def start_all_active_bots(self):
        """Запуск Long Poll для всех активных ботов, у которых включен use_longpoll"""
        with Session(engine) as db:
            bots = db.exec(
                select(VkBotConnection).where(
                    VkBotConnection.is_active == True,
                    VkBotConnection.use_longpoll == True
                )
            ).all()
            
            logger.info(f"Long Poll: Found {len(bots)} active bots with Long Poll enabled.")
            for bot in bots:
                self.start_bot(bot.id)

    def start_bot(self, bot_id: int):
        """Запуск Long Poll для конкретного бота"""
        self.stop_bot(bot_id)
        task = asyncio.create_task(self._run_longpoll(bot_id))
        self.active_tasks[bot_id] = task
        logger.info(f"Long Poll: Started listener task for bot_id={bot_id}")

    def stop_bot(self, bot_id: int):
        """Остановка Long Poll для конкретного бота"""
        if bot_id in self.active_tasks:
            task = self.active_tasks[bot_id]
            task.cancel()
            del self.active_tasks[bot_id]
            logger.info(f"Long Poll: Stopped listener task for bot_id={bot_id}")

    async def _run_longpoll(self, bot_id: int):
        """Бесконечный цикл опроса VK Long Poll API"""
        server = None
        key = None
        ts = None
        
        while True:
            try:
                # Получаем свежие данные бота
                with Session(engine) as db:
                    bot = db.get(VkBotConnection, bot_id)
                    if not bot or not bot.is_active or not bot.use_longpoll:
                        logger.info(f"Long Poll: Bot {bot_id} is no longer active or use_longpoll is False. Stopping task.")
                        break
                    
                    token = bot.vk_bot_token
                    group_id = bot.vk_group_id

                if not server or not key or not ts:
                    # Запрашиваем данные Long Poll сервера через api.vk.ru
                    url = f"https://api.vk.ru/method/groups.getLongPollServer"
                    params = {
                        "group_id": group_id,
                        "access_token": token,
                        "v": "5.199"
                    }
                    async with httpx.AsyncClient() as client:
                        resp = await client.get(url, params=params)
                        res_json = resp.json()
                        if "error" in res_json:
                            logger.error(f"Long Poll: Error getting Long Poll server for bot {bot_id}: {res_json['error']}")
                            await asyncio.sleep(10) # пауза перед повторной попыткой
                            continue
                        
                        response_data = res_json.get("response", {})
                        server = response_data.get("server")
                        key = response_data.get("key")
                        ts = response_data.get("ts")
                        
                        if not server:
                            logger.error(f"Long Poll: Server URL is empty in response: {res_json}")
                            await asyncio.sleep(10)
                            continue

                # Принудительно заменяем lp.vk.com на lp.vk.ru для соответствия требованию домена .ru
                if "vk.com" in server:
                    server = server.replace("vk.com", "vk.ru")

                # Делаем запрос к Long Poll серверу
                async with httpx.AsyncClient(timeout=30) as client:
                    lp_resp = await client.get(
                        server,
                        params={
                            "act": "a_check",
                            "key": key,
                            "ts": ts,
                            "wait": 25
                        }
                    )
                    lp_data = lp_resp.json()

                if "failed" in lp_data:
                    failed = lp_data["failed"]
                    logger.warning(f"Long Poll: Server returned failed={failed} for bot {bot_id}. Resetting connection params.")
                    if failed == 1:
                        ts = lp_data.get("ts")
                    elif failed in [2, 3]:
                        server, key, ts = None, None, None
                    continue

                ts = lp_data.get("ts")
                updates = lp_data.get("updates", [])
                
                if updates:
                    logger.info(f"Long Poll: Received {len(updates)} events for bot {bot_id}")
                    for update in updates:
                        # Обрабатываем событие в фоновой задаче с новой сессией БД
                        asyncio.create_task(self._process_event_safely(update, token, group_id))

            except asyncio.CancelledError:
                logger.info(f"Long Poll: Task for bot {bot_id} cancelled.")
                raise
            except Exception as e:
                logger.error(f"Long Poll: Exception in loop for bot {bot_id}: {e}", exc_info=True)
                # Сбрасываем параметры в случае сетевых сбоев
                server, key, ts = None, None, None
                await asyncio.sleep(5)

    async def _process_event_safely(self, update: dict, token: str, group_id: int):
        event_type = update.get("type")
        
        # Логируем входящее событие в БД vk_webhook_logs для прозрачности
        try:
            with Session(engine) as db:
                log_entry = VkWebhookLog(event_type=event_type or "unknown", payload=update, vk_group_id=group_id)
                db.add(log_entry)
                db.commit()
                db.refresh(log_entry)
                
                # Обрабатываем событие через стандартный обработчик vk_service
                await process_vk_event(update, db, token, group_id)
        except Exception as e:
            logger.error(f"Long Poll: Error processing event safely: {e}", exc_info=True)

vk_longpoll_manager = VkLongPollManager()
