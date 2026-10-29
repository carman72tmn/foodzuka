# Лог задачи: Доработка истории статусов заказа в карточке заказа

- **Дата и время начала:** 2026-09-16 16:20 (UTC+5)
- **Дата и время завершения:** 2026-09-16 16:35 (UTC+5)
- **Цель:**
  1. Отображать полную цепочку статусов (начиная от принятия заказа, затем подтверждение, готовка, доставка, закрытие).
  2. Отображать точное время смены статуса согласно часовому поясу из настроек админки.
  3. Отображать время между сменой статусов (длительность пребывания в каждом статусе).
  4. Останавливать учет времени только при статусе «Закрыт» или «Отменен».
  5. Гарантированно сохранять историю статусов и рассчитанные длительности в БД (orders.status_history).

## Затронутые компоненты и файлы:
- ackend/app/services/order_status_history_service.py [NEW] — Единый сервис фиксации переходов, расчета длительностей, форматирования строк времени и учета таймзон заведения.
- ackend/app/services/iiko_sync_service.py [MODIFY] — Фиксация исходного статуса «Заказ принят» при создании и фиксация каждого изменения mapped_status из iikoCloud.
- ackend/app/api/orders.py [MODIFY] — Добавление истории при создании через REST API, при подтверждении заказа, отмене (cancelled) и закрытии (closed).
- ackend/app/api/kitchen.py [MODIFY] — Добавление истории при смене кухонных статусов (cooking, assembling, ready).
- ackend/app/api/courier.py [MODIFY] — Добавление истории при работе курьера (delivering, delivered, closed).
- dmin/resources/js/components/OrderDetailModal.vue [MODIFY] — Нормализация цепочки статусов, автообновление таймера активного статуса каждые 10 сек, корректный расчет длительности, фиксация общего времени при закрытии/отмене.
- dmin/resources/js/utils/date.js [MODIFY] — Функция ormatStatusTime(val, showSeconds) с поддержкой таймзоны админки.

## Сверка файлов между локальной средой и VPS:
- Все файлы выгружены на сервер по SSH (ssh vezuroll).
- Сверка контрольных сумм MD5:
  - ackend/app/services/order_status_history_service.py: 5506a72e796061148496ae9ca3ca11d2 (OK)
  - ackend/app/services/iiko_sync_service.py: 84618e7e1c8b3233ef14400cfbe34766 (OK)
  - ackend/app/api/orders.py: e758df634f19b16ff36a2ce08ee66d33 (OK)
  - ackend/app/api/kitchen.py: dcbe202e86bfda9ee6c527e025539ab1 (OK)
  - ackend/app/api/courier.py: 2ad661ee2d39aa47547b744a56c421f1 (OK)
  - dmin/resources/js/components/OrderDetailModal.vue: f61fc37f14b216fb932ff46dbf73fbf5 (OK)
  - dmin/resources/js/utils/date.js: 47f9fecdc55a80f1e8e52dbb06d4e286 (OK)

## Перезапуск и сборка:
- Перезапущены контейнеры oodtech-backend и oodtech-worker на VPS.
- В каталоге /root/foodzuka/admin выполнена сборка фронтенда: 
pm run build (успешно, сгенерирован чанк OrderDetailModal-2zi0-FKh.js).

## Тестирование:
- Протестирован бэкенд-сервис order_status_history_service:
  - Рассчитаны переходы ccepted -> confirmed (5м) -> cooking (15м) -> 
eady (10м) -> delivering (20м) -> delivered (5м) -> closed (фиксация общего времени 55м).
- Проверена корректность вывода времени по часовому поясу клиента/админки.

## Документация:
- Обновлены Service_info/sql_faq.md, Service_info/sitenav.md, Service_info/system_faq.md.
