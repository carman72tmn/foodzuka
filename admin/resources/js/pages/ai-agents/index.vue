<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'

// ==========================================
// СОСТОЯНИЕ
// ==========================================
const loading = ref(false)
const sending = ref(false)
const sessions = ref([])
const activeSessionId = ref(null)
const messages = ref([])

const siteAgents = ref([])
const connections = ref([])
const quotaSummary = ref(null)

const selectedAgentCode = ref('stats_analyst')
const selectedConnectionId = ref(null)
const selectedModel = ref(null)
const inputMessage = ref('')
const chatContainer = ref(null)

const snackbar = ref({ show: false, text: '', color: 'success' })
const showSnackbar = (text, color = 'success') => { snackbar.value = { show: true, text, color } }

// Активный выбранный агент
const currentAgent = computed(() => {
  return siteAgents.value.find(a => a.agent_code === selectedAgentCode.value) || { title: 'ИИ Агент', description: '' }
})

// Активное подключение
const activeConnection = computed(() => {
  if (selectedConnectionId.value) {
    return connections.value.find(c => c.id === selectedConnectionId.value)
  }
  return connections.value.find(c => c.is_enabled)
})

// Текущая системная квота и лимиты выбранного ИИ
const currentQuota = computed(() => {
  if (quotaSummary.value && quotaSummary.value.connections && selectedConnectionId.value) {
    const found = quotaSummary.value.connections.find(c => c.id === selectedConnectionId.value)
    if (found) return found
  }
  if (quotaSummary.value) {
    return {
      tier_title: 'Общий пул активных ИИ',
      rpm_limit: activeConnection.value ? (activeConnection.value.rpm_limit || 15) : 15,
      today_requests: quotaSummary.value.total_today_requests,
      daily_requests_limit: quotaSummary.value.total_daily_requests_limit,
      requests_percent: quotaSummary.value.total_requests_percent,
      today_tokens: quotaSummary.value.total_today_tokens,
      daily_tokens_limit: quotaSummary.value.total_daily_tokens_limit,
      tokens_percent: quotaSummary.value.total_tokens_percent
    }
  }
  return {
    tier_title: 'Google Gemini (Free Tier)',
    rpm_limit: 15,
    today_requests: 0,
    daily_requests_limit: 1500,
    requests_percent: 0,
    today_tokens: 0,
    daily_tokens_limit: 1000000,
    tokens_percent: 0
  }
})

// Динамически подгруженные модели по ID подключения
const dynamicModels = ref({})
const loadingModels = ref(false)

// Рекомендуемые модели для текущего подключения
const recommendedModels = computed(() => {
  if (selectedConnectionId.value && dynamicModels.value[selectedConnectionId.value]) {
    return dynamicModels.value[selectedConnectionId.value]
  }

  const conn = activeConnection.value
  if (!conn || conn.provider_type === 'gemini') {
    return [
      'gemini-3.1-flash-lite',
      'gemini-3.5-flash-lite',
      'gemini-3.8-flash',
      'gemini-flash-latest',
      'gemini-pro-latest'
    ]
  }
  if (conn.provider_type === 'openai') {
    return ['gpt-4o-mini', 'gpt-4o']
  }
  if (conn.provider_type === 'gigachat') {
    return ['GigaChat', 'GigaChat-Pro']
  }
  if (conn.provider_type === 'yandexgpt') {
    return ['yandexgpt/latest', 'yandexgpt-lite/latest']
  }
  return [conn.default_model]
})

const fetchModelsForConnection = async (connId) => {
  if (!connId || dynamicModels.value[connId]) return
  loadingModels.value = true
  try {
    const res = await fetch(`/api/v1/ai-agents/connections/${connId}/models`)
    if (res.ok) {
      const list = await res.json()
      if (list && list.length > 0) {
        dynamicModels.value[connId] = list
      }
    }
  } catch (e) {
    console.error('Error fetching connection models:', e)
  } finally {
    loadingModels.value = false
  }
}

