export const routes = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/',
    component: () => import('@/layouts/default.vue'),
    children: [
      {
        path: 'dashboard',
        component: () => import('@/pages/dashboard.vue'),
        meta: { permission: 'dashboard_view' }
      },
      {
        path: 'orders',
        component: () => import('@/pages/orders/index.vue'),
        meta: { permission: 'orders_view' }
      },
      {
        path: 'multichat',
        component: () => import('@/pages/multichat/index.vue'),
        meta: { permission: 'multichat_view' }
      },
      {
        path: 'notifications-feed',
        name: 'notifications-feed',
        component: () => import('@/pages/notifications-feed/index.vue'),
        meta: { permission: 'notifications_feed_view' }
      },
      {
        path: 'courier',
        component: () => import('@/pages/employee/courier.vue'),
        meta: { permission: 'courier_view', allowCourier: true }
      },
      {
        path: 'companies',
        component: () => import('@/pages/companies.vue'),
        meta: { permission: 'companies_view' }
      },
      {
        path: 'menu/products',
        component: () => import('@/pages/menu/products.vue'),
        meta: { permission: 'menu_products_view' }
      },
      {
        path: 'menu/categories',
        component: () => import('@/pages/menu/categories.vue'),
        meta: { permission: 'menu_categories_view' }
      },
      {
        path: 'menu/options',
        component: () => import('@/pages/menu/options.vue'),
        meta: { permission: 'menu_options_view' }
      },
      {
        path: 'menu/import',
        component: () => import('@/pages/menu/import.vue'),
        meta: { permission: 'menu_import_view' }
      },
      {
        path: 'kitchen/recipes',
        component: () => import('@/pages/kitchen/recipes.vue'),
        meta: { permission: 'kitchen_recipes_view' }
      },
      {
        path: 'kitchen/screen',
        component: () => import('@/pages/kitchen/screen.vue'),
        meta: { permission: 'kitchen_screen_view' }
      },
      {
        path: 'purchase',
        component: () => import('@/pages/purchase/index.vue'),
        meta: { permission: 'purchase_lists_view' }
      },
      {
        path: 'purchase/positions',
        component: () => import('@/pages/purchase/positions.vue'),
        meta: { permission: 'purchase_positions_view' }
      },
      {
        path: 'ai-chat',
        name: 'ai-chat',
        component: () => import('@/pages/ai-chat/index.vue'),
        meta: { permission: 'settings_ai_agents_view' }
      },
      {
        path: 'ai-agents',
        name: 'ai-agents',
        redirect: '/ai-chat'
      },
      {
        path: 'settings/ai-agents',
        name: 'settings-ai-agents',
        component: () => import('@/pages/settings/ai-agents.vue'),
        meta: { permission: 'settings_ai_agents_view' }
      },
      {
        path: 'settings/ai-assistants',
        name: 'settings-ai-assistants',
        component: () => import('@/pages/settings/ai-assistants.vue'),
        meta: { permission: 'settings_ai_agents_view' }
      },
      {
        path: 'settings/iiko',
        component: () => import('@/pages/settings/iiko.vue'),
        meta: { permission: 'settings_iiko_view' }
      },
      {
        path: 'settings/notifications',
        component: () => import('@/pages/settings/notifications.vue'),
        meta: { permission: 'settings_notifications_view' }
      },
      {
        path: 'settings/bot',
        component: () => import('@/pages/settings/bot.vue'),
        meta: { permission: 'settings_bot_view' }
      },
      {
        path: 'settings/vk',
        component: () => import('@/pages/settings/vk.vue'),
        meta: { permission: 'settings_vk_view' }
      },
      {
        path: 'settings/vk-notifications',
        component: () => import('@/pages/settings/vk-notifications_utf8.vue'),
        meta: { permission: 'settings_vk_notifications_view' }
      },
      {
        path: 'settings/vk-parser',
        name: 'settings-vk-parser',
        component: () => import('@/pages/settings/vk-parser.vue'),
        meta: { permission: 'settings_vk_parser_view' }
      },
      {
        path: 'settings/senler',
        name: 'settings-senler',
        component: () => import('@/pages/settings/senler.vue'),
        meta: { permission: 'settings_senler_view' }
      },
      {
        path: 'settings/yandex',
        component: () => import('@/pages/settings/yandex.vue'),
        meta: { permission: 'settings_yandex_view' }
      },
      {
        path: 'settings/tbank',
        component: () => import('@/pages/settings/tbank.vue'),
        meta: { permission: 'settings_tbank_view' }
      },
      {
        path: 'settings/mango',
        name: 'settings-mango',
        component: () => import('@/pages/settings/mango.vue'),
        meta: { permission: 'settings_mango_view' }
      },
      {
        path: 'settings/validation',
        component: () => import('@/pages/settings/validation.vue'),
        meta: { permission: 'settings_validation_view' }
      },
      {
        path: 'settings/max',
        component: () => import('@/pages/settings/max.vue'),
        meta: { permission: 'settings_max_view' }
      },
      {
        path: 'settings/bot-commands',
        component: () => import('@/pages/settings/bot-commands.vue'),
        meta: { permission: 'settings_bot_commands_view' }
      },
      {
        path: 'mailings/cascades',
        component: () => import('@/pages/mailings/notifications-and-mailings.vue'),
        meta: { permission: 'mailings_cascades_view' }
      },
      {
        path: 'bank/payments',
        component: () => import('@/pages/bank/payments.vue'),
        meta: { permission: 'bank_payments_view' }
      },
      {
        path: 'bank/tbank-payments',
        component: () => import('@/pages/bank/tbank-payments.vue'),
        meta: { permission: 'bank_tbank_payments_view' }
      },
      {
        path: 'settings/sync-logs',
        component: () => import('@/pages/settings/sync-logs.vue'),
        meta: { permission: 'settings_sync_logs_view' }
      },
      {
        path: 'system/logs',
        component: () => import('@/pages/system/logs.vue'),
        meta: { permission: 'system_logs_view' }
      },
      {
        path: 'system/tasks',
        component: () => import('@/pages/system/tasks.vue'),
        meta: { permission: 'system_tasks_view' }
      },
      {
        path: 'system/backups',
        name: 'system-backups',
        component: () => import('@/pages/system/backups.vue'),
        meta: { permission: 'system_server_view' }
      },
      {
        path: 'system/server',
        component: () => import('@/pages/system/server.vue'),
        meta: { permission: 'system_server_view' }
      },
      {
        path: 'loyalty',
        component: () => import('@/pages/loyalty/index.vue'),
        meta: { permission: 'loyalty_view' }
      },
      {
        path: 'marketing/vk-bots',
        component: () => import('@/pages/marketing/vk-bots.vue'),
        meta: { permission: 'marketing_vk_bots_view' }
      },
      {
        path: 'marketing/vk-scheduler',
        component: () => import('@/pages/marketing/vk-scheduler.vue'),
        meta: { permission: 'marketing_vk_scheduler_view' }
      },
      {
        path: 'marketing/group-posting',
        name: 'marketing-group-posting',
        component: () => import('@/pages/marketing/group-posting.vue'),
        meta: { permission: 'marketing_group_posting_view' }
      },
      {
        path: 'branches',
        component: () => import('@/pages/branches/index.vue'),
        meta: { permission: 'branches_view' }
      },
      {
        path: 'branches/zones',
        component: () => import('@/pages/branches/zones.vue'),
        meta: { permission: 'zones_view' }
      },
      {
        path: 'promo',
        component: () => import('@/pages/promo/index.vue'),
        meta: { permission: 'promo_codes_view' }
      },
      {
        path: 'users',
        component: () => import('@/pages/users.vue'),
        meta: { permission: 'users_view' }
      },
      {
        path: 'employees',
        component: () => import('@/pages/employees.vue'),
        meta: { permission: 'employees_view' }
      },
      {
        path: 'clients',
        component: () => import('@/pages/clients/index.vue'),
        meta: { permission: 'clients_view' }
      },
      {
        path: 'account-settings',
        component: () => import('@/pages/account-settings.vue'),
      },
      {
        path: 'reports/revenue',
        component: () => import('@/pages/reports/revenue.vue'),
        meta: { permission: 'reports_view' }
      },
      {
        path: 'reports/sales',
        component: () => import('@/pages/reports/sales.vue'),
        meta: { permission: 'reports_view' }
      },
      {
        path: 'reports/products',
        component: () => import('@/pages/reports/products.vue'),
        meta: { permission: 'reports_view' }
      },
      {
        path: 'reports/days',
        component: () => import('@/pages/reports/days.vue'),
        meta: { permission: 'reports_view' }
      },
      {
        path: 'reports/clients',
        component: () => import('@/pages/reports/clients.vue'),
        meta: { permission: 'reports_view' }
      },
      {
        path: 'reports/orders',
        component: () => import('@/pages/reports/orders.vue'),
        meta: { permission: 'reports_view' }
      },
      {
        path: 'reports/payments',
        component: () => import('@/pages/reports/payment_types.vue'),
        meta: { permission: 'reports_view' }
      },
    ],
  },
  {
    path: '/',
    component: () => import('@/layouts/blank.vue'),
    children: [
      {
        path: 'login',
        component: () => import('@/pages/login.vue'),
      },
      {
        path: 'register',
        component: () => import('@/pages/register.vue'),
      },
      {
        path: '/:pathMatch(.*)*',
        component: () => import('@/pages/[...error].vue'),
      },
    ],
  },
]
