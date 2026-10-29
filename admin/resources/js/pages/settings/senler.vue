<script setup>
import { ref, onMounted, watch } from "vue"
import axios from "axios"

const tab = ref("settings")
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const syncing = ref(false)
const loadingStats = ref(false)
const loadingSubscribers = ref(false)
const sendingBroadcast = ref(false)

const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

// Данные настроек
const settings = ref({
  id: null,
  access_token: "",
  group_id: null,
  vk_group_id: null,
  secret_key: "",
  is_active: true
})

// Данные статистики
const stats = ref({
  total_subscribers: 0,
  active_subscribers: 0,
  deliveries: []
})

// Данные подписчиков
const subscribers = ref([])
const totalSubscribers = ref(0)
const page = ref(1)
const size = ref(20)
const search = ref("")
const filterGroupId = ref(null)
const filterSubscribed = ref(null)
const senlerGroups = ref([])

// Форма рассылки
const broadcastDialog = ref(false)
const broadcastForm = ref({
  name: "",
  message: "",
  subscription_id: 0,
  is_now: true,
  scheduled_time: null,
  scheduled_date_val: "",
  scheduled_time_val: ""
})

const getWebhookUrl = () => {
  const secretPart = settings.value.secret_key ? `?secret=${settings.value.secret_key}` : ""
  return `https://vezuroll.ru/api/v1/webhooks/senler${secretPart}`
}

const loadSettings = async () => {
  loading.value = true
  try {
    const res = await axios.get("/api/v1/senler/settings")
    settings.value = res.data
  } catch (e) {
    showMessage("Ошибка загрузки настроек", "error")
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    const res = await axios.post("/api/v1/senler/settings", settings.value)
    settings.value = res.data
    showMessage("Настройки сохранены")
  } catch (e) {
    const errorMsg = e.response?.data?.detail || "Ошибка сохранения настроек"
    showMessage(errorMsg, "error")
  } finally {
    saving.value = false
  }
}

const testConnection = async () => {
  testing.value = true
  try {
    await axios.post("/api/v1/senler/settings/test", {
      access_token: settings.value.access_token,
      group_id: settings.value.group_id
    })
    showMessage("Соединение успешно проверено!")
  } catch (e) {
    const errorMsg = e.response?.data?.detail || "Ошибка проверки соединения"
    showMessage(errorMsg, "error")
  } finally {
    testing.value = false
  }
}

const loadStatsAndDeliveries = async () => {
  loadingStats.value = true
  try {
    const res = await axios.get("/api/v1/senler/stats")
    stats.value = res.data
  } catch (e) {
    showMessage("Не удалось загрузить статистику", "error")
  } finally {
    loadingStats.value = false
  }
}

const loadSenlerGroups = async () => {
  try {
    const res = await axios.get("/api/v1/senler/groups")
    senlerGroups.value = res.data
  } catch (e) {
    logger.error("Failed to load Senler groups:", e)
  }
}

const loadSubscribers = async () => {
  loadingSubscribers.value = true
  try {
    const params = {
      page: page.value,
      size: size.value
    }
    if (search.value) params.search = search.value
    if (filterGroupId.value !== null) params.group_id = filterGroupId.value
    if (filterSubscribed.value !== null) params.is_subscribed = filterSubscribed.value

    const res = await axios.get("/api/v1/senler/subscribers", { params })
    subscribers.value = res.data.items
    totalSubscribers.value = res.data.total
  } catch (e) {
    showMessage("Не удалось загрузить список подписчиков", "error")
  } finally {
    loadingSubscribers.value = false
  }
}

const triggerSync = async () => {
  syncing.value = true
  try {
    await axios.post("/api/v1/senler/subscribers/sync")
    showMessage("Синхронизация запущена в фоновом режиме")
  } catch (e) {
    showMessage("Не удалось запустить синхронизацию", "error")
  } finally {
    syncing.value = false
  }
}

const openBroadcastDialog = async () => {
  broadcastForm.value = {
    name: "",
    message: "",
    subscription_id: 0,
    is_now: true,
    scheduled_time: null,
    scheduled_date_val: "",
    scheduled_time_val: ""
  }
  broadcastDialog.value = true
  await loadSenlerGroups()
}

