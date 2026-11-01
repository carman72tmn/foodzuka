<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useChatStore } from '@/stores/chatStore'
import { authState, isCourierUser } from '@/utils/auth'

const chatStore = useChatStore()
const isCourier = computed(() => isCourierUser())

const loading = ref(false)
const saving = ref(false)
const testLoading = ref(false)
const subLoading = ref(false)

const snackbar = ref(false)
const snackbarColor = ref('success')
const snackbarText = ref('')

const settings = ref({
  disable_browser_notifications_couriers: false,
  disable_browser_notifications_all: false,

  order_delivered_sound_enabled: true,
  order_delivered_sound_file: 'chime.mp3',
  order_delivered_push_enabled: true,

  new_order_sound_enabled: true,
  new_order_sound_file: 'bell.mp3',
  new_order_push_enabled: true,
  new_order_repeat_enabled: false,
  new_order_repeat_interval: 30,
  
  new_payment_sound_enabled: true,
  new_payment_sound_file: 'cash.mp3',
  new_payment_push_enabled: true,
  
  courier_delivery_sound_enabled: true,
  courier_delivery_sound_file: 'chime.mp3',
  courier_delivery_push_enabled: true,
  
  chat_message_sound_enabled: true,
  chat_message_sound_file: 'sonar.mp3',
  chat_message_push_enabled: true,
  
  order_cancelled_sound_enabled: true,
  order_cancelled_sound_file: 'bell.mp3',
  order_cancelled_push_enabled: true,
  
  order_changed_sound_enabled: false,
  order_changed_sound_file: 'bell.mp3',
  order_changed_push_enabled: false,
  
  delivery_unassigned_sound_enabled: true,
  delivery_unassigned_sound_file: 'chime.mp3',
  delivery_unassigned_push_enabled: true,
  
  delivery_assigned_sound_enabled: true,
  delivery_assigned_sound_file: 'chime.mp3',
  delivery_assigned_push_enabled: true,
  
  change_cooking_time_sound_enabled: true,
  change_cooking_time_sound_file: 'click.mp3',
  change_cooking_time_push_enabled: true,
  
  change_items_sound_enabled: true,
  change_items_sound_file: 'click.mp3',
  change_items_push_enabled: true,
  
  change_amount_sound_enabled: true,
  change_amount_sound_file: 'click.mp3',
  change_amount_push_enabled: true,
  
  change_payment_sound_enabled: true,
  change_payment_sound_file: 'click.mp3',
  change_payment_push_enabled: true,
  
  change_address_sound_enabled: true,
  change_address_sound_file: 'click.mp3',
  change_address_push_enabled: true,
  order_changed_scope: 'all',

  // ==========================================
  // ПЕРСОНАЛЬНЫЕ НАСТРОЙКИ КУРЬЕРА (10 СОБЫТИЙ)
  // ==========================================
  courier_order_assigned_sound_enabled: true,
  courier_order_assigned_sound_file: 'chime.mp3',
  courier_order_assigned_push_enabled: true,

  courier_cooking_time_set_sound_enabled: true,
  courier_cooking_time_set_sound_file: 'bell.mp3',
  courier_cooking_time_set_push_enabled: true,

  courier_cooking_time_changed_sound_enabled: true,
  courier_cooking_time_changed_sound_file: 'click.mp3',
  courier_cooking_time_changed_push_enabled: true,

  courier_status_changed_sound_enabled: true,
  courier_status_changed_sound_file: 'bell.mp3',
  courier_status_changed_push_enabled: true,

  courier_amount_changed_sound_enabled: true,
  courier_amount_changed_sound_file: 'cash.mp3',
  courier_amount_changed_push_enabled: true,

  courier_address_changed_sound_enabled: true,
  courier_address_changed_sound_file: 'doorbell.mp3',
  courier_address_changed_push_enabled: true,

  courier_changed_to_pickup_sound_enabled: true,
  courier_changed_to_pickup_sound_file: 'branch.mp3',
  courier_changed_to_pickup_push_enabled: true,

  courier_removed_from_delivery_sound_enabled: true,
  courier_removed_from_delivery_sound_file: 'error.mp3',
  courier_removed_from_delivery_push_enabled: true,

  courier_unassigned_sound_enabled: true,
  courier_unassigned_sound_file: 'sonar.mp3',
  courier_unassigned_push_enabled: true,

  courier_delivery_time_changed_sound_enabled: true,
  courier_delivery_time_changed_sound_file: 'water.mp3',
  courier_delivery_time_changed_push_enabled: true,
})

const courierNotificationItems = [
  {
    key: 'courier_order_assigned',
    title: '1. Назначен заказ на доставку',
    desc: 'Оповещение, когда заказ назначен вам на доставку',
    icon: 'bx-car',
    color: 'warning'
  },
  {
    key: 'courier_cooking_time_set',
    title: '2. Установление времени приготовления заказа',
    desc: 'Оповещение, когда кухня установила время готовности заказа',
    icon: 'bx-time-five',
    color: 'info'
  },
  {
    key: 'courier_cooking_time_changed',
    title: '3. Изменение времени приготовления заказа',
    desc: 'Оповещение при изменении времени приготовления заказа на кухне',
    icon: 'bx-history',
    color: 'primary'
  },
  {
    key: 'courier_status_changed',
    title: '4. Изменение статуса заказа (готов / отменен)',
    desc: 'Оповещение, когда блюда приготовлены кухней или заказ был отменен',
    icon: 'bx-check-shield',
    color: 'success'
  },
  {
    key: 'courier_amount_changed',
    title: '5. Изменение суммы заказа',
    desc: 'Оповещение, когда изменилась сумма к оплате по вашему заказу',
    icon: 'bx-money',
    color: 'teal'
  },
  {
    key: 'courier_address_changed',
    title: '6. Изменение адреса доставки',
    desc: 'Оповещение, если изменился адрес доставки заказа',
    icon: 'bx-map-pin',
    color: 'deep-purple'
  },
  {
    key: 'courier_changed_to_pickup',
    title: '7. Изменение способа доставки заказа (самовывоз)',
    desc: 'Оповещение, если заказ переведен на самовывоз (доставка отменена)',
    icon: 'bx-store',
    color: 'amber-darken-3'
  },
  {
    key: 'courier_removed_from_delivery',
    title: '8. Заказ убран из доставки',
    desc: 'Оповещение, если заказ снят с доставки или отменен',
    icon: 'bx-x-circle',
    color: 'error'
  },
  {
    key: 'courier_unassigned',
    title: '9. Заказ убран из списка доставок выбранного курьера',
    desc: 'Оповещение, если заказ снят с вас или переназначен другому курьеру',
    icon: 'bx-user-x',
    color: 'deep-orange'
  },
  {
    key: 'courier_delivery_time_changed',
    title: '10. Изменение времени доставки заказа',
    desc: 'Оповещение, если изменилось ожидаемое время доставки заказа',
    icon: 'bx-calendar-event',
    color: 'cyan-darken-3'
  },
]

