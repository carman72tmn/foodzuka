import { createRouter, createWebHistory } from 'vue-router'
import { routes as adminRoutes } from './routes'
import { routes as employeeRoutes } from './employee_routes'
import { authState, fetchMe } from '@/utils/auth'

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
    if (!authState.token && authRequired) {
      console.log('[Router] Session expired during fetchMe, redirecting to /login')
      return next('/login')
    }
  }

  next()
})

export default function (app) {
  app.use(router)
}
export { router }
