# Лог сессии: Исправление статусов оплаты и банковских операций строго по данным iiko

**Дата и время**: 15.10.2026 21:30  
**Сессия**: e870ff52-0791-405f-bda7-366bd8a742f5  
**Задача**: Анализ и исправление проблемы ошибочных обновлений статусов оплаты в заказах и преждевременного отображения банковских поступлений в админ-панели (vezuroll.ru/admin). Обеспечение принципа: информация об оплате заказов берется СТРОГО из iiko, а в банковских операциях отображаются только реальные подтвержденные оплаты.

---

### 1. Первопричины проблемы (Root Causes)

1. **Ложноположительное определение оплаты в фоновом сервисе синхронизации iiko (`iiko_sync_service.py`)**:
   - В методе `process_iiko_order` (строка 1753) флаг `is_processed` вычислялся с условием:
     `(pk in ["online", "external"] and not is_courier_payment)`.
   - Любой заказ, поступающий с сайта или из мобильного приложения со способом «1. Оплата Картой T Bank» (в iiko категория `External`), сразу при создании получал `is_processed = True`, даже если платеж еще не был совершен клиентом (`isProcessedExternally == False`, `isPrepay == False`, `processedPaymentsSum == 0.0`).
   - В результате заказ в CRM мгновенно получал `total_paid = sum`, `left_to_pay = 0.00`, `is_paid = True` («Оплачен полностью») еще до реальной оплаты.

2. **Преждевременное добавление заказов в монитор банковских операций (`backend/app/api/bank.py`)**:
   - В эндпоинте `get_bank_payments` блок заказов iiko добавлял абсолютно все заказы с методом «Наличные» (`cash_{order.id}`) и «Перевод» (`tr_{order.id}`) со статусом `matched` и флагом `is_real = True` независимо от того, был ли заказ оплачен или закрыт.
   - Также заказы с онлайн-оплатой попадали в список из-за того, что `order.total_paid` был ошибочно > 0.
   - В итоге оператор видел в мониторе оплат запись «Оплата прошла», хотя деньги еще не были получены.

3. **Ошибочные WebSocket-уведомления о банковских платежах (`iiko_sync_service.py`)**:
   - В строках 2442–2454 при синхронизации каждого безналичного заказа отправлялось WebSocket-событие `new_bank_payment`, вызывавшее звуковой сигнал и баннер «Поступление оплаты!» в админке даже для неоплаченных заказов.

4. **Автономная мутация статуса оплаты заказов (`order.is_paid = True`) из банковских сопоставлений**:
   - В фоновой Celery-задаче `sync_tbank_operations_task` (`tbank_tasks.py`), вебхуке движения по счетам `handle_account_info_webhook` (`tbank_webhooks.py`), и эндпоинтах `auto_match_all_payments` / `manual_match_payment` (`bank.py`) алгоритм `find_best_matching_order` угадывал заказы по совпадению суммы (+/- 3 часа) и вызывал `process_order_payment`.
   - Это приводило к тому, что при любой оплате на терминале или поступлении на счет совершенно посторонний неоплаченный заказ с аналогичной суммой помечался как `is_paid = True`, минуя iiko.

---

### 2. План исправлений

1. **В `backend/app/services/iiko_sync_service.py`**:
   - Устранить условие `(pk in ["online", "external"] and not is_courier_payment)`.
   - Оплата считается проведенной (`is_processed = True`) СТРОГО при:
     `is_processed_externally == True`, либо `is_prepay == True`, либо `status_payment in ["processed", "closed", "success"]`, либо если заказ закрыт в iiko (`raw_status_lower == "closed"`).
   - Учитывать официальное поле iiko `processedPaymentsSum`.
   - Запретить отправку WebSocket-событий `new_bank_payment` для неоплаченных заказов.
   - Расширить временное окно сопоставления с выписками Т-Банка с учетом времени закрытия заказа (`order.updated_at` / `actual_time`).

2. **В `backend/app/api/bank.py`**:
   - В `get_bank_payments` отображать заказы iiko (наличные, переводы, карты) как совершенные оплаты СТРОГО только если заказ РЕАЛЬНО оплачен в iiko (`order.is_paid == True` или `order.status == OrderStatus.closed`).
   - В `manual_match_payment` и `auto_match_all_payments` только привязывать банковскую проводку (`stmt.matched_order_id = order.id`), НЕ изменяя статус оплаты самого заказа (статус заказа берется строго из iiko).

3. **В `backend/app/tasks/tbank_tasks.py`, `backend/app/api/tbank.py`, `backend/app/api/tbank_webhooks.py`**:
   - Исключить мутацию `order.is_paid` из авто-сопоставлений выписок (`find_best_matching_order`).
   - Привязывать транзакции в `tbank_statements`, но оставлять `Order.is_paid` в ведении iiko.

---

### 3. Результаты выполнения и верификации

1. **Кодировка и целостность**:
   - Файл `backend/app/services/iiko_sync_service.py` сохранен строго в кодировке **UTF-8**.
   - Во всех 5 файлах сохранены существующие комментарии и функции.

2. **Синхронизация с VPS (`ssh vezuroll`)**:
   - Все файлы скопированы на сервер в `/root/foodzuka/`.
   - Проведена сверка контрольных сумм (MD5):
     - `backend/app/services/iiko_sync_service.py`: `558EA194BA08BDE87B67D64782D11F4F` (Match: True)
     - `backend/app/api/bank.py`: `0687B83228872AACB3C1F24F1B7C41BD` (Match: True)
     - `backend/app/tasks/tbank_tasks.py`: `06B29A7B26C905B19FF6EE672A52A285` (Match: True)
     - `backend/app/api/tbank.py`: `7667CC937B45A3C0792B5D5DC9C5358B` (Match: True)
     - `backend/app/api/tbank_webhooks.py`: `F7C3581CC78FE0F6661F6A5A6AE99598` (Match: True)

3. **Боевое тестирование внутри Docker-контейнера `foodtech-backend`**:
   - Скрипт верификации проверил 15 последних заказов в БД:
     - Активный заказ в готовке #76932 (`OrderStatus.cooking`) имеет `is_paid = False`, `total_paid = 0.00`.
     - Заказ #76931 (`OrderStatus.closed`) имеет `is_paid = True`, `total_paid = 1210.00`.
   - Тест функции `get_bank_payments`:
     - Из 24 поступлений за сегодня все 22 сопоставленных заказа — это исключительно подтвержденные закрытые заказы iiko (`status = OrderStatus.closed`, `is_paid = True`).
     - Ни один незакрытый или неоплаченный заказ не попал в категорию `matched`.
   - Симуляции логики оплат в `iiko_sync_service`:
     - Неоплаченный онлайн заказ -> `total_paid = 0.0`, `is_paid = False` (PASS: True).
     - Оплаченный онлайн заказ (`isProcessedExternally = True`) -> `total_paid = 1500.0`, `is_paid = True` (PASS: True).
     - Закрытый заказ в кассе iiko -> `total_paid = 1200.0`, `is_paid = True` (PASS: True).

4. **Перезапуск сервисов**:
   - Контейнеры `foodtech-backend` и `foodtech-worker` перезапущены.
   - Celery worker готов к работе (`celery@55c70599e2cd ready.`).
   - Бэкенд штатно обрабатывает запросы (200 OK) и обслуживает вебсокет-соединения с админкой.

