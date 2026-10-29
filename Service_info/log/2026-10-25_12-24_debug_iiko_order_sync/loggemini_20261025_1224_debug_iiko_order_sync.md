# Лог расследования: почему в админку не приходят заказы из iiko
Дата: 2026-10-25 12:24

## 1. Симптомы проблемы
- Заказы из iiko перестали отображаться в панели администратора (vezuroll.ru/admin).
- В таблице `orders` последним отображался заказ №77145 от 05:24, после чего новые заказы не сохранялись.

## 2. Диагностика на VPS
- Проверено состояние Docker-контейнеров: все контейнеры (`foodtech-backend`, `foodtech-worker`, `foodtech-admin` и др.) работали.
- Проверена таблица `iiko_webhook_events`: входящие вебхуки от iiko Cloud API (`DeliveryOrderUpdate`) регулярно поступали на эндпоинт `/api/v1/webhooks/iiko`.
- При вызове обработки вебхуков и плановой синхронизации заказов (`process_iiko_order` / `sync_order_by_id`) на сервере возникала критическая ошибка:
  ```text
  CRITICAL Error processing order ...: cannot access local variable 'order' where it is not associated with a value
  Traceback (most recent call last):
    File "/app/app/services/iiko_sync_service.py", line 1819, in process_iiko_order
      if not is_paid and order and getattr(order, 'is_paid', False) and mapped_status in (OrderStatus.delivering, OrderStatus.delivered):
                         ^^^^^
  UnboundLocalError: cannot access local variable 'order' where it is not associated with a value
  ```

## 3. Причина ошибки
В методе `process_iiko_order` файла `iiko_sync_service.py` на строке 1819 была добавлена проверка:
```python
if not is_paid and order and getattr(order, 'is_paid', False) and mapped_status in (OrderStatus.delivering, OrderStatus.delivered):
    is_paid = True
    left_to_pay = Decimal('0.00')
    logger.info(f"Order {order_id_iiko}: Retaining local courier paid status")
```
Эта проверка обращалась к переменной `order` до блока `# 8. Сохранение` (строка 1918), где `order` фактически загружается из БД или создается (`order = await asyncio.to_thread(_get_order)`).
Так как `order` является локальной переменной функции, в Python обращение к ней до присваивания вызывало фатальное исключение `UnboundLocalError` при обработке любого нового или обновляемого заказа. В результате транзакция прерывалась и заказ не сохранялся в базе данных.

## 4. Внесенные исправления
1. В файле `backend/app/services/iiko_sync_service.py` (локально и в scratch):
   - Ошибочный блок проверки локального статуса оплаты курьером удален со строки 1819.
   - Проверка перенесена в блок финального назначения параметров заказа (после строки получения/создания `order`, перед сохранением флага `order.is_paid`).
   - Файл сохранен строго в кодировке UTF-8 с сохранением всей кириллицы.
2. Проведена верификация AST и таблицы символов Python (`find_order_usages.py`): обращений к `order` до присваивания нет (`Usages before assign: []`).
3. Файл выгружен на VPS (`/root/foodzuka/backend/app/services/iiko_sync_service.py`).
4. Проведена сверка контрольной суммы SHA256: хеши локального файла и файла на VPS полностью совпали (`afa28a2360d3caf21b77efccf983496629b332141cdc714e454ad9c7a39b1ee0`).
5. Перезапущены контейнеры `backend` и `worker`.

## 5. Тестирование
- Запущен скрипт тестовой синхронизации `sync_orders` на VPS.
- Зависшие заказы №77146 (`ready`) и №77147 (`cooking`) успешно обработаны, созданы и записаны в таблицу `orders`.
- Сработали веб-пуш уведомления и уведомления по смене статусов.
- Заказы отображаются в админке.
