<script setup>
import { ref, onMounted, computed, onBeforeUnmount } from "vue"
import { formatDateTime } from "@/utils/date"
import { getAuthHeaders } from "@/utils/auth"

const loading = ref(false)
const saving = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")
const logs = ref([])
const loadingLogs = ref(false)
const activeTab = ref(0)
const selectedFilterBot = ref(null)

const botFilterOptions = computed(() => {
  const options = [{ title: 'Все группы', value: null }]
  bots.value.forEach(bot => {
    options.push({ title: `${bot.name} (${bot.vk_group_id})`, value: bot.vk_group_id })
  })
  return options
})

// Статистика и боты
const bots = ref([])
const loadingBots = ref(false)
const botDialog = ref(false)
const dialogMode = ref('create') // 'create' | 'edit'
const editBotId = ref(null)

const botForm = ref({
  name: '',
  vk_group_id: '',
  vk_bot_token: '',
  vk_user_token: '',
  vk_secret_key: '',
  vk_confirmation_code: '',
  is_active: true,
  is_main: false,
  use_longpoll: false
})

const testingBotId = ref(null)
const scanningBotId = ref(null)
const scanIntervals = {}

const API_BASE = "/api/v1/vk"

const webhookUrl = computed(() => {
  return `${window.location.origin}/api/v1/vk/webhook`
})

const kpiStats = computed(() => {
  const totalBots = bots.value.length
  const activeBots = bots.value.filter(b => b.is_active).length
  const totalLinkedUsers = bots.value.reduce((sum, b) => sum + (b.linked_users_count || 0), 0)
  const totalEvents = bots.value.reduce((sum, b) => sum + (b.total_events_count || 0), 0)
  
  return {
    totalBots,
    activeBots,
    totalLinkedUsers,
    totalEvents
  }
})

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

// Загрузка ботов и их статистики
const loadBots = async () => {
  loadingBots.value = true
  try {
    const res = await fetch(`${API_BASE}/bots`, { headers: getAuthHeaders() })
    if (res.ok) {
      bots.value = await res.json()
      
      // Запускаем опрос статуса сканирования для ботов, которые в процессе
      bots.value.forEach(bot => {
        if (bot.scan_status?.status === 'running') {
          startScanPolling(bot.id)
        }
      })
    }
  } catch (e) {
    showMessage("Ошибка загрузки списка ботов", "error")
  } finally {
    loadingBots.value = false
  }
}

