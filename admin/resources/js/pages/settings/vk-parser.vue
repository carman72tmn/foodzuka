<script setup>
import { ref, onMounted, computed } from "vue"
import { hasPermission, getAuthHeaders } from "@/utils/auth"

const tabs = computed(() => {
  const allTabs = [
    { id: 0, title: 'Настройки и статистика', permission: 'vk_parser_tab_settings_view' },
    { id: 1, title: 'Настройка уведомлений ВК', permission: 'vk_parser_tab_notifications_view' },
    { id: 2, title: 'Мониторинг сообщений', permission: 'vk_parser_tab_monitoring_view' },
    { id: 3, title: 'Связанные аккаунты ВК', permission: 'vk_parser_tab_accounts_view' }
  ]
  return allTabs.filter(t => hasPermission(t.permission))
})

const loading = ref(false)
const saving = ref(false)
const snackbar = ref(false)

const notifications = ref([])
const globalDeliveryEnabled = ref(false)
const globalPickupEnabled = ref(false)

const dialogOpen = ref(false)
const dialogMode = ref('create')
const editIndex = ref(-1)

const formNotification = ref({
  type: 'delivery',
  status: '',
  enabled: true,
  template: ''
})
const snackbarColor = ref("success")
const snackbarText = ref("")

const deliveryStatusList = [
  { value: "confirmed", title: "Заказ подтвержден" },
  { value: "cooking", title: "Заказ готовится" },
  { value: "ready", title: "Заказ готов" },
  { value: "delivering", title: "Курьер в пути" },
  { value: "delivered", title: "Заказ доставлен" },
  { value: "cancelled", title: "Заказ отменен" }
]

const pickupStatusList = [
  { value: "confirmed", title: "Заказ подтвержден" },
  { value: "cooking", title: "Заказ готовится" },
  { value: "ready", title: "Заказ готов к выдаче" },
  { value: "cancelled", title: "Заказ отменен" }
]

const ensureNotificationSettings = (rawSettings) => {
  const defaultSettings = {
    delivery: {
      enabled: false,
      statuses: {
        confirmed: { enabled: false, template: "" },
        cooking: { enabled: false, template: "" },
        ready: { enabled: false, template: "" },
        delivering: { enabled: false, template: "" },
        delivered: { enabled: false, template: "" },
        cancelled: { enabled: false, template: "" }
      }
    },
    pickup: {
      enabled: false,
      statuses: {
        confirmed: { enabled: false, template: "" },
        cooking: { enabled: false, template: "" },
        ready: { enabled: false, template: "" },
        cancelled: { enabled: false, template: "" }
      }
    }
  }

  if (!rawSettings) return defaultSettings

  const merged = { ...defaultSettings }

  // Слияние доставки
  if (rawSettings.delivery) {
    merged.delivery.enabled = !!rawSettings.delivery.enabled
    if (rawSettings.delivery.statuses) {
      Object.keys(defaultSettings.delivery.statuses).forEach(status => {
        if (rawSettings.delivery.statuses[status]) {
          merged.delivery.statuses[status].enabled = !!rawSettings.delivery.statuses[status].enabled
          merged.delivery.statuses[status].template = rawSettings.delivery.statuses[status].template || ""
        }
      })
    } else if (rawSettings.delivery.enabled_statuses && rawSettings.delivery.templates) {
      rawSettings.delivery.enabled_statuses.forEach(status => {
        if (merged.delivery.statuses[status]) {
          merged.delivery.statuses[status].enabled = true
          merged.delivery.statuses[status].template = rawSettings.delivery.templates[status] || ""
        }
      })
    }
  }

  // Слияние самовывоза
  if (rawSettings.pickup) {
    merged.pickup.enabled = !!rawSettings.pickup.enabled
    if (rawSettings.pickup.statuses) {
      Object.keys(defaultSettings.pickup.statuses).forEach(status => {
        if (rawSettings.pickup.statuses[status]) {
          merged.pickup.statuses[status].enabled = !!rawSettings.pickup.statuses[status].enabled
          merged.pickup.statuses[status].template = rawSettings.pickup.statuses[status].template || ""
        }
      })
    } else if (rawSettings.pickup.enabled_statuses && rawSettings.pickup.templates) {
      rawSettings.pickup.enabled_statuses.forEach(status => {
        if (merged.pickup.statuses[status]) {
          merged.pickup.statuses[status].enabled = true
          merged.pickup.statuses[status].template = rawSettings.pickup.templates[status] || ""
        }
      })
    }
  }

  return merged
}

const settings = ref({
  vk_parser_enabled: false,
  vk_parser_phrase: "здравствуйте! Ваш заказ {order_id} принят и мы приступили к его приготовлению",
  vk_parser_mask: "",
  vk_parser_ignored_ids: "",
  vk_app_id: "",
  vk_app_secret: "",
  vk_notification_settings: ensureNotificationSettings(null)
})

const insertVariable = (type, statusValue, variable) => {
  const textarea = document.getElementById(`template-${type}-${statusValue}`)
  if (textarea) {
    const text = settings.value.vk_notification_settings[type].statuses[statusValue].template || ""
    const start = textarea.selectionStart || 0
    const end = textarea.selectionEnd || 0
    const newText = text.substring(0, start) + variable + text.substring(end)
    settings.value.vk_notification_settings[type].statuses[statusValue].template = newText
    
    setTimeout(() => {
      textarea.focus()
      textarea.setSelectionRange(start + variable.length, start + variable.length)
    }, 50)
  } else {
    settings.value.vk_notification_settings[type].statuses[statusValue].template = 
      (settings.value.vk_notification_settings[type].statuses[statusValue].template || "") + variable
  }
}

const availableStatuses = computed(() => {
  const list = formNotification.value.type === 'delivery' ? deliveryStatusList : pickupStatusList
  return list.filter(s => {
    if (dialogMode.value === 'edit' && s.value === notifications.value[editIndex.value]?.status) {
      return true
    }
    return !notifications.value.some(n => n.type === formNotification.value.type && n.status === s.value)
  })
})

const availableStatusesCount = computed(() => {
  const deliveryLeft = deliveryStatusList.filter(s => !notifications.value.some(n => n.type === 'delivery' && n.status === s.value)).length
  const pickupLeft = pickupStatusList.filter(s => !notifications.value.some(n => n.type === 'pickup' && n.status === s.value)).length
  return deliveryLeft + pickupLeft
})

const onFormTypeChange = () => {
  const statuses = availableStatuses.value
  if (statuses.length > 0) {
    formNotification.value.status = statuses[0].value
  } else {
    formNotification.value.status = ''
  }
}

const openCreateDialog = () => {
  dialogMode.value = 'create'
  editIndex.value = -1
  
  const availableDelivery = deliveryStatusList.filter(s => !notifications.value.some(n => n.type === 'delivery' && n.status === s.value))
  const availablePickup = pickupStatusList.filter(s => !notifications.value.some(n => n.type === 'pickup' && n.status === s.value))
  
  let defaultType = 'delivery'
  let defaultStatus = ''
  
  if (availableDelivery.length > 0) {
    defaultStatus = availableDelivery[0].value
  } else if (availablePickup.length > 0) {
    defaultType = 'pickup'
    defaultStatus = availablePickup[0].value
  }
  
  formNotification.value = {
    type: defaultType,
    status: defaultStatus,
    enabled: true,
    template: ''
  }
  dialogOpen.value = true
}

