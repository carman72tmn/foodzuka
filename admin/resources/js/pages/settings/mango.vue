<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { getAuthHeaders } from '@/utils/auth'
import '@styles/mango.css'

// Вкладки
const activeTab = ref('settings')

// Настройки
const settings = ref({
  id: null,
  vpbx_api_key: '',
  vpbx_api_salt: '',
  vpbx_url: 'https://app.mango-office.ru/vpbx/',
  is_active: false,
  default_extension: '',
  auto_lookup_customer: true,
  create_customer_if_missing: false,
  notify_incoming_call: true,
  recording_storage_mode: 'stream',
  webhook_url: 'https://vezuroll.ru/api/v1/mango/webhook',
})

// UI состояния
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const isApiKeyVisible = ref(false)
const isApiSaltVisible = ref(false)

// Уведомления (Snackbar)
const snackbar = ref({
  show: false,
  text: '',
  color: 'success',
})

const showMessage = (text, color = 'success') => {
  snackbar.value.text = text
  snackbar.value.color = color
  snackbar.value.show = true
}

// Диалог проверки подключения
const testDialog = ref({
  show: false,
  success: false,
  title: '',
  message: '',
  usersCount: 0,
  usersSample: [],
})

// Журнал звонков
const calls = ref([])
const callsLoading = ref(false)
const callsTotal = ref(0)
const callsPage = ref(1)
const callsLimit = ref(15)
const callsFilter = ref({
  direction: null,
  status: null,
  search: '',
  date_from: '',
  date_to: '',
})

// Инструменты: Click-to-Call
const c2cForm = ref({
  from_extension: '',
  to_number: '+79220079019',
  line_number: '',
  loading: false,
})

// Инструменты: SMS
const smsForm = ref({
  to_number: '+79220079019',
  text: 'Здравствуйте! Ваш заказ принят.',
  sender: '',
  from_extension: '',
  loading: false,
})

// Инструменты: Справочник сотрудников
const vatsUsers = ref([])
const vatsUsersLoading = ref(false)

// Инструменты: Эмулятор Webhook
const emuForm = ref({
  caller_phone: '+79220079019',
  extension: '101',
  line_number: '73452000000',
  call_state: 'Appeared',
  loading: false,
})

// --- Загрузка и Сохранение Настроек ---

const fetchSettings = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/settings/mango', {
      headers: getAuthHeaders(),
    })
    if (res.data) {
      settings.value = {
        ...settings.value,
        ...res.data,
      }
      if (settings.value.default_extension && !c2cForm.value.from_extension) {
        c2cForm.value.from_extension = settings.value.default_extension
      }
    }
  } catch (err) {
    console.error('Ошибка загрузки настроек Mango:', err)
    showMessage('Не удалось загрузить настройки', 'error')
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    const res = await axios.post('/api/v1/settings/mango', settings.value, {
      headers: getAuthHeaders(),
    })
    settings.value = {
      ...settings.value,
      ...res.data,
    }
    showMessage('Настройки телефонии Mango успешно сохранены!')
  } catch (err) {
    const errorMsg = err.response?.data?.detail || 'Ошибка сохранения настроек'
    showMessage(errorMsg, 'error')
  } finally {
    saving.value = false
  }
}

// Тест подключения
const testConnection = async () => {
  if (!settings.value.vpbx_api_key || !settings.value.vpbx_api_salt) {
    showMessage('Укажите API Key и API Salt перед проверкой', 'warning')
    return
  }

  testing.value = true
  try {
    const res = await axios.post(
      '/api/v1/settings/mango/test-connection',
      {
        vpbx_api_key: settings.value.vpbx_api_key,
        vpbx_api_salt: settings.value.vpbx_api_salt,
        vpbx_url: settings.value.vpbx_url,
      },
      { headers: getAuthHeaders() },
    )

    const data = res.data
    testDialog.value.success = data.success
    testDialog.value.title = data.success ? 'Связь с Mango Office установлена!' : 'Ошибка подключения к Mango Office'
    testDialog.value.message = data.message || ''
    testDialog.value.usersCount = data.users_count || 0
    testDialog.value.usersSample = data.users_sample || []
    testDialog.value.show = true
  } catch (err) {
    const errorMsg = err.response?.data?.detail || 'Ошибка при тестировании подключения'
    showMessage(errorMsg, 'error')
  } finally {
    testing.value = false
  }
}

// Копирование Webhook URL
const copyWebhookUrl = () => {
  navigator.clipboard.writeText(settings.value.webhook_url)
  showMessage('URL для Webhook скопирован в буфер обмена!')
}

// --- Журнал звонков ---

const fetchCalls = async () => {
  callsLoading.value = true
  try {
    const params = {
      page: callsPage.value,
      limit: callsLimit.value,
    }
    if (callsFilter.value.direction) params.direction = callsFilter.value.direction
    if (callsFilter.value.status) params.status = callsFilter.value.status
    if (callsFilter.value.search) params.search = callsFilter.value.search
    if (callsFilter.value.date_from) params.date_from = callsFilter.value.date_from
    if (callsFilter.value.date_to) params.date_to = callsFilter.value.date_to

    const res = await axios.get('/api/v1/mango/calls', {
      params,
      headers: getAuthHeaders(),
    })
    calls.value = res.data.items || []
    callsTotal.value = res.data.total || 0
  } catch (err) {
    console.error('Ошибка загрузки журнала звонков:', err)
  } finally {
    callsLoading.value = false
  }
}

