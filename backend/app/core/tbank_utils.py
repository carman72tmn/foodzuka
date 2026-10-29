import hashlib
import logging

logger = logging.getLogger(__name__)

def generate_tbank_token(payload: dict, password: str) -> str:
    """
    Генерация подписи (Token) для Acquiring API Т-Банка (Merchant API / securepay).
    
    Алгоритм:
    1. Исключаем Token, а также массивы и объекты (Receipt, DATA, Shops, Receipts и др.).
    2. Добавляем ключ Password со значением секретного ключа (пароля терминала).
    3. Сортируем ключи по алфавиту.
    4. Конкатенируем значения.
    5. Вычисляем SHA-256 в hex-виде (в нижнем регистре).
    """
    params = payload.copy()
    
    # Исключаем служебные поля и сложные типы данных
    keys_to_exclude = ['Token', 'token', 'Receipt', 'DATA', 'DATA_TYPE', 'Shops', 'Receipts', 'DATA_TYPE_QR']
    for key in keys_to_exclude:
        params.pop(key, None)
        
    # Оставляем только плоские типы (строки, числа, булевы значения)
    filtered_params = {}
    for k, v in params.items():
        if not isinstance(v, (dict, list)):
            filtered_params[k] = v
            
    filtered_params['Password'] = password
    
    # Сортируем по ключам
    sorted_keys = sorted(filtered_params.keys())
    
    # Собираем значения в строку
    concatenated = "".join(str(filtered_params[k]) for k in sorted_keys)
    
    # Вычисляем SHA-256
    token_hex = hashlib.sha256(concatenated.encode('utf-8')).hexdigest()
    return token_hex

def generate_tbank_qrpay_signature(payload: dict, secret_key: str, method: str) -> str:
    """
    Генерация подписи (signature) для QRPay API Т-Банка (кассовое ПО).
    
    Алгоритм:
    1. Исключаем signature и signType.
    2. Добавляем поле method со значением метода в нижнем регистре.
    3. Оставляем только плоские непустые значения.
    4. Сортируем ключи по алфавиту.
    5. Формируем строку stringToSign в виде key1=val1&key2=val2...
    6. При этом totalAmount форматируем с 2 знаками после запятой.
    7. Декодируем base64 секретный ключ (или используем как строку, если декодирование не удалось).
    8. Вычисляем HMAC-SHA256 в hex-виде (в нижнем регистре).
    """
    import base64
    import hmac
    
    params = payload.copy()
    params.pop('signature', None)
    
    params['method'] = method
    
    # Оставляем только непустые значения
    filtered = {}
    for k, v in params.items():
        if v is not None and v != "":
            filtered[k] = v
            
    # Сортируем по ключам
    sorted_keys = sorted(filtered.keys())
    
    # Собираем строку
    parts = []
    for k in sorted_keys:
        val = filtered[k]
        if isinstance(val, bool):
            val = str(val).lower()
        elif isinstance(val, (int, float)):
            if k == "totalAmount":
                val = f"{float(val):.2f}"
            else:
                val = str(val)
        parts.append(f"{k}={val}")
        
    string_to_sign = "&".join(parts)
    
    # Декодируем base64 секретный ключ
    try:
        key_bytes = base64.b64decode(secret_key)
    except Exception:
        key_bytes = secret_key.encode('utf-8')
        
    msg_bytes = string_to_sign.encode('utf-8')
    sig = hmac.new(key_bytes, msg_bytes, hashlib.sha256).hexdigest()
    return sig


def get_tbank_sbp_credentials(settings) -> tuple:
    """
    Возвращает валидные параметры для работы с сервисом СБП QRPAY Т-Банка:
    (mch_id, ter_id, secret_key)
    
    1. mch_id: Merchant ID (по умолчанию мерчант FoodZuka/Dovezuka '400000001164353')
    2. ter_id: TID кассового терминала СБП (по умолчанию '42734785')
    3. secret_key: Секретный ключ подписи HMAC-SHA256 Base64
    """
    mch_id = "400000001164353"
    if settings and getattr(settings, "merchant_id", None):
        val = str(settings.merchant_id).strip()
        if val:
            mch_id = val
            
    ter_id = "42734785"
    if settings and getattr(settings, "sbp_terminal_id", None):
        val = str(settings.sbp_terminal_id).strip()
        if val:
            ter_id = val

    secret_key = "LYqV0t7V3FBffuphkOs7oR7Le9Cr994xRjmaGxoVJKY="
    if settings:
        if getattr(settings, "sbp_secret_key", None):
            val = str(settings.sbp_secret_key).strip()
            if val:
                secret_key = val
        elif getattr(settings, "terminal_key", None):
            val = str(settings.terminal_key).strip()
            # Если в terminal_key сохранен base64 ключ подписи (не числовой POS терминал)
            if val and not val.isdigit():
                secret_key = val
                
    return mch_id, ter_id, secret_key


import json

def parse_terminal_names(settings) -> dict:
    """Парсит пользовательские названия терминалов из JSON настройки terminal_names."""
    if not settings:
        return {}
    raw = getattr(settings, "terminal_names", None)
    if not raw:
        return {}
    if isinstance(raw, dict):
        return {str(k).strip(): str(v).strip() for k, v in raw.items() if str(v).strip()}
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return {str(k).strip(): str(v).strip() for k, v in parsed.items() if str(v).strip()}
    except Exception:
        pass
    return {}

def get_terminal_display_name(terminal_key: str, sbp_acc: str = "", settings=None) -> str:
    """
    Возвращает отображаемое имя терминала Т-Банка с приоритетом пользовательского названия из настроек.
    """
    key = str(terminal_key or "").strip()
    custom_names = parse_terminal_names(settings)
    
    # 1. Проверяем точное совпадение ключа терминала с кастомным названием
    if key and key in custom_names:
        return custom_names[key]
        
    # 2. Проверяем вхождение ключа в sbp_acc / purpose
    sbp_lower = str(sbp_acc or "").lower()
    for c_key, c_name in custom_names.items():
        if c_key and (c_key in sbp_lower or (key and c_key == key)):
            return c_name

    # 3. Дефолтные человекопонятные названия
    if key == "3190040478" or "3190040478" in sbp_lower:
        return "Терминал 3190040478 (Доставка)"
    if key == "3210284772" or "3210284772" in sbp_lower:
        return "Терминал 3210284772 (Касса)"
    if key == "2332089853" or "2332089853" in sbp_lower:
        return "Терминал 2332089853 (Касса архив)"
    if key == "42734785" or "42734785" in sbp_lower:
        return "T-API (42734785)"
    if "dovezuka" in sbp_lower:
        return "Терминал DOVEZUKA (СБП)"
    if "litvinov" in sbp_lower or "литвинов" in sbp_lower:
        return "Терминал Литвинов (СБП)"
    if key.startswith("408"):
        return f"Счет ...{key[-4:]}"
    if len(key) > 0 and len(key) <= 12 and key.isdigit():
        return f"Терминал {key}"
    if key:
        return f"Терминал {key}"
    return "Терминал Т-Банк"


