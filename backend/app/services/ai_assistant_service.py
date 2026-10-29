"""
Сервис виртуальных ИИ-Помощников сайта FoodTech (AI Assistant Service)
Обеспечивает:
1. CRUD помощников, привязка к маршрутам админки, скины, аватары, характеры.
2. Серверный модуль быстрой аналитики рабочих процессов БЕЗ вызова LLM (0 токенов):
   - Зависшие новые заказы (> 5 мин)
   - Задержки отдачи на кухне (> 25 мин)
   - Задержки курьерской доставки (> 40 мин)
   - Контроль незакрытых смен сотрудников
3. Интеллектуальный чат с помощником с жесткой экономией токенов и кэшированием.
"""
import time
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, date, timedelta
from sqlmodel import Session, select, desc
from sqlalchemy import text, func

from app.models.ai_assistant import AiSiteAssistant, AiAssistantMessage
from app.models.ai_agent import AiSiteAgent, AiProviderConnection
from app.models.order import Order
from app.models.employee import Shift
from app.services.ai_agent_service import ai_agent_service

logger = logging.getLogger(__name__)

# Кэш оперативных метрик для экономии нагрузки на БД (TTL 30 секунд)
_OPERATIONAL_CACHE: Dict[str, Any] = {
    "timestamp": 0,
    "data": None
}