const openEditDialog = (index) => {
  dialogMode.value = 'edit'
  editIndex.value = index
  const item = notifications.value[index]
  formNotification.value = {
    type: item.type,
    status: item.status,
    enabled: item.enabled,
    template: item.template
  }
  dialogOpen.value = true
}

const deleteNotification = (index) => {
  if (confirm("Вы уверены, что хотите удалить это уведомление?")) {
    notifications.value.splice(index, 1)
    saveSettings()
  }
}

const saveNotificationForm = () => {
  if (!formNotification.value.status) {
    showMessage("Пожалуйста, выберите событие", "error")
    return
  }
  
  if (dialogMode.value === 'create') {
    const exists = notifications.value.some(n => n.type === formNotification.value.type && n.status === formNotification.value.status)
    if (exists) {
      showMessage("Уведомление для этого события уже создано", "error")
      return
    }
    notifications.value.push({ ...formNotification.value })
  } else {
    notifications.value[editIndex.value] = { ...formNotification.value }
  }
  
  dialogOpen.value = false
  saveSettings()
}

const insertVariableToDialog = (variable) => {
  const textarea = document.getElementById('dialog-template-textarea')
  if (textarea) {
    const text = formNotification.value.template || ""
    const start = textarea.selectionStart || 0
    const end = textarea.selectionEnd || 0
    const newText = text.substring(0, start) + variable + text.substring(end)
    formNotification.value.template = newText
    
    setTimeout(() => {
      textarea.focus()
      textarea.setSelectionRange(start + variable.length, start + variable.length)
    }, 50)
  } else {
    formNotification.value.template = (formNotification.value.template || "") + variable
  }
}

const getStatusName = (type, value) => {
  const list = type === 'delivery' ? deliveryStatusList : pickupStatusList
  const found = list.find(s => s.value === value)
  return found ? found.title : value
}

const getStatusColor = (value) => {
  const colors = {
    confirmed: 'info',
    cooking: 'warning',
    ready: 'success',
    delivering: 'primary',
    delivered: 'success',
    cancelled: 'error'
  }
  return colors[value] || 'grey'
}

const API_BASE = "/api/v1/vk"


const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const scanStatus = ref({ status: "idle" })
const isScanning = ref(false)

const unlinking = ref(false)
const confirmUnlinkDialog = ref(false)
const userToUnlink = ref(null)

