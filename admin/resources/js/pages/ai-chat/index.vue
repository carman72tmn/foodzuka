<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useDisplay } from 'vuetify'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const toast = useToast()
const { smAndDown } = useDisplay()

// Drawer state for mobile screens
const isMobileDrawerOpen = ref(false)

// Sessions & messages
const sessions = ref([])
const activeSessionId = ref(null)
const messages = ref([])
const isLoadingSessions = ref(false)
const isLoadingMessages = ref(false)
const isSending = ref(false)
const userPrompt = ref('')
const messagesContainerRef = ref(null)

// Configured Agents
const siteAgents = ref([])
const activeAgentCode = ref('omni_assistant')

// Configured Providers & Models
const connections = ref([])
const selectedConnectionId = ref(null)
const availableModels = ref([])
const selectedModel = ref(null)

// Search in dialogs
const sessionSearchQuery = ref('')

// Predefined quick templates by agent
const quickPromptsByAgent = {
  omni_assistant: [
    { label: '🧠 Любой вопрос', prompt: 'Привет! Расскажи, в чем ты можешь мне помочь без ограничений и на какие темы мы можем общаться?' },
    { label: '🚀 Идеи для выручки', prompt: 'Предложи 5 нестандартных практических шагов по увеличению среднего чека и повторных заказов в доставке еды.' },
    { label: '🍣 Новинка меню', prompt: 'Придумай концепт хитового ролла или пиццы: состав, себестоимость, аппетитное описание и слоган для рекламы.' },
    { label: '💻 Код и интеграции', prompt: 'Помоги составить алгоритм, написать SQL-запрос или оптимизировать работу скриптов.' }
  ],
  stats_analyst: [
    { label: '📊 Срез выручки', prompt: 'Проанализируй текущую выручку, средний чек и структуру заказов за последние дни.' },
    { label: '🔥 Топ блюд', prompt: 'Какие блюда и категории сейчас продаются активнее всего? Что приносит основную маржу?' },
    { label: '🚴 Отчет по курьерам', prompt: 'Как справляются курьеры? Оцени среднее время доставки и ключевые метрики логистики.' },
    { label: '💡 Совет по среднему чеку', prompt: 'Какие комбо-наборы или допродажи можно внедрить для увеличения среднего чека?' }
  ],
  site_manager: [
    { label: '🍣 Промо-пост ВК', prompt: 'Напиши яркий, вовлекающий пост для сообщества ВК с акцией на сет роллов в эти выходные.' },
    { label: '✨ Описание новинки', prompt: 'Составь аппетитное, продающее описание для нового запеченного ролла с креветкой и соусом манго-чили.' },
    { label: '📢 Текст для рассылки', prompt: 'Придумай цепляющий текст пуш/СМС сообщения для возврата гостей, которые не заказывали больше 14 дней.' },
    { label: '🎁 Идея для акции', prompt: 'Предложи 3 креативные маркетинговые акции на следующую неделю для повышения повторных заказов.' }
  ],
  feedback_nps: [
    { label: '❤️ Ответ на позитив', prompt: 'Составь теплый, дружелюбный и искренний ответ постоянному гостю на отзыв с 5 звездами.' },
    { label: '🛡️ Урегулирование жалобы', prompt: 'Гость пожаловался, что роллы приехали холодными, а курьер опоздал на 20 минут. Напиши вежливый, эмпатичный ответ с решением проблемы.' },
    { label: '⭐ Анализ оценок', prompt: 'Проанализируй последние оценки и отзывы гостей: на что чаще всего обращают внимание клиенты?' }
  ],
  general_assistant: [
    { label: '🛒 Конверсия корзины', prompt: 'Как сократить процент брошенных корзин на сайте доставки еды?' },
    { label: '⚡ Скорость кухни', prompt: 'Какие чек-листы и стандарты помогают поварам отдавать заказы на 10-15% быстрее?' },
    { label: '🍣 Тренды меню', prompt: 'Какие тренды в японской и паназиатской кухне сейчас наиболее популярны среди молодежи?' }
  ]
}

// Current active agent info
const currentAgent = computed(() => {
  return siteAgents.value.find(a => a.agent_code === activeAgentCode.value) || {
    agent_code: activeAgentCode.value,
    title: 'ИИ-Ассистент',
    description: 'Универсальный помощник по ресторану и сайту'
  }
})

