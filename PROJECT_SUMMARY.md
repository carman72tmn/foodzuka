# FoodTech Project Summary (Статус проекта)

## Текущая задача: Синхронизация заказов iiko Cloud API

Мы реализовали расширенную синхронизацию текущих (активных) заказов, чтобы в админ-панели и в системе всегда была актуальная информация о статусах и составе чеков.

### Что уже сделано (02.03.2026):

1.  **Backend Services (`app/services/iiko_service.py`):**
    - Добавлен метод `get_active_orders`, который запрашивает в iiko заказы со статусами `New`, `CookingStarted`, `CookingCompleted`, `Waiting`, `OnWay`, `ReadyForCooking`.
2.  **Order Processing (`app/api/orders.py`):**
    - Расширен маппинг статусов iiko -> наше приложение.
    - Реализовано сохранение полного состава заказа (`items`) в JSON-поле `order_items_details`.
    - Добавлено сохранение данных о курьере, скидках и итоговой сумме.
    - Обновлен эндпоинт `/api/v1/orders/sync`, теперь он выгружает и историю за 24ч, и все активные заказы.
3.  **Сохранение проекта:**
    - Все изменения закоммичены и запушены в репозиторий в ветку `backup-local-config`.

### Текущее состояние Docker:

- `foodtech-backend`: Запущен, порт 8000. **Исправлено (переменные окружения добавлены)**.
- `foodtech-db`: Запущен (PostgreSQL 15), порт 5432.
- `foodtech-redis`: Запущен, порт 6379.
- `foodtech-admin`: Запущен (Vue/Vite), порт 8081.
- `foodtech-frontend`: Запущен, порт 5173.
- `foodtech-bot`: **Циклическая перезагрузка (Restarting)**. Ошибка `Token is invalid!`. Нужно прописать `BOT_TOKEN` в `bot/.env`.

### Блокер и План на следующую сессию:

При попытке тестирования через `docker compose exec backend` возникла ошибка валидации Pydantic Settings:
`SECRET_KEY`, `IIKO_API_LOGIN`, `IIKO_ORGANIZATION_ID` - Field required.

**Текущий статус (Обновлено):**

- **Backend / Скрипты**:
  - ✅ Переменные окружения (`backend/.env`) установлены. Контейнер запускается успешно.
  - ✅ Логика синхронизации заказов из iiko перенесена в отдельный сервис (`iiko_sync_service.py`).
  - ✅ Исправлены ошибки форматов iiko API (даты, статусы DeliveryStatus).
  - ✅ Верификационный скрипт (`verify_sync.py`) успешно стягивает данные из iiko (ошибки 400 и 422 устранены).
- **Bot**:
  - ⚠️ Отложено. Бот падает из-за неверного/отсутствующего `BOT_TOKEN`.
- **Frontend / Админка**:
  - ⏳ Ожидает проверки: Настройка отображения информации о составе заказов, сохраненной в формате JSON.

### Важные файлы для контекста:

- [iiko_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/iiko_service.py) - Логика запросов к iiko.
- [orders.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/orders.py) - Обработка и сохранение заказов.
- [task.md](file:///c:/Users/v_kva/.gemini/antigravity/brain/4451f982-0786-4050-8e02-181f44e2d49a/task.md) - Детальный список задач.
- [active_orders_implementation_plan.md](file:///c:/Users/v_kva/.gemini/antigravity/brain/4451f982-0786-4050-8e02-181f44e2d49a/active_orders_implementation_plan.md) - Принятый план реализации.
