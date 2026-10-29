<script setup>
import { ref, onMounted, computed } from 'vue'
import '@/../styles/ai-agents.css'

// ==========================================
// СОСТОЯНИЕ И ДАННЫЕ
// ==========================================
const currentTab = ref('proxies')
const loading = ref(false)
const testingItem = ref(null)

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

const showSnackbar = (text, color = 'success') => {
  snackbar.value = { show: true, text, color }
}

// Данные с сервера
const proxies = ref([])
const connections = ref([])
const siteAgents = ref([])
const quotaPresets = ref({})

// Список моделей и состояние загрузки
const availableModelsList = ref([])
const loadingModels = ref(false)

// Модальные окна
const isProxyModalOpen = ref(false)
const isBulkProxyModalOpen = ref(false)
const isConnectionModalOpen = ref(false)

// Формы
const proxyForm = ref({
  id: null,
  name: '',
  protocol: 'socks5',
  host: '',
  port: 1080,
  username: '',
  password: '',
  priority: 10,
  is_enabled: true
})

const bulkProxyText = ref('')

const connForm = ref({
  id: null,
  name: '',
  provider_group: 'global',
  provider_type: 'gemini',
  api_key: '',
  client_id: '',
  auth_scope: '',
  base_url: '',
  default_model: 'gemini-3.1-flash-lite',
  use_proxy: true,
  pinned_proxy_id: null,
  verify_ssl: true,
  rotation_weight: 1,
  rpm_limit: 15,
  daily_requests_limit: 1500,
  daily_tokens_limit: 1000000,
  tier_key: 'free',
  extra_config: {},
  is_enabled: true
})

// Доступные данные и реестр
const dataCatalog = ref([])
const useLiveDataInSandbox = ref(true)

// Управление ролями агентов
const isAgentModalOpen = ref(false)
const agentModalMode = ref('create') // 'create' | 'edit'
const agentFormLoading = ref(false)
const agentForm = ref({
  id: null,
  agent_code: '',
  title: '',
  description: '',
  is_active: true,
  primary_connection_id: null,
  fallback_connection_id: null,
  use_gemini_pool: false,
  model_override: null,
  temperature: 0.7,
  max_tokens: 2048,
  system_prompt: '',
  selected_data_sources: ['olap_stats', 'orders']
})

// Генератор системных промптов через подключенные ИИ
const isPromptModalOpen = ref(false)
const promptGenerating = ref(false)
const promptForm = ref({
  goal: '',
  title: '',
  selected_data_sources: ['olap_stats', 'orders'],
  connection_id: null,
  current_prompt: '',
  custom_instructions: ''
})
const generatedPromptResult = ref(null)

// Песочница
const sandboxAgent = ref('stats_analyst')
const sandboxQuery = ref('')
const sandboxLoading = ref(false)
const sandboxResult = ref(null)

// ==========================================
// ВЫЧИСЛЯЕМЫЕ СВОЙСТВА ДЛЯ KPI
// ==========================================
const activeProxy = computed(() => {
  return proxies.value.find(p => p.is_active_current) || proxies.value.find(p => p.status === 'working')
})

const activeGeminiCount = computed(() => {
  return connections.value.filter(c => c.provider_type === 'gemini' && c.is_enabled).length
})

const globalConnections = computed(() => {
  return connections.value.filter(c => c.provider_group === 'global')
})

const ruConnections = computed(() => {
  return connections.value.filter(c => c.provider_group === 'ru')
})

const geminiConnections = computed(() => {
  return connections.value.filter(c => c.provider_type === 'gemini')
})

// ==========================================
// ЗАГРУЗКА ДАННЫХ
// ==========================================
const fetchAllData = async () => {
  loading.value = true
  try {
    const [pRes, cRes, aRes, qRes, dRes] = await Promise.all([
      fetch('/api/v1/ai-agents/proxies'),
      fetch('/api/v1/ai-agents/connections'),
      fetch('/api/v1/ai-agents/site-agents'),
      fetch('/api/v1/ai-agents/quota-presets'),
      fetch('/api/v1/ai-agents/data-catalog')
    ])

    if (pRes.ok) proxies.value = await pRes.json()
    if (cRes.ok) connections.value = await cRes.json()
    if (aRes.ok) siteAgents.value = await aRes.json()
    if (qRes && qRes.ok) quotaPresets.value = await qRes.json()
    if (dRes && dRes.ok) dataCatalog.value = await dRes.json()
  } catch (err) {
    showSnackbar('Ошибка загрузки настроек ИИ', 'error')
  } finally {
    loading.value = false
  }
}

const availableTiers = computed(() => {
  const ptype = connForm.value.provider_type
  if (!quotaPresets.value || !quotaPresets.value[ptype]) {
    return [{ value: 'custom', title: 'Пользовательский тариф' }]
  }
  const presets = quotaPresets.value[ptype]
  const list = Object.keys(presets).map(k => ({
    value: k,
    title: presets[k].tier_name,
    data: presets[k]
  }))
  list.push({ value: 'custom', title: 'Пользовательский (ручной ввод лимитов)' })
  return list
})

const providerTypeOptions = [
  { title: 'Groq (Ультрабыстрый LPU инференс)', value: 'groq' },
  { title: 'Cerebras (Высокоскоростной CS-3 чип)', value: 'cerebras' },
  { title: 'NVIDIA NIM (Microservices & Build AI)', value: 'nvidia' },
  { title: 'GitHub Models (Azure AI / PAT токен)', value: 'github_models' },
  { title: 'Google Gemini (Пул ключей API)', value: 'gemini' },
  { title: 'OpenAI (ChatGPT, GPT-4o, o1, o3)', value: 'openai' },
  { title: 'Anthropic Claude (Sonnet 3.5, Haiku)', value: 'anthropic' },
  { title: 'DeepSeek (DeepSeek-V3 / R1)', value: 'deepseek' },
  { title: 'OpenRouter (Шлюз всех моделей)', value: 'openrouter' },
  { title: 'Сбер GigaChat (РФ прямой канал)', value: 'gigachat' },
  { title: 'Яндекс YandexGPT (РФ прямой канал)', value: 'yandexgpt' },
  { title: 'Пользовательский OpenAI-совместимый', value: 'custom' },
]

const getProviderMeta = (type) => {
  const map = {
    gemini: { name: 'Google Gemini', icon: 'bxl-google', color: 'primary', badge: 'Gemini Пул' },
    groq: { name: 'Groq LPU', icon: 'bx-bolt-circle', color: 'warning', badge: 'Groq LPU' },
    cerebras: { name: 'Cerebras CS-3', icon: 'bx-chip', color: 'deep-purple', badge: 'CS-3 Inference' },
    nvidia: { name: 'NVIDIA NIM', icon: 'bx-microchip', color: 'success', badge: 'NVIDIA Build' },
    github_models: { name: 'GitHub Models', icon: 'bxl-github', color: 'secondary', badge: 'Azure AI' },
    openai: { name: 'OpenAI ChatGPT', icon: 'bx-bot', color: 'success', badge: 'OpenAI API' },
    anthropic: { name: 'Anthropic Claude', icon: 'bx-message-square-dots', color: 'orange', badge: 'Claude API' },
    deepseek: { name: 'DeepSeek', icon: 'bx-brain', color: 'info', badge: 'DeepSeek' },
    openrouter: { name: 'OpenRouter', icon: 'bx-network-chart', color: 'purple', badge: 'OpenRouter' },
    gigachat: { name: 'Сбер GigaChat', icon: 'bx-shield', color: 'success', badge: 'РФ Прямой канал' },
    yandexgpt: { name: 'Яндекс YandexGPT', icon: 'bx-cloud', color: 'error', badge: 'РФ Прямой канал' },
    custom: { name: 'OpenAI-Compatible', icon: 'bx-code-alt', color: 'grey', badge: 'Custom' }
  }
  return map[type] || { name: type?.toUpperCase() || 'AI', icon: 'bx-cube', color: 'primary', badge: 'Провайдер' }
}

const getApiKeyLabel = (type) => {
  if (type === 'github_models') return 'GitHub Personal Access Token (PAT) *'
  if (type === 'groq') return 'Секретный ключ Groq API (gsk_...) *'
  if (type === 'cerebras') return 'Секретный ключ Cerebras API (csk-...) *'
  if (type === 'nvidia') return 'Секретный ключ NVIDIA API (nvapi-...) *'
  return 'API Key / Secret Key *'
}

const getApiKeyPlaceholder = (type) => {
  if (type === 'github_models') return 'ghp_... или github_pat_...'
  if (type === 'groq') return 'gsk_...'
  if (type === 'cerebras') return 'csk-...'
  if (type === 'nvidia') return 'nvapi-...'
  return 'Оставьте пустым, если не меняется'
}

const getApiKeyHint = (type) => {
  if (type === 'groq') return 'Создайте бесплатный ключ в консоли Groq: console.groq.com/keys'
  if (type === 'cerebras') return 'Получите API-ключ на платформе Cerebras: cloud.cerebras.ai'
  if (type === 'nvidia') return 'Получите ключ в каталоге NVIDIA NIM: build.nvidia.com'
  if (type === 'github_models') return 'Сгенерируйте токен в GitHub: github.com/settings/tokens (права не требуются)'
  return 'Секретный ключ авторизации для обращения к API'
}

const onTierChange = (tierKey) => {
  connForm.value.tier_key = tierKey
  if (tierKey === 'custom') return
  const ptype = connForm.value.provider_type
  const preset = quotaPresets.value[ptype]?.[tierKey]
  if (preset) {
    connForm.value.rpm_limit = preset.rpm_limit
    connForm.value.daily_requests_limit = preset.daily_requests_limit
    connForm.value.daily_tokens_limit = preset.daily_tokens_limit
    connForm.value.default_model = preset.default_model
    connForm.value.extra_config = {
      ...(connForm.value.extra_config || {}),
      tier_key: preset.tier_key,
      tier_name: preset.tier_name,
      tpm_limit: preset.tpm_limit,
      description: preset.description,
      reset_interval: preset.reset_interval
    }
  }
}

