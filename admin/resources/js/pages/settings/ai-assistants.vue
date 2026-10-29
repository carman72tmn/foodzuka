<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import '@/../styles/ai-assistants.css'

// ==========================================
// СОСТОЯНИЕ
// ==========================================
const activeTab = ref('assistants') // 'assistants' | 'analytics'
const loading = ref(false)
const assistants = ref([])
const siteAgents = ref([])
const connections = ref([])

// Аналитика и наблюдения (Zero-Token mode)
const analyticsLoading = ref(false)
const analyticsDays = ref(7)
const analyticsData = ref(null)
const aiSummaryLoading = ref(false)
const aiSummaryText = ref('')

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

const showSnackbar = (text, color = 'success') => {
  snackbar.value = { show: true, text, color }
}

// Модальное окно создания / редактирования
const isEditModalOpen = ref(false)
const isSaving = ref(false)
const formMode = ref('create') // 'create' | 'edit'

const assistantForm = ref({
  id: null,
  name: '',
  code: '',
  role_title: '',
  avatar_skin: 'chef_male',
  avatar_custom_url: '',
  avatar_animation_mode: 'alive',
  character_tone: 'professional',
  assigned_pages: ['*'],
  zone_of_responsibility: 'full_control',
  linked_agent_code: 'omni_assistant',
  connection_id: null,
  model_override: null,
  is_active: true,
  allow_sound_alerts: true,
  allow_voice_tts: false,
  daily_token_limit: 50000,
  daily_requests_limit: 100,
  auto_check_interval_sec: 30,
  system_prompt_addon: '',
  allow_external_queries: true,
  allow_iiko_api_queries: false,
  allow_iiko_export: false,
  allowed_external_tools: ['weather', 'general_search', 'consulting'],
  iiko_allowed_actions: ['read_orders', 'read_menu', 'read_stop_list'],
  enable_analytics_learning: true
})

// Модальное окно тестового чата
const isTestChatOpen = ref(false)
const testAssistant = ref(null)
const testMessage = ref('')
const isTestingSending = ref(false)
const testChatMessages = ref([])

// Доступные варианты скинов
const skinOptions = [
  {
    code: 'chef_male',
    title: 'Шеф-Повар Марк',
    desc: 'Белый китель, колпак, строгий взгляд. Контроль кухни и скорости отдачи.',
    icon: 'bx-restaurant',
    color: '#ffb88c'
  },
  {
    code: 'admin_female',
    title: 'Управляющая Анна',
    desc: 'Деловой костюм, гарнитура, очки. Координация кассы, операторов и смен.',
    icon: 'bx-user-check',
    color: '#fed7aa'
  },
  {
    code: 'courier_male',
    title: 'Курьер Макс',
    desc: 'Кепка, брендированное худи, термосумка. Логистика, время доставки и курьеры.',
    icon: 'bx-cycling',
    color: '#ef4444'
  },
  {
    code: 'cyber_bot',
    title: 'Кибер-Робот Нео',
    desc: 'Неоновый визор, парящий корпус. Универсальный интеллектуальный советник.',
    icon: 'bx-bot',
    color: '#7367f0'
  },
  {
    code: 'fox_mascot',
    title: 'Лис Везунчик',
    desc: 'Фирменный маскот сети «Везу Ролл». Позитив, поддержка команды и гостей.',
    icon: 'bx-smile',
    color: '#ea580c'
  },
  {
    code: 'custom',
    title: 'Свой Аватар',
    desc: 'Загрузите собственное изображение по ссылке.',
    icon: 'bx-image',
    color: '#00cfe8'
  }
]

// Доступные характеры
const characterTones = [
  { value: 'strict_supervisor', title: 'Строгий шеф (Контроль и дисциплина)' },
  { value: 'professional', title: 'Деловой и лаконичный (Старший администратор)' },
  { value: 'caring_mentor', title: 'Заботливый наставник (Обучение и подсказки)' },
  { value: 'friendly', title: 'Дружелюбный и бодрый (Энергия команды)' },
  { value: 'humorous', title: 'С юмором и позитивом (Фирменный стиль)' }
]

// Доступные зоны ответственности
const responsibilityZones = [
  { value: 'kitchen_control', title: '🍳 Контроль кухни и времени отдачи', color: 'warning' },
  { value: 'delivery_control', title: '🚴 Контроль доставки и курьеров', color: 'info' },
  { value: 'admin_cashier', title: '💼 Касса, операторы и подтверждение заказов', color: 'success' },
  { value: 'full_control', title: '🌐 Полный комплексный контроль заведения', color: 'primary' }
]