const onConnectionChange = async (connId) => {
  const c = connections.value.find(x => x.id === connId)
  if (c) selectedModel.value = c.default_model
  await fetchModelsForConnection(connId)
}

// ==========================================
// ЗАГРУЗКА ДАННЫХ
// ==========================================
const loadInitialData = async () => {
  loading.value = true
  try {
    const [agentsRes, connsRes, quotaRes, sessRes] = await Promise.all([
      fetch('/api/v1/ai-agents/site-agents'),
      fetch('/api/v1/ai-agents/connections'),
      fetch('/api/v1/ai-agents/quota-summary'),
      fetch('/api/v1/ai-agents/chat/sessions')
    ])

    if (agentsRes.ok) siteAgents.value = await agentsRes.json()
    if (connsRes.ok) {
      connections.value = await connsRes.json()
      if (connections.value.length > 0 && !selectedConnectionId.value) {
        selectedConnectionId.value = connections.value[0].id
        selectedModel.value = connections.value[0].default_model
      }
      if (selectedConnectionId.value) {
        fetchModelsForConnection(selectedConnectionId.value)
      }
    }
    if (quotaRes.ok) quotaSummary.value = await quotaRes.json()
    if (sessRes.ok) {
      sessions.value = await sessRes.json()
      if (sessions.value.length > 0) {
        selectSession(sessions.value[0].id)
      } else {
        createNewDialog()
      }
    }
  } catch (err) {
    showSnackbar('Ошибка загрузки данных чата', 'error')
  } finally {
    loading.value = false
  }
}

const selectSession = async (sessId) => {
  activeSessionId.value = sessId
  const sess = sessions.value.find(s => s.id === sessId)
  if (sess && sess.agent_code) {
    selectedAgentCode.value = sess.agent_code
  }

  try {
    const res = await fetch(`/api/v1/ai-agents/chat/sessions/${sessId}/messages`)
    if (res.ok) {
      messages.value = await res.json()
      scrollToBottom()
    }
  } catch (e) {
    console.error(e)
  }
}

const createNewDialog = async () => {
  try {
    const res = await fetch('/api/v1/ai-agents/chat/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: 'Новый диалог',
        agent_code: selectedAgentCode.value
      })
    })
    if (res.ok) {
      const newSess = await res.json()
      sessions.value.unshift(newSess)
      activeSessionId.value = newSess.id
      messages.value = []
    }
  } catch (e) {
    showSnackbar('Ошибка создания диалога', 'error')
  }
}

const deleteSession = async (sessId) => {
  try {
    const res = await fetch(`/api/v1/ai-agents/chat/sessions/${sessId}`, { method: 'DELETE' })
    if (res.ok) {
      sessions.value = sessions.value.filter(s => s.id !== sessId)
      if (activeSessionId.value === sessId) {
        if (sessions.value.length > 0) {
          selectSession(sessions.value[0].id)
        } else {
          createNewDialog()
        }
      }
      showSnackbar('Диалог удален')
    }
  } catch (e) {
    showSnackbar('Ошибка удаления диалога', 'error')
  }
}

const sendMessage = async () => {
  const text = inputMessage.value.trim()
  if (!text || sending.value) return

  // Добавляем сообщение пользователя в UI локально
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: text,
    created_at: new Date().toISOString()
  })
  inputMessage.value = ''
  sending.value = true
  scrollToBottom()

  try {
    const res = await fetch('/api/v1/ai-agents/chat/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_code: selectedAgentCode.value,
        message: text,
        session_id: activeSessionId.value,
        connection_id: selectedConnectionId.value,
        model: selectedModel.value
      })
    })

    const data = await res.json()
    if (res.ok) {
      messages.value.push({
        id: data.message_id,
        role: 'assistant',
        content: data.response,
        model: data.model,
        fallback_note: data.fallback_note,
        provider_name: data.provider_name,
        tokens_used: data.tokens_used,
        latency_ms: data.latency_ms,
        created_at: new Date().toISOString()
      })
      activeSessionId.value = data.session_id

      // Обновляем шкалу квоты
      await refreshQuota()
      scrollToBottom()
    } else {
      showSnackbar(data.detail || 'Ошибка ответа модели', 'error')
    }
  } catch (e) {
    showSnackbar('Сбой отправки запроса', 'error')
  } finally {
    sending.value = false
  }
}