const onProviderTypeChange = (newType) => {
  connForm.value.provider_type = newType
  if (newType === 'gemini') {
    connForm.value.default_model = 'gemini-3.1-flash-lite'
    connForm.value.provider_group = 'global'
    connForm.value.use_proxy = true
    connForm.value.base_url = ''
    onTierChange('free')
  } else if (newType === 'groq') {
    connForm.value.default_model = 'llama-3.3-70b-versatile'
    connForm.value.provider_group = 'global'
    connForm.value.use_proxy = true
    connForm.value.base_url = 'https://api.groq.com/openai/v1'
    onTierChange('free')
  } else if (newType === 'cerebras') {
    connForm.value.default_model = 'llama3.3-70b'
    connForm.value.provider_group = 'global'
    connForm.value.use_proxy = true
    connForm.value.base_url = 'https://api.cerebras.ai/v1'
    onTierChange('free')
  } else if (newType === 'nvidia') {
    connForm.value.default_model = 'meta/llama-3.3-70b-instruct'
    connForm.value.provider_group = 'global'
    connForm.value.use_proxy = true
    connForm.value.base_url = 'https://integrate.api.nvidia.com/v1'
    onTierChange('eval')
  } else if (newType === 'github_models') {
    connForm.value.default_model = 'gpt-4o-mini'
    connForm.value.provider_group = 'global'
    connForm.value.use_proxy = true
    connForm.value.base_url = 'https://models.inference.ai.azure.com'
    onTierChange('free')
  } else if (newType === 'openai') {
    connForm.value.default_model = 'gpt-4o-mini'
    connForm.value.provider_group = 'global'
    connForm.value.use_proxy = true
    connForm.value.base_url = 'https://api.openai.com/v1'
    onTierChange('tier1')
  } else if (newType === 'gigachat') {
    connForm.value.default_model = 'GigaChat'
    connForm.value.provider_group = 'ru'
    connForm.value.use_proxy = false
    connForm.value.base_url = ''
    connForm.value.auth_scope = 'GIGACHAT_API_PERS'
    onTierChange('pers')
  } else if (newType === 'yandexgpt') {
    connForm.value.default_model = 'yandexgpt/latest'
    connForm.value.provider_group = 'ru'
    connForm.value.use_proxy = false
    connForm.value.base_url = ''
    connForm.value.auth_scope = 'api_key'
    onTierChange('standard')
  } else {
    connForm.value.base_url = ''
    onTierChange('custom')
  }
}

// ==========================================
// ДЕЙСТВИЯ С ПРОКСИ
// ==========================================
const openAddProxy = () => {
  proxyForm.value = {
    id: null,
    name: 'Proxy #' + (proxies.value.length + 1),
    protocol: 'socks5',
    host: '',
    port: 1080,
    username: '',
    password: '',
    priority: 10,
    is_enabled: true
  }
  isProxyModalOpen.value = true
}

const editProxy = (p) => {
  proxyForm.value = { ...p }
  isProxyModalOpen.value = true
}

const saveProxy = async () => {
  try {
    const url = proxyForm.value.id 
      ? `/api/v1/ai-agents/proxies/${proxyForm.value.id}` 
      : '/api/v1/ai-agents/proxies'
    const method = proxyForm.value.id ? 'PUT' : 'POST'

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(proxyForm.value)
    })

    if (res.ok) {
      showSnackbar(proxyForm.value.id ? 'Прокси обновлен' : 'Прокси добавлен')
      isProxyModalOpen.value = false
      await fetchAllData()
    } else {
      showSnackbar('Ошибка сохранения прокси', 'error')
    }
  } catch (e) {
    showSnackbar('Ошибка сети', 'error')
  }
}

const deleteProxy = async (id) => {
  if (!confirm('Удалить этот прокси-сервер?')) return
  try {
    const res = await fetch(`/api/v1/ai-agents/proxies/${id}`, { method: 'DELETE' })
    if (res.ok) {
      showSnackbar('Прокси удален')
      await fetchAllData()
    }
  } catch (e) {
    showSnackbar('Ошибка удаления', 'error')
  }
}

const testProxy = async (id) => {
  testingItem.value = `proxy_${id}`
  try {
    const res = await fetch(`/api/v1/ai-agents/proxies/${id}/test`, { method: 'POST' })
    const data = await res.json()
    if (data.status === 'working') {
      showSnackbar(`Прокси работает! Задержка: ${data.latency_ms} мс (IP: ${data.detected_ip}, ${data.detected_country})`)
    } else {
      showSnackbar(`Ошибка прокси: ${data.last_error || 'Не отвечает'}`, 'error')
    }
    await fetchAllData()
  } catch (e) {
    showSnackbar('Ошибка проверки прокси', 'error')
  } finally {
    testingItem.value = null
  }
}

const testAllProxies = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/v1/ai-agents/proxies/test-all', { method: 'POST' })
    const data = await res.json()
    if (data.status === 'success') {
      showSnackbar(data.message, 'success')
    } else {
      showSnackbar(data.message, 'warning')
    }
    await fetchAllData()
  } catch (e) {
    showSnackbar('Ошибка массовой проверки прокси', 'error')
  } finally {
    loading.value = false
  }
}

const setProxyActive = async (id) => {
  try {
    const res = await fetch(`/api/v1/ai-agents/proxies/${id}/set-active`, { method: 'POST' })
    if (res.ok) {
      showSnackbar('Прокси назначен текущим активным')
      await fetchAllData()
    }
  } catch (e) {
    showSnackbar('Ошибка назначения прокси', 'error')
  }
}

const saveBulkProxies = async () => {
  if (!bulkProxyText.value.trim()) return
  try {
    const res = await fetch('/api/v1/ai-agents/proxies/bulk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_lines: bulkProxyText.value })
    })
    const data = await res.json()
    showSnackbar(`Добавлено прокси: ${data.added_count}`)
    bulkProxyText.value = ''
    isBulkProxyModalOpen.value = false
    await fetchAllData()
  } catch (e) {
    showSnackbar('Ошибка импорта прокси', 'error')
  }
}

// ==========================================
// ДЕЙСТВИЯ С ПОДКЛЮЧЕНИЯМИ ИИ
// ==========================================
const openAddConnection = (group = 'global', type = 'groq') => {
  const defaultTierMap = {
    gemini: 'free',
    groq: 'free',
    cerebras: 'free',
    nvidia: 'eval',
    github_models: 'free',
    openai: 'tier1',
    gigachat: 'pers',
    yandexgpt: 'standard'
  }
  const defaultTier = defaultTierMap[type] || 'free'

  const nameMap = {
    gemini: `Gemini Key #${geminiConnections.value.length + 1}`,
    groq: 'Groq Cloud LPU',
    cerebras: 'Cerebras Fast CS-3',
    nvidia: 'NVIDIA NIM API',
    github_models: 'GitHub Models (PAT)',
    openai: 'OpenAI ChatGPT',
    yandexgpt: 'YandexGPT Cloud',
    gigachat: 'Сбер GigaChat',
    anthropic: 'Anthropic Claude',
    deepseek: 'DeepSeek API',
    openrouter: 'OpenRouter'
  }

  const defaultUrlMap = {
    groq: 'https://api.groq.com/openai/v1',
    cerebras: 'https://api.cerebras.ai/v1',
    nvidia: 'https://integrate.api.nvidia.com/v1',
    github_models: 'https://models.inference.ai.azure.com',
    openai: 'https://api.openai.com/v1',
    deepseek: 'https://api.deepseek.com',
    openrouter: 'https://openrouter.ai/api/v1'
  }

  const defaultModelMap = {
    gemini: 'gemini-3.1-flash-lite',
    groq: 'llama-3.3-70b-versatile',
    cerebras: 'llama3.3-70b',
    nvidia: 'meta/llama-3.3-70b-instruct',
    github_models: 'gpt-4o-mini',
    openai: 'gpt-4o-mini',
    gigachat: 'GigaChat',
    yandexgpt: 'yandexgpt/latest',
    anthropic: 'claude-3-5-haiku-20241022',
    deepseek: 'deepseek-chat'
  }

  connForm.value = {
    id: null,
    name: nameMap[type] || `${type.toUpperCase()} Подключение`,
    provider_group: group,
    provider_type: type,
    api_key: '',
    client_id: '',
    auth_scope: type === 'gigachat' ? 'GIGACHAT_API_PERS' : (type === 'yandexgpt' ? 'api_key' : ''),
    base_url: defaultUrlMap[type] || '',
    default_model: defaultModelMap[type] || 'default',
    use_proxy: group === 'global',
    pinned_proxy_id: null,
    verify_ssl: true,
    rotation_weight: 1,
    rpm_limit: 30,
    daily_requests_limit: 1000,
    daily_tokens_limit: 1000000,
    tier_key: defaultTier,
    extra_config: { key_id: '' },
    is_enabled: true
  }
  onTierChange(defaultTier)
  
  // Базовые модели для выбранного типа
  const preset = quotaPresets.value[type]?.[defaultTier]
  availableModelsList.value = preset?.models || [connForm.value.default_model]
  
  isConnectionModalOpen.value = true
}

const editConnection = async (c) => {
  const extra = c.extra_config || {}
  connForm.value = {
    ...c,
    api_key: '', // Оставляем пустым, чтобы не перезаписывать если пользователь не меняет
    client_id: c.client_id || extra.folder_id || '',
    tier_key: extra.tier_key || (c.provider_type === 'yandexgpt' ? 'standard' : 'free'),
    extra_config: { key_id: extra.key_id || '', ...extra }
  }
  
  // Загружаем список моделей из API для этого подключения
  availableModelsList.value = [c.default_model]
  isConnectionModalOpen.value = true
  await loadModelsForConnection()
}

// Умная вставка ключей Yandex
const onYandexKeyPaste = (event, targetField) => {
  const text = (event.clipboardData || window.clipboardData)?.getData('text')?.trim()
  if (!text) return

  if (text.startsWith('b1') && text.length >= 18 && text.length <= 25) {
    connForm.value.client_id = text
    showSnackbar('Распознан Folder ID каталога Yandex Cloud', 'info')
    event.preventDefault()
  } else if (text.startsWith('aje') && text.length >= 18 && text.length <= 25) {
    if (!connForm.value.extra_config) connForm.value.extra_config = {}
    connForm.value.extra_config.key_id = text
    if (targetField === 'secret') {
      showSnackbar('Это Идентификатор API-ключа (aje...). Значение автоматически помещено в поле Key ID!', 'warning')
      event.preventDefault()
    }
  } else if (text.startsWith('AQVN') || text.length > 35) {
    connForm.value.api_key = text
    if (targetField === 'key_id') {
      showSnackbar('Это Секретный ключ (AQVN...). Значение помещено в поле Секретный ключ!', 'info')
      event.preventDefault()
    }
  }
}

const loadModelsForConnection = async () => {
  loadingModels.value = true
  try {
    if (connForm.value.id) {
      const res = await fetch(`/api/v1/ai-agents/connections/${connForm.value.id}/models`)
      if (res.ok) {
        const list = await res.json()
        if (list && list.length > 0) {
          availableModelsList.value = list
          showSnackbar(`Загружено ${list.length} моделей из API`)
          return
        }
      }
    }
    // Preview запрос
    const res = await fetch('/api/v1/ai-agents/models/fetch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider_type: connForm.value.provider_type,
        provider_group: connForm.value.provider_group,
        api_key: connForm.value.api_key,
        base_url: connForm.value.base_url,
        pinned_proxy_id: connForm.value.pinned_proxy_id
      })
    })
    if (res.ok) {
      const list = await res.json()
      if (list && list.length > 0) {
        availableModelsList.value = list
        showSnackbar(`Загружено ${list.length} моделей`)
      }
    }
  } catch (e) {
    showSnackbar('Ошибка загрузки моделей из API', 'warning')
  } finally {
    loadingModels.value = false
  }
}