const sendBroadcast = async () => {
  sendingBroadcast.value = true
  try {
    const payload = {
      name: broadcastForm.value.name,
      message: broadcastForm.value.message,
      subscription_id: broadcastForm.value.subscription_id,
      is_now: broadcastForm.value.is_now
    }

    if (!broadcastForm.value.is_now && broadcastForm.value.scheduled_date_val && broadcastForm.value.scheduled_time_val) {
      const dateTimeStr = `${broadcastForm.value.scheduled_date_val}T${broadcastForm.value.scheduled_time_val}`
      const dateObj = new Date(dateTimeStr)
      payload.scheduled_time = Math.floor(dateObj.getTime() / 1000)
    }

    await axios.post("/api/v1/senler/broadcasts", payload)
    showMessage("Рассылка успешно запланирована/отправлена")
    broadcastDialog.value = false
    await loadStatsAndDeliveries()
  } catch (e) {
    const errorMsg = e.response?.data?.detail || "Не удалось отправить рассылку"
    showMessage(errorMsg, "error")
  } finally {
    sendingBroadcast.value = false
  }
}

const formatUnixTime = (timestamp) => {
  if (!timestamp) return "-"
  const date = new Date(timestamp * 1000)
  return date.toLocaleString("ru-RU")
}

const formatIsoTime = (isoString) => {
  if (!isoString) return "-"
  const date = new Date(isoString)
  return date.toLocaleString("ru-RU")
}

const getDeliveryStatusColor = (status) => {
  // В Senler: 1 - черновик, 2 - в очереди, 3 - отправлено
  if (status === 3) return "success"
  if (status === 2) return "warning"
  return "secondary"
}

const getDeliveryStatusText = (status) => {
  if (status === 3) return "Отправлено"
  if (status === 2) return "В очереди"
  return "Черновик"
}

// Наблюдение за вкладками
watch(tab, (newTab) => {
  if (newTab === "stats") {
    loadStatsAndDeliveries()
  } else if (newTab === "subscribers") {
    loadSubscribers()
    loadSenlerGroups()
  }
})

// Наблюдение за фильтрами подписчиков
watch([page, size, filterGroupId, filterSubscribed], () => {
  if (tab.value === "subscribers") {
    loadSubscribers()
  }
})

// Поиск с задержкой (Debounce)
let searchTimeout = null
watch(search, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    page.value = 1
    loadSubscribers()
  }, 500)
})

