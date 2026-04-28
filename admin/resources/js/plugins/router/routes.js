export const routes = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/',
    component: () => import('@/layouts/default.vue'),
    children: [
      {
        path: 'dashboard',
        component: () => import('@/pages/dashboard.vue'),
      },
      {
        path: 'orders',
        component: () => import('@/pages/orders/index.vue'),
      },
      {
        path: 'companies',
        component: () => import('@/pages/companies.vue'),
      },
      {
        path: 'menu/products',
        component: () => import('@/pages/menu/products.vue'),
      },
      {
        path: 'menu/categories',
        component: () => import('@/pages/menu/categories.vue'),
      },
      {
        path: 'menu/options',
        component: () => import('@/pages/menu/options.vue'),
      },
      {
        path: 'menu/import',
        component: () => import('@/pages/menu/import.vue'),
      },
      {
        path: 'settings/iiko',
        component: () => import('@/pages/settings/iiko.vue'),
      },
      {
        path: 'settings/bot',
        component: () => import('@/pages/settings/bot.vue'),
      },
      {
        path: 'settings/vk',
        component: () => import('@/pages/settings/vk.vue'),
      },
      {
        path: 'settings/vk-notifications',
        component: () => import('@/pages/settings/vk-notifications_utf8.vue'),
      },
      {
        path: 'settings/yandex',
        component: () => import('@/pages/settings/yandex.vue'),
      },

      {
        path: 'settings/sync-logs',
        component: () => import('@/pages/settings/sync-logs.vue'),
      },
      {
        path: 'system/logs',
        component: () => import('@/pages/system/logs.vue'),
      },
      {
        path: 'system/tasks',
        component: () => import('@/pages/system/tasks.vue'),
      },
      {
        path: 'loyalty',
        component: () => import('@/pages/loyalty/index.vue'),
      },
      {
        path: 'branches',
        component: () => import('@/pages/branches/index.vue'),
      },
      {
        path: 'branches/zones',
        component: () => import('@/pages/branches/zones.vue'),
      },
      {
        path: 'promo',
        component: () => import('@/pages/promo/index.vue'),
      },
      {
        path: 'users',
        component: () => import('@/pages/users.vue'),
      },
      {
        path: 'employees',
        component: () => import('@/pages/employees.vue'),
      },
      {
        path: 'clients',
        component: () => import('@/pages/clients/index.vue'),
      },
      {
        path: 'account-settings',
        component: () => import('@/pages/account-settings.vue'),
      },
      {
        path: 'reports/revenue',
        component: () => import('@/pages/reports/revenue.vue'),
      },
      {
        path: 'reports/sales',
        component: () => import('@/pages/reports/sales.vue'),
      },
      {
        path: 'reports/products',
        component: () => import('@/pages/reports/products.vue'),
      },
      {
        path: 'reports/days',
        component: () => import('@/pages/reports/days.vue'),
      },
      {
        path: 'reports/clients',
        component: () => import('@/pages/reports/clients.vue'),
      },
      {
        path: 'reports/orders',
        component: () => import('@/pages/reports/orders.vue'),
      },
      {
        path: 'reports/payments',
        component: () => import('@/pages/reports/payment_types.vue'),
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
