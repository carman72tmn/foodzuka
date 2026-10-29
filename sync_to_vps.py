import os
import subprocess

# Files to sync: (local_path, remote_path)
files_to_sync = [
    ('backend/app/models/vk_activity_settings.py', '/root/foodzuka/backend/app/models/vk_activity_settings.py'),
    ('backend/app/models/vk_activity.py', '/root/foodzuka/backend/app/models/vk_activity.py'),
    ('backend/app/models/__init__.py', '/root/foodzuka/backend/app/models/__init__.py'),
    ('backend/app/api/vk_activity_bots.py', '/root/foodzuka/backend/app/api/vk_activity_bots.py'),
    ('backend/app/services/vk_activity_service.py', '/root/foodzuka/backend/app/services/vk_activity_service.py'),
    ('backend/app/scripts/migrate_vk_activity_penalty_timers.py', '/root/foodzuka/backend/app/scripts/migrate_vk_activity_penalty_timers.py'),
    ('backend/app/models/vk_post_scheduler.py', '/root/foodzuka/backend/app/models/vk_post_scheduler.py'),
    ('backend/app/scripts/create_vk_scheduler_tables.py', '/root/foodzuka/backend/app/scripts/create_vk_scheduler_tables.py'),
    ('backend/app/services/vk_scheduler_service.py', '/root/foodzuka/backend/app/services/vk_scheduler_service.py'),
    ('backend/app/api/vk_scheduler.py', '/root/foodzuka/backend/app/api/vk_scheduler.py'),
    ('backend/main.py', '/root/foodzuka/backend/main.py'),
    ('backend/app/tasks/vk_scheduler_task.py', '/root/foodzuka/backend/app/tasks/vk_scheduler_task.py'),
    ('backend/app/core/scheduler.py', '/root/foodzuka/backend/app/core/scheduler.py'),
    ('admin/resources/js/pages/marketing/vk-scheduler.vue', '/root/foodzuka/admin/resources/js/pages/marketing/vk-scheduler.vue'),
    ('admin/resources/js/plugins/router/routes.js', '/root/foodzuka/admin/resources/js/plugins/router/routes.js'),
    ('admin/resources/js/pages/marketing/vk-bots.vue', '/root/foodzuka/admin/resources/js/pages/marketing/vk-bots.vue'),
    ('backend/app/services/iiko_service.py', '/root/foodzuka/backend/app/services/iiko_service.py'),
    ('backend/app/services/iiko_sync_service.py', '/root/foodzuka/backend/app/services/iiko_sync_service.py'),
    ('backend/app/services/mailing_cascade_service.py', '/root/foodzuka/backend/app/services/mailing_cascade_service.py'),
    ('backend/app/core/scheduler.py', '/root/foodzuka/backend/app/core/scheduler.py'),
    ('backend/app/core/logging_utils.py', '/root/foodzuka/backend/app/core/logging_utils.py'),
    ('backend/app/tasks/customer_tasks.py', '/root/foodzuka/backend/app/tasks/customer_tasks.py'),
    ('backend/app/api/webhooks.py', '/root/foodzuka/backend/app/api/webhooks.py'),
    ('backend/app/api/orders.py', '/root/foodzuka/backend/app/api/orders.py'),
    ('backend/app/models/order.py', '/root/foodzuka/backend/app/models/order.py'),
    ('admin/resources/js/components/CustomerDetailModal.vue', '/root/foodzuka/admin/resources/js/components/CustomerDetailModal.vue'),
    ('admin/resources/js/components/OrderDetailModal.vue', '/root/foodzuka/admin/resources/js/components/OrderDetailModal.vue'),
    ('admin/resources/js/components/OrderArchiveCard.vue', '/root/foodzuka/admin/resources/js/components/OrderArchiveCard.vue'),
    ('admin/resources/js/pages/orders/index.vue', '/root/foodzuka/admin/resources/js/pages/orders/index.vue'),
    ('admin/resources/styles/order-detail-soft.css', '/root/foodzuka/admin/resources/styles/order-detail-soft.css'),
    ('backend/app/api/customers.py', '/root/foodzuka/backend/app/api/customers.py'),
    ('admin/resources/js/pages/clients/index.vue', '/root/foodzuka/admin/resources/js/pages/clients/index.vue'),
    ('admin/resources/js/utils/date.js', '/root/foodzuka/admin/resources/js/utils/date.js'),
    ('admin/resources/js/pages/settings/iiko.vue', '/root/foodzuka/admin/resources/js/pages/settings/iiko.vue'),
    ('admin/resources/js/pages/employee/courier.vue', '/root/foodzuka/admin/resources/js/pages/employee/courier.vue'),
    ('admin/resources/js/EmployeeApp.vue', '/root/foodzuka/admin/resources/js/EmployeeApp.vue'),
    ('admin/resources/views/employee_application.blade.php', '/root/foodzuka/admin/resources/views/employee_application.blade.php'),
    ('admin/resources/js/pages/settings/vk.vue', '/root/foodzuka/admin/resources/js/pages/settings/vk.vue'),
    ('admin/resources/js/pages/loyalty/index.vue', '/root/foodzuka/admin/resources/js/pages/loyalty/index.vue'),
    ('admin/resources/js/pages/settings/sync-logs.vue', '/root/foodzuka/admin/resources/js/pages/settings/sync-logs.vue'),
    ('admin/resources/js/pages/reports/orders.vue', '/root/foodzuka/admin/resources/js/pages/reports/orders.vue'),
    ('backend/app/models/iiko_loyalty.py', '/root/foodzuka/backend/app/models/iiko_loyalty.py'),
    ('backend/app/models/iiko_settings.py', '/root/foodzuka/backend/app/models/iiko_settings.py'),
    ('backend/app/scripts/migrate_iiko_dev_fields.py', '/root/foodzuka/backend/app/scripts/migrate_iiko_dev_fields.py'),
    ('Service_info/system_faq.md', '/root/foodzuka/Service_info/system_faq.md'),
    ('Service_info/sql_faq.md', '/root/foodzuka/Service_info/sql_faq.md'),
    ('Service_info/sitenav.md', '/root/foodzuka/Service_info/sitenav.md'),
    ('backend/app/schemas/__init__.py', '/root/foodzuka/backend/app/schemas/__init__.py'),
    ('bot/handlers/__init__.py', '/root/foodzuka/bot/handlers/__init__.py'),
    ('bot/utils/date_utils.py', '/root/foodzuka/bot/utils/date_utils.py'),
    ('bot/requirements.txt', '/root/foodzuka/bot/requirements.txt'),
    ('docker-compose.prod.yml', '/root/foodzuka/docker-compose.prod.yml'),
    ('configs/nginx/default.conf', '/root/foodzuka/configs/nginx/default.conf'),
    ('admin/resources/js/plugins/iconify/build-icons.js', '/root/foodzuka/admin/resources/js/plugins/iconify/build-icons.js'),
    ('trash/test_loyalty_sync.py', '/root/foodzuka/test_loyalty_sync.py'),
    ('backend/add_courier_fields.py', '/root/foodzuka/backend/add_courier_fields.py'),
    ('backend/app/services/revenue_sync.py', '/root/foodzuka/backend/app/services/revenue_sync.py'),
    ('backend/app/api/courier.py', '/root/foodzuka/backend/app/api/courier.py'),
    ('backend/app/api/employees.py', '/root/foodzuka/backend/app/api/employees.py'),
    ('admin/resources/js/pages/employees.vue', '/root/foodzuka/admin/resources/js/pages/employees.vue'),
    ('backend/app/core/datetime_utils.py', '/root/foodzuka/backend/app/core/datetime_utils.py'),
    ('admin/resources/styles/courier.css', '/root/foodzuka/admin/resources/styles/courier.css'),
    # Chat system files
    ('backend/app/models/chat.py', '/root/foodzuka/backend/app/models/chat.py'),
    ('backend/app/schemas/chat.py', '/root/foodzuka/backend/app/schemas/chat.py'),
    ('backend/app/api/chat.py', '/root/foodzuka/backend/app/api/chat.py'),
    ('admin/resources/js/stores/chatStore.js', '/root/foodzuka/admin/resources/js/stores/chatStore.js'),
    ('admin/resources/js/components/ChatDrawer.vue', '/root/foodzuka/admin/resources/js/components/ChatDrawer.vue'),
    ('backend/app/models/user.py', '/root/foodzuka/backend/app/models/user.py'),
    ('backend/app/models/__init__.py', '/root/foodzuka/backend/app/models/__init__.py'),
    ('backend/app/api/auth.py', '/root/foodzuka/backend/app/api/auth.py'),
    ('backend/app/api/deps.py', '/root/foodzuka/backend/app/api/deps.py'),
    ('backend/app/api/__init__.py', '/root/foodzuka/backend/app/api/__init__.py'),
    ('backend/app/schemas/user.py', '/root/foodzuka/backend/app/schemas/user.py'),
    ('backend/main.py', '/root/foodzuka/backend/main.py'),
    ('admin/resources/js/layouts/components/DefaultLayoutWithVerticalNav.vue', '/root/foodzuka/admin/resources/js/layouts/components/DefaultLayoutWithVerticalNav.vue'),
    ('backend/alembic/versions/2026_05_04_1330-chat_v1.py', '/root/foodzuka/backend/alembic/versions/2026_05_04_1330-chat_v1.py'),
    ('backend/alembic/versions/2026_05_04_2355-add_bonus_ids.py', '/root/foodzuka/backend/alembic/versions/2026_05_04_2355-add_bonus_ids.py'),
    ('backend/app/models/customer.py', '/root/foodzuka/backend/app/models/customer.py'),
    ('backend/app/services/sync_single_order.py', '/root/foodzuka/backend/app/services/sync_single_order.py'),
    ('backend/alembic/versions/2026_05_05_0430-fix_address_history_not_null.py', '/root/foodzuka/backend/alembic/versions/2026_05_05_0430-fix_address_history_not_null.py'),
    ('backend/alembic/versions/2026_05_05_1045-add_order_payment_fields.py', '/root/foodzuka/backend/alembic/versions/2026_05_05_1045-add_order_payment_fields.py'),
    ('backend/alembic/versions/2026_05_13_1300_vk_monitoring.py', '/root/foodzuka/backend/alembic/versions/2026_05_13_1300_vk_monitoring.py'),
    ('backend/alembic/versions/2026_05_13_2000_add_vk_notification_settings.py', '/root/foodzuka/backend/alembic/versions/2026_05_13_2000_add_vk_notification_settings.py'),
    ('backend/alembic/versions/2026_06_10_2045_add_vk_parser_mask.py', '/root/foodzuka/backend/alembic/versions/2026_06_10_2045_add_vk_parser_mask.py'),
    ('backend/alembic/versions/2026_06_10_2200_add_vk_user_flags.py', '/root/foodzuka/backend/alembic/versions/2026_06_10_2200_add_vk_user_flags.py'),
    ('backend/alembic/versions/2026_06_16_0015_add_price_source_to_iiko_settings.py', '/root/foodzuka/backend/alembic/versions/2026_06_16_0015_add_price_source_to_iiko_settings.py'),
    ('backend/app/services/force_sync_186.py', '/root/foodzuka/backend/app/services/force_sync_186.py'),
    ('backend/app/core/config.py', '/root/foodzuka/backend/app/core/config.py'),
    ('backend/app/core/security.py', '/root/foodzuka/backend/app/core/security.py'),
    ('admin/resources/js/utils/auth.js', '/root/foodzuka/admin/resources/js/utils/auth.js'),
    ('admin/resources/js/pages/login.vue', '/root/foodzuka/admin/resources/js/pages/login.vue'),
    ('admin/resources/js/pages/employee/dashboard.vue', '/root/foodzuka/admin/resources/js/pages/employee/dashboard.vue'),
    ('admin/resources/js/views/pages/account-settings/AccountSettingsAccount.vue', '/root/foodzuka/admin/resources/js/views/pages/account-settings/AccountSettingsAccount.vue'),
    ('admin/resources/js/plugins/router/index.js', '/root/foodzuka/admin/resources/js/plugins/router/index.js'),
    ('admin/resources/js/views/pages/users/UserList.vue', '/root/foodzuka/admin/resources/js/views/pages/users/UserList.vue'),
    ('admin/resources/js/views/pages/users/RoleList.vue', '/root/foodzuka/admin/resources/js/views/pages/users/RoleList.vue'),
    ('backend/app/models/vk_settings.py', '/root/foodzuka/backend/app/models/vk_settings.py'),
    ('backend/app/models/vk_user.py', '/root/foodzuka/backend/app/models/vk_user.py'),
    ('backend/app/models/vk_message.py', '/root/foodzuka/backend/app/models/vk_message.py'),
    ('backend/app/models/vk_webhook_log.py', '/root/foodzuka/backend/app/models/vk_webhook_log.py'),
    ('backend/app/models/vk_bot_connection.py', '/root/foodzuka/backend/app/models/vk_bot_connection.py'),
    ('backend/app/services/vk_service.py', '/root/foodzuka/backend/app/services/vk_service.py'),
    ('backend/app/api/vk.py', '/root/foodzuka/backend/app/api/vk.py'),
    ('backend/app/scripts/test_vk_multibot_vps.py', '/root/foodzuka/backend/app/scripts/test_vk_multibot_vps.py'),
    ('admin/resources/js/layouts/components/NavItems.vue', '/root/foodzuka/admin/resources/js/layouts/components/NavItems.vue'),
    ('admin/resources/js/plugins/router/routes.js', '/root/foodzuka/admin/resources/js/plugins/router/routes.js'),
    ('admin/resources/js/pages/settings/vk-parser.vue', '/root/foodzuka/admin/resources/js/pages/settings/vk-parser.vue'),
    ('admin/resources/js/pages/settings/vk-notifications_utf8.vue', '/root/foodzuka/admin/resources/js/pages/settings/vk-notifications_utf8.vue'),
    ('backend/app/tasks/vk_parser_tasks.py', '/root/foodzuka/backend/app/tasks/vk_parser_tasks.py'),
    ('backend/app/scripts/create_vk_bot_tables.py', '/root/foodzuka/backend/app/scripts/create_vk_bot_tables.py'),
    ('backend/app/services/vk_longpoll_service.py', '/root/foodzuka/backend/app/services/vk_longpoll_service.py'),
    ('backend/app/scripts/add_use_longpoll_to_vk_connections.py', '/root/foodzuka/backend/app/scripts/add_use_longpoll_to_vk_connections.py'),
    # MAX integration
    ('backend/app/models/max_settings.py', '/root/foodzuka/backend/app/models/max_settings.py'),
    ('backend/app/api/max.py', '/root/foodzuka/backend/app/api/max.py'),
    ('admin/resources/js/pages/settings/max.vue', '/root/foodzuka/admin/resources/js/pages/settings/max.vue'),
    ('backend/app/services/max_service.py', '/root/foodzuka/backend/app/services/max_service.py'),
    ('backend/app/services/multichat_user_service.py', '/root/foodzuka/backend/app/services/multichat_user_service.py'),
    ('backend/app/scripts/create_multichat_tables.py', '/root/foodzuka/backend/app/scripts/create_multichat_tables.py'),
    ('backend/app/scripts/create_multichat_tags_tables.py', '/root/foodzuka/backend/app/scripts/create_multichat_tags_tables.py'),
    ('backend/app/scripts/create_multichat_accounts_tables.py', '/root/foodzuka/backend/app/scripts/create_multichat_accounts_tables.py'),
    ('backend/app/scripts/check_user_rbac.py', '/root/foodzuka/backend/app/scripts/check_user_rbac.py'),
    ('backend/app/api/multichat.py', '/root/foodzuka/backend/app/api/multichat.py'),
    ('admin/resources/js/pages/multichat/index.vue', '/root/foodzuka/admin/resources/js/pages/multichat/index.vue'),
    # Mailing Cascades
    ('backend/app/models/mailing_cascade.py', '/root/foodzuka/backend/app/models/mailing_cascade.py'),
    ('backend/app/api/mailing_cascades.py', '/root/foodzuka/backend/app/api/mailing_cascades.py'),
    ('backend/app/services/mailing_cascade_service.py', '/root/foodzuka/backend/app/services/mailing_cascade_service.py'),
    ('backend/app/tasks/mailing_tasks.py', '/root/foodzuka/backend/app/tasks/mailing_tasks.py'),
    ('backend/app/schemas/mailing_cascade.py', '/root/foodzuka/backend/app/schemas/mailing_cascade.py'),
    ('admin/resources/js/pages/mailings/cascades.vue', '/root/foodzuka/admin/resources/js/pages/mailings/cascades.vue'),
    ('backend/alembic/versions/2026_05_13_2230_add_cascades_and_max.py', '/root/foodzuka/backend/alembic/versions/2026_05_13_2230_add_cascades_and_max.py'),
    ('backend/app/api/bank.py', '/root/foodzuka/backend/app/api/bank.py'),
    ('admin/resources/js/pages/bank/payments.vue', '/root/foodzuka/admin/resources/js/pages/bank/payments.vue'),
    ('admin/resources/js/pages/bank/tbank-payments.vue', '/root/foodzuka/admin/resources/js/pages/bank/tbank-payments.vue'),
    ('admin/resources/js/plugins/router/routes.js', '/root/foodzuka/admin/resources/js/plugins/router/routes.js'),
    ('admin/resources/js/layouts/components/NavItems.vue', '/root/foodzuka/admin/resources/js/layouts/components/NavItems.vue'),
    ('backend/app/models/tbank_settings.py', '/root/foodzuka/backend/app/models/tbank_settings.py'),
    ('backend/alembic/versions/2026_06_02_1540_add_tbank_settings.py', '/root/foodzuka/backend/alembic/versions/2026_06_02_1540_add_tbank_settings.py'),
    ('backend/alembic/versions/2026_06_02_1615_add_selected_terminals.py', '/root/foodzuka/backend/alembic/versions/2026_06_02_1615_add_selected_terminals.py'),
    ('backend/alembic/versions/2026_06_02_1333-cb52bb53a875_add_tbank_statements.py', '/root/foodzuka/backend/alembic/versions/2026_06_02_1333-cb52bb53a875_add_tbank_statements.py'),
    ('backend/app/api/tbank.py', '/root/foodzuka/backend/app/api/tbank.py'),
    ('backend/app/api/tbank_webhooks.py', '/root/foodzuka/backend/app/api/tbank_webhooks.py'),
    ('admin/resources/js/pages/settings/tbank.vue', '/root/foodzuka/admin/resources/js/pages/settings/tbank.vue'),
    # Notification & Push features
    ('backend/requirements.txt', '/root/foodzuka/backend/requirements.txt'),
    ('backend/app/models/push_subscription.py', '/root/foodzuka/backend/app/models/push_subscription.py'),
    ('backend/app/models/admin_notification_settings.py', '/root/foodzuka/backend/app/models/admin_notification_settings.py'),
    ('backend/app/core/webpush_utils.py', '/root/foodzuka/backend/app/core/webpush_utils.py'),
    ('backend/app/models/admin_notification.py', '/root/foodzuka/backend/app/models/admin_notification.py'),
    ('create_admin_notifications_table.py', '/root/foodzuka/backend/create_admin_notifications_table.py'),
    ('backend/app/api/notifications.py', '/root/foodzuka/backend/app/api/notifications.py'),
    ('admin/public/sw.js', '/root/foodzuka/admin/public/sw.js'),
    ('admin/public/manifest.json', '/root/foodzuka/admin/public/manifest.json'),
    ('admin/public/pwa-192.png', '/root/foodzuka/admin/public/pwa-192.png'),
    ('admin/public/pwa-512.png', '/root/foodzuka/admin/public/pwa-512.png'),
    ('admin/resources/views/application.blade.php', '/root/foodzuka/admin/resources/views/application.blade.php'),
    ('admin/resources/views/employee_application.blade.php', '/root/foodzuka/admin/resources/views/employee_application.blade.php'),
    ('admin/resources/js/pages/settings/notifications.vue', '/root/foodzuka/admin/resources/js/pages/settings/notifications.vue'),
    ('admin/resources/js/main.js', '/root/foodzuka/admin/resources/js/main.js'),
    ('admin/resources/js/employee_main.js', '/root/foodzuka/admin/resources/js/employee_main.js'),
    ('admin/public/sounds/bell.mp3', '/root/foodzuka/admin/public/sounds/bell.mp3'),
    ('admin/public/sounds/cash.mp3', '/root/foodzuka/admin/public/sounds/cash.mp3'),
    ('admin/public/sounds/chime.mp3', '/root/foodzuka/admin/public/sounds/chime.mp3'),
    ('admin/public/sounds/sonar.mp3', '/root/foodzuka/admin/public/sounds/sonar.mp3'),
    ('admin/public/sounds/water.mp3', '/root/foodzuka/admin/public/sounds/water.mp3'),
    ('admin/public/sounds/click.mp3', '/root/foodzuka/admin/public/sounds/click.mp3'),
    ('admin/public/sounds/branch.mp3', '/root/foodzuka/admin/public/sounds/branch.mp3'),
    ('admin/public/sounds/push.mp3', '/root/foodzuka/admin/public/sounds/push.mp3'),
    ('admin/public/sounds/doorbell.mp3', '/root/foodzuka/admin/public/sounds/doorbell.mp3'),
    ('admin/public/sounds/error.mp3', '/root/foodzuka/admin/public/sounds/error.mp3'),
    ('create_notification_tables.py', '/root/foodzuka/backend/create_notification_tables.py'),
    ('download_sounds.py', '/root/foodzuka/backend/download_sounds.py'),
    ('backend/app/tasks/tbank_tasks.py', '/root/foodzuka/backend/app/tasks/tbank_tasks.py'),
    ('backend/app/core/celery_app.py', '/root/foodzuka/backend/app/core/celery_app.py'),
    ('backend/scripts/add_tbank_sync_task.py', '/root/foodzuka/backend/scripts/add_tbank_sync_task.py'),
    ('backend/scripts/add_tbank_terminal_sync_task.py', '/root/foodzuka/backend/scripts/add_tbank_terminal_sync_task.py'),
    # Bot Commands & FSM integration
    ('backend/app/models/bot_command.py', '/root/foodzuka/backend/app/models/bot_command.py'),
    ('backend/app/api/bot_commands.py', '/root/foodzuka/backend/app/api/bot_commands.py'),
    ('admin/resources/js/pages/settings/bot-commands.vue', '/root/foodzuka/admin/resources/js/pages/settings/bot-commands.vue'),
    ('backend/migrate_bot_commands.py', '/root/foodzuka/backend/migrate_bot_commands.py'),
    # VK templates overhaul files
    ('backend/app/models/vk_bot.py', '/root/foodzuka/backend/app/models/vk_bot.py'),
    ('backend/app/api/vk_bot_admin.py', '/root/foodzuka/backend/app/api/vk_bot_admin.py'),
    ('backend/app/services/vk_bot_service.py', '/root/foodzuka/backend/app/services/vk_bot_service.py'),
    ('backend/app/services/vk_notification_router.py', '/root/foodzuka/backend/app/services/vk_notification_router.py'),
    ('backend/app/scripts/migrate_notifications_channels.py', '/root/foodzuka/backend/app/scripts/migrate_notifications_channels.py'),
    ('backend/app/scripts/migrate_payment_qr.py', '/root/foodzuka/backend/app/scripts/migrate_payment_qr.py'),
    ('backend/app/scripts/migrate_vk_templates_courier_chains.py', '/root/foodzuka/backend/app/scripts/migrate_vk_templates_courier_chains.py'),
    # Новая система уведомлений и рассылок (5 вкладок)
    ('backend/app/models/review.py', '/root/foodzuka/backend/app/models/review.py'),
    ('backend/app/models/reminder.py', '/root/foodzuka/backend/app/models/reminder.py'),
    ('backend/app/models/broadcast.py', '/root/foodzuka/backend/app/models/broadcast.py'),
    ('backend/app/models/message_log.py', '/root/foodzuka/backend/app/models/message_log.py'),
    ('backend/app/scripts/migrate_notification_system_tables.py', '/root/foodzuka/backend/app/scripts/migrate_notification_system_tables.py'),
    ('backend/app/api/reviews.py', '/root/foodzuka/backend/app/api/reviews.py'),
    ('backend/app/api/reminders.py', '/root/foodzuka/backend/app/api/reminders.py'),
    ('backend/app/api/broadcasts.py', '/root/foodzuka/backend/app/api/broadcasts.py'),
    ('backend/app/api/message_logs.py', '/root/foodzuka/backend/app/api/message_logs.py'),
    ('backend/app/api/link_tracker.py', '/root/foodzuka/backend/app/api/link_tracker.py'),
    ('backend/app/api/mailings.py', '/root/foodzuka/backend/app/api/mailings.py'),
    ('admin/resources/js/pages/mailings/notifications-and-mailings.vue', '/root/foodzuka/admin/resources/js/pages/mailings/notifications-and-mailings.vue'),
    ('backend/app/models/update_purchase_system.sql', '/root/foodzuka/backend/app/models/update_purchase_system.sql'),
    ('backend/app/models/update_purchase_system_v3.sql', '/root/foodzuka/backend/app/models/update_purchase_system_v3.sql'),
    ('backend/app/models/purchase.py', '/root/foodzuka/backend/app/models/purchase.py'),
    ('backend/app/api/purchase.py', '/root/foodzuka/backend/app/api/purchase.py'),
    ('admin/resources/styles/purchase.css', '/root/foodzuka/admin/resources/styles/purchase.css'),
    ('admin/resources/js/pages/purchase/index.vue', '/root/foodzuka/admin/resources/js/pages/purchase/index.vue'),
    ('admin/resources/js/pages/purchase/positions.vue', '/root/foodzuka/admin/resources/js/pages/purchase/positions.vue'),
    # Role permissions editor new/modified files
    ('backend/app/scripts/seed_rbac.py', '/root/foodzuka/backend/app/scripts/seed_rbac.py'),
    ('backend/app/api/max.py', '/root/foodzuka/backend/app/api/max.py'),
    ('backend/app/api/mailing_cascades.py', '/root/foodzuka/backend/app/api/mailing_cascades.py'),
    ('backend/app/api/system.py', '/root/foodzuka/backend/app/api/system.py'),
    ('backend/app/api/users.py', '/root/foodzuka/backend/app/api/users.py'),
    ('backend/app/api/reports.py', '/root/foodzuka/backend/app/api/reports.py'),
    ('admin/resources/js/pages/system/server.vue', '/root/foodzuka/admin/resources/js/pages/system/server.vue'),
    ('admin/resources/js/pages/reports/revenue.vue', '/root/foodzuka/admin/resources/js/pages/reports/revenue.vue'),
    ('admin/resources/js/pages/reports/sales.vue', '/root/foodzuka/admin/resources/js/pages/reports/sales.vue'),
    ('admin/resources/js/pages/reports/products.vue', '/root/foodzuka/admin/resources/js/pages/reports/products.vue'),
    ('admin/resources/js/pages/reports/days.vue', '/root/foodzuka/admin/resources/js/pages/reports/days.vue'),
    ('admin/resources/js/pages/reports/clients.vue', '/root/foodzuka/admin/resources/js/pages/reports/clients.vue'),
    ('admin/resources/js/pages/reports/payment_types.vue', '/root/foodzuka/admin/resources/js/pages/reports/payment_types.vue'),
    ('admin/resources/js/pages/employees.vue', '/root/foodzuka/admin/resources/js/pages/employees.vue'),
    ('backend/app/scripts/update_cooking_time_default.py', '/root/foodzuka/backend/app/scripts/update_cooking_time_default.py'),
    ('backend/app/scripts/add_cooking_time_updated_at.py', '/root/foodzuka/backend/app/scripts/add_cooking_time_updated_at.py'),
    ('backend/app/scripts/migrate_payment_qr_shares.py', '/root/foodzuka/backend/app/scripts/migrate_payment_qr_shares.py'),
    ('backend/app/scripts/add_ignored_ids_to_vk_settings.py', '/root/foodzuka/backend/app/scripts/add_ignored_ids_to_vk_settings.py'),
    # Kitchen System
    ('backend/app/models/product.py', '/root/foodzuka/backend/app/models/product.py'),
    ('backend/app/models/create_kitchen_tables.sql', '/root/foodzuka/backend/app/models/create_kitchen_tables.sql'),
    ('backend/app/scripts/apply_kitchen_migrations.py', '/root/foodzuka/backend/app/scripts/apply_kitchen_migrations.py'),
    ('backend/app/api/kitchen.py', '/root/foodzuka/backend/app/api/kitchen.py'),
    ('admin/resources/js/pages/kitchen/recipes.vue', '/root/foodzuka/admin/resources/js/pages/kitchen/recipes.vue'),
    ('admin/resources/js/pages/kitchen/screen.vue', '/root/foodzuka/admin/resources/js/pages/kitchen/screen.vue'),
    # VK Birthday Bots
    ('backend/app/models/vk_birthday_bot.py', '/root/foodzuka/backend/app/models/vk_birthday_bot.py'),
    ('backend/app/services/vk_birthday_service.py', '/root/foodzuka/backend/app/services/vk_birthday_service.py'),
    ('backend/app/api/vk_birthday_bots.py', '/root/foodzuka/backend/app/api/vk_birthday_bots.py'),
    ('backend/app/tasks/vk_birthday_task.py', '/root/foodzuka/backend/app/tasks/vk_birthday_task.py'),
    ('admin/resources/js/pages/marketing/vk-bots.vue', '/root/foodzuka/admin/resources/js/pages/marketing/vk-bots.vue'),
    ('backend/app/scripts/create_vk_birthday_bot_tables.py', '/root/foodzuka/backend/app/scripts/create_vk_birthday_bot_tables.py'),
    # VK Cover Bots
    ('backend/app/models/vk_cover_bot.py', '/root/foodzuka/backend/app/models/vk_cover_bot.py'),
    ('backend/app/services/vk_cover_service.py', '/root/foodzuka/backend/app/services/vk_cover_service.py'),
    ('backend/app/api/vk_cover_bots.py', '/root/foodzuka/backend/app/api/vk_cover_bots.py'),
    ('backend/app/tasks/vk_cover_task.py', '/root/foodzuka/backend/app/tasks/vk_cover_task.py'),
    ('backend/app/scripts/create_vk_cover_bot_tables.py', '/root/foodzuka/backend/app/scripts/create_vk_cover_bot_tables.py'),
    # VK Contest Bots
    ('backend/app/models/vk_contest.py', '/root/foodzuka/backend/app/models/vk_contest.py'),
    ('backend/app/services/vk_contest_service.py', '/root/foodzuka/backend/app/services/vk_contest_service.py'),
    ('backend/app/api/vk_contests.py', '/root/foodzuka/backend/app/api/vk_contests.py'),
    ('backend/app/scripts/create_vk_contest_tables.py', '/root/foodzuka/backend/app/scripts/create_vk_contest_tables.py'),
    ('backend/app/scripts/update_vk_contest_messages.py', '/root/foodzuka/backend/app/scripts/update_vk_contest_messages.py'),
    ('backend/app/tasks/vk_contest_reminders_task.py', '/root/foodzuka/backend/app/tasks/vk_contest_reminders_task.py'),
    ('backend/app/scripts/update_vk_contest_advanced_fields.py', '/root/foodzuka/backend/app/scripts/update_vk_contest_advanced_fields.py'),
    ('backend/app/scripts/update_vk_contest_battle_fields.py', '/root/foodzuka/backend/app/scripts/update_vk_contest_battle_fields.py'),
    ('backend/app/scripts/update_vk_contest_stats_tables.py', '/root/foodzuka/backend/app/scripts/update_vk_contest_stats_tables.py'),
    ('backend/app/scripts/update_vk_bot_connection_user_token.py', '/root/foodzuka/backend/app/scripts/update_vk_bot_connection_user_token.py'),
    ('backend/app/scripts/add_callback_fields_to_cover_bots.py', '/root/foodzuka/backend/app/scripts/add_callback_fields_to_cover_bots.py'),
    # VK Activity Bot
    ('backend/app/models/vk_activity_settings.py', '/root/foodzuka/backend/app/models/vk_activity_settings.py'),
    ('backend/app/services/vk_activity_service.py', '/root/foodzuka/backend/app/services/vk_activity_service.py'),
    ('backend/app/api/vk_activity_bots.py', '/root/foodzuka/backend/app/api/vk_activity_bots.py'),
    ('backend/app/scripts/create_vk_activity_tables.py', '/root/foodzuka/backend/app/scripts/create_vk_activity_tables.py'),
    ('backend/app/scripts/add_ignored_post_ids_to_activity_settings.py', '/root/foodzuka/backend/app/scripts/add_ignored_post_ids_to_activity_settings.py'),
    # VK First Comment Bot & Custom Bot Tokens
    ('backend/app/models/vk_first_comment_settings.py', '/root/foodzuka/backend/app/models/vk_first_comment_settings.py'),
    ('backend/app/api/vk_first_comment_bots.py', '/root/foodzuka/backend/app/api/vk_first_comment_bots.py'),
    ('backend/app/services/vk_first_comment_service.py', '/root/foodzuka/backend/app/services/vk_first_comment_service.py'),
    ('backend/app/services/vk_bot_service.py', '/root/foodzuka/backend/app/services/vk_bot_service.py'),
    ('backend/app/scripts/migrate_vk_bot_token_v4.py', '/root/foodzuka/backend/app/scripts/migrate_vk_bot_token_v4.py'),
    # Senler Integration
    ('backend/app/models/senler.py', '/root/foodzuka/backend/app/models/senler.py'),
    ('backend/app/services/senler_service.py', '/root/foodzuka/backend/app/services/senler_service.py'),
    ('backend/app/tasks/senler_tasks.py', '/root/foodzuka/backend/app/tasks/senler_tasks.py'),
    ('backend/app/api/senler.py', '/root/foodzuka/backend/app/api/senler.py'),
    ('backend/app/scripts/create_senler_tables.py', '/root/foodzuka/backend/app/scripts/create_senler_tables.py'),
    ('admin/resources/js/pages/settings/senler.vue', '/root/foodzuka/admin/resources/js/pages/settings/senler.vue'),
    # Validation Integration
    ('backend/app/models/validation_settings.py', '/root/foodzuka/backend/app/models/validation_settings.py'),
    ('backend/app/services/validation_service.py', '/root/foodzuka/backend/app/services/validation_service.py'),
    ('backend/app/api/validation.py', '/root/foodzuka/backend/app/api/validation.py'),
    ('backend/app/scripts/create_validation_tables.py', '/root/foodzuka/backend/app/scripts/create_validation_tables.py'),
    ('admin/resources/js/pages/settings/validation.vue', '/root/foodzuka/admin/resources/js/pages/settings/validation.vue'),
    ('backend/app/scripts/seed_rbac.py', '/root/foodzuka/backend/app/scripts/seed_rbac.py'),
    ('backend/app/scripts/add_vk_verification_fields.py', '/root/foodzuka/backend/app/scripts/add_vk_verification_fields.py'),
]