// Список доступных моделей для функционального агента
const getAgentAvailableModels = (agent) => {
  let targetConn = null
  if (agent?.primary_connection_id) {
    targetConn = connections.value.find(c => c.id === agent.primary_connection_id)
  }
  if (!targetConn && connections.value.length > 0) {
    targetConn = connections.value[0]
  }

  const ptype = targetConn?.provider_type || 'gemini'
  const presetModels = quotaPresets.value?.[ptype]?.free?.models || quotaPresets.value?.[ptype]?.standard?.models || quotaPresets.value?.[ptype]?.tier1?.models || []
  
  const modelsSet = new Set(presetModels)
  if (targetConn?.default_model) {
    modelsSet.add(targetConn.default_model)
  }
  if (agent?.model_override) {
    modelsSet.add(agent.model_override)
  }

  return Array.from(modelsSet)
}

const saveConnection = async () => {
  // Валидация перед сохранением для YandexGPT
  if (connForm.value.provider_type === 'yandexgpt') {
    const fId = (connForm.value.client_id || (connForm.value.extra_config && connForm.value.extra_config.folder_id) || '').trim()
    if (!fId) {
      showSnackbar('Для YandexGPT обязателен Folder ID каталога (например: b1g...)!', 'error')
      return
    }
    if (!connForm.value.id && !connForm.value.api_key.trim()) {
      showSnackbar('Укажите Секретный ключ (Secret Key) API Yandex Cloud!', 'error')
      return
    }
  }

  try {
    const url = connForm.value.id 
      ? `/api/v1/ai-agents/connections/${connForm.value.id}` 
      : '/api/v1/ai-agents/connections'
    const method = connForm.value.id ? 'PUT' : 'POST'

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(connForm.value)
    })

    if (res.ok) {
      showSnackbar(connForm.value.id ? 'Подключение обновлено' : 'Подключение создано')
      isConnectionModalOpen.value = false
      await fetchAllData()
    } else {
      const err = await res.json()
      showSnackbar(err.detail || 'Ошибка сохранения подключения', 'error')
    }
  } catch (e) {
    showSnackbar('Ошибка сети при сохранении', 'error')
  }
}

const deleteConnection = async (id) => {
  if (!confirm('Удалить это подключение к ИИ?')) return
  try {
    const res = await fetch(`/api/v1/ai-agents/connections/${id}`, { method: 'DELETE' })
    if (res.ok) {
      showSnackbar('Подключение удалено')
      await fetchAllData()
    }
  } catch (e) {
    showSnackbar('Ошибка удаления', 'error')
  }
}

const testConnection = async (id) => {
  testingItem.value = `conn_${id}`
  try {
    const res = await fetch(`/api/v1/ai-agents/connections/${id}/test`, { method: 'POST' })
    const data = await res.json()
    if (data.success) {
      showSnackbar(`Успешно! Ответ модели за ${data.latency_ms} мс: "${data.message}"`)
    } else {
      showSnackbar(`Ошибка проверки: ${data.message}`, 'error')
    }
    await fetchAllData()
  } catch (e) {
    showSnackbar('Ошибка при тестировании API', 'error')
  } finally {
    testingItem.value = null
  }
}

// ==========================================
// ДЕЙСТВИЯ С АГЕНТАМИ САЙТА И ИСТОЧНИКАМИ ДАННЫХ
// ==========================================
const isSystemAgent = (agent) => {
  const code = typeof agent === 'string' ? agent : (agent?.agent_code || '')
  return ['stats_analyst', 'feedback_nps', 'site_manager'].includes(code)
}

const getAgentSources = (agent) => {
  if (agent?.permissions_config?.data_sources && Array.isArray(agent.permissions_config.data_sources)) {
    return agent.permissions_config.data_sources
  }
  const code = agent?.agent_code || ''
  if (code === 'stats_analyst') return ['olap_stats', 'orders']
  if (code === 'feedback_nps') return ['nps_reviews', 'orders']
  if (code === 'site_manager') return ['menu_catalog', 'orders']
  return ['olap_stats', 'orders', 'menu_catalog']
}

const getSourceMeta = (srcId) => {
  return dataCatalog.value.find(s => s.id === srcId) || {
    id: srcId,
    name: srcId,
    icon: 'bx-data',
    badge_color: 'primary'
  }
}

const openCreateAgent = () => {
  agentModalMode.value = 'create'
  agentForm.value = {
    id: null,
    agent_code: '',
    title: '',
    description: '',
    is_active: true,
    primary_connection_id: connections.value.find(c => c.is_enabled)?.id || null,
    fallback_connection_id: null,
    use_gemini_pool: true,
    model_override: null,
    temperature: 0.7,
    max_tokens: 2048,
    system_prompt: '',
    selected_data_sources: ['olap_stats', 'orders', 'menu_catalog']
  }
  isAgentModalOpen.value = true
}

const openEditAgent = (agent) => {
  agentModalMode.value = 'edit'
  const sources = getAgentSources(agent)
  agentForm.value = {
    ...agent,
    selected_data_sources: [...sources]
  }
  isAgentModalOpen.value = true
}

const toggleSourceInAgentForm = (srcId) => {
  const idx = agentForm.value.selected_data_sources.indexOf(srcId)
  if (idx > -1) {
    agentForm.value.selected_data_sources.splice(idx, 1)
  } else {
    agentForm.value.selected_data_sources.push(srcId)
  }
}

const toggleSourceInPromptForm = (srcId) => {
  const idx = promptForm.value.selected_data_sources.indexOf(srcId)
  if (idx > -1) {
    promptForm.value.selected_data_sources.splice(idx, 1)
  } else {
    promptForm.value.selected_data_sources.push(srcId)
  }
}

const saveAgentModal = async () => {
  if (!agentForm.value.title.trim()) {
    showSnackbar('Укажите название агента', 'error')
    return
  }
  agentFormLoading.value = true
  try {
    const payload = {
      agent_code: agentForm.value.agent_code,
      title: agentForm.value.title,
      description: agentForm.value.description,
      is_active: agentForm.value.is_active,
      primary_connection_id: agentForm.value.primary_connection_id,
      fallback_connection_id: agentForm.value.fallback_connection_id,
      use_gemini_pool: agentForm.value.use_gemini_pool,
      model_override: agentForm.value.model_override,
      temperature: agentForm.value.temperature,
      max_tokens: agentForm.value.max_tokens,
      system_prompt: agentForm.value.system_prompt,
      permissions_config: {
        ...(agentForm.value.permissions_config || {}),
        data_sources: agentForm.value.selected_data_sources,
        is_custom: !isSystemAgent(agentForm.value)
      }
    }

    let res
    if (agentModalMode.value === 'create') {
      res = await fetch('/api/v1/ai-agents/site-agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
    } else {
      res = await fetch(`/api/v1/ai-agents/site-agents/${agentForm.value.agent_code}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
    }

    if (res.ok) {
      showSnackbar(`Агент «${agentForm.value.title}» успешно сохранен!`, 'success')
      isAgentModalOpen.value = false
      await fetchAllData()
    } else {
      const err = await res.json()
      showSnackbar(err.detail || 'Ошибка сохранения агента', 'error')
    }
  } catch (e) {
    showSnackbar('Ошибка сервера при сохранении агента', 'error')
  } finally {
    agentFormLoading.value = false
  }
}

const deleteSiteAgent = async (agent) => {
  if (isSystemAgent(agent)) {
    showSnackbar('Системных агентов нельзя удалить (можно деактивировать переключателем)', 'warning')
    return
  }
  if (!confirm(`Вы действительно хотите удалить агента «${agent.title}»?`)) return
  try {
    const res = await fetch(`/api/v1/ai-agents/site-agents/${agent.agent_code}`, {
      method: 'DELETE'
    })
    if (res.ok) {
      showSnackbar(`Агент «${agent.title}» удален`)
      if (sandboxAgent.value === agent.agent_code) {
        sandboxAgent.value = 'stats_analyst'
      }
      await fetchAllData()
    } else {
      const err = await res.json()
      showSnackbar(err.detail || 'Не удалось удалить агента', 'error')
    }
  } catch (e) {
    showSnackbar('Ошибка связи с сервером', 'error')
  }
}

const saveSiteAgent = async (agent) => {
  try {
    const res = await fetch(`/api/v1/ai-agents/site-agents/${agent.agent_code}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(agent)
    })
    if (res.ok) {
      showSnackbar(`Настройки агента «${agent.title}» сохранены`)
    } else {
      showSnackbar('Ошибка сохранения агента', 'error')
    }
  } catch (e) {
    showSnackbar('Ошибка сети', 'error')
  }
}

// ==========================================
// ГЕНЕРАТОР ПРОМПТОВ ЧЕРЕЗ ПОДКЛЮЧЕННЫЕ ИИ
// ==========================================
const openPromptGenerator = (targetAgent = null) => {
  const ag = targetAgent || (isAgentModalOpen.value ? agentForm.value : null)
  promptForm.value = {
    goal: '',
    title: ag?.title || '',
    selected_data_sources: ag ? getAgentSources(ag) : ['olap_stats', 'orders', 'menu_catalog'],
    connection_id: ag?.primary_connection_id || null,
    current_prompt: ag?.system_prompt || '',
    custom_instructions: ''
  }
  generatedPromptResult.value = null
  isPromptModalOpen.value = true
}

const runGeneratePrompt = async () => {
  if (!promptForm.value.goal.trim() && !promptForm.value.current_prompt.trim()) {
    showSnackbar('Опишите задачу или цель агента своими словами', 'warning')
    return
  }
  promptGenerating.value = true
  try {
    const res = await fetch('/api/v1/ai-agents/generate-prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(promptForm.value)
    })
    const data = await res.json()
    if (res.ok) {
      generatedPromptResult.value = data
      showSnackbar('Системный промпт успешно составлен ИИ без ограничений!')
    } else {
      showSnackbar(data.detail || 'Ошибка генерации промпта', 'error')
    }
  } catch (e) {
    showSnackbar('Ошибка сервера при генерации промпта', 'error')
  } finally {
    promptGenerating.value = false
  }
}