// Current agent quick prompts
const activeQuickPrompts = computed(() => {
  return quickPromptsByAgent[activeAgentCode.value] || quickPromptsByAgent.stats_analyst
})

// Filtered sessions
const filteredSessions = computed(() => {
  if (!sessionSearchQuery.value) return sessions.value
  const q = sessionSearchQuery.value.toLowerCase()
  return sessions.value.filter(s => s.title.toLowerCase().includes(q))
})

// --- API METHODS ---

const fetchAgents = async () => {
  try {
    const res = await axios.get('/api/v1/ai-agents/site-agents')
    siteAgents.value = res.data
    if (siteAgents.value.length > 0 && !activeAgentCode.value) {
      activeAgentCode.value = siteAgents.value[0].agent_code
    }
  } catch (e) {
    console.error('Ошибка загрузки агентов', e)
  }
}

const fetchConnectionsAndModels = async () => {
  try {
    const res = await axios.get('/api/v1/ai-agents/connections')
    connections.value = res.data.filter(c => c.is_enabled)
    
    // Сбор уникальных моделей из активных подключений
    const modelsSet = new Set()
    connections.value.forEach(c => {
      if (c.default_model) modelsSet.add(c.default_model)
    })
    
    // Добавляем популярные быстрые модели
    modelsSet.add('gemini-3.5-flash-lite')
    modelsSet.add('gemini-1.5-flash')
    modelsSet.add('qwen/qwen3.8-27b')
    modelsSet.add('GigaChat')
    
    availableModels.value = Array.from(modelsSet)
    if (!selectedModel.value && availableModels.value.length > 0) {
      selectedModel.value = availableModels.value[0]
    }
  } catch (e) {
    console.error('Ошибка загрузки подключений', e)
  }
}

const fetchSessions = async () => {
  isLoadingSessions.value = true
  try {
    const res = await axios.get('/api/v1/ai-agents/chat/sessions')
    sessions.value = res.data
    if (sessions.value.length > 0 && !activeSessionId.value) {
      selectSession(sessions.value[0].id)
    }
  } catch (e) {
    console.error('Ошибка загрузки диалогов', e)
  } finally {
    isLoadingSessions.value = false
  }
}

const selectSession = async (sessionId) => {
  activeSessionId.value = sessionId
  if (smAndDown.value) isMobileDrawerOpen.value = false
  
  const sess = sessions.value.find(s => s.id === sessionId)
  if (sess && sess.agent_code) {
    activeAgentCode.value = sess.agent_code
  }

  isLoadingMessages.value = true
  try {
    const res = await axios.get(`/api/v1/ai-agents/chat/sessions/${sessionId}/messages`)
    messages.value = res.data
    scrollToBottom()
  } catch (e) {
    toast.error('Не удалось загрузить историю диалога')
  } finally {
    isLoadingMessages.value = false
  }
}

const createNewSession = async () => {
  try {
    const title = `Диалог ${new Date().toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}`
    const res = await axios.post(`/api/v1/ai-agents/chat/sessions?title=${encodeURIComponent(title)}&agent_code=${activeAgentCode.value}`)
    sessions.value.unshift(res.data)
    activeSessionId.value = res.data.id
    messages.value = []
    if (smAndDown.value) isMobileDrawerOpen.value = false
    toast.success('Начат новый диалог')
  } catch (e) {
    toast.error('Ошибка создания диалога')
  }
}

const deleteSession = async (sessionId) => {
  if (!confirm('Удалить этот диалог?')) return
  try {
    await axios.delete(`/api/v1/ai-agents/chat/sessions/${sessionId}`)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (activeSessionId.value === sessionId) {
      if (sessions.value.length > 0) {
        selectSession(sessions.value[0].id)
      } else {
        activeSessionId.value = null
        messages.value = []
      }
    }
    toast.success('Диалог удален')
  } catch (e) {
    toast.error('Не удалось удалить диалог')
  }
}

