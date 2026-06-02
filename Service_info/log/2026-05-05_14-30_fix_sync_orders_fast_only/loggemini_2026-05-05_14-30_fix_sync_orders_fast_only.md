# Лог задачи: Исправление ошибки sync_orders(fast_only)
Дата: 2026-05-05 14:30

## Проблема
В разделе "Курьеры" возникала ошибка `IikoSyncService.sync_orders() got an unexpected keyword argument 'fast_only'`.

## Выполненные действия
1. Изучен файл `backend/app/api/courier.py`, найден вызов `await sync_service.sync_orders(db, fast_only=True)`.
2. Изучен файл `backend/app/services/iiko_sync_service.py`, обнаружено отсутствие параметров `fast_only` и `skip_revision` в методе `sync_orders`.
3. Обновлена сигнатура метода `sync_orders` в `iiko_sync_service.py`:
   - Добавлены `fast_only: bool = False` и `skip_revision: bool = False`.
   - Реализована логика быстрого возврата при `fast_only=True` после синхронизации по ревизиям.
   - Реализовано уменьшение интервала опроса до 4 часов при `fast_only=True`.
4. Очищена избыточная логика получения настроек внутри `try` блока.

## Файлы
- `backend/app/services/iiko_sync_service.py` (изменен)
- `Service_info/system_faq.md` (будет обновлен)

## Статус
Правки внесены локально. Готовность к выгрузке на VPS.
