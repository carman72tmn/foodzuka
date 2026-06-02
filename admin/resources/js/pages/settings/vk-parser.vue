<script setup>
import { ref, onMounted } from "vue"

const loading = ref(false)
const saving = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const settings = ref({
  vk_parser_enabled: false,
  vk_parser_phrase: "здравствуйте! Ваш заказ {order_id} принят и мы приступили к его приготовлению",
  vk_notification_settings: {
    delivery: {
      enabled_statuses: [],
      templates: {}
    },
    pickup: {
      enabled_statuses: [],
      templates: {}
    }
  }
})

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
    const res = await fetch(`${API_BASE}/settings`)
    if (res.ok) {
      const data = await res.json()
      settings.value.vk_parser_enabled = !!data.vk_parser_enabled
      if (data.vk_parser_phrase) {
        settings.value.vk_parser_phrase = data.vk_parser_phrase
      }
      
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
    const res = await fetch(`${API_BASE}/parser/scan/status`)
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
    const res = await fetch(`${API_BASE}/parser/scan`, { method: "POST" })
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
      method: "DELETE"
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
  try {
    // Сначала получаем все настройки, чтобы не затереть другие поля
    const currentRes = await fetch(`${API_BASE}/settings`)
    let currentData = {}
    if (currentRes.ok) {
      currentData = await currentRes.json()
    }

    const payload = {
      ...currentData,
      vk_parser_enabled: settings.value.vk_parser_enabled,
      vk_parser_phrase: settings.value.vk_parser_phrase,
      vk_notification_settings: settings.value.vk_notification_settings,
    }

    const res = await fetch(`${API_BASE}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
const activeTab = ref(0)

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
    
    const res = await fetch(url)
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
    
    const res = await fetch(url)
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
    const res = await fetch(`${API_BASE}/parser/messages/cleanup`, { method: "POST" })
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
    const res = await fetch(`${API_BASE}/parser/stats`)
    if (res.ok) {
      stats.value = await res.json()
    }
  } catch (e) {
    console.error("Error loading stats:", e)
  }
}

onMounted(async () => {
  await loadSettings()
  await loadStats()
  await loadMessageStats()
  await loadMessages()
})
</script>

<template>
  <VTabs v-model="activeTab" class="mb-4">
    <VTab :value="0">
      <VIcon icon="mdi-cog" class="me-2" />
      Настройки и статистика
    </VTab>
    <VTab :value="1">
      <VIcon icon="mdi-bell-ring" class="me-2" />
      Настройка уведомлений
    </VTab>
    <VTab :value="2">
      <VIcon icon="mdi-message-text" class="me-2" />
      Мониторинг сообщений
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

            <VCol cols="12" class="d-flex gap-4 mt-4">
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
            <VCardTitle class="d-flex align-center">
              <VIcon icon="mdi-bell-cog-outline" class="me-2" color="primary" />
              Настройка уведомлений о заказах
              <VSpacer />
              <VBtn
                color="primary"
                :loading="saving"
                prepend-icon="mdi-content-save"
                @click="saveSettings"
                size="small"
              >
                Сохранить всё
              </VBtn>
            </VCardTitle>
            <VCardText>
              <p class="text-body-2 mb-6">
                Здесь вы можете настроить автоматические сообщения, которые будут приходить клиенту в ВК при изменении статуса его заказа.
                Уведомления приходят только тем пользователям, чей VK профиль привязан к системе.
              </p>

              <VTabs v-model="notificationTypeTab" density="compact" color="primary" class="mb-4">
                <VTab value="delivery">Доставка</VTab>
                <VTab value="pickup">Самовывоз</VTab>
              </VTabs>

              <VWindow v-model="notificationTypeTab">
                <!-- ДОСТАВКА -->
                <VWindowItem value="delivery">
                  <VRow>
                    <VCol 
                      cols="12" 
                      v-for="status in deliveryStatusList" 
                      :key="status.value"
                      class="border-bottom pb-4"
                    >
                      <div class="d-flex align-center mb-2">
                        <VCheckbox
                          v-model="settings.vk_notification_settings.delivery.enabled_statuses"
                          :value="status.value"
                          :label="status.title"
                          hide-details
                          density="compact"
                          color="success"
                        />
                        <VChip size="x-small" class="ms-2" variant="flat">{{ status.value }}</VChip>
                      </div>
                      
                      <VTextarea
                        v-if="settings.vk_notification_settings.delivery.enabled_statuses.includes(status.value)"
                        v-model="settings.vk_notification_settings.delivery.templates[status.value]"
                        label="Шаблон сообщения"
                        rows="2"
                        density="comfortable"
                        variant="outlined"
                        hide-details
                        placeholder="Введите текст уведомления..."
                        class="mt-2"
                      />
                    </VCol>
                  </VRow>
                </VWindowItem>

                <!-- САМОВЫВОЗ -->
                <VWindowItem value="pickup">
                  <VRow>
                    <VCol 
                      cols="12" 
                      v-for="status in pickupStatusList" 
                      :key="status.value"
                      class="border-bottom pb-4"
                    >
                      <div class="d-flex align-center mb-2">
                        <VCheckbox
                          v-model="settings.vk_notification_settings.pickup.enabled_statuses"
                          :value="status.value"
                          :label="status.title"
                          hide-details
                          density="compact"
                          color="success"
                        />
                        <VChip size="x-small" class="ms-2" variant="flat">{{ status.value }}</VChip>
                      </div>
                      
                      <VTextarea
                        v-if="settings.vk_notification_settings.pickup.enabled_statuses.includes(status.value)"
                        v-model="settings.vk_notification_settings.pickup.templates[status.value]"
                        label="Шаблон сообщения"
                        rows="2"
                        density="comfortable"
                        variant="outlined"
                        hide-details
                        placeholder="Введите текст уведомления..."
                        class="mt-2"
                      />
                    </VCol>
                  </VRow>
                </VWindowItem>
              </VWindow>

              <VDivider class="my-6" />
              
              <VAlert type="info" variant="tonal" density="compact">
                <div class="text-subtitle-2 mb-1">Доступные переменные для шаблонов:</div>
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

              <div class="mt-6">
                <VBtn
                  color="primary"
                  :loading="saving"
                  prepend-icon="mdi-content-save"
                  @click="saveSettings"
                >
                  Сохранить настройки уведомлений
                </VBtn>
              </div>
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
                            <a :href="`https://vk.com/id${msg.vk_user_id}`" target="_blank" class="text-subtitle-2 text-decoration-none">
                              {{ msg.user?.first_name ? `${msg.user.first_name} ${msg.user.last_name}` : `ID ${msg.vk_user_id}` }}
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
</template>
