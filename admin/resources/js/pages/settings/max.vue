<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue"
import { getAuthHeaders } from "@/utils/auth"

// Стили вынесены в отдельный файл по регламенту проекта
import "@styles/settings-max.css"

const activeTab = ref("bots")
const loading = ref(false)
const saving = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

// Универсальный fetch с автоматической передачей JWT авторизации и X-Device-Id
const apiFetch = async (url, options = {}) => {
  const headers = {
    ...getAuthHeaders(),
    ...(options.headers || {})
  }
  const res = await fetch(url, {
    ...options,
    headers
  })
  if (res.status === 401) {
    showMessage("Сессия авторизации не активна. Обновите страницу или перезайдите в панель.", "error")
  }
  return res
}

// Настройки
const settings = ref({
  api_key: "",
  api_secret: "",
  base_url: "https://platform-api2.max.ru",
  sender_name: "FoodZuka",
  default_template: "",
  is_active: true,
  send_priority: "bot_first",
  auto_search_phone: true,
  bots: [],
  bridge_account: null
})

// Диалоги ботов
const botDialog = ref(false)
const webhookDialog = ref(false)
const commandsDialog = ref(false)
const verifyingBot = ref(false)

const editingBot = ref({
  id: null,
  bot_type: "MAX",
  bot_name: "",
  bot_token: "",
  bot_external_id: "",
  bot_username: "",
  bot_avatar: "",
  is_default_for_notifications: false,
  webhook_url: "",
  commands_json: "",
  welcome_message: "Здравствуйте! Я официальный бот для уведомлений о ваших заказах.",
  request_contact_on_start: true,
  is_active: true
})

const selectedBotForWebhook = ref(null)
const webhookUrlInput = ref("")
const selectedBotForCommands = ref(null)
const commandsList = ref([
  { name: "start", description: "Запустить бота" },
  { name: "status", description: "Статус текущего заказа" },
  { name: "bonuses", description: "Мой баланс бонусов" }
])

// Личный аккаунт (Web Instance Bridge / QR)
const bridgeAccount = ref(null)
const qrLoading = ref(false)
const qrSession = ref(null)
const qrTimer = ref(null)
const qrTimeLeft = ref(0)
const qrPollInterval = ref(null)

// Поиск клиентов по номеру телефона
const searchPhone = ref("79220079019")
const searchingPhone = ref(false)
const searchResult = ref(null)
const batchSearching = ref(false)
const batchResult = ref(null)

// Тестовая отправка сообщений
const testMsg = ref({
  recipient: "79220079019",
  text: "Привет! Это тестовое уведомление от сервиса доставки через мессенджер MAX.",
  format: "markdown",
  notify: true,
  channel: "bot",
  with_button: true
})
const sendingTest = ref(false)
const testResult = ref(null)

// Журналы
const logsSubTab = ref("messages")
const messageLogs = ref([])
const webhookEvents = ref([])
const loadingLogs = ref(false)
const selectedJsonPayload = ref(null)
const jsonDialog = ref(false)

// Загрузка настроек
const loadSettings = async () => {
  loading.value = true
  try {
    const res = await apiFetch("/api/v1/max/settings")
    if (res.ok) {
      const data = await res.json()
      settings.value = {
        ...settings.value,
        ...data,
        bots: Array.isArray(data.bots) ? data.bots : [],
        base_url: data.base_url || "https://platform-api2.max.ru"
      }
      bridgeAccount.value = data.bridge_account || null
    }
  } catch (e) {
    showMessage("Ошибка загрузки настроек MAX", "error")
  } finally {
    loading.value = false
  }
}

// Сохранение общих настроек
const saveSettings = async () => {
  saving.value = true
  try {
    const res = await apiFetch("/api/v1/max/settings", {
      method: "POST",
      body: JSON.stringify(settings.value)
    })
    if (res.ok) {
      showMessage("Настройки MAX успешно сохранены")
      await loadSettings()
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка сохранения", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети при сохранении", "error")
  } finally {
    saving.value = false
  }
}

// Управление ботами
const openBotDialog = (bot = null) => {
  if (bot) {
    editingBot.value = { ...bot }
  } else {
    editingBot.value = {
      id: null,
      bot_type: "MAX",
      bot_name: "",
      bot_token: "",
      bot_external_id: "",
      bot_username: "",
      bot_avatar: "",
      is_default_for_notifications: (settings.value.bots || []).length === 0,
      webhook_url: "",
      commands_json: JSON.stringify(commandsList.value),
      welcome_message: "Здравствуйте! Я официальный бот для уведомлений о ваших заказах.",
      request_contact_on_start: true,
      is_active: true
    }
  }
  botDialog.value = true
}

const verifyTokenInDialog = async () => {
  if (!editingBot.value.bot_token) {
    showMessage("Введите токен бота", "warning")
    return
  }
  verifyingBot.value = true
  try {
    const res = await apiFetch("/api/v1/max/bots/verify-token", {
      method: "POST",
      body: JSON.stringify({ token: editingBot.value.bot_token.trim() })
    })
    const data = await res.json()
    if (res.ok && data.valid) {
      editingBot.value.bot_external_id = String(data.bot_id || "")
      editingBot.value.bot_name = data.bot_name || editingBot.value.bot_name || "Бот MAX"
      editingBot.value.bot_username = data.bot_username || ""
      editingBot.value.bot_avatar = data.bot_avatar || ""
      showMessage(`Бот подтвержден: ${editingBot.value.bot_name} (@${editingBot.value.bot_username})`)
    } else {
      showMessage(data.error || "Токен не распознан сервером MAX", "error")
    }
  } catch (e) {
    showMessage("Ошибка проверки токена бота", "error")
  } finally {
    verifyingBot.value = false
  }
}

