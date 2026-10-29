import { createRouter, createWebHistory } from 'vue-router'
import { routes as adminRoutes } from './routes'
import { routes as employeeRoutes } from './employee_routes'
import { authState, fetchMe, hasPermission } from '@/utils/auth'

const path = window.location.pathname
const isEmployeePath = path.startsWith('/pers')

console.log('[Router] Path:', path, 'isEmployee:', isEmployeePath)

const router = createRouter({
  history: createWebHistory(isEmployeePath ? '/pers/' : '/admin/'),
  routes: isEmployeePath ? employeeRoutes : adminRoutes,
})

router.beforeEach(async (to, from, next) => {
  const publicPages = ['/login', '/register', '/error']
  const authRequired = !publicPages.includes(to.path)

  console.log('[Router] Navigating to:', to.path, 'Auth required:', authRequired)

  if (authRequired && !authState.token) {
    console.log('[Router] Auth required but no token, redirecting to /login')
    return next('/login')
  }

  if (authState.token && !authState.user && to.path !== '/login') {
    await fetchMe()
    if (!authState.user && authRequired) {
      console.log('[Router] Session expired or user unavailable during fetchMe, redirecting to /login')
      return next('/login')
    }
  }

  // Перенаправление на страницу роли по умолчанию при входе или первом открытии
  if (authState.user && (to.path === '/' || to.path === '/dashboard')) {
    const defaultPage = authState.user.role?.default_page
    if (defaultPage && defaultPage !== to.path) {
      const isInitialOrLogin = from.path === '/login' || from.path === '/' || !from.name
      if (isInitialOrLogin) {
        console.log('[Router] Redirecting to user role default page:', defaultPage)
        return next(defaultPage)
      }
    }
  }

  // Проверка гранулярных прав
  if (authState.user && to.meta && to.meta.permission) {
    let allowed = hasPermission(to.meta.permission)
    
    // Специальный доступ для курьеров (если привязан iiko_id курьера)
    if (!allowed && to.meta.allowCourier) {
      if (authState.user.iiko_id || authState.user.employee?.iiko_id) {
        allowed = true
      }
    }

    if (!allowed) {
      console.warn(`[Router] Access denied to ${to.path}. Required: ${to.meta.permission}`)
      
      // Перенаправляем на разрешенную страницу
      if (hasPermission('dashboard_view') && to.path !== '/dashboard') {
        return next('/dashboard')
      } else if (to.path !== '/account-settings') {
        return next('/account-settings')
      } else {
        return next('/login')
      }
    }
  }

  next()
})

export default function (app) {
  app.use(router)
}
export { router }
