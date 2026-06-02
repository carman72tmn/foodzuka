import os
import subprocess

# Files to sync: (local_path, remote_path)
files_to_sync = [
    ('backend/app/services/iiko_service.py', '/root/foodzuka/backend/app/services/iiko_service.py'),
    ('backend/app/services/iiko_sync_service.py', '/root/foodzuka/backend/app/services/iiko_sync_service.py'),
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
    ('admin/resources/js/pages/settings/vk.vue', '/root/foodzuka/admin/resources/js/pages/settings/vk.vue'),
    ('admin/resources/js/pages/loyalty/index.vue', '/root/foodzuka/admin/resources/js/pages/loyalty/index.vue'),
    ('admin/resources/js/pages/settings/sync-logs.vue', '/root/foodzuka/admin/resources/js/pages/settings/sync-logs.vue'),
    ('admin/resources/js/pages/reports/orders.vue', '/root/foodzuka/admin/resources/js/pages/reports/orders.vue'),
    ('backend/app/models/iiko_loyalty.py', '/root/foodzuka/backend/app/models/iiko_loyalty.py'),
    ('backend/app/models/iiko_settings.py', '/root/foodzuka/backend/app/models/iiko_settings.py'),
    ('Service_info/system_faq.md', '/root/foodzuka/Service_info/system_faq.md'),
    ('Service_info/sql_faq.md', '/root/foodzuka/Service_info/sql_faq.md'),
    ('Service_info/sitenav.md', '/root/foodzuka/Service_info/sitenav.md'),
    ('backend/app/schemas/__init__.py', '/root/foodzuka/backend/app/schemas/__init__.py'),
    ('bot/handlers/__init__.py', '/root/foodzuka/bot/handlers/__init__.py'),
    ('bot/utils/date_utils.py', '/root/foodzuka/bot/utils/date_utils.py'),
    ('bot/requirements.txt', '/root/foodzuka/bot/requirements.txt'),
    ('docker-compose.prod.yml', '/root/foodzuka/docker-compose.prod.yml'),
    ('configs/nginx/default.conf', '/root/foodzuka/configs/nginx/default.conf'),
    ('trash/test_loyalty_sync.py', '/root/foodzuka/test_loyalty_sync.py'),
    ('backend/app/services/revenue_sync.py', '/root/foodzuka/backend/app/services/revenue_sync.py'),
    ('backend/app/api/courier.py', '/root/foodzuka/backend/app/api/courier.py'),
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
    ('backend/app/services/force_sync_186.py', '/root/foodzuka/backend/app/services/force_sync_186.py'),
    ('backend/app/core/config.py', '/root/foodzuka/backend/app/core/config.py'),
    ('backend/app/core/security.py', '/root/foodzuka/backend/app/core/security.py'),
    ('admin/resources/js/utils/auth.js', '/root/foodzuka/admin/resources/js/utils/auth.js'),
    ('admin/resources/js/pages/login.vue', '/root/foodzuka/admin/resources/js/pages/login.vue'),
    ('admin/resources/js/plugins/router/index.js', '/root/foodzuka/admin/resources/js/plugins/router/index.js'),
    ('admin/resources/js/views/pages/users/UserList.vue', '/root/foodzuka/admin/resources/js/views/pages/users/UserList.vue'),
    ('admin/resources/js/views/pages/users/RoleList.vue', '/root/foodzuka/admin/resources/js/views/pages/users/RoleList.vue'),
    ('backend/app/models/vk_settings.py', '/root/foodzuka/backend/app/models/vk_settings.py'),
    ('backend/app/models/vk_user.py', '/root/foodzuka/backend/app/models/vk_user.py'),
    ('backend/app/models/vk_message.py', '/root/foodzuka/backend/app/models/vk_message.py'),
    ('backend/app/services/vk_service.py', '/root/foodzuka/backend/app/services/vk_service.py'),
    ('backend/app/api/vk.py', '/root/foodzuka/backend/app/api/vk.py'),
    ('admin/resources/js/layouts/components/NavItems.vue', '/root/foodzuka/admin/resources/js/layouts/components/NavItems.vue'),
    ('admin/resources/js/plugins/router/routes.js', '/root/foodzuka/admin/resources/js/plugins/router/routes.js'),
    ('admin/resources/js/pages/settings/vk-parser.vue', '/root/foodzuka/admin/resources/js/pages/settings/vk-parser.vue'),
    ('backend/app/tasks/vk_parser_tasks.py', '/root/foodzuka/backend/app/tasks/vk_parser_tasks.py'),
    # MAX integration
    ('backend/app/models/max_settings.py', '/root/foodzuka/backend/app/models/max_settings.py'),
    ('backend/app/api/max.py', '/root/foodzuka/backend/app/api/max.py'),
    ('admin/resources/js/pages/settings/max.vue', '/root/foodzuka/admin/resources/js/pages/settings/max.vue'),
    # Mailing Cascades
    ('backend/app/models/mailing_cascade.py', '/root/foodzuka/backend/app/models/mailing_cascade.py'),
    ('backend/app/api/mailing_cascades.py', '/root/foodzuka/backend/app/api/mailing_cascades.py'),
    ('backend/app/services/mailing_cascade_service.py', '/root/foodzuka/backend/app/services/mailing_cascade_service.py'),
    ('backend/app/tasks/mailing_tasks.py', '/root/foodzuka/backend/app/tasks/mailing_tasks.py'),
    ('backend/app/schemas/mailing_cascade.py', '/root/foodzuka/backend/app/schemas/mailing_cascade.py'),
    ('admin/resources/js/pages/mailings/cascades.vue', '/root/foodzuka/admin/resources/js/pages/mailings/cascades.vue'),
    ('backend/alembic/versions/2026_05_13_2230_add_cascades_and_max.py', '/root/foodzuka/backend/alembic/versions/2026_05_13_2230_add_cascades_and_max.py'),
]

def ensure_remote_dirs():
    print("Ensuring remote directories exist...")
    dirs = [
        "/root/foodzuka/admin/resources/js/stores",
        "/root/foodzuka/admin/resources/js/components",
        "/root/foodzuka/admin/resources/js/pages/mailings",
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
    cmd = 'ssh vezuroll "cd foodzuka/admin && npm run build"'
    subprocess.run(cmd, shell=True)

def clear_cache():
    print("Cleaning cache...")
    cmd = 'ssh vezuroll "docker exec -t foodtech-admin php artisan optimize:clear"'
    subprocess.run(cmd, shell=True)

def run_migrations():
    print("Running database migrations...")
    cmd = 'ssh vezuroll "docker exec -t foodtech-backend alembic upgrade head"'
    subprocess.run(cmd, shell=True)

def restart_containers():
    print("Restarting containers...")
    cmd = 'ssh vezuroll "cd foodzuka && docker compose restart backend worker nginx"'
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    ensure_remote_dirs()
    for local, remote in files_to_sync:
        if os.path.exists(local):
            sync_file(local, remote)
        else:
            print(f"Warning: Local file {local} not found.")
    
    run_migrations()
    rebuild_frontend()
    clear_cache()
    restart_containers()
    print("Sync, Migrate and Rebuild complete!")