onMounted(() => {
  loadSettings()
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <div class="d-flex align-center justify-between mb-4">
        <h1 class="text-h4 font-weight-bold">Интеграция с Senler</h1>
      </div>
      
      <!-- Вкладки управления -->
      <VTabs v-model="tab" color="primary" class="mb-4">
        <VTab value="settings" prepend-icon="ri-settings-4-line">Настройки</VTab>
        <VTab value="stats" prepend-icon="ri-bar-chart-box-line">Статистика и Рассылки</VTab>
        <VTab value="subscribers" prepend-icon="ri-group-line">База подписчиков</VTab>
      </VTabs>

      <VWindow v-model="tab">
        <!-- 1. ВКЛАДКА НАСТРОЕК -->
        <VWindowItem value="settings">
          <VRow>
            <VCol cols="12" md="8">
              <VCard title="Параметры интеграции" subtitle="Подключение к API сервиса Senler и настройка Webhook">
                <VCardText>
                  <VForm @submit.prevent="saveSettings">
                    <VRow>
                      <VCol cols="12">
                        <VSwitch
                          v-model="settings.is_active"
                          label="Интеграция активна"
                          color="success"
                          hide-details
                          class="mb-4"
                        />
                      </VCol>
                      
                      <VCol cols="12" md="6">
                        <VTextField
                          v-model="settings.access_token"
                          label="API Access Token"
                          placeholder="Введите API токен Senler"
                          type="password"
                          hint="Токен получается в кабинете Senler: Настройки -> Работа с API"
                          persistent-hint
                        />
                      </VCol>
                      
                      <VCol cols="12" md="6">
                        <VTextField
                          v-model="settings.group_id"
                          label="Senler Group ID (Идентификатор сообщества)"
                          placeholder="Например, 318747"
                          type="number"
                          hint="Идентификатор сообщества в самом сервисе Senler"
                          persistent-hint
                        />
                      </VCol>

                      <VCol cols="12" md="6">
                        <VTextField
                          v-model="settings.vk_group_id"
                          label="VK Group ID (Оригинальный ID группы ВК)"
                          placeholder="Например, 12345678"
                          type="number"
                          hint="Для связывания подписчиков с основным ботом ВК"
                          persistent-hint
                        />
                      </VCol>

                      <VCol cols="12" md="6">
                        <VTextField
                          v-model="settings.secret_key"
                          label="Секретный ключ вебхука (любая строка)"
                          placeholder="Введите секретный ключ для защиты"
                          hint="Используется для проверки подлинности входящих вебхуков от Senler"
                          persistent-hint
                        />
                      </VCol>

                      <VCol cols="12" class="d-flex gap-3 mt-4">
                        <VBtn
                          type="submit"
                          color="primary"
                          :loading="saving"
                        >
                          Сохранить настройки
                        </VBtn>
                        
                        <VBtn
                          variant="tonal"
                          color="info"
                          :loading="testing"
                          @click="testConnection"
                        >
                          Проверить подключение
                        </VBtn>
                      </VCol>
                    </VRow>
                  </VForm>
                </VCardText>
              </VCard>
            </VCol>

            <VCol cols="12" md="4">
              <VCard title="Настройка Webhook" class="h-100">
                <VCardText>
                  <p class="text-body-2 mb-4">
                    Для того чтобы новые подписки и отписки импортировались в базу данных сайта мгновенно в реальном времени, настройте Webhook в личном кабинете Senler.
                  </p>
                  
                  <h4 class="text-subtitle-2 font-weight-bold mb-1">Инструкция:</h4>
                  <ol class="text-caption mb-4 pl-4">
                    <li>Перейдите в кабинет Senler вашего сообщества.</li>
                    <li>Откройте раздел <strong>Настройки</strong> -> <strong>Webhook API</strong>.</li>
                    <li>Нажмите <strong>Добавить сервер</strong>.</li>
                    <li>Скопируйте URL адрес из поля ниже и вставьте его.</li>
                    <li>Выберите события подписки (subscribe) и отписки (unsubscribe).</li>
                    <li>Сохраните изменения.</li>
                  </ol>

                  <VTextField
                    :model-value="getWebhookUrl()"
                    label="URL Webhook для Senler"
                    readonly
                    append-inner-icon="ri-file-copy-line"
                    @click:append-inner="() => { navigator.clipboard.writeText(getWebhookUrl()); showMessage('Ссылка скопирована в буфер обмена') }"
                    class="bg-grey-lighten-4"
                  />
                </VCardText>
              </VCard>
            </VCol>
          </VRow>
        </VWindowItem>

        <!-- 2. ВКЛАДКА СТАТИСТИКИ И РАССЫЛОК -->
        <VWindowItem value="stats">
          <!-- Карточки статистики -->
          <VRow class="mb-4">
            <VCol cols="12" sm="4">
              <VCard class="bg-primary text-white">
                <VCardText class="d-flex align-center justify-space-between">
                  <div>
                    <div class="text-h6 opacity-80">Всего подписчиков (БД)</div>
                    <div class="text-h3 font-weight-bold">{{ stats.total_subscribers }}</div>
                  </div>
                  <VIcon size="48" icon="ri-group-line" class="opacity-30" />
                </VCardText>
              </VCard>
            </VCol>

            <VCol cols="12" sm="4">
              <VCard class="bg-success text-white">
                <VCardText class="d-flex align-center justify-space-between">
                  <div>
                    <div class="text-h6 opacity-80">Активные подписчики</div>
                    <div class="text-h3 font-weight-bold">{{ stats.active_subscribers }}</div>
                  </div>
                  <VIcon size="48" icon="ri-checkbox-circle-line" class="opacity-30" />
                </VCardText>
              </VCard>
            </VCol>

            <VCol cols="12" sm="4">
              <VCard class="bg-info text-white">
                <VCardText class="d-flex align-center justify-space-between">
                  <div>
                    <div class="text-h6 opacity-80">Рассылок в Senler</div>
                    <div class="text-h3 font-weight-bold">{{ stats.deliveries?.length || 0 }}</div>
                  </div>
                  <VIcon size="48" icon="ri-mail-send-line" class="opacity-30" />
                </VCardText>
              </VCard>
            </VCol>
          </VRow>

          <!-- Список рассылок -->
          <VCard>
            <VCardItem>
              <VCardTitle>Рассылки сообщества ВК через Senler</VCardTitle>
              <template #append>
                <VBtn
                  prepend-icon="ri-add-line"
                  color="primary"
                  @click="openBroadcastDialog"
                >
                  Создать рассылку
                </VBtn>
              </template>
            </VCardItem>

            <VCardText>
              <VDataTable
                :headers="[
                  { title: 'Название', key: 'name' },
                  { title: 'Статус', key: 'status' },
                  { title: 'Дата создания', key: 'date' },
                  { title: 'Отправлено', key: 'sent', align: 'center' },
                  { title: 'Доставлено', key: 'delivered', align: 'center' },
                  { title: 'Прочитано', key: 'read', align: 'center' },
                  { title: 'Переходы', key: 'away', align: 'center' }
                ]"
                :items="stats.deliveries"
                :loading="loadingStats"
                no-data-text="Рассылки еще не созданы или API Senler недоступно"
              >
                <template #item.status="{ item }">
                  <VChip
                    :color="getDeliveryStatusColor(item.status)"
                    size="small"
                    label
                  >
                    {{ getDeliveryStatusText(item.status) }}
                  </VChip>
                </template>

                <template #item.date="{ item }">
                  {{ formatUnixTime(item.date) }}
                </template>
              </VDataTable>
            </VCardText>
          </VCard>
        </VWindowItem>

        <!-- 3. ВКЛАДКА ПОДПИСЧИКОВ -->
        <VWindowItem value="subscribers">
          <VCard>
            <VCardText>
              <!-- Фильтры и поиск -->
              <VRow class="mb-4" align="center">
                <VCol cols="12" md="4">
                  <VTextField
                    v-model="search"
                    prepend-inner-icon="ri-search-line"
                    label="Поиск по имени или VK ID"
                    clearable
                    hide-details
                  />
                </VCol>

                <VCol cols="12" sm="6" md="3">
                  <VSelect
                    v-model="filterGroupId"
                    :items="senlerGroups"
                    item-title="name"
                    item-value="subscription_id"
                    label="Группа подписки Senler"
                    clearable
                    hide-details
                  />
                </VCol>

                <VCol cols="12" sm="6" md="2">
                  <VSelect
                    v-model="filterSubscribed"
                    :items="[
                      { title: 'Все', value: null },
                      { title: 'Подписан', value: true },
                      { title: 'Отписан', value: false }
                    ]"
                    item-title="title"
                    item-value="value"
                    label="Статус"
                    hide-details
                  />
                </VCol>

                <VCol cols="12" md="3" class="d-flex justify-end gap-2">
                  <VBtn
                    color="info"
                    variant="tonal"
                    prepend-icon="ri-refresh-line"
                    :loading="syncing"
                    @click="triggerSync"
                  >
                    Синхронизировать
                  </VBtn>
                </VCol>
              </VRow>

              <!-- Таблица подписчиков -->
              <VDataTableServer
                v-model:items-per-page="size"
                v-model:page="page"
                :headers="[
                  { title: 'VK ID / Подписчик', key: 'vk_user_id' },
                  { title: 'Статус', key: 'is_subscribed' },
                  { title: 'Дата подписки', key: 'subscribe_date' },
                  { title: 'UTM метки', key: 'utm_tags' },
                  { title: 'Связанный клиент', key: 'customer_name' }
                ]"
                :items="subscribers"
                :items-length="totalSubscribers"
                :loading="loadingSubscribers"
                no-data-text="Подписчики не найдены. Нажмите «Синхронизировать», чтобы выгрузить подписчиков из Senler."
              >
                <template #item.vk_user_id="{ item }">
                  <div class="d-flex align-center gap-2 py-1">
                    <span class="font-weight-medium">{{ item.first_name }} {{ item.last_name }}</span>
                    <a
                      :href="`https://vk.com/id${item.vk_user_id}`"
                      target="_blank"
                      class="text-caption text-primary"
                    >
                      (vk.com/id{{ item.vk_user_id }})
                    </a>
                  </div>
                </template>

                <template #item.is_subscribed="{ item }">
                  <VChip
                    :color="item.is_subscribed ? 'success' : 'error'"
                    size="small"
                    label
                  >
                    {{ item.is_subscribed ? 'Подписан' : 'Отписан' }}
                  </VChip>
                </template>

                <template #item.subscribe_date="{ item }">
                  {{ formatIsoTime(item.subscribe_date) }}
                </template>

                <template #item.utm_tags="{ item }">
                  <div v-if="item.utm_tags && Object.keys(item.utm_tags).length > 0">
                    <div v-for="(v, k) in item.utm_tags" :key="k" class="text-caption">
                      <strong>{{ k }}</strong>: {{ v }}
                    </div>
                  </div>
                  <span v-else class="text-grey-lighten-1 italic">-</span>
                </template>

                <template #item.customer_name="{ item }">
                  <div v-if="item.customer_id">
                    <router-link
                      :to="`/clients?id=${item.customer_id}`"
                      class="font-weight-medium text-decoration-none text-primary"
                    >
                      {{ item.customer_name }}
                    </router-link>
                    <div class="text-caption text-grey">{{ item.customer_phone }}</div>
                  </div>
                  <span v-else class="text-caption text-grey-lighten-1">Не связан</span>
                </template>
              </VDataTableServer>
            </VCardText>
          </VCard>
        </VWindowItem>
      </VWindow>
    </VCol>

    <!-- Диалог создания рассылки -->
    <VDialog v-model="broadcastDialog" max-width="700px">
      <VCard title="Создать рассылку ВКонтакте через Senler">
        <VCardText>
          <VForm @submit.prevent="sendBroadcast">
            <VRow>
              <VCol cols="12">
                <VTextField
                  v-model="broadcastForm.name"
                  label="Название рассылки"
                  placeholder="Например, Акция выходного дня 15%"
                  required
                />
              </VCol>
              
              <VCol cols="12">
                <VSelect
                  v-model="broadcastForm.subscription_id"
                  :items="[{ subscription_id: 0, name: 'Все подписчики (без конкретной группы)' }, ...senlerGroups]"
                  item-title="name"
                  item-value="subscription_id"
                  label="Целевая группа подписчиков Senler"
                  required
                />
              </VCol>

              <VCol cols="12">
                <VTextarea
                  v-model="broadcastForm.message"
                  label="Текст сообщения"
                  placeholder="Привет, {first_name}! Только сегодня дарим скидку 15% по промокоду..."
                  hint="Поддерживаются плейсхолдеры Senler: {first_name} - имя, {last_name} - фамилия"
                  persistent-hint
                  rows="5"
                  required
                />
              </VCol>

              <VCol cols="12">
                <VSwitch
                  v-model="broadcastForm.is_now"
                  label="Отправить немедленно"
                  color="primary"
                />
              </VCol>

              <!-- Выбор времени, если отложено -->
              <template v-if="!broadcastForm.is_now">
                <VCol cols="12" sm="6">
                  <VTextField
                    v-model="broadcastForm.scheduled_date_val"
                    label="Дата отправки"
                    type="date"
                    required
                  />
                </VCol>
                <VCol cols="12" sm="6">
                  <VTextField
                    v-model="broadcastForm.scheduled_time_val"
                    label="Время отправки"
                    type="time"
                    required
                  />
                </VCol>
              </template>
            </VRow>
          </VForm>
        </VCardText>
        
        <VCardActions>
          <VSpacer />
          <VBtn
            variant="tonal"
            color="secondary"
            @click="broadcastDialog = false"
          >
            Отмена
          </VBtn>
          <VBtn
            color="primary"
            :loading="sendingBroadcast"
            :disabled="!broadcastForm.name || !broadcastForm.message"
            @click="sendBroadcast"
          >
            Запустить рассылку
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <VSnackbar v-model="snackbar" :color="snackbarColor" :timeout="3000">
      {{ snackbarText }}
    </VSnackbar>
  </VRow>
</template>