const refreshQuota = async () => {
  try {
    const res = await fetch('/api/v1/ai-agents/quota-summary')
    if (res.ok) quotaSummary.value = await res.json()
  } catch (e) {
    console.error(e)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

// Быстрые подсказки
const sendPreset = (prompt) => {
  inputMessage.value = prompt
  sendMessage()
}

onMounted(() => {
  loadInitialData()
})
</script>

<template>
  <div class="ai-chat-layout">
    <!-- Верхняя панель шкалы доступных токенов и запросов -->
    <VCard class="mb-4 pa-4 border rounded-lg">
      <div class="d-flex flex-wrap justify-space-between align-center gap-4">
        <div>
          <div class="d-flex align-center">
            <i class="bx bx-bot text-h5 text-primary me-2"></i>
            <h2 class="text-h6 font-weight-bold mb-0">Центр ИИ Агентов</h2>
            <VChip size="small" color="primary" variant="tonal" class="ms-3">
              {{ currentAgent.title }}
            </VChip>
          </div>
          <p class="text-caption text-medium-emphasis mb-0 mt-1">
            {{ currentAgent.description || 'Интерактивное общение с ИИ и управление данными сайта в реальном времени' }}
          </p>
        </div>

        <!-- Шкала токенов и системных лимитов запросов -->
        <div class="d-flex flex-wrap align-center gap-6">
          <!-- Шкала запросов -->
          <div style="min-width: 230px;">
            <div class="d-flex justify-space-between text-caption mb-1">
              <span class="font-weight-medium">
                <i class="bx bx-transfer-alt me-1"></i>Запросы:
              </span>
              <strong>{{ currentQuota.today_requests }} / {{ currentQuota.daily_requests_limit }}</strong>
            </div>
            <VProgressLinear
              :model-value="currentQuota.requests_percent"
              color="primary"
              height="8"
              rounded
            />
            <div class="d-flex justify-space-between text-caption text-grey mt-1">
              <span>{{ currentQuota.tier_title }}</span>
              <span>Осталось: {{ Math.max(0, currentQuota.daily_requests_limit - currentQuota.today_requests) }}</span>
            </div>
          </div>

          <!-- Шкала токенов -->
          <div style="min-width: 230px;">
            <div class="d-flex justify-space-between text-caption mb-1">
              <span class="font-weight-medium">
                <i class="bx bx-coin me-1"></i>Токены:
              </span>
              <strong>{{ (currentQuota.today_tokens || 0).toLocaleString() }} / {{ (currentQuota.daily_tokens_limit || 1000000).toLocaleString() }}</strong>
            </div>
            <VProgressLinear
              :model-value="currentQuota.tokens_percent"
              color="success"
              height="8"
              rounded
            />
            <div class="d-flex justify-space-between text-caption text-grey mt-1">
              <span>Лимит: {{ currentQuota.rpm_limit }} RPM</span>
              <span>Осталось: {{ Math.max(0, (currentQuota.daily_tokens_limit || 1000000) - (currentQuota.today_tokens || 0)).toLocaleString() }}</span>
            </div>
          </div>

          <VBtn
            to="/settings/ai-agents"
            color="secondary"
            variant="outlined"
            size="small"
            prepend-icon="bx-cog"
          >
            Настройки ИИ
          </VBtn>
        </div>
      </div>
    </VCard>

    <!-- Основной блок чата -->
    <VRow>
      <!-- Боковая панель: выбор агента, модели и история диалогов -->
      <VCol cols="12" md="3">
        <VCard class="pa-4 border rounded-lg h-100 d-flex flex-column justify-space-between">
          <div>
            <div class="font-weight-bold text-subtitle-2 mb-2">1. Выбор ИИ Агента</div>
            <VSelect
              v-model="selectedAgentCode"
              :items="siteAgents"
              item-title="title"
              item-value="agent_code"
              density="compact"
              class="mb-3"
            />

            <div class="font-weight-bold text-subtitle-2 mb-2">2. Подключение и Модель</div>
            <VSelect
              v-model="selectedConnectionId"
              :items="connections"
              item-title="name"
              item-value="id"
              density="compact"
              class="mb-2"
              @update:model-value="onConnectionChange"
            />

            <VCombobox
              v-model="selectedModel"
              :items="recommendedModels"
              label="Модель ИИ"
              density="compact"
              class="mb-4"
              :loading="loadingModels"
              placeholder="gemini-3.1-flash-lite, gpt-4o"
            />

            <VDivider class="mb-3" />

            <div class="d-flex justify-space-between align-center mb-2">
              <span class="font-weight-bold text-subtitle-2">Диалоги</span>
              <VBtn size="x-small" color="primary" variant="tonal" prepend-icon="bx-plus" @click="createNewDialog">
                Новый
              </VBtn>
            </div>

            <!-- Список сессий -->
            <VList density="compact" class="py-0 session-list" style="max-height: 280px; overflow-y: auto;">
              <VListItem
                v-for="s in sessions"
                :key="s.id"
                :active="s.id === activeSessionId"
                rounded
                class="mb-1"
                @click="selectSession(s.id)"
              >
                <template #prepend>
                  <i class="bx bx-message-dots text-primary me-2"></i>
                </template>
                <VListItemTitle class="text-caption font-weight-medium text-truncate">
                  {{ s.title }}
                </VListItemTitle>
                <template #append>
                  <VBtn
                    icon="bx-x"
                    size="x-small"
                    variant="text"
                    color="grey"
                    @click.stop="deleteSession(s.id)"
                  />
                </template>
              </VListItem>
            </VList>
          </div>

          <div class="mt-4 pt-3 border-t">
            <div class="text-caption text-grey mb-1">
              <i class="bx bx-shield-check text-success me-1"></i>
              Канал: <strong>{{ activeConnection?.provider_group === 'ru' ? 'Прямой РФ (без прокси)' : 'Через активный прокси' }}</strong>
            </div>
            <div class="text-caption text-grey">
              RPM лимит: <strong>{{ activeConnection?.rpm_limit || 60 }} запр/мин</strong>
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- Окно сообщений и поле ввода -->
      <VCol cols="12" md="9">
        <VCard class="border rounded-lg d-flex flex-column" style="height: 680px;">
          <!-- Шапка чата с пресетами -->
          <div class="pa-3 border-b bg-surface d-flex flex-wrap justify-space-between align-center gap-2">
            <div class="d-flex align-center">
              <VAvatar color="primary-lighten-5" class="text-primary me-2" size="32">
                <i class="bx bx-chat"></i>
              </VAvatar>
              <div class="font-weight-bold text-body-2">
                {{ currentAgent.title }}
                <span class="text-caption text-grey ms-2">({{ selectedModel || 'По умолчанию' }})</span>
              </div>
            </div>

            <!-- Быстрые вопросы -->
            <div class="d-flex gap-1 flex-wrap">
              <VBtn size="x-small" variant="tonal" color="primary" @click="sendPreset('Сделай краткую сводку по выручке и среднему чеку за последние дни')">
                📊 Выручка
              </VBtn>
              <VBtn size="x-small" variant="tonal" color="info" @click="sendPreset('Какие блюда в меню сейчас самые популярные и какая у них стоимость?')">
                🍣 Блюда
              </VBtn>
              <VBtn size="x-small" variant="tonal" color="warning" @click="sendPreset('Придумай эмпатичный ответ на отзыв с оценкой 3 звезды за опоздание курьера')">
                💬 Ответ на отзыв
              </VBtn>
            </div>
          </div>

          <!-- Лента сообщений -->
          <div ref="chatContainer" class="flex-grow-1 pa-4 overflow-y-auto chat-messages-container">
            <div v-if="messages.length === 0" class="text-center py-12 text-grey">
              <i class="bx bx-bot text-h2 mb-3 text-primary-lighten-3 d-block"></i>
              <div class="font-weight-bold text-subtitle-1 mb-1">Готов к работе с сайтом!</div>
              <div class="text-caption" style="max-width: 480px; margin: 0 auto;">
                Задайте вопрос агенту — он подключен к базе данных (заказы, выручка OLAP, блюда, отзывы) и мгновенно предоставит точный ответ.
              </div>
            </div>

            <div
              v-for="m in messages"
              :key="m.id"
              :class="['d-flex mb-4', m.role === 'user' ? 'justify-end' : 'justify-start']"
            >
              <div
                :class="[
                  'chat-bubble pa-3 rounded-lg',
                  m.role === 'user' ? 'chat-bubble-user bg-primary text-white' : 'chat-bubble-ai bg-surface border'
                ]"
                style="max-width: 82%;"
              >
                <div class="d-flex align-center justify-space-between mb-1" style="font-size: 0.75rem; opacity: 0.85;">
                  <span class="font-weight-bold">
                    {{ m.role === 'user' ? 'Вы' : (m.provider_name || currentAgent.title) }}
                  </span>
                  <span v-if="m.latency_ms" class="ms-3">{{ m.latency_ms }} мс • {{ m.tokens_used }} токенов</span>
                </div>

                <div class="chat-text" style="white-space: pre-wrap; word-break: break-word; line-height: 1.5;">
                  {{ m.content }}
                </div>

                <div v-if="m.fallback_note" class="text-caption text-warning mt-2 pt-1 border-t d-flex align-center">
                  <i class="bx bx-info-circle me-1"></i>
                  <span>{{ m.fallback_note }}</span>
                </div>
              </div>
            </div>

            <!-- Индикатор генерации -->
            <div v-if="sending" class="d-flex justify-start mb-3">
              <div class="chat-bubble pa-3 rounded-lg bg-surface border d-flex align-center">
                <i class="bx bx-loader-alt bx-spin text-primary me-2"></i>
                <span class="text-caption text-grey">ИИ агент анализирует данные сайта и формирует ответ...</span>
              </div>
            </div>
          </div>

          <!-- Поле ввода сообщения -->
          <div class="pa-3 border-t bg-surface">
            <VRow no-gutters align="center" class="gap-2">
              <VCol>
                <VTextField
                  v-model="inputMessage"
                  placeholder="Введите запрос к агенту (например: проанализируй выручку за вчера)..."
                  density="comfortable"
                  variant="outlined"
                  hide-details
                  :disabled="sending"
                  @keydown.enter="sendMessage"
                />
              </VCol>
              <VCol cols="auto">
                <VBtn
                  color="primary"
                  icon="bx-send"
                  :loading="sending"
                  :disabled="!inputMessage.trim()"
                  @click="sendMessage"
                />
              </VCol>
            </VRow>
          </div>
        </VCard>
      </VCol>
    </VRow>

    <VSnackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </VSnackbar>
  </div>
</template>

<style scoped>
.chat-messages-container {
  background-color: rgba(var(--v-theme-surface), 0.5);
}

.chat-bubble {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}

.chat-bubble-user {
  border-bottom-right-radius: 2px !important;
}

.chat-bubble-ai {
  border-bottom-left-radius: 2px !important;
}

.session-list .v-list-item--active {
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
}
</style>