// Все доступные страницы и блоки системы для привязки помощника
const availablePages = [
  { value: '*', title: '⭐ Все страницы сайта и админки (*)' },
  { value: '/orders', title: '📦 Заказы и касса (/orders)' },
  { value: '/kitchen', title: '🍳 Кухня, цеха и монитор повара (/kitchen)' },
  { value: '/pers', title: '📱 Панель сотрудников и курьеров (/pers)' },
  { value: '/employees', title: '👥 Сотрудники, должности и смены (/employees)' },
  { value: '/customers', title: '👤 База гостей и CRM (/customers)' },
  { value: '/loyalty', title: '🎁 Программа лояльности и акции (/loyalty)' },
  { value: '/multichat', title: '💬 Мультичат и диалоги с гостями (/multichat)' },
  { value: '/notifications-feed', title: '🔔 Лента уведомлений (/notifications-feed)' },
  { value: '/mailings/notifications-and-mailings', title: '📢 Маркетинговые рассылки (/mailings/...)' },
  { value: '/mailings/cascades', title: '🔀 Каскадные рассылки VK, MAX, TG (/mailings/cascades)' },
  { value: '/dashboard', title: '📊 Главный дашборд заведения (/dashboard)' },
  { value: '/reports', title: '📈 Финансовые отчеты и OLAP (/reports)' },
  { value: '/reports/courier-reports', title: '🚴 Отчеты курьеров (/reports/courier-reports)' },
  { value: '/products', title: '🍱 Меню, товары и модификаторы (/products)' },
  { value: '/categories', title: '📑 Категории блюд (/categories)' },
  { value: '/companies', title: '🏢 Юрлица и филиалы (/companies)' },
  { value: '/system/modules', title: '🧩 Модули системы (/system/modules)' },
  { value: '/system/backups', title: '🛡️ Бэкапы и ИИ-протоколы (/system/backups)' },
  { value: '/system/server', title: '🖥️ Мониторинг сервера (/system/server)' },
  { value: '/system/tasks', title: '⚙️ Фоновые задачи Celery (/system/tasks)' },
  { value: '/system/tags', title: '🏷️ Метки клиентов (/system/tags)' },
  { value: '/system/logs', title: '📋 Логи синхронизации (/system/logs)' },
  { value: '/system/system-logs', title: '⚠️ Системные ошибки (/system/system-logs)' },
  { value: '/system/maintenance', title: '🧹 Обслуживание базы (/system/maintenance)' },
  { value: '/settings/ai-assistants', title: '🤖 Настройки Помощников ИИ (/settings/ai-assistants)' },
  { value: '/settings/ai-agents', title: '🧠 ИИ-Агенты и LLM (/settings/ai-agents)' },
  { value: '/settings/iiko', title: '⚙️ Интеграция iiko Cloud & Resto (/settings/iiko)' },
  { value: '/settings/yandex', title: '🗺️ Яндекс Доставка (/settings/yandex)' },
  { value: '/settings/tbank', title: '💳 Т-Банк эквайринг (/settings/tbank)' },
  { value: '/settings/mango', title: '📞 Телефония Mango (/settings/mango)' },
  { value: '/settings/max', title: '💬 Мессенджер MAX (/settings/max)' },
  { value: '/settings/vk-parser', title: '🔍 ВК Парсер клиентов (/settings/vk-parser)' },
  { value: '/settings/vk-notifications', title: '✉️ ВК Уведомления (/settings/vk-notifications)' }
]

// Доступные внешние инструменты
const externalToolOptions = [
  { value: 'weather', title: '🌤️ Погода и температура' },
  { value: 'general_search', title: '🔍 Общий поиск и факты' },
  { value: 'consulting', title: '💡 Консультирование и подсказки' },
  { value: 'traffic', title: '🚗 Дорожная ситуация и пробки' }
]

// Разрешенные действия iiko API
const iikoActionOptions = [
  { value: 'read_orders', title: '📋 Чтение текущих заказов iiko' },
  { value: 'read_menu', title: '🍱 Чтение меню и цен iiko' },
  { value: 'read_stop_list', title: '🚫 Чтение стоп-листов блюд' },
  { value: 'export_reports', title: '📊 Выгрузка сводных отчетов' }
]

// Анимационные стили
const animationModes = [
  { value: 'alive', title: 'Живой (дыхание, легкое покачивание)' },
  { value: 'float', title: 'Левитация (плавный полет вверх-вниз)' },
  { value: 'pulse', title: 'Мягкая неоновая пульсация' },
  { value: 'static', title: 'Статичный' }
]

// Суммарная статистика
const totalTokensToday = computed(() => {
  return assistants.value.reduce((acc, a) => acc + (a.used_tokens_today || 0), 0)
})

const totalRequestsToday = computed(() => {
  return assistants.value.reduce((acc, a) => acc + (a.used_requests_today || 0), 0)
})

const activeAssistantsCount = computed(() => {
  return assistants.value.filter(a => a.is_active).length
})

// ==========================================
// ЗАГРУЗКА ДАННЫХ
// ==========================================
const fetchData = async () => {
  loading.value = true
  try {
    const [asRes, agRes, cnRes] = await Promise.all([
      axios.get('/api/v1/ai-assistants/'),
      axios.get('/api/v1/ai-agents/site-agents'),
      axios.get('/api/v1/ai-agents/connections')
    ])
    assistants.value = asRes.data || []
    siteAgents.value = agRes.data || []
    connections.value = cnRes.data || []
  } catch (e) {
    showSnackbar('Ошибка загрузки данных помощников', 'error')
  } finally {
    loading.value = false
  }
}

