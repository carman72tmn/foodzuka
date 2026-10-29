"""
API эндпоинты для интеграции с телефонией Mango Office (ВАТС)
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select, desc, func, or_

from app.core.database import get_session
from app.models.mango_settings import MangoSettings, MangoCallLog
from app.models.user import User
from app.services.mango_service import mango_service
from app.api import deps

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Mango Office"])


# --- Pydantic Schemas ---

class MangoSettingsSchema(BaseModel):
    id: Optional[int] = None
    vpbx_api_key: Optional[str] = None
    vpbx_api_salt: Optional[str] = None
    vpbx_url: str = "https://app.mango-office.ru/vpbx/"
    is_active: bool = False
    default_extension: Optional[str] = None
    auto_lookup_customer: bool = True
    create_customer_if_missing: bool = False
    notify_incoming_call: bool = True
    recording_storage_mode: str = "stream"
    webhook_url: Optional[str] = "https://vezuroll.ru/api/v1/mango/webhook"


class TestConnectionSchema(BaseModel):
    vpbx_api_key: str
    vpbx_api_salt: str
    vpbx_url: str = "https://app.mango-office.ru/vpbx/"


class CallbackRequestSchema(BaseModel):
    from_extension: str
    to_number: str
    line_number: Optional[str] = None
    command_id: Optional[str] = None


class HangupRequestSchema(BaseModel):
    call_id: str
    command_id: Optional[str] = None


class SendSmsRequestSchema(BaseModel):
    to_number: str
    text: str
    from_extension: Optional[str] = None
    sender: Optional[str] = None


class WebhookEmulatorSchema(BaseModel):
    caller_phone: str = "+79220079019"
    extension: str = "101"
    line_number: str = "73452000000"
    call_state: str = "Appeared"


# --- Settings Endpoints ---

@router.get("/settings/mango", response_model=MangoSettingsSchema)
def get_mango_settings(
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_mango_view"))
):
    """Получение настроек подключения к Mango Office ВАТС"""
    settings = db.exec(select(MangoSettings)).first()
    if not settings:
        return MangoSettingsSchema()
    
    schema_dict = settings.model_dump()
    schema_dict["webhook_url"] = "https://vezuroll.ru/api/v1/mango/webhook"
    return MangoSettingsSchema(**schema_dict)


@router.post("/settings/mango", response_model=MangoSettingsSchema)
def save_mango_settings(
    data: MangoSettingsSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_mango_edit"))
):
    """Сохранение настроек Mango Office"""
    settings = db.exec(select(MangoSettings)).first()
    if settings:
        settings.vpbx_api_key = data.vpbx_api_key.strip() if data.vpbx_api_key else None
        settings.vpbx_api_salt = data.vpbx_api_salt.strip() if data.vpbx_api_salt else None
        settings.vpbx_url = data.vpbx_url.strip() if data.vpbx_url else "https://app.mango-office.ru/vpbx/"
        settings.is_active = data.is_active
        settings.default_extension = data.default_extension.strip() if data.default_extension else None
        settings.auto_lookup_customer = data.auto_lookup_customer
        settings.create_customer_if_missing = data.create_customer_if_missing
        settings.notify_incoming_call = data.notify_incoming_call
        settings.recording_storage_mode = data.recording_storage_mode
        settings.updated_at = datetime.utcnow()
    else:
        settings = MangoSettings(
            vpbx_api_key=data.vpbx_api_key.strip() if data.vpbx_api_key else None,
            vpbx_api_salt=data.vpbx_api_salt.strip() if data.vpbx_api_salt else None,
            vpbx_url=data.vpbx_url.strip() if data.vpbx_url else "https://app.mango-office.ru/vpbx/",
            is_active=data.is_active,
            default_extension=data.default_extension.strip() if data.default_extension else None,
            auto_lookup_customer=data.auto_lookup_customer,
            create_customer_if_missing=data.create_customer_if_missing,
            notify_incoming_call=data.notify_incoming_call,
            recording_storage_mode=data.recording_storage_mode
        )
        db.add(settings)

    db.commit()
    db.refresh(settings)

    schema_dict = settings.model_dump()
    schema_dict["webhook_url"] = "https://vezuroll.ru/api/v1/mango/webhook"
    return MangoSettingsSchema(**schema_dict)


@router.post("/settings/mango/test-connection")
async def test_mango_connection(
    data: TestConnectionSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_mango_edit"))
):
    """Проверка подключения и подписи SHA256 к Mango Office"""
    res = await mango_service.test_connection(
        api_key=data.vpbx_api_key,
        api_salt=data.vpbx_api_salt,
        url=data.vpbx_url
    )
    return res


# --- Call Management & Telephony Operations ---

@router.get("/mango/calls")
def get_call_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    direction: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_mango_view"))
):
    """Получение журнала звонков с фильтрами и пагинацией"""
    query = select(MangoCallLog)

    if direction:
        query = query.where(MangoCallLog.direction == direction)

    if status:
        query = query.where(MangoCallLog.status == status)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.where(
            or_(
                MangoCallLog.from_number.ilike(search_term),
                MangoCallLog.to_number.ilike(search_term),
                MangoCallLog.customer_name.ilike(search_term),
                MangoCallLog.comment.ilike(search_term)
            )
        )

    if date_from:
        try:
            d_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.where(MangoCallLog.created_at >= d_from)
        except Exception:
            pass

    if date_to:
        try:
            d_to = datetime.strptime(date_to + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            query = query.where(MangoCallLog.created_at <= d_to)
        except Exception:
            pass

    # Общее количество
    count_query = select(func.count()).select_from(query.subquery())
    total = db.exec(count_query).one()

    # Пагинация и сортировка от свежих к старым
    query = query.order_by(desc(MangoCallLog.created_at))
    offset = (page - 1) * limit
    items = db.exec(query.offset(offset).limit(limit)).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 1
    }


@router.post("/mango/commands/callback")
async def make_callback(
    data: CallbackRequestSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_mango_edit"))
):
    """Инициация звонка из CRM (Click-to-Call)"""
    success, res, err = await mango_service.make_callback(
        from_extension=data.from_extension,
        to_number=data.to_number,
        line_number=data.line_number,
        command_id=data.command_id,
        db=db
    )
    if not success:
        raise HTTPException(status_code=400, detail=err or "Не удалось инициировать звонок")
    return {"success": True, "result": res}


@router.post("/mango/commands/hangup")
async def hangup_call(
    data: HangupRequestSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_mango_edit"))
):
    """Завершение звонка по call_id"""
    success, res, err = await mango_service.hangup_call(
        call_id=data.call_id,
        command_id=data.command_id,
        db=db
    )
    if not success:
        raise HTTPException(status_code=400, detail=err or "Не удалось завершить вызов")
    return {"success": True, "result": res}


@router.post("/mango/commands/sms")
async def send_sms_via_mango(
    data: SendSmsRequestSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_mango_edit"))
):
    """Отправка SMS через Mango Office ВАТС"""
    success, res, err = await mango_service.send_sms(
        to_number=data.to_number,
        text=data.text,
        from_extension=data.from_extension,
        sender=data.sender,
        db=db
    )
    if not success:
        raise HTTPException(status_code=400, detail=err or "Не удалось отправить SMS")
    return {"success": True, "result": res}


@router.get("/mango/users")
async def get_mango_users(
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_mango_view"))
):
    """Получение справочника сотрудников и внутренних линий ВАТС"""
    success, users, err = await mango_service.get_users_list(db)
    if not success:
        raise HTTPException(status_code=400, detail=err or "Не удалось загрузить список сотрудников")
    return {"success": True, "users": users}


@router.get("/mango/recordings/{recording_id}/stream")
async def stream_recording(
    recording_id: str,
    action: str = Query("play", regex="^(play|download)$"),
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_mango_view"))
):
    """Стриминг аудиозаписи разговора для HTML5 плеера без проблем с CORS"""
    success, data, err = await mango_service.get_recording_url_or_stream(
        recording_id=recording_id,
        action=action,
        db=db
    )
    if not success or not data:
        raise HTTPException(status_code=404, detail=err or "Запись разговора недоступна")

    # Если Mango вернул ссылку редиректа или URL записи
    url = None
    if isinstance(data, dict):
        url = data.get("url") or data.get("link")
    elif isinstance(data, str) and data.startswith("http"):
        url = data

    if url:
        # Проксируем поток из Mango
        async def audio_streamer():
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("GET", url) as resp:
                    async for chunk in resp.aiter_bytes():
                        yield chunk

        headers = {
            "Content-Disposition": f"{'inline' if action == 'play' else 'attachment'}; filename=recording_{recording_id}.mp3"
        }
        return StreamingResponse(audio_streamer(), media_type="audio/mpeg", headers=headers)

    return {"success": True, "recording_data": data}


@router.post("/mango/test-webhook-emulator")
async def emulate_webhook(
    data: WebhookEmulatorSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_mango_edit"))
):
    """Эмулятор входящего события от Mango Office для отладки"""
    fake_payload = {
        "entry_id": f"emu_{int(datetime.utcnow().timestamp())}",
        "call_id": f"call_emu_{int(datetime.utcnow().timestamp())}",
        "timestamp": int(datetime.utcnow().timestamp()),
        "call_state": data.call_state,
        "from": {
            "number": data.caller_phone
        },
        "to": {
            "extension": data.extension
        },
        "line_number": data.line_number
    }
    result = await mango_service.process_webhook(fake_payload, db)
    return {"success": True, "payload": fake_payload, "result": result}


# --- Public Webhook Receiver ---

@router.post("/mango/webhook")
async def receive_mango_webhook(
    request: Request,
    db: Session = Depends(get_session)
):
    """
    Публичный эндпоинт для приема входящих вебхуков от Mango Office.
    Mango Office отправляет POST запрос с параметрами:
    - vpbx_api_key
    - sign: SHA256(vpbx_api_key + json + vpbx_api_salt)
    - json: строковый JSON с данными события
    """
    settings = mango_service.get_settings(db)
    content_type = request.headers.get("content-type", "")

    raw_json = None
    vpbx_api_key = None
    sign = None

    try:
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            vpbx_api_key = form.get("vpbx_api_key")
            sign = form.get("sign")
            raw_json = form.get("json")
        else:
            body = await request.body()
            body_text = body.decode("utf-8")
            if body_text.strip().startswith("{"):
                body_json = json.loads(body_text)
                vpbx_api_key = body_json.get("vpbx_api_key")
                sign = body_json.get("sign")
                raw_json = body_json.get("json") or body_text
    except Exception as e:
        logger.error(f"Ошибка разбора входящего вебхука Mango: {e}")
        return Response(content=json.dumps({"result": 1002, "error": "Invalid format"}), media_type="application/json", status_code=200)

    if not raw_json:
        return Response(content=json.dumps({"result": 1002, "error": "Missing json payload"}), media_type="application/json", status_code=200)

    # Валидация подписи (если интеграция активна и задан salt)
    if settings and settings.vpbx_api_salt and sign and vpbx_api_key:
        valid = mango_service.verify_sign(
            api_key=str(vpbx_api_key),
            json_str=str(raw_json),
            sign=str(sign),
            api_salt=settings.vpbx_api_salt
        )
        if not valid:
            logger.warning("Вебхук Mango: несовпадение цифровой подписи SHA-256")
            # Mango ожидает 200 даже при ошибках авторизации по регламенту
            return Response(content=json.dumps({"result": 1001, "error": "Invalid signature"}), media_type="application/json", status_code=200)

    try:
        data = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
        await mango_service.process_webhook(data, db)
    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука Mango Office: {e}")

    # Стандартный успешный ответ Mango Office
    return Response(content=json.dumps({"result": 1000}), media_type="application/json", status_code=200)