const saveBot = async () => {
  if (!editingBot.value.bot_token) {
    showMessage("Укажите токен бота", "warning")
    return
  }
  if (!editingBot.value.bot_name) {
    editingBot.value.bot_name = "Бот MAX"
  }

  const method = editingBot.value.id ? "PUT" : "POST"
  const url = editingBot.value.id 
    ? `/api/v1/max/bots/${editingBot.value.id}` 
    : "/api/v1/max/bots"
  
  try {
    const res = await apiFetch(url, {
      method,
      body: JSON.stringify(editingBot.value)
    })
    if (res.ok) {
      showMessage(editingBot.value.id ? "Параметры бота обновлены" : "Бот успешно добавлен")
      botDialog.value = false
      await loadSettings()
    } else {
      const data = await res.json()
      showMessage(data.detail || "Ошибка сохранения бота", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  }
}

const verifyBotConnection = async (bot) => {
  try {
    const res = await apiFetch(`/api/v1/max/bots/${bot.id}/verify`, { method: "POST" })
    const data = await res.json()
    if (data.status === "success") {
      showMessage(data.message)
      await loadSettings()
    } else {
      showMessage(data.message, "error")
    }
  } catch (e) {
    showMessage("Ошибка проверки бота", "error")
  }
}

const openWebhookDialog = (bot) => {
  selectedBotForWebhook.value = bot
  webhookUrlInput.value = bot.webhook_url || `https://vezuroll.ru/api/v1/max/webhook/${bot.id}`
  webhookDialog.value = true
}

const setBotWebhook = async () => {
  if (!selectedBotForWebhook.value) return
  try {
    const res = await apiFetch(`/api/v1/max/bots/${selectedBotForWebhook.value.id}/webhook/set`, {
      method: "POST",
      body: JSON.stringify({ webhook_url: webhookUrlInput.value })
    })
    if (res.ok) {
      showMessage("Webhook успешно зарегистрирован в MAX")
      webhookDialog.value = false
      await loadSettings()
    } else {
      const data = await res.json()
      showMessage(data.detail || "Ошибка установки вебхука", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  }
}

const deleteBotWebhook = async () => {
  if (!selectedBotForWebhook.value) return
  try {
    const res = await apiFetch(`/api/v1/max/bots/${selectedBotForWebhook.value.id}/webhook/delete`, {
      method: "POST"
    })
    if (res.ok) {
      showMessage("Webhook успешно удален из MAX")
      webhookDialog.value = false
      await loadSettings()
    } else {
      showMessage("Ошибка удаления вебхука", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  }
}

const openCommandsDialog = (bot) => {
  selectedBotForCommands.value = bot
  if (bot.commands_json) {
    try {
      commandsList.value = JSON.parse(bot.commands_json)
    } catch (e) {
      commandsList.value = [{ name: "start", description: "Запустить бота" }]
    }
  } else {
    commandsList.value = [
      { name: "start", description: "Запустить бота" },
      { name: "status", description: "Статус текущего заказа" }
    ]
  }
  commandsDialog.value = true
}

const addCommandRow = () => {
  commandsList.value.push({ name: "", description: "" })
}

const removeCommandRow = (index) => {
  commandsList.value.splice(index, 1)
}

const saveBotCommands = async () => {
  if (!selectedBotForCommands.value) return
  const validCommands = commandsList.value.filter(c => c.name && c.description)
  try {
    const res = await apiFetch(`/api/v1/max/bots/${selectedBotForCommands.value.id}/commands`, {
      method: "POST",
      body: JSON.stringify({ commands: validCommands })
    })
    if (res.ok) {
      showMessage("Команды бота успешно сохранены в MAX")
      commandsDialog.value = false
      await loadSettings()
    } else {
      const data = await res.json()
      showMessage(data.detail || "Ошибка сохранения команд", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  }
}

const deleteBot = async (botId) => {
  if (!confirm("Вы уверены, что хотите удалить этого бота из системы?")) return
  try {
    const res = await apiFetch(`/api/v1/max/bots/${botId}`, { method: "DELETE" })
    if (res.ok) {
      showMessage("Бот удален")
      await loadSettings()
    } else {
      showMessage("Ошибка удаления бота", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  }
}

// Web Instance Bridge (QR авторизация)
const startQrSession = async () => {
  qrLoading.value = true
  stopQrPolling()
  try {
    const res = await apiFetch("/api/v1/max/bridge/qr/init", { method: "POST" })
    if (res.ok) {
      const data = await res.json()
      qrSession.value = data
      qrTimeLeft.value = data.expires_in || 90

      // Запуск таймера
      qrTimer.value = setInterval(() => {
        if (qrTimeLeft.value > 0) {
          qrTimeLeft.value--
        } else {
          stopQrPolling()
        }
      }, 1000)

      // Запуск опроса статуса каждые 2 секунды
      qrPollInterval.value = setInterval(async () => {
        try {
          const statusRes = await apiFetch(`/api/v1/max/bridge/qr/status/${data.session_id}`)
          if (statusRes.ok) {
            const statusData = await statusRes.json()
            if (statusData.status === "active") {
              stopQrPolling()
              showMessage(`Личный аккаунт успешно подключен: ${statusData.user_name || statusData.phone}`)
              await loadSettings()
            } else if (statusData.status === "expired") {
              stopQrPolling()
              showMessage("Время действия QR-кода истекло", "warning")
            }
          }
        } catch (err) {
          // Игнорируем кратковременные сетевые сбои опроса
        }
      }, 2000)
    } else {
      const err = await res.json()
      showMessage(err.detail || "Не удалось сгенерировать QR-код", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети при запросе QR", "error")
  } finally {
    qrLoading.value = false
  }
}

const stopQrPolling = () => {
  if (qrTimer.value) {
    clearInterval(qrTimer.value)
    qrTimer.value = null
  }
  if (qrPollInterval.value) {
    clearInterval(qrPollInterval.value)
    qrPollInterval.value = null
  }
  qrSession.value = null
}

const disconnectBridge = async () => {
  if (!confirm("Отключить личный аккаунт MAX? Отправка от его имени будет прекращена.")) return
  try {
    const res = await apiFetch("/api/v1/max/bridge/disconnect", { method: "POST" })
    if (res.ok) {
      showMessage("Аккаунт MAX отключен")
      bridgeAccount.value = null
      await loadSettings()
    } else {
      showMessage("Ошибка отключения аккаунта", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  }
}

// Поиск клиентов по номеру телефона
const doSearchPhone = async () => {
  if (!searchPhone.value) {
    showMessage("Введите номер телефона", "warning")
    return
  }
  searchingPhone.value = true
  searchResult.value = null
  try {
    const res = await apiFetch("/api/v1/max/search-phone", {
      method: "POST",
      body: JSON.stringify({ phone: searchPhone.value, link_to_customer: true })
    })
    const data = await res.json()
    searchResult.value = data
    if (data.found) {
      showMessage(`Пользователь найден: ${data.name || data.user_id}`)
    } else {
      showMessage(data.error || "Пользователь не найден в MAX", "warning")
    }
  } catch (e) {
    showMessage("Ошибка поиска по номеру", "error")
  } finally {
    searchingPhone.value = false
  }
}

const runBatchSearch = async () => {
  batchSearching.value = true
  batchResult.value = null
  try {
    const res = await apiFetch("/api/v1/max/batch-search-phones", {
      method: "POST",
      body: JSON.stringify({ limit: 30 })
    })
    const data = await res.json()
    batchResult.value = data
    if (data.error) {
      showMessage(data.error, "error")
    } else {
      showMessage(`Синхронизация завершена: проверено ${data.total}, привязано ${data.found_count} MAX ID`)
    }
  } catch (e) {
    showMessage("Ошибка пакетного поиска", "error")
  } finally {
    batchSearching.value = false
  }
}

// Тестовая отправка
const sendTestMessage = async () => {
  if (!testMsg.value.recipient || !testMsg.value.text) {
    showMessage("Укажите получателя и текст сообщения", "warning")
    return
  }
  sendingTest.value = true
  testResult.value = null
  try {
    const payload = {
      recipient: testMsg.value.recipient,
      text: testMsg.value.text,
      format: testMsg.value.format,
      notify: testMsg.value.notify,
      channel: testMsg.value.channel,
      buttons: testMsg.value.with_button ? [
        [{ type: "link", text: "🌐 Перейти на сайт VezuRoll", url: "https://vezuroll.ru" }]
      ] : null
    }

    const res = await apiFetch("/api/v1/max/send-message", {
      method: "POST",
      body: JSON.stringify(payload)
    })
    const data = await res.json()
    if (res.ok && data.status === "success") {
      testResult.value = data.data
      showMessage("Сообщение успешно отправлено в MAX!")
      if (activeTab.value === "logs") {
        await loadLogs()
      }
    } else {
      showMessage(data.detail || "Не удалось доставить сообщение", "error")
      testResult.value = { success: false, error: data.detail }
    }
  } catch (e) {
    showMessage("Ошибка сети при отправке", "error")
  } finally {
    sendingTest.value = false
  }
}

// Журналы сообщений и вебхуков
const loadLogs = async () => {
  loadingLogs.value = true
  try {
    const [msgRes, wbRes] = await Promise.all([
      apiFetch("/api/v1/max/logs?limit=50"),
      apiFetch("/api/v1/max/webhook/events?limit=50")
    ])
    if (msgRes.ok) {
      const msgData = await msgRes.json()
      messageLogs.value = msgData.items || []
    }
    if (wbRes.ok) {
      const wbData = await wbRes.json()
      webhookEvents.value = wbData.items || []
    }
  } catch (e) {
    showMessage("Ошибка загрузки журналов", "error")
  } finally {
    loadingLogs.value = false
  }
}

const openJsonModal = (jsonStr) => {
  try {
    selectedJsonPayload.value = JSON.stringify(JSON.parse(jsonStr), null, 2)
  } catch (e) {
    selectedJsonPayload.value = jsonStr
  }
  jsonDialog.value = true
}

const formatDate = (isoStr) => {
  if (!isoStr) return "-"
  const d = new Date(isoStr)
  return d.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  })
}

onMounted(async () => {
  await loadSettings()
  await loadLogs()
})

onUnmounted(() => {
  stopQrPolling()
})
</script>

<template>
  <div class="max-integration-wrapper">
    <!-- Шапка страницы -->
    <VCard class="max-header-card mb-6">
      <VCardText class="d-flex flex-wrap align-center justify-space-between gap-4">
        <div>
          <div class="d-flex align-center gap-3 mb-1">
            <h2 class="text-h5 font-weight-bold">
              Интеграция с мессенджером MAX
            </h2>
            <span class="max-brand-badge">
              <VIcon icon="bx-paper-plane" size="18" />
              MAX Official
            </span>
          </div>
          <p class="text-body-2 text-medium-emphasis mb-0">
            Мультиботность (Bot API), подключение личного аккаунта через QR-мост, поиск клиентов по номеру телефона и рассылки
          </p>
        </div>

        <div class="d-flex align-center gap-3">
          <VChip
            :color="settings.is_active ? 'success' : 'secondary'"
            variant="tonal"
            size="small"
            class="font-weight-medium"
          >
            <VIcon
              start
              :icon="settings.is_active ? 'bx-check-circle' : 'bx-power-off'"
              size="16"
            />
            {{ settings.is_active ? 'Интеграция активна' : 'Отключена' }}
          </VChip>

          <VBtn
            color="primary"
            prepend-icon="bx-save"
            :loading="saving"
            @click="saveSettings"
          >
            Сохранить настройки
          </VBtn>
        </div>
      </VCardText>
    </VCard>

    <!-- Основные вкладки -->
    <VCard>
      <VTabs
        v-model="activeTab"
        class="max-nav-tabs border-b"
        color="primary"
      >
        <VTab value="bots">
          <VIcon start icon="bx-bot" size="18" />
          Боты MAX (Bot API)
          <VChip size="x-small" color="primary" class="ms-2">
            {{ settings.bots.length }}
          </VChip>
        </VTab>

        <VTab value="bridge">
          <VIcon start icon="bx-qr-scan" size="18" />
          Личный аккаунт (QR)
          <span
            v-if="bridgeAccount"
            class="max-pulse-dot ms-2"
            title="Аккаунт в сети"
          />
        </VTab>

        <VTab value="search">
          <VIcon start icon="bx-search-alt" size="18" />
          Поиск клиентов
        </VTab>

        <VTab value="notifications">
          <VIcon start icon="bx-send" size="18" />
          Уведомления и рассылки
        </VTab>

        <VTab value="logs" @click="loadLogs">
          <VIcon start icon="bx-history" size="18" />
          Журнал и Webhook
        </VTab>
      </VTabs>

      <VCardText class="pa-6">
        <VWindow v-model="activeTab">
          <!-- ========================================== -->
          <!-- 1. ВКЛАДКА: БОТЫ MAX (BOT API) -->
          <!-- ========================================== -->
          <VWindowItem value="bots">
            <div class="d-flex align-center justify-space-between mb-4">
              <div>
                <h3 class="text-h6 font-weight-bold">
                  Подключенные боты MAX
                </h3>
                <p class="text-caption text-medium-emphasis mb-0">
                  Официальные боты платформы platform-api2.max.ru для отправки кнопочных меню и рассылок
                </p>
              </div>
              <VBtn
                color="primary"
                prepend-icon="bx-plus"
                @click="openBotDialog()"
              >
                Добавить бота MAX
              </VBtn>
            </div>

            <!-- Список ботов -->
            <VRow v-if="settings.bots && settings.bots.length > 0">
              <VCol
                v-for="bot in settings.bots"
                :key="bot.id"
                cols="12"
                md="6"
              >
                <VCard
                  class="max-bot-card pa-4"
                  :class="{ 'is-default': bot.is_default_for_notifications }"
                >
                  <div class="d-flex align-start justify-space-between mb-3">
                    <div class="d-flex align-center gap-3">
                      <img
                        v-if="bot.bot_avatar"
                        :src="bot.bot_avatar"
                        class="max-bot-avatar"
                        alt="Avatar"
                      />
                      <div v-else class="max-bot-avatar-placeholder">
                        <VIcon icon="bx-bot" />
                      </div>

                      <div>
                        <div class="d-flex align-center gap-2">
                          <span class="font-weight-bold text-subtitle-1">
                            {{ bot.bot_name }}
                          </span>
                          <VChip
                            v-if="bot.is_default_for_notifications"
                            size="x-small"
                            color="primary"
                            variant="tonal"
                          >
                            По умолчанию
                          </VChip>
                        </div>
                        <div class="text-caption text-medium-emphasis">
                          {{ bot.bot_username ? `@${bot.bot_username}` : 'Юзернейм не задан' }}
                          <span v-if="bot.bot_external_id"> • ID: {{ bot.bot_external_id }}</span>
                        </div>
                      </div>
                    </div>

                    <div class="d-flex align-center gap-1">
                      <VChip
                        size="x-small"
                        :color="bot.is_active ? 'success' : 'error'"
                        variant="tonal"
                      >
                        {{ bot.is_active ? 'Активен' : 'Отключен' }}
                      </VChip>
                    </div>
                  </div>

                  <!-- Статусы Webhook и контакта -->
                  <div class="d-flex flex-wrap gap-2 mb-4">
                    <VChip
                      size="x-small"
                      :color="bot.webhook_set ? 'info' : 'secondary'"
                      variant="tonal"
                    >
                      <VIcon
                        start
                        :icon="bot.webhook_set ? 'bx-broadcast' : 'bx-globe'"
                        size="14"
                      />
                      Webhook: {{ bot.webhook_set ? 'Активен' : 'Не установлен' }}
                    </VChip>

                    <VChip
                      size="x-small"
                      :color="bot.request_contact_on_start ? 'warning' : 'secondary'"
                      variant="tonal"
                    >
                      <VIcon start icon="bx-phone-call" size="14" />
                      {{ bot.request_contact_on_start ? 'Запрос контакта: ВКЛ' : 'Без запроса контакта' }}
                    </VChip>
                  </div>

                  <VDivider class="mb-3" />

                  <!-- Кнопки управления ботом -->
                  <div class="d-flex flex-wrap align-center justify-space-between gap-2">
                    <div class="d-flex gap-2">
                      <VBtn
                        size="small"
                        variant="tonal"
                        color="info"
                        prepend-icon="bx-refresh"
                        @click="verifyBotConnection(bot)"
                      >
                        Проверить связь
                      </VBtn>

                      <VBtn
                        size="small"
                        variant="tonal"
                        color="secondary"
                        prepend-icon="bx-broadcast"
                        @click="openWebhookDialog(bot)"
                      >
                        Webhook
                      </VBtn>

                      <VBtn
                        size="small"
                        variant="tonal"
                        color="secondary"
                        prepend-icon="bx-list-ul"
                        @click="openCommandsDialog(bot)"
                      >
                        Команды
                      </VBtn>
                    </div>

                    <div class="d-flex gap-1">
                      <VBtn
                        icon="bx-edit"
                        variant="text"
                        size="small"
                        color="primary"
                        @click="openBotDialog(bot)"
                      />
                      <VBtn
                        icon="bx-trash"
                        variant="text"
                        size="small"
                        color="error"
                        @click="deleteBot(bot.id)"
                      />
                    </div>
                  </div>
                </VCard>
              </VCol>
            </VRow>

            <VAlert
              v-else
              type="info"
              variant="tonal"
              class="mt-4"
            >
              В системе пока нет зарегистрированных ботов MAX. Нажмите <strong>«Добавить бота MAX»</strong> и введите токен официального бота.
            </VAlert>
          </VWindowItem>

          <!-- ========================================== -->
          <!-- 2. ВКЛАДКА: ЛИЧНЫЙ АККАУНТ (QR) -->
          <!-- ========================================== -->
          <VWindowItem value="bridge">
            <VRow>
              <VCol cols="12" md="7">
                <div class="max-bridge-box">
                  <h3 class="text-h6 font-weight-bold mb-2">
                    Подключение личного аккаунта MAX (Web Bridge)
                  </h3>
                  <p class="text-body-2 text-medium-emphasis mb-6">
                    Позволяет отправлять сервисные уведомления клиентам по номеру телефона напрямую от лица вашего личного аккаунта или аккаунта компании, а также искать профили пользователей в реальном времени.
                  </p>

                  <!-- Состояние: Аккаунт уже подключен -->
                  <div v-if="bridgeAccount" class="mb-4">
                    <VAlert
                      type="success"
                      variant="tonal"
                      prominent
                      class="mb-4"
                    >
                      <template #title>
                        <span class="font-weight-bold">
                          Аккаунт успешно подключен и активен!
                        </span>
                      </template>
                      <div class="mt-2 text-body-2">
                        <div><strong>Имя аккаунта:</strong> {{ bridgeAccount.name }}</div>
                        <div v-if="bridgeAccount.phone"><strong>Телефон:</strong> {{ bridgeAccount.phone }}</div>
                        <div><strong>Статус:</strong> Подключен к серверам MAX WebSocket</div>
                      </div>
                    </VAlert>

                    <div class="d-flex gap-3">
                      <VBtn
                        color="error"
                        variant="outlined"
                        prepend-icon="bx-log-out"
                        @click="disconnectBridge"
                      >
                        Отключить аккаунт
                      </VBtn>

                      <VBtn
                        color="primary"
                        variant="tonal"
                        prepend-icon="bx-send"
                        @click="activeTab = 'notifications'"
                      >
                        Тестовая отправка
                      </VBtn>
                    </div>
                  </div>

                  <!-- Состояние: Аккаунт не подключен -->
                  <div v-else>
                    <div v-if="!qrSession" class="text-center py-6">
                      <VIcon
                        icon="bx-qr-scan"
                        size="64"
                        color="primary"
                        class="mb-3"
                      />
                      <h4 class="text-subtitle-1 font-weight-bold mb-2">
                        Свяжите ваш аккаунт MAX с панелью
                      </h4>
                      <p class="text-caption text-medium-emphasis mb-4">
                        Для генерации индивидуального QR-кода нажмите кнопку ниже
                      </p>
                      <VBtn
                        color="primary"
                        size="large"
                        prepend-icon="bx-qr"
                        :loading="qrLoading"
                        @click="startQrSession"
                      >
                        Получить QR-код для входа
                      </VBtn>
                    </div>

                    <!-- Активный QR-код с таймером -->
                    <div v-else class="text-center py-4">
                      <div class="max-qr-wrapper mb-3">
                        <img
                          :src="qrSession.qr_base64"
                          class="max-qr-image"
                          alt="QR-код MAX"
                        />
                      </div>

                      <div class="d-flex align-center justify-center gap-2 mb-2">
                        <span class="max-pulse-dot" />
                        <span class="text-caption font-weight-medium">
                          Ожидание сканирования через приложение MAX...
                        </span>
                      </div>

                      <div class="mb-4">
                        <span class="text-caption text-medium-emphasis">Действителен еще: </span>
                        <span class="max-timer-countdown">{{ qrTimeLeft }} сек.</span>
                      </div>

                      <div class="d-flex justify-center gap-2">
                        <VBtn
                          size="small"
                          variant="tonal"
                          prepend-icon="bx-refresh"
                          :loading="qrLoading"
                          @click="startQrSession"
                        >
                          Обновить QR-код
                        </VBtn>
                        <VBtn
                          size="small"
                          variant="text"
                          color="secondary"
                          @click="stopQrPolling"
                        >
                          Отмена
                        </VBtn>
                      </div>
                    </div>
                  </div>
                </div>
              </VCol>

              <VCol cols="12" md="5">
                <VCard variant="tonal" color="primary" class="h-100">
                  <VCardText>
                    <h4 class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center gap-2">
                      <VIcon icon="bx-help-circle" />
                      Инструкция по подключению
                    </h4>
                    <ol class="text-body-2 text-medium-emphasis ps-4 mb-4">
                      <li class="mb-2">Откройте приложение <strong>MAX</strong> на смартфоне.</li>
                      <li class="mb-2">Перейдите в <strong>Настройки ➔ Связанные устройства</strong>.</li>
                      <li class="mb-2">Нажмите <strong>«Подключить устройство»</strong> и наведите камеру на QR-код.</li>
                      <li class="mb-2">После подтверждения система автоматически сохранит защищенную сессию в FoodZuka.</li>
                    </ol>
                    <VAlert type="info" variant="text" density="compact" class="px-0">
                      Сессия сохраняется на сервере и автоматически поддерживает соединение Keep-Alive.
                    </VAlert>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>
          </VWindowItem>

          <!-- ========================================== -->
          <!-- 3. ВКЛАДКА: ПОИСК КЛИЕНТОВ ПО ТЕЛЕФОНУ -->
          <!-- ========================================== -->
          <VWindowItem value="search">
            <VRow>
              <VCol cols="12" md="7">
                <VCard title="Поиск пользователя в MAX по номеру телефона" class="mb-6">
                  <VCardText>
                    <p class="text-body-2 text-medium-emphasis mb-4">
                      Введите номер телефона клиента для мгновенной проверки его регистрации в мессенджере MAX и связки с CRM-профилем.
                    </p>

                    <div class="d-flex gap-3 mb-4">
                      <VTextField
                        v-model="searchPhone"
                        label="Номер телефона"
                        placeholder="79220079019"
                        prepend-inner-icon="bx-phone"
                        hint="Тестовый номер: 79220079019"
                        persistent-hint
                        @keyup.enter="doSearchPhone"
                      />
                      <VBtn
                        color="primary"
                        size="large"
                        prepend-icon="bx-search"
                        :loading="searchingPhone"
                        @click="doSearchPhone"
                      >
                        Найти в MAX
                      </VBtn>
                    </div>

                    <!-- Карточка найденного пользователя -->
                    <div v-if="searchResult && searchResult.found" class="max-client-card mt-4">
                      <div class="d-flex align-center gap-4 mb-3">
                        <img
                          v-if="searchResult.avatar_url"
                          :src="searchResult.avatar_url"
                          class="max-client-avatar"
                          alt="Avatar"
                        />
                        <div v-else class="max-client-avatar-placeholder">
                          <VIcon icon="bx-user" />
                        </div>

                        <div>
                          <div class="text-h6 font-weight-bold">
                            {{ searchResult.name }}
                          </div>
                          <div class="text-body-2 text-medium-emphasis">
                            {{ searchResult.phone }} • ID MAX: <strong>{{ searchResult.user_id }}</strong>
                          </div>
                          <VChip
                            size="x-small"
                            color="success"
                            variant="tonal"
                            class="mt-1"
                          >
                            Зарегистрирован в MAX
                          </VChip>
                        </div>
                      </div>

                      <VDivider class="my-3" />

                      <!-- Данные из CRM -->
                      <div v-if="searchResult.customer" class="mb-3">
                        <div class="text-subtitle-2 font-weight-bold mb-1">
                          Привязанный клиент в CRM:
                        </div>
                        <div class="text-body-2">
                          Имя в CRM: <strong>{{ searchResult.customer.name }}</strong> |
                          Заказов: <strong>{{ searchResult.customer.total_orders_count }}</strong> |
                          Бонусы: <strong>{{ searchResult.customer.bonus_points }} ₽</strong>
                        </div>
                      </div>
                      <div v-else class="text-caption text-medium-emphasis mb-3">
                        Клиент с таким номером еще не делал заказов в CRM, но профиль в MAX успешно найден.
                      </div>

                      <div class="d-flex gap-2">
                        <VBtn
                          size="small"
                          color="primary"
                          prepend-icon="bx-send"
                          @click="testMsg.recipient = searchResult.user_id; activeTab = 'notifications'"
                        >
                          Написать сообщение
                        </VBtn>
                      </div>
                    </div>

                    <VAlert
                      v-else-if="searchResult && !searchResult.found"
                      type="warning"
                      variant="tonal"
                      class="mt-4"
                    >
                      {{ searchResult.error || 'Пользователь с таким номером телефона не зарегистрирован в MAX' }}
                    </VAlert>
                  </VCardText>
                </VCard>
              </VCol>

              <!-- Пакетный поиск -->
              <VCol cols="12" md="5">
                <VCard title="Синхронизация базы CRM с MAX">
                  <VCardText>
                    <p class="text-body-2 text-medium-emphasis mb-4">
                      Автоматический обход клиентов из базы данных (без привязанного MAX ID) и связывание профилей.
                    </p>

                    <VBtn
                      block
                      color="secondary"
                      variant="tonal"
                      prepend-icon="bx-sync"
                      :loading="batchSearching"
                      class="mb-4"
                      @click="runBatchSearch"
                    >
                      Синхронизировать пакет клиентов (30)
                    </VBtn>

                    <div v-if="batchResult" class="text-caption">
                      <VAlert
                        :type="batchResult.error ? 'error' : 'success'"
                        variant="tonal"
                        density="compact"
                      >
                        <div v-if="batchResult.error">{{ batchResult.error }}</div>
                        <div v-else>
                          Проверено клиентов: <strong>{{ batchResult.total }}</strong><br>
                          Успешно привязано MAX ID: <strong>{{ batchResult.found_count }}</strong>
                        </div>
                      </VAlert>
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>
          </VWindowItem>

          <!-- ========================================== -->
          <!-- 4. ВКЛАДКА: УВЕДОМЛЕНИЯ И РАССЫЛКИ -->
          <!-- ========================================== -->
          <VWindowItem value="notifications">
            <VRow>
              <!-- Настройки маршрутизации -->
              <VCol cols="12" md="6">
                <VCard title="Маршрутизация и параметры рассылок" class="mb-6">
                  <VCardText>
                    <VForm @submit.prevent="saveSettings">
                      <VSwitch
                        v-model="settings.is_active"
                        label="Глобальная активация канала MAX"
                        color="success"
                        class="mb-4"
                      />

                      <VSelect
                        v-model="settings.send_priority"
                        label="Приоритет канала доставки"
                        :items="[
                          { title: 'Сначала официальный бот (Bot API ➔ Fallback на личный аккаунт)', value: 'bot_first' },
                          { title: 'Сначала личный аккаунт (Web Bridge ➔ Fallback на бота)', value: 'bridge_first' },
                          { title: 'Только через бота', value: 'bot_only' }
                        ]"
                        class="mb-4"
                      />

                      <VSwitch
                        v-model="settings.auto_search_phone"
                        label="Автоматически искать MAX ID по телефону при отправке"
                        color="primary"
                        class="mb-4"
                      />

                      <VTextField
                        v-model="settings.sender_name"
                        label="Имя отправителя"
                        placeholder="FoodZuka"
                        class="mb-4"
                      />

                      <VTextField
                        v-model="settings.base_url"
                        label="Базовый URL Bot API"
                        placeholder="https://platform-api2.max.ru"
                        class="mb-4"
                      />

                      <VBtn
                        type="submit"
                        color="primary"
                        :loading="saving"
                      >
                        Сохранить параметры
                      </VBtn>
                    </VForm>
                  </VCardText>
                </VCard>
              </VCol>

              <!-- Тестовая отправка -->
              <VCol cols="12" md="6">
                <VCard title="Тестовая отправка сообщения">
                  <VCardText>
                    <VTextField
                      v-model="testMsg.recipient"
                      label="Получатель (Телефон / User ID / Chat ID)"
                      placeholder="79220079019"
                      class="mb-4"
                    />

                    <VSelect
                      v-model="testMsg.channel"
                      label="Канал отправки"
                      :items="[
                        { title: 'Автоматически (согласно приоритету)', value: 'auto' },
                        { title: 'Официальный бот (Bot API)', value: 'bot' },
                        { title: 'Личный аккаунт (Web Bridge)', value: 'bridge' }
                      ]"
                      class="mb-4"
                    />

                    <VTextarea
                      v-model="testMsg.text"
                      label="Текст сообщения (Markdown поддерживается)"
                      rows="4"
                      class="mb-4"
                    />

                    <div class="d-flex flex-wrap gap-4 mb-4">
                      <VCheckbox
                        v-model="testMsg.notify"
                        label="Звуковое push-уведомление"
                      />
                      <VCheckbox
                        v-model="testMsg.with_button"
                        label="Прикрепить инлайн-кнопку сайта"
                      />
                    </div>

                    <VBtn
                      color="primary"
                      prepend-icon="bx-send"
                      :loading="sendingTest"
                      @click="sendTestMessage"
                    >
                      Отправить в MAX
                    </VBtn>

                    <div v-if="testResult" class="mt-4">
                      <VAlert
                        :type="testResult.success ? 'success' : 'error'"
                        variant="tonal"
                      >
                        <div v-if="testResult.success">
                          Сообщение доставлено! ID сообщения: <strong>{{ testResult.msg_id || 'OK' }}</strong>
                        </div>
                        <div v-else>
                          Ошибка доставки: {{ testResult.error }}
                        </div>
                      </VAlert>
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>
          </VWindowItem>

          <!-- ========================================== -->
          <!-- 5. ВКЛАДКА: ЖУРНАЛ И WEBHOOK -->
          <!-- ========================================== -->
          <VWindowItem value="logs">
            <div class="d-flex align-center justify-space-between mb-4">
              <VTabs v-model="logsSubTab" density="compact">
                <VTab value="messages">Исходящие сообщения ({{ messageLogs.length }})</VTab>
                <VTab value="webhooks">События Webhook ({{ webhookEvents.length }})</VTab>
              </VTabs>

              <VBtn
                size="small"
                variant="tonal"
                prepend-icon="bx-refresh"
                :loading="loadingLogs"
                @click="loadLogs"
              >
                Обновить журнал
              </VBtn>
            </div>

            <VWindow v-model="logsSubTab">
              <!-- Исходящие сообщения -->
              <VWindowItem value="messages">
                <VTable v-if="messageLogs.length > 0" density="compact">
                  <thead>
                    <tr>
                      <th>Дата / Время</th>
                      <th>Получатель</th>
                      <th>Канал</th>
                      <th>Статус</th>
                      <th>Текст</th>
                      <th>ID в MAX</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="log in messageLogs" :key="log.id">
                      <td class="text-caption">{{ formatDate(log.created_at) }}</td>
                      <td class="font-weight-medium">{{ log.recipient }}</td>
                      <td>
                        <span :class="log.channel_type === 'bot' ? 'channel-pill-bot' : 'channel-pill-bridge'">
                          {{ log.channel_type === 'bot' ? 'Бот' : 'Bridge' }}
                        </span>
                      </td>
                      <td>
                        <VChip
                          size="x-small"
                          :color="log.status === 'sent' ? 'success' : 'error'"
                          variant="tonal"
                        >
                          {{ log.status === 'sent' ? 'Отправлено' : 'Ошибка' }}
                        </VChip>
                      </td>
                      <td class="text-truncate" style="max-width: 260px;" :title="log.text">
                        {{ log.text }}
                      </td>
                      <td class="text-caption text-medium-emphasis">
                        {{ log.max_message_id || log.error_text || '-' }}
                      </td>
                    </tr>
                  </tbody>
                </VTable>
                <VAlert v-else type="info" variant="tonal" class="mt-4">
                  Журнал отправленных сообщений пока пуст.
                </VAlert>
              </VWindowItem>

              <!-- Входящие события Webhook -->
              <VWindowItem value="webhooks">
                <VTable v-if="webhookEvents.length > 0" density="compact">
                  <thead>
                    <tr>
                      <th>Дата / Время</th>
                      <th>Тип события</th>
                      <th>User ID</th>
                      <th>Chat ID</th>
                      <th>Payload</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="ev in webhookEvents" :key="ev.id">
                      <td class="text-caption">{{ formatDate(ev.created_at) }}</td>
                      <td>
                        <VChip size="x-small" color="primary" variant="tonal">
                          {{ ev.event_type }}
                        </VChip>
                      </td>
                      <td class="font-weight-medium">{{ ev.user_id || '-' }}</td>
                      <td class="text-caption">{{ ev.chat_id || '-' }}</td>
                      <td>
                        <VBtn
                          size="x-small"
                          variant="text"
                          color="info"
                          @click="openJsonModal(ev.payload_json)"
                        >
                          JSON
                        </VBtn>
                      </td>
                    </tr>
                  </tbody>
                </VTable>
                <VAlert v-else type="info" variant="tonal" class="mt-4">
                  Входящих событий Webhook пока не зафиксировано.
                </VAlert>
              </VWindowItem>
            </VWindow>
          </VWindowItem>
        </VWindow>
      </VCardText>
    </VCard>

    <!-- Диалог добавления/редактирования бота -->
    <VDialog v-model="botDialog" max-width="600px">
      <VCard :title="editingBot.id ? 'Редактирование бота MAX' : 'Добавление нового бота MAX'">
        <VCardText>
          <VRow>
            <VCol cols="12">
              <VTextField
                v-model="editingBot.bot_token"
                label="Токен доступа бота"
                placeholder="Вставьте токен бота из платформы MAX"
                type="password"
                persistent-placeholder
                append-inner-icon="bx-check-shield"
                @click:append-inner="verifyTokenInDialog"
              />
              <div class="d-flex justify-end mt-1">
                <VBtn
                  size="x-small"
                  variant="text"
                  color="primary"
                  :loading="verifyingBot"
                  @click="verifyTokenInDialog"
                >
                  Проверить токен в MAX
                </VBtn>
              </div>
            </VCol>

            <VCol cols="12" md="6">
              <VTextField
                v-model="editingBot.bot_name"
                label="Название бота"
                placeholder="Мой Бот"
              />
            </VCol>

            <VCol cols="12" md="6">
              <VTextField
                v-model="editingBot.bot_username"
                label="Юзернейм бота"
                placeholder="bot_username"
                prefix="@"
              />
            </VCol>

            <VCol cols="12">
              <VTextarea
                v-model="editingBot.welcome_message"
                label="Приветственное сообщение (при старте)"
                rows="2"
              />
            </VCol>

            <VCol cols="12">
              <VSwitch
                v-model="editingBot.request_contact_on_start"
                label="Запрашивать номер телефона при нажатии кнопки Старт"
                color="primary"
              />
            </VCol>

            <VCol cols="12">
              <VSwitch
                v-model="editingBot.is_default_for_notifications"
                label="Использовать этого бота по умолчанию для уведомлений"
                color="primary"
              />
            </VCol>

            <VCol cols="12">
              <VSwitch
                v-model="editingBot.is_active"
                label="Активен"
                color="success"
              />
            </VCol>
          </VRow>
        </VCardText>

        <VCardActions>
          <VSpacer />
          <VBtn variant="text" @click="botDialog = false">Отмена</VBtn>
          <VBtn color="primary" @click="saveBot">Сохранить бота</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог управления Webhook -->
    <VDialog v-model="webhookDialog" max-width="550px">
      <VCard title="Управление Webhook подпиской бота">
        <VCardText>
          <p class="text-body-2 text-medium-emphasis mb-4">
            Webhook позволяет получать уведомления о старте бота, текстовые сообщения и переданные клиентами номера телефонов в реальном времени.
          </p>

          <VTextField
            v-model="webhookUrlInput"
            label="URL обработчика Webhook"
            placeholder="https://vezuroll.ru/api/v1/max/webhook"
            class="mb-4"
          />

          <div class="d-flex justify-space-between align-center">
            <VBtn
              color="error"
              variant="outlined"
              size="small"
              @click="deleteBotWebhook"
            >
              Снять Webhook
            </VBtn>

            <VBtn
              color="primary"
              size="small"
              @click="setBotWebhook"
            >
              Зарегистрировать Webhook
            </VBtn>
          </div>
        </VCardText>
        <VCardActions>
          <VSpacer />
          <VBtn variant="text" @click="webhookDialog = false">Закрыть</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог команд бота -->
    <VDialog v-model="commandsDialog" max-width="600px">
      <VCard title="Команды бота в меню MAX">
        <VCardText>
          <p class="text-body-2 text-medium-emphasis mb-4">
            Управляйте командами, отображаемыми в меню мессенджера MAX для пользователей.
          </p>

          <div
            v-for="(cmd, idx) in commandsList"
            :key="idx"
            class="d-flex gap-2 mb-2 align-center"
          >
            <VTextField
              v-model="cmd.name"
              label="Команда"
              placeholder="start"
              density="compact"
              prefix="/"
              style="max-width: 160px;"
            />
            <VTextField
              v-model="cmd.description"
              label="Описание"
              placeholder="Запустить бота"
              density="compact"
            />
            <VBtn
              icon="bx-trash"
              variant="text"
              color="error"
              size="small"
              @click="removeCommandRow(idx)"
            />
          </div>

          <VBtn
            variant="tonal"
            color="primary"
            size="small"
            prepend-icon="bx-plus"
            class="mt-2"
            @click="addCommandRow"
          >
            Добавить команду
          </VBtn>
        </VCardText>

        <VCardActions>
          <VSpacer />
          <VBtn variant="text" @click="commandsDialog = false">Отмена</VBtn>
          <VBtn color="primary" @click="saveBotCommands">Синхронизировать с MAX</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог просмотра JSON Payload -->
    <VDialog v-model="jsonDialog" max-width="650px">
      <VCard title="Входящий Webhook JSON">
        <VCardText>
          <pre class="max-json-box">{{ selectedJsonPayload }}</pre>
        </VCardText>
        <VCardActions>
          <VSpacer />
          <VBtn variant="text" @click="jsonDialog = false">Закрыть</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Снекбар уведомлений -->
    <VSnackbar
      v-model="snackbar"
      :color="snackbarColor"
      timeout="3500"
      location="top right"
    >
      {{ snackbarText }}
    </VSnackbar>
  </div>
</template>