const resetCallsFilter = () => {
  callsFilter.value = {
    direction: null,
    status: null,
    search: '',
    date_from: '',
    date_to: '',
  }
  callsPage.value = 1
  fetchCalls()
}

// Быстрый перезвон из журнала
const quickCall = call => {
  const targetNumber = call.direction === 'incoming' ? call.from_number : call.to_number
  c2cForm.value.to_number = targetNumber
  activeTab.value = 'tools'
  showMessage(`Номер ${targetNumber} подставлен в форму звонка. Нажмите «Позвонить».`, 'info')
}

// --- Инструменты ---

// Click-to-Call
const executeCallback = async () => {
  if (!c2cForm.value.from_extension || !c2cForm.value.to_number) {
    showMessage('Укажите внутренний добавочный номер и телефон абонента', 'warning')
    return
  }

  c2cForm.value.loading = true
  try {
    const res = await axios.post(
      '/api/v1/mango/commands/callback',
      {
        from_extension: c2cForm.value.from_extension,
        to_number: c2cForm.value.to_number,
        line_number: c2cForm.value.line_number || null,
      },
      { headers: getAuthHeaders() },
    )
    showMessage('Звонок инициирован! Ожидайте вызова на аппарате сотрудника.')
  } catch (err) {
    const msg = err.response?.data?.detail || 'Не удалось совершить вызов'
    showMessage(msg, 'error')
  } finally {
    c2cForm.value.loading = false
  }
}

// Отправка SMS
const sendSms = async () => {
  if (!smsForm.value.to_number || !smsForm.value.text) {
    showMessage('Заполните номер телефона и текст SMS', 'warning')
    return
  }

  smsForm.value.loading = true
  try {
    await axios.post(
      '/api/v1/mango/commands/sms',
      {
        to_number: smsForm.value.to_number,
        text: smsForm.value.text,
        sender: smsForm.value.sender || null,
        from_extension: smsForm.value.from_extension || null,
      },
      { headers: getAuthHeaders() },
    )
    showMessage('SMS успешно отправлено через Mango Office!')
  } catch (err) {
    const msg = err.response?.data?.detail || 'Не удалось отправить SMS'
    showMessage(msg, 'error')
  } finally {
    smsForm.value.loading = false
  }
}

// Загрузка справочника сотрудников ВАТС
const fetchVatsUsers = async () => {
  vatsUsersLoading.value = true
  try {
    const res = await axios.get('/api/v1/mango/users', {
      headers: getAuthHeaders(),
    })
    vatsUsers.value = res.data.users || []
    showMessage(`Загружено сотрудников/линий ВАТС: ${vatsUsers.value.length}`)
  } catch (err) {
    const msg = err.response?.data?.detail || 'Не удалось загрузить сотрудников'
    showMessage(msg, 'error')
  } finally {
    vatsUsersLoading.value = false
  }
}

// Эмуляция вебхука
const triggerWebhookEmulator = async () => {
  emuForm.value.loading = true
  try {
    await axios.post('/api/v1/mango/test-webhook-emulator', emuForm.value, {
      headers: getAuthHeaders(),
    })
    showMessage('Тестовое событие звонка успешно смоделировано! Проверьте журнал.')
    fetchCalls()
  } catch (err) {
    showMessage('Ошибка эмуляции вебхука', 'error')
  } finally {
    emuForm.value.loading = false
  }
}

