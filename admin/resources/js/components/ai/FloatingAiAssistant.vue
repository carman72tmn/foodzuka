<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import '@/../styles/ai-assistants.css'

const route = useRoute()
const router = useRouter()

// Состояние помощника
const isVisible = ref(false)
const isChatOpen = ref(false)
const isMinimized = ref(false)
const assistantData = ref(null)
const allAssistants = ref([])

const getSkinIcon = (skin) => {
  const map = {
    chef_male: 'bx-restaurant',
    admin_female: 'bx-user-check',
    courier_male: 'bx-cycling',
    cyber_bot: 'bx-bot',
    fox_mascot: 'bx-smile',
    custom: 'bx-image'
  }
  return map[skin] || 'bx-bot'
}

const switchAssistant = (ast) => {
  if (!ast || ast.id === assistantData.value?.id) return
  assistantData.value = ast
  localStorage.setItem('preferred_assistant_id', String(ast.id))
  pollOperationalTips()
  loadChatHistory()
}

const loadAllActiveAssistants = async () => {
  try {
    const res = await axios.get('/api/v1/ai-assistants/all-active')
    if (res.data && Array.isArray(res.data)) {
      allAssistants.value = res.data
    }
  } catch (e) {
    console.debug('Failed to load active assistants', e)
  }
}
const operationalData = ref({
  tips: [],
  metrics: {
    total_orders_today: 0,
    revenue_today: 0,
    active_in_progress: 0,
    avg_check: 0,
    stuck_new_count: 0,
    stuck_kitchen_count: 0,
    stuck_delivery_count: 0
  },
  status: 'ok'
})

// Чат
const userMessage = ref('')
const isSending = ref(false)
const messages = ref([])
const chatBodyRef = ref(null)
const sessionId = ref(`session_${Math.random().toString(36).substring(2, 9)}`)
const soundMuted = ref(false)

// Drag and drop перемещение по экрану
const pos = ref({ x: window.innerWidth - 90, y: window.innerHeight - 110 })
const isDragging = ref(false)
let dragOffset = { x: 0, y: 0 }
let pollInterval = null

// Быстрые шаблоны вопросов
const quickTags = [
  '🍳 Ситуация на кухне',
  '🚴 Где курьеры?',
  '📊 Выручка и заказы',
  '⚠️ Что требует внимания?'
]

// Индикатор статуса
const statusClass = computed(() => {
  if (operationalData.value.metrics.stuck_new_count > 0) return 'status-warning'
  if (operationalData.value.tips.length > 0) return 'status-attention'
  return 'status-ok'
})

const statusBadgeText = computed(() => {
  const count = operationalData.value.tips.length
  return count > 0 ? count : '✓'
})

// Загрузка помощника для текущей страницы
const loadAssistantForCurrentPage = async () => {
  try {
    const res = await axios.get('/api/v1/ai-assistants/active-for-page', {
      params: { route: route.path }
    })
    if (res.data && res.data.active && res.data.assistant) {
      assistantData.value = res.data.assistant
      operationalData.value.tips = res.data.tips || []
      operationalData.value.metrics = res.data.metrics || operationalData.value.metrics
      operationalData.value.status = res.data.status || 'ok'
      isVisible.value = true
      
      await loadAllActiveAssistants()
      // Проверяем, есть ли сохраненный выбор пользователя
      const preferredId = localStorage.getItem('preferred_assistant_id')
      if (preferredId && allAssistants.value.length > 0) {
        const found = allAssistants.value.find(a => String(a.id) === String(preferredId))
        if (found) {
          assistantData.value = found
        }
      }
      // Загружаем сохраненную историю
      loadChatHistory()
    } else {
      isVisible.value = false
    }
  } catch (e) {
    console.debug('Floating assistant init check', e)
  }
}