// Загрузка аналитики и наблюдений (Zero-Token mode)
const fetchAnalytics = async () => {
  analyticsLoading.value = true
  try {
    const res = await axios.get('/api/v1/ai-assistants/analytics/observations', {
      params: { days: analyticsDays.value }
    })
    analyticsData.value = res.data
  } catch (e) {
    showSnackbar('Ошибка загрузки аналитики: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    analyticsLoading.value = false
  }
}

const generateAiSummary = async () => {
  aiSummaryLoading.value = true
  try {
    const res = await axios.post(`/api/v1/ai-assistants/analytics/generate-ai-summary?days=${analyticsDays.value}`)
    aiSummaryText.value = res.data.summary || 'Резюме сформировано.'
    showSnackbar('ИИ-резюме успешно сформировано!')
  } catch (e) {
    showSnackbar('Ошибка генерации резюме: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    aiSummaryLoading.value = false
  }
}

// Открытие модалки создания
const openCreateModal = () => {
  formMode.value = 'create'
  assistantForm.value = {
    id: null,
    name: '',
    code: `assistant_${Math.floor(Date.now() / 1000)}`,
    role_title: '',
    avatar_skin: 'chef_male',
    avatar_custom_url: '',
    avatar_animation_mode: 'alive',
    character_tone: 'professional',
    assigned_pages: ['*'],
    zone_of_responsibility: 'full_control',
    linked_agent_code: 'omni_assistant',
    connection_id: null,
    model_override: null,
    is_active: true,
    allow_sound_alerts: true,
    allow_voice_tts: false,
    daily_token_limit: 50000,
    daily_requests_limit: 100,
    auto_check_interval_sec: 30,
    system_prompt_addon: '',
    allow_external_queries: true,
    allow_iiko_api_queries: false,
    allow_iiko_export: false,
    allowed_external_tools: ['weather', 'general_search', 'consulting'],
    iiko_allowed_actions: ['read_orders', 'read_menu', 'read_stop_list'],
    enable_analytics_learning: true
  }
  isEditModalOpen.value = true
}

// Открытие модалки редактирования
const openEditModal = (item) => {
  formMode.value = 'edit'
  assistantForm.value = {
    ...item,
    assigned_pages: Array.isArray(item.assigned_pages) && item.assigned_pages.length > 0 ? [...item.assigned_pages] : ['*'],
    allowed_external_tools: Array.isArray(item.allowed_external_tools) ? [...item.allowed_external_tools] : ['weather', 'general_search', 'consulting'],
    iiko_allowed_actions: Array.isArray(item.iiko_allowed_actions) ? [...item.iiko_allowed_actions] : ['read_orders', 'read_menu', 'read_stop_list'],
    allow_external_queries: item.allow_external_queries !== false,
    allow_iiko_api_queries: item.allow_iiko_api_queries === true,
    allow_iiko_export: item.allow_iiko_export === true,
    enable_analytics_learning: item.enable_analytics_learning !== false
  }
  isEditModalOpen.value = true
}

// Сохранение помощника
const saveAssistant = async () => {
  if (!assistantForm.value.name?.trim() || !assistantForm.value.role_title?.trim()) {
    showSnackbar('Заполните имя и роль помощника', 'warning')
    return
  }

  isSaving.value = true
  try {
    const payload = {
      name: assistantForm.value.name.trim(),
      role_title: assistantForm.value.role_title.trim(),
      avatar_skin: assistantForm.value.avatar_skin || 'chef_male',
      avatar_custom_url: assistantForm.value.avatar_custom_url || null,
      avatar_animation_mode: assistantForm.value.avatar_animation_mode || 'alive',
      character_tone: assistantForm.value.character_tone || 'professional',
      assigned_pages: Array.isArray(assistantForm.value.assigned_pages) && assistantForm.value.assigned_pages.length > 0 ? assistantForm.value.assigned_pages : ['*'],
      zone_of_responsibility: assistantForm.value.zone_of_responsibility || 'full_control',
      linked_agent_code: assistantForm.value.linked_agent_code || 'omni_assistant',
      connection_id: assistantForm.value.connection_id ? Number(assistantForm.value.connection_id) : null,
      model_override: assistantForm.value.model_override || null,
      is_active: assistantForm.value.is_active !== false,
      allow_sound_alerts: assistantForm.value.allow_sound_alerts !== false,
      allow_voice_tts: assistantForm.value.allow_voice_tts === true,
      daily_token_limit: Number(assistantForm.value.daily_token_limit) || 50000,
      daily_requests_limit: Number(assistantForm.value.daily_requests_limit) || 100,
      auto_check_interval_sec: Number(assistantForm.value.auto_check_interval_sec) || 30,
      system_prompt_addon: assistantForm.value.system_prompt_addon || null,
      allow_external_queries: assistantForm.value.allow_external_queries !== false,
      allow_iiko_api_queries: assistantForm.value.allow_iiko_api_queries === true,
      allow_iiko_export: assistantForm.value.allow_iiko_export === true,
      allowed_external_tools: assistantForm.value.allowed_external_tools || ['weather', 'general_search', 'consulting'],
      iiko_allowed_actions: assistantForm.value.iiko_allowed_actions || ['read_orders', 'read_menu', 'read_stop_list'],
      enable_analytics_learning: assistantForm.value.enable_analytics_learning !== false
    }

    if (formMode.value === 'create') {
      payload.code = assistantForm.value.code || `assistant_${Math.floor(Date.now() / 1000)}`
      const res = await axios.post('/api/v1/ai-assistants/', payload)
      assistants.value.push(res.data)
      showSnackbar('Помощник успешно создан!')
    } else {
      const res = await axios.put(`/api/v1/ai-assistants/${assistantForm.value.id}`, payload)
      const idx = assistants.value.findIndex(a => a.id === assistantForm.value.id)
      if (idx !== -1) assistants.value[idx] = res.data
      showSnackbar('Настройки помощника успешно обновлены!')
    }
    isEditModalOpen.value = false
  } catch (e) {
    showSnackbar('Ошибка сохранения помощника: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    isSaving.value = false
  }
}

// Удаление помощника
const deleteAssistant = async (item) => {
  if (!confirm(`Удалить виртуального помощника «${item.name}»?`)) return
  try {
    await axios.delete(`/api/v1/ai-assistants/${item.id}`)
    assistants.value = assistants.value.filter(a => a.id !== item.id)
    showSnackbar(`Помощник «${item.name}» удален`)
  } catch (e) {
    showSnackbar('Ошибка при удалении: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

// Быстрое переключение активности (PATCH toggle)
const toggleActive = async (item) => {
  try {
    const res = await axios.patch(`/api/v1/ai-assistants/${item.id}/toggle`, { is_active: item.is_active })
    item.is_active = res.data.is_active
    showSnackbar(`Статус помощника «${item.name}» изменен`)
  } catch (e) {
    item.is_active = !item.is_active
    showSnackbar('Ошибка изменения статуса: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

// Тестовый диалог с помощником прямо в настройках
const openTestChat = (item) => {
  testAssistant.value = item
  testChatMessages.value = [
    {
      role: 'assistant',
      content: `Привет! Я — ${item.name} (${item.role_title}). Готов ответить на любые вопросы и проверить текущую ситуацию в заведении!`
    }
  ]
  testMessage.value = ''
  isTestChatOpen.value = true
}

const sendTestMessage = async () => {
  const msg = testMessage.value.trim()
  if (!msg || isTestingSending.value || !testAssistant.value) return

  testMessage.value = ''
  testChatMessages.value.push({ role: 'user', content: msg })
  isTestingSending.value = true

  try {
    const res = await axios.post(`/api/v1/ai-assistants/${testAssistant.value.id}/chat`, {
      message: msg,
      session_id: 'settings_preview_test',
      page_route: '/settings/ai-assistants'
    })
    testChatMessages.value.push({
      role: 'assistant',
      content: res.data.reply
    })
  } catch (e) {
    testChatMessages.value.push({
      role: 'assistant',
      content: 'Ошибка при связи с сервером.'
    })
  } finally {
    isTestingSending.value = false
  }
}

onMounted(() => {
  fetchData()
  fetchAnalytics()
})
</script>

<template>
  <div class="ai-assistants-page">
    <!-- Шапка страницы -->
    <div class="d-flex align-center justify-space-between flex-wrap gap-3 mb-6">
      <div>
        <h2 class="text-h4 font-weight-bold d-flex align-center gap-2">
          <v-icon size="32" icon="bx-user-voice" color="primary" />
          <span>Виртуальные Помощники ИИ на страницах сайта</span>
        </h2>
        <p class="text-body-2 text-medium-emphasis mb-0 mt-1">
          Интерактивные анимированные ассистенты для сотрудников: контроль времени кухни, зависших заказов и доставки с жесткой экономией токенов.
        </p>
      </div>

      <div class="d-flex align-center gap-2">
        <v-btn
          v-if="activeTab === 'assistants'"
          color="primary"
          prepend-icon="bx-plus"
          elevation="2"
          @click="openCreateModal"
        >
          Создать помощника
        </v-btn>
        <v-btn
          v-if="activeTab === 'analytics'"
          color="secondary"
          variant="tonal"
          prepend-icon="bx-refresh"
          :loading="analyticsLoading"
          @click="fetchAnalytics"
        >
          Обновить статистику
        </v-btn>
      </div>
    </div>

    <!-- Переключатель вкладок -->
    <v-tabs v-model="activeTab" class="mb-6 border-b">
      <v-tab value="assistants">
        <v-icon icon="bx-bot" class="me-2" />
        Виртуальные помощники ({{ assistants.length }})
      </v-tab>
      <v-tab value="analytics">
        <v-icon icon="bx-line-chart" class="me-2" />
        Наблюдения и статистика работы (Zero-Token)
      </v-tab>
    </v-tabs>

    <div v-if="activeTab === 'assistants'">
    <!-- Информационные карточки статистики -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 assistant-card" elevation="1">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-caption text-medium-emphasis">Активных помощников</div>
              <div class="text-h4 font-weight-bold mt-1 text-primary">{{ activeAssistantsCount }}</div>
            </div>
            <v-avatar size="44" color="rgba(115, 103, 240, 0.15)">
              <v-icon size="24" icon="bx-bot" color="primary" />
            </v-avatar>
          </div>
          <div class="text-caption text-medium-emphasis mt-2">
            Всего настроено: {{ assistants.length }} персонажей
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 assistant-card" elevation="1">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-caption text-medium-emphasis">Запросов к LLM сегодня</div>
              <div class="text-h4 font-weight-bold mt-1 text-info">{{ totalRequestsToday }}</div>
            </div>
            <v-avatar size="44" color="rgba(0, 207, 232, 0.15)">
              <v-icon size="24" icon="bx-message-rounded-dots" color="info" />
            </v-avatar>
          </div>
          <div class="text-caption text-medium-emphasis mt-2">
            Контроль суточных лимитов
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 assistant-card" elevation="1">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-caption text-medium-emphasis">Токенов сегодня</div>
              <div class="text-h4 font-weight-bold mt-1 text-success">{{ totalTokensToday }}</div>
            </div>
            <v-avatar size="44" color="rgba(40, 199, 111, 0.15)">
              <v-icon size="24" icon="bx-chip" color="success" />
            </v-avatar>
          </div>
          <div class="text-caption text-medium-emphasis mt-2">
            Режим жесткой экономии
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 assistant-card" elevation="1">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-caption text-medium-emphasis">Фоновый SQL-анализ</div>
              <div class="text-h4 font-weight-bold mt-1 text-warning">0 токенов</div>
            </div>
            <v-avatar size="44" color="rgba(255, 159, 67, 0.15)">
              <v-icon size="24" icon="bx-tachometer" color="warning" />
            </v-avatar>
          </div>
          <div class="text-caption text-medium-emphasis mt-2">
            Аналитика на сервере без затрат
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Список Помощников -->
    <v-card elevation="2" class="rounded-xl overflow-hidden">
      <v-card-title class="pa-4 d-flex align-center justify-space-between">
        <span class="font-weight-bold">Список настроенных виртуальных помощников</span>
        <v-btn icon size="small" variant="text" @click="fetchData">
          <v-icon size="18" icon="bx-refresh" />
        </v-btn>
      </v-card-title>

      <v-divider />

      <v-table hover>
        <thead>
          <tr>
            <th style="width: 70px;">Аватар</th>
            <th>Имя и Роль</th>
            <th>Зона ответственности</th>
            <th>Привязка к страницам</th>
            <th>Связка с ИИ</th>
            <th>Квота (сегодня)</th>
            <th>Статус</th>
            <th class="text-right">Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in assistants" :key="item.id">
            <!-- Аватар -->
            <td>
              <div
                class="floating-assistant-avatar"
                :class="[
                  item.avatar_animation_mode === 'alive' ? 'avatar-anim-alive' :
                  item.avatar_animation_mode === 'float' ? 'avatar-anim-float' :
                  item.avatar_animation_mode === 'pulse' ? 'avatar-anim-pulse' : ''
                ]"
                style="width: 44px; height: 44px; margin: 4px 0;"
              >
                <!-- 1. Шеф -->
                <svg v-if="item.avatar_skin === 'chef_male'" viewBox="0 0 48 48" width="30" height="30" fill="none">
                  <circle cx="24" cy="28" r="14" fill="#ffb88c" />
                  <path d="M14 20 C10 10, 20 6, 24 10 C28 6, 38 10, 34 20 Z" fill="#ffffff" />
                  <rect x="14" y="19" width="20" height="4" rx="2" fill="#e2e8f0" />
                  <circle cx="19" cy="26" r="2" fill="#2d3748" />
                  <circle cx="29" cy="26" r="2" fill="#2d3748" />
                  <path d="M17 31 C21 34, 24 32, 24 31 C24 32, 27 34, 31 31" stroke="#4a5568" stroke-width="2.2" stroke-linecap="round" fill="none" />
                </svg>

                <!-- 2. Анна -->
                <svg v-else-if="item.avatar_skin === 'admin_female'" viewBox="0 0 48 48" width="30" height="30" fill="none">
                  <circle cx="24" cy="24" r="13" fill="#fed7aa" />
                  <path d="M11 24 C11 14, 18 10, 24 10 C30 10, 37 14, 37 24 Z" fill="#92400e" />
                  <rect x="15" y="21" width="7" height="5" rx="1.5" stroke="#7c3aed" stroke-width="1.8" fill="rgba(255,255,255,0.3)" />
                  <rect x="26" y="21" width="7" height="5" rx="1.5" stroke="#7c3aed" stroke-width="1.8" fill="rgba(255,255,255,0.3)" />
                </svg>

                <!-- 3. Курьер -->
                <svg v-else-if="item.avatar_skin === 'courier_male'" viewBox="0 0 48 48" width="30" height="30" fill="none">
                  <circle cx="24" cy="26" r="13" fill="#fcd34d" />
                  <path d="M13 20 C13 13, 20 11, 28 12 L37 15 L28 19 L13 20 Z" fill="#ef4444" />
                </svg>

                <!-- 4. Кибер-Бот -->
                <svg v-else-if="item.avatar_skin === 'cyber_bot'" viewBox="0 0 48 48" width="30" height="30" fill="none">
                  <rect x="12" y="14" width="24" height="22" rx="8" fill="#1e1e2d" stroke="#7367f0" stroke-width="2" />
                  <rect x="16" y="20" width="16" height="8" rx="4" fill="#0f172a" stroke="#00cfe8" stroke-width="1.5" />
                </svg>

                <!-- 5. Лис -->
                <svg v-else-if="item.avatar_skin === 'fox_mascot'" viewBox="0 0 48 48" width="30" height="30" fill="none">
                  <polygon points="12,18 17,6 23,17" fill="#ea580c" />
                  <polygon points="36,18 31,6 25,17" fill="#ea580c" />
                  <circle cx="24" cy="27" r="14" fill="#ea580c" />
                </svg>

                <img
                  v-else-if="item.avatar_custom_url"
                  :src="item.avatar_custom_url"
                  style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;"
                />
                <v-icon v-else size="24" icon="bx-bot" color="primary" />
              </div>
            </td>

            <!-- Имя и Роль -->
            <td>
              <div class="font-weight-bold text-subtitle-2">{{ item.name }}</div>
              <div class="text-caption text-medium-emphasis">{{ item.role_title }}</div>
              <v-chip size="x-small" variant="tonal" class="mt-1" color="secondary">
                {{ item.character_tone }}
              </v-chip>
            </td>

            <!-- Зона ответственности -->
            <td>
              <v-chip
                size="small"
                variant="tonal"
                :color="
                  item.zone_of_responsibility === 'kitchen_control' ? 'warning' :
                  item.zone_of_responsibility === 'delivery_control' ? 'info' :
                  item.zone_of_responsibility === 'admin_cashier' ? 'success' : 'primary'
                "
              >
                {{
                  item.zone_of_responsibility === 'kitchen_control' ? 'Кухня и отдача' :
                  item.zone_of_responsibility === 'delivery_control' ? 'Доставка и курьеры' :
                  item.zone_of_responsibility === 'admin_cashier' ? 'Касса и заказы' : 'Полный контроль'
                }}
              </v-chip>
            </td>

            <!-- Привязка к страницам -->
            <td>
              <div class="d-flex flex-wrap gap-1">
                <v-chip
                  v-for="(p, pIdx) in item.assigned_pages"
                  :key="pIdx"
                  size="x-small"
                  variant="outlined"
                >
                  {{ p === '*' ? '⭐ Все страницы' : p }}
                </v-chip>
              </div>
            </td>

            <!-- Связка с ИИ -->
            <td>
              <div class="d-flex align-center gap-1">
                <v-icon size="14" icon="bx-link" color="primary" />
                <span class="text-caption font-weight-medium">{{ item.linked_agent_code || 'omni_assistant' }}</span>
              </div>
              <div v-if="item.model_override" class="text-caption text-medium-emphasis">
                {{ item.model_override }}
              </div>
            </td>

            <!-- Квота -->
            <td>
              <div class="text-caption">
                {{ item.used_requests_today || 0 }} / {{ item.daily_requests_limit }} зап.
              </div>
              <div class="text-caption text-medium-emphasis">
                {{ item.used_tokens_today || 0 }} ток.
              </div>
              <v-progress-linear
                :model-value="((item.used_requests_today || 0) / item.daily_requests_limit) * 100"
                height="4"
                rounded
                color="primary"
                class="mt-1"
                style="max-width: 80px;"
              />
            </td>

            <!-- Статус -->
            <td>
              <v-switch
                v-model="item.is_active"
                density="compact"
                hide-details
                color="success"
                @change="toggleActive(item)"
              />
            </td>

            <!-- Действия -->
            <td class="text-right">
              <v-btn
                icon
                size="small"
                variant="text"
                color="info"
                title="Тестировать диалог"
                @click="openTestChat(item)"
              >
                <v-icon size="18" icon="bx-chat" />
              </v-btn>

              <v-btn
                icon
                size="small"
                variant="text"
                color="primary"
                title="Редактировать"
                @click="openEditModal(item)"
              >
                <v-icon size="18" icon="bx-edit" />
              </v-btn>

              <v-btn
                icon
                size="small"
                variant="text"
                color="error"
                title="Удалить"
                @click="deleteAssistant(item)"
              >
                <v-icon size="18" icon="bx-trash" />
              </v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    </div> <!-- Конец вкладки помощников -->

    <!-- Вкладка: Наблюдения и статистика работы заведения (Zero-Token mode) -->
    <div v-else-if="activeTab === 'analytics'">
      <!-- Фильтры периода и значок экономии токенов -->
      <v-card class="mb-6 pa-4 border" elevation="1">
        <div class="d-flex align-center justify-space-between flex-wrap gap-4">
          <div class="d-flex align-center gap-3">
            <span class="text-subtitle-2 font-weight-bold">Период анализа:</span>
            <v-btn-toggle v-model="analyticsDays" mandatory density="compact" color="primary" @update:model-value="fetchAnalytics">
              <v-btn :value="7">7 дней</v-btn>
              <v-btn :value="14">14 дней</v-btn>
              <v-btn :value="30">30 дней</v-btn>
            </v-btn-toggle>
          </div>

          <div class="d-flex align-center gap-2">
            <v-chip color="success" variant="tonal" size="small" prepend-icon="bx-leaf">
              Режим экономии токенов: 0 LLM токенов на расчет
            </v-chip>
            <v-btn
              color="primary"
              variant="elevated"
              size="small"
              prepend-icon="bx-brain"
              :loading="aiSummaryLoading"
              @click="generateAiSummary"
            >
              Сгенерировать ИИ-вывод (~150 токенов)
            </v-btn>
          </div>
        </div>
      </v-card>

      <!-- KPI Метрики заведения -->
      <v-row v-if="analyticsData?.metrics" class="mb-6">
        <v-col cols="12" sm="6" md="3">
          <v-card class="pa-4 border" elevation="1">
            <div class="text-caption text-medium-emphasis">Всего заказов</div>
            <div class="text-h4 font-weight-bold mt-1 text-primary">{{ analyticsData.metrics.total_orders }}</div>
            <div class="text-caption text-medium-emphasis mt-1">
              Выручка: {{ Number(analyticsData.metrics.total_revenue).toLocaleString('ru-RU') }} ₽
            </div>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card class="pa-4 border" elevation="1">
            <div class="text-caption text-medium-emphasis">Средний чек</div>
            <div class="text-h4 font-weight-bold mt-1 text-success">{{ analyticsData.metrics.avg_check }} ₽</div>
            <div class="text-caption text-medium-emphasis mt-1">
              Отмененных заказов: {{ analyticsData.metrics.cancelled_count }}
            </div>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card class="pa-4 border" elevation="1">
            <div class="text-caption text-medium-emphasis">Пунктуальность доставки</div>
            <div class="text-h4 font-weight-bold mt-1" :class="analyticsData.metrics.punctuality_pct >= 85 ? 'text-success' : 'text-warning'">
              {{ analyticsData.metrics.punctuality_pct }}%
            </div>
            <div class="text-caption text-medium-emphasis mt-1">
              Вовремя: {{ analyticsData.metrics.on_time_count }} | Опозданий: {{ analyticsData.metrics.delayed_count }}
            </div>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card class="pa-4 border" elevation="1">
            <div class="text-caption text-medium-emphasis">Ср. время выполнения</div>
            <div class="text-h4 font-weight-bold mt-1 text-info">{{ analyticsData.metrics.avg_turnaround_min }} мин</div>
            <div class="text-caption text-medium-emphasis mt-1">
              От чека до вручения гостю
            </div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Блок Стратегического ИИ-резюме (если запрошено) -->
      <v-alert
        v-if="aiSummaryText"
        type="info"
        variant="tonal"
        class="mb-6 border"
        title="Стратегическое резюме ИИ-Ассистента (Smart Summary)"
      >
        <div class="mt-2 text-body-1" style="white-space: pre-line;">{{ aiSummaryText }}</div>
      </v-alert>

      <!-- Наблюдения экспертной системы (Zero-Token mode) -->
      <v-card class="mb-6 border" elevation="1">
        <v-card-title class="pa-4 d-flex align-center gap-2">
          <v-icon icon="bx-bulb" color="warning" />
          <span class="text-h6 font-weight-bold">Наблюдения и выводы системы (Автономный режим)</span>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4">
          <v-list density="comfortable" class="bg-transparent">
            <v-list-item
              v-for="(obs, oIdx) in analyticsData?.observations || []"
              :key="oIdx"
              class="px-0 py-2"
            >
              <div class="text-body-1" v-html="obs.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')" />
            </v-list-item>
            <v-list-item v-if="!analyticsData?.observations?.length">
              <div class="text-body-2 text-medium-emphasis">Сбор данных по заказам за указанный период продолжается...</div>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>

      <!-- Географическая зависимость и популярные улицы доставок -->
      <v-row class="mb-6">
        <v-col cols="12" md="7">
          <v-card class="border fill-height" elevation="1">
            <v-card-title class="pa-4 d-flex align-center gap-2">
              <v-icon icon="bx-map-pin" color="primary" />
              <span class="text-h6 font-weight-bold">Концентрация доставок по улицам</span>
            </v-card-title>
            <v-divider />
            <v-table density="compact">
              <thead>
                <tr>
                  <th>Улица / Направление</th>
                  <th class="text-center">Заказов</th>
                  <th class="text-end">Ср. чек</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="st in analyticsData?.streets_analysis || []" :key="st.street">
                  <td class="font-weight-medium">{{ st.street }}</td>
                  <td class="text-center">
                    <v-chip size="x-small" color="primary" variant="tonal">{{ st.orders_count }}</v-chip>
                  </td>
                  <td class="text-end font-weight-bold">{{ st.avg_amount }} ₽</td>
                </tr>
                <tr v-if="!analyticsData?.streets_analysis?.length">
                  <td colspan="3" class="text-center text-medium-emphasis py-4">Нет данных по адресам доставок</td>
                </tr>
              </tbody>
            </v-table>
          </v-card>
        </v-col>

        <!-- Курьеры и скорость доставки -->
        <v-col cols="12" md="5">
          <v-card class="border fill-height" elevation="1">
            <v-card-title class="pa-4 d-flex align-center gap-2">
              <v-icon icon="bx-cycling" color="info" />
              <span class="text-h6 font-weight-bold">Рейтинг курьеров</span>
            </v-card-title>
            <v-divider />
            <v-table density="compact">
              <thead>
                <tr>
                  <th>Курьер</th>
                  <th class="text-center">Рейсов</th>
                  <th class="text-end">Вовремя</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="cr in analyticsData?.courier_analysis || []" :key="cr.courier">
                  <td class="font-weight-medium">{{ cr.courier }}</td>
                  <td class="text-center">{{ cr.deliveries_count }}</td>
                  <td class="text-end">
                    <v-chip size="x-small" :color="cr.punctuality_pct >= 85 ? 'success' : 'warning'" variant="tonal">
                      {{ cr.punctuality_pct }}%
                    </v-chip>
                  </td>
                </tr>
                <tr v-if="!analyticsData?.courier_analysis?.length">
                  <td colspan="3" class="text-center text-medium-emphasis py-4">Нет данных по курьерам</td>
                </tr>
              </tbody>
            </v-table>
          </v-card>
        </v-col>
      </v-row>
    </div> <!-- Конец вкладки аналитики -->

    <!-- Модальное окно Создания / Редактирования Помощника -->
    <v-dialog v-model="isEditModalOpen" max-width="840" persistent>
      <v-card class="pa-2 rounded-xl">
        <v-card-title class="pa-4 d-flex align-center justify-space-between">
          <span class="font-weight-bold text-h6">
            {{ formMode === 'create' ? 'Создание виртуального помощника' : `Редактирование: ${assistantForm.name}` }}
          </span>
          <v-btn icon size="small" variant="text" @click="isEditModalOpen = false">
            <v-icon size="18" icon="bx-x" />
          </v-btn>
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-4" style="max-height: 70vh; overflow-y: auto;">
          <!-- 1. ВЫБОР СКИНА И АВАТАРА -->
          <div class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center gap-2">
            <v-icon size="20" icon="bx-palette" color="primary" />
            <span>1. Внешний вид и анимированный скин аватара</span>
          </div>

          <v-row class="mb-4">
            <v-col
              v-for="skin in skinOptions"
              :key="skin.code"
              cols="12"
              sm="6"
              md="4"
            >
              <div
                class="skin-card-item"
                :class="{ selected: assistantForm.avatar_skin === skin.code }"
                @click="assistantForm.avatar_skin = skin.code"
              >
                <div class="skin-avatar-preview">
                  <v-icon size="32" :icon="skin.icon" :color="skin.color" />
                </div>
                <div class="font-weight-bold text-subtitle-2">{{ skin.title }}</div>
                <div class="text-caption text-medium-emphasis mt-1">{{ skin.desc }}</div>
              </div>
            </v-col>
          </v-row>

          <v-text-field
            v-if="assistantForm.avatar_skin === 'custom'"
            v-model="assistantForm.avatar_custom_url"
            label="Ссылка на изображение аватара (URL)"
            placeholder="https://vezuroll.ru/media/avatar.png"
            density="compact"
            variant="outlined"
            class="mb-4"
          />

          <!-- 2. ОСНОВНЫЕ ПАРАМЕТРЫ -->
          <div class="text-subtitle-1 font-weight-bold mb-3 mt-4 d-flex align-center gap-2">
            <v-icon size="20" icon="bx-id-card" color="primary" />
            <span>2. Имя, должность и характер</span>
          </div>

          <v-row>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="assistantForm.name"
                label="Имя помощника *"
                placeholder="Например: Шеф Марк"
                density="compact"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model="assistantForm.role_title"
                label="Должность / Роль *"
                placeholder="Шеф-Повар / Контроль кухни"
                density="compact"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-select
                v-model="assistantForm.character_tone"
                :items="characterTones"
                item-value="value"
                item-title="title"
                label="Характер и тон общения"
                density="compact"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-select
                v-model="assistantForm.avatar_animation_mode"
                :items="animationModes"
                item-value="value"
                item-title="title"
                label="Стиль движения аватара"
                density="compact"
                variant="outlined"
              />
            </v-col>
          </v-row>

          <!-- 3. ЗОНА ОТВЕТСТВЕННОСТИ И ПРИВЯЗКА К СТРАНИЦАМ -->
          <div class="text-subtitle-1 font-weight-bold mb-3 mt-4 d-flex align-center gap-2">
            <v-icon size="20" icon="bx-compass" color="primary" />
            <span>3. Зона ответственности и привязка к страницам админки</span>
          </div>

          <v-row>
            <v-col cols="12" sm="6">
              <v-select
                v-model="assistantForm.zone_of_responsibility"
                :items="responsibilityZones"
                item-value="value"
                item-title="title"
                label="Зона ответственности"
                density="compact"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-select
                v-model="assistantForm.assigned_pages"
                :items="availablePages"
                item-value="value"
                item-title="title"
                multiple
                chips
                label="Где показывать плавающего ассистента"
                density="compact"
                variant="outlined"
              />
            </v-col>
          </v-row>

          <!-- 4. СВЯЗКА С ИИ-АГЕНТОМ И КВОТЫ -->
          <div class="text-subtitle-1 font-weight-bold mb-3 mt-4 d-flex align-center gap-2">
            <v-icon size="20" icon="bx-slider-alt" color="primary" />
            <span>4. Модель ИИ, квоты и оптимизация токенов</span>
          </div>

          <v-row>
            <v-col cols="12" sm="6">
              <v-select
                v-model="assistantForm.linked_agent_code"
                :items="siteAgents"
                item-value="agent_code"
                item-title="title"
                label="Связанный ИИ-Агент"
                density="compact"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model="assistantForm.daily_requests_limit"
                type="number"
                label="Дневной лимит сообщений к LLM"
                density="compact"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model="assistantForm.auto_check_interval_sec"
                type="number"
                label="Интервал фоновой проверки задержек (сек)"
                density="compact"
                variant="outlined"
              />
            </v-col>

            <v-col cols="12" sm="6" class="d-flex align-center gap-4">
              <v-switch
                v-model="assistantForm.allow_sound_alerts"
                label="Звуковые сигналы при задержках"
                density="compact"
                color="primary"
                hide-details
              />
            </v-col>
          </v-row>

          <!-- 5. ОГРАНИЧЕНИЯ, СТОРОННИЕ РЕСУРСЫ И IIKO API -->
          <div class="text-subtitle-1 font-weight-bold mb-3 mt-4 d-flex align-center gap-2">
            <v-icon size="20" icon="bx-shield" color="primary" />
            <span>5. Ограничения, сторонние ресурсы и доступ к iiko API</span>
          </div>

          <v-card variant="tonal" class="pa-4 mb-4 rounded-lg">
            <v-row dense>
              <v-col cols="12" md="6">
                <v-switch
                  v-model="assistantForm.allow_external_queries"
                  label="Разрешить запросы к сторонним ресурсам (погода, внешние данные)"
                  color="primary"
                  density="compact"
                  hide-details
                  class="mb-2"
                />
                <v-select
                  v-if="assistantForm.allow_external_queries"
                  v-model="assistantForm.allowed_external_tools"
                  :items="externalToolOptions"
                  item-value="value"
                  item-title="title"
                  multiple
                  chips
                  label="Разрешенные внешние инструменты"
                  density="compact"
                  variant="outlined"
                  class="mt-2"
                />
              </v-col>

              <v-col cols="12" md="6">
                <v-switch
                  v-model="assistantForm.allow_iiko_api_queries"
                  label="Разрешить самостоятельные запросы к iiko API"
                  color="warning"
                  density="compact"
                  hide-details
                  class="mb-2"
                />
                <v-switch
                  v-if="assistantForm.allow_iiko_api_queries"
                  v-model="assistantForm.allow_iiko_export"
                  label="Разрешить выгрузку данных и отчетов iiko"
                  color="warning"
                  density="compact"
                  hide-details
                  class="mb-2 ms-4"
                />
                <v-select
                  v-if="assistantForm.allow_iiko_api_queries"
                  v-model="assistantForm.iiko_allowed_actions"
                  :items="iikoActionOptions"
                  item-value="value"
                  item-title="title"
                  multiple
                  chips
                  label="Разрешенные действия в iiko"
                  density="compact"
                  variant="outlined"
                  class="mt-2"
                />
              </v-col>

              <v-col cols="12" class="mt-2">
                <v-switch
                  v-model="assistantForm.enable_analytics_learning"
                  label="Вести наблюдения и изучать статистику работы заведения (Zero-Token mode)"
                  color="success"
                  density="compact"
                  hide-details
                />
              </v-col>
            </v-row>
          </v-card>

          <!-- 6. ДОПОЛНИТЕЛЬНЫЙ СИСТЕМНЫЙ ПРОМПТ -->
          <div class="text-subtitle-1 font-weight-bold mb-2 mt-4 d-flex align-center gap-2">
            <v-icon size="20" icon="bx-code-block" color="primary" />
            <span>5. Дополнительные инструкции персонажу (System Prompt)</span>
          </div>

          <v-textarea
            v-model="assistantForm.system_prompt_addon"
            rows="3"
            label="Индивидуальные правила поведения или специфика заведения"
            placeholder="Следи за временем запекания горячих роллов, при задержке более 20 минут сразу предупреждай..."
            density="compact"
            variant="outlined"
          />
        </v-card-text>

        <v-divider />

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="isEditModalOpen = false">Отмена</v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            :loading="isSaving"
            @click="saveAssistant"
          >
            Сохранить помощника
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог Тестирования Помощника -->
    <v-dialog v-model="isTestChatOpen" max-width="500">
      <v-card class="rounded-xl overflow-hidden">
        <v-card-title class="pa-4 d-flex align-center justify-space-between bg-primary">
          <div class="d-flex align-center gap-2 text-white">
            <v-icon size="20" icon="bx-chat" />
            <span class="font-weight-bold">Тест диалога: {{ testAssistant?.name }}</span>
          </div>
          <v-btn icon size="small" variant="text" color="white" @click="isTestChatOpen = false">
            <v-icon size="18" icon="bx-x" />
          </v-btn>
        </v-card-title>

        <div style="height: 380px; overflow-y: auto; padding: 14px; background: rgba(0,0,0,0.1);">
          <div
            v-for="(msg, mIdx) in testChatMessages"
            :key="mIdx"
            class="assistant-msg mb-2"
            :class="msg.role === 'user' ? 'assistant-msg-user' : 'assistant-msg-bot'"
          >
            {{ msg.content }}
          </div>
          <div v-if="isTestingSending" class="assistant-msg assistant-msg-bot">
            <v-progress-circular indeterminate size="16" width="2" color="primary" />
            <span class="ml-2 text-caption">Помощник думает...</span>
          </div>
        </div>

        <v-divider />

        <div class="pa-3 d-flex align-center gap-2">
          <v-text-field
            v-model="testMessage"
            placeholder="Задать проверочный вопрос..."
            density="compact"
            variant="outlined"
            hide-details
            @keydown.enter="sendTestMessage"
          />
          <v-btn
            icon
            color="primary"
            :loading="isTestingSending"
            :disabled="!testMessage.trim()"
            @click="sendTestMessage"
          >
            <v-icon size="18" icon="bx-send" />
          </v-btn>
        </div>
      </v-card>
    </v-dialog>

    <!-- Снэкбар уведомлений -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>