// Форматирование даты
const formatDate = str => {
  if (!str) return '-'
  try {
    const d = new Date(str)
    return d.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch (e) {
    return str
  }
}

// Форматирование секунд
const formatDuration = sec => {
  if (!sec || sec <= 0) return '0 сек.'
  const m = Math.floor(sec / 60)
  const s = sec % 60
  if (m > 0) return `${m} мин. ${s} сек.`
  return `${s} сек.`
}

onMounted(() => {
  fetchSettings()
  fetchCalls()
})
</script>

<template>
  <div class="mango-settings-container">
    <!-- Верхняя панель заголовка -->
    <div class="d-flex flex-wrap align-center justify-space-between gap-4 mb-6">
      <div>
        <h2 class="text-h4 font-weight-bold d-flex align-center gap-2">
          <VIcon icon="bx-phone-call" color="primary" size="36" />
          Интеграция с Mango Office
        </h2>
        <p class="text-subtitle-1 text-medium-emphasis mb-0">
          Связка с Виртуальной АТС (ВАТС): телефония, уведомления о звонках, история, записи и Click-to-Call
        </p>
      </div>

      <div class="d-flex align-center gap-3">
        <VChip
          :color="settings.is_active ? 'success' : 'default'"
          variant="tonal"
          size="large"
          class="font-weight-medium"
        >
          <VIcon :icon="settings.is_active ? 'bx-check-circle' : 'bx-power-off'" start />
          {{ settings.is_active ? 'Интеграция активна' : 'Интеграция выключена' }}
        </VChip>

        <VBtn
          color="info"
          variant="outlined"
          :loading="testing"
          @click="testConnection"
        >
          <VIcon icon="bx-wifi" start />
          Проверить подключение
        </VBtn>

        <VBtn
          color="primary"
          :loading="saving"
          @click="saveSettings"
        >
          <VIcon icon="bx-save" start />
          Сохранить
        </VBtn>
      </div>
    </div>

    <!-- Вкладки управления -->
    <VCard elevation="1" class="mb-6">
      <VTabs v-model="activeTab" color="primary" grow>
        <VTab value="settings">
          <VIcon icon="bx-cog" start />
          Настройки подключения
        </VTab>
        <VTab value="calls" @click="fetchCalls">
          <VIcon icon="bx-history" start />
          Журнал вызовов
          <VBadge
            v-if="callsTotal > 0"
            :content="callsTotal"
            color="primary"
            class="ms-2"
          />
        </VTab>
        <VTab value="tools">
          <VIcon icon="bx-wrench" start />
          Инструменты и API
        </VTab>
        <VTab value="instructions">
          <VIcon icon="bx-book-open" start />
          Инструкции и Документация
        </VTab>
      </VTabs>
    </VCard>

    <!-- Содержимое вкладок -->
    <VWindow v-model="activeTab">
      <!-- 1. Настройки подключения -->
      <VWindowItem value="settings">
        <VRow>
          <!-- Левая колонка: Ключи и реквизиты -->
          <VCol cols="12" md="7">
            <VCard elevation="1" class="mb-6">
              <VCardItem>
                <VCardTitle class="d-flex align-center gap-2">
                  <VIcon icon="bx-key" color="primary" />
                  Реквизиты доступа к API ВАТС
                </VCardTitle>
                <VCardSubtitle>
                  Данные ключи формируются в личном кабинете Mango Office в разделе «Интеграции -> API»
                </VCardSubtitle>
              </VCardItem>

              <VDivider />

              <VCardText>
                <!-- Тумблер активности -->
                <div class="d-flex align-center justify-space-between p-3 rounded mb-4 bg-var-theme-background">
                  <div>
                    <div class="font-weight-bold">Активность интеграции</div>
                    <div class="text-caption text-medium-emphasis">
                      Включите для обработки входящих звонков и совершения вызовов
                    </div>
                  </div>
                  <VSwitch
                    v-model="settings.is_active"
                    color="success"
                    hide-details
                    inset
                  />
                </div>

                <!-- API Key -->
                <VTextField
                  v-model="settings.vpbx_api_key"
                  label="Уникальный код АТС (vpbx_api_key)"
                  placeholder="Например: vpbx_1234567890abcdef"
                  class="mb-4"
                  :type="isApiKeyVisible ? 'text' : 'password'"
                  :append-inner-icon="isApiKeyVisible ? 'bx-hide' : 'bx-show'"
                  @click:append-inner="isApiKeyVisible = !isApiKeyVisible"
                  hint="Уникальный ключ идентификации вашей виртуальной АТС в Mango"
                  persistent-hint
                />

                <!-- API Salt -->
                <VTextField
                  v-model="settings.vpbx_api_salt"
                  label="Ключ для создания подписи (vpbx_api_salt)"
                  placeholder="Секретный ключ подписи SHA-256"
                  class="mb-4"
                  :type="isApiSaltVisible ? 'text' : 'password'"
                  :append-inner-icon="isApiSaltVisible ? 'bx-hide' : 'bx-show'"
                  @click:append-inner="isApiSaltVisible = !isApiSaltVisible"
                  hint="Секретная строка для подписи каждого запроса и валидации входящих вебхуков"
                  persistent-hint
                />

                <!-- API URL -->
                <VTextField
                  v-model="settings.vpbx_url"
                  label="Базовый адрес API шлюза (vpbx_url)"
                  placeholder="https://app.mango-office.ru/vpbx/"
                  class="mb-4"
                  hint="Стандартный шлюз API Mango Office"
                  persistent-hint
                />

                <!-- Внутренний номер по умолчанию -->
                <VTextField
                  v-model="settings.default_extension"
                  label="Добавочный номер сотрудника по умолчанию"
                  placeholder="Например: 101"
                  hint="Используется для быстрого набора Click-to-Call операторами"
                  persistent-hint
                />
              </VCardText>
            </VCard>
          </VCol>

          <!-- Правая колонка: Webhook и опции -->
          <VCol cols="12" md="5">
            <!-- Блок Webhook -->
            <VCard elevation="1" class="mb-6">
              <VCardItem>
                <VCardTitle class="d-flex align-center gap-2">
                  <VIcon icon="bx-broadcast" color="info" />
                  Адрес для Webhook (ВАТС)
                </VCardTitle>
                <VCardSubtitle>
                  Скопируйте этот URL и укажите его в ЛК Mango в настройках уведомлений
                </VCardSubtitle>
              </VCardItem>

              <VDivider />

              <VCardText>
                <div class="mango-webhook-box mb-4">
                  <span class="mango-webhook-url">{{ settings.webhook_url }}</span>
                  <VBtn
                    icon="bx-copy"
                    variant="text"
                    color="primary"
                    size="small"
                    @click="copyWebhookUrl"
                  />
                </div>

                <p class="text-caption text-medium-emphasis mb-0">
                  Виртуальная АТС Mango Office отправляет на этот URL данные о вызовах в реальном времени (поступление звонка, ответ оператора, завершение, ссылка на аудиозапись).
                </p>
              </VCardText>
            </VCard>

            <!-- Опции обработки звонков -->
            <VCard elevation="1">
              <VCardItem>
                <VCardTitle class="d-flex align-center gap-2">
                  <VIcon icon="bx-slider-alt" color="primary" />
                  Параметры телефонии
                </VCardTitle>
              </VCardItem>

              <VDivider />

              <VCardText class="d-flex flex-column gap-3">
                <VCheckbox
                  v-model="settings.auto_lookup_customer"
                  label="Авто-поиск гостя по номеру входящего звонка"
                  hint="При звонке система моментально сопоставляет номер с таблицей клиентов"
                  persistent-hint
                />

                <VCheckbox
                  v-model="settings.notify_incoming_call"
                  label="Всплывающее оповещение о звонке в админке"
                  hint="Показывать оператору имя звонящего клиента в колокольчике"
                  persistent-hint
                />

                <VCheckbox
                  v-model="settings.create_customer_if_missing"
                  label="Создавать нового клиента при звонке с незнакомого номера"
                  hint="Если включено, новый гость автоматически заносится в базу"
                  persistent-hint
                />
              </VCardText>
            </VCard>
          </VCol>
        </VRow>
      </VWindowItem>

      <!-- 2. Журнал вызовов -->
      <VWindowItem value="calls">
        <!-- Панель фильтров -->
        <VCard elevation="1" class="mb-4">
          <VCardText>
            <VRow dense align="center">
              <VCol cols="12" sm="6" md="3">
                <VTextField
                  v-model="callsFilter.search"
                  label="Поиск по телефону или имени"
                  prepend-inner-icon="bx-search"
                  hide-details
                  density="compact"
                  clearable
                  @keyup.enter="fetchCalls"
                />
              </VCol>

              <VCol cols="12" sm="6" md="2">
                <VSelect
                  v-model="callsFilter.direction"
                  :items="[
                    { title: 'Все направления', value: null },
                    { title: 'Входящие 📥', value: 'incoming' },
                    { title: 'Исходящие 📤', value: 'outgoing' }
                  ]"
                  label="Направление"
                  hide-details
                  density="compact"
                  @update:model-value="fetchCalls"
                />
              </VCol>

              <VCol cols="12" sm="6" md="2">
                <VSelect
                  v-model="callsFilter.status"
                  :items="[
                    { title: 'Все статусы', value: null },
                    { title: 'Отвечен 🟢', value: 'success' },
                    { title: 'Пропущен 🔴', value: 'missed' },
                    { title: 'В процессе 🔵', value: 'active' }
                  ]"
                  label="Статус"
                  hide-details
                  density="compact"
                  @update:model-value="fetchCalls"
                />
              </VCol>

              <VCol cols="12" sm="6" md="2">
                <VTextField
                  v-model="callsFilter.date_from"
                  type="date"
                  label="Дата с"
                  hide-details
                  density="compact"
                />
              </VCol>

              <VCol cols="12" sm="6" md="2">
                <VTextField
                  v-model="callsFilter.date_to"
                  type="date"
                  label="Дата по"
                  hide-details
                  density="compact"
                />
              </VCol>

              <VCol cols="12" md="1" class="d-flex gap-1 justify-end">
                <VBtn
                  icon="bx-filter-alt"
                  color="primary"
                  size="small"
                  @click="fetchCalls"
                />
                <VBtn
                  icon="bx-reset"
                  variant="outlined"
                  size="small"
                  @click="resetCallsFilter"
                />
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Таблица звонков -->
        <VCard elevation="1">
          <VTable class="mango-call-table">
            <thead>
              <tr>
                <th>ДАТА / ВРЕМЯ</th>
                <th>НАПРАВЛЕНИЕ</th>
                <th>НОМЕР ТЕЛЕФОНА</th>
                <th>ГОСТЬ (КЛИЕНТ)</th>
                <th>ЛИНИЯ / ДОБАВОЧНЫЙ</th>
                <th>СТАТУС</th>
                <th>РАЗГОВОР</th>
                <th>ЗАПИСЬ РАЗГОВОРА</th>
                <th class="text-end">ДЕЙСТВИЯ</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="callsLoading">
                <td colspan="9" class="text-center py-6">
                  <VProgressCircular indeterminate color="primary" />
                  <div class="text-caption mt-2">Загрузка истории вызовов...</div>
                </td>
              </tr>

              <tr v-else-if="calls.length === 0">
                <td colspan="9" class="text-center py-6 text-medium-emphasis">
                  <VIcon icon="bx-phone-off" size="40" class="mb-2" />
                  <div>Записи звонков не найдены</div>
                </td>
              </tr>

              <tr v-for="call in calls" :key="call.id">
                <!-- Дата -->
                <td class="text-no-wrap font-weight-medium">
                  {{ formatDate(call.started_at || call.created_at) }}
                </td>

                <!-- Направление -->
                <td>
                  <span
                    class="mango-call-direction"
                    :class="call.direction === 'incoming' ? 'mango-call-incoming' : 'mango-call-outgoing'"
                  >
                    <VIcon :icon="call.direction === 'incoming' ? 'bx-phone-incoming' : 'bx-phone-outgoing'" size="18" />
                    {{ call.direction === 'incoming' ? 'Входящий' : 'Исходящий' }}
                  </span>
                </td>

                <!-- Телефон -->
                <td class="font-weight-bold text-no-wrap">
                  {{ call.direction === 'incoming' ? call.from_number : call.to_number }}
                </td>

                <!-- Гость -->
                <td>
                  <template v-if="call.customer_name">
                    <RouterLink
                      v-if="call.customer_id"
                      :to="`/clients?search=${call.direction === 'incoming' ? call.from_number : call.to_number}`"
                      class="text-primary font-weight-medium text-decoration-none"
                    >
                      <VIcon icon="bx-user" size="16" start />
                      {{ call.customer_name }}
                    </RouterLink>
                    <span v-else>{{ call.customer_name }}</span>
                  </template>
                  <span v-else class="text-medium-emphasis">-</span>
                </td>

                <!-- Линия / Добавочный -->
                <td>
                  <div v-if="call.to_extension || call.from_extension" class="font-weight-medium">
                    Добавочный: {{ call.to_extension || call.from_extension }}
                  </div>
                  <div v-if="call.line_number" class="text-caption text-medium-emphasis">
                    Линия: {{ call.line_number }}
                  </div>
                </td>

                <!-- Статус -->
                <td>
                  <VChip
                    v-if="call.status === 'success'"
                    class="mango-badge-success"
                    size="small"
                  >
                    Отвечен
                  </VChip>
                  <VChip
                    v-else-if="call.status === 'missed'"
                    class="mango-badge-missed"
                    size="small"
                  >
                    Пропущен
                  </VChip>
                  <VChip
                    v-else-if="call.status === 'busy'"
                    class="mango-badge-busy"
                    size="small"
                  >
                    Занято
                  </VChip>
                  <VChip
                    v-else
                    class="mango-badge-active"
                    size="small"
                  >
                    В процессе
                  </VChip>
                </td>

                <!-- Длительность -->
                <td class="text-no-wrap">
                  <div>{{ formatDuration(call.duration_talk) }}</div>
                  <div v-if="call.duration_wait > 0" class="text-caption text-medium-emphasis">
                    ожидание {{ call.duration_wait }} сек.
                  </div>
                </td>

                <!-- Запись разговора -->
                <td>
                  <div v-if="call.recording_id" class="mango-audio-player">
                    <audio controls preload="none">
                      <source :src="`/api/v1/mango/recordings/${call.recording_id}/stream?action=play`" type="audio/mpeg" />
                      Ваш браузер не поддерживает воспроизведение звука.
                    </audio>
                    <VBtn
                      icon="bx-download"
                      size="x-small"
                      variant="text"
                      color="primary"
                      :href="`/api/v1/mango/recordings/${call.recording_id}/stream?action=download`"
                      target="_blank"
                      title="Скачать MP3"
                    />
                  </div>
                  <span v-else class="text-caption text-medium-emphasis">Нет записи</span>
                </td>

                <!-- Действия -->
                <td class="text-end text-no-wrap">
                  <VBtn
                    icon="bx-phone-call"
                    size="small"
                    variant="tonal"
                    color="success"
                    title="Перезвонить клиенту в 1 клик"
                    @click="quickCall(call)"
                  />
                </td>
              </tr>
            </tbody>
          </VTable>

          <!-- Пагинация -->
          <VDivider />
          <div class="d-flex justify-space-between align-center p-4">
            <span class="text-caption text-medium-emphasis">
              Всего вызовов в базе: {{ callsTotal }}
            </span>
            <VPagination
              v-model="callsPage"
              :length="Math.ceil(callsTotal / callsLimit) || 1"
              :total-visible="5"
              density="compact"
              @update:model-value="fetchCalls"
            />
          </div>
        </VCard>
      </VWindowItem>

      <!-- 3. Инструменты и Тестирование API -->
      <VWindowItem value="tools">
        <VRow>
          <!-- Click-to-Call (Звонок из CRM) -->
          <VCol cols="12" md="6">
            <VCard elevation="1" class="mb-6">
              <VCardItem>
                <VCardTitle class="d-flex align-center gap-2">
                  <VIcon icon="bx-phone-outgoing" color="primary" />
                  Звонок из CRM (Click-to-Call)
                </VCardTitle>
                <VCardSubtitle>
                  Инициирует звонок на внутренний номер оператора и соединяет с клиентом
                </VCardSubtitle>
              </VCardItem>
              <VDivider />
              <VCardText>
                <VTextField
                  v-model="c2cForm.from_extension"
                  label="Внутренний добавочный номер сотрудника"
                  placeholder="101"
                  class="mb-3"
                  hint="Номер SIP/линии, на который поступит первый звонок"
                  persistent-hint
                />
                <VTextField
                  v-model="c2cForm.to_number"
                  label="Номер телефона абонента"
                  placeholder="+79220079019"
                  class="mb-3"
                  hint="Номер клиента для соединения"
                  persistent-hint
                />
                <VTextField
                  v-model="c2cForm.line_number"
                  label="Внешний номер линии (необязательно)"
                  placeholder="73452000000"
                  class="mb-4"
                  hint="Многоканальный номер компании, который отобразится у клиента"
                  persistent-hint
                />
                <VBtn
                  color="primary"
                  block
                  size="large"
                  :loading="c2cForm.loading"
                  @click="executeCallback"
                >
                  <VIcon icon="bx-phone-call" start />
                  Совершить звонок
                </VBtn>
              </VCardText>
            </VCard>

            <!-- Отправка SMS через Mango -->
            <VCard elevation="1">
              <VCardItem>
                <VCardTitle class="d-flex align-center gap-2">
                  <VIcon icon="bx-message-rounded-dots" color="info" />
                  Отправка SMS через Mango
                </VCardTitle>
                <VCardSubtitle>
                  Отправка сервисных SMS-сообщений через шлюз Mango Office
                </VCardSubtitle>
              </VCardItem>
              <VDivider />
              <VCardText>
                <VTextField
                  v-model="smsForm.to_number"
                  label="Номер получателя"
                  placeholder="+79220079019"
                  class="mb-3"
                />
                <VTextarea
                  v-model="smsForm.text"
                  label="Текст SMS"
                  rows="3"
                  class="mb-3"
                />
                <VTextField
                  v-model="smsForm.sender"
                  label="Имя отправителя (Sender / Альфа-номер)"
                  placeholder="Оставьте пустым или укажите согласованное имя"
                  class="mb-4"
                />
                <VBtn
                  color="info"
                  block
                  :loading="smsForm.loading"
                  @click="sendSms"
                >
                  <VIcon icon="bx-send" start />
                  Отправить SMS
                </VBtn>
              </VCardText>
            </VCard>
          </VCol>

          <!-- Правая колонка: Справочник линий и Эмулятор -->
          <VCol cols="12" md="6">
            <!-- Справочник сотрудников ВАТС -->
            <VCard elevation="1" class="mb-6">
              <VCardItem class="d-flex justify-space-between align-center">
                <div>
                  <VCardTitle class="d-flex align-center gap-2">
                    <VIcon icon="bx-user-voice" color="warning" />
                    Линии и сотрудники ВАТС
                  </VCardTitle>
                  <VCardSubtitle>Справочник добавочных номеров Mango Office</VCardSubtitle>
                </div>
                <VBtn
                  size="small"
                  variant="outlined"
                  color="primary"
                  :loading="vatsUsersLoading"
                  @click="fetchVatsUsers"
                >
                  <VIcon icon="bx-refresh" start />
                  Загрузить из Mango
                </VBtn>
              </VCardItem>
              <VDivider />
              <VCardText>
                <VTable v-if="vatsUsers.length > 0" density="compact">
                  <thead>
                    <tr>
                      <th>ДОБАВОЧНЫЙ</th>
                      <th>СОТРУДНИК</th>
                      <th>EMAIL / ТЕЛЕФОН</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="u in vatsUsers" :key="u.extension">
                      <td class="font-weight-bold text-primary">{{ u.extension }}</td>
                      <td>{{ u.name || 'Без имени' }}</td>
                      <td class="text-caption">{{ u.email || u.general_phone || '-' }}</td>
                    </tr>
                  </tbody>
                </VTable>
                <div v-else class="text-center py-6 text-medium-emphasis">
                  Нажмите «Загрузить из Mango», чтобы получить перечень всех сотрудников и внутренних линий из вашей виртуальной АТС.
                </div>
              </VCardText>
            </VCard>

            <!-- Эмулятор входящих вебхуков -->
            <VCard elevation="1">
              <VCardItem>
                <VCardTitle class="d-flex align-center gap-2">
                  <VIcon icon="bx-test-tube" color="secondary" />
                  Эмулятор события Webhook
                </VCardTitle>
                <VCardSubtitle>
                  Тестирование всплывающего алерта и создания записи без реального звонка
                </VCardSubtitle>
              </VCardItem>
              <VDivider />
              <VCardText>
                <VTextField
                  v-model="emuForm.caller_phone"
                  label="Тестовый номер звонящего"
                  placeholder="+79220079019"
                  class="mb-3"
                />
                <VTextField
                  v-model="emuForm.extension"
                  label="Внутренний номер оператора"
                  placeholder="101"
                  class="mb-3"
                />
                <VSelect
                  v-model="emuForm.call_state"
                  :items="['Appeared', 'Connected', 'Disconnected']"
                  label="Событие вызова"
                  class="mb-4"
                />
                <VBtn
                  color="secondary"
                  variant="tonal"
                  block
                  :loading="emuForm.loading"
                  @click="triggerWebhookEmulator"
                >
                  <VIcon icon="bx-play-circle" start />
                  Смоделировать звонок
                </VBtn>
              </VCardText>
            </VCard>
          </VCol>
        </VRow>
      </VWindowItem>

      <!-- 4. Инструкции и Документация -->
      <VWindowItem value="instructions">
        <VCard elevation="1">
          <VCardItem>
            <VCardTitle class="d-flex align-center gap-2">
              <VIcon icon="bx-help-circle" color="primary" />
              Полное руководство по интеграции с телефонией Mango Office ВАТС
            </VCardTitle>
            <VCardSubtitle>
              Пошаговая инструкция по подключению API, настройке вебхуков и сценариям работы
            </VCardSubtitle>
          </VCardItem>
          <VDivider />

          <VCardText>
            <VExpansionPanels variant="accordion" multiple>
              <!-- Шаг 1 -->
              <VExpansionPanel>
                <VExpansionPanelTitle class="font-weight-bold">
                  <span class="mango-step-number">1</span>
                  Где получить API Key и API Salt в личном кабинете Mango Office
                </VExpansionPanelTitle>
                <VExpansionPanelText>
                  <ol class="ps-4 mb-3">
                    <li class="mb-2">
                      Войдите в личный кабинет <strong>Mango Office</strong> под учетной записью администратора по адресу <a href="https://lk.mango-office.ru" target="_blank">lk.mango-office.ru</a>.
                    </li>
                    <li class="mb-2">
                      Перейдите в раздел меню <strong>«Инструменты»</strong> &rarr; <strong>«Интеграции»</strong> &rarr; <strong>«API для разработчиков»</strong> (или «Виртуальная АТС» &rarr; «Интеграция с CRM»).
                    </li>
                    <li class="mb-2">
                      Включите переключатель <strong>«Подключение по API»</strong>.
                    </li>
                    <li class="mb-2">
                      Скопируйте значение поля <strong>«Уникальный код вашей АТС»</strong> — это ваш <span class="mango-code-inline">vpbx_api_key</span>.
                    </li>
                    <li class="mb-2">
                      Нажмите кнопку <strong>«Сгенерировать ключ»</strong> в блоке подписи — это ваш <span class="mango-code-inline">vpbx_api_salt</span>.
                    </li>
                    <li>
                      Вставьте полученные значения во вкладке <strong>«Настройки подключения»</strong> данной админ-панели и нажмите «Сохранить».
                    </li>
                  </ol>
                </VExpansionPanelText>
              </VExpansionPanel>

              <!-- Шаг 2 -->
              <VExpansionPanel>
                <VExpansionPanelTitle class="font-weight-bold">
                  <span class="mango-step-number">2</span>
                  Настройка Webhook (URL внешней системы для получения уведомлений)
                </VExpansionPanelTitle>
                <VExpansionPanelText>
                  <p>Для того чтобы система в режиме реального времени определяла звонящего клиента и сохраняла аудиозаписи разговоров, настройте Webhook в Mango:</p>
                  <ol class="ps-4 mb-3">
                    <li class="mb-2">
                      В ЛК Mango Office в блоке <strong>«Адрес внешней системы (URL)»</strong> вставьте адрес:
                      <div class="mango-code-block">{{ settings.webhook_url }}</div>
                    </li>
                    <li class="mb-2">
                      Отметьте чекбоксами следующие типы событий:
                      <ul>
                        <li><strong>Звонки (events/call)</strong> — уведомления о начале вызова, соединении и завершении;</li>
                        <li><strong>Записи разговоров (events/recording)</strong> — получение идентификатора аудиозаписи после окончания беседы;</li>
                        <li><strong>Сводная статистика (events/summary)</strong> — итоговая длительность и результаты.</li>
                      </ul>
                    </li>
                    <li>
                      Сохраните настройки в личном кабинете Mango Office.
                    </li>
                  </ol>
                </VExpansionPanelText>
              </VExpansionPanel>

              <!-- Шаг 3 -->
              <VExpansionPanel>
                <VExpansionPanelTitle class="font-weight-bold">
                  <span class="mango-step-number">3</span>
                  Технические требования: расчет цифровой подписи SHA-256
                </VExpansionPanelTitle>
                <VExpansionPanelText>
                  <p>Все запросы между вашей платформой и Mango Office защищаются криптографической подписью <strong>SHA-256</strong>:</p>
                  <div class="mango-code-block">