const applyGeneratedPrompt = () => {
  if (!generatedPromptResult.value) return
  const res = generatedPromptResult.value
  agentForm.value.system_prompt = res.system_prompt
  if (res.title && (!agentForm.value.title || agentModalMode.value === 'create')) {
    agentForm.value.title = res.title
  }
  if (res.agent_code && (!agentForm.value.agent_code || agentModalMode.value === 'create')) {
    agentForm.value.agent_code = res.agent_code
  }
  if (res.description && (!agentForm.value.description || agentModalMode.value === 'create')) {
    agentForm.value.description = res.description
  }
  if (res.recommended_data_sources && res.recommended_data_sources.length > 0) {
    agentForm.value.selected_data_sources = [...res.recommended_data_sources]
  }
  isPromptModalOpen.value = false
  isAgentModalOpen.value = true
  showSnackbar('Сгенерированный промпт и параметры применены к агенту!')
}

// ==========================================
// ПЕСОЧНИЦА (ТЕСТ РАБОТЫ АГЕНТОВ)
// ==========================================
const setSandboxPreset = (code, query) => {
  sandboxAgent.value = code
  sandboxQuery.value = query
}

const runSandboxQuery = async () => {
  if (!sandboxQuery.value.trim()) return
  sandboxLoading.value = true
  sandboxResult.value = null

  try {
    const res = await fetch('/api/v1/ai-agents/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_code: sandboxAgent.value,
        query: sandboxQuery.value,
        use_live_data: useLiveDataInSandbox.value
      })
    })

    const data = await res.json()
    if (res.ok) {
      sandboxResult.value = data
      showSnackbar('Запрос успешно выполнен агентом с данными сайта')
    } else {
      showSnackbar(data.detail || 'Ошибка выполнения запроса', 'error')
    }
  } catch (err) {
    showSnackbar('Ошибка связи с сервером', 'error')
  } finally {
    sandboxLoading.value = false
  }
}

onMounted(() => {
  fetchAllData()
})
</script>

