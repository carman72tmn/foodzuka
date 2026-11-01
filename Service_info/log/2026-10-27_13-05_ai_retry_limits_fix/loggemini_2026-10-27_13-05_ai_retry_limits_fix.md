# Лог сессии разработки: Решение ошибки Gemini 503, retry/fallback и системные лимиты
Дата: 27.10.2026 13:05 (UTC+5)
Ветка: ai_agents_admin_settings

## 1. Проблема
- При отправке запроса в чат к агенту аналитики возникала ошибка:
  `Gemini API Error (503): {"error": {"code": 503, "message": "This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.", "status": "UNAVAILABLE"}}`
- При этом бэкенд выбрасывал необработанное исключение HTTPException(500), чат ломался в красную плашку.
- Лимиты запросов и токенов имели условные значения (1000 запросов / 1M токенов) без привязки к официальным спецификациям тарифов Google Gemini, OpenAI, GigaChat.

## 2. Анализ и причины
1. Ошибка 503 Service Unavailable на стороне Google Generative Language API вызвана перегрузкой дата-центров Google при обращении к новейшим моделям (`gemini-3.8-flash`, `gemini-flash-latest`). Это временный пик нагрузки в Google.
2. Тестирование показало, что облегченная модель `gemini-3.1-flash-lite` и `gemini-3.5-flash-lite` отвечают мгновенно (HTTP 200) со стабильным пингом и не подвержены 503.
3. Отсутствовал механизм экспоненциального повтора (retry) и фоллбэка на стабильную модель.

## 3. Выполненные доработки
1. **Бэкенд (`backend/app/services/ai_agent_service.py`)**:
   - Внедрена таблица официальных системных тарифов `SYSTEM_QUOTA_PRESETS`:
     - Google Gemini Free: 15 RPM, 1 500 RPD, 1 000 000 TPM.
     - Google Gemini Pay-as-you-go: 1 000 RPM, 4 000 000 TPM.
     - OpenAI: Tier 1 (500 RPM, 10 000 RPD).
     - Сбер GigaChat: 60 RPM, пакет 1 млн токенов.
   - Метод `generate_completion` дополнен автоповторами (до 2 попыток с задержкой 1.2–2.4 с при 503/429) и автоматическим fallback на стабильные модели (`gemini-3.1-flash-lite`, `gemini-3.5-flash-lite`, `gemini-flash-latest`).
   - `chat_with_agent` дополнен обработкой непредвиденных сбоев — вместо падения 500 чат сохраняет вежливое объяснение от ассистента с рекомендациями по смене модели.
2. **API (`backend/app/api/ai_agents.py`)**:
   - Добавлен эндпоинт `/api/v1/ai-agents/quota-presets` для получения официальных тарифов.
   - Эндпоинты `/connections` и `/quota-summary` возвращают подробные данные о тарифе (`tier_title`, `rpm_limit`, остаток лимитов).
3. **Frontend (`admin/resources/js/pages/settings/ai-agents.vue` и `admin/resources/js/pages/ai-agents/index.vue`)**:
   - В настройках подключения добавлен селект тарифа с автозаполнением системных лимитов и описанием спецификации.
   - В чате шкала лимитов динамически привязана к выбранному ИИ с индикатором RPM и названием тарифа.
   - Добавлен умный выпадающий список `VCombobox` с рекомендуемыми стабильными моделями.
   - Добавлена плашка авто-переключения модели (`fallback_note`).

## 4. Тестирование на сервере
- Выполнен запрос от агента `stats_analyst` к реальной БД (выручка OLAP, чеки, заказы).
- Модель `gemini-3.1-flash-lite` отработала за 3.4 сек, вернув полный структурированный отчет и обновив квоту (запросы 3/1500, токены 3945/1000000).
- Все контейнеры запущены и стабильны.
