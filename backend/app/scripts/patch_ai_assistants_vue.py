file_path = "admin/resources/js/pages/settings/ai-assistants.vue"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add activeTab and analytics state
old_state_section = """// ==========================================
// СОСТОЯНИЕ
// ==========================================
const loading = ref(false)
const assistants = ref([])
const siteAgents = ref([])
const connections = ref([])"""

new_state_section = """// ==========================================
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
const aiSummaryText = ref('')"""

content = content.replace(old_state_section, new_state_section)

# 2. Update assistantForm fields with new settings
old_form_def = """const assistantForm = ref({
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
  system_prompt_addon: ''
})"""

new_form_def = """const assistantForm = ref({
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
})"""

content = content.replace(old_form_def, new_form_def)

# 3. Replace availablePages with comprehensive list
old_pages = """// Доступные страницы админки для привязки
const availablePages = [
  { value: '*', title: '⭐ Все страницы сайта и админки (*)' },
  { value: '/orders', title: '📦 Заказы (/orders)' },
  { value: '/dashboard', title: '📊 Главный дашборд (/dashboard)' },
  { value: '/kitchen', title: '🍳 Кухня и цеха (/kitchen)' },
  { value: '/employees', title: '👥 Сотрудники и смены (/employees)' },
  { value: '/pers', title: '📱 Панель сотрудников (/pers)' },
  { value: '/marketing', title: '📢 Маркетинг и рассылки (/marketing)' },
  { value: '/reports', title: '📈 Отчеты и аналитика (/reports)' }
]"""

new_pages = """// Все доступные страницы и блоки системы для привязки помощника
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
]"""

content = content.replace(old_pages, new_pages)

# 4. Update openCreateModal and openEditModal
old_modals = """// Открытие модалки создания
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
    system_prompt_addon: ''
  }
  isEditModalOpen.value = true
}

// Открытие модалки редактирования
const openEditModal = (item) => {
  formMode.value = 'edit'
  assistantForm.value = {
    ...item,
    assigned_pages: Array.isArray(item.assigned_pages) ? [...item.assigned_pages] : ['*']
  }
  isEditModalOpen.value = true
}"""

new_modals = """// Загрузка аналитики и наблюдений (Zero-Token mode)
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
}"""

content = content.replace(old_modals, new_modals)

# 5. Fix saveAssistant and toggleActive
old_save_and_toggle = """// Сохранение помощника
const saveAssistant = async () => {
  if (!assistantForm.value.name.trim() || !assistantForm.value.role_title.trim()) {
    showSnackbar('Заполните имя и роль помощника', 'warning')
    return
  }

  isSaving.value = true
  try {
    if (formMode.value === 'create') {
      const res = await axios.post('/api/v1/ai-assistants/', assistantForm.value)
      assistants.value.push(res.data)
      showSnackbar('Помощник успешно создан!')
    } else {
      const res = await axios.put(`/api/v1/ai-assistants/${assistantForm.value.id}`, assistantForm.value)
      const idx = assistants.value.findIndex(a => a.id === assistantForm.value.id)
      if (idx !== -1) assistants.value[idx] = res.data
      showSnackbar('Настройки помощника обновлены!')
    }
    isEditModalOpen.value = false
  } catch (e) {
    showSnackbar('Ошибка сохранения помощника', 'error')
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
    showSnackbar('Ошибка при удалении', 'error')
  }
}

// Быстрое переключение активности
const toggleActive = async (item) => {
  try {
    await axios.put(`/api/v1/ai-assistants/${item.id}`, { is_active: item.is_active })
    showSnackbar(`Статус помощника «${item.name}» изменен`)
  } catch (e) {
    item.is_active = !item.is_active
    showSnackbar('Ошибка изменения статуса', 'error')
  }
}"""

new_save_and_toggle = """// Сохранение помощника
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
}"""

content = content.replace(old_save_and_toggle, new_save_and_toggle)

# 6. onMounted: also call fetchAnalytics
old_mounted = """onMounted(() => {
  fetchData()
})"""

new_mounted = """onMounted(() => {
  fetchData()
  fetchAnalytics()
})"""

content = content.replace(old_mounted, new_mounted)

# 7. Add form section for restrictions, external queries & iiko API in modal
old_prompt_section_in_modal = """          <!-- 5. ДОПОЛНИТЕЛЬНЫЙ СИСТЕМНЫЙ ПРОМПТ -->"""

new_restrictions_and_prompt = """          <!-- 5. ОГРАНИЧЕНИЯ, СТОРОННИЕ РЕСУРСЫ И IIKO API -->
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

          <!-- 6. ДОПОЛНИТЕЛЬНЫЙ СИСТЕМНЫЙ ПРОМПТ -->"""

content = content.replace(old_prompt_section_in_modal, new_restrictions_and_prompt)

# 8. Add Tabs in the template header and Analytics Tab view
old_template_header_end = """      <div class="d-flex align-center gap-2">
        <v-btn
          color="primary"
          prepend-icon="bx-plus"
          elevation="2"
          @click="openCreateModal"
        >
          Создать помощника
        </v-btn>
      </div>
    </div>"""

new_template_header_tabs = """      <div class="d-flex align-center gap-2">
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
    </v-tabs>"""

content = content.replace(old_template_header_end, new_template_header_tabs)

# 9. Wrap assistants view in v-if="activeTab === 'assistants'" and add v-else analytics view
old_assistants_view_start = """    <!-- Информационные карточки статистики -->
    <v-row class="mb-6">"""

new_assistants_view_start = """    <div v-if="activeTab === 'assistants'">
    <!-- Информационные карточки статистики -->
    <v-row class="mb-6">"""

content = content.replace(old_assistants_view_start, new_assistants_view_start)

# Close the div before dialogs
old_dialogs_start = """    <!-- Модальное окно Создания / Редактирования Помощника -->"""

new_analytics_view_and_dialogs = """    </div> <!-- Конец вкладки помощников -->

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
              <div class="text-body-1" v-html="obs.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')" />
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

    <!-- Модальное окно Создания / Редактирования Помощника -->"""

content = content.replace(old_dialogs_start, new_analytics_view_and_dialogs)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("ai-assistants.vue successfully patched!")
