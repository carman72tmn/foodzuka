# Лог задачи: Подключение API Groq, Cerebras, Nvidia, GitHub Models с лимитами и сбросом
Дата: 2026-10-27 19:25

## Цель задачи
1. Добавить возможность подключения новых провайдеров ИИ:
   - Groq (https://console.groq.com/docs/overview) с загрузкой и выбором моделей, лимитов по тарифам и времени сброса (reset time).
   - Cerebras (https://inference-docs.cerebras.ai/) с загрузкой моделей, лимитов и времени сброса.
   - Nvidia NIM / Build (https://build.nvidia.com/) с загрузкой моделей, квот/кредитов и статуса обновления.
   - GitHub Models (https://models.inference.ai.azure.com) с PAT-токенами, выбором моделей, лимитами RPM/RPD и временем сброса.
2. Отображение доступных лимитов (RPM, RPD, TPM, остаток запросов) и времени обновления квот (например: "через 4м 12с" / "каждые сутки в 00:00 UTC"). Если лимит не обновляется автоматически — отображать строго `n/a`.
3. Поддержка выбора моделей как из списка по умолчанию, так и через динамическую подгрузку из API провайдеров по кнопке "Загрузить список из API".
4. Возможность использования данных провайдеров во всех агентах сайта и в интерактивной песочнице.


## Выполненные изменения

1. **Сервис ИИ (`backend/app/services/ai_agent_service.py`)**:
   - В `SYSTEM_QUOTA_PRESETS` добавлены подробные тарифные планы:
     - `groq`: Free Tier (30 RPM, 6k TPM, 14.4k RPD, суточный сброс в 00:00 UTC), Pay-as-you-go (1000 RPM, 300k TPM).
     - `cerebras`: Developer Free (30 RPM, 60k TPM, 14.4k RPD, 00:00 UTC), Enterprise (300 RPM).
     - `nvidia`: Free 1000 Credits (`eval`, 40 RPM, `reset_interval: none` -> строго `n/a`), Enterprise Cloud (`monthly`).
     - `github_models`: Free Tier PAT (15 RPM, 150 RPD, 8k TPM, `daily_utc`), Copilot Enterprise (60 RPM).
   - Добавлен реестр базовых адресов `DEFAULT_BASE_URLS`:
     - Groq: `https://api.groq.com/openai/v1`
     - Cerebras: `https://api.cerebras.ai/v1`
     - NVIDIA NIM: `https://integrate.api.nvidia.com/v1`
     - GitHub Models: `https://models.inference.ai.azure.com`
   - Реализована функция `calculate_limits_reset`:
     - Определяет оставшееся время до сброса лимитов.
     - Если провайдер вернул заголовок `x-ratelimit-reset-*`, парсит секунды или интервалы (`через 45с`, `через 1м 20с`).
     - Для суточных тарифов вычисляет оставшиеся часы и минуты до 00:00 UTC (`через Xч Yм (00:00 UTC)`).
     - Для невозобновляемых квот (Nvidia Free Credits, кастомные токены) возвращает строго `n/a`.
   - В `fetch_available_models` добавлена динамическая подгрузка моделей для Groq, Cerebras, NVIDIA и GitHub Models из их официальных эндпоинтов `/models`.
   - В `generate_completion` подключена обработка провайдеров `groq`, `cerebras`, `nvidia`, `github_models` с захватом заголовков Rate Limit и сохранением фактических данных в `extra_config.live_rate_limits`.

2. **API (`backend/app/api/ai_agents.py`)**:
   - В `GET /connections` добавлены поля `limits_reset_display` (время сброса или `n/a`), `is_reset_renewable` (True/False) и `live_rate_limits`.
   - При создании/обновлении подключений автоматически проставляется дефолтный `base_url`.
   - `GET /quota-presets` отдает клиенту свежие тарифные планы.

3. **Интерфейс Vue (`admin/resources/js/pages/settings/ai-agents.vue`)**:
   - Во вкладке «Мировые ИИ» добавлены цветные кнопки быстрого добавления: `+ Groq`, `+ Cerebras`, `+ NVIDIA NIM`, `+ GitHub Models`.
   - В карточках провайдеров отображаются:
     - Бейдж и фирменная иконка провайдера.
     - Лимиты тарифа (RPM, RPD).
     - Блок «Сброс лимитов» с бейджем времени (`через ...`) или `n/a`.
     - Счетчик и остаток запросов за текущий день.
   - В модальном окне:
     - Выбор типа провайдера из расширенного списка.
     - Динамические подсказки по получению API-ключей для каждого сервиса.
     - Подгрузка моделей из API кнопкой «Запросить доступные модели через API».
     - Предварительный просмотр периода сброса лимитов.