const soundFiles = [
  { title: 'Звонок (Bell)', value: 'bell.mp3' },
  { title: 'Касса (Cash Register)', value: 'cash.mp3' },
  { title: 'Стекло (Chime)', value: 'chime.mp3' },
  { title: 'Сонар (Sonar)', value: 'sonar.mp3' },
  { title: 'Капля воды (Water)', value: 'water.mp3' },
  { title: 'Клик кнопки (Click)', value: 'click.mp3' },
  { title: 'Ветка (Branch)', value: 'branch.mp3' },
  { title: 'Мягкий клик (Push)', value: 'push.mp3' },
  { title: 'Дверной звонок (Doorbell)', value: 'doorbell.mp3' },
  { title: 'Ошибка (Error)', value: 'error.mp3' }
]

const repeatIntervals = [
  { title: 'Каждые 15 секунд', value: 15 },
  { title: 'Каждые 30 секунд', value: 30 },
  { title: 'Каждую минуту', value: 60 },
  { title: 'Каждые 2 минуты', value: 120 }
]

const scopeOptions = [
  { title: 'Всех заказов', value: 'all' },
  { title: 'Только заказов на самовывоз', value: 'pickup' },
  { title: 'Только заказов на доставку', value: 'delivery' },
  { title: 'Только заказов на доставку, назначенных курьеру', value: 'courier_assigned' }
]

