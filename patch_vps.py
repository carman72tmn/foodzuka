import os

def patch_file(filepath, target, replacement):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if target in content:
        new_content = content.replace(target, replacement)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Patched {filepath}")
    else:
        print(f"Target not found in {filepath}")

# Paths
base_path = "/root/foodzuka/foodtech"
sync_service = os.path.join(base_path, "backend/app/services/iiko_sync_service.py")
order_modal = os.path.join(base_path, "admin/resources/js/components/OrderDetailModal.vue")
order_index = os.path.join(base_path, "admin/resources/js/pages/orders/index.vue")

# 1. iiko_sync_service.py - parse_dt
parse_dt_target = """            def parse_dt(dt_str):
                if not dt_str:
                    return None
                try:
                    if 'Z' in dt_str:
                        dt_parsed = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                        dt_naive = dt_parsed.replace(tzinfo=None)
                        return dt_naive.replace(tzinfo=tz).astimezone(timezone.utc)
                    dt = datetime.fromisoformat(dt_str)
                    if dt.tzinfo is None:
                        # Используем часовой пояс организации для наивных дат
                        dt = dt.replace(tzinfo=tz)
                    return dt.astimezone(timezone.utc)
                except:
                    return None"""

parse_dt_replacement = """            def parse_dt(dt_str):
                if not dt_str:
                    return None
                try:
                    # ISO 8601 с Z или смещением
                    if 'Z' in dt_str or '+' in dt_str or '-' in dt_str[10:]:
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                        return dt.astimezone(timezone.utc)
                    # Наивная дата - считаем локальной для заведения
                    dt = datetime.fromisoformat(dt_str)
                    return dt.replace(tzinfo=tz).astimezone(timezone.utc)
                except Exception as e:
                    logger.error(f"Error parsing date {dt_str}: {e}")
                    return None"""

patch_file(sync_service, parse_dt_target, parse_dt_replacement)

# 2. iiko_sync_service.py - fallback expected_time
fallback_target = """            di = o_data.get("deliveryInfo") or {}
            expected_time = None
            actual_time = None
            if di:
                expected_time = parse_dt(di.get("expectedDate") or di.get("completeBefore"))
                actual_time = parse_dt(di.get("actualDate") or di.get("actualTime"))"""

fallback_replacement = """            di = o_data.get("deliveryInfo") or {}
            expected_time = None
            actual_time = None
            if di:
                expected_time = parse_dt(di.get("expectedDate") or di.get("completeBefore"))
                actual_time = parse_dt(di.get("actualDate") or di.get("actualTime"))
            
            # Фолбэк на верхний уровень объекта заказа (iiko Cloud API v2)
            if not expected_time:
                expected_time = parse_dt(o_data.get("completeBefore"))
            if not actual_time:
                actual_time = parse_dt(o_data.get("actualDate"))"""

patch_file(sync_service, fallback_target, fallback_replacement)

# 3. is_asap logic
is_asap_target = """            # --- ЛОГИКА ОПРЕДЕЛЕНИЯ ASAP / ПРЕДЗАКАЗ ---
            raw_comment = clean_str(o_data.get("comment"))
            comment_lower = (raw_comment or "").lower()
            
            # Базовые значения из iiko
            final_is_asap = bool(o_data.get("isAsap", True))
            
            # 1. Если delivery date (expected_time) отсутствует -> ASAP
            if not expected_time:
                final_is_asap = True
            else:
                # 2. Если есть время готовности
                # А) Время готовности > время создания + 180 мин И нет комментария -> Заказ на время
                if iiko_creation_time:
                    diff_mins = (expected_time - iiko_creation_time).total_seconds() / 60
                    if diff_mins > 180 and not raw_comment:
                        final_is_asap = False
                
                # Б) Если в комменте "на время" или "предзаказ" -> Заказ на время
                if "на время" in comment_lower or "предзаказ" in comment_lower:
                    final_is_asap = False
                # В) Если коммент есть, но в нем НЕТ "на время" или "предзаказ" -> ASAP
                elif raw_comment and "на время" not in comment_lower and "предзаказ" not in comment_lower:
                    final_is_asap = True"""

is_asap_replacement = """            # --- ЛОГИКА ОПРЕДЕЛЕНИЯ ASAP / ПРЕДЗАКАЗ ---
            raw_comment = clean_str(o_data.get("comment"))
            comment_lower = (raw_comment or "").lower()
            
            # Базовые значения из iiko (приоритет - флагу isAsap)
            final_is_asap = bool(o_data.get("isAsap", True))
            
            # 1. Если флаг isAsap явно False - это предзаказ
            if o_data.get("isAsap") is False:
                final_is_asap = False
            
            # 2. Если есть время готовности и оно значительно отличается от времени создания
            if expected_time and iiko_creation_time:
                diff_mins = (expected_time - iiko_creation_time).total_seconds() / 60
                # Если разница более 90 минут - скорее всего это предзаказ (на время)
                if diff_mins > 90:
                    final_is_asap = False
            
            # 3. Дополнительные проверки по комментарию (если флаг все еще True)
            if final_is_asap:
                if "на время" in comment_lower or "предзаказ" in comment_lower:
                    final_is_asap = False
            
            # 4. Если в комменте НЕТ ключевых слов предзаказа, но есть другой текст, 
            # и при этом время доставки близко к времени создания - оставляем ASAP
            elif raw_comment and "на время" not in comment_lower and "предзаказ" not in comment_lower:
                if expected_time and iiko_creation_time:
                    diff_mins = (expected_time - iiko_creation_time).total_seconds() / 60
                    if diff_mins < 90:
                        final_is_asap = True"""

patch_file(sync_service, is_asap_target, is_asap_replacement)

# UI changes are more complex for direct string replacement if they differ slightly on VPS.
# I will overwrite the files with the local versions for UI components as they should be identical.