// Периодический легкий опрос подсказок (0 токенов)
const pollOperationalTips = async () => {
  if (!assistantData.value || !assistantData.value.id) return
  try {
    const res = await axios.get('/api/v1/ai-assistants/operational-tips', {
      params: { assistant_id: assistantData.value.id }
    })
    if (res.data) {
      const prevStuck = operationalData.value.metrics.stuck_new_count || 0
      operationalData.value.tips = res.data.tips || []
      operationalData.value.metrics = res.data.metrics || operationalData.value.metrics
      operationalData.value.status = res.data.status || 'ok'

      // Звуковой сигнал при появлении критического зависшего заказа
      if (!soundMuted.value && assistantData.value.allow_sound_alerts) {
        if (operationalData.value.metrics.stuck_new_count > prevStuck && operationalData.value.metrics.stuck_new_count > 0) {
          playAlertBeep()
        }
      }
    }
  } catch (e) {
    // Тихо игнорируем сетевые сбои поллинга
  }
}

const playAlertBeep = () => {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(880, ctx.currentTime)
    gain.gain.setValueAtTime(0.08, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start()
    osc.stop(ctx.currentTime + 0.35)
  } catch (e) {
    // audio context not allowed before user gesture
  }
}

// Загрузка истории диалога
const loadChatHistory = async () => {
  if (!assistantData.value) return
  try {
    const res = await axios.get(`/api/v1/ai-assistants/${assistantData.value.id}/history`, {
      params: { session_id: sessionId.value }
    })
    if (Array.isArray(res.data) && res.data.length > 0) {
      messages.value = res.data
      scrollToBottom()
    }
  } catch (e) {
    console.debug('Failed to load history', e)
  }
}

// Отправка вопроса помощнику
const sendMessage = async (textToSend) => {
  const text = (typeof textToSend === 'string' ? textToSend : userMessage.value).trim()
  if (!text || isSending.value || !assistantData.value) return

  userMessage.value = ''
  messages.value.push({
    role: 'user',
    content: text,
    created_at: new Date().toISOString()
  })
  scrollToBottom()

  isSending.value = true
  try {
    const res = await axios.post(`/api/v1/ai-assistants/${assistantData.value.id}/chat`, {
      message: text,
      session_id: sessionId.value,
      page_route: route.path
    })
    if (res.data) {
      messages.value.push({
        role: 'assistant',
        content: res.data.reply,
        created_at: new Date().toISOString()
      })
      scrollToBottom()
    }
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      content: 'Извините, возникла заминка при связи с сервером. Я на связи и слежу за процессами!',
      created_at: new Date().toISOString()
    })
  } finally {
    isSending.value = false
    scrollToBottom()
  }
}

const clearHistory = async () => {
  if (!assistantData.value) return
  try {
    await axios.delete(`/api/v1/ai-assistants/${assistantData.value.id}/history`, {
      params: { session_id: sessionId.value }
    })
    messages.value = []
  } catch (e) {
    console.error(e)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatBodyRef.value) {
      chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
    }
  })
}

const toggleChat = () => {
  if (isDragging.value) return
  isChatOpen.value = !isChatOpen.value
  if (isChatOpen.value) {
    scrollToBottom()
  }
}

// Drag & Drop логика
const startDrag = (e) => {
  isDragging.value = false
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY
  dragOffset.x = clientX - pos.value.x
  dragOffset.y = clientY - pos.value.y

  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
  window.addEventListener('touchmove', onDrag)
  window.addEventListener('touchend', stopDrag)
}

const onDrag = (e) => {
  isDragging.value = true
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY

  let newX = clientX - dragOffset.x
  let newY = clientY - dragOffset.y

  // Ограничиваем рамками окна
  newX = Math.max(16, Math.min(window.innerWidth - 80, newX))
  newY = Math.max(16, Math.min(window.innerHeight - 80, newY))

  pos.value = { x: newX, y: newY }
}

const stopDrag = () => {
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
  window.removeEventListener('touchmove', onDrag)
  window.removeEventListener('touchend', stopDrag)

  // Сохраняем позицию
  try {
    localStorage.setItem('ai_assistant_pos', JSON.stringify(pos.value))
  } catch (e) {}

  setTimeout(() => {
    isDragging.value = false
  }, 100)
}