// Загрузка текущих настроек
const loadSettings = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/settings`, { headers: getAuthHeaders() })
    if (res.ok) {
      const data = await res.json()
      settings.value.vk_parser_enabled = !!data.vk_parser_enabled
      if (data.vk_parser_phrase) {
        settings.value.vk_parser_phrase = data.vk_parser_phrase
      }
      settings.value.vk_parser_mask = data.vk_parser_mask || ""
      settings.value.vk_parser_ignored_ids = data.vk_parser_ignored_ids || ""
      settings.value.vk_app_id = data.vk_app_id || ""
      settings.value.vk_app_secret = data.vk_app_secret || ""
      const notifSettings = ensureNotificationSettings(data.vk_notification_settings)
      settings.value.vk_notification_settings = notifSettings
      globalDeliveryEnabled.value = !!notifSettings.delivery?.enabled
      globalPickupEnabled.value = !!notifSettings.pickup?.enabled
      
      const parsed = []
      if (notifSettings.delivery?.statuses) {
        Object.keys(notifSettings.delivery.statuses).forEach(status => {
          const s = notifSettings.delivery.statuses[status]
          if (s.enabled || s.template) {
            parsed.push({
              type: 'delivery',
              status: status,
              enabled: !!s.enabled,
              template: s.template || ''
            })
          }
        })
      }
      if (notifSettings.pickup?.statuses) {
        Object.keys(notifSettings.pickup.statuses).forEach(status => {
          const s = notifSettings.pickup.statuses[status]
          if (s.enabled || s.template) {
            parsed.push({
              type: 'pickup',
              status: status,
              enabled: !!s.enabled,
              template: s.template || ''
            })
          }
        })
      }
      notifications.value = parsed
      
      // Загружаем статус сканирования
      if (data.vk_parser_scan_status) {
        scanStatus.value = data.vk_parser_scan_status
        if (scanStatus.value.status === "running") {
          isScanning.value = true
          setTimeout(checkScanStatus, 3000)
        }
      }
    }
  } catch (e) {
    showMessage("Ошибка загрузки настроек", "error")
  } finally {
    loading.value = false
  }
}

// Проверка статуса сканирования
const checkScanStatus = async () => {
  try {
    const res = await fetch(`${API_BASE}/parser/scan/status`, { headers: getAuthHeaders() })
    if (res.ok) {
      const data = await res.json()
      scanStatus.value = data
      if (data.status === "running") {
        isScanning.value = true
        setTimeout(checkScanStatus, 3000)
      } else {
        isScanning.value = false
        if (data.status === "completed") {
          showMessage("Сканирование истории завершено!")
        } else if (data.status === "error") {
          showMessage(`Ошибка сканирования: ${data.error}`, "error")
        }
      }
    }
  } catch (e) {
    console.error("Error polling scan status:", e)
  }
}

// Запуск сканирования
const startScan = async () => {
  isScanning.value = true
  try {
    const res = await fetch(`${API_BASE}/parser/scan`, {
      method: "POST",
      headers: getAuthHeaders()
    })
    if (res.ok) {
      showMessage("Задача сканирования добавлена в очередь")
      scanStatus.value = { status: "running", progress: 0, total: 0, matches: 0 }
      setTimeout(checkScanStatus, 2000)
    } else {
      const err = await res.json()
      showMessage(err.message || "Ошибка запуска", "error")
      isScanning.value = false
    }
  } catch (e) {
    showMessage("Ошибка подключения", "error")
    isScanning.value = false
  }
}

// Удаление привязки
const confirmUnlink = (user) => {
  userToUnlink.value = user
  confirmUnlinkDialog.value = true
}

const unlinkUser = async () => {
  if (!userToUnlink.value) return
  
  unlinking.value = true
  try {
    const res = await fetch(`${API_BASE}/parser/users/${userToUnlink.value.vk_id}/link`, {
      method: "DELETE",
      headers: getAuthHeaders()
    })
    
    if (res.ok) {
      showMessage("Привязка успешно удалена")
      await loadStats()
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка удаления", "error")
    }
  } catch (e) {
    showMessage("Ошибка подключения", "error")
  } finally {
    unlinking.value = false
    confirmUnlinkDialog.value = false
    userToUnlink.value = null
  }
}

// Сохранение настроек
const saveSettings = async () => {
  saving.value = true
  
  // Собираем vk_notification_settings из notifications и глобальных флагов
  const notifSettings = {
    delivery: {
      enabled: globalDeliveryEnabled.value,
      statuses: {
        confirmed: { enabled: false, template: "" },
        cooking: { enabled: false, template: "" },
        ready: { enabled: false, template: "" },
        delivering: { enabled: false, template: "" },
        delivered: { enabled: false, template: "" },
        cancelled: { enabled: false, template: "" }
      }
    },
    pickup: {
      enabled: globalPickupEnabled.value,
      statuses: {
        confirmed: { enabled: false, template: "" },
        cooking: { enabled: false, template: "" },
        ready: { enabled: false, template: "" },
        cancelled: { enabled: false, template: "" }
      }
    }
  }

  notifications.value.forEach(n => {
    if (notifSettings[n.type]?.statuses[n.status]) {
      notifSettings[n.type].statuses[n.status] = {
        enabled: n.enabled,
        template: n.template
      }
    }
  })

  settings.value.vk_notification_settings = notifSettings

  try {
    // Сначала получаем все настройки, чтобы не затереть другие поля
    const currentRes = await fetch(`${API_BASE}/settings`, { headers: getAuthHeaders() })
    let currentData = {}
    if (currentRes.ok) {
      currentData = await currentRes.json()
    }

    const payload = {
      ...currentData,
      vk_parser_enabled: settings.value.vk_parser_enabled,
      vk_parser_phrase: settings.value.vk_parser_phrase,
      vk_parser_mask: settings.value.vk_parser_mask,
      vk_parser_ignored_ids: settings.value.vk_parser_ignored_ids,
      vk_notification_settings: settings.value.vk_notification_settings,
      vk_app_id: settings.value.vk_app_id,
      vk_app_secret: settings.value.vk_app_secret,
    }

    const res = await fetch(`${API_BASE}/settings`, {
      method: "POST",
      headers: {
        ...getAuthHeaders(),
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload),
    })

    if (res.ok) {
      showMessage("Настройки парсера успешно сохранены")
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка сохранения", "error")
    }
  } catch (e) {
    showMessage("Ошибка подключения к серверу", "error")
  } finally {
    saving.value = false
  }
}

const stats = ref({ summary: { total_linked: 0, linked_realtime: 0, linked_history: 0 }, recent_links: [] })
const activeTab = ref(null)
const notificationTypeTab = ref("delivery")

// Сообщения
const messages = ref([])
const messageStats = ref({ total: 0, inbound: 0, outbound: 0 })
const messagesLoading = ref(false)
const messagePage = ref(1)
const totalMessagePages = ref(1)
const messageSearch = ref("")
const messageDirection = ref(null)
const messageDate = ref(new Date().toISOString().substr(0, 10)) // ГГГГ-ММ-ДД

const loadMessageStats = async () => {
  try {
    let url = `${API_BASE}/parser/messages/stats`
    if (messageDate.value) url += `?date=${messageDate.value}`
    
    const res = await fetch(url, { headers: getAuthHeaders() })
    if (res.ok) {
      messageStats.value = await res.json()
    }
  } catch (e) {
    console.error("Error loading message stats:", e)
  }
}

const loadMessages = async () => {
  messagesLoading.value = true
  try {
    let url = `${API_BASE}/parser/messages?page=${messagePage.value}`
    if (messageSearch.value) url += `&search=${encodeURIComponent(messageSearch.value)}`
    if (messageDirection.value) url += `&direction=${messageDirection.value}`
    if (messageDate.value) url += `&date=${messageDate.value}`
    
    const res = await fetch(url, { headers: getAuthHeaders() })
    if (res.ok) {
      const data = await res.json()
      messages.value = data.items
      totalMessagePages.value = data.total_pages
    }
  } catch (e) {
    console.error("Error loading messages:", e)
    showMessage("Ошибка загрузки сообщений", "error")
  } finally {
    messagesLoading.value = false
  }
}

const cleaning = ref(false)
const cleanupMessages = async () => {
  if (!confirm("Вы уверены, что хотите удалить все сообщения старше 90 дней?")) return
  
  cleaning.value = true
  try {
    const res = await fetch(`${API_BASE}/parser/messages/cleanup`, {
      method: "POST",
      headers: getAuthHeaders()
    })
    if (res.ok) {
      const data = await res.json()
      showMessage(data.message || "Очистка завершена")
      await loadMessageStats()
      await loadMessages()
    } else {
      showMessage("Ошибка при очистке", "error")
    }
  } catch (e) {
    showMessage("Ошибка подключения", "error")
  } finally {
    cleaning.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await fetch(`${API_BASE}/parser/stats`, { headers: getAuthHeaders() })
    if (res.ok) {
      stats.value = await res.json()
    }
  } catch (e) {
    console.error("Error loading stats:", e)
  }
}

// Связанные аккаунты гостей
const linkedAccounts = ref([])
const linkedAccountsLoading = ref(false)
const linkedAccountsPage = ref(1)
const totalLinkedAccountsPages = ref(1)
const linkedAccountsSearch = ref("")
const linkedAccountsFilterStatus = ref("all") // all, active, blocked

const loadLinkedAccounts = async () => {
  linkedAccountsLoading.value = true
  try {
    let url = `/api/v1/vk/parser/linked-accounts?page=${linkedAccountsPage.value}`
    if (linkedAccountsSearch.value) {
      url += `&search=${encodeURIComponent(linkedAccountsSearch.value)}`
    }
    if (linkedAccountsFilterStatus.value) {
      url += `&filter_status=${linkedAccountsFilterStatus.value}`
    }
    const res = await fetch(url, { headers: getAuthHeaders() })
    if (res.ok) {
      const data = await res.json()
      linkedAccounts.value = data.items
      totalLinkedAccountsPages.value = data.total_pages
    }
  } catch (e) {
    console.error("Error loading linked accounts:", e)
    showMessage("Ошибка загрузки связанных аккаунтов", "error")
  } finally {
    linkedAccountsLoading.value = false
  }
}

const toggleLinkedAccountFlag = async (account, flagName) => {
  try {
    const updatedValue = !account[flagName]
    const payload = {
      [flagName]: updatedValue
    }
    const res = await fetch(`/api/v1/vk/parser/linked-accounts/${account.vk_id}`, {
      method: "PATCH",
      headers: {
        ...getAuthHeaders(),
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    })
    if (res.ok) {
      account[flagName] = updatedValue
      showMessage("Настройки аккаунта обновлены")
    } else {
      showMessage("Ошибка обновления настроек", "error")
    }
  } catch (e) {
    showMessage("Ошибка подключения к серверу", "error")
  }
}

onMounted(async () => {
  await loadSettings()
  await loadStats()
  await loadMessageStats()
  await loadMessages()
  await loadLinkedAccounts()
  activeTab.value = tabs.value.length ? tabs.value[0].id : null
})
</script>

<template>
  <VTabs v-model="activeTab" class="mb-4" v-if="tabs.length">
    <VTab
      v-for="tab in tabs"
      :key="tab.id"
      :value="tab.id"
    >
      <VIcon
        :icon="
          tab.id === 0 ? 'mdi-cog' :
          tab.id === 1 ? 'mdi-bell-ring' :
          tab.id === 2 ? 'mdi-message-text' :
          'mdi-account-multiple'
        "
        class="me-2"
      />
      {{ tab.title }}
    </VTab>
  </VTabs>

  <VWindow v-model="activeTab">
    <VWindowItem :value="0">
      <VRow>
    <VCol cols="12">
      <VCard>
        <VCardTitle class="d-flex align-center">
          <VIcon icon="mdi-message-search-outline" class="me-2" color="primary" />
          Настройки Парсера ВК
        </VCardTitle>
        <VCardText>
          <p class="text-body-1 mb-6">
            Парсер автоматически анализирует входящие и исходящие сообщения в VK. 
            Если в сообщении обнаружена ключевая фраза с номером заказа, система автоматически связывает 
            профиль пользователя VK с его картой гостя в базе данных.
          </p>

          <fieldset :disabled="!hasPermission('vk_parser_tab_settings_edit')" class="border-0 pa-0 ma-0 w-100">
          <VRow>
            <VCol cols="12">
              <VSwitch
                v-model="settings.vk_parser_enabled"
                label="Активировать автоматический парсинг"
                color="success"
                hint="Если включено, система будет искать номер заказа в каждом сообщении"
                persistent-hint
              />
            </VCol>

            <VCol cols="12" class="mt-4">
              <VTextarea
                v-model="settings.vk_parser_phrase"
                label="Ключевая фраза для поиска"
                rows="3"
                hint="Используйте {order_id} там, где должен быть номер заказа"
                persistent-hint
                placeholder="здравствуйте! Ваш заказ {order_id} принят..."
              />
            </VCol>

            <VCol cols="12" class="mt-4">
              <VTextField
                v-model="settings.vk_parser_mask"
                label="Маска номера заказа (order_id)"
                hint="Допускаются символы, буквы, цифры для фиксированных значений и звездочки (*) для случайных (например, 'RU-***'). Оставьте пустым или '*', чтобы принимать любые заказы."
                persistent-hint
                placeholder="Например, RU-***"
                clearable
              />
            </VCol>

            <VCol cols="12" class="mt-4">
              <VTextField
                v-model="settings.vk_parser_ignored_ids"
                label="Игнорируемые ID аккаунтов VK"
                hint="ID аккаунтов ВКонтакте через запятую, которые не участвуют в парсинге (сообщения от них не будут привязываться и сохраняться в базу)."
                persistent-hint
                placeholder="Например: 12345, 67890"
                clearable
              />
            </VCol>

            <VCol cols="12">
              <VAlert
                type="info"
                variant="tonal"
                class="mt-4"
              >
                <strong>Как это работает:</strong>
                <ul class="mt-2">
                  <li>Система отслеживает события <code>message_new</code> (от пользователя) и <code>message_reply</code> (от бота).</li>
                  <li>Если текст совпадает с шаблоном, извлекается номер заказа.</li>
                  <li>По номеру заказа находится телефон клиента и его ID в iiko.</li>
                  <li>Данные сохраняются в профиль клиента, обеспечивая полную связку.</li>
                </ul>
              </VAlert>
            </VCol>

            <VCol cols="12" class="d-flex gap-4 mt-4" v-if="hasPermission('vk_parser_tab_settings_edit')">
              <VBtn
                color="primary"
                :loading="saving"
                prepend-icon="mdi-content-save"
                @click="saveSettings"
              >
                Сохранить настройки
              </VBtn>
            </VCol>
          </VRow>
          </fieldset>
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12" class="mt-6">
      <VCard>
        <VCardTitle class="d-flex align-center">
          <VIcon icon="bxl-vk" class="me-2" color="primary" />
          Настройки Авторизации ВК (OAuth App)
        </VCardTitle>
        <VCardText>
          <p class="text-body-1 mb-6">
            Укажите ID приложения (VK App ID) и защищенный ключ (VK App Secret) для работы OAuth-авторизации, 
            которая позволяет сотрудникам привязывать личные аккаунты ВКонтакте в профиле.
          </p>

          <fieldset :disabled="!hasPermission('vk_parser_tab_settings_edit')" class="border-0 pa-0 ma-0 w-100">
            <VRow>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.vk_app_id"
                  label="VK App ID (ID приложения)"
                  hint="ID созданного Standalone/Веб-приложения в кабинете разработчика VK"
                  persistent-hint
                  placeholder="Например: 51234567"
                  clearable
                />
              </VCol>

              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.vk_app_secret"
                  label="VK App Secret (Защищенный ключ)"
                  hint="Защищенный ключ приложения (из вкладки Настройки вашего VK App)"
                  persistent-hint
                  placeholder="Например: aBcDeFgHiJkLmNoP"
                  type="password"
                  clearable
                />
              </VCol>

              <VCol cols="12">
                <VAlert
                  type="warning"
                  variant="tonal"
                  class="mt-4"
                >
                  <strong>Важно для работы привязки ВК:</strong>
                  <ul class="mt-2">
                    <li>В настройках вашего приложения ВКонтакте (в разделе <strong>Настройки -> Доверенный URL</strong>) должен быть строго указан Redirect URI:</li>
                    <li><code class="text-primary font-weight-bold bg-grey-lighten-3 px-2 py-1 rounded">https://vezuroll.ru/api/v1/auth/vk/callback</code></li>
                    <li>Доверенный домен приложения должен быть настроен как: <code class="font-weight-bold bg-grey-lighten-3 px-2 py-1 rounded">vezuroll.ru</code></li>
                  </ul>
                </VAlert>
              </VCol>

              <VCol cols="12" class="d-flex gap-4 mt-4" v-if="hasPermission('vk_parser_tab_settings_edit')">
                <VBtn
                  color="primary"
                  :loading="saving"
                  prepend-icon="mdi-content-save"
                  @click="saveSettings"
                >
                  Сохранить настройки OAuth
                </VBtn>
              </VCol>
            </VRow>
          </fieldset>
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12">
      <VCard>
        <VCardTitle class="d-flex align-center">
          <VIcon icon="mdi-history" class="me-2" color="secondary" />
          Ретроспективное сканирование
        </VCardTitle>
        <VCardText>
          <p class="text-body-1 mb-4">
            Вы можете просканировать всю историю сообщений группы, чтобы автоматически привязать клиентов, которые писали ранее. 
            Это полезно, если у вас уже есть большая база переписки.
          </p>

          <div v-if="scanStatus.status === 'running'" class="mt-6 mb-6">
            <div class="d-flex justify-space-between mb-2">
              <span class="text-subtitle-2">Идет сканирование истории...</span>
              <span class="text-subtitle-2">{{ Math.round((scanStatus.progress / (scanStatus.total || 1)) * 100) }}%</span>
            </div>
            <VProgressLinear
              :model-value="(scanStatus.progress / (scanStatus.total || 1)) * 100"
              height="24"
              color="primary"
              striped
              rounded
            >
              <template v-slot:default="{ value }">
                <span class="text-white">{{ Math.round(value) }}%</span>
              </template>
            </VProgressLinear>
            <div class="mt-4 d-flex justify-space-between text-caption text-medium-emphasis">
              <span>Обработано диалогов: {{ scanStatus.progress }} / {{ scanStatus.total }}</span>
              <span>Найдено совпадений: <strong>{{ scanStatus.matches }}</strong></span>
            </div>
          </div>

          <div v-else>
            <div v-if="scanStatus.status === 'completed'" class="mb-4">
              <VAlert type="success" variant="tonal" density="compact" class="mb-4">
                Последнее сканирование завершено: {{ new Date(scanStatus.completed_at).toLocaleString() }}.
                Найдено связок: <strong>{{ scanStatus.matches }}</strong>
              </VAlert>
            </div>
            
            <div v-if="scanStatus.status === 'error'" class="mb-4">
              <VAlert type="error" variant="tonal" density="compact" class="mb-4">
                Ошибка при последнем сканировании: {{ scanStatus.error }}
              </VAlert>
            </div>

            <VBtn
              color="secondary"
              :loading="isScanning"
              prepend-icon="mdi-refresh-circle"
              v-if="hasPermission('vk_parser_tab_settings_edit')"
              @click="startScan"
            >
              Запустить полное сканирование истории
            </VBtn>
            
            <p class="text-caption text-medium-emphasis mt-2">
              Внимание: процесс может занять несколько минут в зависимости от количества сообщений.
            </p>
          </div>
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12">
      <VCard>
        <VCardTitle class="d-flex align-center">
          <VIcon icon="mdi-chart-bar" class="me-2" color="success" />
          Статистика привязок
        </VCardTitle>
        <VCardText>
          <VRow class="mb-6">
            <VCol cols="12" md="4">
              <VCard variant="tonal" color="primary">
                <VCardText class="text-center">
                  <div class="text-h4 font-weight-bold">{{ stats.summary.total_linked }}</div>
                  <div class="text-caption">Всего привязано</div>
                </VCardText>
              </VCard>
            </VCol>
            <VCol cols="12" md="4">
              <VCard variant="tonal" color="success">
                <VCardText class="text-center">
                  <div class="text-h4 font-weight-bold">{{ stats.summary.linked_realtime }}</div>
                  <div class="text-caption">Через чат (Realtime)</div>
                </VCardText>
              </VCard>
            </VCol>
            <VCol cols="12" md="4">
              <VCard variant="tonal" color="secondary">
                <VCardText class="text-center">
                  <div class="text-h4 font-weight-bold">{{ stats.summary.linked_history }}</div>
                  <div class="text-caption">Через сканер истории</div>
                </VCardText>
              </VCard>
            </VCol>
          </VRow>

          <h3 class="text-h6 mb-4">Последние 20 связок</h3>
          <VTable class="text-no-wrap">
            <thead>
              <tr>
                <th>VK ID</th>
                <th>Телефон</th>
                <th>Источник</th>
                <th>Дата привязки</th>
                <th>Заказ</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="link in stats.recent_links" :key="link.vk_id">
                <td>
                  <a :href="`https://vk.com/id${link.vk_id}`" target="_blank" class="text-decoration-none">
                    {{ link.vk_id }}
                    <VIcon icon="mdi-open-in-new" size="x-small" />
                  </a>
                </td>
                <td>{{ link.phone }}</td>
                <td>
                  <VChip
                    size="x-small"
                    :color="link.linking_source === 'parser_history' ? 'secondary' : 'success'"
                  >
                    {{ link.linking_source === 'parser_history' ? 'История' : 'Чат' }}
                  </VChip>
                </td>
                <td>{{ link.linked_at ? new Date(link.linked_at).toLocaleString() : '—' }}</td>
                <td>
                  <VChip size="x-small" variant="outlined" v-if="link.last_order_id">
                    #{{ link.last_order_id }}
                  </VChip>
                  <span v-else>—</span>
                </td>
                <td>
                  <VBtn
                    icon="mdi-account-details"
                    variant="text"
                    size="small"
                    color="info"
                    title="Перейти к клиенту"
                    :to="`/clients/${link.iiko_customer_id}`"
                    v-if="link.iiko_customer_id"
                  />
                  <VBtn
                    icon="mdi-delete-outline"
                    variant="text"
                    size="small"
                    color="error"
                    title="Удалить привязку"
                    @click="confirmUnlink(link)"
                  />
                </td>
              </tr>
              <tr v-if="stats.recent_links.length === 0">
                <td colspan="6" class="text-center py-4 text-medium-emphasis">
                  Данные о связках отсутствуют
                </td>
              </tr>
            </tbody>
          </VTable>
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12">
      <VCard>
        <VCardTitle>Статус привязки</VCardTitle>
        <VCardText>
          <p>Автоматическая привязка позволяет:</p>
          <VList density="compact">
            <VListItem prepend-icon="mdi-check-circle-outline">
              Узнавать клиента по его VK ID при следующем обращении.
            </VListItem>
            <VListItem prepend-icon="mdi-check-circle-outline">
              Автоматически начислять баллы за активность в группе тем, кто уже делал заказы.
            </VListItem>
            <VListItem prepend-icon="mdi-check-circle-outline">
              Отправлять персонализированные уведомления о статусе заказа прямо в ЛС ВКонтакте.
            </VListItem>
          </VList>
        </VCardText>
      </VCard>
    </VCol>
      </VRow>
    </VWindowItem>

    <!-- Вкладка Настройка уведомлений -->
    <VWindowItem :value="1">
      <VRow>
        <VCol cols="12">
          <VCard>
            <VCardTitle class="d-flex align-center flex-wrap gap-4 py-4">
              <div>
                <VIcon icon="mdi-bell-cog-outline" class="me-2" color="primary" />
                Конструктор уведомлений клиентов
              </div>
              <VSpacer />
              <VBtn
                color="primary"
                prepend-icon="mdi-plus"
                v-if="hasPermission('vk_parser_tab_notifications_edit')"
                @click="openCreateDialog"
                :disabled="availableStatusesCount === 0"
              >
                Создать уведомление
              </VBtn>
            </VCardTitle>
            <VCardText>
              <p class="text-body-2 mb-6">
                Настройте автоматические сообщения, которые будут приходить клиенту в ЛС ВКонтакте при изменении статуса его заказа. 
                Уведомления приходят только привязанным гостям, разрешившим отправку сообщений.
              </p>

              <!-- Глобальные переключатели каналов -->
              <VRow class="mb-6">
                <VCol cols="12" md="6">
                  <VCard variant="outlined" class="pa-4 d-flex align-center">
                    <VIcon icon="mdi-truck-delivery-outline" size="36" class="me-4" color="primary" />
                    <div>
                      <div class="text-subtitle-1 font-weight-bold">Доставка заказов</div>
                      <div class="text-caption text-medium-emphasis">Глобальный переключатель рассылки на доставку</div>
                    </div>
                    <VSpacer />
                    <VSwitch
                      v-model="globalDeliveryEnabled"
                      color="success"
                      hide-details
                      :disabled="!hasPermission('vk_parser_tab_notifications_edit')"
                      @update:model-value="saveSettings"
                    />
                  </VCard>
                </VCol>
                <VCol cols="12" md="6">
                  <VCard variant="outlined" class="pa-4 d-flex align-center">
                    <VIcon icon="mdi-storefront-outline" size="36" class="me-4" color="primary" />
                    <div>
                      <div class="text-subtitle-1 font-weight-bold">Самовывоз заказов</div>
                      <div class="text-caption text-medium-emphasis">Глобальный переключатель рассылки на самовывоз</div>
                    </div>
                    <VSpacer />
                    <VSwitch
                      v-model="globalPickupEnabled"
                      color="success"
                      hide-details
                      :disabled="!hasPermission('vk_parser_tab_notifications_edit')"
                      @update:model-value="saveSettings"
                    />
                  </VCard>
                </VCol>
              </VRow>

              <VDivider class="mb-6" />

              <!-- Список уведомлений -->
              <div v-if="notifications.length === 0" class="text-center py-12 text-disabled border rounded-lg bg-var-theme-background">
                <VIcon icon="mdi-bell-off-outline" size="64" class="mb-4" color="grey-lighten-1" />
                <div class="text-h6 font-weight-bold mb-2">Уведомления не созданы</div>
                <p class="text-body-2 mb-6 text-medium-emphasis">
                  Вы можете добавить уведомления для событий доставки или самовывоза, нажав кнопку ниже.
                </p>
                <VBtn
                  color="primary"
                  prepend-icon="mdi-plus"
                  v-if="hasPermission('vk_parser_tab_notifications_edit')"
                  @click="openCreateDialog"
                >
                  Создать первое уведомление
                </VBtn>
              </div>

              <VRow v-else>
                <VCol
                  cols="12"
                  md="6"
                  v-for="(notif, idx) in notifications"
                  :key="`${notif.type}-${notif.status}`"
                >
                  <VCard variant="outlined" class="d-flex flex-column h-100 position-relative overflow-hidden" style="border-left: 6px solid !important;" :style="{ 'border-left-color': notif.type === 'delivery' ? 'var(--v-theme-primary)' : 'var(--v-theme-secondary)' + ' !important' }">
                    <VCardItem class="pb-2">
                      <div class="d-flex align-center justify-space-between w-100">
                        <div class="d-flex align-center">
                          <VIcon 
                            :icon="notif.type === 'delivery' ? 'mdi-truck-delivery-outline' : 'mdi-storefront-outline'" 
                            class="me-2" 
                            :color="notif.type === 'delivery' ? 'primary' : 'secondary'"
                          />
                          <span class="text-caption text-medium-emphasis font-weight-bold uppercase">
                            {{ notif.type === 'delivery' ? 'Доставка' : 'Самовывоз' }}
                          </span>
                        </div>
                        <VChip
                          size="small"
                          :color="getStatusColor(notif.status)"
                          variant="tonal"
                          class="font-weight-bold"
                        >
                          {{ getStatusName(notif.type, notif.status) }}
                        </VChip>
                      </div>
                    </VCardItem>

                    <VCardText class="flex-grow-1 py-2">
                      <div class="bg-grey-lighten-4 pa-3 rounded-lg text-body-2 text-pre-wrap font-monospace overflow-y-auto" style="max-height: 120px; height: 120px;">
                        {{ notif.template || 'Шаблон сообщения пуст...' }}
                      </div>
                    </VCardText>

                    <VDivider />

                    <VCardActions class="pa-3">
                      <VSwitch
                        v-model="notif.enabled"
                        color="success"
                        density="compact"
                        hide-details
                        :disabled="!hasPermission('vk_parser_tab_notifications_edit')"
                        @update:model-value="saveSettings"
                        label="Активно"
                      />
                      <VSpacer />
                      <VBtn
                        icon="mdi-pencil-outline"
                        variant="text"
                        size="small"
                        color="info"
                        v-if="hasPermission('vk_parser_tab_notifications_edit')"
                        @click="openEditDialog(idx)"
                        title="Редактировать"
                      />
                      <VBtn
                        icon="mdi-delete-outline"
                        variant="text"
                        size="small"
                        color="error"
                        v-if="hasPermission('vk_parser_tab_notifications_edit')"
                        @click="deleteNotification(idx)"
                        title="Удалить"
                      />
                    </VCardActions>
                  </VCard>
                </VCol>
              </VRow>

              <VDivider class="my-8" />
              
              <VAlert type="info" variant="tonal" density="compact">
                <div class="text-subtitle-2 mb-1">Доступные переменные для использования в шаблонах:</div>
                <VRow no-gutters>
                  <VCol cols="12" md="4" class="text-caption"><code>{order_number}</code> — Номер заказа</VCol>
                  <VCol cols="12" md="4" class="text-caption"><code>{total_sum}</code> — Сумма к оплате</VCol>
                  <VCol cols="12" md="4" class="text-caption"><code>{ready_time}</code> — Время ожидания</VCol>
                  <VCol cols="12" md="4" class="text-caption"><code>{address}</code> — Адрес доставки</VCol>
                  <VCol cols="12" md="4" class="text-caption"><code>{items}</code> — Состав заказа</VCol>
                  <VCol cols="12" md="4" class="text-caption"><code>{comment}</code> — Комментарий</VCol>
                  <VCol cols="12" md="4" class="text-caption"><code>{order_type}</code> — Тип заказа</VCol>
                </VRow>
              </VAlert>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>
    </VWindowItem>

    <VWindowItem :value="2">
      <VRow>
        <VCol cols="12">
          <VCard>
            <VCardTitle class="d-flex align-center">
              <VIcon icon="mdi-message-text-outline" class="me-2" color="primary" />
              История сообщений
              <VSpacer />
              <div class="d-flex gap-2 flex-wrap" style="max-width: 800px;">
                <VTextField
                  v-model="messageDate"
                  type="date"
                  label="Дата"
                  density="compact"
                  variant="outlined"
                  hide-details
                  style="width: 160px;"
                  @update:model-value="() => { messagePage = 1; loadMessages(); loadMessageStats(); }"
                />
                <VSelect
                  v-model="messageDirection"
                  :items="[
                    { title: 'Все', value: null },
                    { title: 'Входящие', value: 'inbound' },
                    { title: 'Исходящие', value: 'outbound' }
                  ]"
                  label="Направление"
                  density="compact"
                  variant="outlined"
                  hide-details
                  style="width: 150px;"
                  @update:model-value="() => { messagePage = 1; loadMessages(); }"
                />
                <VTextField
                  v-model="messageSearch"
                  prepend-inner-icon="mdi-magnify"
                  label="Поиск по тексту"
                  density="compact"
                  variant="outlined"
                  hide-details
                  @keyup.enter="() => { messagePage = 1; loadMessages(); }"
                />
                <VBtn
                  color="primary"
                  icon="mdi-refresh"
                  variant="text"
                  :loading="messagesLoading"
                  @click="() => { loadMessages(); loadMessageStats(); }"
                />
                <VBtn
                  color="error"
                  icon="mdi-delete-sweep-outline"
                  variant="text"
                  title="Очистить старые (>90 дней)"
                  :loading="cleaning"
                  v-if="hasPermission('vk_parser_tab_monitoring_edit')"
                  @click="cleanupMessages"
                />
              </div>
            </VCardTitle>

            <VCardText>
              <!-- Статистика сообщений -->
              <VRow class="mb-4">
                <VCol cols="12" md="4">
                  <VCard variant="tonal" color="info" density="compact">
                    <VCardText class="d-flex align-center justify-space-between py-2">
                      <div>
                        <div class="text-caption">Всего сообщений</div>
                        <div class="text-h6">{{ messageStats.total }}</div>
                      </div>
                      <VIcon icon="mdi-message-bulleted" size="32" opacity="0.3" />
                    </VCardText>
                  </VCard>
                </VCol>
                <VCol cols="12" md="4">
                  <VCard variant="tonal" color="success" density="compact">
                    <VCardText class="d-flex align-center justify-space-between py-2">
                      <div>
                        <div class="text-caption">Входящие (от пользователей)</div>
                        <div class="text-h6">{{ messageStats.inbound }}</div>
                      </div>
                      <VIcon icon="mdi-message-arrow-left" size="32" opacity="0.3" />
                    </VCardText>
                  </VCard>
                </VCol>
                <VCol cols="12" md="4">
                  <VCard variant="tonal" color="orange" density="compact">
                    <VCardText class="d-flex align-center justify-space-between py-2">
                      <div>
                        <div class="text-caption">Исходящие (от сообщества)</div>
                        <div class="text-h6">{{ messageStats.outbound }}</div>
                      </div>
                      <VIcon icon="mdi-message-arrow-right" size="32" opacity="0.3" />
                    </VCardText>
                  </VCard>
                </VCol>
              </VRow>

              <VDivider class="mb-4" />

              <!-- Таблица сообщений -->
              <div v-if="messagesLoading && messages.length === 0" class="text-center py-10">
                <VProgressCircular indeterminate color="primary" />
                <div class="mt-2">Загрузка сообщений...</div>
              </div>

              <template v-else>
                <VTable density="comfortable">
                  <thead>
                    <tr>
                      <th style="width: 200px;">Пользователь</th>
                      <th>Сообщение</th>
                      <th style="width: 100px;">Тип</th>
                      <th style="width: 180px;">Дата</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="msg in messages" :key="msg.id">
                      <td>
                        <div class="d-flex align-center py-2">
                          <VAvatar size="32" class="me-2" color="grey-lighten-3">
                            <VImg v-if="msg.user?.photo_50" :src="msg.user.photo_50" />
                            <VIcon v-else icon="mdi-account" />
                          </VAvatar>
                          <div class="text-truncate" style="max-width: 150px;">
                            <a :href="`https://vk.com/id${msg.peer_id}`" target="_blank" class="text-subtitle-2 text-decoration-none">
                              {{ msg.user?.first_name ? `${msg.user.first_name} ${msg.user.last_name}` : `ID ${msg.peer_id}` }}
                            </a>
                          </div>
                        </div>
                      </td>
                      <td>
                        <div class="py-2 text-body-2" style="white-space: pre-wrap; word-break: break-word;">
                          {{ msg.text }}
                          <div v-if="msg.payload" class="mt-1">
                            <VChip size="x-small" variant="tonal" color="grey">
                              Payload: {{ JSON.stringify(msg.payload) }}
                            </VChip>
                          </div>
                        </div>
                      </td>
                      <td>
                        <VChip
                          size="x-small"
                          :color="msg.direction === 'inbound' ? 'success' : 'orange'"
                          variant="tonal"
                        >
                          {{ msg.direction === 'inbound' ? 'Входящее' : 'Исходящее' }}
                        </VChip>
                      </td>
                      <td class="text-caption text-medium-emphasis">
                        {{ new Date(msg.created_at).toLocaleString() }}
                      </td>
                    </tr>
                    <tr v-if="messages.length === 0">
                      <td colspan="4" class="text-center py-10 text-medium-emphasis">
                        Сообщения не найдены
                      </td>
                    </tr>
                  </tbody>
                </VTable>

                <div class="d-flex justify-center mt-4" v-if="totalMessagePages > 1">
                  <VPagination
                    v-model="messagePage"
                    :length="totalMessagePages"
                    :total-visible="7"
                    @update:model-value="loadMessages"
                  />
                </div>
              </template>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>
    </VWindowItem>

    <VWindowItem :value="3">
      <VRow>
        <VCol cols="12">
          <VCard>
            <VCardTitle class="d-flex align-center flex-wrap gap-4">
              <VIcon icon="mdi-account-multiple-outline" class="me-2" color="primary" />
              Связанные аккаунты гостей (VK)
              <VSpacer />
              <div class="d-flex gap-2 flex-wrap" style="max-width: 600px;">
                <VSelect
                  v-model="linkedAccountsFilterStatus"
                  :items="[
                    { title: 'Все', value: 'all' },
                    { title: 'Активные', value: 'active' },
                    { title: 'Заблокированные', value: 'blocked' }
                  ]"
                  label="Фильтр"
                  density="compact"
                  variant="outlined"
                  hide-details
                  style="width: 170px;"
                  @update:model-value="() => { linkedAccountsPage = 1; loadLinkedAccounts(); }"
                />
                <VTextField
                  v-model="linkedAccountsSearch"
                  prepend-inner-icon="mdi-magnify"
                  label="Поиск по имени/телефону"
                  density="compact"
                  variant="outlined"
                  hide-details
                  @keyup.enter="() => { linkedAccountsPage = 1; loadLinkedAccounts(); }"
                />
                <VBtn
                  color="primary"
                  icon="mdi-refresh"
                  variant="text"
                  :loading="linkedAccountsLoading"
                  @click="loadLinkedAccounts"
                />
              </div>
            </VCardTitle>

            <VCardText>
              <div v-if="linkedAccountsLoading && linkedAccounts.length === 0" class="text-center py-10">
                <VProgressCircular indeterminate color="primary" />
                <div class="mt-2">Загрузка привязок...</div>
              </div>

              <template v-else>
                <VTable density="comfortable">
                  <thead>
                    <tr>
                      <th style="width: 250px;">Гость (VK)</th>
                      <th>Телефон</th>
                      <th>Дата привязки</th>
                      <th>Статус подписки</th>
                      <th>Уведомления</th>
                      <th>Рассылки</th>
                      <th style="width: 100px;">Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="acc in linkedAccounts" :key="acc.vk_id">
                      <td>
                        <div class="d-flex align-center py-2">
                          <VAvatar size="36" class="me-2" color="grey-lighten-3">
                            <VImg v-if="acc.photo_50" :src="acc.photo_50" />
                            <VIcon v-else icon="mdi-account" />
                          </VAvatar>
                          <div>
                            <a :href="`https://vk.com/id${acc.vk_id}`" target="_blank" class="text-subtitle-2 text-decoration-none d-flex align-center">
                              {{ acc.first_name }} {{ acc.last_name }}
                              <VIcon icon="mdi-open-in-new" size="x-small" class="ms-1" />
                            </a>
                            <div class="text-caption text-medium-emphasis">
                              ID: {{ acc.vk_id }} ({{ acc.screen_name || 'domain' }})
                            </div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <div>{{ acc.phone || '—' }}</div>
                        <div v-if="acc.customer" class="text-caption text-primary">
                          Профиль: {{ acc.customer.name }} {{ acc.customer.surname }}
                        </div>
                      </td>
                      <td class="text-caption text-medium-emphasis">
                        {{ acc.linked_at ? new Date(acc.linked_at).toLocaleString() : '—' }}
                      </td>
                      <td>
                        <VChip
                          size="x-small"
                          :color="acc.is_subscribed ? 'success' : 'error'"
                          variant="tonal"
                        >
                          {{ acc.is_subscribed ? 'Подписан' : 'Отписан' }}
                        </VChip>
                      </td>
                      <td>
                        <div class="d-flex align-center gap-2">
                          <VSwitch
                            :model-value="acc.notifications_enabled"
                            @update:model-value="toggleLinkedAccountFlag(acc, 'notifications_enabled')"
                            :disabled="!hasPermission('vk_parser_tab_accounts_edit')"
                            color="success"
                            density="compact"
                            hide-details
                          />
                          <span class="text-caption">{{ acc.notifications_enabled ? 'Разрешено' : 'Запрещено' }}</span>
                        </div>
                      </td>
                      <td>
                        <div class="d-flex align-center gap-2">
                          <VSwitch
                            :model-value="acc.is_blocked"
                            @update:model-value="toggleLinkedAccountFlag(acc, 'is_blocked')"
                            :disabled="!hasPermission('vk_parser_tab_accounts_edit')"
                            color="error"
                            density="compact"
                            hide-details
                          />
                          <span class="text-caption text-error" v-if="acc.is_blocked">Заблокирован</span>
                          <span class="text-caption" v-else>Активен</span>
                        </div>
                      </td>
                      <td>
                        <div class="d-flex gap-1">
                          <VBtn
                            icon="mdi-account-details"
                            variant="text"
                            size="small"
                            color="info"
                            title="Перейти к клиенту"
                            :to="acc.customer?.id ? `/clients?search=${encodeURIComponent(acc.phone)}` : null"
                            :disabled="!acc.customer?.id"
                          />
                          <VBtn
                            icon="mdi-delete-outline"
                            variant="text"
                            size="small"
                            color="error"
                            title="Удалить привязку"
                            v-if="hasPermission('vk_parser_tab_accounts_edit')"
                            @click="confirmUnlink(acc)"
                          />
                        </div>
                      </td>
                    </tr>
                    <tr v-if="linkedAccounts.length === 0">
                      <td colspan="7" class="text-center py-10 text-medium-emphasis">
                        Связанные аккаунты не найдены
                      </td>
                    </tr>
                  </tbody>
                </VTable>

                <div class="d-flex justify-center mt-4" v-if="totalLinkedAccountsPages > 1">
                  <VPagination
                    v-model="linkedAccountsPage"
                    :length="totalLinkedAccountsPages"
                    :total-visible="7"
                    @update:model-value="loadLinkedAccounts"
                  />
                </div>
              </template>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>
    </VWindowItem>
  </VWindow>

  <!-- Snackbar -->
  <VSnackbar
    v-model="snackbar"
    :color="snackbarColor"
    :timeout="3000"
    location="top"
  >
    {{ snackbarText }}
  </VSnackbar>

  <!-- Диалог подтверждения удаления -->
  <VDialog v-model="confirmUnlinkDialog" max-width="500">
    <VCard>
      <VCardTitle>Удаление привязки</VCardTitle>
      <VCardText>
        Вы уверены, что хотите удалить привязку VK профиля <strong>ID {{ userToUnlink?.vk_id }}</strong>?
        <br><br>
        Связь с карточкой клиента будет разорвана. Это действие не удалит историю сообщений.
      </VCardText>
      <VCardActions>
        <VSpacer />
        <VBtn variant="text" @click="confirmUnlinkDialog = false">Отмена</VBtn>
        <VBtn color="error" :loading="unlinking" @click="unlinkUser">Удалить</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- Диалог создания/редактирования уведомления -->
  <VDialog v-model="dialogOpen" max-width="600" persistent>
    <VCard>
      <VCardTitle class="d-flex align-center py-4 bg-primary text-white">
        <VIcon :icon="dialogMode === 'create' ? 'mdi-bell-plus-outline' : 'mdi-bell-ring-outline'" class="me-2" />
        <span>{{ dialogMode === 'create' ? 'Создать уведомление' : 'Редактировать уведомление' }}</span>
        <VSpacer />
        <VBtn icon="mdi-close" variant="text" color="white" @click="dialogOpen = false" />
      </VCardTitle>
      <VCardText class="pt-6">
        <VRow>
          <VCol cols="12" md="6">
            <VSelect
              v-model="formNotification.type"
              :items="[
                { title: 'Доставка', value: 'delivery' },
                { title: 'Самовывоз', value: 'pickup' }
              ]"
              label="Тип заказа"
              variant="outlined"
              :disabled="dialogMode === 'edit'"
              @update:model-value="onFormTypeChange"
            />
          </VCol>
          <VCol cols="12" md="6">
            <VSelect
              v-model="formNotification.status"
              :items="availableStatuses"
              item-title="title"
              item-value="value"
              label="Событие iiko"
              variant="outlined"
              :disabled="dialogMode === 'edit' || availableStatuses.length === 0"
              no-data-text="Все события уже настроены"
            />
          </VCol>
          <VCol cols="12">
            <VTextarea
              id="dialog-template-textarea"
              v-model="formNotification.template"
              label="Шаблон сообщения"
              rows="5"
              variant="outlined"
              placeholder="Введите текст уведомления..."
              hint="Используйте переменные ниже для динамической подстановки"
              persistent-hint
            />
          </VCol>
          <VCol cols="12">
            <div class="d-flex flex-wrap gap-1 mt-1">
              <span class="text-caption text-medium-emphasis me-2 align-self-center">Быстрая вставка:</span>
              <VChip
                v-for="variable in ['{order_number}', '{customer_name}', '{total_sum}', '{ready_time}', '{address}', '{items}', '{comment}']"
                :key="variable"
                size="x-small"
                variant="outlined"
                color="primary"
                class="cursor-pointer"
                @click="insertVariableToDialog(variable)"
              >
                {{ variable }}
              </VChip>
            </div>
          </VCol>
          <VCol cols="12" class="pt-0">
            <VSwitch
              v-model="formNotification.enabled"
              label="Активировать уведомление сразу"
              color="success"
              hide-details
            />
          </VCol>
        </VRow>
      </VCardText>
      <VCardActions class="pa-4 pt-0">
        <VSpacer />
        <VBtn variant="text" @click="dialogOpen = false">Отмена</VBtn>
        <VBtn 
          color="primary" 
          variant="elevated" 
          @click="saveNotificationForm"
          :disabled="availableStatuses.length === 0 && dialogMode === 'create'"
        >
          Сохранить
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>