def ensure_remote_dirs():
    print("Ensuring remote directories exist...")
    dirs = [
      "/root/foodzuka/admin/resources/js/stores",
      "/root/foodzuka/admin/resources/js/components",
      "/root/foodzuka/admin/resources/js/pages/mailings",
      "/root/foodzuka/admin/resources/js/pages/bank",
      "/root/foodzuka/admin/resources/js/pages/purchase",
      "/root/foodzuka/admin/resources/js/pages/kitchen",
      "/root/foodzuka/admin/resources/js/pages/marketing",
      "/root/foodzuka/admin/resources/js/pages/multichat",
      "/root/foodzuka/admin/public/sounds",
    ]
    for d in dirs:
        cmd = f'ssh vezuroll "mkdir -p {d}"'
        subprocess.run(cmd, shell=True)

def sync_file(local_path, remote_path):
    print(f"Syncing {local_path} -> {remote_path}")
    cmd = f'scp {local_path} vezuroll:{remote_path}'
    subprocess.run(cmd, shell=True)

def rebuild_frontend():
    print("Rebuilding frontend...")
    cmd = 'ssh vezuroll "cd foodzuka/admin && npm run build:icons && npm run build"'
    subprocess.run(cmd, shell=True)

def clear_cache():
    print("Cleaning cache...")
    cmd = 'ssh vezuroll "docker exec -t foodtech-admin php artisan optimize:clear"'
    subprocess.run(cmd, shell=True)

