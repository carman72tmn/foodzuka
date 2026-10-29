# Лог задачи: Обязательное условие «Время кухни задано (>0 мин)» для всех логистических цепочек курьера

**Дата и время**: 04.09.2026 19:55  
**Сессия**: require_cooking_time_set_all_chains  
**Исполнитель**: Antigravity AI Assistant  

---

## 1. Исходный запрос
Пользователь запросил:
> «и в логической цепочке для уведомлений , нужно добавить для всех цепочек одно условие : было установлено время приготовления (кухня) , т.е активировать отправку уведомления только после установления времени кухни.»

---

## 2. Анализ ситуации
1. Ранее в базе данных (`vk_templates`) флаг `require_cooking_time_set: true` был прописан только для шаблона 39 (`order_new`) и 48 (`change_cooking_time`).
2. У остальных курьерских событий (`order_status_update`, `order_amount_changed`, `order_items_changed`, `order_time_changed`, `order_address_changed`, `order_cancelled`, `courier_assigned`) флаг либо отсутствовал, либо был `false`.
3. В `vk_notification_router.py` проверка условий цепочки `chain_config` для некоторых событий происходила до полного разрешения контекста заказа и времени готовности кухни, а для ряда событий проверка `require_cooking_time_set` не выполнялась.
4. В результате, если по заказу происходили изменения (например, смена статуса или суммы) до того, как повар/оператор кухни выставил ориентировочное время готовки блюда, курьер мог получать уведомления преждевременно.

---

## 3. Выполненные изменения

### А. Бэкенд (`backend/app/services/vk_notification_router.py`)
1. **Реорганизация логики валидации заказа и времени кухни**:
   - Перенесены вверх (до анализа `chain_config`) вызовы разрешения заказа (`order_for_check`), курьера (`get_order_courier_name()`) и времени кухни (`get_order_cooking_time_minutes()`).
2. **Функция `get_order_cooking_time_minutes(order_obj, ctx)`**:
   - Надежно извлекает время кухни из `order_context` (`cooking_time`, `cooking_time_minutes`), из атрибутов модели `Order` (`cooking_time_minutes`, `cooking_time_updated_at`), а также выполняет фоллбэк-запрос в БД к таблице `orders`.
   - Поддерживает строковые форматы (напр. `"25 мин"`, `"30"`).
3. **Строгая блокировка отправки при отсутствии времени кухни**:
   - Для всех курьерских событий проверяется флаг `require_cooking_time_set` (по умолчанию `True` для курьерских цепочек):
     ```python
     if is_courier_event and require_cooking_time_set:
         cook_mins = get_order_cooking_time_minutes(order_for_check, order_context)
         if cook_mins <= 0:
             logger.info(
                 f"Skipping notification: chain requires cooking time to be set, "
                 f"but order {order_number} cooking_time is {cook_mins} mins"
             )
             return results
     ```
   - Если кухня не установила время приготовления (`<= 0`), роутер логирует пропуск и уведомление курьеру не отправляется.
4. **Автоматическая активация и досылка**:
   - Как только время кухни выставляется в iiko / админке / KDS (`> 0` минут), срабатывает метод `check_and_send_order_new_to_courier`, который досылает курьеру шаг 1 (`order_new`), а все последующие уведомления по заказу беспрепятственно доставляются курьеру.

### Б. Фронтенд (`admin/resources/js/pages/settings/vk-notifications_utf8.vue`)
1. В `parseChainConfig` для курьерских шаблонов значение `require_cooking_time_set` по умолчанию установлено в `true`.
2. В карточках шагов логистических цепочек чипс «Время кухни задано (>0)» отображает актуальный статус условия и переключается в 1 клик.
3. В модальном диалоге редактирования шаблона тумблер условия сохранен и синхронизирован.

### В. База данных PostgreSQL (`vk_templates` на VPS)
1. Выполнен безопасный скрипт обновления `chain_config` для всех 9 шаблонов курьера:
   - ID 39: `order_new`
   - ID 40: `order_status_update`
   - ID 41: `order_amount_changed`
   - ID 42: `order_items_changed`
   - ID 43: `order_time_changed`
   - ID 44: `order_address_changed`
   - ID 45: `order_cancelled`
   - ID 47: `courier_assigned`
   - ID 48: `change_cooking_time`
   У всех шаблонов установлено `"require_cooking_time_set": true`.
2. Все существующие пользовательские настройки (тексты, привязка к боту «Курьеры» ID=2, каналы VK/TG/MAX/SMS) сохранены без изменений.

---

## 4. Верификация и тестирование на VPS
1. **Сверка хэшей SHA-256**:
   - `vk_notification_router.py`: `04804da873475af3ec2bbc52bd66d424387e22bf21971966f59a3c219b31c55f` (совпадает).
   - `vk-notifications_utf8.vue`: `16d19999f5ec0f54681c6bbe5706a5d33cc77d4f811d67f5fa4b21f8f5f2ba3e` (совпадает).
2. **Сборка фронтенда**:
   - `npm run build` выполнен на сервере, завершился успешно без ошибок (`built in 1m 15s`).
   - `php artisan optimize:clear` очистил кэш шаблонов и роутов.
3. **Перезапуск контейнеров**:
   - `foodtech-backend`, `foodtech-worker`, `foodtech-admin`, `foodtech-nginx` перезапущены.
4. **Тест логики**:
   - Тестовым вызовом проверено:
     - При `cooking_time = 0` уведомления курьера блокируются: `Skipping notification: chain requires cooking time to be set, but order cooking_time is 0 mins`.
     - При `cooking_time = 25` уведомление успешно формируется и отправляется курьеру.