const sendMessage = async () => {
  const text = userPrompt.value.trim()
  if (!text || isSending.value) return

  // Очищаем инпут
  userPrompt.value = ''

  // Добавляем сообщение пользователя в интерфейс оптимистично
  const tempUserMsg = {
    id: 'temp-' + Date.now(),
    role: 'user',
    content: text,
    created_at: new Date().toISOString()
  }
  messages.value.push(tempUserMsg)
  scrollToBottom()

  isSending.value = true
  try {
    const payload = {
      agent_code: activeAgentCode.value,
      message: text,
      session_id: activeSessionId.value,
      connection_id: selectedConnectionId.value || undefined,
      model: selectedModel.value || undefined
    }

    const res = await axios.post('/api/v1/ai-agents/chat/send', payload)

    // Обновляем id сессии, если создалась новая на бэкенде
    if (res.data.session_id && (!activeSessionId.value || activeSessionId.value !== res.data.session_id)) {
      activeSessionId.value = res.data.session_id
      fetchSessions()
    }

    // Добавляем ответ ИИ
    const aiMsg = {
      id: res.data.message_id || Date.now(),
      role: 'assistant',
      content: res.data.response,
      model: res.data.model,
      tokens_used: res.data.tokens_used,
      latency_ms: res.data.latency_ms,
      provider_name: res.data.provider_name,
      fallback_note: res.data.fallback_note,
      created_at: new Date().toISOString()
    }
    messages.value.push(aiMsg)
    scrollToBottom()
  } catch (e) {
    const errorMsg = e.response?.data?.detail || e.message || 'Ошибка генерации ответа'
    messages.value.push({
      id: 'err-' + Date.now(),
      role: 'assistant',
      is_error: true,
      content: `⚠️ Ошибка: ${errorMsg}\n\nПожалуйста, убедитесь, что в разделе «Система -> Агенты ИИ» добавлены и включены активные ключи провайдеров.`,
      created_at: new Date().toISOString()
    })
    scrollToBottom()
  } finally {
    isSending.value = false
  }
}

const applyPromptTemplate = (prompt) => {
  userPrompt.value = prompt
  nextTick(() => {
    sendMessage()
  })
}

const copyMessageText = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    toast.success('Текст скопирован в буфер обмена')
  } catch (err) {
    toast.info('Не удалось автоматически скопировать текст')
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainerRef.value) {
      messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight
    }
  })
}

