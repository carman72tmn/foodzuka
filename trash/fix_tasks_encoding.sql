UPDATE scheduled_tasks SET 
    name = 'Полная синхронизация iiko (Меню + Категории)',
    description = 'Автоматическая полная синхронизация всех товаров и категорий в 3:00'
WHERE job_id = 'sync_all';

UPDATE scheduled_tasks SET 
    name = 'Синхронизация заказов (каждые 10 мин)',
    description = 'Синхронизация заказов из iiko каждые 10 минут'
WHERE job_id = 'sync_orders';

UPDATE scheduled_tasks SET 
    name = 'Ежечасная синхронизация заказов',
    description = 'Полная синхронизация заказов за последние 24 часа'
WHERE job_id = 'sync_orders_hourly';

UPDATE scheduled_tasks SET 
    name = 'Синхронизация смен',
    description = 'Синхронизация кассовых смен из iiko каждые 10 минут'
WHERE job_id = 'sync_shifts';

UPDATE scheduled_tasks SET 
    name = 'Очистка системных логов',
    description = 'Автоматическое удаление старых системных логов старше 30 дней'
WHERE job_id = 'cleanup_logs';

UPDATE scheduled_tasks SET 
    name = 'Синхронизация выручки (сегодня)',
    description = 'Обновление данных о выручке за текущий день каждые 30 минут'
WHERE job_id = 'sync_today_revenue';

UPDATE scheduled_tasks SET 
    name = 'Синхронизация выручки (вчера)',
    description = 'Итоговая синхронизация выручки за вчерашний день в 00:05'
WHERE job_id = 'sync_yesterday_revenue';

UPDATE scheduled_tasks SET 
    name = 'Ночная синхронизация гостей',
    description = 'Полная синхронизация базы гостей в 03:00 ночи'
WHERE job_id = 'nightly_sync';

UPDATE scheduled_tasks SET 
    name = 'Рассылка VK Дайджеста',
    description = 'Отправка уведомлений в VK для сотрудников'
WHERE job_id = 'vk_digest';