<template>
  <div class="ai-agents-container">
    <!-- Верхняя панель KPI -->
    <VRow class="mb-4">
      <VCol cols="12" sm="6" md="3">
        <VCard class="ai-kpi-card pa-4">
          <div class="d-flex align-center">
            <div class="ai-kpi-icon-wrap bg-primary-lighten-5 text-primary me-3">
              <i class="bx bx-globe"></i>
            </div>
            <div>
              <div class="text-caption text-medium-emphasis">Активный прокси</div>
              <div class="text-body-1 font-weight-bold text-truncate" style="max-width: 170px;">
                <span v-if="activeProxy">
                  <span class="proxy-status-dot proxy-status-dot--working"></span>
                  {{ activeProxy.name }}
                </span>
                <span v-else class="text-grey">Не выбран</span>
              </div>
            </div>
          </div>
        </VCard>
      </VCol>

      <VCol cols="12" sm="6" md="3">
        <VCard class="ai-kpi-card pa-4">
          <div class="d-flex align-center">
            <div class="ai-kpi-icon-wrap bg-info-lighten-5 text-info me-3">
              <i class="bx bxl-google"></i>
            </div>
            <div>
              <div class="text-caption text-medium-emphasis">Пул Gemini (Ключи)</div>
              <div class="text-h6 font-weight-bold">{{ activeGeminiCount }} активных</div>
            </div>
          </div>
        </VCard>
      </VCol>

      <VCol cols="12" sm="6" md="3">
        <VCard class="ai-kpi-card pa-4">
          <div class="d-flex align-center">
            <div class="ai-kpi-icon-wrap bg-success-lighten-5 text-success me-3">
              <i class="bx bx-shield-quarter"></i>
            </div>
            <div>
              <div class="text-caption text-medium-emphasis">РФ ИИ (Без прокси)</div>
              <div class="text-h6 font-weight-bold">{{ ruConnections.length }} подключено</div>
            </div>
          </div>
        </VCard>
      </VCol>

      <VCol cols="12" sm="6" md="3">
        <VCard class="ai-kpi-card pa-4">
          <div class="d-flex align-center">
            <div class="ai-kpi-icon-wrap bg-warning-lighten-5 text-warning me-3">
              <i class="bx bx-bot"></i>
            </div>
            <div>
              <div class="text-caption text-medium-emphasis">Роли агентов сайта</div>
              <div class="text-h6 font-weight-bold">{{ siteAgents.filter(a => a.is_active).length }} из {{ siteAgents.length }} активны</div>
            </div>
          </div>
        </VCard>
      </VCol>
    </VRow>

    <!-- Главная карточка с табами -->
    <VCard>
      <VTabs v-model="currentTab" bg-color="surface">
        <VTab value="proxies"><i class="bx bx-network-chart me-2"></i> Прокси (HTTPS/SOCKS5)</VTab>
        <VTab value="gemini"><i class="bx bxl-google me-2"></i> Google Gemini (Мульти-Агент)</VTab>
        <VTab value="global"><i class="bx bx-world me-2"></i> Мировые ИИ (OpenAI, Claude)</VTab>
        <VTab value="ru"><i class="bx bx-flag me-2"></i> РФ ИИ (Сбер, Яндекс — Прямой канал)</VTab>
        <VTab value="agents"><i class="bx bx-brain me-2"></i> Роли сайта и Песочница</VTab>
      </VTabs>

      <VDivider />

      <VCardText class="pa-6">
        <VWindow v-model="currentTab">
          <!-- ---------------------------------------------------- -->
          <!-- ВКЛАДКА 1: ПУЛ ПРОКСИ-СЕРВЕРОВ                        -->
          <!-- ---------------------------------------------------- -->
          <VWindowItem value="proxies">
            <div class="d-flex flex-wrap justify-space-between align-center mb-4 gap-2">
              <div>
                <h3 class="text-h6 font-weight-bold">Пул прокси-серверов для мировых ИИ</h3>
                <p class="text-caption text-medium-emphasis mb-0">
                  Поддерживает HTTPS и SOCKS5 прокси. Система автоматически подбирает рабочий прокси с минимальным пингом.
                </p>
              </div>
              <div class="d-flex gap-2">
                <VBtn color="primary" variant="tonal" prepend-icon="bx-refresh" :loading="loading" @click="testAllProxies">
                  Проверить все и подобрать лучший
                </VBtn>
                <VBtn color="secondary" variant="outlined" prepend-icon="bx-upload" @click="isBulkProxyModalOpen = true">
                  Массовый импорт
                </VBtn>
                <VBtn color="primary" prepend-icon="bx-plus" @click="openAddProxy">
                  Добавить прокси
                </VBtn>
              </div>
            </div>

            <VTable class="border rounded">
              <thead>
                <tr>
                  <th>Статус</th>
                  <th>Название</th>
                  <th>Протокол</th>
                  <th>Хост : Порт</th>
                  <th>Локация / IP</th>
                  <th>Пинг</th>
                  <th>Приоритет</th>
                  <th>Активен</th>
                  <th class="text-end">Действия</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="proxies.length === 0">
                  <td colspan="9" class="text-center py-6 text-grey">
                    Прокси-серверы еще не добавлены. Добавьте хотя бы один SOCKS5 или HTTPS прокси для работы Gemini и OpenAI.
                  </td>
                </tr>
                <tr v-for="p in proxies" :key="p.id">
                  <td>
                    <span :class="['proxy-status-dot', p.status === 'working' ? 'proxy-status-dot--working' : (p.status === 'failed' ? 'proxy-status-dot--failed' : 'proxy-status-dot--untested')]"></span>
                    <VChip v-if="p.is_active_current" size="x-small" color="success" class="ms-1">АКТИВНЫЙ</VChip>
                  </td>
                  <td class="font-weight-medium">{{ p.name }}</td>
                  <td><VChip size="small" variant="tonal" color="info">{{ p.protocol.toUpperCase() }}</VChip></td>
                  <td><code>{{ p.host }}:{{ p.port }}</code></td>
                  <td>
                    <span v-if="p.detected_ip">{{ p.detected_country || 'Мир' }} ({{ p.detected_ip }})</span>
                    <span v-else class="text-grey-lighten-1">Не проверен</span>
                  </td>
                  <td>
                    <span v-if="p.latency_ms" class="text-success font-weight-medium">{{ p.latency_ms }} мс</span>
                    <span v-else class="text-grey-lighten-1">–</span>
                  </td>
                  <td>{{ p.priority }}</td>
                  <td>
                    <VSwitch v-model="p.is_enabled" color="primary" density="compact" hide-details @update:model-value="saveProxyDirect(p)" />
                  </td>
                  <td class="text-end">
                    <VBtn icon="bx-check-circle" size="small" variant="text" color="success" title="Сделать основным" @click="setProxyActive(p.id)" />
                    <VBtn icon="bx-play" size="small" variant="text" color="primary" title="Проверить пинг" :loading="testingItem === `proxy_${p.id}`" @click="testProxy(p.id)" />
                    <VBtn icon="bx-edit" size="small" variant="text" color="secondary" title="Редактировать" @click="editProxy(p)" />
                    <VBtn icon="bx-trash" size="small" variant="text" color="error" title="Удалить" @click="deleteProxy(p.id)" />
                  </td>
                </tr>
              </tbody>
            </VTable>
          </VWindowItem>

          <!-- ---------------------------------------------------- -->
          <!-- ВКЛАДКА 2: GOOGLE GEMINI (МУЛЬТИ-АГЕНТ)             -->
          <!-- ---------------------------------------------------- -->
          <VWindowItem value="gemini">
            <div class="d-flex justify-space-between align-center mb-4">
              <div>
                <h3 class="text-h6 font-weight-bold">Google Gemini (Мульти-подключения и Пул ключей)</h3>
                <p class="text-caption text-medium-emphasis mb-0">
                  Добавьте несколько ключей Gemini API. Система автоматически балансирует нагрузку и переключается на запасной ключ при исчерпании лимитов.
                </p>
              </div>
              <VBtn color="primary" prepend-icon="bx-plus" @click="openAddConnection('global', 'gemini')">
                Добавить ключ Gemini
              </VBtn>
            </div>

            <VRow>
              <VCol v-if="geminiConnections.length === 0" cols="12">
                <VAlert type="info" variant="tonal" class="mb-4">
                  Подключения Google Gemini еще не настроены. Нажмите «Добавить ключ Gemini», чтобы подключить модель (например, gemini-2.5-flash или gemini-3.8-flash-lite).
                </VAlert>
              </VCol>

              <VCol v-for="c in geminiConnections" :key="c.id" cols="12" md="6">
                <VCard class="ai-provider-card pa-4" :class="{ 'is-active': c.is_enabled }">
                  <div class="d-flex justify-space-between align-center mb-3">
                    <div class="d-flex align-center">
                      <VAvatar color="primary-lighten-5" class="text-primary me-3" size="40">
                        <i class="bx bxl-google text-h5"></i>
                      </VAvatar>
                      <div>
                        <div class="font-weight-bold text-subtitle-1">{{ c.name }}</div>
                        <div class="text-caption text-grey">Модель: <strong>{{ c.default_model }}</strong></div>
                      </div>
                    </div>
                    <VSwitch v-model="c.is_enabled" color="primary" density="compact" hide-details @update:model-value="toggleConnectionDirect(c)" />
                  </div>

                  <VDivider class="my-2" />

                  <div class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">API Key:</span>
                    <code>{{ c.api_key_masked || 'Ключ сохранен' }}</code>
                  </div>
                  <div class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">Маршрут прокси:</span>
                    <span class="text-primary">
                      {{ c.pinned_proxy_id ? 'Привязан конкретный' : 'Активный из пула' }}
                    </span>
                  </div>
                  <div class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">Лимиты тарифа:</span>
                    <span class="font-weight-medium">{{ c.rpm_limit || 0 }} RPM | {{ c.daily_requests_limit || 0 }} RPD</span>
                  </div>
                  <div class="d-flex justify-space-between align-center text-caption py-1">
                    <span class="text-grey">Сброс лимитов:</span>
                    <VChip v-if="c.is_reset_renewable" size="x-small" color="primary" variant="tonal">
                      <i class="bx bx-time-five me-1"></i> {{ c.limits_reset_display }}
                    </VChip>
                    <VChip v-else size="x-small" color="secondary" variant="outlined">
                      <i class="bx bx-infinite me-1"></i> n/a
                    </VChip>
                  </div>
                  <div class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">Статистика:</span>
                    <span>{{ c.total_requests }} запросов ({{ c.total_tokens }} токенов)</span>
                  </div>

                  <div class="d-flex justify-space-between align-center mt-3 pt-2 border-t">
                    <VChip size="small" :color="c.status === 'connected' ? 'success' : (c.status === 'error' ? 'error' : 'secondary')" variant="tonal">
                      {{ c.status === 'connected' ? 'Подключен' : (c.status === 'error' ? 'Ошибка' : 'Не проверен') }}
                    </VChip>
                    <div class="d-flex gap-1">
                      <VBtn size="small" variant="tonal" color="primary" :loading="testingItem === `conn_${c.id}`" @click="testConnection(c.id)">
                        Проверить API
                      </VBtn>
                      <VBtn size="small" icon="bx-edit" variant="text" color="secondary" @click="editConnection(c)" />
                      <VBtn size="small" icon="bx-trash" variant="text" color="error" @click="deleteConnection(c.id)" />
                    </div>
                  </div>
                </VCard>
              </VCol>
            </VRow>
          </VWindowItem>

          <!-- ---------------------------------------------------- -->
          <!-- ВКЛАДКА 3: МИРОВЫЕ ИИ (OPENAI, CLAUDE И ДР.)         -->
          <!-- ---------------------------------------------------- -->
          <VWindowItem value="global">
            <div class="d-flex flex-wrap justify-space-between align-center mb-4 gap-2">
              <div>
                <h3 class="text-h6 font-weight-bold">Мировые ИИ-провайдеры (Работа через прокси)</h3>
                <p class="text-caption text-medium-emphasis mb-0">
                  Groq, Cerebras, NVIDIA NIM, GitHub Models, OpenAI, Anthropic, DeepSeek. Автоматическая маршрутизация через активный прокси.
                </p>
              </div>
              <div class="d-flex flex-wrap gap-2">
                <VBtn color="warning" variant="tonal" prepend-icon="bx-bolt-circle" @click="openAddConnection('global', 'groq')">
                  + Groq
                </VBtn>
                <VBtn color="deep-purple" variant="tonal" prepend-icon="bx-chip" @click="openAddConnection('global', 'cerebras')">
                  + Cerebras
                </VBtn>
                <VBtn color="success" variant="tonal" prepend-icon="bx-microchip" @click="openAddConnection('global', 'nvidia')">
                  + NVIDIA NIM
                </VBtn>
                <VBtn color="secondary" variant="tonal" prepend-icon="bxl-github" @click="openAddConnection('global', 'github_models')">
                  + GitHub Models
                </VBtn>
                <VBtn color="primary" prepend-icon="bx-plus" @click="openAddConnection('global', 'openai')">
                  Другой ИИ
                </VBtn>
              </div>
            </div>

            <VRow>
              <VCol v-if="globalConnections.filter(x => x.provider_type !== 'gemini').length === 0" cols="12">
                <VAlert type="info" variant="tonal">
                  Пока нет подключенных мировых провайдеров. Нажмите на любую из кнопок выше (+ Groq, + Cerebras, + NVIDIA NIM, + GitHub Models), чтобы добавить высокоскоростной ИИ!
                </VAlert>
              </VCol>

              <VCol v-for="c in globalConnections.filter(x => x.provider_type !== 'gemini')" :key="c.id" cols="12" md="6">
                <VCard class="ai-provider-card pa-4" :class="{ 'is-active': c.is_enabled }">
                  <div class="d-flex justify-space-between align-center mb-2">
                    <div class="d-flex align-center">
                      <VAvatar :color="`${getProviderMeta(c.provider_type).color}-lighten-5`" :class="`text-${getProviderMeta(c.provider_type).color} me-3`" size="42">
                        <i :class="['bx text-h5', getProviderMeta(c.provider_type).icon]"></i>
                      </VAvatar>
                      <div>
                        <div class="font-weight-bold text-subtitle-1 d-flex align-center gap-2">
                          {{ c.name }}
                          <VChip size="x-small" :color="getProviderMeta(c.provider_type).color" variant="tonal">
                            {{ getProviderMeta(c.provider_type).badge }}
                          </VChip>
                        </div>
                        <div class="text-caption text-grey">Модель: <strong>{{ c.default_model }}</strong></div>
                      </div>
                    </div>
                    <VSwitch v-model="c.is_enabled" color="primary" density="compact" hide-details @update:model-value="toggleConnectionDirect(c)" />
                  </div>

                  <VDivider class="my-2" />

                  <div class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">API Key:</span>
                    <code>{{ c.api_key_masked || 'Ключ задан' }}</code>
                  </div>
                  <div class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">Endpoint URL:</span>
                    <span class="text-truncate font-mono" style="max-width: 260px;">{{ c.base_url || 'Стандартный URL' }}</span>
                  </div>
                  <div class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">Лимиты тарифа:</span>
                    <span class="font-weight-medium">
                      {{ c.rpm_limit || 0 }} RPM | {{ c.daily_requests_limit || 0 }} RPD
                    </span>
                  </div>
                  <div class="d-flex justify-space-between align-center text-caption py-1">
                    <span class="text-grey">Сброс лимитов:</span>
                    <VChip v-if="c.is_reset_renewable" size="x-small" color="primary" variant="tonal">
                      <i class="bx bx-time-five me-1"></i> {{ c.limits_reset_display }}
                    </VChip>
                    <VChip v-else size="x-small" color="secondary" variant="outlined">
                      <i class="bx bx-infinite me-1"></i> n/a
                    </VChip>
                  </div>
                  <div class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">Запросов сегодня:</span>
                    <span>{{ c.today_requests || 0 }} из {{ c.daily_requests_limit || 0 }} (осталось: {{ c.remaining_requests || 0 }})</span>
                  </div>

                  <div class="d-flex justify-space-between align-center mt-3 pt-2 border-t">
                    <VChip size="small" :color="c.status === 'connected' ? 'success' : (c.status === 'error' ? 'error' : 'secondary')" variant="tonal">
                      {{ c.status === 'connected' ? 'Подключен' : (c.status === 'error' ? 'Ошибка' : 'Не проверен') }}
                    </VChip>
                    <div class="d-flex gap-1">
                      <VBtn size="small" variant="tonal" color="primary" :loading="testingItem === `conn_${c.id}`" @click="testConnection(c.id)">
                        Проверить
                      </VBtn>
                      <VBtn size="small" icon="bx-edit" variant="text" color="secondary" @click="editConnection(c)" />
                      <VBtn size="small" icon="bx-trash" variant="text" color="error" @click="deleteConnection(c.id)" />
                    </div>
                  </div>
                </VCard>
              </VCol>
            </VRow>
          </VWindowItem>

          <!-- ---------------------------------------------------- -->
          <!-- ВКЛАДКА 4: РОССИЙСКИЕ ИИ (ПРЯМОЙ КАНАЛ)              -->
          <!-- ---------------------------------------------------- -->
          <VWindowItem value="ru">
            <div class="ru-direct-banner d-flex align-center">
              <i class="bx bx-shield-check text-h5 text-primary me-3"></i>
              <div>
                <div class="font-weight-bold text-subtitle-2">Прямой защищенный канал связи РФ (МИНУЯ ПРОКСИ)</div>
                <div class="text-caption">
                  Запросы к Сбер GigaChat, Яндекс YandexGPT и другим российским сервисам отправляются напрямую с VPS-сервера в России без использования зарубежных прокси.
                </div>
              </div>
            </div>

            <div class="d-flex justify-space-between align-center mb-4">
              <h3 class="text-h6 font-weight-bold">Российские ИИ-агенты</h3>
              <div class="d-flex gap-2">
                <VBtn color="success" prepend-icon="bx-plus" @click="openAddConnection('ru', 'gigachat')">
                  Добавить Сбер GigaChat
                </VBtn>
                <VBtn color="primary" prepend-icon="bx-plus" @click="openAddConnection('ru', 'yandexgpt')">
                  Добавить YandexGPT
                </VBtn>
              </div>
            </div>

            <VRow>
              <VCol v-for="c in ruConnections" :key="c.id" cols="12" md="6">
                <VCard class="ai-provider-card pa-4" :class="{ 'is-active': c.is_enabled }">
                  <div class="d-flex justify-space-between align-center mb-2">
                    <div class="d-flex align-center">
                      <VAvatar :color="c.provider_type === 'gigachat' ? 'success-lighten-5' : 'error-lighten-5'" class="me-3" size="40">
                        <i :class="['bx text-h5', c.provider_type === 'gigachat' ? 'bx-brain text-success' : 'bx-cloud text-error']"></i>
                      </VAvatar>
                      <div>
                        <div class="font-weight-bold text-subtitle-1">{{ c.name }}</div>
                        <div class="text-caption text-grey">{{ c.provider_type.toUpperCase() }} — {{ c.default_model }}</div>
                      </div>
                    </div>
                    <VSwitch v-model="c.is_enabled" color="success" density="compact" hide-details @update:model-value="toggleConnectionDirect(c)" />
                  </div>
                  <VDivider class="my-2" />
                  <div class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">Канал:</span>
                    <strong class="text-success">Прямой (без прокси)</strong>
                  </div>
                  <div v-if="c.client_id" class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">{{ c.provider_type === 'yandexgpt' ? 'Folder ID:' : 'Client ID:' }}</span>
                    <code>{{ c.client_id }}</code>
                  </div>
                  <div v-if="c.extra_config && c.extra_config.key_id" class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">Key ID:</span>
                    <code>{{ c.extra_config.key_id }}</code>
                  </div>
                  <div v-if="c.api_key_masked" class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">{{ c.provider_type === 'yandexgpt' ? 'Секретный ключ:' : 'API Key:' }}</span>
                    <code>{{ c.api_key_masked }}</code>
                  </div>
                  <div v-if="c.auth_scope" class="d-flex justify-space-between text-caption py-1">
                    <span class="text-grey">Scope / Тип:</span>
                    <span>{{ c.auth_scope }}</span>
                  </div>
                  <div class="d-flex justify-space-between align-center mt-3 pt-2 border-t">
                    <VChip size="small" :color="c.status === 'connected' ? 'success' : (c.status === 'error' ? 'error' : 'secondary')" variant="tonal">
                      {{ c.status === 'connected' ? 'Подключен' : (c.status === 'error' ? 'Ошибка' : 'Не проверен') }}
                    </VChip>
                    <div class="d-flex gap-1">
                      <VBtn size="small" variant="tonal" color="success" :loading="testingItem === `conn_${c.id}`" @click="testConnection(c.id)">
                        Проверить API
                      </VBtn>
                      <VBtn size="small" icon="bx-edit" variant="text" color="secondary" @click="editConnection(c)" />
                      <VBtn size="small" icon="bx-trash" variant="text" color="error" @click="deleteConnection(c.id)" />
                    </div>
                  </div>
                </VCard>
              </VCol>
            </VRow>
          </VWindowItem>

          <!-- ---------------------------------------------------- -->
          <!-- ВКЛАДКА 5: РОЛИ САЙТА И ПЕСОЧНИЦА                    -->
          <!-- ---------------------------------------------------- -->
          <VWindowItem value="agents">
            <div class="mb-6">
              <div class="d-flex flex-wrap justify-space-between align-center mb-3 gap-2">
                <div>
                  <h3 class="text-h6 font-weight-bold mb-1">Функциональные агенты сайта FoodTech</h3>
                  <p class="text-caption text-medium-emphasis mb-0">
                    Создавайте роли агентов, подключайте доступные данные системы (OLAP, заказы, клиенты, отзывы, меню) и пишите промпты с помощью подключенных ИИ без ограничений.
                  </p>
                </div>
                <div class="d-flex gap-2">
                  <VBtn color="primary" prepend-icon="bx-plus" @click="openCreateAgent">
                    Создать агента
                  </VBtn>
                  <VBtn variant="tonal" icon="bx-refresh" :loading="loading" @click="fetchAllData" title="Обновить список" />
                </div>
              </div>

              <!-- Сетка карточек агентов -->
              <VRow>
                <VCol v-for="agent in siteAgents" :key="agent.agent_code" cols="12" md="6" lg="4">
                  <VCard class="border pa-4 h-100 d-flex flex-column justify-space-between ai-provider-card" :class="{ 'is-active': agent.is_active }">
                    <div>
                      <div class="d-flex justify-space-between align-start mb-2">
                        <div>
                          <div class="d-flex align-center gap-1 mb-1">
                            <VChip size="x-small" :color="isSystemAgent(agent) ? 'primary' : 'info'" variant="tonal">
                              {{ isSystemAgent(agent) ? 'Системный' : 'Кастомный' }}
                            </VChip>
                            <code class="text-caption text-grey">@{{ agent.agent_code }}</code>
                          </div>
                          <div class="font-weight-bold text-subtitle-1">{{ agent.title }}</div>
                        </div>
                        <VSwitch v-model="agent.is_active" color="primary" density="compact" hide-details @update:model-value="saveSiteAgent(agent)" />
                      </div>
                      <p class="text-caption text-grey mb-3" style="min-height: 38px;">{{ agent.description || 'Пользовательский ИИ-агент для задач сайта.' }}</p>

                      <!-- Доступные данные сайта (бейдж-чипсы) -->
                      <div class="mb-3">
                        <div class="text-caption text-medium-emphasis mb-1 font-weight-medium">Подключенные данные:</div>
                        <div class="d-flex flex-wrap gap-1">
                          <VChip
                            v-for="srcId in getAgentSources(agent)"
                            :key="srcId"
                            size="x-small"
                            :color="getSourceMeta(srcId).badge_color"
                            variant="tonal"
                          >
                            <i :class="['bx me-1', getSourceMeta(srcId).icon]"></i>
                            {{ getSourceMeta(srcId).name.split(' ')[0] }}
                          </VChip>
                        </div>
                      </div>

                      <!-- Инфо о подключении -->
                      <div class="text-caption bg-surface-variant pa-2 rounded mb-3">
                        <div class="d-flex justify-space-between">
                          <span class="text-grey">Модель:</span>
                          <strong>{{ agent.model_override || 'Из подключения' }}</strong>
                        </div>
                        <div class="d-flex justify-space-between">
                          <span class="text-grey">Пул Gemini:</span>
                          <span>{{ agent.use_gemini_pool ? 'Да' : 'Нет' }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- Кнопки управления -->
                    <div class="d-flex flex-column gap-2 pt-2 border-t">
                      <div class="d-flex gap-2">
                        <VBtn color="primary" variant="tonal" size="small" class="flex-grow-1" prepend-icon="bx-cog" @click="openEditAgent(agent)">
                          Настроить
                        </VBtn>
                        <VBtn color="secondary" variant="tonal" size="small" prepend-icon="bx-magic-wand" @click="openPromptGenerator(agent)" title="Написать / улучшить промпт с помощью ИИ">
                          Промпт
                        </VBtn>
                        <VBtn v-if="!isSystemAgent(agent)" color="error" variant="text" size="small" icon="bx-trash" @click="deleteSiteAgent(agent)" title="Удалить агента" />
                      </div>
                    </div>
                  </VCard>
                </VCol>
              </VRow>
            </div>

            <VDivider class="my-6" />

            <!-- ЖИВАЯ ПЕСОЧНИЦА -->
            <VCard class="border pa-5 bg-surface">
              <div class="d-flex flex-wrap justify-space-between align-center mb-3 gap-2">
                <div class="d-flex align-center">
                  <i class="bx bx-terminal text-h5 text-primary me-2"></i>
                  <h4 class="text-subtitle-1 font-weight-bold">⚡ Живая тестовая песочница ИИ</h4>
                </div>
                <div class="d-flex flex-wrap gap-2">
                  <VBtn size="small" variant="tonal" @click="setSandboxPreset('stats_analyst', 'Проанализируй выручку и продажи за последние дни по данным базы')">
                    📊 Сводка выручки
                  </VBtn>
                  <VBtn size="small" variant="tonal" @click="setSandboxPreset('feedback_nps', 'Придумай эмпатичный ответ гостю на оценку 3/5 с жалобой на опоздание курьера')">
                    💬 Ответ на отзыв
                  </VBtn>
                  <VBtn size="small" variant="tonal" @click="setSandboxPreset('site_manager', 'Напиши аппетитное продающее описание для нового сета запеченных роллов')">
                    🍣 Описание блюда
                  </VBtn>
                </div>
              </div>

              <!-- Переключатель передачи данных и индикаторы -->
              <div class="d-flex flex-wrap justify-space-between align-center pa-2 mb-3 rounded bg-surface-variant text-caption">
                <div class="d-flex align-center gap-1">
                  <span class="text-grey me-1">Данные агента в запросе:</span>
                  <VChip
                    v-for="s in getAgentSources(siteAgents.find(a => a.agent_code === sandboxAgent))"
                    :key="s"
                    size="x-small"
                    :color="getSourceMeta(s).badge_color"
                    variant="tonal"
                  >
                    <i :class="['bx me-1', getSourceMeta(s).icon]"></i>
                    {{ getSourceMeta(s).name.split(' ')[0] }}
                  </VChip>
                </div>
                <div>
                  <VSwitch
                    v-model="useLiveDataInSandbox"
                    label="Передавать реальные данные из БД сайта"
                    color="primary"
                    density="compact"
                    hide-details
                  />
                </div>
              </div>

              <VRow class="mb-2">
                <VCol cols="12" md="4">
                  <VSelect
                    v-model="sandboxAgent"
                    :items="siteAgents"
                    item-title="title"
                    item-value="agent_code"
                    label="Выбор агента"
                    density="compact"
                  />
                </VCol>
                <VCol cols="12" md="8">
                  <VTextField
                    v-model="sandboxQuery"
                    label="Запрос к агенту"
                    placeholder="Например: Составь краткий отчет по среднему чеку..."
                    density="compact"
                    append-inner-icon="bx-send"
                    @click:append-inner="runSandboxQuery"
                    @keydown.enter="runSandboxQuery"
                  />
                </VCol>
              </VRow>

              <div class="d-flex justify-end mb-3">
                <VBtn color="primary" prepend-icon="bx-play" :loading="sandboxLoading" @click="runSandboxQuery">
                  Выполнить запрос к сайту
                </VBtn>
              </div>

              <!-- Окно ответа -->
              <div v-if="sandboxResult" class="ai-sandbox-terminal">
                <div class="font-weight-bold text-primary mb-2">
                  <i class="bx bx-check-double me-1"></i> Ответ от агента «{{ sandboxResult.agent_title }}»:
                </div>
                <div>{{ sandboxResult.response }}</div>

                <div class="ai-sandbox-meta">
                  <span>Модель: <strong>{{ sandboxResult.model }}</strong> ({{ sandboxResult.provider_name }})</span>
                  <span>Канал: <strong>{{ sandboxResult.used_proxy ? 'Через прокси' : 'Прямой РФ (без прокси)' }}</strong></span>
                  <span>Время: <strong>{{ sandboxResult.latency_ms }} мс</strong></span>
                  <span>Токены: <strong>{{ sandboxResult.tokens }}</strong></span>
                  <span v-if="sandboxResult.data_sources_used && sandboxResult.data_sources_used.length">
                    Источники: <strong>{{ sandboxResult.data_sources_used.join(', ') }}</strong>
                  </span>
                </div>
              </div>
            </VCard>
          </VWindowItem>
        </VWindow>
      </VCardText>
    </VCard>

    <!-- МОДАЛЬНОЕ ОКНО: ДОБАВЛЕНИЕ/РЕДАКТИРОВАНИЕ ПРОКСИ -->
    <VDialog v-model="isProxyModalOpen" max-width="500">
      <VCard title="Настройка прокси-сервера">
        <VCardText class="pa-4">
          <VTextField v-model="proxyForm.name" label="Название / Метка" class="mb-3" />
          <VSelect v-model="proxyForm.protocol" :items="['socks5', 'http', 'https']" label="Протокол" class="mb-3" />
          <VRow>
            <VCol cols="8"><VTextField v-model="proxyForm.host" label="Хост / IP" /></VCol>
            <VCol cols="4"><VTextField v-model.number="proxyForm.port" label="Порт" type="number" /></VCol>
          </VRow>
          <VRow>
            <VCol cols="6"><VTextField v-model="proxyForm.username" label="Логин (опционально)" /></VCol>
            <VCol cols="6"><VTextField v-model="proxyForm.password" label="Пароль (опционально)" type="password" /></VCol>
          </VRow>
          <VTextField v-model.number="proxyForm.priority" label="Приоритет (меньше = выше)" type="number" class="mt-2" />
        </VCardText>
        <VCardActions class="pa-4 border-t">
          <VSpacer />
          <VBtn variant="text" color="secondary" @click="isProxyModalOpen = false">Отмена</VBtn>
          <VBtn color="primary" variant="elevated" @click="saveProxy">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- МОДАЛЬНОЕ ОКНО: МАССОВЫЙ ИМПОРТ ПРОКСИ -->
    <VDialog v-model="isBulkProxyModalOpen" max-width="600">
      <VCard title="Массовый импорт прокси списком">
        <VCardText class="pa-4">
          <p class="text-caption text-grey">Вставьте строки формата <code>ip:port:user:pass</code>, <code>socks5://user:pass@host:port</code> или <code>host:port</code> (по одной на строку):</p>
          <VTextarea v-model="bulkProxyText" rows="6" placeholder="45.140.12.34:1080:user:pass&#10;socks5://user:pass@194.226.1.1:1080" />
        </VCardText>
        <VCardActions class="pa-4 border-t">
          <VSpacer />
          <VBtn variant="text" color="secondary" @click="isBulkProxyModalOpen = false">Отмена</VBtn>
          <VBtn color="primary" variant="elevated" @click="saveBulkProxies">Импортировать</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- МОДАЛЬНОЕ ОКНО: ПОДКЛЮЧЕНИЕ К ИИ -->
    <VDialog v-model="isConnectionModalOpen" max-width="580">
      <VCard :title="connForm.id ? 'Редактировать подключение ИИ' : 'Новое подключение к ИИ'">
        <VCardText class="pa-4">
          <VTextField v-model="connForm.name" label="Название подключения" class="mb-3" />
          <VRow>
            <VCol cols="6">
              <VSelect
                v-model="connForm.provider_group"
                :items="[{ title: 'Мировой ИИ (через прокси)', value: 'global' }, { title: 'РФ ИИ (прямой без прокси)', value: 'ru' }]"
                label="Группа провайдера"
              />
            </VCol>
            <VCol cols="6">
              <VSelect
                v-model="connForm.provider_type"
                :items="providerTypeOptions"
                item-title="title"
                item-value="value"
                label="Тип провайдера"
                @update:model-value="onProviderTypeChange"
              />
            </VCol>
          </VRow>

          <!-- Выбор системного тарифа и квоты -->
          <div class="mt-3">
            <VSelect
              v-model="connForm.tier_key"
              :items="availableTiers"
              item-title="title"
              item-value="value"
              label="Системный тарифный план / Квота"
              density="compact"
              @update:model-value="onTierChange"
            />
            <div class="d-flex justify-space-between align-center text-caption text-primary mb-2 mt-1">
              <div>
                <i class="bx bx-info-circle me-1"></i>
                {{ (connForm.extra_config && connForm.extra_config.description) || 'Официальные системные лимиты провайдера' }}
              </div>
            </div>
            <div class="d-flex justify-space-between align-center px-1 mb-3 text-caption">
              <span class="text-grey">Обновление лимитов тарифа:</span>
              <VChip v-if="connForm.extra_config && connForm.extra_config.reset_interval && connForm.extra_config.reset_interval !== 'none'" size="x-small" color="primary" variant="tonal">
                <i class="bx bx-time-five me-1"></i> {{ connForm.extra_config.reset_interval === 'daily_utc' ? 'Ежедневно в 00:00 UTC' : (connForm.extra_config.reset_interval === 'rpm_minute' ? 'Каждую минуту' : connForm.extra_config.reset_interval) }}
              </VChip>
              <VChip v-else size="x-small" color="secondary" variant="outlined">
                <i class="bx bx-infinite me-1"></i> n/a (не обновляются)
              </VChip>
            </div>
          </div>

          <!-- Базовый Endpoint URL -->
          <VTextField
            v-if="connForm.provider_type !== 'yandexgpt' && connForm.provider_type !== 'gigachat'"
            v-model="connForm.base_url"
            label="Endpoint URL (Base URL)"
            placeholder="https://api.groq.com/openai/v1"
            density="compact"
            class="mb-3"
            hint="Базовый адрес API (подставляется автоматически для Groq, Cerebras, NVIDIA NIM, GitHub Models)"
            persistent-hint
          />

          <!-- Стандартный ввод ключа (для всех, кроме YandexGPT) -->
          <VTextField
            v-if="connForm.provider_type !== 'yandexgpt'"
            v-model="connForm.api_key"
            :label="getApiKeyLabel(connForm.provider_type)"
            type="password"
            class="mb-3"
            :placeholder="getApiKeyPlaceholder(connForm.provider_type)"
            :hint="getApiKeyHint(connForm.provider_type)"
            persistent-hint
          />

          <!-- Специфичный структурированный блок Yandex Cloud -->
          <div v-if="connForm.provider_type === 'yandexgpt'" class="pa-3 rounded bg-surface-variant mb-4 border">
            <div class="d-flex align-center mb-2">
              <i class="bx bx-cloud text-error me-2 text-h6"></i>
              <strong class="text-subtitle-2">Авторизация Yandex Cloud (YandexGPT)</strong>
            </div>
            
            <VTextField
              v-model="connForm.client_id"
              label="Идентификатор каталога (Folder ID) *"
              placeholder="b1g..."
              class="mb-3"
              density="compact"
              hint="ID каталога в консоли Yandex Cloud (вверху страницы). Обязателен для адреса модели: gpt://<folder_id>/<модель>"
              persistent-hint
              @paste="onYandexKeyPaste($event, 'folder_id')"
            />

            <VTextField
              v-model="connForm.api_key"
              label="Секретный ключ (Secret Key) *"
              placeholder="AQVN..."
              type="password"
              class="mb-3"
              density="compact"
              hint="Секретный ключ сервисного аккаунта (AQVN...). Именно он используется для запросов (передается в Api-Key)"
              persistent-hint
              @paste="onYandexKeyPaste($event, 'secret')"
            />

            <VTextField
              v-model="connForm.extra_config.key_id"
              label="Идентификатор API-ключа (Key ID)"
              placeholder="ajev..."
              class="mb-3"
              density="compact"
              hint="Идентификатор ключа из консоли Yandex Cloud (для идентификации и сверки)"
              persistent-hint
              @paste="onYandexKeyPaste($event, 'key_id')"
            />

            <VSelect
              v-model="connForm.auth_scope"
              :items="[{ title: 'API-Key (рекомендуется)', value: 'api_key' }, { title: 'IAM-Token', value: 'iam_token' }]"
              label="Тип авторизации"
              density="compact"
              class="mb-1"
            />
          </div>

          <!-- Выбор модели из выпадающего списка с подгрузкой из API -->
          <div class="d-flex align-start gap-2 mb-3">
            <VCombobox
              v-model="connForm.default_model"
              :items="availableModelsList.length > 0 ? availableModelsList : ((quotaPresets[connForm.provider_type] && (quotaPresets[connForm.provider_type][connForm.tier_key]?.models || quotaPresets[connForm.provider_type]?.free?.models || quotaPresets[connForm.provider_type]?.standard?.models || quotaPresets[connForm.provider_type]?.eval?.models)) || [connForm.default_model])"
              label="Модель по умолчанию"
              density="compact"
              class="flex-grow-1"
              placeholder="Выберите из списка или введите вручную"
              hint="Выберите из списка или нажмите кнопку справа для запроса свежих моделей через API"
              persistent-hint
            />
            <VBtn
              color="primary"
              variant="tonal"
              density="compact"
              class="mt-1"
              :loading="loadingModels"
              icon="bx-cloud-download"
              title="Запросить доступные модели через API"
              @click="loadModelsForConnection"
            />
          </div>

          <!-- Системные лимиты RPM / RPD / Токены -->
          <VRow class="mb-1">
            <VCol cols="4">
              <VTextField v-model.number="connForm.rpm_limit" label="RPM (в минуту)" type="number" density="compact" />
            </VCol>
            <VCol cols="4">
              <VTextField v-model.number="connForm.daily_requests_limit" label="Запросов в день" type="number" density="compact" />
            </VCol>
            <VCol cols="4">
              <VTextField v-model.number="connForm.daily_tokens_limit" label="Токенов в день" type="number" density="compact" />
            </VCol>
          </VRow>

          <!-- Специфичные поля Сбер GigaChat -->
          <div v-if="connForm.provider_type === 'gigachat'">
            <VSelect v-model="connForm.auth_scope" :items="['GIGACHAT_API_PERS', 'GIGACHAT_API_B2B', 'GIGACHAT_API_CORP']" label="Scope GigaChat" class="mb-3" />
            <VSwitch v-model="connForm.verify_ssl" label="Проверка сертификатов SSL" density="compact" />
          </div>

          <!-- Привязка прокси для мировых -->
          <div v-if="connForm.provider_group === 'global'">
            <VSelect
              v-model="connForm.pinned_proxy_id"
              :items="[{ id: null, name: 'Автоподбор лучшего рабочего из пула' }, ...proxies]"
              item-title="name"
              item-value="id"
              label="Использовать прокси"
              class="mb-3"
            />
          </div>
        </VCardText>
        <VCardActions class="pa-4 border-t">
          <VSpacer />
          <VBtn variant="text" color="secondary" @click="isConnectionModalOpen = false">Отмена</VBtn>
          <VBtn color="primary" variant="elevated" @click="saveConnection">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- МОДАЛЬНОЕ ОКНО: СОЗДАНИЕ / НАСТРОЙКА АГЕНТА САЙТА -->
    <VDialog v-model="isAgentModalOpen" max-width="800">
      <VCard>
        <VCardTitle class="pa-4 border-b d-flex justify-space-between align-center">
          <div class="d-flex align-center">
            <i class="bx bx-brain text-primary text-h5 me-2"></i>
            <span class="font-weight-bold">
              {{ agentModalMode === 'create' ? 'Создать нового ИИ-агента сайта' : `Настройка агента «${agentForm.title}»` }}
            </span>
          </div>
          <VBtn icon="bx-x" variant="text" size="small" @click="isAgentModalOpen = false" />
        </VCardTitle>

        <VCardText class="pa-5" style="max-height: 75vh; overflow-y: auto;">
          <VRow>
            <VCol cols="12" md="8">
              <VTextField
                v-model="agentForm.title"
                label="Название агента *"
                placeholder="Например: Аналитик выручки и акций"
                density="compact"
                class="mb-3"
              />
            </VCol>
            <VCol cols="12" md="4">
              <VTextField
                v-model="agentForm.agent_code"
                label="Системный код (ID)"
                placeholder="promo_analyst_agent"
                density="compact"
                class="mb-3"
                hint="Используется в API. Оставьте пустым для автогенерации"
                persistent-hint
                :disabled="agentModalMode === 'edit' && isSystemAgent(agentForm)"
              />
            </VCol>

            <VCol cols="12">
              <VTextarea
                v-model="agentForm.description"
                label="Краткое описание обязанностей роли"
                rows="2"
                density="compact"
                placeholder="Опишите, за что отвечает агент..."
                class="mb-3"
              />
            </VCol>

            <VCol cols="12">
              <VSwitch
                v-model="agentForm.is_active"
                label="Агент активен на сайте"
                color="primary"
                density="compact"
                class="mb-2"
              />
            </VCol>
          </VRow>

          <VDivider class="my-3" />

          <!-- БЛОК ДОСТУПНЫХ ДАННЫХ САЙТА -->
          <div class="mb-4">
            <div class="d-flex justify-space-between align-center mb-2">
              <div>
                <strong class="text-subtitle-2 font-weight-bold">Доступные данные сайта для работы и обработки агентом:</strong>
                <p class="text-caption text-grey mb-0">Выберите, какую информацию из базы данных агент будет получать в запросах:</p>
              </div>
            </div>

            <VRow>
              <VCol v-for="src in dataCatalog" :key="src.id" cols="12" sm="6">
                <div
                  class="pa-3 border rounded cursor-pointer transition-all d-flex align-start gap-2"
                  :style="agentForm.selected_data_sources.includes(src.id) ? 'border-color: rgb(var(--v-theme-primary)) !important; background: rgba(var(--v-theme-primary), 0.05);' : ''"
                  @click="toggleSourceInAgentForm(src.id)"
                >
                  <VCheckbox
                    :model-value="agentForm.selected_data_sources.includes(src.id)"
                    density="compact"
                    hide-details
                    class="mt-0 pt-0"
                    @click.stop="toggleSourceInAgentForm(src.id)"
                  />
                  <div class="flex-grow-1">
                    <div class="font-weight-bold text-caption text-primary d-flex align-center">
                      <i :class="['bx me-1', src.icon]"></i>
                      {{ src.name }}
                    </div>
                    <div class="text-caption text-grey mt-1">{{ src.description }}</div>
                  </div>
                </div>
              </VCol>
            </VRow>
          </div>

          <VDivider class="my-3" />

          <!-- ПОДКЛЮЧЕНИЕ И МОДЕЛЬ -->
          <div class="mb-3">
            <strong class="text-subtitle-2 font-weight-bold mb-2 d-block">Подключение к ИИ и параметры генерации:</strong>
            <VRow>
              <VCol cols="12" md="6">
                <VSelect
                  v-model="agentForm.primary_connection_id"
                  :items="connections"
                  item-title="name"
                  item-value="id"
                  label="Основной ИИ провайдер"
                  density="compact"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VCombobox
                  v-model="agentForm.model_override"
                  :items="getAgentAvailableModels(agentForm)"
                  label="Модель (по умолчанию из подключения)"
                  density="compact"
                  clearable
                  placeholder="По умолчанию из подключения"
                />
              </VCol>

              <VCol cols="12" md="6">
                <VSelect
                  v-model="agentForm.fallback_connection_id"
                  :items="connections"
                  item-title="name"
                  item-value="id"
                  label="Резервный ИИ (Failover)"
                  density="compact"
                  clearable
                />
              </VCol>
              <VCol cols="12" md="6">
                <VCheckbox
                  v-model="agentForm.use_gemini_pool"
                  label="Использовать весь пул Gemini с ротацией"
                  density="compact"
                  hide-details
                  class="mt-1"
                />
              </VCol>

              <VCol cols="6">
                <VTextField
                  v-model.number="agentForm.temperature"
                  label="Креативность (Temperature 0.0 - 1.0)"
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  density="compact"
                />
              </VCol>
              <VCol cols="6">
                <VTextField
                  v-model.number="agentForm.max_tokens"
                  label="Макс. токенов ответа"
                  type="number"
                  density="compact"
                />
              </VCol>
            </VRow>
          </div>

          <VDivider class="my-3" />

          <!-- СИСТЕМНЫЙ ПРОМПТ -->
          <div>
            <div class="d-flex flex-wrap justify-space-between align-center mb-2 gap-2">
              <div>
                <strong class="text-subtitle-2 font-weight-bold">Системный промпт (Инструкция агента)</strong>
                <span class="text-caption text-grey d-block">Определяет логику, формат ответа и правила анализа переданных данных</span>
              </div>
              <VBtn
                color="primary"
                variant="elevated"
                size="small"
                prepend-icon="bx-magic-wand"
                @click="openPromptGenerator(agentForm)"
              >
                ✨ Написать / улучшить с помощью ИИ
              </VBtn>
            </div>

            <VTextarea
              v-model="agentForm.system_prompt"
              label="Текст системного промпта"
              rows="8"
              density="compact"
              placeholder="Введите системный промпт или нажмите кнопку выше для создания профессионального промпта с помощью подключенных ИИ..."
            />
          </div>
        </VCardText>

        <VCardActions class="pa-4 border-t">
          <VSpacer />
          <VBtn variant="text" color="secondary" @click="isAgentModalOpen = false">Отмена</VBtn>
          <VBtn color="primary" variant="elevated" :loading="agentFormLoading" @click="saveAgentModal">
            Сохранить агента
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- МОДАЛЬНОЕ ОКНО: ГЕНЕРАТОР ПРОМПТОВ ЧЕРЕЗ ПОДКЛЮЧЕННЫЕ ИИ -->
    <VDialog v-model="isPromptModalOpen" max-width="850">
      <VCard>
        <VCardTitle class="pa-4 border-b d-flex justify-space-between align-center">
          <div class="d-flex align-center">
            <i class="bx bx-magic-wand text-primary text-h5 me-2"></i>
            <span class="font-weight-bold">Генератор системных промптов через подключенные ИИ</span>
          </div>
          <VBtn icon="bx-x" variant="text" size="small" @click="isPromptModalOpen = false" />
        </VCardTitle>

        <VCardText class="pa-5" style="max-height: 80vh; overflow-y: auto;">
          <VAlert color="info" variant="tonal" class="mb-4">
            <div class="d-flex align-center">
              <i class="bx bx-info-circle me-2 text-h6"></i>
              <div class="text-caption">
                Опишите своими словами, какую задачу должен решать агент. Подключенный ИИ проанализирует выбранные данные сайта (OLAP, заказы, клиенты, меню) и составит исчерпывающий, профессиональный системный промпт <strong>без ограничений</strong>.
              </div>
            </div>
          </VAlert>

          <VRow>
            <VCol cols="12" md="7">
              <VTextField
                v-model="promptForm.title"
                label="Желаемое название агента"
                placeholder="Например: Эксперт по среднему чеку и скидкам"
                density="compact"
                class="mb-3"
              />
            </VCol>
            <VCol cols="12" md="5">
              <VSelect
                v-model="promptForm.connection_id"
                :items="[{ id: null, name: 'Автовыбор лучшего подключенного ИИ' }, ...connections]"
                item-title="name"
                item-value="id"
                label="Использовать для генерации"
                density="compact"
                class="mb-3"
              />
            </VCol>

            <VCol cols="12">
              <VTextarea
                v-model="promptForm.goal"
                label="Цель и задачи агента своими словами *"
                rows="3"
                density="compact"
                placeholder="Например: Агент должен ежедневно анализировать динамику выручки и среднего чека по дням недели, выявлять проседания в будние дни и предлагать управляющему конкретные промокоды и сеты роллов для стимулирования заказов..."
                class="mb-3"
              />
            </VCol>

            <VCol cols="12">
              <strong class="text-caption font-weight-bold text-medium-emphasis mb-2 d-block">
                Источники данных сайта для включения в инструкцию агента:
              </strong>
              <div class="d-flex flex-wrap gap-2 mb-3">
                <VChip
                  v-for="src in dataCatalog"
                  :key="src.id"
                  size="small"
                  :color="promptForm.selected_data_sources.includes(src.id) ? src.badge_color : 'default'"
                  :variant="promptForm.selected_data_sources.includes(src.id) ? 'elevated' : 'outlined'"
                  class="cursor-pointer"
                  @click="toggleSourceInPromptForm(src.id)"
                >
                  <i :class="['bx me-1', src.icon]"></i>
                  {{ src.name }}
                </VChip>
              </div>
            </VCol>

            <VCol cols="12">
              <VTextField
                v-model="promptForm.custom_instructions"
                label="Дополнительные пожелания к стилю или правилам (опционально)"
                placeholder="Например: Отвечать строго таблицами, давать расчеты в рублях и %"
                density="compact"
                class="mb-3"
              />
            </VCol>
          </VRow>

          <div class="d-flex justify-end mb-4">
            <VBtn
              color="primary"
              size="large"
              prepend-icon="bx-sparkles"
              :loading="promptGenerating"
              @click="runGeneratePrompt"
            >
              Сгенерировать системный промпт через ИИ
            </VBtn>
          </div>

          <!-- РЕЗУЛЬТАТ ГЕНЕРАЦИИ -->
          <div v-if="generatedPromptResult" class="pa-4 rounded border bg-surface-variant">
            <div class="d-flex justify-space-between align-center mb-2">
              <div class="font-weight-bold text-subtitle-2 text-primary d-flex align-center">
                <i class="bx bx-check-circle me-1"></i> Системный промпт составлен:
              </div>
              <div class="text-caption text-grey">
                Модель: <strong>{{ generatedPromptResult.generated_by_model }}</strong> ({{ generatedPromptResult.tokens_used }} токенов)
              </div>
            </div>

            <VTextarea
              v-model="generatedPromptResult.system_prompt"
              rows="10"
              density="compact"
              class="mb-3"
              label="Текст системного промпта (можно отредактировать)"
            />

            <div class="d-flex justify-end gap-2">
              <VBtn variant="tonal" color="secondary" @click="runGeneratePrompt">
                Перегенерировать
              </VBtn>
              <VBtn color="success" variant="elevated" prepend-icon="bx-check" @click="applyGeneratedPrompt">
                Применить в настройки агента
              </VBtn>
            </div>
          </div>
        </VCardText>
      </VCard>
    </VDialog>

    <VSnackbar v-model="snackbar.show" :color="snackbar.color" timeout="4000">
      {{ snackbar.text }}
    </VSnackbar>
  </div>
</template>