const onKeyDown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// Format basic markdown text into clean HTML
const formatMarkdown = (text) => {
  if (!text) return ''
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Code blocks ```code```
  html = html.replace(/```([\s\S]*?)```/g, '<pre class="ai-code-block"><code>$1</code></pre>')

  // Inline code `code`
  html = html.replace(/`([^`]+)`/g, '<code class="ai-inline-code">$1</code>')

  // Bold **text**
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')

  // Italic *text*
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')

  // Headers ### Header
  html = html.replace(/^### (.*$)/gim, '<h4 class="text-subtitle-1 font-weight-bold my-2 text-primary">$1</h4>')
  html = html.replace(/^## (.*$)/gim, '<h3 class="text-h6 font-weight-bold my-2 text-primary">$1</h3>')
  html = html.replace(/^# (.*$)/gim, '<h2 class="text-h5 font-weight-bold my-3 text-primary">$1</h2>')

  // Bullet points
  html = html.replace(/^\s*[-•]\s+(.*)$/gim, '<li class="ms-4 mb-1">$1</li>')

  // Line breaks
  html = html.replace(/\n/g, '<br>')

  return html
}

const getAgentIcon = (code) => {
  switch (code) {
    case 'omni_assistant': return 'bx-brain'
    case 'stats_analyst': return 'bx-bar-chart-alt-2'
    case 'site_manager': return 'bx-pencil'
    case 'feedback_nps': return 'bx-heart'
    default: return 'bx-bot'
  }
}

const getAgentColor = (code) => {
  switch (code) {
    case 'omni_assistant': return 'purple'
    case 'stats_analyst': return 'primary'
    case 'site_manager': return 'success'
    case 'feedback_nps': return 'warning'
    default: return 'info'
  }
}

onMounted(() => {
  fetchAgents()
  fetchConnectionsAndModels()
  fetchSessions()
})
</script>

<template>
  <div class="ai-chat-wrapper">
    <!-- Mobile Drawer for Dialogs List -->
    <VNavigationDrawer
      v-if="smAndDown"
      v-model="isMobileDrawerOpen"
      temporary
      location="left"
      width="300"
      class="bg-surface"
    >
      <div class="pa-4 border-bottom d-flex align-center justify-space-between">
        <div class="d-flex align-center gap-2">
          <VIcon icon="bx-conversation" color="primary" />
          <span class="font-weight-bold">Диалоги с ИИ</span>
        </div>
        <VBtn icon size="small" variant="text" @click="isMobileDrawerOpen = false">
          <VIcon icon="bx-x" />
        </VBtn>
      </div>

      <div class="pa-3">
        <VBtn block color="primary" class="mb-3" prepend-icon="bx-plus" @click="createNewSession">
          Новый диалог
        </VBtn>

        <VTextField
          v-model="sessionSearchQuery"
          placeholder="Поиск диалогов..."
          density="compact"
          prepend-inner-icon="bx-search"
          variant="outlined"
          hide-details
          class="mb-3"
        />

        <VList lines="two" density="compact" class="session-list">
          <VListItem
            v-for="s in filteredSessions"
            :key="s.id"
            :active="s.id === activeSessionId"
            rounded="lg"
            class="mb-1"
            @click="selectSession(s.id)"
          >
            <template #prepend>
              <VAvatar size="32" :color="getAgentColor(s.agent_code)" variant="tonal" class="me-2">
                <VIcon size="18" :icon="getAgentIcon(s.agent_code)" />
              </VAvatar>
            </template>
            <VListItemTitle class="font-weight-medium text-body-2 text-truncate">
              {{ s.title }}
            </VListItemTitle>
            <VListItemSubtitle class="text-caption text-muted">
              {{ s.updated_at ? new Date(s.updated_at).toLocaleDateString('ru-RU') : 'Недавно' }}
            </VListItemSubtitle>
            <template #append>
              <VBtn icon size="x-small" variant="text" color="error" @click.stop="deleteSession(s.id)">
                <VIcon size="16" icon="bx-trash" />
              </VBtn>
            </template>
          </VListItem>
        </VList>
      </div>
    </VNavigationDrawer>

    <!-- Main Container Card -->
    <VCard class="chat-card elevation-2 overflow-hidden border">
      <div class="d-flex fill-height">
        <!-- Desktop Sidebar (Dialogs List) -->
        <div v-if="!smAndDown" class="chat-sidebar border-end d-flex flex-column">
          <!-- Sidebar Header -->
          <div class="pa-4 border-bottom">
            <div class="d-flex align-center justify-space-between mb-3">
              <div class="d-flex align-center gap-2">
                <VAvatar color="primary" variant="tonal" size="36">
                  <VIcon icon="bx-bot" size="22" />
                </VAvatar>
                <div>
                  <h3 class="text-subtitle-1 font-weight-bold mb-0">ИИ Агенты</h3>
                  <span class="text-caption text-muted">Ассистенты Vezuroll</span>
                </div>
              </div>
            </div>

            <VBtn
              block
              color="primary"
              variant="elevated"
              prepend-icon="bx-plus"
              class="shadow-sm"
              @click="createNewSession"
            >
              Новый диалог
            </VBtn>
          </div>

          <!-- Dialogs Search -->
          <div class="px-3 pt-3">
            <VTextField
              v-model="sessionSearchQuery"
              placeholder="Поиск тем..."
              density="compact"
              prepend-inner-icon="bx-search"
              variant="outlined"
              hide-details
              clearable
            />
          </div>

          <!-- Dialogs List -->
          <div class="flex-grow-1 overflow-y-auto pa-3 session-list">
            <div v-if="filteredSessions.length === 0" class="text-center py-8 text-muted text-caption">
              Нет сохраненных диалогов
            </div>

            <div
              v-for="s in filteredSessions"
              :key="s.id"
              class="session-item d-flex align-center justify-space-between pa-2 rounded-lg cursor-pointer mb-1 transition-all"
              :class="{ 'active-session': s.id === activeSessionId }"
              @click="selectSession(s.id)"
            >
              <div class="d-flex align-center overflow-hidden gap-2">
                <VAvatar size="32" :color="getAgentColor(s.agent_code)" variant="tonal">
                  <VIcon size="18" :icon="getAgentIcon(s.agent_code)" />
                </VAvatar>
                <div class="overflow-hidden">
                  <div class="text-body-2 font-weight-medium text-truncate" :title="s.title">
                    {{ s.title }}
                  </div>
                  <div class="text-caption text-muted">
                    {{ s.updated_at ? new Date(s.updated_at).toLocaleDateString('ru-RU') : 'Диалог' }}
                  </div>
                </div>
              </div>

              <VBtn
                icon
                size="x-small"
                variant="text"
                color="secondary"
                class="session-delete-btn"
                @click.stop="deleteSession(s.id)"
              >
                <VIcon size="16" icon="bx-trash" />
              </VBtn>
            </div>
          </div>

          <!-- Quick Agent Picker Footer -->
          <div class="pa-3 border-top bg-light">
            <div class="text-caption text-muted font-weight-bold mb-2 text-uppercase">
              Сменить агента:
            </div>
            <div class="d-flex gap-1">
              <VBtn
                v-for="agent in siteAgents"
                :key="agent.agent_code"
                size="small"
                variant="tonal"
                :color="activeAgentCode === agent.agent_code ? getAgentColor(agent.agent_code) : 'secondary'"
                class="flex-grow-1 text-caption px-2"
                @click="activeAgentCode = agent.agent_code"
              >
                <VIcon start size="16" :icon="getAgentIcon(agent.agent_code)" />
                {{ agent.agent_code === 'stats_analyst' ? 'Аналитик' : agent.agent_code === 'site_manager' ? 'Маркетолог' : 'Сервис' }}
              </VBtn>
            </div>
          </div>
        </div>

        <!-- Chat Conversation Area -->
        <div class="chat-main flex-grow-1 d-flex flex-column">
          <!-- Chat Top Navigation Bar -->
          <div class="chat-header pa-3 border-bottom d-flex align-center justify-space-between flex-wrap gap-2">
            <!-- Left: Toggle & Active Agent Info -->
            <div class="d-flex align-center gap-3">
              <VBtn
                v-if="smAndDown"
                icon
                variant="text"
                size="small"
                @click="isMobileDrawerOpen = true"
              >
                <VIcon icon="bx-menu" />
              </VBtn>

              <VAvatar :color="getAgentColor(activeAgentCode)" variant="tonal" size="40">
                <VIcon size="24" :icon="getAgentIcon(activeAgentCode)" />
              </VAvatar>

              <div>
                <div class="d-flex align-center gap-2">
                  <span class="font-weight-bold text-subtitle-1">{{ currentAgent.title }}</span>
                  <VChip size="x-small" color="success" variant="tonal" class="font-weight-medium">
                    Онлайн
                  </VChip>
                </div>
                <div class="text-caption text-muted d-none d-sm-block text-truncate" style="max-width: 420px">
                  {{ currentAgent.description }}
                </div>
              </div>
            </div>

            <!-- Right: Agent Selector & Model Switcher Dropdowns -->
            <div class="d-flex align-center gap-2 flex-wrap ai-header-controls">
              <!-- Select Agent -->
              <VSelect
                v-model="activeAgentCode"
                :items="siteAgents"
                item-title="title"
                item-value="agent_code"
                density="compact"
                variant="outlined"
                hide-details
                label="Агент"
                class="ai-selector-agent"
              >
                <template #prepend-inner>
                  <VIcon size="18" :icon="getAgentIcon(activeAgentCode)" :color="getAgentColor(activeAgentCode)" />
                </template>
              </VSelect>

              <!-- Select Model -->
              <VSelect
                v-model="selectedModel"
                :items="availableModels"
                density="compact"
                variant="outlined"
                hide-details
                label="Модель ИИ"
                class="ai-selector-model"
              >
                <template #prepend-inner>
                  <VIcon size="18" icon="bx-chip" color="primary" />
                </template>
              </VSelect>
            </div>
          </div>

          <!-- Chat Messages Scroll Container -->
          <div ref="messagesContainerRef" class="chat-messages flex-grow-1 overflow-y-auto pa-4">
            <!-- Empty State / Welcome Screen -->
            <div v-if="messages.length === 0 && !isLoadingMessages" class="empty-state text-center py-8">
              <VAvatar :color="getAgentColor(activeAgentCode)" variant="tonal" size="72" class="mb-4">
                <VIcon size="44" :icon="getAgentIcon(activeAgentCode)" />
              </VAvatar>

              <h2 class="text-h5 font-weight-bold mb-2">Чем я могу помочь вам сегодня?</h2>
              <p class="text-body-2 text-muted mx-auto mb-6" style="max-width: 550px">
                Я подключен к базе данных заказов, меню и клиентам «Везу Ролл». Задайте вопрос своими словами или воспользуйтесь готовыми сценариями ниже:
              </p>

              <!-- Quick Action Cards Grid -->
              <div class="quick-prompts-grid mx-auto" style="max-width: 700px">
                <VRow dense>
                  <VCol
                    v-for="(item, idx) in activeQuickPrompts"
                    :key="idx"
                    cols="12"
                    sm="6"
                  >
                    <VCard
                      variant="outlined"
                      class="quick-prompt-card pa-3 text-start cursor-pointer transition-all hover-elevate"
                      @click="applyPromptTemplate(item.prompt)"
                    >
                      <div class="font-weight-bold text-body-2 text-primary mb-1">
                        {{ item.label }}
                      </div>
                      <div class="text-caption text-muted text-truncate-2">
                        {{ item.prompt }}
                      </div>
                    </VCard>
                  </VCol>
                </VRow>
              </div>
            </div>

            <!-- Loading Spinner for Messages -->
            <div v-if="isLoadingMessages" class="text-center py-12">
              <VProgressCircular indeterminate color="primary" size="36" />
              <div class="text-caption text-muted mt-2">Загрузка диалога...</div>
            </div>

            <!-- Message Bubbles -->
            <div v-for="msg in messages" :key="msg.id" class="message-row mb-4" :class="msg.role">
              <!-- User Message Bubble -->
              <div v-if="msg.role === 'user'" class="d-flex justify-end gap-2">
                <div class="user-bubble pa-3 rounded-xl elevation-1">
                  <div class="text-body-1 text-white" style="white-space: pre-wrap">
                    {{ msg.content }}
                  </div>
                  <div class="text-caption text-end mt-1 text-white opacity-70">
                    {{ msg.created_at ? new Date(msg.created_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) : '' }}
                  </div>
                </div>
                <VAvatar size="32" color="primary" class="mt-1 shadow-sm">
                  <VIcon size="18" icon="bx-user" color="white" />
                </VAvatar>
              </div>

              <!-- Assistant / AI Message Bubble -->
              <div v-else class="d-flex justify-start gap-2">
                <VAvatar size="32" :color="getAgentColor(activeAgentCode)" variant="tonal" class="mt-1">
                  <VIcon size="18" :icon="getAgentIcon(activeAgentCode)" />
                </VAvatar>

                <div class="assistant-bubble pa-4 rounded-xl border elevation-1">
                  <!-- AI Meta header -->
                  <div class="d-flex align-center justify-space-between mb-2 pb-1 border-bottom gap-2">
                    <div class="d-flex align-center gap-2">
                      <span class="text-caption font-weight-bold text-primary">
                        {{ currentAgent.title }}
                      </span>
                      <VChip v-if="msg.model" size="x-small" variant="outlined" color="primary">
                        {{ msg.model }}
                      </VChip>
                    </div>

                    <div class="d-flex align-center gap-2">
                      <span v-if="msg.latency_ms" class="text-caption text-muted">
                        ⚡ {{ (msg.latency_ms / 1000).toFixed(1) }}s
                      </span>
                      <VBtn
                        icon
                        size="x-small"
                        variant="text"
                        color="secondary"
                        title="Копировать ответ"
                        @click="copyMessageText(msg.content)"
                      >
                        <VIcon size="16" icon="bx-copy" />
                      </VBtn>
                    </div>
                  </div>

                  <!-- AI Content with rich Markdown formatting -->
                  <div class="ai-content text-body-1" v-html="formatMarkdown(msg.content)"></div>

                  <!-- Fallback notice if provider was switched -->
                  <div v-if="msg.fallback_note" class="text-caption text-warning mt-2">
                    <VIcon icon="bx-info-circle" size="14" class="me-1" />
                    {{ msg.fallback_note }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Typing indicator when AI is generating -->
            <div v-if="isSending" class="d-flex align-center gap-2 my-2">
              <VAvatar size="32" :color="getAgentColor(activeAgentCode)" variant="tonal">
                <VIcon size="18" :icon="getAgentIcon(activeAgentCode)" />
              </VAvatar>
              <div class="typing-bubble pa-3 rounded-xl border bg-card d-flex align-center gap-2">
                <div class="typing-dots">
                  <span></span><span></span><span></span>
                </div>
                <span class="text-caption text-muted">ИИ анализирует данные и формулирует ответ...</span>
              </div>
            </div>
          </div>

          <!-- Quick Action Chips Bar (Above Input) -->
          <div class="quick-chips-bar px-4 py-2 border-top bg-light d-flex align-center gap-2 overflow-x-auto">
            <span class="text-caption text-muted font-weight-medium text-no-wrap">
              Быстрые запросы:
            </span>
            <VChip
              v-for="(item, idx) in activeQuickPrompts"
              :key="idx"
              size="small"
              variant="outlined"
              color="primary"
              class="cursor-pointer quick-chip"
              @click="applyPromptTemplate(item.prompt)"
            >
              {{ item.label }}
            </VChip>
          </div>

          <!-- Input Footer -->
          <div class="chat-footer pa-3 border-top bg-surface">
            <div class="d-flex align-center gap-2">
              <VTextarea
                v-model="userPrompt"
                rows="1"
                max-rows="5"
                auto-grow
                density="compact"
                variant="outlined"
                placeholder="Задайте вопрос агенту (Enter для отправки, Shift+Enter для новой строки)..."
                hide-details
                class="flex-grow-1 chat-textarea"
                :disabled="isSending"
                @keydown="onKeyDown"
              />

              <VBtn
                color="primary"
                size="large"
                class="send-btn shadow-primary"
                :loading="isSending"
                :disabled="!userPrompt.trim() || isSending"
                @click="sendMessage"
              >
                <VIcon icon="bx-send" />
              </VBtn>
            </div>

            <div class="text-caption text-muted text-center mt-2 d-none d-sm-block">
              Ответ формируется на основе актуальных данных сайта, меню и заказов «Везу Ролл»
            </div>
          </div>
        </div>
      </div>
    </VCard>
  </div>
</template>

<style scoped>
.ai-chat-wrapper {
  height: calc(100vh - 120px);
  min-height: 480px;
  max-width: 100%;
  width: 100%;
  overflow-x: hidden;
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  max-width: 100%;
  overflow-x: hidden;
}

.chat-sidebar {
  width: 300px;
  min-width: 300px;
  background-color: rgb(var(--v-theme-surface));
}

.chat-main {
  min-width: 0;
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
  background-color: rgb(var(--v-theme-background));
}

.ai-selector-agent {
  min-width: 170px;
  max-width: 220px;
}

.ai-selector-model {
  min-width: 160px;
  max-width: 200px;
}

@media (max-width: 600px) {
  .ai-chat-wrapper {
    height: calc(100vh - 75px);
    min-height: 400px;
  }
  .ai-header-controls {
    width: 100%;
  }
  .ai-selector-agent,
  .ai-selector-model {
    min-width: 100% !important;
    max-width: 100% !important;
    width: 100% !important;
  }
  .user-bubble, .assistant-bubble {
    max-width: 90% !important;
  }
}

.session-list {
  scrollbar-width: thin;
}

.session-item {
  border: 1px solid transparent;
}

.session-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.06);
}

.active-session {
  background-color: rgba(var(--v-theme-primary), 0.12) !important;
  border-color: rgba(var(--v-theme-primary), 0.3) !important;
}

.session-delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .session-delete-btn {
  opacity: 1;
}

.user-bubble {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)), #556ee6);
  max-width: 75%;
}

.assistant-bubble {
  background-color: rgb(var(--v-theme-surface));
  max-width: 82%;
  line-height: 1.6;
}

.hover-elevate:hover {
  border-color: rgb(var(--v-theme-primary)) !important;
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.1);
  transform: translateY(-2px);
}

.quick-chip:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
}

/* Typing Dots Animation */
.typing-dots span {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: rgb(var(--v-theme-primary));
  margin: 0 2px;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Markdown styling inside bubbles */
:deep(.ai-code-block) {
  background-color: #1e1e2f;
  color: #f8f8f2;
  padding: 12px;
  border-radius: 8px;
  font-family: monospace;
  font-size: 0.88rem;
  overflow-x: auto;
  margin: 8px 0;
}

:deep(.ai-inline-code) {
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
}

:deep(li) {
  margin-bottom: 4px;
}
</style>