// Восстановление сохраненной позиции
const restorePosition = () => {
  try {
    const saved = localStorage.getItem('ai_assistant_pos')
    if (saved) {
      const p = JSON.parse(saved)
      if (p.x < window.innerWidth && p.y < window.innerHeight) {
        pos.value = p
      }
    }
  } catch (e) {}
}

// Следим за сменой маршрута в vue-router
watch(() => route.path, () => {
  loadAssistantForCurrentPage()
})

onMounted(() => {
  restorePosition()
  loadAssistantForCurrentPage()
  pollInterval = setInterval(pollOperationalTips, 30000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<template>
  <div
    v-if="isVisible && assistantData"
    class="floating-assistant-wrapper"
    :style="{ left: `${pos.x}px`, top: `${pos.y}px` }"
  >
    <!-- Анимированный Аватар Помощника -->
    <div
      class="floating-assistant-avatar"
      :class="[
        assistantData.avatar_animation_mode === 'alive' ? 'avatar-anim-alive' :
        assistantData.avatar_animation_mode === 'float' ? 'avatar-anim-float' :
        assistantData.avatar_animation_mode === 'pulse' ? 'avatar-anim-pulse' : ''
      ]"
      @mousedown="startDrag"
      @touchstart="startDrag"
      @click="toggleChat"
      :title="`${assistantData.name} — ${assistantData.role_title}`"
    >
      <!-- Бейдж статуса -->
      <div class="avatar-status-badge" :class="statusClass">
        {{ statusBadgeText }}
      </div>

      <!-- Графика Аватара по Скину -->
      <!-- 1. Шеф-повар -->
      <svg v-if="assistantData.avatar_skin === 'chef_male'" viewBox="0 0 48 48" width="42" height="42" fill="none">
        <circle cx="24" cy="28" r="14" fill="#ffb88c" />
        <!-- Поварской колпак -->
        <path d="M14 20 C10 10, 20 6, 24 10 C28 6, 38 10, 34 20 Z" fill="#ffffff" />
        <rect x="14" y="19" width="20" height="4" rx="2" fill="#e2e8f0" />
        <!-- Глаза и улыбка -->
        <circle cx="19" cy="26" r="2" fill="#2d3748" />
        <circle cx="29" cy="26" r="2" fill="#2d3748" />
        <!-- Поварские усы -->
        <path d="M17 31 C21 34, 24 32, 24 31 C24 32, 27 34, 31 31" stroke="#4a5568" stroke-width="2.2" stroke-linecap="round" fill="none" />
        <!-- Китель -->
        <path d="M12 42 C12 37, 16 35, 24 35 C32 35, 36 37, 36 42 Z" fill="#ffffff" />
        <!-- Красный шейный платок -->
        <path d="M21 35 L24 38 L27 35 Z" fill="#e53e3e" />
      </svg>

      <!-- 2. Администратор Анна -->
      <svg v-else-if="assistantData.avatar_skin === 'admin_female'" viewBox="0 0 48 48" width="42" height="42" fill="none">
        <circle cx="24" cy="24" r="13" fill="#fed7aa" />
        <!-- Прическа каре -->
        <path d="M11 24 C11 14, 18 10, 24 10 C30 10, 37 14, 37 24 C37 28, 35 30, 34 30 C33 26, 33 20, 31 17 C28 14, 20 14, 17 17 C15 20, 15 26, 14 30 C13 30, 11 28, 11 24 Z" fill="#92400e" />
        <!-- Очки -->
        <rect x="15" y="21" width="7" height="5" rx="1.5" stroke="#7c3aed" stroke-width="1.8" fill="rgba(255,255,255,0.3)" />
        <rect x="26" y="21" width="7" height="5" rx="1.5" stroke="#7c3aed" stroke-width="1.8" fill="rgba(255,255,255,0.3)" />
        <line x1="22" y1="23.5" x2="26" y2="23.5" stroke="#7c3aed" stroke-width="1.8" />
        <!-- Улыбка -->
        <path d="M20 30 Q24 33 28 30" stroke="#b91c1c" stroke-width="1.8" stroke-linecap="round" fill="none" />
        <!-- Гарнитура связи -->
        <path d="M11 22 Q10 27 16 30" stroke="#64748b" stroke-width="1.5" fill="none" />
        <circle cx="16" cy="30" r="1.5" fill="#10b981" />
        <!-- Деловой костюм -->
        <path d="M12 44 C12 38, 17 36, 24 36 C31 36, 36 38, 36 44 Z" fill="#4f46e5" />
      </svg>

      <!-- 3. Курьер Макс -->
      <svg v-else-if="assistantData.avatar_skin === 'courier_male'" viewBox="0 0 48 48" width="42" height="42" fill="none">
        <circle cx="24" cy="26" r="13" fill="#fcd34d" />
        <!-- Кепка вперед -->
        <path d="M13 20 C13 13, 20 11, 28 12 L37 15 L28 19 L13 20 Z" fill="#ef4444" />
        <path d="M28 12 L38 15 L29 18 Z" fill="#dc2626" />
        <!-- Глаза и озорная улыбка -->
        <circle cx="19" cy="26" r="1.8" fill="#1f2937" />
        <circle cx="28" cy="26" r="1.8" fill="#1f2937" />
        <path d="M20 31 Q24 35 28 31" stroke="#1f2937" stroke-width="1.8" stroke-linecap="round" fill="none" />
        <!-- Брендированное худи -->
        <path d="M12 44 C12 38, 17 35, 24 35 C31 35, 36 38, 36 44 Z" fill="#ef4444" />
        <!-- Термосумка на лямке -->
        <line x1="14" y1="36" x2="34" y2="44" stroke="#1f2937" stroke-width="2.5" />
      </svg>

      <!-- 4. Кибер-Робот Нео -->
      <svg v-else-if="assistantData.avatar_skin === 'cyber_bot'" viewBox="0 0 48 48" width="42" height="42" fill="none">
        <rect x="12" y="14" width="24" height="22" rx="8" fill="#1e1e2d" stroke="#7367f0" stroke-width="2.2" />
        <!-- Антенна -->
        <line x1="24" y1="14" x2="24" y2="8" stroke="#7367f0" stroke-width="2" />
        <circle cx="24" cy="7" r="2.5" fill="#00cfe8" />
        <!-- Неоновый светящийся визор -->
        <rect x="16" y="20" width="16" height="8" rx="4" fill="#0f172a" stroke="#00cfe8" stroke-width="1.5" />
        <circle cx="20" cy="24" r="2" fill="#00cfe8" />
        <circle cx="28" cy="24" r="2" fill="#00cfe8" />
        <!-- Ротовой звуковой датчик -->
        <line x1="20" y1="31" x2="28" y2="31" stroke="#7367f0" stroke-width="2" stroke-linecap="round" />
      </svg>

      <!-- 5. Лис Везунчик -->
      <svg v-else-if="assistantData.avatar_skin === 'fox_mascot'" viewBox="0 0 48 48" width="42" height="42" fill="none">
        <!-- Ушки лисы -->
        <polygon points="12,18 17,6 23,17" fill="#ea580c" />
        <polygon points="14,16 17,9 20,16" fill="#fef08a" />
        <polygon points="36,18 31,6 25,17" fill="#ea580c" />
        <polygon points="34,16 31,9 28,16" fill="#fef08a" />
        <!-- Мордочка -->
        <circle cx="24" cy="27" r="14" fill="#ea580c" />
        <path d="M14 27 C14 34, 18 38, 24 38 C30 38, 34 34, 34 27 C34 22, 30 20, 24 20 C18 20, 14 22, 14 27 Z" fill="#ffffff" />
        <!-- Глазки и носик -->
        <circle cx="19" cy="27" r="2" fill="#1e293b" />
        <circle cx="29" cy="27" r="2" fill="#1e293b" />
        <circle cx="24" cy="32" r="2.2" fill="#1e293b" />
        <path d="M21 34 Q24 37 27 34" stroke="#1e293b" stroke-width="1.5" fill="none" stroke-linecap="round" />
      </svg>

      <!-- Пользовательский аватар -->
      <img
        v-else-if="assistantData.avatar_custom_url"
        :src="assistantData.avatar_custom_url"
        alt="Avatar"
        style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;"
      />
      <!-- Иконка по умолчанию -->
      <v-icon v-else size="32" icon="bx-bot" color="primary" />
    </div>

    <!-- Всплывающий интерактивный Чат-Помощник -->
    <div v-if="isChatOpen" class="assistant-chat-panel">
      <!-- Шапка -->
      <div class="assistant-chat-header">
        <v-menu v-if="allAssistants.length > 1" offset-y>
          <template #activator="{ props }">
            <div class="assistant-header-info cursor-pointer d-flex align-center gap-2" v-bind="props" title="Нажмите, чтобы сменить помощника">
              <v-avatar size="32" color="rgba(115, 103, 240, 0.2)">
                <v-icon size="18" :icon="getSkinIcon(assistantData.avatar_skin)" color="primary" />
              </v-avatar>
              <div>
                <div class="assistant-header-title d-flex align-center gap-1 font-weight-bold">
                  <span>{{ assistantData.name }}</span>
                  <v-icon size="16" icon="bx-chevron-down" />
                </div>
                <div class="assistant-header-subtitle">{{ assistantData.role_title }}</div>
              </div>
            </div>
          </template>

          <v-list density="compact" class="py-1" style="min-width: 220px;">
            <v-list-subheader class="text-caption font-weight-bold">Сменить помощника:</v-list-subheader>
            <v-list-item
              v-for="ast in allAssistants"
              :key="ast.id"
              :active="ast.id === assistantData.id"
              class="cursor-pointer"
              @click="switchAssistant(ast)"
            >
              <template #prepend>
                <v-avatar size="28" :color="ast.id === assistantData.id ? 'primary' : 'secondary'" variant="tonal">
                  <v-icon size="16" :icon="getSkinIcon(ast.avatar_skin)" />
                </v-avatar>
              </template>
              <v-list-item-title class="font-weight-medium text-body-2">{{ ast.name }}</v-list-item-title>
              <v-list-item-subtitle class="text-caption text-truncate">{{ ast.role_title }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-menu>

        <div v-else class="assistant-header-info">
          <v-avatar size="32" color="rgba(115, 103, 240, 0.2)">
            <v-icon size="18" :icon="getSkinIcon(assistantData.avatar_skin)" color="primary" />
          </v-avatar>
          <div>
            <div class="assistant-header-title">{{ assistantData.name }}</div>
            <div class="assistant-header-subtitle">{{ assistantData.role_title }}</div>
          </div>
        </div>

        <div class="d-flex align-center gap-1">
          <!-- Звук вкл/выкл -->
          <v-btn
            icon
            variant="text"
            size="x-small"
            :color="soundMuted ? 'secondary' : 'primary'"
            :title="soundMuted ? 'Включить звук' : 'Выключить звук'"
            @click="soundMuted = !soundMuted"
          >
            <v-icon size="16" :icon="soundMuted ? 'bx-volume-mute' : 'bx-volume-full'" />
          </v-btn>

          <!-- Очистка диалога -->
          <v-btn
            icon
            variant="text"
            size="x-small"
            color="secondary"
            title="Очистить историю диалога"
            @click="clearHistory"
          >
            <v-icon size="16" icon="bx-trash" />
          </v-btn>

          <!-- Закрыть -->
          <v-btn
            icon
            variant="text"
            size="x-small"
            title="Свернуть"
            @click="isChatOpen = false"
          >
            <v-icon size="16" icon="bx-x" />
          </v-btn>
        </div>
      </div>

      <!-- Экспресс-сводка заведения за текущие сутки -->
      <div class="assistant-metrics-bar">
        <div class="assistant-metric-chip" title="Выручка сегодня">
          <v-icon size="12" icon="bx-ruble" color="success" />
          <span>{{ operationalData.metrics.revenue_today }} ₽</span>
        </div>
        <div class="assistant-metric-chip" title="Заказов за сегодня">
          <v-icon size="12" icon="bx-receipt" color="primary" />
          <span>{{ operationalData.metrics.total_orders_today }} зак.</span>
        </div>
        <div class="assistant-metric-chip" title="В процессе приготовления/доставки">
          <v-icon size="12" icon="bx-time-five" color="warning" />
          <span>{{ operationalData.metrics.active_in_progress }} в работе</span>
        </div>
      </div>

      <!-- Тело сообщений и подсказок -->
      <div ref="chatBodyRef" class="assistant-chat-body">
        <!-- Блок автоматических оперативных подсказок (0 токенов!) -->
        <div
          v-for="tip in operationalData.tips"
          :key="tip.id"
          class="assistant-tip-alert"
          :class="`severity-${tip.severity}`"
        >
          <div class="d-flex align-center gap-1 font-weight-bold">
            <v-icon
              size="14"
              :icon="tip.severity === 'high' ? 'bx-error-circle' : 'bx-info-circle'"
            />
            <span>{{ tip.title }}</span>
          </div>
          <div class="mt-1">{{ tip.text }}</div>
          <router-link
            v-if="tip.action_url"
            :to="tip.action_url"
            class="assistant-tip-btn"
            @click="isChatOpen = false"
          >
            <span>Посмотреть в заказах</span>
            <v-icon size="12" icon="bx-right-arrow-alt" />
          </router-link>
        </div>

        <!-- Приветственное сообщение если история пуста -->
        <div v-if="messages.length === 0 && operationalData.tips.length === 0" class="assistant-msg assistant-msg-bot">
          👋 Привет! Я — <strong>{{ assistantData.name }}</strong>.
          Слежу за текущими заказами, временем отдачи блюд и доставкой. Чем могу помочь прямо сейчас?
        </div>

        <!-- История диалога -->
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="assistant-msg"
          :class="msg.role === 'user' ? 'assistant-msg-user' : 'assistant-msg-bot'"
        >
          <div style="white-space: pre-wrap;">{{ msg.content }}</div>
        </div>

        <!-- Индикатор ожидания ответа -->
        <div v-if="isSending" class="assistant-msg assistant-msg-bot d-flex align-center gap-2">
          <v-progress-circular indeterminate size="16" width="2" color="primary" />
          <span style="font-size: 11px; opacity: 0.8;">{{ assistantData.name }} анализирует...</span>
        </div>
      </div>

      <!-- Подвал с быстрыми кнопками и полем ввода -->
      <div class="assistant-chat-footer">
        <!-- Быстрые шаблоны -->
        <div class="assistant-quick-tags">
          <span
            v-for="(tag, tIdx) in quickTags"
            :key="tIdx"
            class="assistant-quick-tag"
            @click="sendMessage(tag)"
          >
            {{ tag }}
          </span>
        </div>

        <!-- Строка ввода -->
        <div class="assistant-input-row">
          <input
            v-model="userMessage"
            class="assistant-input-field"
            type="text"
            placeholder="Спросить о процессах, кухне, доставке..."
            :disabled="isSending"
            @keydown.enter="sendMessage"
          />
          <v-btn
            icon
            size="small"
            color="primary"
            :loading="isSending"
            :disabled="!userMessage.trim()"
            @click="sendMessage"
          >
            <v-icon size="16" icon="bx-send" />
          </v-btn>
        </div>
      </div>
    </div>
  </div>
</template>
