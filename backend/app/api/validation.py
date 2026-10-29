"""
Роутер для управления настройками валидации телефонов и тестирования RedSMS
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.user import User
from app.api.deps import require_permission
from app.models.validation_settings import ValidationSettings
from app.services.validation_service import validation_service
from app.core.datetime_utils import utc_now

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Схемы Pydantic ---

class ValidationSettingsSchema(BaseModel):
    id: Optional[int] = None
    is_active: bool = False
    provider: str = "red_sms"
    api_login: Optional[str] = None
    api_key: Optional[str] = None
    sender_name: Optional[str] = "REDSMS"
    wait_call_num: Optional[str] = None
    wait_call_no_voice: bool = False
    active_route: str = "sms"
    cascade_routes: str = "fcall,voice,sms"
    cascade_delay: int = 30
    
    # ВКонтакте верификация
    vk_verification_method: str = "none"
    vk_mini_app_id: Optional[int] = None
    vk_mini_app_secret: Optional[str] = None
    vk_lead_form_url: Optional[str] = None
    
    # Текстовые сообщения и шаги для ВК-бота верификации
    vk_alternative_methods: str = "fcall,wcall,tg,max"
    vk_msg_start: Optional[str] = None
    vk_msg_choose_method: Optional[str] = None
    vk_msg_fcall_prompt: Optional[str] = None
    vk_msg_fcall_code: Optional[str] = None
    vk_msg_wcall_prompt: Optional[str] = None
    vk_msg_wcall_instruct: Optional[str] = None
    vk_msg_tg_instruct: Optional[str] = None
    vk_msg_max_instruct: Optional[str] = None
    vk_msg_success: Optional[str] = None
    vk_msg_error_code: Optional[str] = None

    # Telegram бот для клиентов
    telegram_bot_token: Optional[str] = None
    telegram_bot_username: Optional[str] = None

    # МАКС бот для клиентов
    max_bot_token: Optional[str] = None
    max_bot_username: Optional[str] = None

    class Config:
        from_attributes = True

class TestSendSchema(BaseModel):
    phone: str = Field(..., description="Номер телефона для тестирования в формате +79991234567")
    code: Optional[str] = Field(None, description="Код подтверждения (4-6 цифр), если не указан - сгенерируется случайно")
    route: Optional[str] = Field(None, description="Принудительный канал отправки (sms, voice, wcall, fcall, cascade)")


# --- Эндпоинты ---

@router.get("/settings", response_model=ValidationSettingsSchema)
def get_validation_settings(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_validation_view"))
):
    """Получение настроек валидации телефонов"""
    settings = db.exec(select(ValidationSettings)).first()
    if not settings:
        # Возвращаем дефолтные настройки
        return ValidationSettingsSchema()
    return settings


def register_max_webhook(token: str):
    """Регистрация вебхука в MAX API"""
    from app.core.config import settings as app_settings
    import requests
    
    base_url = app_settings.APP_PUBLIC_URL or "https://vezuroll.ru"
    base_url = base_url.rstrip("/")
    
    webhook_url = f"{base_url}/api/v1/validation/max-webhook"
    api_url = "https://platform-api2.max.ru/subscriptions"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    payload = {
        "url": webhook_url,
        "update_types": ["message_created", "bot_started"]
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, verify=False, timeout=10)
        logger.info(f"MAX Webhook registration status {response.status_code}: {response.text}")
        return response.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Failed to register MAX webhook: {e}")
        return False


@router.post("/settings", response_model=ValidationSettingsSchema)
def save_validation_settings(
    data: ValidationSettingsSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_validation_edit"))
):
    """Сохранение настроек валидации телефонов"""
    settings = db.exec(select(ValidationSettings)).first()
    
    token_changed = False
    if settings:
        if data.max_bot_token != settings.max_bot_token:
            token_changed = True
    else:
        if data.max_bot_token:
            token_changed = True
            
    if settings:
        settings.is_active = data.is_active
        settings.provider = data.provider
        settings.api_login = data.api_login
        settings.api_key = data.api_key
        settings.sender_name = data.sender_name
        settings.wait_call_num = data.wait_call_num
        settings.wait_call_no_voice = data.wait_call_no_voice
        settings.active_route = data.active_route
        settings.cascade_routes = data.cascade_routes
        settings.cascade_delay = data.cascade_delay
        
        # ВК настройки
        settings.vk_verification_method = data.vk_verification_method
        settings.vk_mini_app_id = data.vk_mini_app_id
        settings.vk_mini_app_secret = data.vk_mini_app_secret
        settings.vk_lead_form_url = data.vk_lead_form_url
        
        # ВК сообщения
        settings.vk_alternative_methods = data.vk_alternative_methods
        settings.vk_msg_start = data.vk_msg_start
        settings.vk_msg_choose_method = data.vk_msg_choose_method
        settings.vk_msg_fcall_prompt = data.vk_msg_fcall_prompt
        settings.vk_msg_fcall_code = data.vk_msg_fcall_code
        settings.vk_msg_wcall_prompt = data.vk_msg_wcall_prompt
        settings.vk_msg_wcall_instruct = data.vk_msg_wcall_instruct
        settings.vk_msg_tg_instruct = data.vk_msg_tg_instruct
        settings.vk_msg_max_instruct = data.vk_msg_max_instruct
        settings.vk_msg_success = data.vk_msg_success
        settings.vk_msg_error_code = data.vk_msg_error_code
        
        # TG настройки
        settings.telegram_bot_token = data.telegram_bot_token
        settings.telegram_bot_username = data.telegram_bot_username
        
        # MAX настройки
        settings.max_bot_token = data.max_bot_token
        settings.max_bot_username = data.max_bot_username
    else:
        settings = ValidationSettings(
            is_active=data.is_active,
            provider=data.provider,
            api_login=data.api_login,
            api_key=data.api_key,
            sender_name=data.sender_name,
            wait_call_num=data.wait_call_num,
            wait_call_no_voice=data.wait_call_no_voice,
            active_route=data.active_route,
            cascade_routes=data.cascade_routes,
            cascade_delay=data.cascade_delay,
            
            vk_verification_method=data.vk_verification_method,
            vk_mini_app_id=data.vk_mini_app_id,
            vk_mini_app_secret=data.vk_mini_app_secret,
            vk_lead_form_url=data.vk_lead_form_url,
            
            vk_alternative_methods=data.vk_alternative_methods,
            vk_msg_start=data.vk_msg_start,
            vk_msg_choose_method=data.vk_msg_choose_method,
            vk_msg_fcall_prompt=data.vk_msg_fcall_prompt,
            vk_msg_fcall_code=data.vk_msg_fcall_code,
            vk_msg_wcall_prompt=data.vk_msg_wcall_prompt,
            vk_msg_wcall_instruct=data.vk_msg_wcall_instruct,
            vk_msg_tg_instruct=data.vk_msg_tg_instruct,
            vk_msg_max_instruct=data.vk_msg_max_instruct,
            vk_msg_success=data.vk_msg_success,
            vk_msg_error_code=data.vk_msg_error_code,
            
            telegram_bot_token=data.telegram_bot_token,
            telegram_bot_username=data.telegram_bot_username,
            
            max_bot_token=data.max_bot_token,
            max_bot_username=data.max_bot_username
        )
        db.add(settings)
        
    db.commit()
    db.refresh(settings)
    
    # Автоматическая регистрация вебхука при изменении токена
    if token_changed and settings.max_bot_token:
        register_max_webhook(settings.max_bot_token)
        
    return settings


@router.post("/test-send")
async def test_send_verification(
    data: TestSendSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_validation_edit"))
):
    """Тестовая отправка кода верификации через RedSMS"""
    import random
    
    # 1. Если код не передан, генерируем случайный 4-значный код
    code = data.code
    if not code:
        code = str(random.randint(1000, 9999))
        
    # 2. Вызываем сервис отправки
    try:
        result = await validation_service.send_verification(
            db=db,
            phone=data.phone,
            code=code,
            custom_route=data.route
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Ошибка отправки кода")
            )
            
        return {
            "status": "success",
            "code_sent": code,
            "response": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка при тестовой отправке кода: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@router.post("/clear-sessions")
def clear_bot_sessions(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings_validation_edit"))
):
    """Принудительный сброс всех активных сессий верификации ВКонтакте"""
    from app.models.bot_command import BotUserState
    try:
        statement = select(BotUserState).where(BotUserState.messenger == "vk")
        results = db.exec(statement).all()
        for state in results:
            db.delete(state)
        db.commit()
        return {
            "status": "success",
            "message": "Все активные сессии верификации ВКонтакте успешно сброшены"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при очистке сессий бота: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось сбросить сессии: {str(e)}"
        )


# --- Новые вебхуки и методы интеграции ---

class VkMiniAppVerificationSchema(BaseModel):
    vk_id: int
    phone: str
    query_params: str

@router.post("/vk-miniapp-phone")
async def verify_vk_miniapp_phone(
    data: VkMiniAppVerificationSchema,
    db: Session = Depends(get_session)
):
    """Верификация номера из VK Mini App с проверкой подписи"""
    settings = db.exec(select(ValidationSettings)).first()
    if not settings or settings.vk_verification_method != "mini_app":
        raise HTTPException(status_code=400, detail="Верификация через Mini App отключена")
    
    if not settings.vk_mini_app_secret:
        raise HTTPException(status_code=400, detail="Не настроен защищенный ключ Mini App")
        
    # Проверяем подпись query_params
    import hmac
    import hashlib
    from urllib.parse import parse_qsl, urlencode
    import base64
    
    try:
        raw_params = {}
        q_str = data.query_params.lstrip('?')
        for item in q_str.split('&'):
            if not item:
                continue
            if '=' in item:
                k, v = item.split('=', 1)
                raw_params[k] = v
            else:
                raw_params[item] = ''
                
        vk_sign = raw_params.get("sign")
        if not vk_sign:
            raise ValueError("Параметр sign отсутствует в query_params")
            
        vk_params = {k: v for k, v in raw_params.items() if k.startswith("vk_")}
        sorted_params = sorted(vk_params.items())
        query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
        
        hash_obj = hmac.new(
            settings.vk_mini_app_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        )
        
        # 1. Вариант в hex формате (стандартный для параметров запуска ВК)
        expected_sign_hex = hash_obj.hexdigest()
        
        # 2. Вариант в base64url формате (резервный)
        expected_sign_b64 = base64.b64encode(hash_obj.digest()).decode("utf-8")
        expected_sign_b64 = expected_sign_b64.replace("+", "-").replace("/", "_").rstrip("=")
        
        if not hmac.compare_digest(vk_sign, expected_sign_hex) and not hmac.compare_digest(vk_sign, expected_sign_b64):
            raise ValueError(f"Несоответствие подписи. Получено: {vk_sign}, ожидалось: {expected_sign_hex} (hex) или {expected_sign_b64} (b64)")
            
        # Проверяем, что vk_id из тела совпадает с vk_user_id из query_params
        vk_user_id_param = raw_params.get("vk_user_id")
        if not vk_user_id_param or int(vk_user_id_param) != data.vk_id:
            raise ValueError("ID пользователя не совпадает")
            
    except Exception as e:
        logger.error(f"VK Signature verification failed: {e}")
        raise HTTPException(status_code=400, detail=f"Ошибка проверки подписи VK: {str(e)}")
        
    # Подпись проверена. Привязываем телефон
    phone_digits = "".join(c for c in data.phone if c.isdigit())
    if len(phone_digits) == 11 and (phone_digits.startswith("8") or phone_digits.startswith("7")):
        phone_digits = "7" + phone_digits[1:]
    elif len(phone_digits) == 10 and phone_digits.startswith("9"):
        phone_digits = "7" + phone_digits
        
    if len(phone_digits) != 11 or not phone_digits.startswith("7"):
        raise HTTPException(status_code=400, detail="Неверный формат номера телефона")
        
    db_phone = f"+{phone_digits}"
    
    # Связываем пользователя ВК и Customer
    from app.services.vk_service import send_vk_message, fetch_vk_user_info, link_phone_to_vk_user
    from app.models.vk_user import VkUser
    from app.models.vk_settings import VkSettings
    from app.models.vk_bot_connection import VkBotConnection
    
    vk_settings = db.exec(select(VkSettings)).first()
    bot_token = vk_settings.vk_bot_token if vk_settings else None
    
    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == data.vk_id)).first()
    group_id = vk_user.vk_group_id if vk_user else None
    if group_id:
        bot_conn = db.exec(select(VkBotConnection).where(VkBotConnection.vk_group_id == group_id, VkBotConnection.is_active == True)).first()
        if bot_conn:
            bot_token = bot_conn.vk_bot_token
            
    # Привязываем и получаем баланс
    points = await link_phone_to_vk_user(db, data.vk_id, db_phone, bot_token, group_id, source="miniapp")
    
    # Удаляем FSM
    from app.models.bot_command import BotUserState, BotCommand
    user_state = db.exec(
        select(BotUserState)
        .where(BotUserState.messenger == "vk")
        .where(BotUserState.peer_id == str(data.vk_id))
    ).first()
    
    cmd = None
    if user_state and user_state.command_id:
        cmd = db.get(BotCommand, user_state.command_id)
        
    if user_state:
        db.delete(user_state)
        db.commit()
        
    if bot_token:
        if cmd and cmd.action_type == "transfer_points":
            from app.services.vk_service import transfer_vk_points_to_iiko
            msg = await transfer_vk_points_to_iiko(db, vk_user, group_id, bot_token)
        else:
            settings = db.exec(select(ValidationSettings)).first()
            msg = (settings.vk_msg_success.replace("{balance}", str(int(points))) if settings and settings.vk_msg_success 
                   else f"Подтверждение через VK Mini App успешно пройдено! Ваш бонусный баланс: {int(points)} бонусов.")
        await send_vk_message(
            vk_id=data.vk_id,
            message=msg,
            bot_token=bot_token
        )
        
    return {"status": "success", "phone": db_phone, "bonus_balance": points}


@router.post("/telegram-webhook")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_session)
):
    """Вебхук для Telegram-бота подтверждения клиентов"""
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"TG Webhook invalid JSON: {e}")
        return {"status": "ok"}
        
    # 1. Проверяем нажатие инлайн-кнопок курьером (callback_query)
    callback_query = data.get("callback_query")
    if callback_query:
        cb_data = callback_query.get("data", "")
        cb_id = callback_query.get("id")
        from_id = callback_query.get("from", {}).get("id")
        if cb_data.startswith("cdeliv:"):
            parts = cb_data.split(":")
            if len(parts) >= 3:
                try:
                    order_id = int(parts[1])
                    pay = parts[2]
                    from app.services.vk_notification_router import handle_courier_order_action
                    import asyncio
                    asyncio.create_task(handle_courier_order_action(order_id, pay, "tg", str(from_id)))
                    settings = db.exec(select(ValidationSettings)).first()
                    bot_token = settings.telegram_bot_token if settings else None
                    if bot_token and cb_id:
                        import httpx
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            await client.post(
                                f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery",
                                json={"callback_query_id": cb_id, "text": "✅ Заказ отмечен как доставленный!"}
                            )
                except Exception as e_tg_cb:
                    logger.error(f"Error handling Telegram courier callback: {e_tg_cb}")
        return {"status": "ok"}

    message = data.get("message")
    if not message:
        return {"status": "ok"}
        
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    contact = message.get("contact")
    
    if not chat_id:
        return {"status": "ok"}
        
    settings = db.exec(select(ValidationSettings)).first()
    if not settings or not settings.telegram_bot_token:
        return {"status": "ok"}
        
    bot_token = settings.telegram_bot_token
    
    # Логируем входящее сообщение в Мультичат
    try:
        from app.models.chat import MultichatMessage
        from app.api.chat import manager
        import asyncio
        
        from_user = message.get("from", {})
        first_name = from_user.get("first_name", "")
        last_name = from_user.get("last_name", "")
        username = from_user.get("username", "")
        peer_name = f"{first_name} {last_name}".strip() or username or f"Telegram User {chat_id}"
        
        msg_text = text or ""
        if not msg_text and contact:
            phone_num = contact.get("phone_number", "")
            msg_text = f"Отправлен контакт: {phone_num}"
            
        if msg_text:
            multichat_msg = MultichatMessage(
                channel="telegram_bot",
                channel_id=settings.telegram_bot_username or "bot",
                peer_id=str(chat_id),
                peer_name=peer_name,
                peer_avatar=None,
                from_id=str(from_user.get("id") or chat_id),
                text=msg_text,
                direction="inbound",
                external_id=str(message.get("message_id")) if message.get("message_id") else None,
                is_read=False,
                payload=data
            )
            db.add(multichat_msg)
            db.commit()
            
            # Вебсокет-уведомление с поддержкой флага скрытия и медиа-вложений
            try:
                from app.api.multichat import broadcast_ws_message
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(broadcast_ws_message(multichat_msg))
                else:
                    loop.run_until_complete(broadcast_ws_message(multichat_msg))
            except Exception as ws_ex:
                logger.debug(f"WS broadcast error for Telegram in validation: {ws_ex}")
    except Exception as e:
        logger.error(f"Error logging Telegram message to multichat: {e}")

    # Обработка ответа курьера в Telegram
    try:
        from app.services.vk_service import handle_courier_social_feedback
        tg_sender_id = (from_user.get("id") if from_user else None) or chat_id
        if tg_sender_id:
            await handle_courier_social_feedback("tg", tg_sender_id, "reply", msg_text, db)
    except Exception as cf_err:
        logger.debug(f"Courier feedback handling from TG: {cf_err}")

    from app.services.vk_notification_router import send_telegram_message
    from app.models.bot_command import BotUserState
    
    # 1. Обработка команды /start VK{vk_id}
    if text and text.startswith("/start"):
        parts = text.split()
        vk_id = None
        if len(parts) > 1 and parts[1].startswith("VK"):
            try:
                vk_id = int(parts[1].replace("VK", ""))
            except ValueError:
                pass
                
        if vk_id:
            user_state = db.exec(
                select(BotUserState)
                .where(BotUserState.messenger == "telegram")
                .where(BotUserState.peer_id == str(chat_id))
            ).first()
            
            if user_state:
                user_state.state = "awaiting_tg_contact"
                user_state.context_data = {"vk_id": vk_id}
            else:
                user_state = BotUserState(
                    messenger="telegram",
                    peer_id=str(chat_id),
                    state="awaiting_tg_contact",
                    context_data={"vk_id": vk_id}
                )
            db.add(user_state)
            db.commit()
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": "Для подтверждения номера телефона нажмите кнопку «📱 Поделиться контактом» ниже.",
                "reply_markup": {
                    "keyboard": [
                        [
                            {
                                "text": "📱 Поделиться контактом",
                                "request_contact": True
                            }
                        ]
                    ],
                    "one_time_keyboard": True,
                    "resize_keyboard": True
                }
            }
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload)
        else:
            await send_telegram_message(
                chat_id=chat_id,
                text="Привет! Этот бот используется для подтверждения номера телефона в ВКонтакте. Перейдите в диалог с группой ВК, чтобы получить ссылку на авторизацию.",
                token=bot_token
            )
            
    # 2. Обработка контакта
    elif contact:
        phone = contact.get("phone_number")
        contact_user_id = contact.get("user_id")
        from_user_id = message.get("from", {}).get("id")
        
        if contact_user_id and contact_user_id != from_user_id:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": "Пожалуйста, отправьте именно СВОЙ контакт через встроенную кнопку."
            }
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload)
            return {"status": "ok"}
            
        user_state = db.exec(
            select(BotUserState)
            .where(BotUserState.messenger == "telegram")
            .where(BotUserState.peer_id == str(chat_id))
            .where(BotUserState.state == "awaiting_tg_contact")
        ).first()
        
        if user_state and phone:
            vk_id = user_state.context_data.get("vk_id")
            
            phone_digits = "".join(c for c in phone if c.isdigit())
            if len(phone_digits) == 11 and (phone_digits.startswith("8") or phone_digits.startswith("7")):
                phone_digits = "7" + phone_digits[1:]
            elif len(phone_digits) == 10 and phone_digits.startswith("9"):
                phone_digits = "7" + phone_digits
                
            db_phone = f"+{phone_digits}"
            
            from app.models.vk_user import VkUser
            from app.models.customer import Customer
            from app.services.vk_service import send_vk_message, fetch_vk_user_info
            from app.models.vk_settings import VkSettings
            from app.models.vk_bot_connection import VkBotConnection
            from app.services.iiko_service import iiko_service
            
            vk_settings = db.exec(select(VkSettings)).first()
            vk_bot_token = vk_settings.vk_bot_token if vk_settings else None
            
            vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
            group_id = vk_user.vk_group_id if vk_user else None
            if group_id:
                bot_conn = db.exec(select(VkBotConnection).where(VkBotConnection.vk_group_id == group_id, VkBotConnection.is_active == True)).first()
                if bot_conn:
                    vk_bot_token = bot_conn.vk_bot_token
                    
            # Привязываем и получаем баланс
            from app.services.vk_service import link_phone_to_vk_user
            points = await link_phone_to_vk_user(db, vk_id, db_phone, vk_bot_token, group_id, source="telegram")
            
            db.delete(user_state)
            
            vk_user_state = db.exec(
                select(BotUserState)
                .where(BotUserState.messenger == "vk")
                .where(BotUserState.peer_id == str(vk_id))
            ).first()
            if vk_user_state:
                db.delete(vk_user_state)
                
            db.commit()
            
            url_send = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload_send = {
                "chat_id": chat_id,
                "text": "Номер телефона успешно подтвержден! Вы можете вернуться в диалог ВКонтакте.",
                "reply_markup": {"remove_keyboard": True}
            }
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(url_send, json=payload_send)
                
            if vk_bot_token:
                settings = db.exec(select(ValidationSettings)).first()
                msg = (settings.vk_msg_success.replace("{balance}", str(int(points))) if settings and settings.vk_msg_success 
                       else f"Проверка через Telegram пройдена успешно! Ваш бонусный баланс: {int(points)} бонусов.")
                await send_vk_message(
                    vk_id=vk_id,
                    message=msg,
                    bot_token=vk_bot_token
                )
                
    return {"status": "ok"}


@router.post("/max-webhook")
async def max_webhook(
    request: Request,
    db: Session = Depends(get_session)
):
    """Вебхук для МАКС-бота подтверждения клиентов по MAX API v2"""
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"MAX Webhook invalid JSON: {e}")
        return {"status": "ok"}
        
    logger.info(f"Received MAX Webhook payload: {data}")
    
    update_type = data.get("update_type")
    chat_id = data.get("chat_id")
    
    # Извлекаем message и body
    message = data.get("message", {})
    body = message.get("body", {})
    text = body.get("text", "")
    
    # Для обратной совместимости проверим старый формат
    if not chat_id:
        chat_id = data.get("chat", {}).get("chatId")
        text = data.get("text", "")
        
    if not chat_id:
        return {"status": "ok"}
        
    settings = db.exec(select(ValidationSettings)).first()
    if not settings or not settings.max_bot_token:
        return {"status": "ok"}
        
    bot_token = settings.max_bot_token

    # Логируем входящее сообщение в Мультичат
    try:
        from app.models.chat import MultichatMessage
        from app.api.chat import manager
        import asyncio
        
        from_user = message.get("from", {})
        first_name = from_user.get("firstName") or from_user.get("first_name", "")
        last_name = from_user.get("lastName") or from_user.get("last_name", "")
        username = from_user.get("userId") or from_user.get("username", "")
        peer_name = f"{first_name} {last_name}".strip() or username or f"MAX User {chat_id}"
        
        if text:
            multichat_msg = MultichatMessage(
                channel="max_bot",
                channel_id=settings.max_bot_username or "bot",
                peer_id=str(chat_id),
                peer_name=peer_name,
                peer_avatar=None,
                from_id=str(from_user.get("userId") or chat_id),
                text=text,
                direction="inbound",
                external_id=str(message.get("msgId")) if message.get("msgId") else None,
                is_read=False,
                payload=data
            )
            db.add(multichat_msg)
            db.commit()
            
            # Вебсокет-уведомление с поддержкой флага скрытия и медиа-вложений
            try:
                from app.api.multichat import broadcast_ws_message
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(broadcast_ws_message(multichat_msg))
                else:
                    loop.run_until_complete(broadcast_ws_message(multichat_msg))
            except Exception as ws_ex:
                logger.debug(f"WS broadcast error for MAX Bot in validation: {ws_ex}")
    except Exception as e:
        logger.error(f"Error logging MAX message to multichat: {e}")

    async def send_max_bot_message(chat_id_val: str, text_val: str, inline_keyboard: list = None):
        url = "https://platform-api2.max.ru/messages"
        params = {
            "chat_id": chat_id_val
        }
        headers = {
            "Authorization": bot_token,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text_val
        }
        if inline_keyboard:
            payload["attachments"] = [
                {
                    "type": "inline_keyboard",
                    "payload": {
                        "buttons": inline_keyboard
                    }
                }
            ]
        import httpx
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(url, params=params, headers=headers, json=payload, timeout=10)
                logger.info(f"MAX send message response {response.status_code}: {response.text}")
        except Exception as ex:
            logger.error(f"Error sending MAX message: {ex}")

    # 1. Проверяем команду /start
    if text and text.startswith("/start"):
        parts = text.split()
        vk_id = None
        if len(parts) > 1 and parts[1].startswith("VK"):
            try:
                vk_id = int(parts[1].replace("VK", ""))
            except ValueError:
                pass
                
        if vk_id:
            from app.models.bot_command import BotUserState
            user_state = db.exec(
                select(BotUserState)
                .where(BotUserState.messenger == "max")
                .where(BotUserState.peer_id == str(chat_id))
            ).first()
            
            if user_state:
                user_state.state = "awaiting_max_contact"
                user_state.context_data = {"vk_id": vk_id}
            else:
                user_state = BotUserState(
                    messenger="max",
                    peer_id=str(chat_id),
                    state="awaiting_max_contact",
                    context_data={"vk_id": vk_id}
                )
            db.add(user_state)
            db.commit()
            
            inline_kb = [
                [
                    {
                        "type": "request_contact",
                        "text": "📱 Поделиться контактом"
                    }
                ]
            ]
            await send_max_bot_message(
                chat_id_val=str(chat_id),
                text_val="Для подтверждения номера телефона нажмите кнопку «📱 Поделиться контактом» ниже.",
                inline_keyboard=inline_kb
            )
        else:
            await send_max_bot_message(
                chat_id_val=str(chat_id),
                text_val="Привет! Этот бот используется для подтверждения номера телефона в ВКонтакте."
            )
            
    # 2. Проверяем наличие контакта во вложениях (attachments) нового формата
    attachments = body.get("attachments", [])
    contact_payload = None
    for att in attachments:
        if att.get("type") == "contact":
            contact_payload = att.get("payload", {})
            break
            
    # Для совместимости проверим старый формат с parts
    if not contact_payload:
        parts_list = data.get("parts", [])
        for part in parts_list:
            if part.get("type") == "contact":
                contact_payload = part.get("payload", {})
                break
            
    if contact_payload:
        phone = contact_payload.get("phone")
        
        from app.models.bot_command import BotUserState
        user_state = db.exec(
            select(BotUserState)
            .where(BotUserState.messenger == "max")
            .where(BotUserState.peer_id == str(chat_id))
            .where(BotUserState.state == "awaiting_max_contact")
        ).first()
        
        if user_state and phone:
            vk_id = user_state.context_data.get("vk_id")
            
            phone_digits = "".join(c for c in phone if c.isdigit())
            if len(phone_digits) == 11 and (phone_digits.startswith("8") or phone_digits.startswith("7")):
                phone_digits = "7" + phone_digits[1:]
            elif len(phone_digits) == 10 and phone_digits.startswith("9"):
                phone_digits = "7" + phone_digits
            db_phone = f"+{phone_digits}"
            
            from app.models.vk_user import VkUser
            from app.models.customer import Customer
            from app.services.vk_service import send_vk_message, fetch_vk_user_info
            from app.models.vk_settings import VkSettings
            from app.models.vk_bot_connection import VkBotConnection
            from app.services.iiko_service import iiko_service
            
            vk_settings = db.exec(select(VkSettings)).first()
            vk_bot_token = vk_settings.vk_bot_token if vk_settings else None
            
            vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
            group_id = vk_user.vk_group_id if vk_user else None
            if group_id:
                bot_conn = db.exec(select(VkBotConnection).where(VkBotConnection.vk_group_id == group_id, VkBotConnection.is_active == True)).first()
                if bot_conn:
                    vk_bot_token = bot_conn.vk_bot_token
                    
            # Привязываем и получаем баланс
            from app.services.vk_service import link_phone_to_vk_user
            points = await link_phone_to_vk_user(db, vk_id, db_phone, vk_bot_token, group_id, source="max")
            
            db.delete(user_state)
            
            vk_user_state = db.exec(
                select(BotUserState)
                .where(BotUserState.messenger == "vk")
                .where(BotUserState.peer_id == str(vk_id))
            ).first()
            if vk_user_state:
                db.delete(vk_user_state)
                
            db.commit()
            
            await send_max_bot_message(
                chat_id_val=str(chat_id),
                text_val="Номер телефона успешно подтвержден! Вы можете вернуться в диалог ВКонтакте."
            )
            
            if vk_bot_token:
                settings = db.exec(select(ValidationSettings)).first()
                msg = (settings.vk_msg_success.replace("{balance}", str(int(points))) if settings and settings.vk_msg_success 
                       else f"Проверка через мессенджер МАКС пройдена успешно! Ваш бонусный баланс: {int(points)} бонусов.")
                await send_vk_message(
                    vk_id=vk_id,
                    message=msg,
                    bot_token=vk_bot_token
                )
                
    return {"status": "ok"}


@router.post("/redsms-webhook")
async def redsms_webhook(
    request: Request,
    db: Session = Depends(get_session)
):
    """Вебхук для приема входящих звонков/статусов от RedSMS (Wait Call)"""
    content_type = request.headers.get("content-type", "")
    payload = {}
    
    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception as e:
            logger.error(f"RedSMS Webhook invalid JSON: {e}")
            return {"status": "error", "message": "Invalid JSON"}
    else:
        try:
            form_data = await request.form()
            payload = dict(form_data)
        except Exception as e:
            logger.error(f"RedSMS Webhook invalid Form-data: {e}")
            return {"status": "error", "message": "Invalid Form-data"}
            
    logger.info(f"Incoming RedSMS webhook: {payload}")
    
    uuid = payload.get("uuid")
    status_val = payload.get("status")
    client_phone = payload.get("phone") or payload.get("client") or payload.get("from") or payload.get("to")
    
    from app.models.bot_command import BotUserState
    from app.models.vk_user import VkUser
    from app.models.customer import Customer
    from app.services.vk_service import send_vk_message, fetch_vk_user_info
    from app.models.vk_settings import VkSettings
    from app.models.vk_bot_connection import VkBotConnection
    from app.services.iiko_service import iiko_service
    from app.services.vk_service import link_phone_to_vk_user

    matched_state = None
    matched_by = None
    db_phone = None

    # 1. Если пришел UUID и статус "delivered" (сброс вызова Wait Call зафиксирован на АТС)
    if uuid and status_val == "delivered":
        states = db.exec(
            select(BotUserState)
            .where(BotUserState.messenger == "vk")
            .where(BotUserState.state == "awaiting_wait_call")
        ).all()
        for state in states:
            if state.context_data and state.context_data.get("uuid") == uuid:
                matched_state = state
                db_phone = state.context_data.get("phone")
                matched_by = "uuid"
                break

    # 2. Если не нашли по UUID, пробуем найти по номеру телефона
    if not matched_state and client_phone:
        phone_digits = "".join(c for c in str(client_phone) if c.isdigit())
        if len(phone_digits) == 11 and (phone_digits.startswith("8") or phone_digits.startswith("7")):
            phone_digits = "7" + phone_digits[1:]
        elif len(phone_digits) == 10 and phone_digits.startswith("9"):
            phone_digits = "7" + phone_digits
            
        if len(phone_digits) == 11 and phone_digits.startswith("7"):
            candidate_phone = f"+{phone_digits}"
            
            # Ищем сессию в БД с таким телефоном
            states = db.exec(
                select(BotUserState)
                .where(BotUserState.messenger == "vk")
                .where(BotUserState.state == "awaiting_wait_call")
            ).all()
            for state in states:
                stored_phone = state.context_data.get("phone")
                if stored_phone:
                    stored_phone_digits = "".join(c for c in stored_phone if c.isdigit())
                    if stored_phone_digits == phone_digits:
                        matched_state = state
                        db_phone = candidate_phone
                        matched_by = "phone"
                        break
                        
            # Если всё равно не нашли сессию, но есть такой клиент, ищем сессию по его vk_user_id
            if not matched_state:
                customer = db.exec(select(Customer).where(Customer.phone == candidate_phone)).first()
                if customer and customer.vk_user_id:
                    matched_state = db.exec(
                        select(BotUserState)
                        .where(BotUserState.messenger == "vk")
                        .where(BotUserState.peer_id == str(customer.vk_user_id))
                        .where(BotUserState.state == "awaiting_wait_call")
                    ).first()
                    if matched_state:
                        db_phone = candidate_phone
                        matched_by = "customer_vk_id"
                        
    if matched_state and db_phone:
        vk_id = int(matched_state.peer_id)
        
        vk_settings = db.exec(select(VkSettings)).first()
        vk_bot_token = vk_settings.vk_bot_token if vk_settings else None
        
        vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
        group_id = vk_user.vk_group_id if vk_user else None
        if group_id:
            bot_conn = db.exec(select(VkBotConnection).where(VkBotConnection.vk_group_id == group_id, VkBotConnection.is_active == True)).first()
            if bot_conn:
                vk_bot_token = bot_conn.vk_bot_token
                
        # Привязываем телефон и получаем бонусный баланс
        points = await link_phone_to_vk_user(db, vk_id, db_phone, vk_bot_token, group_id, source="wait_call")
        
        # Получаем command_id перед удалением matched_state
        from app.models.bot_command import BotCommand
        cmd = None
        if matched_state and matched_state.command_id:
            cmd = db.get(BotCommand, matched_state.command_id)

        # Удаляем состояние FSM
        db.delete(matched_state)
        db.commit()
            
        if vk_bot_token:
            if cmd and cmd.action_type == "transfer_points":
                from app.services.vk_service import transfer_vk_points_to_iiko
                msg = await transfer_vk_points_to_iiko(db, vk_user, group_id, vk_bot_token)
            else:
                settings = db.exec(select(ValidationSettings)).first()
                msg = (settings.vk_msg_success.replace("{balance}", str(int(points))) if settings and settings.vk_msg_success 
                       else f"Входящий звонок зафиксирован! Проверка номера телефона успешно пройдена. Ваш бонусный баланс: {int(points)} бонусов.")
            await send_vk_message(
                vk_id=vk_id,
                message=msg,
                bot_token=vk_bot_token
            )
            
        return {"status": "success", "message": "Phone verified", "matched_by": matched_by}
        
    return {"status": "ignored", "reason": "no pending session for this payload", "payload": payload}
