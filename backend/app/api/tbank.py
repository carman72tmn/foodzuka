"""
API эндпоинты для настроек интеграции с Т-Банком (T-API)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.tbank_settings import TBankSettings, TBankAccountStatement
from app.models.order import Order
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import httpx
import tempfile
import os
import ssl
from app.api import deps
from app.models.user import User
from app.core.tbank_utils import get_terminal_display_name, parse_terminal_names

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings/tbank", tags=["T-Bank Settings"])

# --- Schemas ---

class TBankSettingsSchema(BaseModel):
    id: Optional[int] = None
    terminal_key: Optional[str] = None
    token: Optional[str] = None
    certificate_content: Optional[str] = None
    selected_terminals: Optional[str] = None
    is_active: bool = False
    terminal_pickup: Optional[str] = None
    terminal_delivery: Optional[str] = None
    merchant_id: Optional[str] = None
    sbp_terminal_id: Optional[str] = "42734785"
    sbp_secret_key: Optional[str] = None
    terminal_names: Optional[str] = None
    acquiring_terminal_key: Optional[str] = None
    acquiring_password: Optional[str] = None
    acquiring_is_active: bool = True
    webhook_secret: Optional[str] = None

# --- Endpoints ---

@router.get("/", response_model=TBankSettingsSchema)
def get_tbank_settings(
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_tbank_view"))
):
    """Получение настроек Т-Банка (Terminal Key, Token, Certificate, Acquiring)"""
    settings = db.exec(select(TBankSettings)).first()
    if not settings:
        return TBankSettingsSchema()
    return settings

@router.post("/", response_model=TBankSettingsSchema)
def save_tbank_settings(
    data: TBankSettingsSchema, 
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_tbank_edit"))
):
    """Сохранение основных настроек Т-Банка"""
    settings = db.exec(select(TBankSettings)).first()
    
    clean_merchant_id = data.merchant_id.strip() if data.merchant_id else None
    clean_sbp_terminal_id = data.sbp_terminal_id.strip() if data.sbp_terminal_id else "42734785"
    clean_sbp_secret_key = data.sbp_secret_key.strip() if data.sbp_secret_key else None
    clean_acq_term = data.acquiring_terminal_key.strip() if data.acquiring_terminal_key else None
    clean_acq_pass = data.acquiring_password.strip() if data.acquiring_password else None
    clean_webhook_secret = data.webhook_secret.strip() if data.webhook_secret else None
    
    if settings:
        settings.terminal_key = data.terminal_key
        settings.token = data.token
        settings.certificate_content = data.certificate_content
        settings.selected_terminals = data.selected_terminals
        settings.is_active = data.is_active
        settings.terminal_pickup = data.terminal_pickup
        settings.terminal_delivery = data.terminal_delivery
        settings.merchant_id = clean_merchant_id
        settings.sbp_terminal_id = clean_sbp_terminal_id
        settings.sbp_secret_key = clean_sbp_secret_key
        settings.terminal_names = data.terminal_names
        settings.acquiring_terminal_key = clean_acq_term
        settings.acquiring_password = clean_acq_pass
        settings.acquiring_is_active = data.acquiring_is_active
        settings.webhook_secret = clean_webhook_secret
    else:
        settings = TBankSettings(
            terminal_key=data.terminal_key,
            token=data.token,
            certificate_content=data.certificate_content,
            selected_terminals=data.selected_terminals,
            is_active=data.is_active,
            terminal_pickup=data.terminal_pickup,
            terminal_delivery=data.terminal_delivery,
            merchant_id=clean_merchant_id,
            sbp_terminal_id=clean_sbp_terminal_id,
            sbp_secret_key=clean_sbp_secret_key,
            terminal_names=data.terminal_names,
            acquiring_terminal_key=clean_acq_term,
            acquiring_password=clean_acq_pass,
            acquiring_is_active=data.acquiring_is_active,
            webhook_secret=clean_webhook_secret
        )
        db.add(settings)
        
    db.commit()
    db.refresh(settings)
    return settings

@router.post("/test-connection", response_model=Dict[str, Any])
def test_tbank_connection(
    data: TBankSettingsSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_permission("settings_tbank_edit"))
):
    """Тестирование подключения к API Т-Банка (T-API Бизнес или Интернет-эквайринг)"""
    result = {
        "success": False,
        "tls_ok": False,
        "api_response_code": None,
        "error_message": None,
        "details": {},
        "available_apis": []
    }
    
    cert_file_path = None
    try:
        client = httpx.Client(timeout=10.0, verify=False)
        # Если передан сертификат, сохраняем его во временный файл для TLS-клиента
        if data.certificate_content and data.certificate_content.strip():
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w", encoding="utf-8") as temp_cert:
                temp_cert.write(data.certificate_content.strip())
                cert_file_path = temp_cert.name
            client.cert = cert_file_path
            result["details"]["cert_used"] = True
        else:
            result["details"]["cert_used"] = False

        # Определение типа тестирования:
        # Если передан acquiring_terminal_key (или проверяется эквайринг без PEM-сертификата)
        test_acquiring = bool(data.acquiring_terminal_key and data.acquiring_terminal_key.strip())
        is_business_api = bool(data.certificate_content and data.certificate_content.strip()) and not test_acquiring

        if is_business_api:
            # ТЕСТИРОВАНИЕ T-API БИЗНЕС (OpenAPI) через получение списка счетов
            url = "https://business.tbank.ru/openapi/api/v3/bank-accounts"
            headers = {
                "Authorization": f"Bearer {data.token or ''}",
                "Content-Type": "application/json"
            }
            
            try:
                response = client.get(url, headers=headers)
                result["api_response_code"] = response.status_code
                result["tls_ok"] = True
                
                if response.status_code == 200:
                    result["success"] = True
                    result["error_message"] = "Подключение к T-API Бизнес успешно установлено. Доступ к счетам получен."
                    try:
                        result["details"]["api_response"] = response.json()
                    except Exception:
                        pass
                elif response.status_code in [401, 403]:
                    result["success"] = False
                    result["error_message"] = f"TLS-соединение установлено (TLS OK), но Т-Банк отклонил токен авторизации (Код ошибки: {response.status_code})"
                else:
                    result["success"] = False
                    result["error_message"] = f"Транспорт OK, но бизнес API вернул ошибку (HTTP: {response.status_code}): {response.text[:200]}"
            except httpx.ConnectError as ce:
                result["error_message"] = f"Ошибка сети при подключении к T-API: {str(ce)}"
            except httpx.ConnectTimeout:
                result["error_message"] = "Превышено время ожидания ответа от T-API (10 секунд)"
            except ssl.SSLError as se:
                result["error_message"] = f"Ошибка Mutual TLS (проблема с SSL-сертификатом PEM): {str(se)}"
            except Exception as e:
                result["error_message"] = f"Ошибка соединения с T-API: {str(e)}"
                
        else:
            # ТЕСТИРОВАНИЕ ИНТЕРНЕТ-ЭКВАЙРИНГА (Merchant API / e-commerce)
            url = "https://securepay.tinkoff.ru/v2/Init"
            import time
            
            target_terminal = data.acquiring_terminal_key or data.terminal_key or "TEST_KEY"
            target_password = data.acquiring_password or data.token
            
            payload = {
                "TerminalKey": target_terminal,
                "Amount": 1000,
                "OrderId": f"TEST_CONN_{int(time.time())}",
                "Description": "Тест подключения интернет-эквайринга FoodZuka"
            }
            if target_password:
                from app.core.tbank_utils import generate_tbank_token
                payload["Token"] = generate_tbank_token(payload, target_password)
            
            try:
                response = client.post(url, json=payload)
                result["api_response_code"] = response.status_code
                result["tls_ok"] = True
                
                try:
                    api_data = response.json()
                    result["details"]["api_response"] = api_data
                    
                    if api_data.get("Success") is True:
                        result["success"] = True
                        result["error_message"] = f"Интернет-эквайринг Т-Банка успешно подключен! TerminalKey: {target_terminal}. API отвечает корректно (PaymentId: {api_data.get('PaymentId')})."
                        result["available_apis"] = [
                            {"name": "Init", "description": "Инициализация платежной сессии (карты, СБП, T-Pay)", "status": "АКТИВЕН"},
                            {"name": "GetState", "description": "Проверка статуса оплаты транзакции", "status": "АКТИВЕН"},
                            {"name": "Webhooks (HTTP Notifications)", "description": "Прием уведомлений о платежах в реальном времени", "status": "АКТИВЕН"}
                        ]
                    else:
                        error_code = str(api_data.get("ErrorCode", "Неизвестный"))
                        message = api_data.get("Message", "Ошибка параметров")
                        details_msg = api_data.get("Details", "")
                        result["details"]["error_code"] = error_code
                        
                        # Если сервер Т-Банка ответил, что не найден терминал или неверный пароль
                        if error_code in ["9999", "1010", "9004"] or "TerminalKey" in message:
                            result["success"] = False
                            result["error_message"] = f"Транспорт OK, но Т-Банк отклонил TerminalKey эквайринга '{target_terminal}' (Код: {error_code}, Сообщение: {message} {details_msg})"
                        elif error_code == "501" or "токен" in message.lower() or "token" in message.lower() or "подпис" in message.lower():
                            result["success"] = False
                            result["error_message"] = f"Транспорт OK, но ошибка подписи/пароля терминала: {message} ({details_msg})"
                        else:
                            result["success"] = False
                            result["error_message"] = f"Ответ эквайринга с ошибкой (Код: {error_code}): {message} ({details_msg})"
                except Exception as e:
                    result["success"] = False
                    result["error_message"] = f"Транспорт OK, но ответ не JSON (HTTP: {response.status_code}): {response.text[:200]}"
            except httpx.ConnectError as ce:
                result["error_message"] = f"Ошибка сети при подключении к эквайрингу: {str(ce)}"
            except httpx.ConnectTimeout:
                result["error_message"] = "Превышено время ожидания ответа от эквайринга (10 секунд)"
            except ssl.SSLError as se:
                result["error_message"] = f"Ошибка SSL/TLS-сертификата эквайринга: {str(se)}"
            except Exception as e:
                result["error_message"] = f"Ошибка соединения с эквайрингом: {str(e)}"
            
    finally:
        # Очищаем временный PEM-файл
        if cert_file_path and os.path.exists(cert_file_path):
            try:
                os.unlink(cert_file_path)
            except Exception:
                pass
                
    return result
                
@router.get("/terminals", response_model=List[Dict[str, Any]])
def get_tbank_terminals(
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_tbank_payments_view", "bank_payments_view"))
):
    """Получение списка активных терминалов торгового эквайринга Т-Банка с мягким фолбэком"""
    settings = db.exec(select(TBankSettings)).first()
    
    # Демонстрационные терминалы (fallback в случае пустых настроек или ошибок API)
    demo_terminals = [
        {"terminalKey": "POS_TERM_7711", "name": "Терминал Касса 1 (ул. Ленина, 12)", "status": "ACTIVE", "inn": "7712345678"},
        {"terminalKey": "POS_TERM_7722", "name": "Терминал Касса 2 (ул. Ленина, 12)", "status": "ACTIVE", "inn": "7712345678"},
        {"terminalKey": "POS_TERM_8811", "name": "Курьерский терминал №1 (Михаил)", "status": "ACTIVE", "inn": "7712345678"},
        {"terminalKey": "POS_TERM_8822", "name": "Курьерский терминал №2 (Сергей)", "status": "ACTIVE", "inn": "7712345678"},
        {"terminalKey": "POS_TERM_9901", "name": "Резервный терминал СБП (QR)", "status": "ACTIVE", "inn": "7712345678"}
    ]

    if not settings or not settings.token:
        return demo_terminals

    url = "https://business.tbank.ru/openapi/api/v1/tacq/terminals"
    params = {"page": 0, "size": 100}
    headers = {
        "Authorization": f"Bearer {settings.token}",
        "Content-Type": "application/json"
    }

    cert_file_path = None
    try:
        client = httpx.Client(timeout=10.0, verify=False)
        
        # Если передан сертификат, сохраняем его во временный файл для TLS-клиента
        if settings.certificate_content and settings.certificate_content.strip():
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w", encoding="utf-8") as temp_cert:
                temp_cert.write(settings.certificate_content.strip())
                cert_file_path = temp_cert.name
            client.cert = cert_file_path

        try:
            response = client.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.warning(f"Т-Банк API вернул код {response.status_code} при запросе терминалов: {response.text[:200]}")
                raise ValueError(f"HTTP статус {response.status_code}")
                
            api_data = response.json()
            raw_terminals = []
            if isinstance(api_data, list):
                raw_terminals = api_data
            elif isinstance(api_data, dict):
                if "terminals" in api_data:
                    raw_terminals = api_data["terminals"]
                elif "content" in api_data:
                    raw_terminals = api_data["content"]
                else:
                    raw_terminals = [api_data]
                    
            terminals_list = []
            custom_names = parse_terminal_names(settings)
            for t in raw_terminals:
                if not isinstance(t, dict):
                    continue
                t_key = str(t.get("key") or t.get("terminalKey") or t.get("id") or "").strip()
                if not t_key:
                    continue
                
                term_name = get_terminal_display_name(t_key, settings=settings)
                terminals_list.append({
                    "terminalKey": t_key,
                    "id": t.get("id"),
                    "name": term_name,
                    "custom_name": custom_names.get(t_key, ""),
                    "default_name": get_terminal_display_name(t_key, settings=None),
                    "inn": t.get("inn") or settings.terminal_key or "-",
                    "status": t.get("status") or "ACTIVE"
                })
            
            # Если реальный API вернул пустой список, добавляем основной терминал
            if not terminals_list and settings.terminal_key:
                main_key = settings.terminal_key
                terminals_list.append({
                    "terminalKey": main_key,
                    "id": main_key,
                    "name": get_terminal_display_name(main_key, settings=settings),
                    "custom_name": custom_names.get(main_key, ""),
                    "default_name": "Основной терминал эквайринга/СБП (из настроек)",
                    "inn": "-",
                    "status": "ACTIVE"
                })
                
            return terminals_list

        except Exception as api_err:
            logger.warning(f"Не удалось выгрузить терминалы из Т-Банк API ({str(api_err)}). Применяем фолбэк.")
            
            terminals_list = []
            custom_names = parse_terminal_names(settings)
            if settings.terminal_key:
                main_key = settings.terminal_key
                terminals_list.append({
                    "terminalKey": main_key,
                    "id": main_key,
                    "name": get_terminal_display_name(main_key, settings=settings),
                    "custom_name": custom_names.get(main_key, ""),
                    "default_name": "Основной терминал эквайринга/СБП (из настроек)",
                    "inn": "-",
                    "status": "ACTIVE"
                })
                
            for dt in demo_terminals:
                if settings.terminal_key and dt["terminalKey"] == settings.terminal_key:
                    continue
                dt_copy = dict(dt)
                t_key = dt_copy["terminalKey"]
                dt_copy["name"] = get_terminal_display_name(t_key, settings=settings)
                dt_copy["custom_name"] = custom_names.get(t_key, "")
                dt_copy["default_name"] = dt.get("name")
                terminals_list.append(dt_copy)
                
            return terminals_list

    except Exception as e:
        logger.error(f"Критическая ошибка при выгрузке терминалов Т-Банка: {str(e)}")
        return demo_terminals

    finally:
        if cert_file_path and os.path.exists(cert_file_path):
            try:
                os.unlink(cert_file_path)
            except Exception:
                pass

@router.get("/accounts", response_model=List[Dict[str, Any]])
def get_tbank_accounts(
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_tbank_payments_view", "bank_payments_view"))
):
    """Получение расчетных счетов компании из T-API Т-Банка"""
    settings = db.exec(select(TBankSettings)).first()
    
    # Демо-счета
    demo_accounts = [
        {
            "accountNumber": "40702810987654321001",
            "balance": {
                "otb": 850400.12,
                "authorized": 850400.12,
                "pending": 0.0,
                "currency": "RUB"
            },
            "name": "Основной счет ООО 'ФудЗука'",
            "status": "ACTIVE"
        },
        {
            "accountNumber": "40702810987654321002",
            "balance": {
                "otb": 120500.00,
                "authorized": 120500.00,
                "pending": 0.0,
                "currency": "RUB"
            },
            "name": "Резервный счет (СБП)",
            "status": "ACTIVE"
        }
    ]
    
    if not settings or not settings.token:
        return demo_accounts
        
    url = "https://business.tbank.ru/openapi/api/v3/bank-accounts"
    headers = {
        "Authorization": f"Bearer {settings.token}",
        "Content-Type": "application/json"
    }
    
    cert_file_path = None
    try:
        client = httpx.Client(timeout=10.0, verify=False)
        if settings.certificate_content and settings.certificate_content.strip():
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w", encoding="utf-8") as temp_cert:
                temp_cert.write(settings.certificate_content.strip())
                cert_file_path = temp_cert.name
            client.cert = cert_file_path
            
        response = client.get(url, headers=headers)
        if response.status_code == 200:
            try:
                return response.json()
            except Exception:
                pass
                
        return demo_accounts
    except Exception as e:
        logger.warning(f"Ошибка при выгрузке расчетных счетов Т-Банка: {str(e)}. Возвращен fallback.")
        return demo_accounts
    finally:
        if cert_file_path and os.path.exists(cert_file_path):
            try:
                os.unlink(cert_file_path)
            except Exception:
                pass

# --- Схемы для СБП QR ---
class SbpQrRequestSchema(BaseModel):
    order_id: int
    amount: float

@router.post("/sbp/create-qr", response_model=Dict[str, Any])
async def create_sbp_qr_payment(
    data: SbpQrRequestSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_tbank_payments_edit", "bank_payments_edit"))
):
    """Генерация динамического QR-кода СБП для оплаты заказа (Т-Банк касса)"""
    settings = db.exec(select(TBankSettings)).first()
    
    demo_qr = {
        "id": f"demo_sbp_qr_{data.order_id}",
        "url": f"https://qr.nspk.ru/AD1000787B2943B2943B2943B2943B29?orderId={data.order_id}",
        "svg": "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIiB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCI+PHJlY3Qgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiNmZmYiLz48cGF0aCBkPSJNMTAgMTBoODB2ODBIMTB6IiBmaWxsPSJub25lIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iNSIvPjxwYXRoIGQ9Ik0zMCAzMGg0MHY0MEgzMHoiIGZpbGw9IiMwMDAiLz48L3N2Zz4="
    }
    
    if not settings or not settings.is_active:
        logger.info(f"Т-Банк API не активен. Возвращаем демо QR для заказа {data.order_id}")
        return demo_qr

    from app.core.tbank_utils import generate_tbank_qrpay_signature, get_tbank_sbp_credentials
    mch_id, ter_id, secret_key = get_tbank_sbp_credentials(settings)

    import httpx
    import time
    import base64
    import io
    import qrcode
    import qrcode.image.svg
    from datetime import datetime

    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            url = "https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QRPAY"
            
            out_transaction_no = str(int(time.time() * 100))
            amount_str = f"{data.amount:.2f}"
            
            payload = {
                "mchId": mch_id,
                "terId": ter_id,
                "currency": "643",
                "totalAmount": amount_str,
                "outTransactionNo": out_transaction_no,
                "subject": f"Оплата заказа №{data.order_id} в FoodZuka",
                "tradeType": "pay.paxpay.native",
                "version": "V1.0",
                "signType": "HMAC_SHA256",
                "timeStart": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            payload["signature"] = generate_tbank_qrpay_signature(payload, secret_key, "qrpay")
            
            logger.info(f"Отправляем QRPAY в Т-Банк для заказа {data.order_id}: {out_transaction_no} (terId={ter_id})")
            res = await client.post(url, json=payload)
            if res.status_code != 200:
                logger.warning(f"Ошибка QRPAY Т-Банк ({res.status_code}): {res.text}")
                raise HTTPException(status_code=500, detail=f"Ошибка Т-Банк API ({res.status_code}): {res.text}")
                
            res_data = res.json()
            if res_data.get("code") != "SUCCESS":
                msg = res_data.get("msg") or res_data.get("message") or "Отклонено Т-Банком"
                logger.warning(f"Т-Банк отклонил QRPAY: {res_data}")
                raise HTTPException(status_code=500, detail=f"Т-Банк отклонил генерацию QR: {msg}")
                
            out_trade_no = res_data.get("outTradeNo")
            code_url = res_data.get("codeUrl")
            if not out_trade_no or not code_url:
                logger.warning(f"Некорректные данные в ответе QRPAY Т-Банка: {res_data}")
                raise HTTPException(status_code=500, detail="Т-Банк не вернул QR-ссылку")
                
            # Генерируем SVG QR-кода на бэкенде
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(code_url)
            qr.make(fit=True)
            
            img = qr.make_image(image_factory=qrcode.image.svg.SvgImage)
            stream = io.BytesIO()
            img.save(stream)
            qr_svg_b64 = base64.b64encode(stream.getvalue()).decode('utf-8')
            
            return {
                "id": f"tbank_qr_{out_trade_no}_{data.order_id}_{amount_str}",
                "url": code_url,
                "svg": qr_svg_b64
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Исключение при генерации QR-кода СБП: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации QR-кода: {str(e)}")

@router.get("/sbp/qr/{qr_id}/state", response_model=Dict[str, Any])
async def get_sbp_qr_state(
    qr_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_tbank_payments_view", "bank_payments_view"))
):
    """Опрос статуса оплаты по СБП QR-коду"""
    # Для демо-кодов проверяем статус заказа по БД (без авто-оплаты)
    if qr_id.startswith("demo_sbp_qr_"):
        order_id = qr_id.replace("demo_sbp_qr_", "")
        try:
            order = db.exec(select(Order).where((Order.id == int(order_id)) | (Order.external_number == order_id))).first()
            if order and order.is_paid:
                return {"id": qr_id, "status": "PAID", "amount": float(order.total_paid)}
        except Exception:
            pass
        return {"id": qr_id, "status": "CREATED", "amount": 0.0}
        
    if not qr_id.startswith("tbank_qr_"):
        return {"id": qr_id, "status": "CREATED", "amount": 0.0}

    parts = qr_id.split("_")
    if len(parts) < 5:
        return {"id": qr_id, "status": "CREATED", "amount": 0.0}
        
    out_trade_no = parts[2]
    order_id = parts[3]
    amount_str = parts[4]

    settings = db.exec(select(TBankSettings)).first()
    if not settings or not settings.is_active:
        return {"id": qr_id, "status": "CREATED", "amount": 0.0}

    from app.core.tbank_utils import generate_tbank_qrpay_signature, get_tbank_sbp_credentials
    mch_id, ter_id, secret_key = get_tbank_sbp_credentials(settings)
        
    url = "https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QUERY"
    import httpx
    import time
    from datetime import datetime
    
    out_transaction_no = str(int(time.time() * 100))
    
    payload = {
        "mchId": mch_id,
        "terId": ter_id,
        "oriTransactionNo": out_trade_no,
        "outTransactionNo": out_transaction_no,
        "totalAmount": amount_str,
        "currency": "643",
        "tradeType": "pay.paxpay.native",
        "version": "V1.0",
        "signType": "HMAC_SHA256",
        "timeStart": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
    payload["signature"] = generate_tbank_qrpay_signature(payload, secret_key, "query")
    
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            logger.info(f"Запрашиваем QUERY для outTradeNo {out_trade_no} (terId={ter_id})...")
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                api_data = response.json()
                code_str = api_data.get("code")
                status_str = api_data.get("status", "")
                
                mapped_status = "CREATED"
                if code_str == "SUCCESS" and status_str == "PAID":
                    mapped_status = "PAID"
                    amount_rub = float(amount_str)
                    
                    # 1. Если оплачено, автоматически обновляем статус оплаты в БД
                    from app.api.tbank_webhooks import process_order_payment
                    process_order_payment(db, str(order_id), amount_rub, out_trade_no, "СБП (Т-Банк касса)")
                    
                    # 2. Регистрируем реальную транзакцию в tbank_statements
                    try:
                        from app.models.tbank_settings import TBankAccountStatement
                        existing_stmt = db.exec(
                            select(TBankAccountStatement).where(
                                TBankAccountStatement.payer_account == out_trade_no,
                                TBankAccountStatement.amount == float(amount_rub)
                            )
                        ).first()
                        
                        if not existing_stmt:
                            db_op = TBankAccountStatement(
                                account_number="СБП (T-API)",
                                charge_date=datetime.now(),
                                amount=float(amount_rub),
                                payment_purpose=f"Оплата СБП QR по заказу #{order_id} (T-Pay/СБП)",
                                payer_name="Физическое лицо (СБП)",
                                payer_inn="",
                                payer_account=out_trade_no,
                                payer_bank_bic="",
                                matched_order_id=int(order_id) if str(order_id).isdigit() else None
                            )
                            db.add(db_op)
                            db.commit()
                            logger.info(f"Реальный платеж СБП {amount_rub}руб. (outTradeNo: {out_trade_no}) сохранен в tbank_statements")
                    except Exception as stmt_err:
                        logger.error(f"Ошибка сохранения транзакции СБП в tbank_statements: {stmt_err}")
                        db.rollback()
                        
                    # 3. Отправка WebSocket и Push-уведомления администратору в реальном времени
                    try:
                        from app.api.chat import manager
                        import asyncio
                        ws_payload = {
                            "type": "new_bank_payment",
                            "amount": float(amount_rub),
                            "method": "СБП (T-Pay)",
                            "customer": "Физическое лицо (СБП)",
                            "order_id": int(order_id) if str(order_id).isdigit() else None,
                            "rrn": out_trade_no
                        }
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                        if loop.is_running():
                            loop.create_task(manager.broadcast(ws_payload))
                            from app.services.iiko_sync_service import iiko_sync_service
                            loop.create_task(iiko_sync_service.send_admin_push_notification(
                                session=db,
                                title="Поступление оплаты!",
                                body=f"Сумма: {amount_rub:.2f} ₽ (СБП T-Pay) | Заказ #{order_id}",
                                url="/admin/bank/tbank-payments",
                                event_type="new_payment",
                                tag=f"payment-sbp-{out_trade_no}"
                            ))
                    except Exception as ws_err:
                        logger.error(f"Failed to send websocket payment notification: {ws_err}")
                        
                    # 4. Отправка Telegram-уведомления
                    try:
                        from app.api.tbank_webhooks import send_admin_telegram_notification
                        msg = (
                            f"⚡️ <b>Новый платеж по СБП (T-Pay)</b>\n"
                            f"💰 Сумма: <b>{amount_rub:.2f} ₽</b>\n"
                            f"📝 Заказ: <b>#{order_id}</b>\n"
                            f"👤 Способ: СБП (QR-код/Админка)\n"
                            f"🆔 RRN/QR: {out_trade_no}\n"
                            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                        )
                        send_admin_telegram_notification(msg, db)
                    except Exception as tg_err:
                        logger.error(f"Failed to send telegram sbp notification: {tg_err}")
                        
                return {"id": qr_id, "status": mapped_status, "amount": float(amount_str) if mapped_status == "PAID" else 0.0}
                
        return {"id": qr_id, "status": "CREATED", "amount": 0.0}
    except Exception as e:
        logger.warning(f"Ошибка опроса статуса QR СБП Т-Банк: {str(e)}.")
        return {"id": qr_id, "status": "CREATED", "amount": 0.0}
    finally:
        if cert_file_path and os.path.exists(cert_file_path):
            try:
                os.unlink(cert_file_path)
            except Exception:
                pass

@router.post("/sbp/qr/{order_id}/simulate-pay")
async def simulate_sbp_payment(
    order_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_tbank_payments_edit", "bank_payments_edit"))
):
    """Имитация успешной оплаты по СБП для демо-режима"""
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    from app.api.tbank_webhooks import process_order_payment
    amount = float(order.left_to_pay if order.left_to_pay > 0 else (order.total_with_discount or order.total_amount))
    
    success = process_order_payment(db, str(order_id), amount, "RRN_DEMO_SBP", "СБП (QR-код/Тест)")
    if success:
        return {"status": "success", "message": "Оплата успешно сэмулирована"}
    else:
        raise HTTPException(status_code=500, detail="Не удалось обработать оплату")

# --- Модуль 4: Операции по POS-терминалу ---
@router.get("/terminals/{terminalKey}/operations", response_model=List[Dict[str, Any]])
def get_terminal_operations(
    terminalKey: str,
    from_date: Optional[str] = None,
    till_date: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_tbank_payments_view", "bank_payments_view"))
):
    """Выгрузка успешных транзакций по конкретному POS-терминалу торгового эквайринга"""
    settings = db.exec(select(TBankSettings)).first()
    
    # Демо-транзакции
    demo_ops = [
        {"id": "txn_001", "date": "2026-06-02T16:00:00+05:00", "amount": 1500.00, "status": "CONFIRMED", "pan": "430000******0777", "rrn": "RRN173002754380", "operationType": "PAYMENT"},
        {"id": "txn_002", "date": "2026-06-02T16:10:00+05:00", "amount": 850.00, "status": "CONFIRMED", "pan": "553691******1122", "rrn": "RRN173002754381", "operationType": "PAYMENT"},
        {"id": "txn_003", "date": "2026-06-02T16:15:00+05:00", "amount": 2300.00, "status": "CONFIRMED", "pan": "430000******0777", "rrn": "RRN173002754382", "operationType": "PAYMENT"}
    ]
    
    if not settings or not settings.token:
        return demo_ops
        
    url = f"https://business.tbank.ru/openapi/api/v1/tacq/operations/terminal/{terminalKey}"
    params = {}
    if from_date:
        params["from"] = from_date
    if till_date:
        params["till"] = till_date
        
    headers = {
        "Authorization": f"Bearer {settings.token}",
        "Content-Type": "application/json"
    }
    
    cert_file_path = None
    try:
        client = httpx.Client(timeout=10.0, verify=False)
        if settings.certificate_content and settings.certificate_content.strip():
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w", encoding="utf-8") as temp_cert:
                temp_cert.write(settings.certificate_content.strip())
                cert_file_path = temp_cert.name
            client.cert = cert_file_path
            
        response = client.get(url, headers=headers, params=params)
        if response.status_code == 200:
            try:
                return response.json()
            except Exception:
                pass
                
        return demo_ops
    except Exception as e:
        logger.warning(f"Ошибка выгрузки операций по терминалу {terminalKey}: {str(e)}. Возвращен fallback.")
        return demo_ops
    finally:
        if cert_file_path and os.path.exists(cert_file_path):
            try:
                os.unlink(cert_file_path)
            except Exception:
                pass

# --- Схемы для Выписок ---
class TBankSyncStatementRequestSchema(BaseModel):
    account_number: str
    from_date: str  # YYYY-MM-DD
    till_date: str  # YYYY-MM-DD

@router.post("/sync-statement", response_model=Dict[str, Any])
def sync_tbank_statement(
    data: TBankSyncStatementRequestSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_tbank_payments_edit", "bank_payments_edit"))
):
    """Синхронизация выписки по счету Т-Банка с автоматической сверкой платежей"""
    settings = db.exec(select(TBankSettings)).first()
    
    # Демо-проводки для fallback режима
    demo_ops = [
        {
            "accountNumber": data.account_number,
            "chargeDate": f"{data.from_date}T10:15:30+05:00",
            "amount": 2500.00,
            "paymentPurpose": "Оплата заказа №186 через СБП Т-Банк",
            "payerName": "СИДОРОВ AЛЕКСЕЙ П.",
            "payerInn": "771234567891",
            "payerAccount": "40817810123456789011",
            "payerBankBic": "044525974"
        },
        {
            "accountNumber": data.account_number,
            "chargeDate": f"{data.from_date}T12:30:15+05:00",
            "amount": 1500.00,
            "paymentPurpose": "Предоплата заказа №187",
            "payerName": "ПЕТРОВ ДМИТРИЙ В.",
            "payerInn": "771234567892",
            "payerAccount": "40817810123456789012",
            "payerBankBic": "044525974"
        }
    ]
    
    real_ops = []
    
    if settings and settings.token:
        # Преобразуем даты YYYY-MM-DD в формат ISO 8601 UTC с временем
        from_api_date = f"{data.from_date}T00:00:00Z"
        
        # Т-Банк OpenAPI 'to' параметр не включителен.
        # Чтобы получить операции за till_date включительно, прибавим 1 день и установим T00:00:00Z.
        from datetime import datetime, timedelta
        to_api_date = f"{data.till_date}T23:59:59Z"
        try:
            till_dt = datetime.strptime(data.till_date, "%Y-%m-%d")
            to_api_date = (till_dt + timedelta(days=1)).strftime("%Y-%m-%d") + "T00:00:00Z"
        except Exception as e:
            logger.warning(f"Ошибка парсинга till_date '{data.till_date}': {e}")
            to_api_date = f"{data.till_date}T23:59:59Z"

        # Выгрузка реальной выписки по OpenAPI Т-Банка
        url = "https://business.tbank.ru/openapi/api/v1/statement"
        params = {
            "accountNumber": data.account_number,
            "from": from_api_date,
            "to": to_api_date
        }
        headers = {
            "Authorization": f"Bearer {settings.token}",
            "Content-Type": "application/json"
        }
        
        cert_file_path = None
        try:
            client = httpx.Client(timeout=10.0, verify=False)
            if settings.certificate_content and settings.certificate_content.strip():
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w", encoding="utf-8") as temp_cert:
                    temp_cert.write(settings.certificate_content.strip())
                    cert_file_path = temp_cert.name
                client.cert = cert_file_path
                
            response = client.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.warning(f"Т-Банк API вернул ошибку {response.status_code} при запросе выписки: {response.text[:200]}")
                return {
                    "success": False,
                    "error_message": f"Т-Банк API вернул код {response.status_code}: {response.text[:150]}"
                }
                
            try:
                api_data = response.json()
                if isinstance(api_data, list):
                    real_ops = api_data
                elif isinstance(api_data, dict):
                    # Проверяем все возможные варианты расположения массива транзакций в JSON
                    if "operation" in api_data:
                        real_ops = api_data["operation"]
                    elif "operations" in api_data:
                        real_ops = api_data["operations"]
                    elif "content" in api_data:
                        real_ops = api_data["content"]
                    elif "payload" in api_data:
                        payload = api_data["payload"]
                        if isinstance(payload, list):
                            real_ops = payload
                        elif isinstance(payload, dict):
                            if "operation" in payload:
                                real_ops = payload["operation"]
                            elif "operations" in payload:
                                real_ops = payload["operations"]
                            elif "content" in payload:
                                real_ops = payload["content"]
                            else:
                                real_ops = []
                        else:
                            real_ops = []
                    else:
                        real_ops = []
                else:
                    real_ops = []
            except Exception as parse_err:
                logger.error(f"Ошибка разбора ответа выписки Т-Банка: {parse_err}")
                return {
                    "success": False,
                    "error_message": f"Не удалось распарсить ответ Т-Банка: {str(parse_err)}"
                }
                
        except Exception as e:
            logger.warning(f"Ошибка при выгрузке выписки Т-Банка: {str(e)}")
            return {
                "success": False,
                "error_message": f"Ошибка соединения с Т-Банк API: {str(e)}"
            }
        finally:
            if cert_file_path and os.path.exists(cert_file_path):
                try:
                    os.unlink(cert_file_path)
                except Exception:
                    pass
                    
    # Сохраняем и обрабатываем строго реальные проводки, избегаем записи демо-данных в БД
    ops_to_process = real_ops
    
    added_count = 0
    added_sum = 0.0
    matched_count = 0
    
    import re
    from datetime import datetime
    
    for op in ops_to_process:
        if not isinstance(op, dict):
            continue
            
        # Фильтруем только зачисления (Credit)
        type_op = op.get("typeOfOperation")
        if type_op != "Credit":
            continue
            
        # Нормализация назначения платежа и плательщика
        purpose = (op.get("paymentPurpose") or op.get("purpose") or op.get("description") or op.get("payPurpose") or "").lower()
        payer_obj = op.get("payer") or {}
        cp_obj = op.get("counterParty") or {}
        p_name_check = op.get("payerName") or payer_obj.get("name") or cp_obj.get("name") or "Физическое лицо"
        p_inn_check = str(op.get("payerInn") or payer_obj.get("inn") or cp_obj.get("inn") or "").strip()
        payer_lower = p_name_check.lower()

        # 1. Зачисления от самого Банка (выплаты эквайринга, реестры, проценты, комиссии)
        is_bank_sender = (
            any(word in payer_lower for word in ["т-банк", "тбанк", "t-bank", "tbank", "тинькофф", "tinkoff", "t-pay", "tpay"])
            or p_inn_check == "7710140679"
        )

        # Чисто служебные операции банка
        is_bank_service = any(word in purpose for word in [
            "реестр выплат", "реестр договоров", "реестр операций", "реестр за", "реестр",
            "комиссия за", "комиссионное вознаграждение", "удержание комиссии", "списание комиссии",
            "проценты по счету", "проценты на остаток", "плата за обслуживание", "абонентская плата"
        ])
        
        # Зачисление реестра по терминалам эквайринга от банка
        is_acquiring_settlement = any(word in purpose for word in [
            "зачисление средств по терминалам", "зачисление средств по операциям", "выплата по терминалам",
            "выплата по операциям эквайринга", "выплата возмещения", "возмещение по торговому эквайрингу",
            "возмещение по эквайрингу", "перечисление выручки", "перечисление возмещения", "зачисление выручки",
            "по договору эквайринга", "по договору интернет-эквайринга", "по операциям с использованием карт",
            "зачисление средств по договору"
        ])

        # 2. Признаки возвратов
        is_refund = "возврат" in purpose or "refund" in purpose

        # 3. Признаки B2B (другие юрлица и ИП)
        is_b2b = False
        has_corp_keywords = any(word in payer_lower for word in [
            "ооо", "пао", "зао", "ао ", " лтд", " ltd", "ип ", "ип.", "и.п.", "индивидуальный предприниматель"
        ])
        
        if p_inn_check:
            if len(p_inn_check) == 10 and p_inn_check != "7710140679":
                is_b2b = True
            elif len(p_inn_check) == 12 and has_corp_keywords and not is_bank_sender:
                is_b2b = True
        else:
            if has_corp_keywords and not is_bank_sender:
                is_b2b = True

        # Проверка назначения платежа на наличие фразы про заказ/доставку
        has_order_phrase = False
        if any(word in purpose for word in ["заказ", "заказа", "доставк", "foodzuka", "фудзука", "оплата заказа", "оплата по сбп"]):
            has_order_phrase = True

        # Признаки платежа физического лица (СБП, T-Pay, взносы наличных, пополнения через банкомат/кассу)
        is_retail_payment = any(word in purpose for word in [
            "сбп", "qr", "tpay", "t-pay", "перевод от физ"
        ])

        # Сводим все правила сокрытия
        should_hide = False
        if is_refund:
            should_hide = True
        elif is_bank_service:
            should_hide = True
        elif is_acquiring_settlement:
            should_hide = True
        elif is_bank_sender:
            # Скрываем зачисления от самого банка, только если это не прямой розничный платеж СБП/T-Pay
            if not (is_retail_payment or has_order_phrase):
                should_hide = True
        elif is_b2b:
            # Скрываем переводы от юрлиц/ИП, только если это не оплата конкретного заказа
            if not (has_order_phrase or is_retail_payment):
                should_hide = True

        if should_hide:
            continue

        is_payment = True


        # Устойчивое получение поля даты
        charge_dt_str = op.get("chargeDate") or op.get("date") or op.get("drawDate") or op.get("operationDate")
        if not charge_dt_str:
            logger.warning(f"Пропущена операция, так как не найдено поле даты: {op}")
            continue
            
        try:
            charge_dt = datetime.fromisoformat(charge_dt_str.replace("Z", "+00:00"))
        except Exception:
            try:
                from dateutil import parser
                charge_dt = parser.parse(charge_dt_str)
            except Exception:
                charge_dt = datetime.now()
                
        # Нормализация полей суммы, счета и плательщика
        op_account = op.get("accountNumber") or op.get("account") or data.account_number
        try:
            op_amount = float(op.get("amount") or op.get("operationAmount") or op.get("payment") or 0)
        except Exception:
            op_amount = 0.0
            
        # Проверяем, есть ли уже такая операция в БД (по совпадению счета, даты и суммы)
        existing = db.exec(
            select(TBankAccountStatement).where(
                TBankAccountStatement.account_number == op_account,
                TBankAccountStatement.charge_date == charge_dt,
                TBankAccountStatement.amount == op_amount
            )
        ).first()
        
        if not existing:
            # Считываем реквизиты плательщика из вложенных структур payer/counterParty, если они есть
            payer_obj = op.get("payer") or {}
            cp_obj = op.get("counterParty") or {}
            
            p_name = op.get("payerName") or payer_obj.get("name") or cp_obj.get("name") or "Физическое лицо"
            
            # Если это розничный платеж, заменяем служебные имена банка-плательщика на понятные для человека
            if is_payment and any(word in p_name.lower() for word in ["т-банк", "тбанк", "t-bank", "tbank", "тинькофф", "tinkoff"]):
                if "сбп" in purpose or "qr" in purpose:
                    p_name = "Физическое лицо (СБП)"
                elif "tpay" in purpose or "t-pay" in purpose:
                    p_name = "Физическое лицо (T-Pay)"
                else:
                    p_name = "Физическое лицо (Эквайринг)"
                    
            p_inn = op.get("payerInn") or payer_obj.get("inn") or cp_obj.get("inn")
            p_acc = op.get("payerAccount") or op.get("payerAccountNum") or payer_obj.get("acct") or cp_obj.get("account")
            p_bic = op.get("payerBankBic") or op.get("bic") or payer_obj.get("bicRu") or cp_obj.get("bankBic")

            # Создаем запись
            db_op = TBankAccountStatement(
                account_number=op_account,
                charge_date=charge_dt,
                amount=op_amount,
                payment_purpose=op.get("paymentPurpose") or op.get("purpose") or op.get("description") or op.get("payPurpose") or "Входящий платеж",
                payer_name=p_name,
                payer_inn=p_inn,
                payer_account=p_acc,
                payer_bank_bic=p_bic
            )
            
            # Пытаемся автоматически сопоставить входящий платеж с заказом
            if db_op.amount > 0:
                from app.api.tbank_webhooks import find_best_matching_order, process_order_payment
                
                # Используем интеллектуальный алгоритм сверки по времени и сумме
                matched_order = find_best_matching_order(
                    db=db,
                    amount=db_op.amount,
                    tx_date=db_op.charge_date,
                    terminal_key=None,
                    purpose=db_op.payment_purpose
                )
                
                if matched_order:
                    db_op.matched_order_id = matched_order.id
                    matched_count += 1
                        
            db.add(db_op)
            db.flush()
            added_count += 1
            added_sum += db_op.amount

            # WebSocket и Web Push оповещение в реальном времени
            try:
                from app.services.iiko_sync_service import iiko_sync_service
                method_txt = "СБП (Выписка)" if ("сбп" in db_op.payment_purpose.lower() or "qr" in db_op.payment_purpose.lower()) else "Выписка"
                ws_payload = {
                    "type": "new_bank_payment",
                    "amount": float(db_op.amount),
                    "method": method_txt,
                    "customer": db_op.payer_name or "Физическое лицо",
                    "order_id": db_op.matched_order_id
                }
                iiko_sync_service.send_websocket_broadcast_safe(ws_payload)

                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                push_coro = iiko_sync_service.send_admin_push_notification(
                    session=db,
                    title="Поступление оплаты!",
                    body=f"Сумма: {db_op.amount:.2f} ₽ ({method_txt}) | {db_op.payer_name or 'Физическое лицо'}",
                    url="/admin/bank/tbank-payments",
                    event_type="new_payment",
                    tag=f"payment-bank-{db_op.id or Date.now()}"
                )
                if loop.is_running():
                    loop.create_task(push_coro)
                else:
                    loop.run_until_complete(push_coro)
            except Exception as ws_err:
                logger.error(f"Failed to send real-time notification for synced statement payment: {ws_err}")
            
    db.commit()
    
    # Отправляем сводное уведомление администратору при добавлении новых проводок
    if added_count > 0:
        try:
            from app.api.tbank_webhooks import send_admin_telegram_notification
            msg = (
                f"📊 <b>Успешная выгрузка выписки Т-Банка</b>\n"
                f"📥 Новых операций: <b>{added_count}</b>\n"
                f"💰 На общую сумму: <b>{added_sum:.2f} ₽</b>\n"
                f"🎯 Автоматически сверено: <b>{matched_count}</b>\n"
                f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            )
            send_admin_telegram_notification(msg, db)
        except Exception as e:
            logger.error(f"Failed to send statement summary notification: {e}")
    
    return {
        "success": True,
        "processed_operations": len(ops_to_process),
        "new_operations_added": added_count,
        "orders_automatically_matched": matched_count
    }


class TBankCheckPaymentRequest(BaseModel):
    payment_id: Optional[str] = None
    order_id: Optional[int] = None
    rrn: Optional[str] = None

@router.post("/check-payment-status", response_model=Dict[str, Any])
async def check_tbank_payment_status(
    data: TBankCheckPaymentRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(deps.require_any_permission("bank_tbank_payments_view", "bank_payments_view"))
):
    """
    Запрос типа платежа, способа оплаты и реального статуса через API Т-Банка
    (Проверка через Merchant Acquiring API v2/GetState и QRPay QUERY)
    """
    settings = db.exec(select(TBankSettings)).first()
    
    result = {
        "success": False,
        "source": "api",
        "payment_method": "Эквайринг",
        "status": "UNKNOWN",
        "amount": 0.0,
        "rrn": data.rrn or "-",
        "details": {}
    }
    
    if not settings or not settings.token:
        # Фолбэк по базе данных
        if data.order_id:
            ord_obj = db.get(Order, data.order_id)
            if ord_obj:
                pm = (ord_obj.payment_method or "").lower()
                method_name = "Эквайринг"
                if "сбп" in pm or "qr" in pm:
                    method_name = "СБП"
                elif "tpay" in pm or "t-pay" in pm:
                    method_name = "T-Pay"
                elif "курьер" in pm:
                    method_name = "Картой курьеру"
                elif "налич" in pm:
                    method_name = "Наличные"
                    
                result["success"] = True
                result["source"] = "database"
                result["payment_method"] = method_name
                result["status"] = "CONFIRMED" if ord_obj.is_paid else "PENDING"
                result["amount"] = float(ord_obj.total_paid if ord_obj.total_paid else (ord_obj.total_with_discount or ord_obj.total_amount))
                result["details"] = {"order_status": ord_obj.status, "payment_method": ord_obj.payment_method}
                return result
                
        return result

    terminal_key = settings.acquiring_terminal_key or settings.terminal_key or "42734785"
    terminal_password = settings.acquiring_password or settings.token or ""
    
    # 1. Запрос в Merchant Acquiring API Т-Банка (GetState)
    from app.core.tbank_utils import generate_tbank_token
    query_id = data.payment_id or (str(data.order_id) if data.order_id else None)
    
    if query_id and terminal_password:
        try:
            async with httpx.AsyncClient(timeout=8.0, verify=False) as client:
                payload = {
                    "TerminalKey": terminal_key,
                    "PaymentId": query_id
                }
                payload["Token"] = generate_tbank_token(payload, terminal_password)
                
                resp = await client.post("https://securepay.tinkoff.ru/v2/GetState", json=payload)
                if resp.status_code == 200:
                    api_resp = resp.json()
                    if api_resp.get("Success") is True:
                        st = api_resp.get("Status", "CONFIRMED")
                        amt = float(api_resp.get("Amount", 0)) / 100.0
                        
                        # Определяем метод оплаты по ответу Т-Банка
                        pm_str = "Эквайринг"
                        params_data = api_resp.get("Params") or []
                        params_dict = {p.get("Key"): p.get("Value") for p in params_data if isinstance(p, dict)}
                        
                        if api_resp.get("PaymentType") == "QR" or "qr" in str(api_resp).lower() or params_dict.get("QR"):
                            pm_str = "СБП"
                        elif "tpay" in str(api_resp).lower() or params_dict.get("TPAY"):
                            pm_str = "T-Pay"
                            
                        result["success"] = True
                        result["source"] = "tbank_acquiring_api"
                        result["payment_method"] = pm_str
                        result["status"] = st
                        result["amount"] = amt
                        result["rrn"] = api_resp.get("Rrn") or data.rrn or f"42734785{data.order_id:04d}" if data.order_id else "-"
                        result["details"] = api_resp
                        return result
        except Exception as e:
            logger.warning(f"Ошибка запроса GetState в Т-Банк: {e}")

    # 2. Запрос в QRPay API Т-Банка (для СБП транзакций)
    if data.rrn or data.payment_id:
        try:
            from app.core.tbank_utils import generate_tbank_qrpay_signature, get_tbank_sbp_credentials
            from datetime import datetime
            import time
            mch_id, ter_id, secret_key = get_tbank_sbp_credentials(settings)
            
            async with httpx.AsyncClient(timeout=8.0, verify=False) as client:
                out_trade_no = data.rrn or data.payment_id
                out_transaction_no = str(int(time.time() * 100))
                
                qr_payload = {
                    "mchId": mch_id,
                    "terId": ter_id,
                    "oriTransactionNo": out_trade_no,
                    "outTransactionNo": out_transaction_no,
                    "totalAmount": "0.00",
                    "currency": "643",
                    "tradeType": "pay.paxpay.native",
                    "version": "V1.0",
                    "signType": "HMAC_SHA256",
                    "timeStart": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                }
                qr_payload["signature"] = generate_tbank_qrpay_signature(qr_payload, secret_key, "query")
                
                qr_resp = await client.post("https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QUERY", json=qr_payload)
                if qr_resp.status_code == 200:
                    qr_data = qr_resp.json()
                    if qr_data.get("code") == "SUCCESS":
                        result["success"] = True
                        result["source"] = "tbank_qrpay_api"
                        result["payment_method"] = "СБП"
                        result["status"] = qr_data.get("status", "PAID")
                        result["amount"] = float(qr_data.get("totalAmount", 0))
                        result["rrn"] = out_trade_no
                        result["details"] = qr_data
                        return result
        except Exception as e:
            logger.warning(f"Ошибка запроса QUERY в QRPay Т-Банк: {e}")

    # 3. Фолбэк по сопоставленному заказу в БД
    if data.order_id:
        ord_obj = db.get(Order, data.order_id)
        if ord_obj:
            pm = (ord_obj.payment_method or "").lower()
            comm = (ord_obj.comment or "").lower()
            method_name = "Эквайринг"
            
            if isinstance(ord_obj.payments_details, dict) and ord_obj.payments_details.get("actual_payment_method"):
                method_name = ord_obj.payments_details["actual_payment_method"]
            elif any(w in pm for w in ["сбп", "qr"]) or any(w in comm for w in ["сбп", "sbp"]):
                method_name = "СБП"
            elif any(w in pm for w in ["tpay", "t-pay"]) or any(w in comm for w in ["tpay", "t-pay"]):
                method_name = "T-Pay"
            elif "приложении" in comm:
                method_name = "СБП (T-Pay)"
            elif "курьер" in pm:
                method_name = "Картой курьеру"
                
            result["success"] = True
            result["source"] = "database_order"
            result["payment_method"] = method_name
            result["status"] = "CONFIRMED" if ord_obj.is_paid else "PENDING"
            result["amount"] = float(ord_obj.total_paid if ord_obj.total_paid else (ord_obj.total_with_discount or ord_obj.total_amount))
            result["details"] = {"order_status": ord_obj.status, "payment_method": ord_obj.payment_method}

    return result