def run_migrations():
    print("Running database migrations...")
    cmd = 'ssh vezuroll "docker exec -t foodtech-backend alembic upgrade head"'
    subprocess.run(cmd, shell=True)
    
    print("Running bot commands database migration...")
    cmd_commands = 'ssh vezuroll "docker exec -t foodtech-backend python /app/migrate_bot_commands.py"'
    subprocess.run(cmd_commands, shell=True)
    
    print("Running VK multibot tables creation & migration...")
    cmd_vk = 'ssh vezuroll "docker exec -t foodtech-backend python /app/app/scripts/create_vk_bot_tables.py"'
    subprocess.run(cmd_vk, shell=True)

    print("Running notification channels migration...")
    cmd_channels = 'ssh vezuroll "docker exec -t foodtech-backend python /app/app/scripts/migrate_notifications_channels.py"'
    subprocess.run(cmd_channels, shell=True)

    print("Running notification system overhaul tables migration...")
    cmd_system = 'ssh vezuroll "docker exec -t foodtech-backend python /app/app/scripts/migrate_notification_system_tables.py"'
    subprocess.run(cmd_system, shell=True)

    print("Running notification database tables migration...")
    cmd_notif = 'ssh vezuroll "docker exec -t foodtech-backend python /app/create_notification_tables.py"'
    subprocess.run(cmd_notif, shell=True)

    print("Running admin notifications database table migration...")
    cmd_admin_notif = 'ssh vezuroll "docker exec -t foodtech-backend python /app/create_admin_notifications_table.py"'
    subprocess.run(cmd_admin_notif, shell=True)

    print("Downloading notification sounds...")
    cmd_sounds = 'ssh vezuroll "docker exec -t foodtech-backend python /app/download_sounds.py"'
    subprocess.run(cmd_sounds, shell=True)

    print("Running RBAC seeding with granular permissions...")
    cmd_rbac = 'ssh vezuroll "docker exec -t foodtech-backend python /app/app/scripts/seed_rbac.py"'
    subprocess.run(cmd_rbac, shell=True)

    print("Running database update for cooking_time_minutes...")
    cmd_cooking = 'ssh vezuroll "docker exec -t foodtech-backend python -m app.scripts.update_cooking_time_default"'
    subprocess.run(cmd_cooking, shell=True)

    print("Running database update to add cooking_time_updated_at...")
    cmd_cooking_time = 'ssh vezuroll "docker exec -t foodtech-backend python -m app.scripts.add_cooking_time_updated_at"'
    subprocess.run(cmd_cooking_time, shell=True)