sign = SHA256(vpbx_api_key + json_string + vpbx_api_salt)
                  </div>
                  <p class="mb-0">
                    Бэкенд системы автоматически вычисляет данную подпись при каждом обращении (Click-to-Call, SMS, запрос записей) и сверяет подпись каждого входящего вебхука для защиты от спама и подделки данных.
                  </p>
                </VExpansionPanelText>
              </VExpansionPanel>

              <!-- Шаг 4 -->
              <VExpansionPanel>
                <VExpansionPanelTitle class="font-weight-bold">
                  <span class="mango-step-number">4</span>
                  Коды ответов и ошибок Mango Office API
                </VExpansionPanelTitle>
                <VExpansionPanelText>
                  <VTable density="compact">
                    <thead>
                      <tr>
                        <th>КОД</th>
                        <th>ЗНАЧЕНИЕ</th>
                        <th>КАК ИСПРАВИТЬ</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>1000</strong></td>
                        <td>Успешно</td>
                        <td>Запрос успешно принят и обработан Mango ВАТС.</td>
                      </tr>
                      <tr>
                        <td class="text-error"><strong>1001</strong></td>
                        <td>Неверная цифровая подпись</td>
                        <td>Проверьте правильность поля <code>vpbx_api_salt</code> в настройках.</td>
                      </tr>
                      <tr>
                        <td class="text-error"><strong>1003</strong></td>
                        <td>Неверный код АТС</td>
                        <td>Проверьте значение <code>vpbx_api_key</code>.</td>
                      </tr>
                      <tr>
                        <td class="text-error"><strong>1004</strong></td>
                        <td>Запрещен доступ по IP</td>
                        <td>В ЛК Mango в настройках API снимите ограничение по IP или добавьте IP <code>178.212.13.48</code>.</td>
                      </tr>
                      <tr>
                        <td class="text-error"><strong>1007</strong></td>
                        <td>Сотрудник не найден</td>
                        <td>Указанный добавочный номер (extension) отсутствует в списке линий ВАТС.</td>
                      </tr>
                    </tbody>
                  </VTable>
                </VExpansionPanelText>
              </VExpansionPanel>

              <!-- Шаг 5 -->
              <VExpansionPanel>
                <VExpansionPanelTitle class="font-weight-bold">
                  <span class="mango-step-number">5</span>
                  Сценарии использования в доставке еды и ресторанах
                </VExpansionPanelTitle>
                <VExpansionPanelText>
                  <ul>
                    <li class="mb-2">
                      <strong>Моментальное распознавание гостя при звонке:</strong> Как только клиент набирает номер ресторана, система по входящему событию Mango находит гостя в базе, отображая оператору его имя, баланс баллов и последние заказы.
                    </li>
                    <li class="mb-2">
                      <strong>Звонок из заказа в 1 клик (Click-to-Call):</strong> Оператор или курьер нажимает кнопку вызова в карточке заказа — телефон сотрудника звонит и автоматически соединяет с клиентом без ручного набора номера.
                    </li>
                    <li class="mb-2">
                      <strong>Контроль качества обслуживания:</strong> Все записи разговоров доступны для мгновенного прослушивания прямо в таблице админки с возможностью скачивания аудио в MP3.
                    </li>
                  </ul>
                </VExpansionPanelText>
              </VExpansionPanel>
            </VExpansionPanels>
          </VCardText>
        </VCard>
      </VWindowItem>
    </VWindow>

    <!-- Диалог результатов тестирования подключения -->
    <VDialog v-model="testDialog.show" max-width="600">
      <VCard>
        <VCardItem :class="testDialog.success ? 'bg-success' : 'bg-error'">
          <VCardTitle class="text-white d-flex align-center gap-2">
            <VIcon :icon="testDialog.success ? 'bx-check-circle' : 'bx-error-circle'" />
            {{ testDialog.title }}
          </VCardTitle>
        </VCardItem>
        <VCardText class="pa-6">
          <p class="text-body-1 mb-4">{{ testDialog.message }}</p>

          <div v-if="testDialog.success">
            <VAlert type="success" variant="tonal" class="mb-4">
              Ключ API (vpbx_api_key) и ключ подписи (vpbx_api_salt) корректны. Запрос к шлюзу Mango Office выполнен успешно.
            </VAlert>

            <div v-if="testDialog.usersCount > 0" class="mb-3">
              <div class="font-weight-bold mb-2">
                Обнаружено активных сотрудников/линий ВАТС: {{ testDialog.usersCount }}
              </div>
              <VList density="compact" lines="one">
                <VListItem
                  v-for="u in testDialog.usersSample"
                  :key="u.extension"
                  :title="`${u.name || 'Сотрудник'} (доб. ${u.extension})`"
                  :subtitle="u.email || u.general_phone || 'Линия ВАТС'"
                  prepend-icon="bx-user"
                />
              </VList>
            </div>
          </div>
          <div v-else>
            <VAlert type="error" variant="tonal">
              Пожалуйста, убедитесь, что API подключено в личном кабинете Mango Office, а ключи скопированы без пробелов.
            </VAlert>
          </div>
        </VCardText>
        <VCardActions class="justify-end pa-4">
          <VBtn color="primary" @click="testDialog.show = false">Понятно</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Snackbar для уведомлений -->
    <VSnackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="4000"
      location="top right"
    >
      {{ snackbar.text }}
      <template #actions>
        <VBtn variant="text" @click="snackbar.show = false">Закрыть</VBtn>
      </template>
    </VSnackbar>
  </div>
</template>
