# Лог выполнения задачи: Глобальные мастер-переключатели браузера, уведомление о доставке заказа и изоляция курьерских уведомлений

Дата: 04.09.2026 20:40 (UTC+5)
Сессия: 2026-09-04_20-40_browser_notification_toggles_and_order_delivered

## 1. Постановка задачи
1. Проверить отправку уведомлений в соцсети: сообщения должны уходить строго согласно настроенным шаблонам, каналам и условиям («Время кухни задано > 0 мин»). Исключить любые дубли.
2. Проверить общие браузерные уведомления (звуковые сигналы, всплывающие окна и Desktop Web Push для сотрудников), чтобы избежать дублей и лишнего шума.
3. Для аккаунта курьера по умолчанию отключить общесистемные уведомления (новые заказы, поступления оплат, чужие отмены и изменения заказов), оставив строго те, что активированы в профиле курьера.
4. Добавить в настройки два общих мастер-переключателя:
   - 1. «Отключить уведомления браузера для курьеров» (disable_browser_notifications_couriers).
   - 2. «Отключить уведомления в браузере для всех!» (disable_browser_notifications_all).
5. Добавить в общие уведомления новое оповещение о Доставке заказа (order_delivered):
   - Web Push.
   - Звуковой сигнал (с выбором mp3 и тумблером вкл/выкл).
   - Стилизованное постоянное всплывающее окно (VSnackbar с :timeout=-1), которое не исчезает с экрана, пока его не закроют («В ЗАКАЗЫ» / «ЗАКРЫТЬ»).
   - Срабатывает строго для доставок при переводе в статус «Доставлен» (OrderStatus.delivered).
   - Для курьеров это уведомление скрыто.

## 2. Реализация
1. База данных PostgreSQL (admin_notification_settings):
   - Добавлены колонки disable_browser_notifications_couriers, disable_browser_notifications_all, order_delivered_sound_enabled, order_delivered_sound_file, order_delivered_push_enabled.
   - Для всех курьеров (users.role_id = 7) дефолтные общие уведомления сброшены в false.
2. Бэкенд:
   - backend/app/models/admin_notification_settings.py: поля добавлены в модель.
   - backend/app/api/notifications.py: схемы и логика обновлены.
   - backend/app/services/iiko_sync_service.py (UTF-8): триггер order_delivered, флаг order_delivered_notified, проверка мастер-переключателей в send_admin_push_notification, исключение курьеров.
3. Фронтенд:
   - admin/resources/js/stores/chatStore.js: orderDeliveredAlert, мастер-переключатели, изоляция курьеров.
   - admin/resources/js/layouts/components/DefaultLayoutWithVerticalNav.vue: стилизованный VSnackbar с :timeout=-1.
   - admin/resources/js/pages/settings/notifications.vue: блок мастер-переключателей и блок настройки доставки заказа.

## 3. Сверка и деплой
- Все SHA-256 хэши проверены и совпадают на 100%.
- Сборка npm run build на VPS успешно завершена.
- Контейнеры foodtech-backend и foodtech-worker перезапущены.
- Кэш Laravel очищен (php artisan optimize:clear).
- Документация system_faq.md, sql_faq.md, sitenav.md обновлена.
