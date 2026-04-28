import { createRouter, createWebHistory } from 'vue-router'
import { routes } from './routes'
import { authState, fetchMe } from '@/utils/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const publicPages = ['/login', '/register', '/error']
  const authRequired = !publicPages.includes(to.path)

  if (authRequired && !authState.token) {
    return next('/login')
  }

  if (authState.token && !authState.user && to.path !== '/login') {
    await fetchMe()
  }

  next()
})

export default function (app) {
  app.use(router)
}
export { router }