def restart_containers():
    print("Restarting containers...")
    cmd = 'ssh vezuroll "cd foodzuka && docker compose restart backend worker nginx"'
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    # Динамически добавляем новые и измененные файлы проекта
    files_to_sync.extend([
        ('backend/app/models/product.py', '/root/foodzuka/backend/app/models/product.py'),
        ('backend/app/models/category.py', '/root/foodzuka/backend/app/models/category.py'),
        ('backend/app/api/categories.py', '/root/foodzuka/backend/app/api/categories.py'),
        ('backend/app/api/products.py', '/root/foodzuka/backend/app/api/products.py'),
        ('backend/app/services/iiko_sync_service.py', '/root/foodzuka/backend/app/services/iiko_sync_service.py'),
        ('backend/app/schemas/__init__.py', '/root/foodzuka/backend/app/schemas/__init__.py'),
        ('admin/resources/js/pages/menu/categories.vue', '/root/foodzuka/admin/resources/js/pages/menu/categories.vue'),
        ('admin/resources/js/pages/menu/products.vue', '/root/foodzuka/admin/resources/js/pages/menu/products.vue'),
        ('frontend/src/views/Home.vue', '/root/foodzuka/frontend/src/views/Home.vue'),
        ('frontend/src/views/Cart.vue', '/root/foodzuka/frontend/src/views/Cart.vue'),
        ('backend/app/scripts/migrate_category_locks_and_tags.py', '/root/foodzuka/backend/app/scripts/migrate_category_locks_and_tags.py'),
        ('backend/app/scripts/migrate_category_hierarchy_and_hiding.py', '/root/foodzuka/backend/app/scripts/migrate_category_hierarchy_and_hiding.py')
    ])
    ensure_remote_dirs()
    for local, remote in files_to_sync:
        if os.path.exists(local):
            sync_file(local, remote)
        else:
            print(f"Warning: Local file {local} not found.")
    
    # run_migrations()  # Отключено для ускорения и избежания сетевых таймаутов на VPS
    print("Running payment QR shares migration on VPS...")
    cmd_migrate = 'ssh vezuroll "docker exec -t foodtech-backend python /app/app/scripts/migrate_payment_qr_shares.py"'
    subprocess.run(cmd_migrate, shell=True)
    
    print("Running VK ignored IDs migration on VPS...")
    cmd_ignored = 'ssh vezuroll "docker exec -t foodtech-backend python /app/app/scripts/add_ignored_ids_to_vk_settings.py"'
    subprocess.run(cmd_ignored, shell=True)
    
    print("Running Kitchen Database migrations on VPS...")
    cmd_kitchen_migrate = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/apply_kitchen_migrations.py"'
    subprocess.run(cmd_kitchen_migrate, shell=True)

    print("Running RBAC seeding on VPS...")
    cmd_rbac = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/seed_rbac.py"'
    subprocess.run(cmd_rbac, shell=True)

    print("Running VK Birthday Bot tables creation on VPS...")
    cmd_vk_bday = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/create_vk_birthday_bot_tables.py"'
    subprocess.run(cmd_vk_bday, shell=True)
    
    print("Running VK Cover Bot tables creation on VPS...")
    cmd_vk_cover = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/create_vk_cover_bot_tables.py"'
    subprocess.run(cmd_vk_cover, shell=True)

    print("Running VK Contest Bot tables creation on VPS...")
    cmd_vk_contest = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/create_vk_contest_tables.py"'
    subprocess.run(cmd_vk_contest, shell=True)

    print("Running VK Contest message fields migration on VPS...")
    cmd_vk_contest_msg = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/update_vk_contest_messages.py"'
    subprocess.run(cmd_vk_contest_msg, shell=True)

    print("Running VK Contest advanced settings fields migration on VPS...")
    cmd_vk_contest_adv = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/update_vk_contest_advanced_fields.py"'
    subprocess.run(cmd_vk_contest_adv, shell=True)

    print("Running VK Contest beach battle fields migration on VPS...")
    cmd_vk_contest_battle = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/update_vk_contest_battle_fields.py"'
    subprocess.run(cmd_vk_contest_battle, shell=True)

    print("Running VK Contest stats tables migration on VPS...")
    cmd_vk_contest_stats = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/update_vk_contest_stats_tables.py"'
    subprocess.run(cmd_vk_contest_stats, shell=True)

    print("Running VK Bot Connection user token migration on VPS...")
    cmd_vk_user_token_mig = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/update_vk_bot_connection_user_token.py"'
    subprocess.run(cmd_vk_user_token_mig, shell=True)

    print("Running VK Cover Bot advanced update and callback fields migration on VPS...")
    cmd_vk_cover_callback_mig = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/add_callback_fields_to_cover_bots.py"'
    subprocess.run(cmd_vk_cover_callback_mig, shell=True)

    print("Running VK Activity Bot tables creation on VPS...")
    cmd_vk_activity = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/create_vk_activity_tables.py"'
    subprocess.run(cmd_vk_activity, shell=True)

    print("Running VK Activity Bot ignored posts migration on VPS...")
    cmd_vk_activity_ignored = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/add_ignored_post_ids_to_activity_settings.py"'
    subprocess.run(cmd_vk_activity_ignored, shell=True)

    print("Running VK Custom Bot Tokens Database Migration v4 on VPS...")
    cmd_vk_mig_v4 = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/migrate_vk_bot_token_v4.py"'
    subprocess.run(cmd_vk_mig_v4, shell=True)
    
    print("Running Senler database tables creation on VPS...")
    cmd_senler_tables = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/create_senler_tables.py"'
    subprocess.run(cmd_senler_tables, shell=True)
    
    print("Running Validation database tables creation & seeding on VPS...")
    cmd_val_tables = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/create_validation_tables.py"'
    subprocess.run(cmd_val_tables, shell=True)
    
    print("Running VK validation fields migration on VPS...")
    cmd_vk_fields = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/add_vk_verification_fields.py"'
    subprocess.run(cmd_vk_fields, shell=True)
    
    print("Running VK Bot use_longpoll migration on VPS...")
    cmd_vk_longpoll = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/add_use_longpoll_to_vk_connections.py"'
    subprocess.run(cmd_vk_longpoll, shell=True)
    
    print("Running VK Post Scheduler tables creation on VPS...")
    cmd_vk_scheduler = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/create_vk_scheduler_tables.py"'
    subprocess.run(cmd_vk_scheduler, shell=True)
    
    print("Running locks and tags db migrations on VPS...")
    cmd_locks_tags = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/migrate_category_locks_and_tags.py"'
    subprocess.run(cmd_locks_tags, shell=True)

    print("Running hierarchy and hiding db migrations on VPS...")
    cmd_hierarchy_hiding = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/migrate_category_hierarchy_and_hiding.py"'
    subprocess.run(cmd_hierarchy_hiding, shell=True)

    print("Running VK Activity Penalty Timers migration on VPS...")
    cmd_vk_penalty = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/migrate_vk_activity_penalty_timers.py"'
    subprocess.run(cmd_vk_penalty, shell=True)

    print("Running Multichat database tables creation on VPS...")
    cmd_multichat = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/create_multichat_tables.py"'
    subprocess.run(cmd_multichat, shell=True)

    print("Running Multichat Tags database tables creation on VPS...")
    cmd_multichat_tags = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/create_multichat_tags_tables.py"'
    subprocess.run(cmd_multichat_tags, shell=True)

    print("Running Multichat Accounts database tables creation on VPS...")
    cmd_multichat_accounts = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/create_multichat_accounts_tables.py"'
    subprocess.run(cmd_multichat_accounts, shell=True)

    print("Running iiko Developer fields db migration on VPS...")
    cmd_iiko_dev = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/migrate_iiko_dev_fields.py"'
    subprocess.run(cmd_iiko_dev, shell=True)

    print("Running Courier Chains vk_templates db migration on VPS...")
    cmd_courier_chains = 'ssh vezuroll "docker exec -t foodtech-backend env PYTHONPATH=/app python /app/app/scripts/migrate_vk_templates_courier_chains.py"'
    subprocess.run(cmd_courier_chains, shell=True)

    rebuild_frontend()
    clear_cache()
    restart_containers()
    print("Sync and Rebuild complete!")
