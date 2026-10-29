import { routes as adminRoutes } from './routes'

// Маршруты панели сотрудников на базе общих маршрутов с переопределением dashboard на специализированный
export const routes = adminRoutes.map(group => {
  if (group.children) {
    return {
      ...group,
      children: group.children.map(child => {
        if (child.path === 'dashboard') {
          return {
            ...child,
            component: () => import('@/pages/employee/dashboard.vue'),
          }
        }
        return child
      }),
    }
  }
  return group
})

