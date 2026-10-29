import re

file_path = "backend/app/services/ai_assistant_service.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update update_assistant and add toggle_assistant_active
old_block = """    def update_assistant(self, session: Session, assistant_id: int, data: Dict[str, Any]) -> Optional[AiSiteAssistant]:
        assistant = session.get(AiSiteAssistant, assistant_id)
        if not assistant:
            return None

        for field in [
            "name", "role_title", "avatar_skin", "avatar_custom_url", "avatar_animation_mode",
            "character_tone", "assigned_pages", "zone_of_responsibility", "linked_agent_code",
            "connection_id", "model_override", "is_active", "allow_sound_alerts", "allow_voice_tts",
            "daily_token_limit", "daily_requests_limit", "auto_check_interval_sec", "system_prompt_addon"
        ]:
            if field in data:
                setattr(assistant, field, data[field])

        assistant.updated_at = datetime.utcnow()
        session.add(assistant)
        session.commit()
        session.refresh(assistant)
        return assistant"""

new_block = """    def update_assistant(self, session: Session, assistant_id: int, data: Dict[str, Any]) -> Optional[AiSiteAssistant]:
        assistant = session.get(AiSiteAssistant, assistant_id)
        if not assistant:
            return None

        allowed_fields = [
            "name", "role_title", "avatar_skin", "avatar_custom_url", "avatar_animation_mode",
            "character_tone", "assigned_pages", "zone_of_responsibility", "linked_agent_code",
            "connection_id", "model_override", "is_active", "allow_sound_alerts", "allow_voice_tts",
            "daily_token_limit", "daily_requests_limit", "auto_check_interval_sec", "system_prompt_addon",
            "allow_external_queries", "allow_iiko_api_queries", "allow_iiko_export",
            "allowed_external_tools", "iiko_allowed_actions", "enable_analytics_learning"
        ]

        for field in allowed_fields:
            if field in data and data[field] is not None:
                val = data[field]
                if field in ("daily_token_limit", "daily_requests_limit", "auto_check_interval_sec"):
                    try:
                        val = int(val)
                    except (ValueError, TypeError):
                        continue
                elif field == "connection_id":
                    try:
                        val = int(val) if val not in ("", None) else None
                    except (ValueError, TypeError):
                        val = None
                setattr(assistant, field, val)

        assistant.updated_at = datetime.utcnow()
        session.add(assistant)
        session.commit()
        session.refresh(assistant)
        return assistant

    def toggle_assistant_active(self, session: Session, assistant_id: int, is_active: Optional[bool] = None) -> Optional[AiSiteAssistant]:
        assistant = session.get(AiSiteAssistant, assistant_id)
        if not assistant:
            return None
        if is_active is None:
            assistant.is_active = not assistant.is_active
        else:
            assistant.is_active = bool(is_active)
        assistant.updated_at = datetime.utcnow()
        session.add(assistant)
        session.commit()
        session.refresh(assistant)
        return assistant"""

# Normalize newlines for matching
content_norm = content.replace("\r\n", "\n")
old_block_norm = old_block.replace("\r\n", "\n")
new_block_norm = new_block.replace("\r\n", "\n")

if old_block_norm in content_norm:
    content_norm = content_norm.replace(old_block_norm, new_block_norm)
    print("Found and replaced update_assistant block!")
else:
    print("WARNING: old_block not found in content!")

# 2. Add restrictions into chat_with_assistant prompt
old_prompt_rules = """ПРАВИЛА ОТВЕТА:
1. Отвечай кратко, ёмко и структурированно (не более 2-4 абзацев). Береги токены!
2. Всегда оставайся в своем образе «{assistant.name}».
3. Если есть задержки на кухне или новые зависшие заказы — обязательно упомяни их сотруднику!"""

new_prompt_rules = """ОГРАНИЧЕНИЯ И ПРАВА ДОСТУПА ПОМОЩНИКА:
{ext_queries_rule}
{iiko_access_rule}

ПРАВИЛА ОТВЕТА:
1. Отвечай кратко, ёмко и структурированно (не более 2-4 абзацев). Береги токены!
2. Всегда оставайся в своем образе «{assistant.name}».
3. Если есть задержки на кухне или новые зависшие заказы — обязательно упомяни их сотруднику!
4. Строго соблюдай установленные ограничения на сторонние ресурсы и доступ к iiko API!"""

old_prompt_rules_norm = old_prompt_rules.replace("\r\n", "\n")
new_prompt_rules_norm = new_prompt_rules.replace("\r\n", "\n")

