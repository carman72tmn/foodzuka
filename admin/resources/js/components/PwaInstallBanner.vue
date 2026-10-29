<script setup>
import { ref, onMounted } from 'vue'

const showBanner = ref(false)
const deferredPrompt = ref(null)

const checkPwaStatus = () => {
  // Проверяем, запущено ли уже в режиме standalone (установленное приложение)
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches 
    || navigator.standalone 
    || document.referrer.includes('android-app://')

  if (isStandalone) {
    console.log('[PWA] Application is already running in standalone mode')
    return false
  }

  // Проверяем, скрыл ли пользователь баннер в этой сессии / насовсем
  const isDismissed = localStorage.getItem('pwa_banner_dismissed') === 'true'
  if (isDismissed) {
    console.log('[PWA] Installation banner was dismissed by user')
    return false
  }

  return true
}

const initInstallPrompt = () => {
  if (!checkPwaStatus()) return

  if (window.deferredPrompt) {
    deferredPrompt.value = window.deferredPrompt
    showBanner.value = true
  }

  window.addEventListener('beforeinstallprompt', e => {
    e.preventDefault()
    window.deferredPrompt = e
    deferredPrompt.value = e
    if (checkPwaStatus()) {
      showBanner.value = true
    }
  })

  window.addEventListener('pwa-install-available', () => {
    if (window.deferredPrompt && checkPwaStatus()) {
      deferredPrompt.value = window.deferredPrompt
      showBanner.value = true
    }
  })

  window.addEventListener('appinstalled', () => {
    showBanner.value = false
    window.deferredPrompt = null
    deferredPrompt.value = null
    console.log('[PWA] Application was successfully installed')
  })
}

const installPwa = async () => {
  const promptEvent = deferredPrompt.value || window.deferredPrompt
  if (!promptEvent) return

  promptEvent.prompt()
  const { outcome } = await promptEvent.userChoice
  console.log(`[PWA] User choice outcome: ${outcome}`)
  
  if (outcome === 'accepted') {
    showBanner.value = false
    window.deferredPrompt = null
    deferredPrompt.value = null
  }
}

const dismissBanner = () => {
  showBanner.value = false
  // Скрываем баннер, чтобы не надоедал
  localStorage.setItem('pwa_banner_dismissed', 'true')
}

onMounted(() => {
  // Даем небольшую задержку в 1.5 секунды, чтобы страница полностью загрузилась
  setTimeout(() => {
    initInstallPrompt()
  }, 1500)
})
</script>

<template>
  <Transition name="slide-up">
    <div v-if="showBanner" class="pwa-install-banner">
      <div class="banner-content">
        <div class="banner-icon-wrapper">
          <VIcon icon="bx-mobile-vibration" size="32" class="banner-icon" />
        </div>
        <div class="banner-text">
          <div class="banner-title">Установите Vezuroll на телефон</div>
          <div class="banner-description text-truncate-2">Быстрый запуск, полноэкранный режим и мгновенные пуш-уведомления.</div>
        </div>
      </div>
      <div class="banner-actions">
        <VBtn color="primary" size="small" class="install-btn" @click="installPwa" prepend-icon="bx-down-arrow-alt">
          Установить
        </VBtn>
        <VBtn icon variant="text" size="small" color="secondary" class="close-btn" @click="dismissBanner">
          <VIcon icon="bx-x" />
        </VBtn>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.pwa-install-banner {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 480px;
  background: rgba(var(--v-theme-surface), 0.85);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border: 1px solid rgba(var(--v-border-color), 0.12);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  z-index: 9999;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.banner-icon-wrapper {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  border-radius: 12px;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.banner-icon {
  animation: shake 2.5s infinite;
}

.banner-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.banner-title {
  font-size: 15px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 2px;
  color: rgb(var(--v-theme-on-surface));
}

.banner-description {
  font-size: 12px;
  opacity: 0.8;
  line-height: 1.3;
  color: rgb(var(--v-theme-on-surface));
}

.text-truncate-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;  
  overflow: hidden;
}

.banner-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.install-btn {
  font-weight: 600;
  border-radius: 8px;
}

/* Animations */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translate(-50%, 100px);
  opacity: 0;
}

@keyframes shake {
  0% { transform: rotate(0); }
  15% { transform: rotate(5deg); }
  30% { transform: rotate(-5deg); }
  45% { transform: rotate(3deg); }
  60% { transform: rotate(-3deg); }
  75% { transform: rotate(0); }
  100% { transform: rotate(0); }
}

@media (max-width: 600px) {
  .pwa-install-banner {
    bottom: 16px;
    flex-direction: column;
    align-items: stretch;
    padding: 12px;
    gap: 12px;
  }
  
  .banner-actions {
    justify-content: flex-end;
  }
  
  .install-btn {
    flex: 1;
  }
}
</style>
