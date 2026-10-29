"""
Сервис интеграции с телефонией Mango Office (ВАТС) по API
Включает формирование цифровой подписи SHA-256, обработку вебхуков,
Click-to-Call, управление звонками, работу с записями и статистикой.
"""
import hashlib
import hmac
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
import httpx
from sqlmodel import Session, select

from app.models.mango_settings import MangoSettings, MangoCallLog
from app.models.customer import Customer
from app.models.admin_notification import AdminNotification

logger = logging.getLogger(__name__)


class MangoService:
    """Сервис взаимодействия с API Mango Office ВАТС"""

    @staticmethod
    def normalize_phone(phone: Optional[str]) -> str:
        """Приведение номера телефона к стандартному формату +79991234567"""
        if not phone:
            return ""
        digits = re.sub(r"\D", "", str(phone))
        if len(digits) == 10 and digits.startswith("9"):
            return f"+7{digits}"
        if len(digits) == 11:
            if digits.startswith("8"):
                return f"+7{digits[1:]}"
            if digits.startswith("7"):
                return f"+7{digits[1:]}"
        if digits:
            return f"+{digits}"
        return ""

    @staticmethod
    def generate_sign(api_key: str, json_str: str, api_salt: str) -> str:
        """
        Вычисление цифровой подписи SHA-256 по регламенту Mango Office:
        sign = sha256(vpbx_api_key + json_parameters + vpbx_api_salt)
        """
        raw_string = f"{api_key}{json_str}{api_salt}"
        return hashlib.sha256(raw_string.encode("utf-8")).hexdigest()

    @staticmethod
    def verify_sign(api_key: str, json_str: str, sign: str, api_salt: str) -> bool:
        """Валидация подписи входящего запроса/вебхука от Mango Office"""
        expected_sign = MangoService.generate_sign(api_key, json_str, api_salt)
        return hmac.compare_digest(expected_sign.lower(), (sign or "").lower())

    @classmethod
    def get_settings(cls, db: Session) -> Optional[MangoSettings]:
        """Получение текущих настроек подключения к Mango Office"""
        return db.exec(select(MangoSettings)).first()

    @classmethod
    async def _send_request(
        cls, 
        endpoint: str, 
        params: dict, 
        db: Session, 
        override_settings: Optional[MangoSettings] = None
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Отправка подписанного POST запроса к API Mango Office ВАТС.
        Данные передаются в формате application/x-www-form-urlencoded:
        vpbx_api_key, sign, json
        """
        settings = override_settings or cls.get_settings(db)
        if not settings or not settings.vpbx_api_key or not settings.vpbx_api_salt:
            return False, None, "Реквизиты Mango Office (API Key / Salt) не настроены"

        base_url = settings.vpbx_url.rstrip("/") + "/"
        full_url = base_url + endpoint.lstrip("/")

        json_str = json.dumps(params, ensure_ascii=False)
        sign = cls.generate_sign(settings.vpbx_api_key, json_str, settings.vpbx_api_salt)

        form_data = {
            "vpbx_api_key": settings.vpbx_api_key,
            "sign": sign,
            "json": json_str
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(full_url, data=form_data)
                
                # Обработка ответа
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    res_data = response.json()
                else:
                    try:
                        res_data = response.json()
                    except Exception:
                        res_data = {"raw_text": response.text}

                if response.status_code == 200:
                    # Проверяем внутренний результат Mango (result: 1000.. error codes)
                    if isinstance(res_data, dict) and res_data.get("result") not in (None, 1000, "1000", 0, "0"):
                        error_code = res_data.get("result")
                        error_desc = cls._get_error_description(error_code)
                        return False, res_data, f"Ошибка Mango Office [{error_code}]: {error_desc}"
                    return True, res_data, None
                else:
                    return False, res_data, f"HTTP {response.status_code}: {response.text[:200]}"
        except Exception as e:
            logger.error(f"Ошибка HTTP-запроса к Mango Office ({endpoint}): {e}")
            return False, None, f"Сетевая ошибка обращения к Mango Office: {str(e)}"

    @staticmethod
    def _get_error_description(code: Any) -> str:
        """Интерпретация кодов ошибок Mango Office ВАТС"""
        codes = {
            1000: "Успешно",
            1001: "Неверная подпись (sign) запроса. Проверьте правильность API Salt",
            1002: "Неверный формат JSON параметров",
            1003: "Неверный ключ API (vpbx_api_key). Проверьте ключ в ЛК",
            1004: "Доступ с данного IP-адреса запрещен в настройках безопасности ВАТС",
            1005: "Превышен лимит запросов к API Mango Office",
            1006: "Недостаточно прав для выполнения операции",
            1007: "Указанный сотрудник или добавочный номер не найден",
            1008: "Линия занята или недоступна",
            1009: "Неверный номер абонента",
            1010: "Запись разговора еще не готова или не существует",
            1011: "Запрашиваемый вызов не найден"
        }
        return codes.get(int(code) if str(code).isdigit() else code, "Неизвестный статус или код ошибки Mango")

    @classmethod
    async def test_connection(
        cls, 
        api_key: str, 
        api_salt: str, 
        url: str = "https://app.mango-office.ru/vpbx/"
    ) -> Dict[str, Any]:
        """Тестирование подключения и проверка валидности ключей и подписи"""
        temp_settings = MangoSettings(
            vpbx_api_key=api_key.strip(),
            vpbx_api_salt=api_salt.strip(),
            vpbx_url=url.strip(),
            is_active=True
        )

        # Запрашиваем справочник сотрудников ВАТС для проверки соединения
        success, data, err = await cls._send_request(
            endpoint="config/users/request",
            params={},
            db=None,
            override_settings=temp_settings
        )

        users_count = 0
        users_sample = []
        if success and isinstance(data, dict):
            users = data.get("users", [])
            users_count = len(users)
            users_sample = [
                {
                    "extension": u.get("extension"),
                    "name": u.get("name"),
                    "email": u.get("email"),
                    "general_phone": u.get("general_phone")
                }
                for u in users[:5]
            ]

        return {
            "success": success,
            "message": "Подключение к Mango Office успешно установлено!" if success else (err or "Сбой подключения"),
            "users_count": users_count,
            "users_sample": users_sample,
            "details": data
        }

    @classmethod
    async def make_callback(
        cls, 
        from_extension: str, 
        to_number: str, 
        line_number: Optional[str] = None, 
        command_id: Optional[str] = None,
        db: Session = None
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Инициация вызова Click-to-Call (звонок сотруднику и абоненту).
        POST commands/callback
        """
        cid = command_id or f"c2c_{uuid.uuid4().hex[:12]}"
        clean_to = cls.normalize_phone(to_number)

        params: Dict[str, Any] = {
            "command_id": cid,
            "from": {
                "extension": str(from_extension).strip()
            },
            "to_number": clean_to
        }
        if line_number:
            params["line_number"] = str(line_number).strip()

        return await cls._send_request("commands/callback", params, db)

    @classmethod
    async def hangup_call(
        cls, 
        call_id: str, 
        command_id: Optional[str] = None, 
        db: Session = None
    ) -> Tuple[bool, Any, Optional[str]]:
        """Завершение активного вызова: POST commands/call/hangup"""
        cid = command_id or f"hangup_{uuid.uuid4().hex[:12]}"
        params = {
            "command_id": cid,
            "call_id": call_id
        }
        return await cls._send_request("commands/call/hangup", params, db)

    @classmethod
    async def transfer_call(
        cls, 
        call_id: str, 
        to_number: str, 
        command_id: Optional[str] = None, 
        db: Session = None
    ) -> Tuple[bool, Any, Optional[str]]:
        """Перевод текущего вызова: POST commands/transfer"""
        cid = command_id or f"tr_{uuid.uuid4().hex[:12]}"
        params = {
            "command_id": cid,
            "call_id": call_id,
            "to_number": to_number
        }
        return await cls._send_request("commands/transfer", params, db)

    @classmethod
    async def send_sms(
        cls, 
        to_number: str, 
        text: str, 
        from_extension: Optional[str] = None, 
        sender: Optional[str] = None, 
        command_id: Optional[str] = None, 
        db: Session = None
    ) -> Tuple[bool, Any, Optional[str]]:
        """Отправка SMS через шлюз Mango: POST commands/sms"""
        cid = command_id or f"sms_{uuid.uuid4().hex[:12]}"
        clean_to = cls.normalize_phone(to_number)

        params: Dict[str, Any] = {
            "command_id": cid,
            "to_number": clean_to,
            "text": text
        }
        if from_extension:
            params["from_extension"] = str(from_extension).strip()
        if sender:
            params["sender"] = sender.strip()

        return await cls._send_request("commands/sms", params, db)

    @classmethod
    async def get_users_list(cls, db: Session) -> Tuple[bool, List[dict], Optional[str]]:
        """Получение списка сотрудников и линий ВАТС: POST config/users/request"""
        success, data, err = await cls._send_request("config/users/request", {}, db)
        if not success or not isinstance(data, dict):
            return False, [], err
        return True, data.get("users", []), None

    @classmethod
    async def get_recording_url_or_stream(
        cls, 
        recording_id: str, 
        action: str = "play", 
        db: Session = None
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Запрос записи разговора.
        POST queries/recording/post/
        """
        settings = cls.get_settings(db)
        if not settings:
            return False, None, "Настройки Mango не найдены"

        params = {
            "recording_id": recording_id,
            "action": action
        }
        return await cls._send_request("queries/recording/post/", params, db)

    @classmethod
    async def process_webhook(cls, raw_data: dict, db: Session) -> Dict[str, Any]:
        """
        Обработка входящих вебхуков от Mango Office:
        - events/call (Appeared, Connected, Disconnected, OnHold)
        - events/recording (запись готова)
        - events/summary (сводка вызова)
        """
        settings = cls.get_settings(db)
        logger.info(f"Получен вебхук от Mango Office: {raw_data}")

        entry_id = str(raw_data.get("entry_id") or "")
        call_id = str(raw_data.get("call_id") or "")
        call_state = raw_data.get("call_state")
        timestamp = raw_data.get("timestamp")

        # Извлечение номеров
        from_dict = raw_data.get("from", {}) or {}
        to_dict = raw_data.get("to", {}) or {}
        from_number = from_dict.get("number")
        from_ext = from_dict.get("extension")
        to_number = to_dict.get("number")
        to_ext = to_dict.get("extension")
        line_number = raw_data.get("line_number")
        disconnect_reason = raw_data.get("disconnect_reason")

        # Определение направления (входящий если to_ext задан или from_number внешний)
        direction = "incoming"
        caller_phone = from_number
        if from_ext and not to_ext:
            direction = "outgoing"
            caller_phone = to_number

        norm_phone = cls.normalize_phone(caller_phone)

        # Поиск клиента в базе
        customer_id = None
        customer_name = None
        if norm_phone and (not settings or settings.auto_lookup_customer):
            customer = db.exec(select(Customer).where(Customer.phone == norm_phone)).first()
            if customer:
                customer_id = customer.id
                customer_name = customer.name or f"Клиент {norm_phone}"
            elif settings and settings.create_customer_if_missing:
                try:
                    new_cust = Customer(
                        phone=norm_phone,
                        name=f"Гость {norm_phone[-4:]}",
                        is_new_guest=True
                    )
                    db.add(new_cust)
                    db.commit()
                    db.refresh(new_cust)
                    customer_id = new_cust.id
                    customer_name = new_cust.name
                except Exception as e:
                    logger.warning(f"Не удалось создать нового гостя при звонке: {e}")

        # Поиск существующей записи звонка
        call_log = None
        if call_id:
            call_log = db.exec(select(MangoCallLog).where(MangoCallLog.call_id == call_id)).first()
        if not call_log and entry_id:
            call_log = db.exec(select(MangoCallLog).where(MangoCallLog.entry_id == entry_id)).first()

        now_dt = datetime.now(timezone.utc)

        if not call_log:
            call_log = MangoCallLog(
                entry_id=entry_id,
                call_id=call_id,
                call_state=call_state,
                direction=direction,
                from_number=from_number,
                from_extension=str(from_ext) if from_ext else None,
                to_number=to_number,
                to_extension=str(to_ext) if to_ext else None,
                line_number=str(line_number) if line_number else None,
                customer_id=customer_id,
                customer_name=customer_name,
                raw_data=json.dumps(raw_data, ensure_ascii=False),
                started_at=now_dt
            )
            db.add(call_log)
        else:
            if call_state:
                call_log.call_state = call_state
            if customer_id and not call_log.customer_id:
                call_log.customer_id = customer_id
                call_log.customer_name = customer_name
            if disconnect_reason:
                call_log.disconnect_reason = str(disconnect_reason)

        # Логика смены состояний
        if call_state == "Appeared":
            call_log.status = "active"
            # Создаем системное уведомление о входящем звонке
            if settings and settings.notify_incoming_call and direction == "incoming":
                try:
                    guest_label = customer_name or norm_phone or "Неизвестный номер"
                    notif = AdminNotification(
                        title="📞 Входящий звонок Mango",
                        message=f"Звонит: {guest_label} (номер {caller_phone})",
                        type="call_incoming",
                        icon="bx-phone-call",
                        action_url=f"/clients?search={norm_phone}" if customer_id else "/settings/mango"
                    )
                    db.add(notif)
                except Exception as e:
                    logger.warning(f"Не удалось создать системное уведомление о звонке: {e}")

        elif call_state == "Connected":
            call_log.status = "active"
            call_log.connected_at = now_dt
            if call_log.started_at:
                call_log.duration_wait = max(0, int((now_dt - call_log.started_at.replace(tzinfo=timezone.utc)).total_seconds()))

        elif call_state == "Disconnected":
            call_log.ended_at = now_dt
            if call_log.connected_at:
                call_log.duration_talk = max(0, int((now_dt - call_log.connected_at.replace(tzinfo=timezone.utc)).total_seconds()))
                call_log.status = "success"
            else:
                # Если соединения не было - звонок пропущен
                call_log.status = "missed"

            # Проверяем запись разговора
            recording_id = raw_data.get("recording_id")
            if recording_id:
                call_log.recording_id = str(recording_id)

        # Проверка события recording
        if raw_data.get("recording_id"):
            call_log.recording_id = str(raw_data.get("recording_id"))

        db.commit()
        db.refresh(call_log)

        return {
            "status": "processed",
            "call_log_id": call_log.id,
            "call_state": call_state,
            "customer_id": customer_id
        }


mango_service = MangoService()
