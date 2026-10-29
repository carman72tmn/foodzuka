import { createApp } from 'vue'
import EmployeeApp from '@/EmployeeApp.vue'
import { registerPlugins } from '@core/utils/plugins'
import axios from 'axios'

// Настройка глобального перехватчика для Axios (автоматическая авторизация в панели сотрудников)
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  const deviceId = localStorage.getItem('device_id')
  if (deviceId) {
    config.headers['X-Device-Id'] = deviceId
  }
  return config
})


// Styles
import '@core-scss/template/index.scss'
import '@layouts/styles/index.scss'
import '@styles/styles.scss'

// Create vue app
const app = createApp(EmployeeApp)

// PWA installation event capture
window.deferredPrompt = null
window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault()
  window.deferredPrompt = e
  // Сообщаем Vue-компонентам, что можно показать кнопку
  window.dispatchEvent(new CustomEvent('pwa-install-available'))
})

// Toast
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

// Register plugins
registerPlugins(app)
app.use(Toast)

// Mount vue app
app.mount('#app')

// Register Service Worker for Web Push
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => {
        console.log('[SW] Registered successfully with scope (Employee):', reg.scope)
      })
      .catch(err => {
        console.error('[SW] Registration failed (Employee):', err)
      })
  })

  // Слушаем сообщения от Service Worker при клике на уведомление
  navigator.serviceWorker.addEventListener('message', event => {
    if (event.data && event.data.type === 'navigate') {
      console.log('[SW] Navigation message received (Employee):', event.data.url)
      window.location.href = event.data.url
    }
  })
}