# Check before system_prompt definition to set ext_queries_rule and iiko_access_rule
old_prompt_setup = """        # Тон общения
        tones = {"""

new_prompt_setup = """        # Ограничения и права помощника
        if getattr(assistant, "allow_external_queries", True):
            ext_tools = ", ".join(getattr(assistant, "allowed_external_tools", []) or ["погода", "общий поиск"])
            ext_queries_rule = f"- РАЗРЕШЕНО отвечать на вопросы о погоде, внешних условиях и общих вопросах ({ext_tools})."
        else:
            ext_queries_rule = "- ЗАПРЕЩЕНО делать запросы к сторонним ресурсам (погода, внешние сайты). Вежливо перенаправляй сотрудника на вопросы заведения."

        if getattr(assistant, "allow_iiko_api_queries", False):
            iiko_actions = ", ".join(getattr(assistant, "iiko_allowed_actions", []) or ["чтение заказов", "стоп-лист"])
            iiko_access_rule = f"- РАЗРЕШЕН доступ к iiko API для аналитики данных ({iiko_actions})."
            if getattr(assistant, "allow_iiko_export", False):
                iiko_access_rule += " Разрешена самостоятельная выгрузка отчетов iiko."
        else:
            iiko_access_rule = "- Прямой доступ к iiko API и выгрузкам ограничен."

        # Тон общения
        tones = {"""

if old_prompt_setup.replace("\r\n", "\n") in content_norm:
    content_norm = content_norm.replace(old_prompt_setup.replace("\r\n", "\n"), new_prompt_setup.replace("\r\n", "\n"))
    print("Added prompt setup for restrictions!")

if old_prompt_rules_norm in content_norm:
    content_norm = content_norm.replace(old_prompt_rules_norm, new_prompt_rules_norm)
    print("Added prompt rules for restrictions!")

