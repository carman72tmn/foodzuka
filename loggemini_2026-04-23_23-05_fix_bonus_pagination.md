# Лог изменений: Исправление ошибки пагинации Bonus History

**Дата**: 23.04.2026
**Время**: 23:05
**Задача**: Исправление ошибки 400 Bad Request при запросе истории бонусов (отсутствие pageNumber и pageSize).

## Описание изменений
В файле `backend/app/services/iiko_service.py` в методе `get_customer_bonus_history` изменен процесс формирования полезной нагрузки (payload) для запроса к эндпоинту `/api/1/loyalty/iiko/customer/transactions/by_date`.

Добавлены обязательные параметры:
- `pageNumber`: 0
- `pageSize`: 100

## Список измененных файлов
- [iiko_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/iiko_service.py)
- [system_faq.md](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/system_faq.md)

## Синхронизация с VPS
1. Файл `iiko_service.py` выгружен на VPS по пути `/root/foodzuka/backend/app/services/iiko_service.py`.
2. Файл `system_faq.md` выгружен на VPS по пути `/root/foodzuka/system_faq.md`.
3. Выполнен перезапуск контейнера `foodtech-backend`.

## Верификация
- Логи бэкенда после перезапуска показывают успешный старт.
- Ошибка 400 в логах iiko API (Message: "The request is invalid.", ModelState: "Required property 'pageNumber' not found") должна быть устранена.