const showMessage = (text, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const API_BASE = '/api/v1/notifications'

// Проверка поддержки пушей в текущем браузере
const isPushSupported = ref(false)
const pushPermission = ref('default')
const isSubscribed = ref(false)
const activeSubscription = ref(null)

const checkBrowserSupport = async () => {
  isPushSupported.value = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
  if (isPushSupported.value) {
    pushPermission.value = Notification.permission
    
    // Проверяем наличие активной подписки в сервис-воркере
    try {
      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.getSubscription()
      isSubscribed.value = !!sub
      activeSubscription.value = sub
    } catch (e) {
      console.error('[Notifications] Failed to check active subscription:', e)
    }
  }
}

// Загрузка настроек уведомлений
const loadSettings = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/settings`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    if (res.data) {
      Object.keys(settings.value).forEach(key => {
        if (res.data[key] !== undefined && res.data[key] !== null) {
          settings.value[key] = res.data[key]
        }
      })
    }
  } catch (e) {
    showMessage('Ошибка загрузки настроек', 'error')
  } finally {
    loading.value = false
  }
}

// Сохранение настроек
const saveSettings = async () => {
  saving.value = true
  try {
    await axios.post(`${API_BASE}/settings`, settings.value, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    // Сохраняем также локально для быстрой реактивности
    localStorage.setItem('user_notification_settings', JSON.stringify(settings.value))
    chatStore.notificationSettings = { ...settings.value } // Обновляем в Pinia store
    showMessage('Настройки успешно сохранены')
  } catch (e) {
    showMessage('Ошибка сохранения настроек', 'error')
  } finally {
    saving.value = false
  }
}

// Воспроизвести превью звука
const playSoundPreview = (filename) => {
  const audio = new Audio(`/sounds/${filename}`)
  audio.play().catch(err => {
    if (err.name === 'NotAllowedError') {
      showMessage('Воспроизведение заблокировано браузером. Требуется клик по экрану.', 'warning')
    } else {
      showMessage(`Не удалось воспроизвести файл: ${filename} (Проверьте, загружен ли он на сервер)`, 'error')
    }
    console.error(err)
  })
}

// Конвертация VAPID ключа
const urlBase64ToUint8Array = (base64String) => {
  const padding = '='.repeat((4 - base64String.length % 4) % 4)
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/')

  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

// Подписаться на пуш-уведомления
const subscribeToPush = async () => {
  subLoading.value = true
  try {
    const permission = await Notification.requestPermission()
    pushPermission.value = permission
    if (permission !== 'granted') {
      showMessage('Разрешение на отправку уведомлений отклонено', 'error')
      subLoading.value = false
      return
    }

    const keyRes = await axios.get(`${API_BASE}/vapid-public-key`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    const publicVapidKey = keyRes.data.public_key

    const reg = await navigator.serviceWorker.ready
    
    // Принудительно отписываемся от старой подписки в браузере,
    // чтобы применить новый VAPID-ключ и избежать ошибки 400 Bad Request
    try {
      const oldSub = await reg.pushManager.getSubscription()
      if (oldSub) {
        await oldSub.unsubscribe()
        console.log('[Push] Unsubscribed from old subscription successfully')
      }
    } catch (err) {
      console.warn('[Push] Error during unsubscribe from old subscription:', err)
    }

    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicVapidKey)
    })

    const subJson = sub.toJSON()
    await axios.post(`${API_BASE}/subscribe`, {
      endpoint: subJson.endpoint,
      keys: {
        p256dh: subJson.keys.p256dh,
        auth: subJson.keys.auth
      }
    }, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    })

    isSubscribed.value = true
    activeSubscription.value = sub
    showMessage('Вы успешно подписались на пуш-уведомления!')
  } catch (e) {
    console.error(e)
    showMessage('Не удалось подписаться на пуш-уведомления', 'error')
  } finally {
    subLoading.value = false
  }
}

// Отписаться от пуш-уведомлений
const unsubscribeFromPush = async () => {
  subLoading.value = true
  try {
    const reg = await navigator.serviceWorker.ready
    const sub = await reg.pushManager.getSubscription()
    if (sub) {
      const endpoint = sub.endpoint
      await sub.unsubscribe()
      
      await axios.post(`${API_BASE}/unsubscribe`, { endpoint }, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      })
    }
    isSubscribed.value = false
    activeSubscription.value = null
    showMessage('Подписка отменена')
  } catch (e) {
    console.error(e)
    showMessage('Ошибка при отмене подписки', 'error')
  } finally {
    subLoading.value = false
  }
}

// Отправить тестовое пуш-уведомление
const sendTestPush = async () => {
  testLoading.value = true
  try {
    const res = await axios.post(`${API_BASE}/test-push`, {}, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    if (res.data && res.data.sent > 0) {
      showMessage('Тестовый пуш отправлен!')
    } else {
      showMessage('Пуш не отправлен. Проверьте подписку.', 'warning')
    }
  } catch (e) {
    showMessage(e.response?.data?.detail || 'Не удалось отправить пуш', 'error')
  } finally {
    testLoading.value = false
  }
}

// PWA добавление на экран домой
const deferredPrompt = ref(null)
const showInstallBtn = ref(false)
const instructionDialog = ref(false)

const handlePushClick = () => {
  if (pushPermission.value === 'denied') {
    instructionDialog.value = true
  } else {
    subscribeToPush()
  }
}

const installPWA = async () => {
  const promptObj = deferredPrompt.value || window.deferredPrompt
  if (!promptObj) return
  promptObj.prompt()
  const { outcome } = await promptObj.userChoice
  if (outcome === 'accepted') {
    showInstallBtn.value = false
    window.deferredPrompt = null
    deferredPrompt.value = null
  }
}

onMounted(async () => {
  await loadSettings()
  await checkBrowserSupport()
  
  const checkPwaPrompt = () => {
    if (window.deferredPrompt) {
      deferredPrompt.value = window.deferredPrompt
      showInstallBtn.value = true
    }
  }

  // Проверяем наличие события при монтировании
  checkPwaPrompt()
  
  // Слушаем кастомное событие, если prompt появился позже
  window.addEventListener('pwa-install-available', checkPwaPrompt)
  
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    window.deferredPrompt = e
    deferredPrompt.value = e
    showInstallBtn.value = true
  })
  
  window.addEventListener('appinstalled', () => {
    showInstallBtn.value = false
    deferredPrompt.value = null
    window.deferredPrompt = null
    showMessage('Приложение успешно установлено на экран «Домой»!')
  })
})
</script>

<template>
  <VRow>
    <VCol cols="12" md="7">
      <!-- Настройка PWA -->
      <VCard v-if="showInstallBtn" title="Мобильное Приложение" color="primary" variant="tonal" class="mb-6">
        <VCardText>
          <div class="d-flex align-center justify-between flex-wrap gap-4">
            <div>
              <div class="text-subtitle-1 font-weight-bold">Доступна мобильная версия!</div>
              <div class="text-body-2">Установите админ-панель на главный экран вашего телефона для быстрого доступа.</div>
            </div>
            <VBtn color="primary" prepend-icon="bx-mobile" @click="installPWA">
              Установить на экран «Домой»
            </VBtn>
          </div>
        </VCardText>
      </VCard>

      <VCard title="Звуки и События" class="mb-6">
        <VCardText v-if="loading" class="text-center py-6">
          <VProgressCircular indeterminate color="primary" />
        </VCardText>
        <VCardText v-else>
          <VForm>
            <!-- БЛОК ДЛЯ КУРЬЕРА (10 ВЫДЕЛЕННЫХ СОБЫТИЙ) -->
            <div v-if="isCourier">
              <VAlert
                color="primary"
                variant="tonal"
                icon="bx-user-check"
                class="mb-6"
              >
                <div class="text-subtitle-1 font-weight-bold">Профиль курьера активен</div>
                <div class="text-body-2">
                  Общие уведомления администратора скрыты. Ниже вы можете настроить персональные звуковые сигналы и всплывающие Push-уведомления для ваших 10 событий доставки.
                </div>
              </VAlert>

              <div
                v-for="item in courierNotificationItems"
                :key="item.key"
                class="mb-4 pa-4 rounded border"
                :style="{ borderColor: 'rgba(var(--v-border-color), 0.18)' }"
              >
                <div class="d-flex align-center mb-3">
                  <VAvatar :color="item.color" variant="tonal" size="36" class="me-3">
                    <VIcon :icon="item.icon" size="20" />
                  </VAvatar>
                  <div>
                    <div class="text-subtitle-1 font-weight-bold">{{ item.title }}</div>
                    <div class="text-caption text-medium-emphasis">{{ item.desc }}</div>
                  </div>
                </div>

                <VRow class="mb-1" align="center">
                  <VCol cols="12" sm="6" class="py-1">
                    <VSwitch
                      v-model="settings[item.key + '_sound_enabled']"
                      label="Звуковой сигнал"
                      :color="item.color"
                      density="compact"
                    />
                  </VCol>
                  <VCol cols="12" sm="6" class="py-1">
                    <VSwitch
                      v-model="settings[item.key + '_push_enabled']"
                      label="Всплывающее окно / Push"
                      :color="item.color"
                      density="compact"
                    />
                  </VCol>
                </VRow>

                <div v-if="settings[item.key + '_sound_enabled']" class="d-flex align-center gap-3 mt-1 ps-2">
                  <VSelect
                    v-model="settings[item.key + '_sound_file']"
                    :items="soundFiles"
                    label="Звук уведомления"
                    density="compact"
                    style="max-width: 280px;"
                    @update:model-value="playSoundPreview"
                  />
                  <VBtn
                    icon="bx-play"
                    size="small"
                    color="secondary"
                    variant="outlined"
                    title="Прослушать звук"
                    @click="playSoundPreview(settings[item.key + '_sound_file'])"
                  />
                </div>
              </div>
            </div>

            <!-- БАЗОВЫЕ УВЕДОМЛЕНИЯ АДМИНИСТРАТОРА (ОТОБРАЖАЮТСЯ ТОЛЬКО ЕСЛИ НЕ КУРЬЕР) -->
            <div v-else>
              <!-- Глобальное управление уведомлениями браузера -->
              <VAlert
                color="warning"
                variant="tonal"
                icon="bx-shield-quarter"
                class="mb-6"
              >
                <div class="text-subtitle-1 font-weight-bold mb-1">
                  Глобальное управление уведомлениями в браузере
                </div>
                <div class="text-caption mb-3">
                  Мастер-переключатели позволяют мгновенно отключить звуки, системные Push и всплывающие окна в браузере.
                </div>

                <VSwitch
                  v-model="settings.disable_browser_notifications_couriers"
                  label="Отключить уведомления браузера для курьеров"
                  color="warning"
                  density="compact"
                  class="mb-2"
                />

                <VSwitch
                  v-model="settings.disable_browser_notifications_all"
                  label="Отключить уведомления в браузере для всех!"
                  color="error"
                  density="compact"
                />
              </VAlert>

              <!-- Блок Новых Заказов -->
              <div class="mb-6">
              <h3 class="text-h6 mb-3 d-flex align-center text-primary">
                <VIcon icon="bx-receipt" class="me-2" />
                Новые заказы
              </h3>
              
              <VSwitch
                v-model="settings.new_order_sound_enabled"
                label="Проигрывать звук при поступлении нового заказа"
                color="primary"
                class="mb-2"
              />

              <div class="d-flex align-center gap-4 mb-4" v-if="settings.new_order_sound_enabled">
                <VSelect
                  v-model="settings.new_order_sound_file"
                  :items="soundFiles"
                  label="Выберите звук"
                  style="max-width: 300px;"
                  @update:model-value="playSoundPreview"
                />
                <VBtn
                  icon="bx-play"
                  color="secondary"
                  variant="outlined"
                  @click="playSoundPreview(settings.new_order_sound_file)"
                  title="Прослушать"
                />
              </div>

              <!-- Интервал повторения -->
              <div class="mb-4 ps-6" v-if="settings.new_order_sound_enabled">
                <VSwitch
                  v-model="settings.new_order_repeat_enabled"
                  label="Повторять сигнал, пока заказ не будет просмотрен"
                  color="primary"
                  class="mb-2"
                />
                <div class="d-flex align-center gap-4" v-if="settings.new_order_repeat_enabled">
                  <VSelect
                    v-model="settings.new_order_repeat_interval"
                    :items="repeatIntervals"
                    label="Интервал повторения"
                    style="max-width: 300px;"
                  />
                </div>
              </div>

              <VSwitch
                v-model="settings.new_order_push_enabled"
                label="Показывать всплывающее пуш-уведомление в системе"
                color="primary"
              />
            </div>

            <VDivider class="my-6" />

            <!-- Блок Платежей -->
            <div class="mb-6">
              <h3 class="text-h6 mb-3 d-flex align-center text-success">
                <VIcon icon="bx-credit-card" class="me-2" />
                Поступления оплат (Т-Банк / СБП)
              </h3>
              
              <VSwitch
                v-model="settings.new_payment_sound_enabled"
                label="Проигрывать звук при успешной оплате"
                color="success"
                class="mb-2"
              />

              <div class="d-flex align-center gap-4 mb-4" v-if="settings.new_payment_sound_enabled">
                <VSelect
                  v-model="settings.new_payment_sound_file"
                  :items="soundFiles"
                  label="Выберите звук"
                  style="max-width: 300px;"
                  @update:model-value="playSoundPreview"
                />
                <VBtn
                  icon="bx-play"
                  color="secondary"
                  variant="outlined"
                  @click="playSoundPreview(settings.new_payment_sound_file)"
                  title="Прослушать"
                />
              </div>

              <VSwitch
                v-model="settings.new_payment_push_enabled"
                label="Показывать всплывающее пуш-уведомление об оплате"
                color="success"
              />
            </div>

            <VDivider class="my-6" />

            <!-- Блок Доставок курьеров -->
            <div class="mb-6">
              <h3 class="text-h6 mb-3 d-flex align-center text-warning">
                <VIcon icon="bx-car" class="me-2" />
                Назначение доставок курьерам
              </h3>
              
              <VSwitch
                v-model="settings.courier_delivery_sound_enabled"
                label="Проигрывать звук при назначении доставки (для курьера)"
                color="warning"
                class="mb-2"
              />

              <div class="d-flex align-center gap-4 mb-4" v-if="settings.courier_delivery_sound_enabled">
                <VSelect
                  v-model="settings.courier_delivery_sound_file"
                  :items="soundFiles"
                  label="Выберите звук"
                  style="max-width: 300px;"
                  @update:model-value="playSoundPreview"
                />
                <VBtn
                  icon="bx-play"
                  color="secondary"
                  variant="outlined"
                  @click="playSoundPreview(settings.courier_delivery_sound_file)"
                  title="Прослушать"
                />
              </div>

              <VSwitch
                v-model="settings.courier_delivery_push_enabled"
                label="Показывать пуш-уведомление о новой доставке"
                color="warning"
              />
            </div>

            <VDivider class="my-6" />

            <!-- Блок Сообщений чата -->
            <div class="mb-6">
              <h3 class="text-h6 mb-3 d-flex align-center text-info">
                <VIcon icon="bx-chat" class="me-2" />
                Сообщения в чате
              </h3>
              
              <VSwitch
                v-model="settings.chat_message_sound_enabled"
                label="Проигрывать звук при получении сообщения"
                color="info"
                class="mb-2"
              />

              <div class="d-flex align-center gap-4 mb-4" v-if="settings.chat_message_sound_enabled">
                <VSelect
                  v-model="settings.chat_message_sound_file"
                  :items="soundFiles"
                  label="Выберите звук"
                  style="max-width: 300px;"
                  @update:model-value="playSoundPreview"
                />
                <VBtn
                  icon="bx-play"
                  color="secondary"
                  variant="outlined"
                  @click="playSoundPreview(settings.chat_message_sound_file)"
                  title="Прослушать"
                />
              </div>

              <VSwitch
                v-model="settings.chat_message_push_enabled"
                label="Показывать пуш-уведомление о новом сообщении"
                color="info"
              />
            </div>

            <VDivider class="my-6" />

            <!-- Блок Отмены заказа -->
            <div class="mb-6">
              <h3 class="text-h6 mb-3 d-flex align-center text-error">
                <VIcon icon="bx-x-circle" class="me-2" />
                Отмена заказов
              </h3>
              
              <VSwitch
                v-model="settings.order_cancelled_sound_enabled"
                label="Проигрывать звук при отмене заказа"
                color="error"
                class="mb-2"
              />

              <div class="d-flex align-center gap-4 mb-4" v-if="settings.order_cancelled_sound_enabled">
                <VSelect
                  v-model="settings.order_cancelled_sound_file"
                  :items="soundFiles"
                  label="Выберите звук"
                  style="max-width: 300px;"
                  @update:model-value="playSoundPreview"
                />
                <VBtn
                  icon="bx-play"
                  color="secondary"
                  variant="outlined"
                  @click="playSoundPreview(settings.order_cancelled_sound_file)"
                  title="Прослушать"
                />
              </div>

              <VSwitch
                v-model="settings.order_cancelled_push_enabled"
                label="Показывать пуш-уведомление об отмене заказа"
                color="error"
              />
            </div>

            <VDivider class="my-6" />

            <!-- Блок Изменения заказа -->
            <div class="mb-6">
              <h3 class="text-h6 mb-3 d-flex align-center text-indigo">
                <VIcon icon="bx-edit" class="me-2" />
                Изменения в составе / адресе заказа
              </h3>

              <div class="mb-4">
                <VSelect
                  v-model="settings.order_changed_scope"
                  :items="scopeOptions"
                  label="Уведомлять об изменениях для"
                  color="indigo"
                  style="max-width: 450px;"
                  prepend-inner-icon="bx-filter-alt"
                />
              </div>
              
              <VSwitch
                v-model="settings.order_changed_sound_enabled"
                label="Проигрывать звук при изменении заказа"
                color="indigo"
                class="mb-2"
              />

              <div class="d-flex align-center gap-4 mb-4" v-if="settings.order_changed_sound_enabled">
                <VSelect
                  v-model="settings.order_changed_sound_file"
                  :items="soundFiles"
                  label="Выберите звук"
                  style="max-width: 300px;"
                  @update:model-value="playSoundPreview"
                />
                <VBtn
                  icon="bx-play"
                  color="secondary"
                  variant="outlined"
                  @click="playSoundPreview(settings.order_changed_sound_file)"
                  title="Прослушать"
                />
              </div>

              <VSwitch
                v-model="settings.order_changed_push_enabled"
                label="Показывать пуш-уведомление об изменении заказа"
                color="indigo"
              />
            </div>

             <VDivider class="my-6" />

             <!-- Блок Свободная доставка -->
             <div class="mb-6">
               <h3 class="text-h6 mb-3 d-flex align-center text-teal">
                 <VIcon icon="bx-navigation" class="me-2" />
                 Новая свободная доставка (без курьера)
               </h3>
               
               <VSwitch
                 v-model="settings.delivery_unassigned_sound_enabled"
                 label="Проигрывать звук при поступлении свободной доставки"
                 color="teal"
                 class="mb-2"
               />

               <div class="d-flex align-center gap-4 mb-4" v-if="settings.delivery_unassigned_sound_enabled">
                 <VSelect
                   v-model="settings.delivery_unassigned_sound_file"
                   :items="soundFiles"
                   label="Выберите звук"
                   style="max-width: 300px;"
                   @update:model-value="playSoundPreview"
                 />
                 <VBtn
                   icon="bx-play"
                   color="secondary"
                   variant="outlined"
                   @click="playSoundPreview(settings.delivery_unassigned_sound_file)"
                   title="Прослушать"
                 />
               </div>

               <VSwitch
                 v-model="settings.delivery_unassigned_push_enabled"
                 label="Показывать пуш-уведомление о свободной доставке"
                 color="teal"
               />
             </div>

             <VDivider class="my-6" />

             <!-- Блок Доставка назначена курьеру -->
             <div class="mb-6">
               <h3 class="text-h6 mb-3 d-flex align-center text-deep-purple">
                 <VIcon icon="bx-user-check" class="me-2" />
                 Назначена доставка (для назначенного курьера)
               </h3>
               
               <VSwitch
                 v-model="settings.delivery_assigned_sound_enabled"
                 label="Проигрывать звук при назначении доставки курьеру"
                 color="deep-purple"
                 class="mb-2"
               />

               <div class="d-flex align-center gap-4 mb-4" v-if="settings.delivery_assigned_sound_enabled">
                 <VSelect
                   v-model="settings.delivery_assigned_sound_file"
                   :items="soundFiles"
                   label="Выберите звук"
                   style="max-width: 300px;"
                   @update:model-value="playSoundPreview"
                 />
                 <VBtn
                   icon="bx-play"
                   color="secondary"
                   variant="outlined"
                   @click="playSoundPreview(settings.delivery_assigned_sound_file)"
                   title="Прослушать"
                 />
               </div>

               <VSwitch
                 v-model="settings.delivery_assigned_push_enabled"
                 label="Показывать пуш-уведомление о назначении доставки курьеру"
                 color="deep-purple"
               />
             </div>

             <VDivider class="my-6" />

             <!-- Блок Доставки заказа (Заказ доставлен) -->
             <div class="mb-6">
               <h3 class="text-h6 mb-3 d-flex align-center text-success">
                 <VIcon icon="bx-check-double" class="me-2" />
                 Доставка заказа (заказ доставлен)
               </h3>
               <div class="text-caption text-medium-emphasis mb-3">
                 Оповещение срабатывает для доставок при переводе в статус «Доставлен». В панели администратора отображается стилизованное постоянное всплывающее окно (не пропадает с экрана пока не закроют), проигрывается выбранный звук и отправляется Web Push. Для курьеров это оповещение скрыто.
               </div>
               
               <VSwitch
                 v-model="settings.order_delivered_sound_enabled"
                 label="Проигрывать звук при доставке заказа"
                 color="success"
                 class="mb-2"
               />

               <div class="d-flex align-center gap-4 mb-4" v-if="settings.order_delivered_sound_enabled">
                 <VSelect
                   v-model="settings.order_delivered_sound_file"
                   :items="soundFiles"
                   label="Выберите звук"
                   style="max-width: 300px;"
                   @update:model-value="playSoundPreview"
                 />
                 <VBtn
                   icon="bx-play"
                   color="secondary"
                   variant="outlined"
                   @click="playSoundPreview(settings.order_delivered_sound_file)"
                   title="Прослушать"
                 />
               </div>

               <VSwitch
                 v-model="settings.order_delivered_push_enabled"
                 label="Показывать всплывающее окно и Web Push при доставке заказа"
                 color="success"
               />
             </div>

             <VDivider class="my-6" />

             <!-- Детальные изменения в доставке -->
             <div class="mb-6">
               <h3 class="text-h6 mb-4 d-flex align-center text-orange-darken-3">
                 <VIcon icon="bx-cog" class="me-2" />
                 Изменения параметров доставки (время, состав, оплата, адрес)
               </h3>

               <!-- 1. Время готовности -->
               <div class="ps-4 mb-5 border-l-2">
                 <div class="text-subtitle-2 font-weight-bold mb-2">Изменение времени готовности на кухне</div>
                 <VSwitch
                   v-model="settings.change_cooking_time_sound_enabled"
                   label="Проигрывать звук при изменении времени готовности"
                   color="orange"
                   density="compact"
                 />
                 <div class="d-flex align-center gap-4 mb-2" v-if="settings.change_cooking_time_sound_enabled">
                   <VSelect
                     v-model="settings.change_cooking_time_sound_file"
                     :items="soundFiles"
                     label="Звук"
                     density="compact"
                     style="max-width: 250px;"
                     @update:model-value="playSoundPreview"
                   />
                   <VBtn
                     icon="bx-play"
                     size="small"
                     color="secondary"
                     variant="outlined"
                     @click="playSoundPreview(settings.change_cooking_time_sound_file)"
                   />
                 </div>
                 <VSwitch
                   v-model="settings.change_cooking_time_push_enabled"
                   label="Пуш-уведомление об изменении времени готовности"
                   color="orange"
                   density="compact"
                 />
               </div>

               <!-- 2. Состав -->
               <div class="ps-4 mb-5 border-l-2">
                 <div class="text-subtitle-2 font-weight-bold mb-2">Изменение состава (блюд) заказа</div>
                 <VSwitch
                   v-model="settings.change_items_sound_enabled"
                   label="Проигрывать звук при изменении состава"
                   color="orange"
                   density="compact"
                 />
                 <div class="d-flex align-center gap-4 mb-2" v-if="settings.change_items_sound_enabled">
                   <VSelect
                     v-model="settings.change_items_sound_file"
                     :items="soundFiles"
                     label="Звук"
                     density="compact"
                     style="max-width: 250px;"
                     @update:model-value="playSoundPreview"
                   />
                   <VBtn
                     icon="bx-play"
                     size="small"
                     color="secondary"
                     variant="outlined"
                     @click="playSoundPreview(settings.change_items_sound_file)"
                   />
                 </div>
                 <VSwitch
                   v-model="settings.change_items_push_enabled"
                   label="Пуш-уведомление об изменении состава"
                   color="orange"
                   density="compact"
                 />
               </div>

               <!-- 3. Сумма оплаты -->
               <div class="ps-4 mb-5 border-l-2">
                 <div class="text-subtitle-2 font-weight-bold mb-2">Изменение суммы заказа</div>
                 <VSwitch
                   v-model="settings.change_amount_sound_enabled"
                   label="Проигрывать звук при изменении суммы"
                   color="orange"
                   density="compact"
                 />
                 <div class="d-flex align-center gap-4 mb-2" v-if="settings.change_amount_sound_enabled">
                   <VSelect
                     v-model="settings.change_amount_sound_file"
                     :items="soundFiles"
                     label="Звук"
                     density="compact"
                     style="max-width: 250px;"
                     @update:model-value="playSoundPreview"
                   />
                   <VBtn
                     icon="bx-play"
                     size="small"
                     color="secondary"
                     variant="outlined"
                     @click="playSoundPreview(settings.change_amount_sound_file)"
                   />
                 </div>
                 <VSwitch
                   v-model="settings.change_amount_push_enabled"
                   label="Пуш-уведомление об изменении суммы"
                   color="orange"
                   density="compact"
                 />
               </div>

               <!-- 4. Способ оплаты -->
               <div class="ps-4 mb-5 border-l-2">
                 <div class="text-subtitle-2 font-weight-bold mb-2">Изменение способа оплаты</div>
                 <VSwitch
                   v-model="settings.change_payment_sound_enabled"
                   label="Проигрывать звук при изменении способа оплаты"
                   color="orange"
                   density="compact"
                 />
                 <div class="d-flex align-center gap-4 mb-2" v-if="settings.change_payment_sound_enabled">
                   <VSelect
                     v-model="settings.change_payment_sound_file"
                     :items="soundFiles"
                     label="Звук"
                     density="compact"
                     style="max-width: 250px;"
                     @update:model-value="playSoundPreview"
                   />
                   <VBtn
                     icon="bx-play"
                     size="small"
                     color="secondary"
                     variant="outlined"
                     @click="playSoundPreview(settings.change_payment_sound_file)"
                   />
                 </div>
                 <VSwitch
                   v-model="settings.change_payment_push_enabled"
                   label="Пуш-уведомление об изменении способа оплаты"
                   color="orange"
                   density="compact"
                 />
               </div>

               <!-- 5. Адрес -->
               <div class="ps-4 mb-5 border-l-2">
                 <div class="text-subtitle-2 font-weight-bold mb-2">Изменение адреса доставки</div>
                 <VSwitch
                   v-model="settings.change_address_sound_enabled"
                   label="Проигрывать звук при изменении адреса"
                   color="orange"
                   density="compact"
                 />
                 <div class="d-flex align-center gap-4 mb-2" v-if="settings.change_address_sound_enabled">
                   <VSelect
                     v-model="settings.change_address_sound_file"
                     :items="soundFiles"
                     label="Звук"
                     density="compact"
                     style="max-width: 250px;"
                     @update:model-value="playSoundPreview"
                   />
                   <VBtn
                     icon="bx-play"
                     size="small"
                     color="secondary"
                     variant="outlined"
                     @click="playSoundPreview(settings.change_address_sound_file)"
                   />
                 </div>
                 <VSwitch
                   v-model="settings.change_address_push_enabled"
                   label="Пуш-уведомление об изменении адреса"
                   color="orange"
                   density="compact"
                 />
                </div>
              </div>

              <!-- Дополнительный блок для Администратора: Настройки курьерских уведомлений -->
              <VExpansionPanels class="mt-4 mb-2">
                <VExpansionPanel title="Настройки уведомлений курьеров (по умолчанию)" subtitle="10 выделенных типов курьерских событий">
                  <VExpansionPanelText>
                    <div
                      v-for="item in courierNotificationItems"
                      :key="item.key"
                      class="mb-3 pa-3 rounded border"
                      :style="{ borderColor: 'rgba(var(--v-border-color), 0.16)' }"
                    >
                      <div class="d-flex align-center mb-2">
                        <VAvatar :color="item.color" variant="tonal" size="30" class="me-2">
                          <VIcon :icon="item.icon" size="16" />
                        </VAvatar>
                        <div class="text-subtitle-2 font-weight-bold">{{ item.title }}</div>
                      </div>
                      <VRow align="center">
                        <VCol cols="12" sm="6" class="py-0">
                          <VSwitch
                            v-model="settings[item.key + '_sound_enabled']"
                            label="Звук"
                            density="compact"
                          />
                        </VCol>
                        <VCol cols="12" sm="6" class="py-0">
                          <VSwitch
                            v-model="settings[item.key + '_push_enabled']"
                            label="Push"
                            density="compact"
                          />
                        </VCol>
                      </VRow>
                      <div v-if="settings[item.key + '_sound_enabled']" class="d-flex align-center gap-2 mt-1">
                        <VSelect
                          v-model="settings[item.key + '_sound_file']"
                          :items="soundFiles"
                          label="Звуковой файл"
                          density="compact"
                          style="max-width: 250px;"
                          @update:model-value="playSoundPreview"
                        />
                        <VBtn
                          icon="bx-play"
                          size="small"
                          variant="outlined"
                          @click="playSoundPreview(settings[item.key + '_sound_file'])"
                        />
                      </div>
                    </div>
                  </VExpansionPanelText>
                </VExpansionPanel>
              </VExpansionPanels>
             </div>

            <div class="d-flex gap-4 mt-6">
              <VBtn
                color="primary"
                :loading="saving"
                prepend-icon="bx-save"
                @click="saveSettings"
              >
                Сохранить настройки
              </VBtn>
            </div>
          </VForm>
        </VCardText>
      </VCard>

      <!-- Блок Web Push -->
      <VCard title="Push-уведомления на этом устройстве">
        <VCardText>
          <div v-if="!isPushSupported" class="text-error mb-4">
            <VIcon icon="bx-error-circle" class="me-2" />
            Ваш браузер или операционная система не поддерживают стандартные Web Push-уведомления. 
            Пожалуйста, обновите браузер или ознакомьтесь с инструкцией справа.
          </div>
          <div v-else>
            <div class="mb-4">
              <span class="font-weight-bold">Статус разрешений в браузере:</span>
              <VChip
                :color="pushPermission === 'granted' ? 'success' : pushPermission === 'denied' ? 'error' : 'warning'"
                class="ms-2 font-weight-black"
                size="small"
              >
                {{ pushPermission === 'granted' ? 'РАЗРЕШЕНО' : pushPermission === 'denied' ? 'ЗАБЛОКИРОВАНО' : 'ОЖИДАНИЕ' }}
              </VChip>
            </div>

            <div class="mb-6">
              <span class="font-weight-bold">Статус подписки на сервере:</span>
              <VChip
                :color="isSubscribed ? 'success' : 'grey'"
                class="ms-2 font-weight-black"
                size="small"
              >
                {{ isSubscribed ? 'АКТИВНА' : 'НЕАКТИВНА' }}
              </VChip>
            </div>

            <div class="d-flex flex-wrap gap-4">
              <VBtn
                v-if="!isSubscribed"
                :color="pushPermission === 'denied' ? 'error' : 'success'"
                :loading="subLoading"
                :prepend-icon="pushPermission === 'denied' ? 'bx-bell-off' : 'bx-bell'"
                @click="handlePushClick"
              >
                {{ pushPermission === 'denied' ? 'Заблокировано (Инструкция)' : 'Подписаться на Пуши' }}
              </VBtn>
              <VBtn
                v-else
                color="error"
                variant="outlined"
                :loading="subLoading"
                prepend-icon="bx-bell-off"
                @click="unsubscribeFromPush"
              >
                Отписаться
              </VBtn>

              <VBtn
                v-if="isSubscribed"
                color="secondary"
                variant="tonal"
                :loading="testLoading"
                prepend-icon="bx-paper-plane"
                @click="sendTestPush"
              >
                Тестовое пуш-уведомление
              </VBtn>
            </div>
          </div>
        </VCardText>
      </VCard>
    </VCol>

    <!-- Инструкция -->
    <VCol cols="12" md="5">
      <VCard title="Инструкция по настройке" subtitle="Как сделать, чтобы работало везде">
        <VCardText>
          <h4 class="font-weight-black text-subtitle-1 mb-2 text-primary">🖥️ На компьютерах (Windows / macOS)</h4>
          <ol class="ps-4 mb-4 text-body-2">
            <li class="mb-1">Откройте админ-панель по протоколу <b>HTTPS</b> (https://vezuroll.ru/admin). Пуши работают только по безопасному соединению.</li>
            <li class="mb-1">Нажмите кнопку <b>«Подписаться на Пуши»</b> выше.</li>
            <li class="mb-1">Когда браузер покажет запрос в левом верхнем углу, нажмите <b>«Разрешить» (Allow)</b>.</li>
            <li class="mb-1">Проверьте системные настройки Windows/macOS: убедитесь, что вашему браузеру (Chrome, Safari, Firefox) разрешено отправлять уведомления в панели уведомлений системы.</li>
          </ol>

          <h4 class="font-weight-black text-subtitle-1 mb-2 text-primary">📱 На устройствах Apple (iPhone / iPad — Все версии iOS)</h4>
          
          <div class="mb-3">
            <span class="text-caption font-weight-bold text-success">🍏 Для современных iOS (16.4 и новее):</span>
            <p class="text-caption mb-1">
              Apple добавила Web Push API только для веб-приложений, добавленных на домашний экран (PWA):
            </p>
            <ol class="ps-4 text-caption mb-2">
              <li class="mb-0.5">Откройте <b>Safari</b> и войдите в админку (https://vezuroll.ru/admin).</li>
              <li class="mb-0.5">Нажмите кнопку <b>«Поделиться»</b> (квадрат со стрелочкой вверх) внизу Safari.</li>
              <li class="mb-0.5">Выберите пункт <b>«На экран „Домой“» (Add to Home Screen)</b>. На рабочем столе появится иконка приложения.</li>
              <li class="mb-0.5">Запустите админку с домашнего экрана и нажмите <b>«Подписаться на Пуши»</b> выше.</li>
            </ol>
          </div>

          <div class="mb-3 pa-2 bg-light rounded border">
            <span class="text-caption font-weight-bold text-info">⚡ Для старых версий iOS (до 16.3 включительно):</span>
            <p class="text-caption mb-1">
              В старых версиях Safari технология прямого Web Push отсутствует на уровне самой системы iOS. Для них в панели реализована многоуровневая поддержка:
            </p>
            <ul class="ps-4 text-caption mb-0">
              <li class="mb-1"><b>Разблокировка звука на iOS:</b> при первом касании экрана в Safari активируется звуковая подсистема — все звуковые сигналы заказов, оплат и курьеров будут звучать даже при блокировке ориентации или свернутых меню.</li>
              <li class="mb-1"><b>Резервный Push в Telegram:</b> настройте Telegram-бота во вкладке <a href="/admin/settings/bot" class="text-primary font-weight-bold">«Настройки TG-Бота»</a> — системные уведомления будут приходить в мессенджер в виде нативных пушей на любых версиях iOS.</li>
              <li class="mb-1"><b>ВК-уведомления:</b> подключите шлюз ВКонтакте в <a href="/admin/settings/vk-notifications" class="text-primary font-weight-bold">«Системные рассылки»</a> для пушей в мобильное приложение VK.</li>
              <li><b>Интерактивная лента:</b> используйте вкладку <a href="/admin/notifications-feed" class="text-primary font-weight-bold">«Лента уведомлений»</a> для живого отслеживания всех событий со звуковым сопровождением.</li>
            </ul>
          </div>

          <h4 class="font-weight-black text-subtitle-1 mb-2 text-primary">🤖 На устройствах Android</h4>
          <ol class="ps-4 mb-4 text-body-2">
            <li class="mb-1">Откройте Chrome на вашем телефоне.</li>
            <li class="mb-1">Перейдите в админ-панель (https://vezuroll.ru/admin).</li>
            <li class="mb-1">Нажмите кнопку <b>«Подписаться на Пуши»</b> на этой странице.</li>
            <li class="mb-1">Разрешите отправку уведомлений во всплывающем окне браузера.</li>
          </ol>
          
          <VAlert type="info" variant="tonal" class="mt-4" density="compact">
            <span class="text-caption">
              <b>Звук уведомлений:</b> Звуковой файл проигрывается, если вкладка админки открыта или свернута. 
              Если вкладка полностью закрыта, вы получите системный Push-сигнал со стандартным звуком вашего телефона/ПК.
            </span>
          </VAlert>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <!-- Snackbar -->
  <VSnackbar
    v-model="snackbar"
    :color="snackbarColor"
    :timeout="4000"
    location="top"
  >
    {{ snackbarText }}
  </VSnackbar>

  <!-- Диалог с инструкцией по разблокировке Push -->
  <VDialog v-model="instructionDialog" max-width="500px">
    <VCard>
      <VCardTitle class="headline text-error d-flex align-center">
        <VIcon icon="bx-error" class="me-2" />
        Уведомления заблокированы
      </VCardTitle>
      <VCardText>
        <p class="mb-4">
          Похоже, вы заблокировали отправку уведомлений для этого сайта в настройках браузера. Браузер не позволяет отправлять запросы на подписку, когда разрешения отклонены.
        </p>
        <h4 class="font-weight-bold mb-2">Как разблокировать:</h4>
        <ol class="ps-4 mb-4">
          <li class="mb-2">
            В адресной строке браузера (вверху экрана, слева от <b>vezuroll.ru</b>) нажмите на иконку настроек сайта (обычно это <b>замочек 🔒</b> или <b>ползунки настроек</b>).
          </li>
          <li class="mb-2">
            Найдите пункт <b>«Уведомления»</b> (Notifications).
          </li>
          <li class="mb-2">
            Измените значение с «Блокировать» на <b>«Разрешить»</b> (Allow).
          </li>
          <li class="mb-2">
            <b>Перезагрузите страницу</b> и нажмите кнопку «Подписаться на Пуши» снова.
          </li>
        </ol>
        <div class="text-caption text-grey">
          Если вы используете мобильный телефон, эти настройки также находятся в параметрах сайта в меню браузера (три точки -> Настройки сайта -> Уведомления).
        </div>
      </VCardText>
      <VCardActions>
        <VSpacer />
        <VBtn color="primary" @click="instructionDialog = false">Хорошо, понял</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>

<style scoped>
.gap-4 {
  gap: 16px;
}
.notification-setting-card {
  border: 1px solid rgba(var(--v-border-color), 0.12);
  border-radius: 12px;
  background-color: rgba(var(--v-theme-surface), 0.4);
  transition: all 0.2s ease-in-out;
  overflow: hidden;
}
.notification-setting-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.24);
  background-color: rgba(var(--v-theme-surface), 0.8);
}
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.08);
}
.setting-row:last-child {
  border-bottom: none;
}
.setting-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: rgba(var(--v-theme-on-surface), 0.87);
}
.setting-desc {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.54);
  margin-top: 2px;
}
.border-t {
  border-top: 1px solid rgba(var(--v-border-color), 0.08);
}
.border-l-2 {
  border-left: 2px solid rgba(var(--v-theme-primary), 0.6);
}

:deep(.v-switch) {
  padding: 14px 18px;
  border: 1px solid rgba(var(--v-border-color), 0.12);
  border-radius: 12px;
  background-color: rgba(var(--v-theme-surface), 0.4);
  transition: all 0.25s ease-in-out;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}
:deep(.v-switch:hover) {
  border-color: rgba(var(--v-theme-primary), 0.3);
  background-color: rgba(var(--v-theme-surface), 0.85);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.04);
}
:deep(.v-switch.text-primary.v-switch--active) {
  border-color: rgba(var(--v-theme-primary), 0.5);
  background-color: rgba(var(--v-theme-primary), 0.06);
}
:deep(.v-switch.text-success.v-switch--active) {
  border-color: rgba(var(--v-theme-success), 0.5);
  background-color: rgba(var(--v-theme-success), 0.06);
}
:deep(.v-switch.text-warning.v-switch--active) {
  border-color: rgba(var(--v-theme-warning), 0.5);
  background-color: rgba(var(--v-theme-warning), 0.06);
}
:deep(.v-switch.text-info.v-switch--active) {
  border-color: rgba(var(--v-theme-info), 0.5);
  background-color: rgba(var(--v-theme-info), 0.06);
}
:deep(.v-switch.text-error.v-switch--active) {
  border-color: rgba(var(--v-theme-error), 0.5);
  background-color: rgba(var(--v-theme-error), 0.06);
}
:deep(.v-switch.text-indigo.v-switch--active) {
  border-color: rgba(var(--v-theme-indigo), 0.5);
  background-color: rgba(var(--v-theme-indigo), 0.06);
}
:deep(.v-switch.text-teal.v-switch--active) {
  border-color: rgba(var(--v-theme-teal), 0.5);
  background-color: rgba(var(--v-theme-teal), 0.06);
}
:deep(.v-switch.text-deep-purple.v-switch--active) {
  border-color: rgba(var(--v-theme-deep-purple), 0.5);
  background-color: rgba(var(--v-theme-deep-purple), 0.06);
}
:deep(.v-switch.text-orange.v-switch--active) {
  border-color: rgba(var(--v-theme-orange), 0.5);
  background-color: rgba(var(--v-theme-orange), 0.06);
}
:deep(.v-switch.text-orange-darken-3.v-switch--active) {
  border-color: rgba(var(--v-theme-orange), 0.5);
  background-color: rgba(var(--v-theme-orange), 0.06);
}
:deep(.v-switch .v-label) {
  font-weight: 600;
  font-size: 0.95rem;
  color: rgba(var(--v-theme-on-surface), 0.87);
  padding-left: 8px;
}
</style>
