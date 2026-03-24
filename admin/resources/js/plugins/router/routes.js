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
        path: 'menu/products',
        component: () => import('@/pages/menu/products.vue'),
      },
      {
        path: 'menu/categories',
        component: () => import('@/pages/menu/categories.vue'),
      },
      {
        path: 'settings/iiko',
        component: () => import('@/pages/settings/iiko.vue'),
      },
      {
        path: 'settings/vk',
        component: () => import('@/pages/settings/vk.vue'),
      },
      {
        path: 'settings/sync-logs',
        component: () => import('@/pages/settings/sync-logs.vue'),
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
        path: 'account-settings',
        component: () => import('@/pages/account-settings.vue'),
      },
      {
        path: 'reports/revenue',
        component: () => import('@/pages/reports/revenue.vue'),
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
