import { createApp } from 'vue'
import App from '@/App.vue'
import { registerPlugins } from '@core/utils/plugins'
import axios from 'axios'
import { getAuthHeaders } from '@/utils/auth'

// Настройка глобального перехватчика для Axios (автоматическая авторизация)
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
const app = createApp(App)

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
    // Service Worker регистрируется для всего домена, так как он лежит в public/sw.js
    navigator.serviceWorker.register('/sw.js')
      .then(reg => {
        console.log('[SW] Registered successfully with scope:', reg.scope)
      })
      .catch(err => {
        console.error('[SW] Registration failed:', err)
      })
  })

  // Слушаем сообщения от Service Worker при клике на уведомление
  navigator.serviceWorker.addEventListener('message', event => {
    if (event.data && event.data.type === 'navigate') {
      console.log('[SW] Navigation message received:', event.data.url)
      // Переходим по URL (Vue router автоматически подхватит роут, если мы уже в приложении)
      window.location.href = event.data.url
    }
  })
}


// Автоматическая разблокировка аудиоподсистемы для iOS Safari и мобильных устройств
const unlockIOSAudio = () => {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext
    if (AudioContext) {
      const ctx = new AudioContext()
      if (ctx.state === 'suspended') {
        ctx.resume()
      }
      const buffer = ctx.createBuffer(1, 1, 22050)
      const source = ctx.createBufferSource()
      source.buffer = buffer
      source.connect(ctx.destination)
      source.start(0)
    }
    const silent = new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA')
    silent.play().catch(() => {})
    console.log('[Audio] iOS Audio playback successfully unlocked')
  } catch (e) {
    console.warn('[Audio] Failed to unlock audio:', e)
  }
}
window.addEventListener('touchstart', unlockIOSAudio, { once: true, passive: true })
window.addEventListener('click', unlockIOSAudio, { once: true })
window.addEventListener('keydown', unlockIOSAudio, { once: true })
