# Журнал задачи: Исправление сохранения настроек шаблонов рассылки и уведомлений об открытии смен
**Дата**: 26.10.2026 11:15 (UTC+5)
**Статус**: Выполнено успешно

---

## 1. Выявленные проблемы и причины

### Проблема 1: Настройки шаблона курьера не сохранялись при отключении
**Симптомы:**
В модальном окне редактирования шаблона рассылок (`/settings/vk-notifications`):
1. «Режим одного сообщения (редактировать вместо новых)» (`edit_existing_message`)
2. «Кнопки действий курьера в соцсетях» (`show_courier_action_buttons`)
3. «Сжимать сообщение и скрывать QR-код после доставки» (`collapse_on_delivered`)
При отключении (тумблер в `false`) и сохранении при повторном открытии они снова оставались активными (`true`).

**Причина:**
- В файле `backend/app/api/vk_bot_admin.py` схема валидации `VkTemplateUpdate` (используемая для эндпоинта `PATCH /api/v1/vk-bot/templates/{template_id}`) **не содержала полей** `edit_existing_message`, `collapse_on_delivered`, `show_courier_action_buttons`.
- Pydantic при разборе входящего JSON автоматически отбрасывал эти поля как неизвестные.
- В методе `update_template` вызов `data.dict(exclude_unset=True)` не содержал этих полей, из-за чего `setattr(template, key, value)` не обновлял их в базе данных.
- Во фронтенде (`vk-notifications_utf8.vue`) в объекте `currentTemplate` при открытии модального окна (`openEditTemplate`) отсутствовала явная булева нормализация для этих полей.

### Проблема 2: ВКонтакте не уходили уведомления об открытии смен сотрудниками (`shift_open`)
**Причины:**
1. **Канал VK в шаблоне**: в `vk_templates` для шаблона `shift_open` (ID: 11) тумблер канала VK (`send_vk`) был отключен (активен был только MAX). Роутер `vk_notification_router.py` блокирует отправку в канал, если он выключен в шаблоне.
2. **Конфликт `target_mode: specific` и таблицы `vk_bot_subscriptions`**:
   - В шаблоне выбраны получатели: `[5, 6, 12]` (Руководитель, Администратор, Сергей Доставка).
   - В `vk_notification_router.py` список получателей сначала жестко фильтровался запросом:
     `SELECT ... FROM vk_bot_subscriptions WHERE event_type = 'shift_open'`.
   - В таблице `vk_bot_subscriptions` запись на `shift_open` была только у Аккаунта 5 (Руководитель). У аккаунтов 6 и 12 этой подписки не было, так как `shift_open` не входил в `DEFAULT_SYSTEM_EVENTS`. Из-за этого аккаунты 6 и 12 отбрасывались.
3. **Открытие смен курьерами через панель `/pers` (`courier.py`)**:
   - В эндпоинтах `/api/v1/courier/open-shift` и `/api/v1/courier/admin/open-shift` создавалась запись в `shifts`, но вызов отправки уведомления в ВК/мессенджеры отсутствовал вовсе.

---

## 2. Внесенные изменения

### Бэкенд (FastAPI / SQLModel):
1. **`backend/app/api/vk_bot_admin.py`**:
   - В схему `VkTemplateUpdate` добавлены поля:
     ```python
     edit_existing_message: Optional[bool] = None
     collapse_on_delivered: Optional[bool] = None
     show_courier_action_buttons: Optional[bool] = None
     ```
   - В список `DEFAULT_SYSTEM_EVENTS` добавлены события `shift_open` и `shift_close`.
2. **`backend/app/services/vk_notification_router.py`**:
   - Добавлено автоматическое включение в список получателей сотрудников, явно указанных в `target_accounts` шаблона при `target_mode in ("specific", "by_accounts")`, даже если у них отсутствует явная запись в таблице `vk_bot_subscriptions`.
3. **`backend/app/api/courier.py`**:
   - Добавлен асинхронный вызов `iiko_sync_service._send_shift_vk_notification(new_shift, emp, "shift_open")` при открытии смены курьером в приложении (`/open-shift`) и администратором (`/admin/open-shift`).
   - Добавлен вызов уведомления `shift_close` при закрытии смены курьера через `/admin/close-shift`.

### Фронтенд (Vue 3 / Vite):
1. **`admin/resources/js/pages/settings/vk-notifications_utf8.vue`**:
   - В методе `openEditTemplate(tpl)` добавлена строгая булева инициализация полей `edit_existing_message`, `collapse_on_delivered`, `show_courier_action_buttons`.
   - В методе `saveTemplate()` обеспечена явная передача булевых значений `Boolean(...)` в теле PATCH-запроса.

---

## 3. Развертывание и тестирование
1. Все файлы выгружены на VPS (`178.212.13.48`). Контрольные суммы (MD5) проверены — 100% совпадение.
2. Фронтенд пересобран (`npm run build`), сгенерирован бандл `vk-notifications_utf8-9OBeGSrd.js`.
3. Очищен кэш Laravel (`php artisan optimize:clear`).
4. Перезапущены контейнеры `foodtech-backend` и `foodtech-worker`.
5. Проведено прямое тестирование через API:
   - `PATCH /templates/11` со значениями `False` -> успешно сохранено в БД.
   - `PATCH /templates/11` со значениями `True` -> успешно сохранено в БД.
   - Тестовое событие `shift_open` успешно отправлено и зафиксировано в `vk_bot_message_logs`.
