# Log: loggemini_2026_10_02_shifts_cook_revenue
Дата: 2026-10-02
Задача: Выяснить, почему в админке по сменам не считает выручку по поварам в смену с момента выхода в смену и до закрытия (отображался 0), настроить корректный расчет выручки по поварам по цехам («Кухня» и «Горячий цех»), а также в отчетах для соцсетей по закрытию смен (`shift_close`).

## 1. Причина проблемы
1. В `iiko_sync_service.py` и `employees.py` выручка для не-курьеров рассчитывалась через сравнение `Order.admin_name == employee.name`. Повара (`Cook7`, `повар`, `кухня`) не являются администраторами заказов, поэтому `Order.admin_name` никогда с ними не совпадал, и выручка всегда выходила `0.0 ₽`.
2. При статусе смены `OPEN` выручка принудительно обнулялась (`if not date_close: revenue = 0.0`), поэтому в процессе открытой смены до ее закрытия значение также всегда было `0.0 ₽`.
3. Не существовало разделения выручки по производственным цехам («Кухня» и «Горячий цех»).

## 2. Внесенные изменения

### База данных (VPS & локально)
В таблицу `shifts` добавлены колонки:
```sql
ALTER TABLE shifts ADD COLUMN IF NOT EXISTS kitchen_revenue DOUBLE PRECISION;
ALTER TABLE shifts ADD COLUMN IF NOT EXISTS hot_revenue DOUBLE PRECISION;
```
Обновлена модель `Shift` в [employee.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/models/employee.py):
- `kitchen_revenue: Optional[float] = Field(default=0.0)`
- `hot_revenue: Optional[float] = Field(default=0.0)`

### Сервисный слой расчета смен
Создан модуль [shift_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/shift_service.py):
- `is_cook_employee(emp)`: определяет поваров по ролям (`Cook7`, `повар`, `кухня`, `горячий`, `шеф`, `cook`).
- `get_cook_kitchen_zones(session)`: сопоставляет зоны цехов:
  - Зона кухни (ID 2 «Кухня»)
  - Зона горячего цеха (ID 3 «Горячий цех»)
- `calculate_shift_metrics(session, shift, employee)`:
  - Находит все закрытые / доставленные заказы (`status in ['closed', 'delivered']`), оформленные в интервале от `date_open` до `date_close` (или до `datetime.now(timezone.utc)` для открытых смен).
  - Для каждой позиции заказа (`OrderItem`) определяет зону приготовления через `item.kitchen_zone_id`, `Product.kitchen_zone_id` или название блюда.
  - Умножает стоимость позиций на коэффициент скидки заказа (`total_with_discount / total_amount`), чтобы исключить скидки по акциям/промокодам и не учитывать соусы/пакеты кассы.
  - Рассчитывает: `kitchen_revenue`, `hot_revenue`, `total_revenue`, `deliveries_count`, `cancelled_orders_count`.
  - Для курьеров и администраторов сохранен их штатный раздельный алгоритм расчета (курьеры — по доставленным заказам курьера, администраторы — по заказам админа).

### Интеграция с синхронизацией iiko и отчетами соцсетей
1. [iiko_sync_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/iiko_sync_service.py):
   - При синхронизации смен iiko автоматически вызывается `calculate_shift_metrics`.
   - В `Shift` сохраняются `revenue_at_close`, `kitchen_revenue`, `hot_revenue`.
   - При отправке уведомления о закрытии смены (`_send_shift_vk_notification`) в шаблон и контекст передаются `kitchen_revenue` и `hot_revenue`.
2. [vk_notification_router.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/vk_notification_router.py):
   - Поддержаны теги: `{{shift.revenue_at_close}}`, `{{shift.kitchen_revenue}}`, `{{shift.hot_revenue}}`.
   - Добавлено локальное форматирование времени (Asia/Tyumen) и красивый вывод сумм в рублях (`X.XX ₽`).
3. [vk_bot_admin.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/vk_bot_admin.py):
   - Добавлены переменные `shift.kitchen_revenue` и `shift.hot_revenue` в подсказки конструктора шаблонов сообщений.

### Интерфейс админки и API
1. [employees.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/employees.py):
   - В эндпоинте `GET /api/v1/employees/shifts/all` для активных смен поваров ведется расчет выручки онлайн с момента открытия смены, а для закрытых — берутся сохраненные значения.
   - Добавлен сервисный эндпоинт `POST /api/v1/employees/shifts/recalculate-all` для пересчета исторических смен.
2. [employees.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/employees.vue):
   - В таблице смен добавлено отображение бейджей `🍳 Кухня: X ₽` и `🔥 Гор: Y ₽` для поваров.
   - В модальном окне сотрудника добавлена разбивка выручки по цехам.
   - Добавлена кнопка «Пересчитать выручку» (`bx-calculator`) для обновления данных смен в один клик.

## 3. Развертывание и верификация на VPS
1. Файлы выгружены на VPS в `/root/foodzuka/`.
2. Проведена сверка контрольных сумм MD5 между локальной копией и VPS:
   - `employee.py`: `7efcb6860cc6eabd6b9e2af942bd27e6` (совпадает)
   - `shift_service.py`: `add3e4a424d7f2552d5af8aac3792d7c` (совпадает)
   - `iiko_sync_service.py`: `d2b1548028c9b8490999bcc6b4e0e254` (совпадает)
   - `vk_notification_router.py`: `795a67b204daa6789fbab1996c637a2f` (совпадает)
   - `employees.py`: `9e53d7f4786325bffd81227137986b84` (совпадает)
   - `vk_bot_admin.py`: `a2cb42755bed7550919d40aee2380d9e` (совпадает)
   - `employees.vue`: `e588dd540745f7f5393a8270624b8bda` (совпадает)
3. Выполнена компиляция фронтенда админки `npm run build` на VPS:
   - Успешно собрано в `public/build/assets/employees-BtSakLt5.js` без ошибок.
4. Перезапущены контейнеры `backend` и `worker`.
5. Выполнен пересчет существующих смен в БД:
   - Успешно пересчитано смен: **700**.
6. Проверка данных реальных смен поваров:
   - Смена 933 (Повар Андрей, Cook7): Total: 15 552.72 ₽, Kitchen: 15 552.72 ₽, Hot: 0.00 ₽.
   - Смена 932 (Евгений, Cook7): Total: 31 698.20 ₽, Kitchen: 31 698.20 ₽, Hot: 0.00 ₽.
   - Смена 928 (Айсулу, Cook7): Total: 13 272.40 ₽, Kitchen: 12 882.40 ₽, Hot: 390.00 ₽.
   - Смены курьеров и администраторов продолжают считаться корректно по их заказам.
7. Обновлена проектная документация: `system_faq.md`, `sql_faq.md`, `sitenav.md`.