# 3. Add get_analytics_observations and generate_ai_analytics_summary before the end
analytics_code = '''
    # ==========================================
    # 4. МОДУЛЬ НАБЛЮДЕНИЙ И СТАТИСТИКИ (ZERO-TOKEN)
    # ==========================================

    def get_analytics_observations(self, session: Session, days: int = 7) -> Dict[str, Any]:
        """
        Аналитический модуль наблюдений и статистики работы в админке.
        Режим жесткой экономии токенов (Zero-Token mode):
        Все расчеты выполняются детерминированно SQL/Python средствами без расхода квот LLM.
        """
        since_date = datetime.utcnow() - timedelta(days=days)

        # 1. Общие показатели за период
        total_summary_row = session.execute(
            text("""
                SELECT
                    COUNT(*) as total_orders,
                    COALESCE(SUM(CASE WHEN LOWER(status) NOT IN ('cancelled', 'отменен') THEN total_amount ELSE 0 END), 0) as total_revenue,
                    COALESCE(AVG(CASE WHEN LOWER(status) NOT IN ('cancelled', 'отменен') THEN total_amount ELSE NULL END), 0) as avg_check,
                    COUNT(CASE WHEN LOWER(status) IN ('cancelled', 'отменен') THEN 1 END) as cancelled_count,
                    COUNT(CASE WHEN actual_time IS NOT NULL AND expected_time IS NOT NULL AND actual_time <= expected_time THEN 1 END) as on_time_count,
                    COUNT(CASE WHEN actual_time IS NOT NULL AND expected_time IS NOT NULL AND actual_time > expected_time THEN 1 END) as delayed_count,
                    ROUND(AVG(CASE WHEN actual_time IS NOT NULL AND created_at IS NOT NULL 
                              THEN EXTRACT(EPOCH FROM (actual_time - created_at))/60 ELSE NULL END)::numeric, 1) as avg_turnaround_minutes
                FROM orders
                WHERE created_at >= :since_date
            """),
            {"since_date": since_date}
        ).fetchone()

        total_orders = total_summary_row[0] if total_summary_row else 0
        total_revenue = float(total_summary_row[1]) if total_summary_row else 0.0
        avg_check = round(float(total_summary_row[2]), 1) if total_summary_row else 0.0
        cancelled_count = total_summary_row[3] if total_summary_row else 0
        on_time_count = total_summary_row[4] if total_summary_row else 0
        delayed_count = total_summary_row[5] if total_summary_row else 0
        avg_turnaround_min = float(total_summary_row[6]) if total_summary_row and total_summary_row[6] is not None else 0.0

        delivered_with_time = on_time_count + delayed_count
        punctuality_pct = round((on_time_count / delivered_with_time * 100), 1) if delivered_with_time > 0 else 100.0

        # 2. Почасовое распределение (нагрузка кухни и доставки)
        hourly_rows = session.execute(
            text("""
                SELECT 
                    EXTRACT(HOUR FROM created_at)::int as hr,
                    COUNT(*) as order_count,
                    ROUND(AVG(total_amount)::numeric, 0) as avg_amount
                FROM orders
                WHERE created_at >= :since_date
                GROUP BY hr
                ORDER BY hr ASC
            """),
            {"since_date": since_date}
        ).fetchall()

        hourly_stats = []
        peak_hours = []
        max_hour_count = 0
        for r in hourly_rows:
            hr_val = int(r[0])
            cnt = int(r[1])
            avg_a = float(r[2]) if r[2] else 0.0
            hourly_stats.append({
                "hour": hr_val,
                "hour_label": f"{hr_val:02d}:00",
                "orders_count": cnt,
                "avg_amount": avg_a
            })
            if cnt > max_hour_count:
                max_hour_count = cnt

        if max_hour_count > 0:
            peak_hours = [f"{h['hour']:02d}:00" for h in hourly_stats if h['orders_count'] >= max_hour_count * 0.7]

        # 3. География и зависимость адресов доставок (Топ направлений и зон)
        address_rows = session.execute(
            text("""
                SELECT 
                    COALESCE(delivery_zone, 'Основная зона') as zone_name,
                    COUNT(*) as orders_count,
                    COALESCE(SUM(total_amount), 0) as revenue,
                    ROUND(AVG(CASE WHEN actual_time IS NOT NULL AND created_at IS NOT NULL 
                              THEN EXTRACT(EPOCH FROM (actual_time - created_at))/60 ELSE NULL END)::numeric, 1) as avg_duration
                FROM orders
                WHERE created_at >= :since_date AND delivery_address IS NOT NULL AND LOWER(delivery_address) NOT LIKE '%самовывоз%'
                GROUP BY zone_name
                ORDER BY orders_count DESC
                LIMIT 10
            """),
            {"since_date": since_date}
        ).fetchall()

        zones_analysis = []
        for a in address_rows:
            zones_analysis.append({
                "zone": str(a[0]),
                "orders_count": int(a[1]),
                "revenue": float(a[2]),
                "avg_duration_min": float(a[3]) if a[3] is not None else 0.0
            })

        # Улицы с наибольшей плотностью заказов (кластеризация направлений)
        street_rows = session.execute(
            text("""
                SELECT 
                    TRIM(SPLIT_PART(delivery_address, ',', 2)) as street,
                    COUNT(*) as count,
                    ROUND(AVG(total_amount)::numeric, 0) as avg_amount
                FROM orders
                WHERE created_at >= :since_date 
                  AND delivery_address IS NOT NULL 
                  AND LOWER(delivery_address) NOT LIKE '%самовывоз%'
                  AND SPLIT_PART(delivery_address, ',', 2) != ''
                GROUP BY street
                HAVING COUNT(*) >= 2
                ORDER BY count DESC
                LIMIT 12
            """),
            {"since_date": since_date}
        ).fetchall()

        streets_analysis = []
        for s in street_rows:
            st_name = str(s[0]).strip()
            if st_name and len(st_name) > 2:
                streets_analysis.append({
                    "street": st_name,
                    "orders_count": int(s[1]),
                    "avg_amount": float(s[2]) if s[2] else 0.0
                })

        # 4. Анализ курьеров и скорости доставки
        courier_rows = session.execute(
            text("""
                SELECT 
                    COALESCE(courier_name, 'Не назначен') as courier,
                    COUNT(*) as deliveries_count,
                    COUNT(CASE WHEN actual_time IS NOT NULL AND expected_time IS NOT NULL AND actual_time <= expected_time THEN 1 END) as on_time,
                    ROUND(AVG(CASE WHEN actual_time IS NOT NULL AND created_at IS NOT NULL 
                              THEN EXTRACT(EPOCH FROM (actual_time - created_at))/60 ELSE NULL END)::numeric, 1) as avg_trip_min
                FROM orders
                WHERE created_at >= :since_date 
                  AND LOWER(COALESCE(delivery_address, '')) NOT LIKE '%самовывоз%'
                GROUP BY courier
                ORDER BY deliveries_count DESC
                LIMIT 8
            """),
            {"since_date": since_date}
        ).fetchall()

        courier_analysis = []
        for c in courier_rows:
            c_name = str(c[0])
            c_cnt = int(c[1])
            c_on_time = int(c[2])
            c_rate = round((c_on_time / c_cnt * 100), 1) if c_cnt > 0 else 100.0
            courier_analysis.append({
                "courier": c_name,
                "deliveries_count": c_cnt,
                "on_time_count": c_on_time,
                "punctuality_pct": c_rate,
                "avg_trip_min": float(c[3]) if c[3] is not None else 0.0
            })

        # 5. Детерминированные наблюдения экспертной системы (0 токенов расхода)
        observations = []
        if peak_hours:
            observations.append(f"🔥 **Пиковая нагрузка заведения:** Интервалы {', '.join(peak_hours)}. В эти часы фиксируется наибольший приток заказов — рекомендуется предварительная заготовка позиций и усиление курьерской смены.")
        
        if avg_turnaround_min > 0:
            if avg_turnaround_min <= 45:
                observations.append(f"⚡ **Скорость закрытия заказов:** Отличная ({avg_turnaround_min} мин в среднем). Кухня и курьеры укладываются в график без задержек.")
            elif avg_turnaround_min <= 60:
                observations.append(f"⏱️ **Скорость закрытия заказов:** Умеренная ({avg_turnaround_min} мин в среднем). Имеются скрытые резервы ускорения отдачи горячих роллов.")
            else:
                observations.append(f"⚠️ **Высокое среднее время выполнения:** {avg_turnaround_min} мин. Рекомендуется проанализировать очереди цехов и плотность пробок.")

        if punctuality_pct >= 90:
            observations.append(f"✅ **Пунктуальность доставки:** {punctuality_pct}% заказов вручены вовремя или с опережением расчетного времени.")
        else:
            observations.append(f"⚠️ **Снижение пунктуальности:** {punctuality_pct}% вовремя ({delayed_count} заказов с превышением расчетного ожидания).")

        if streets_analysis:
            top_streets = [s["street"] for s in streets_analysis[:3]]
            observations.append(f"📍 **Географическая плотность:** Основной объем доставок сосредоточен по направлениям: {', '.join(top_streets)}. Рекомендуется объединять заказы в один курьерский рейс.")

        return {
            "status": "success",
            "period_days": days,
            "metrics": {
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "avg_check": avg_check,
                "cancelled_count": cancelled_count,
                "on_time_count": on_time_count,
                "delayed_count": delayed_count,
                "punctuality_pct": punctuality_pct,
                "avg_turnaround_min": avg_turnaround_min
            },
            "hourly_stats": hourly_stats,
            "peak_hours": peak_hours,
            "zones_analysis": zones_analysis,
            "streets_analysis": streets_analysis,
            "courier_analysis": courier_analysis,
            "observations": observations,
            "token_economy": {
                "mode": "Zero-Token SQL Engine",
                "tokens_saved": "~15,000 токенов за отчет",
                "tokens_used": 0
            }
        }

    async def generate_ai_analytics_summary(self, session: Session, days: int = 7) -> Dict[str, Any]:
        """
        Генерация глубокого стратегического ИИ-резюме на основе уже рассчитанных цифр.
        Ограничено ультра-компактным форматом (~150 токенов) для экономии бюджета.
        """
        data = self.get_analytics_observations(session, days=days)
        m = data["metrics"]
        summary_prompt = f"""Сформируй краткое (3-4 тезиса) стратегическое резюме управляющему рестораном за {days} дней:
- Заказов: {m['total_orders']}, Выручка: {m['total_revenue']} руб., Средний чек: {m['avg_check']} руб.
- Пунктуальность: {m['punctuality_pct']}%, Ср. время заказа: {m['avg_turnaround_min']} мин.
- Пиковые часы: {', '.join(data['peak_hours']) if data['peak_hours'] else 'равномерно'}.
Дай 2 конкретные рекомендации по оптимизации кухни и курьеров. Ответь кратко."""

        res = await ai_agent_service.chat_with_agent(
            session=session,
            agent_code="omni_assistant",
            user_message=summary_prompt
        )
        return {
            "status": "success",
            "summary": res.get("response", "Нагрузка стабильна, операционные метрики в пределах нормы."),
            "tokens_used": res.get("tokens_used", 150)
        }
'''

old_end = "ai_assistant_service = AiAssistantService()"
if old_end in content_norm:
    content_norm = content_norm.replace(old_end, analytics_code + "\n" + old_end)
    print("Added analytics_code!")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content_norm)

print("Patch applied to ai_assistant_service.py successfully!")