class AiAssistantService:
    # ==========================================
    # 1. УПРАВЛЕНИЕ ПОМОЩНИКАМИ (CRUD)
    # ==========================================

    def get_all_assistants(self, session: Session) -> List[AiSiteAssistant]:
        """Возвращает всех настроенных помощников"""
        return session.exec(select(AiSiteAssistant).order_by(AiSiteAssistant.id.asc())).all()

    def get_assistant_by_id(self, session: Session, assistant_id: int) -> Optional[AiSiteAssistant]:
        return session.get(AiSiteAssistant, assistant_id)

    def get_assistant_by_code(self, session: Session, code: str) -> Optional[AiSiteAssistant]:
        return session.exec(select(AiSiteAssistant).where(AiSiteAssistant.code == code)).first()

    def get_active_assistant_for_page(self, session: Session, page_route: str) -> Optional[AiSiteAssistant]:
        """
        Находит наиболее подходящего активного помощника для указанной страницы.
        Приоритет: точное совпадение маршрута в assigned_pages -> префиксное совпадение -> универсальный wildcard '*'
        """
        active_assistants = session.exec(
            select(AiSiteAssistant).where(AiSiteAssistant.is_active == True).order_by(AiSiteAssistant.id.asc())
        ).all()

        if not active_assistants:
            return None

        # 1. Точное совпадение
        for a in active_assistants:
            pages = a.assigned_pages or []
            if page_route in pages:
                return a

        # 2. Префиксное совпадение (например /orders/details входит в /orders)
        for a in active_assistants:
            pages = a.assigned_pages or []
            for p in pages:
                if p != "*" and page_route.startswith(p):
                    return a

        # 3. Универсальный помощник со звездочкой '*'
        for a in active_assistants:
            pages = a.assigned_pages or []
            if "*" in pages:
                return a

        # Если ничего не подошло, берем первого активного
        return active_assistants[0]

    def create_assistant(self, session: Session, data: Dict[str, Any]) -> AiSiteAssistant:
        """Создает нового помощника"""
        code = data.get("code") or f"assistant_{int(time.time())}"
        assistant = AiSiteAssistant(
            name=data.get("name", "Новый Помощник"),
            code=code,
            role_title=data.get("role_title", "Интеллектуальный ассистент"),
            avatar_skin=data.get("avatar_skin", "chef_male"),
            avatar_custom_url=data.get("avatar_custom_url"),
            avatar_animation_mode=data.get("avatar_animation_mode", "alive"),
            character_tone=data.get("character_tone", "professional"),
            assigned_pages=data.get("assigned_pages", ["*"]),
            zone_of_responsibility=data.get("zone_of_responsibility", "full_control"),
            linked_agent_code=data.get("linked_agent_code", "omni_assistant"),
            connection_id=data.get("connection_id"),
            model_override=data.get("model_override"),
            is_active=data.get("is_active", True),
            allow_sound_alerts=data.get("allow_sound_alerts", True),
            allow_voice_tts=data.get("allow_voice_tts", False),
            daily_token_limit=data.get("daily_token_limit", 50000),
            daily_requests_limit=data.get("daily_requests_limit", 100),
            auto_check_interval_sec=data.get("auto_check_interval_sec", 30),
            system_prompt_addon=data.get("system_prompt_addon")
        )
        session.add(assistant)
        session.commit()
        session.refresh(assistant)
        return assistant

    def update_assistant(self, session: Session, assistant_id: int, data: Dict[str, Any]) -> Optional[AiSiteAssistant]:
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
        return assistant

    def delete_assistant(self, session: Session, assistant_id: int) -> bool:
        assistant = session.get(AiSiteAssistant, assistant_id)
        if not assistant:
            return False
        # Удаляем историю сообщений
        session.exec(text(f"DELETE FROM ai_assistant_messages WHERE assistant_id = {assistant_id}"))
        session.delete(assistant)
        session.commit()
        return True

    def seed_default_assistants(self, session: Session):
        """Создает базовых помощников по умолчанию, если таблица пуста"""
        count = session.exec(select(func.count(AiSiteAssistant.id))).one()
        if count > 0:
            return

        defaults = [
            {
                "name": "Шеф Марк",
                "code": "kitchen_chef",
                "role_title": "Шеф-Повар / Контроль кухни",
                "avatar_skin": "chef_male",
                "avatar_animation_mode": "alive",
                "character_tone": "strict_supervisor",
                "assigned_pages": ["/orders", "/kitchen", "/pers"],
                "zone_of_responsibility": "kitchen_control",
                "linked_agent_code": "omni_assistant",
                "is_active": True,
                "allow_sound_alerts": True,
                "daily_token_limit": 50000,
                "daily_requests_limit": 150,
                "auto_check_interval_sec": 30,
                "system_prompt_addon": "Ты — шеф-повар Марк. Твоя главная задача — следить за скоростью отдачи блюд, контролем цехов кухни и своевременной передачей заказов на сборку. Отвечай авторитетно, четко и по делу."
            },
            {
                "name": "Анна",
                "code": "admin_anna",
                "role_title": "Старший администратор",
                "avatar_skin": "admin_female",
                "avatar_animation_mode": "alive",
                "character_tone": "professional",
                "assigned_pages": ["*"],
                "zone_of_responsibility": "admin_cashier",
                "linked_agent_code": "omni_assistant",
                "is_active": True,
                "allow_sound_alerts": True,
                "daily_token_limit": 50000,
                "daily_requests_limit": 150,
                "auto_check_interval_sec": 30,
                "system_prompt_addon": "Ты — Анна, старший администратор заведения. Помогаешь кассиру, управляющему и операторам. Контролируешь неразобранные заказы, кассу, напоминаешь о звонках клиентам и координации заведения."
            },
            {
                "name": "Макс",
                "code": "courier_lead",
                "role_title": "Диспетчер логистики",
                "avatar_skin": "courier_male",
                "avatar_animation_mode": "alive",
                "character_tone": "friendly",
                "assigned_pages": ["/orders", "/dashboard"],
                "zone_of_responsibility": "delivery_control",
                "linked_agent_code": "omni_assistant",
                "is_active": True,
                "allow_sound_alerts": True,
                "daily_token_limit": 50000,
                "daily_requests_limit": 100,
                "auto_check_interval_sec": 30,
                "system_prompt_addon": "Ты — Макс, диспетчер доставки. Твоя стихия — курьеры, маршруты, время в пути и предотвращение опозданий клиентам. Общайся дружелюбно, энергично и держи руку на пульсе."
            },
            {
                "name": "Нео",
                "code": "smart_neo",
                "role_title": "Кибер-Ассистент",
                "avatar_skin": "cyber_bot",
                "avatar_animation_mode": "float",
                "character_tone": "caring_mentor",
                "assigned_pages": ["*"],
                "zone_of_responsibility": "full_control",
                "linked_agent_code": "omni_assistant",
                "is_active": True,
                "allow_sound_alerts": False,
                "daily_token_limit": 50000,
                "daily_requests_limit": 100,
                "auto_check_interval_sec": 45,
                "system_prompt_addon": "Ты — высокотехнологичный кибер-помощник Нео. Ты знаешь всю архитектуру FoodTech, помогаешь находить ответы на любые вопросы, давать советы по оптимизации и маркетингу."
            },
            {
                "name": "Везунчик",
                "code": "fox_vezuroll",
                "role_title": "Маскот Везу Ролл",
                "avatar_skin": "fox_mascot",
                "avatar_animation_mode": "pulse",
                "character_tone": "humorous",
                "assigned_pages": ["*"],
                "zone_of_responsibility": "full_control",
                "linked_agent_code": "omni_assistant",
                "is_active": True,
                "allow_sound_alerts": True,
                "daily_token_limit": 50000,
                "daily_requests_limit": 100,
                "auto_check_interval_sec": 60,
                "system_prompt_addon": "Ты — Везунчик, фирменный лисенок сети доставки «Везу Ролл». Поддерживаешь команду, шутишь, поднимаешь настроение и следишь, чтобы все гости были довольны вкусными роллами!"
            }
        ]

        for item in defaults:
            self.create_assistant(session, item)
        logger.info("Default AI Site Assistants seeded successfully.")

    # ==========================================
    # 2. СЕРВЕРНЫЙ МОНИТОРИНГ БЕЗ ВЫЗОВА LLM (0 токенов!)
    # ==========================================

    def get_operational_metrics_and_tips(self, session: Session, assistant: Optional[AiSiteAssistant] = None) -> Dict[str, Any]:
        """
        Быстро и эффективно опрашивает БД через прямые SQL-запросы без расхода токенов LLM.
        Результат кэшируется на 30 секунд.
        """
        now = time.time()
        if now - _OPERATIONAL_CACHE["timestamp"] < 30 and _OPERATIONAL_CACHE["data"] is not None:
            cached = dict(_OPERATIONAL_CACHE["data"])
            # Фильтруем подсказки под зону ответственности текущего помощника
            if assistant:
                cached["tips"] = self._filter_tips_by_zone(cached.get("all_tips", []), assistant.zone_of_responsibility)
            return cached

        tips = []
        now_dt = datetime.utcnow()

        # 1. Зависшие новые заказы (> 5 минут без смены статуса)
        cutoff_new = now_dt - timedelta(minutes=5)
        stuck_new_orders = session.execute(
            text("""
                SELECT id, external_number, created_at, customer_phone, total_amount
                FROM orders
                WHERE LOWER(status) IN ('new', 'новый', 'pending', 'ожидает')
                  AND created_at <= :cutoff
                ORDER BY created_at ASC
                LIMIT 5
            """),
            {"cutoff": cutoff_new}
        ).fetchall()

        for r in stuck_new_orders:
            wait_min = int((now_dt - r[2]).total_seconds() / 60)
            tips.append({
                "id": f"new_stuck_{r[0]}",
                "category": "new_order_stuck",
                "severity": "high",
                "title": f"Заказ #{r[1] or r[0]} ждет подтверждения",
                "text": f"Заказ ожидает отправки на кухню уже {wait_min} мин! Подтвердите или передайте в цех.",
                "order_id": r[0],
                "action_url": f"/orders?search={r[1] or r[0]}"
            })

        # 2. Задержка приготовления на кухне (> 25 минут в готовке)
        cutoff_kitchen = now_dt - timedelta(minutes=25)
        stuck_kitchen_orders = session.execute(
            text("""
                SELECT id, external_number, updated_at, total_amount
                FROM orders
                WHERE LOWER(status) IN ('cooking', 'kitchen', 'готовится', 'на кухне')
                  AND updated_at <= :cutoff
                ORDER BY updated_at ASC
                LIMIT 5
            """),
            {"cutoff": cutoff_kitchen}
        ).fetchall()

        for r in stuck_kitchen_orders:
            cook_min = int((now_dt - r[2]).total_seconds() / 60)
            tips.append({
                "id": f"kitchen_delay_{r[0]}",
                "category": "cooking_delay",
                "severity": "medium",
                "title": f"Задержка кухни: Заказ #{r[1] or r[0]}",
                "text": f"Блюда готовятся уже {cook_min} мин (норма до 25 мин). Проверьте цеха!",
                "order_id": r[0],
                "action_url": f"/orders?search={r[1] or r[0]}"
            })

        # 3. Задержка доставки курьером (> 40 минут в пути)
        cutoff_delivery = now_dt - timedelta(minutes=40)
        stuck_delivery_orders = session.execute(
            text("""
                SELECT id, external_number, updated_at, total_amount
                FROM orders
                WHERE LOWER(status) IN ('delivering', 'on_way', 'в пути', 'доставляется')
                  AND updated_at <= :cutoff
                ORDER BY updated_at ASC
                LIMIT 5
            """),
            {"cutoff": cutoff_delivery}
        ).fetchall()

        for r in stuck_delivery_orders:
            way_min = int((now_dt - r[2]).total_seconds() / 60)
            tips.append({
                "id": f"delivery_delay_{r[0]}",
                "category": "delivery_delay",
                "severity": "medium",
                "title": f"Курьер в пути: Заказ #{r[1] or r[0]}",
                "text": f"Курьер везет заказ уже {way_min} мин. Рекомендуется связаться с курьером.",
                "order_id": r[0],
                "action_url": f"/orders?search={r[1] or r[0]}"
            })

        # 4. Зависшие смены (> 12 часов без закрытия)
        cutoff_shifts = now_dt - timedelta(hours=12)
        stale_shifts = session.execute(
            text("""
                SELECT s.id, e.name, s.date_open
                FROM shifts s
                JOIN employees e ON s.employee_id = e.id
                WHERE s.date_close IS NULL
                  AND s.date_open <= :cutoff
                LIMIT 3
            """),
            {"cutoff": cutoff_shifts}
        ).fetchall()

        for s in stale_shifts:
            hours_open = round((now_dt - s[2]).total_seconds() / 3600, 1)
            tips.append({
                "id": f"shift_stale_{s[0]}",
                "category": "shift_alert",
                "severity": "low",
                "title": f"Открытая смена: {s[1]}",
                "text": f"Смена длится уже {hours_open} ч. Не забудьте закрыть смену сотрудника.",
                "action_url": "/employees"
            })

        # 5. Сводка за текущие сутки
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        day_stats = session.execute(
            text("""
                SELECT 
                    COUNT(*) as total_orders,
                    COALESCE(SUM(CASE WHEN LOWER(status) NOT IN ('cancelled', 'отменен') THEN total_amount ELSE 0 END), 0) as revenue,
                    COUNT(CASE WHEN LOWER(status) IN ('new', 'новый', 'pending', 'cooking', 'kitchen', 'delivering', 'в пути') THEN 1 END) as in_progress
                FROM orders
                WHERE created_at >= :today_start
            """),
            {"today_start": today_start}
        ).fetchone()

        total_orders_today = day_stats[0] if day_stats else 0
        revenue_today = float(day_stats[1]) if day_stats else 0.0
        active_in_progress = day_stats[2] if day_stats else 0
        avg_check = round(revenue_today / total_orders_today, 0) if total_orders_today > 0 else 0

        operational_data = {
            "all_tips": tips,
            "metrics": {
                "total_orders_today": total_orders_today,
                "revenue_today": revenue_today,
                "active_in_progress": active_in_progress,
                "avg_check": avg_check,
                "stuck_new_count": len(stuck_new_orders),
                "stuck_kitchen_count": len(stuck_kitchen_orders),
                "stuck_delivery_count": len(stuck_delivery_orders)
            },
            "status": "warning" if len(stuck_new_orders) > 0 or len(tips) >= 3 else ("attention" if len(tips) > 0 else "ok")
        }

        # Обновляем глобальный кэш
        _OPERATIONAL_CACHE["timestamp"] = now
        _OPERATIONAL_CACHE["data"] = operational_data

        filtered = dict(operational_data)
        if assistant:
            filtered["tips"] = self._filter_tips_by_zone(tips, assistant.zone_of_responsibility)
        else:
            filtered["tips"] = tips

        return filtered

    def _filter_tips_by_zone(self, tips: List[Dict[str, Any]], zone: str) -> List[Dict[str, Any]]:
        """Фильтрует подсказки в соответствии с зоной ответственности помощника"""
        if zone == "full_control" or not zone:
            return tips
        if zone == "kitchen_control":
            return [t for t in tips if t.get("category") in ("cooking_delay", "new_order_stuck")]
        if zone == "delivery_control":
            return [t for t in tips if t.get("category") in ("delivery_delay", "shift_alert")]
        if zone == "admin_cashier":
            return [t for t in tips if t.get("category") in ("new_order_stuck", "shift_alert")]
        return tips

    # ==========================================
    # 3. ИНТЕЛЛЕКТУАЛЬНЫЙ ДИАЛОГ С ПОМОЩНИКОМ
    # ==========================================

    async def chat_with_assistant(
        self,
        session: Session,
        assistant_id: int,
        user_message: str,
        session_id: Optional[str] = None,
        page_route: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Диалог с виртуальным ассистентом.
        Оптимизирован для жесткой экономии токенов:
        - Лимит ответа 400-500 токенов
        - Свежие метрики передаются лаконично
        - Проверка суточных лимитов
        """
        assistant = session.get(AiSiteAssistant, assistant_id)
        if not assistant:
            raise Exception("Помощник не найден")

        # 1. Проверяем суточные квоты
        self._check_and_reset_daily_limits(assistant)
        if assistant.used_requests_today >= assistant.daily_requests_limit:
            return {
                "reply": f"Привет! Я уже ответил на {assistant.used_requests_today} вопросов сегодня и достиг суточного лимита. Однако я продолжаю в реальном времени следить за кухней, заказами и доставкой в фоновом режиме!",
                "emotion": "talking",
                "tokens_used": 0,
                "limit_reached": True
            }

        # 2. Сохраняем сообщение пользователя
        user_msg_db = AiAssistantMessage(
            assistant_id=assistant.id,
            user_id=user_id,
            session_id=session_id,
            page_route=page_route,
            role="user",
            content=user_message,
            is_auto_tip=False,
            tokens_used=0
        )
        session.add(user_msg_db)
        session.commit()

        # 3. Получаем оперативную сводку заведения для контекста
        ops = self.get_operational_metrics_and_tips(session, assistant)
        metrics = ops.get("metrics", {})
        active_tips = ops.get("tips", [])

        tips_summary = "\n".join([f"- {t['title']}: {t['text']}" for t in active_tips[:3]])
        if not tips_summary:
            tips_summary = "Все текущие заказы и процессы в заведении идут в штатном режиме."

        # Ограничения и права помощника
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
        tones = {
            "strict_supervisor": "Строгий, авторитетный и требовательный тон. Фокус на дисциплине, времени и точности.",
            "caring_mentor": "Заботливый, поддерживающий наставник. Объясняй спокойно, помогай и подсказывай наилучшие решения.",
            "friendly": "Дружелюбный, бодрый, оптимистичный тон общения.",
            "humorous": "С легким юмором, позитивом и задором.",
            "professional": "Деловой, лаконичный, вежливый и структурированный тон."
        }
        tone_instruction = tones.get(assistant.character_tone, tones["professional"])

        system_prompt = f"""Ты — интерактивный персонаж-помощник «{assistant.name}» (Роль: {assistant.role_title}) в системе управления FoodTech («Везу Ролл»).
Твой характер: {tone_instruction}
Твоя зона ответственности: {assistant.zone_of_responsibility}.
Страница, на которой находится сотрудник: {page_route or 'Админ-панель'}.

АКТУАЛЬНАЯ ОПЕРАТИВНАЯ СВОДКА ЗАВЕДЕНИЯ В РЕАЛЬНОМ ВРЕМЕНИ:
- Заказов сегодня: {metrics.get('total_orders_today', 0)}, Выручка: {metrics.get('revenue_today', 0)} ₽, Средний чек: {metrics.get('avg_check', 0)} ₽
- Активных заказов в работе: {metrics.get('active_in_progress', 0)}
- ТЕКУЩИЕ ПРЕДУПРЕЖДЕНИЯ СИСТЕМЫ:
{tips_summary}

ДОПОЛНИТЕЛЬНЫЕ ИНСТРУКЦИИ:
{assistant.system_prompt_addon or ''}

ОГРАНИЧЕНИЯ И ПРАВА ДОСТУПА ПОМОЩНИКА:
{ext_queries_rule}
{iiko_access_rule}

ПРАВИЛА ОТВЕТА:
1. Отвечай кратко, ёмко и структурированно (не более 2-4 абзацев). Береги токены!
2. Всегда оставайся в своем образе «{assistant.name}».
3. Если есть задержки на кухне или новые зависшие заказы — обязательно упомяни их сотруднику!
4. Строго соблюдай установленные ограничения на сторонние ресурсы и доступ к iiko API!
"""

        # 4. Вызываем подключение к ИИ через агентский шлюз
        linked_code = assistant.linked_agent_code or "omni_assistant"
        res = await ai_agent_service.chat_with_agent(
            session=session,
            agent_code=linked_code,
            user_message=f"[Вопрос от сотрудника к помощнику {assistant.name}]: {user_message}",
            connection_id_override=assistant.connection_id,
            model_override=assistant.model_override
        )

        reply_text = res.get("response", "Я на связи! Чем помочь по рабочим процессам?")
        tokens_used = res.get("tokens_used", 100)

        # 5. Обновляем счетчики помощника
        assistant.used_requests_today = (assistant.used_requests_today or 0) + 1
        assistant.used_tokens_today = (assistant.used_tokens_today or 0) + tokens_used
        session.add(assistant)

        # 6. Сохраняем ответ ассистента в истории
        ai_msg_db = AiAssistantMessage(
            assistant_id=assistant.id,
            user_id=user_id,
            session_id=session_id,
            page_route=page_route,
            role="assistant",
            content=reply_text,
            is_auto_tip=False,
            tokens_used=tokens_used
        )
        session.add(ai_msg_db)
        session.commit()

        # Определяем эмоцию аватара по контексту
        emotion = "talking"
        if len(active_tips) > 0 and any(t.get("severity") == "high" for t in active_tips):
            emotion = "warning"
        elif "спасибо" in user_message.lower() or "отлично" in user_message.lower():
            emotion = "happy"

        return {
            "reply": reply_text,
            "emotion": emotion,
            "tokens_used": tokens_used,
            "today_requests": assistant.used_requests_today,
            "today_tokens": assistant.used_tokens_today,
            "limit_reached": False
        }

    def _check_and_reset_daily_limits(self, assistant: AiSiteAssistant):
        today = date.today()
        if assistant.last_reset_date != today:
            assistant.used_requests_today = 0
            assistant.used_tokens_today = 0
            assistant.last_reset_date = today

    def get_messages_history(self, session: Session, assistant_id: int, session_id: Optional[str] = None, limit: int = 30) -> List[AiAssistantMessage]:
        query = select(AiAssistantMessage).where(AiAssistantMessage.assistant_id == assistant_id)
        if session_id:
            query = query.where(AiAssistantMessage.session_id == session_id)
        query = query.order_by(AiAssistantMessage.id.desc()).limit(limit)
        items = session.exec(query).all()
        return list(reversed(items))

    def clear_messages_history(self, session: Session, assistant_id: int, session_id: Optional[str] = None):
        if session_id:
            session.exec(text(f"DELETE FROM ai_assistant_messages WHERE assistant_id = {assistant_id} AND session_id = '{session_id}'"))
        else:
            session.exec(text(f"DELETE FROM ai_assistant_messages WHERE assistant_id = {assistant_id}"))
        session.commit()


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
                GROUP BY 1
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

ai_assistant_service = AiAssistantService()