// Сохранение / создание бота
const saveBot = async () => {
  if (!botForm.value.name || !botForm.value.vk_group_id || !botForm.value.vk_bot_token) {
    showMessage("Заполните обязательные поля: Название, ID группы и Токен", "error")
    return
  }
  
  saving.value = true
  try {
    const method = dialogMode.value === 'create' ? 'POST' : 'PATCH'
    const url = dialogMode.value === 'create' ? `${API_BASE}/bots` : `${API_BASE}/bots/${editBotId.value}`
    
    // Подготовка payload
    const payload = { ...botForm.value }
    payload.vk_group_id = parseInt(payload.vk_group_id)
    
    const res = await fetch(url, {
      method,
      headers: {
        ...getAuthHeaders(),
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    })
    
    if (res.ok) {
      showMessage(dialogMode.value === 'create' ? "Бот успешно добавлен" : "Настройки бота успешно сохранены")
      botDialog.value = false
      await loadBots()
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка сохранения бота", "error")
    }
  } catch (e) {
    showMessage("Ошибка при отправке запроса", "error")
  } finally {
    saving.value = false
  }
}

// Открытие диалога создания бота
const openCreateDialog = () => {
  dialogMode.value = 'create'
  editBotId.value = null
  botForm.value = {
    name: '',
    vk_group_id: '',
    vk_bot_token: '',
    vk_user_token: '',
    vk_secret_key: '',
    vk_confirmation_code: '',
    is_active: true,
    is_main: bots.value.length === 0, // первый бот по умолчанию основной
    use_longpoll: false
  }
  botDialog.value = true
}

// Открытие диалога редактирования
const openEditDialog = (bot) => {
  dialogMode.value = 'edit'
  editBotId.value = bot.id
  botForm.value = {
    name: bot.name,
    vk_group_id: bot.vk_group_id.toString(),
    vk_bot_token: bot.vk_bot_token || '',
    vk_user_token: bot.vk_user_token || '',
    vk_secret_key: bot.vk_secret_key || '',
    vk_confirmation_code: bot.vk_confirmation_code || '',
    is_active: bot.is_active,
    is_main: bot.is_main,
    use_longpoll: bot.use_longpoll || false
  }
  botDialog.value = true
}

// Удаление бота
const deleteBot = async (botId) => {
  if (!confirm("Вы действительно хотите удалить этого бота?")) return
  
  try {
    const res = await fetch(`${API_BASE}/bots/${botId}`, {
      method: "DELETE",
      headers: getAuthHeaders()
    })
    if (res.ok) {
      showMessage("Бот успешно удален")
      await loadBots()
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка удаления бота", "error")
    }
  } catch (e) {
    showMessage("Ошибка соединения с сервером", "error")
  }
}

// Проверка соединения бота
const testBotConnection = async (botId) => {
  testingBotId.value = botId
  try {
    const res = await fetch(`${API_BASE}/bots/${botId}/test-connection`, {
      method: "POST",
      headers: getAuthHeaders()
    })
    const data = await res.json()
    if (data.status === "success") {
      showMessage(`Соединение успешно! Группа: ${data.data?.[0]?.name || botId}`, "success")
    } else {
      showMessage(data.message || "Ошибка проверки токена", "error")
    }
  } catch (e) {
    showMessage("Ошибка при проверке соединения", "error")
  } finally {
    testingBotId.value = null
  }
}

// Запуск сканирования истории
const startBotScan = async (botId) => {
  try {
    const res = await fetch(`${API_BASE}/bots/${botId}/scan`, {
      method: "POST",
      headers: getAuthHeaders()
    })
    const data = await res.json()
    if (data.status === "success") {
      showMessage(data.message)
      startScanPolling(botId)
    } else {
      showMessage(data.message || "Ошибка запуска сканирования", "error")
    }
  } catch (e) {
    showMessage("Ошибка при запуске задачи", "error")
  }
}

// Опрос статуса сканирования
const startScanPolling = (botId) => {
  if (scanIntervals[botId]) return
  
  scanIntervals[botId] = setInterval(async () => {
    try {
      const res = await fetch(`${API_BASE}/bots/${botId}/scan/status`, { headers: getAuthHeaders() })
      if (res.ok) {
        const data = await res.json()
        const botIndex = bots.value.findIndex(b => b.id === botId)
        if (botIndex !== -1) {
          bots.value[botIndex].scan_status = data
          if (data.status !== 'running') {
            clearInterval(scanIntervals[botId])
            delete scanIntervals[botId]
            await loadBots() // Обновим статистику при завершении
            if (data.status === 'completed') {
              showMessage(`Сканирование истории бота #${botId} успешно завершено!`)
            } else if (data.status === 'error') {
              showMessage(`Ошибка сканирования бота #${botId}: ${data.error}`, "error")
            }
          }
        }
      }
    } catch (e) {
      console.error(`Error polling scan status for bot ${botId}:`, e)
    }
  }, 3000)
}

// Загрузка логов
const loadLogs = async () => {
  loadingLogs.value = true
  try {
    let url = `${API_BASE}/logs`
    if (selectedFilterBot.value) {
      url += `?vk_group_id=${selectedFilterBot.value}`
    }
    const res = await fetch(url, { headers: getAuthHeaders() })
    if (res.ok) {
      logs.value = await res.json()
    }
  } catch (e) {
    console.error("Ошибка загрузки логов VK:", e)
  } finally {
    loadingLogs.value = false
  }
}

const getBotNameByGroupId = (groupId) => {
  const bot = bots.value.find(b => b.vk_group_id === groupId)
  return bot ? bot.name : `Группа #${groupId}`
}

onMounted(async () => {
  await loadBots()
  await loadLogs()
})

onBeforeUnmount(() => {
  Object.keys(scanIntervals).forEach(key => {
    clearInterval(scanIntervals[key])
  })
})
</script>

<template>
  <VRow>
    <!-- KPI Карточки статистики -->
    <VCol cols="12" sm="6" md="3">
      <VCard class="kpi-card text-center py-4">
        <VCardText>
          <VIcon icon="mdi-robot-outline" size="40" color="primary" class="mb-2" />
          <h3 class="text-h4 font-weight-bold">{{ kpiStats.totalBots }}</h3>
          <p class="text-caption text-medium-emphasis mt-1">Всего VK Ботов ({{ kpiStats.activeBots }} активных)</p>
        </VCardText>
      </VCard>
    </VCol>
    <VCol cols="12" sm="6" md="3">
      <VCard class="kpi-card text-center py-4">
        <VCardText>
          <VIcon icon="mdi-account-multiple-outline" size="40" color="success" class="mb-2" />
          <h3 class="text-h4 font-weight-bold">{{ kpiStats.totalLinkedUsers }}</h3>
          <p class="text-caption text-medium-emphasis mt-1">Привязанных гостей</p>
        </VCardText>
      </VCard>
    </VCol>
    <VCol cols="12" sm="6" md="3">
      <VCard class="kpi-card text-center py-4">
        <VCardText>
          <VIcon icon="mdi-message-processing-outline" size="40" color="info" class="mb-2" />
          <h3 class="text-h4 font-weight-bold">{{ kpiStats.totalEvents }}</h3>
          <p class="text-caption text-medium-emphasis mt-1">Событий Callback API всего</p>
        </VCardText>
      </VCard>
    </VCol>
    <VCol cols="12" sm="6" md="3">
      <VCard class="kpi-card text-center py-4">
        <VCardText>
          <VIcon icon="mdi-link-variant" size="40" color="warning" class="mb-2" />
          <h3 class="text-subtitle-1 font-weight-bold text-truncate" style="max-width: 100%;">/webhook</h3>
          <p class="text-caption text-medium-emphasis mt-1">Общий Callback Webhook</p>
        </VCardText>
      </VCard>
    </VCol>

    <!-- Основной контент (Вкладки) -->
    <VCol cols="12" class="mt-4">
      <VTabs v-model="activeTab" class="mb-4">
        <VTab :value="0">
          <VIcon icon="mdi-robot-industrial-outline" class="me-2" />
          Подключения (Боты)
        </VTab>
        <VTab :value="1">
          <VIcon icon="mdi-history" class="me-2" />
          События API
        </VTab>
        <VTab :value="2">
          <VIcon icon="mdi-information-outline" class="me-2" />
          Справка Callback API
        </VTab>
      </VTabs>

      <VWindow v-model="activeTab">
        <!-- Вкладка Подключения -->
        <VWindowItem :value="0">
          <VCard>
            <VCardTitle class="d-flex justify-space-between align-center py-4">
              <span>Подключения VK Ботов</span>
              <VBtn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
                Добавить бота
              </VBtn>
            </VCardTitle>
            <VCardText>
              <VTable density="comfortable">
                <thead>
                  <tr>
                    <th class="text-uppercase text-no-wrap">Бот</th>
                    <th class="text-uppercase text-no-wrap">Group ID</th>
                    <th class="text-uppercase text-no-wrap text-center">Статус</th>
                    <th class="text-uppercase text-no-wrap text-center">Связи / События</th>
                    <th class="text-uppercase">История сканирования</th>
                    <th class="text-uppercase text-no-wrap text-center">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="loadingBots">
                    <td colspan="6" class="text-center py-8">
                      <VProgressCircular indeterminate color="primary" />
                    </td>
                  </tr>
                  <tr v-else-if="bots.length === 0">
                    <td colspan="6" class="text-center py-8 text-medium-emphasis">
                      Нет подключенных ботов ВКонтакте. Добавьте первого бота.
                    </td>
                  </tr>
                  <tr v-for="bot in bots" :key="bot.id">
                    <td class="text-no-wrap">
                      <div class="d-flex align-center">
                        <VAvatar color="#0077FF" class="me-3" size="32">
                          <VIcon icon="mdi-vk" color="white" />
                        </VAvatar>
                        <div>
                          <div class="font-weight-bold d-flex align-center">
                            {{ bot.name }}
                            <VChip v-if="bot.is_main" size="x-small" color="primary" class="ms-2" variant="flat">
                              Основной
                            </VChip>
                          </div>
                          <div class="d-flex align-center gap-2 mt-1 text-caption">
                            <span class="d-flex align-center">
                              <VIcon :icon="bot.vk_bot_token ? 'mdi-key' : 'mdi-key-off'" size="12" :color="bot.vk_bot_token ? 'success' : 'error'" class="me-1" />
                              <span :class="bot.vk_bot_token ? 'text-success' : 'text-error'" style="font-size: 11px;">Токен {{ bot.vk_bot_token ? 'настроен' : 'не задан' }}</span>
                            </span>
                            <span class="text-medium-emphasis">•</span>
                            <span class="d-flex align-center">
                              <VIcon :icon="bot.vk_secret_key ? 'mdi-lock-check-outline' : 'mdi-lock-open-variant-outline'" size="12" :color="bot.vk_secret_key ? 'success' : 'error'" class="me-1" />
                              <span :class="bot.vk_secret_key ? 'text-success' : 'text-error'" style="font-size: 11px;">Секрет {{ bot.vk_secret_key ? 'настроен' : 'не задан' }}</span>
                            </span>
                          </div>
                        </div>
                      </div>
                    </td>
                    <td><code>{{ bot.vk_group_id }}</code></td>
                    <td class="text-center">
                      <VChip size="small" :color="bot.is_active ? 'success' : 'error'">
                        {{ bot.is_active ? 'Активен' : 'Отключен' }}
                      </VChip>
                    </td>
                    <td class="text-center">
                      <div class="d-flex flex-column align-center">
                        <div>
                          <VIcon icon="mdi-account-circle-outline" size="14" class="me-1" color="success" />
                          <span>{{ bot.linked_users_count || 0 }}</span>
                        </div>
                        <div class="text-caption text-medium-emphasis">
                          <VIcon icon="mdi-bell-outline" size="12" class="me-1" color="info" />
                          <span>{{ bot.total_events_count || 0 }}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <!-- Статус сканирования истории -->
                      <div v-if="bot.scan_status?.status === 'running'" class="pe-4" style="max-width: 180px;">
                        <div class="d-flex justify-space-between text-caption mb-1">
                          <span>Сканирование...</span>
                          <span>{{ Math.round((bot.scan_status.progress / (bot.scan_status.total || 1)) * 100) }}%</span>
                        </div>
                        <VProgressLinear
                          :model-value="(bot.scan_status.progress / (bot.scan_status.total || 1)) * 100"
                          height="6"
                          color="primary"
                          rounded
                          striped
                        />
                      </div>
                      <div v-else-if="bot.last_scan_at" class="text-caption">
                        <VChip size="x-small" color="success" variant="tonal" class="mb-1">
                          Сканировано
                        </VChip>
                        <div class="text-caption text-medium-emphasis" style="font-size: 11px;">
                          {{ formatDateTime(bot.last_scan_at) }}
                        </div>
                      </div>
                      <div v-else>
                        <VChip size="x-small" color="grey" variant="tonal">
                          Не выполнялось
                        </VChip>
                      </div>
                    </td>
                    <td class="text-center text-no-wrap">
                      <div class="d-flex justify-center gap-1">
                        <!-- Проверить соединение -->
                        <VBtn
                          icon
                          size="small"
                          variant="text"
                          color="info"
                          :loading="testingBotId === bot.id"
                          @click="testBotConnection(bot.id)"
                        >
                          <VIcon icon="mdi-robot" />
                          <VTooltip activator="parent">Проверить соединение с VK</VTooltip>
                        </VBtn>
                        
                        <!-- Запустить скан истории -->
                        <VBtn
                          icon
                          size="small"
                          variant="text"
                          color="secondary"
                          :disabled="bot.scan_status?.status === 'running'"
                          @click="startBotScan(bot.id)"
                        >
                          <VIcon icon="mdi-history" />
                          <VTooltip activator="parent">Ретроспективный скан истории</VTooltip>
                        </VBtn>

                        <!-- Редактировать -->
                        <VBtn
                          icon
                          size="small"
                          variant="text"
                          color="primary"
                          @click="openEditDialog(bot)"
                        >
                          <VIcon icon="mdi-pencil-outline" />
                          <VTooltip activator="parent">Редактировать</VTooltip>
                        </VBtn>

                        <!-- Удалить -->
                        <VBtn
                          icon
                          size="small"
                          variant="text"
                          color="error"
                          @click="deleteBot(bot.id)"
                        >
                          <VIcon icon="mdi-delete-outline" />
                          <VTooltip activator="parent">Удалить</VTooltip>
                        </VBtn>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </VTable>
            </VCardText>
          </VCard>
        </VWindowItem>

        <!-- Вкладка События API -->
        <VWindowItem :value="1">
          <VCard>
            <VCardTitle class="d-flex justify-space-between align-center py-4 flex-wrap gap-4">
              <span>Последние события Callback API</span>
              <div class="d-flex align-center gap-3" style="min-width: 300px;">
                <VSelect
                  v-model="selectedFilterBot"
                  :items="botFilterOptions"
                  item-title="title"
                  item-value="value"
                  label="Фильтр по группе"
                  density="compact"
                  variant="outlined"
                  hide-details
                  @update:model-value="loadLogs"
                />
                <VBtn color="secondary" variant="tonal" prepend-icon="mdi-refresh" @click="loadLogs">
                  Обновить
                </VBtn>
              </div>
            </VCardTitle>
            <VCardText>
              <VTable density="compact" class="text-no-wrap">
                <thead>
                  <tr>
                    <th class="text-uppercase">ID</th>
                    <th class="text-uppercase">Бот / Группа</th>
                    <th class="text-uppercase">Событие</th>
                    <th class="text-uppercase">Дата/Время</th>
                    <th class="text-uppercase text-center">Payload</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="loadingLogs">
                    <td colspan="5" class="text-center py-8">Загрузка логов...</td>
                  </tr>
                  <tr v-else-if="logs.length === 0">
                    <td colspan="5" class="text-center py-8 text-medium-emphasis">Событий Callback API пока нет</td>
                  </tr>
                  <tr v-for="log in logs" :key="log.id">
                    <td>{{ log.id }}</td>
                    <td>
                      <span class="font-weight-medium">{{ getBotNameByGroupId(log.vk_group_id) }}</span>
                      <div class="text-caption text-medium-emphasis">Group ID: {{ log.vk_group_id || '---' }}</div>
                    </td>
                    <td>
                      <VChip size="small" :color="log.event_type === 'confirmation' ? 'info' : 'success'">
                        {{ log.event_type }}
                      </VChip>
                    </td>
                    <td>{{ formatDateTime(log.created_at) }}</td>
                    <td class="text-center">
                      <VBtn icon size="x-small" variant="text" @click="console.log(log.payload)">
                        <VIcon icon="mdi-eye" />
                        <VTooltip activator="parent">Вывести Payload в консоль</VTooltip>
                      </VBtn>
                    </td>
                  </tr>
                </tbody>
              </VTable>
            </VCardText>
          </VCard>
        </VWindowItem>

        <!-- Вкладка Справка -->
        <VWindowItem :value="2">
          <VCard>
            <VCardTitle class="py-4">Инструкция по настройке Callback API ВКонтакте</VCardTitle>
            <VCardText>
              <ol class="ps-6 text-body-1 d-flex flex-column gap-3">
                <li>
                  Перейдите в настройки вашего сообщества ВКонтакте: <strong>Управление -> Настройки -> Работа с API</strong>.
                </li>
                <li>
                  Нажмите вкладку <strong>Callback API</strong>.
                </li>
                <li>
                  Скопируйте общий Webhook URL: <code class="text-primary font-weight-bold bg-grey-lighten-3 px-2 py-1 rounded">{{ webhookUrl }}</code>
                </li>
                <li>
                  Вставьте этот URL в поле <strong>Адрес сервера</strong> в ВКонтакте.
                </li>
                <li>
                  В поле <strong>Секретный ключ</strong> введите произвольную строку (например, надежный пароль) и обязательно введите этот же ключ в настройках бота в админ-панели (поле Secret Key).
                </li>
                <li>
                  ВКонтакте покажет вам <strong>Строку, которую должен вернуть сервер</strong> (Confirmation Code). Скопируйте её и сохраните в настройках вашего бота в админ-панели (поле Confirmation Code).
                </li>
                <li>
                  После заполнения всех полей в админ-панели и сохранения настроек, нажмите кнопку <strong>Подтвердить</strong> в интерфейсе ВКонтакте. Наш бэкенд автоматически распознает запрос и вернет нужный Confirmation Code для успешной верификации!
                </li>
                <li>
                  На вкладке <strong>Типы событий</strong> в ВКонтакте отметьте галочками нужные события:
                  <ul>
                    <li><code>Входящие сообщения</code> (message_new) — для работы парсера и команд бота.</li>
                    <li><code>Исходящие сообщения</code> (message_reply) — для сохранения истории ответов бота.</li>
                    <li><code>Разрешение на получение сообщений</code> (message_allow) — для отслеживания подписки гостя.</li>
                    <li><code>Запрет на получение сообщений</code> (message_deny) — для отслеживания отписки.</li>
                  </ul>
                </li>
              </ol>
            </VCardText>
          </VCard>
        </VWindowItem>
      </VWindow>
    </VCol>
  </VRow>

  <!-- Модальное окно Добавления/Редактирования бота -->
  <VDialog v-model="botDialog" max-width="600px">
    <VCard>
      <VCardTitle class="py-4">
        {{ dialogMode === 'create' ? 'Добавить подключение VK Бота' : 'Редактировать VK Бота' }}
      </VCardTitle>
      <VCardText class="pt-2">
        <VRow>
          <VCol cols="12">
            <VTextField
              v-model="botForm.name"
              label="Название подключения *"
              hint="Например: Основной бот, Дополнительная группа доставки"
              persistent-hint
            />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField
              v-model="botForm.vk_group_id"
              label="ID сообщества ВК *"
              hint="Только цифры (например: 186688777)"
              persistent-hint
              type="number"
            />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField
              v-model="botForm.vk_confirmation_code"
              label="Код подтверждения (Confirmation Code)"
              hint="Строка из Callback API для подтверждения сервера"
              persistent-hint
            />
          </VCol>
          <VCol cols="12">
            <VTextField
              v-model="botForm.vk_bot_token"
              label="VK Bot Token *"
              hint="Токен доступа сообщества (с правами на работу с сообщениями)"
              persistent-hint
              type="text"
            />
          </VCol>
          <VCol cols="12">
            <VTextField
              v-model="botForm.vk_user_token"
              label="VK User Token (для динамической обложки)"
              hint="Токен пользователя (User Access Token) с правами photos, groups, offline. Необходим для автоматического обновления обложки."
              persistent-hint
              type="text"
            />
            <div class="mt-2 pa-3 bg-light-error border rounded text-xs" style="border: 1px solid rgba(var(--v-theme-primary), 0.2) !important; background-color: rgba(var(--v-theme-primary), 0.03);">
              <div class="font-weight-bold mb-1 text-primary">Как получить токен пользователя ВК:</div>
              <ol class="ps-4">
                <li class="mb-1">
                  Перейдите по 
                  <a 
                    href="https://oauth.vk.ru/authorize?client_id=2685278&scope=photos,groups,offline&response_type=token&redirect_uri=https://oauth.vk.ru/blank.html" 
                    target="_blank" 
                    class="text-primary font-weight-bold"
                  >
                    ссылке авторизации через Kate Mobile
                  </a>.
                </li>
                <li class="mb-1">Разрешите доступ к вашему аккаунту (аккаунт должен быть администратором группы).</li>
                <li class="mb-1">Вас перенаправит на пустую страницу. Скопируйте из адресной строки браузера весь текст, который находится между <b>access_token=</b> и <b>&expires_in=</b>.</li>
                <li>Вставьте скопированный токен в поле выше и нажмите <b>Сохранить</b>.</li>
              </ol>
            </div>
          </VCol>
          <VCol cols="12">
            <VTextField
              v-model="botForm.vk_secret_key"
              label="Секретный ключ (Secret Key)"
              hint="Ключ для защиты входящих вебхуков Callback API"
              persistent-hint
            />
          </VCol>
          <VCol cols="12" class="mt-2">
            <VSwitch
              v-model="botForm.use_longpoll"
              label="Подключение по Long Poll (вместо Callback API)"
              color="info"
              hide-details
              hint="Включите, чтобы бот работал без настройки вебхуков в панели ВК"
              persistent-hint
            />
          </VCol>
          <VCol cols="6" class="mt-2">
            <VSwitch
              v-model="botForm.is_active"
              label="Активен"
              color="success"
              hide-details
            />
          </VCol>
          <VCol cols="6" class="mt-2">
            <VSwitch
              v-model="botForm.is_main"
              label="Основной бот"
              color="primary"
              hide-details
              hint="Уведомления гостям отправляются от основного бота по умолчанию"
              persistent-hint
            />
          </VCol>
        </VRow>
      </VCardText>
      <VCardActions class="pa-4">
        <VSpacer />
        <VBtn variant="tonal" color="secondary" @click="botDialog = false">Отмена</VBtn>
        <VBtn color="primary" :loading="saving" @click="saveBot">
          Сохранить
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- Toast уведомления -->
  <VSnackbar
    v-model="snackbar"
    :color="snackbarColor"
    :timeout="4000"
    location="top"
  >
    {{ snackbarText }}
  </VSnackbar>
</template>

<style scoped>
.kpi-card {
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 8px;
}
.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}
</style>
