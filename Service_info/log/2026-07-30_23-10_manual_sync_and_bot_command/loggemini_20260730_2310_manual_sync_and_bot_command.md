# Лог изменений - Ручная синхронизация баллов активности ВК и команда перевода баллов в бонусы

**Дата**: 30.07.2026 23:40 (UTC+5)

## Выполненные задачи
1. **Отключение авто-синхронизации**:
   - В [vk_activity_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/vk_activity_service.py) закомментированы вызовы `sync_vk_user_points_to_iiko` во всех автоматических обработчиках событий (лайки, комментарии, репосты, опросы, вступления в группу).
   - В [vk_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/vk_service.py) отключена автоматическая синхронизация при автопривязке, ручном подтверждении телефона, регистрации и запросе баланса.

2. **Кнопка ручной синхронизации**:
   - В [vk_activity_bots.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/vk_activity_bots.py) добавлен эндпоинт `POST /api/v1/vk-activity-settings/users/{vk_id}/sync-iiko`, выполняющий точечную ручную синхронизацию дельты баллов пользователя с iikoCard. Из `/update-points` убран автоматический вызов синхронизации.
   - В [vk-bots.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/marketing/vk-bots.vue) добавлена функция `syncUserPointsToIiko` и кнопка с иконкой `ri-refresh-line` в колонке «Корректировка» таблицы рейтинга.

3. **Команда бота «Перевести баллы в бонусы»**:
   - В [vk_service.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/services/vk_service.py) добавлен метод `transfer_vk_points_to_iiko`, который зачисляет баллы в iikoCard (через `add_customer_bonuses`), обнуляет локальные поля `vk_bonus_balance` and `vk_bonus_balance_synced`, и логирует операцию списания в `vk_activities` (`action_type = "points_transfer"`).
   - В `handle_bot_commands_and_fsm` добавлена поддержка типа действия `transfer_points`. Если профиль пользователя не привязан, инициируется верификация. При успешном завершении верификации в FSM (через Flash Call, анкету или Mini App/Wait Call в [validation.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/validation.py)) автоматически срабатывает перевод баллов без повторного вызова команды.
   - В [bot-commands.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/settings/bot-commands.vue) добавлена поддержка команды `transfer_points` в списке и форме редактирования команд.

4. **Удаление старых активностей**:
   - В [vk_parser_tasks.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/tasks/vk_parser_tasks.py) в периодическую Celery-задачу `cleanup_vk_messages_task` добавлено удаление записей `VkActivity` старше 12 месяцев (365 дней).

## Статус деплоя
- Все измененные файлы скопированы на VPS.
- Контейнеры `backend` и `worker` успешно перезапущены.
- Запущена сборка фронтенда на сервере.
