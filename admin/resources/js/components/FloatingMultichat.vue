<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chatStore'

const router = useRouter()
const chatStore = useChatStore()

// Состояния окна
const isOpen = ref(false)
const isMinimized = ref(false)
const isExpanded = ref(false)

// Диалоги и сообщения
const dialogs = ref([])
const loadingDialogs = ref(false)
const markingAllAsRead = ref(false)
const searchQuery = ref('')
const selectedChannel = ref('all') // 'all', 'unread', 'max', 'vk', 'telegram'

const activeDialog = ref(null)
const messages = ref([])
const loadingMessages = ref(false)
const replyText = ref('')
const sending = ref(false)

const messagesContainerRef = ref(null)

// Каналы и фильтры
const channelOptions = computed(() => {
  const unreadTotal = dialogs.value.filter(d => !d.is_read || (d.unread_count && d.unread_count > 0)).length
  return [
    { value: 'all', label: 'Все' },
    { value: 'unread', label: unreadTotal > 0 ? `Новые (${unreadTotal})` : 'Новые', badge: unreadTotal },
    { value: 'max', label: 'MAX' },
    { value: 'vk', label: 'VK' },
    { value: 'telegram', label: 'TG' },
  ]
})

// Иконки и бейджи каналов
const getChannelIcon = (ch) => {
  if (!ch) return 'bx-message-rounded'
  const c = ch.toLowerCase()
  if (c.includes('max')) return 'bx-message-square-dots'
  if (c.includes('vk')) return 'bxl-vk'
  if (c.includes('telegram')) return 'bxl-telegram'
  if (c.includes('whatsapp')) return 'bxl-whatsapp'
  return 'bx-message-rounded'
}

const getChannelColor = (ch) => {
  if (!ch) return '#64748b'
  const c = ch.toLowerCase()
  if (c.includes('max')) return '#7360F2'
  if (c.includes('vk')) return '#2787F5'
  if (c.includes('telegram')) return '#0088cc'
  if (c.includes('whatsapp')) return '#25d366'
  return '#6366f1'
}

const getChannelLabel = (ch) => {
  if (!ch) return 'Чат'
  if (ch === 'max_user' || ch === 'max_bridge') return 'MAX Личный'
  if (ch === 'max_bot' || ch === 'max_account' || ch === 'max') return 'MAX Бот'
  if (ch === 'vk_user') return 'VK Личный'
  if (ch === 'vk') return 'VK Сообщество'
  if (ch === 'telegram_bot') return 'TG Бот'
  if (ch === 'telegram_user') return 'TG Личный'
  return ch
}

const formatTime = (dt) => {
  if (!dt) return ''
  try {
    const d = new Date(dt)
    const now = new Date()
    const isToday = d.toDateString() === now.toDateString()
    if (isToday) {
      return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    }
    return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' }) + ' ' + d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    return ''
  }
}

// Проверка, является ли диалог непрочитанным (новым)
const isDialogUnread = (d) => {
  if (!d) return false
  if (d.unread_count !== undefined && d.unread_count !== null) {
    return Number(d.unread_count) > 0
  }
  if (d.is_read !== undefined && d.is_read !== null) {
    return !d.is_read
  }
  return false
}

// Получение количества непрочитанных сообщений в диалоге
const getDialogUnreadCount = (d) => {
  if (!d) return 0
  if (d.unread_count !== undefined && d.unread_count !== null) {
    return Number(d.unread_count)
  }
  return d.is_read === false ? 1 : 0
}

// Получение текста последнего сообщения
const getDialogText = (d) => {
  if (!d) return ''
  const t = d.text || d.last_message || ''
  return t ? t.trim() : ''
}

// Получение времени последнего сообщения
const getDialogTime = (d) => {
  if (!d) return ''
  return d.last_message_time || d.created_at || ''
}

// Направление последнего сообщения (исходящее или входящее)
const isDialogOutbound = (d) => {
  if (!d) return false
  return d.direction === 'outbound' || d.last_message_direction === 'outbound'
}

// Вычисляемое общее количество непрочитанных диалогов
const unreadCount = computed(() => {
  return dialogs.value.filter(d => isDialogUnread(d)).length
})

// Фильтрация и интеллектуальная сортировка диалогов
// (НОВЫЕ И НЕПРОЧИТАННЫЕ ВСЕГДА ВВЕРХУ СПИСКА)
const filteredDialogs = computed(() => {
  let list = [...dialogs.value]

  if (selectedChannel.value === 'unread') {
    list = list.filter(d => isDialogUnread(d))
  } else if (selectedChannel.value !== 'all') {
    list = list.filter(d => {
      const c = (d.channel || '').toLowerCase()
      if (selectedChannel.value === 'max') return c.includes('max')
      if (selectedChannel.value === 'vk') return c.includes('vk')
      if (selectedChannel.value === 'telegram') return c.includes('telegram')
      return true
    })
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter(d => 
      (d.peer_name && d.peer_name.toLowerCase().includes(q)) ||
      (getDialogText(d).toLowerCase().includes(q)) ||
      (String(d.peer_id).includes(q)) ||
      (d.phone && d.phone.includes(q))
    )
  }

  // Сортировка:
  // 1. Непрочитанные диалоги СВЕРХУ (самые свежие по дате выше)
  // 2. Прочитанные диалоги НИЖЕ (также отсортированы по убыванию даты)
  list.sort((a, b) => {
    const aUnread = isDialogUnread(a) ? 1 : 0
    const bUnread = isDialogUnread(b) ? 1 : 0

    if (aUnread !== bUnread) {
      return bUnread - aUnread // Непрочитанные идут первыми
    }

    const aTime = getDialogTime(a) ? new Date(getDialogTime(a)).getTime() : 0
    const bTime = getDialogTime(b) ? new Date(getDialogTime(b)).getTime() : 0
    return bTime - aTime
  })

  return list
})

// Загрузка списка диалогов
const fetchDialogs = async () => {
  loadingDialogs.value = true
  try {
    const token = localStorage.getItem('access_token') || ''
    const res = await axios.get('/api/v1/multichat/dialogs', {
      params: { limit: 50 },
      headers: { Authorization: `Bearer ${token}` }
    })
    if (Array.isArray(res.data)) {
      dialogs.value = res.data
    }
  } catch (e) {
    console.warn('[FloatingMultichat] fetchDialogs error:', e)
  } finally {
    loadingDialogs.value = false
  }
}

// Отметить все прочитанными
const markAllAsRead = async () => {
  if (markingAllAsRead.value) return
  markingAllAsRead.value = true
  try {
    // Очищаем активные всплывающие плашки
    chatToasts.value.forEach(t => {
      if (t.timeoutId) clearTimeout(t.timeoutId)
    })
    chatToasts.value = []

    // Оптимистично выставляем статус прочтения у всех диалогов
    dialogs.value.forEach(d => {
      d.is_read = true
      d.unread_count = 0
    })
    if (activeDialog.value) {
      activeDialog.value.is_read = true
      activeDialog.value.unread_count = 0
    }

    const token = localStorage.getItem('access_token') || ''
    const payloadChannel = (selectedChannel.value && selectedChannel.value !== 'all' && selectedChannel.value !== 'unread') ? selectedChannel.value : null
    await axios.post('/api/v1/multichat/dialogs/read-all', {
      channel: payloadChannel
    }, {
      headers: { Authorization: `Bearer ${token}` }
    })
  } catch (e) {
    console.warn('[FloatingMultichat] markAllAsRead error:', e)
    fetchDialogs()
  } finally {
    markingAllAsRead.value = false
  }
}

const emit = defineEmits(['view-order'])

const guestSummary = ref(null)
const loadingGuestSummary = ref(false)

const fetchGuestSummary = async (dialog) => {
  if (!dialog) return
  loadingGuestSummary.value = true
  guestSummary.value = null
  try {
    const token = localStorage.getItem('access_token') || ''
    const res = await axios.get(`/api/v1/multichat/dialogs/${dialog.channel}/${dialog.peer_id}/guest-summary`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    guestSummary.value = res.data
    if (res.data?.phone && !dialog.phone) {
      dialog.phone = res.data.phone
    }
    if (res.data?.customer_name && (!dialog.peer_name || dialog.peer_name.startsWith('Чат') || dialog.peer_name.startsWith('Пользователь'))) {
      dialog.peer_name = res.data.customer_name
    }
  } catch (e) {
    console.warn('[FloatingMultichat] guest summary error:', e)
  } finally {
    loadingGuestSummary.value = false
  }
}

const viewLastOrder = (order) => {
  if (!order) return
  emit('view-order', order.id || order.order_number)
}

// Выбор диалога
const selectDialog = async (dialog) => {
  activeDialog.value = dialog
  removeToast(`${dialog.channel}_${dialog.peer_id}`)
  fetchGuestSummary(dialog)
  
  // Мгновенная выдача из реактивного кэша за 0 мс (без мигания и спиннера)
  const cached = chatStore.getCachedMessages(dialog.channel, dialog.peer_id)
  if (cached && cached.length > 0) {
    messages.value = [...cached]
    loadingMessages.value = false
    scrollToBottom()
  } else {
    loadingMessages.value = true
    messages.value = []
  }
  
  try {
    const token = localStorage.getItem('access_token') || ''
    const res = await axios.get(`/api/v1/multichat/dialogs/${dialog.channel}/${dialog.peer_id}/history`, {
      params: { limit: 35 },
      headers: { Authorization: `Bearer ${token}` }
    })
    if (Array.isArray(res.data)) {
      messages.value = res.data
      chatStore.setCachedMessages(dialog.channel, dialog.peer_id, res.data)
    }
    // Помечаем прочитанным
    if (!dialog.is_read || dialog.unread_count > 0) {
      dialog.is_read = true
      dialog.unread_count = 0
      axios.post(`/api/v1/multichat/dialogs/${dialog.channel}/${dialog.peer_id}/read`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      }).catch(() => {})
    }
  } catch (e) {
    console.warn('[FloatingMultichat] load history error:', e)
  } finally {
    loadingMessages.value = false
    scrollToBottom()
  }
}

// Скролл вниз
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainerRef.value) {
      messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight
    }
  })
}

// Отправка сообщения
const sendMessage = async () => {
  if (!replyText.value || !replyText.value.trim() || !activeDialog.value) return
  const textToSend = replyText.value.trim()
  const d = activeDialog.value
  
  sending.value = true
  try {
    const token = localStorage.getItem('access_token') || ''
    await axios.post(`/api/v1/multichat/dialogs/${d.channel}/${d.peer_id}/send`, {
      text: textToSend
    }, {
      headers: { Authorization: `Bearer ${token}` }
    })

    // Добавляем сообщение в локальный список
    const localMsg = {
      id: Date.now(),
      channel: d.channel,
      peer_id: d.peer_id,
      direction: 'outbound',
      text: textToSend,
      created_at: new Date().toISOString(),
      is_read: true
    }
    messages.value.push(localMsg)
    chatStore.appendMessageToCache(d.channel, d.peer_id, localMsg)
    
    // Обновляем последнее сообщение в диалоге
    d.text = textToSend
    d.created_at = localMsg.created_at
    d.direction = 'outbound'
    d.is_read = true
    d.unread_count = 0
    
    replyText.value = ''
    scrollToBottom()
  } catch (e) {
    console.error('[FloatingMultichat] sendMessage error:', e)
  } finally {
    sending.value = false
  }
}

// Перехват Enter
const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// =========================================================================
// ВСПЛЫВАЮЩИЕ УВЕДОМЛЕНИЯ (ТОСТЫ) В СТИЛЕ ВКОНТАКТЕ (ТАЙМЕР 80 СЕКУНД)
// =========================================================================
const chatToasts = ref([])
const TOAST_LIFETIME_MS = 80000 // 80 секунд

// Удаление плашки уведомления
const removeToast = (toastId) => {
  const idx = chatToasts.value.findIndex(t => t.id === toastId)
  if (idx !== -1) {
    if (chatToasts.value[idx].timeoutId) {
      clearTimeout(chatToasts.value[idx].timeoutId)
    }
    chatToasts.value.splice(idx, 1)
  }
}

// Показ плашки уведомления
const showToastNotification = (dialogData, msgText) => {
  if (!dialogData) return
  const toastId = `${dialogData.channel}_${dialogData.peer_id}`

  // Если для данного диалога уже открыта плашка — сбрасываем старый таймер и удаляем для обновления
  const existingIdx = chatToasts.value.findIndex(t => t.id === toastId)
  if (existingIdx !== -1) {
    if (chatToasts.value[existingIdx].timeoutId) {
      clearTimeout(chatToasts.value[existingIdx].timeoutId)
    }
    chatToasts.value.splice(existingIdx, 1)
  }

  // Запуск таймера скрытия через 80 секунд
  const timeoutId = setTimeout(() => {
    removeToast(toastId)
  }, TOAST_LIFETIME_MS)

  const newToast = {
    id: toastId,
    channel: dialogData.channel,
    peer_id: dialogData.peer_id,
    peer_name: dialogData.peer_name || `Чат ${dialogData.peer_id}`,
    peer_avatar: dialogData.peer_avatar || null,
    text: msgText || 'Новое входящее сообщение',
    time: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }),
    timeoutId,
    key: `${toastId}_${Date.now()}`
  }

  // Добавляем тост
  chatToasts.value.push(newToast)

  // Ограничиваем одновременное количество плашек максимум 5 штук
  if (chatToasts.value.length > 5) {
    const oldest = chatToasts.value.shift()
    if (oldest?.timeoutId) {
      clearTimeout(oldest.timeoutId)
    }
  }
}

// Клик по всплывающей плашке: открытие чата
const onToastClick = (toast) => {
  removeToast(toast.id)

  isOpen.value = true
  isMinimized.value = false

  const pIdStr = String(toast.peer_id)
  let d = dialogs.value.find(item => 
    item.channel === toast.channel && String(item.peer_id) === pIdStr
  )

  if (!d) {
    d = {
      channel: toast.channel || 'vk',
      peer_id: pIdStr,
      peer_name: toast.peer_name || `Клиент ${pIdStr}`,
      peer_avatar: toast.peer_avatar || null,
      text: toast.text || '',
      direction: 'inbound',
      is_read: true,
      unread_count: 0,
      created_at: new Date().toISOString()
    }
    dialogs.value.unshift(d)
  }

  selectDialog(d)
}

// Звуковые уведомления отключены по требованию
const playSound = () => {
  // Звук полностью отключен
}

// Обработка WebSocket события в реальном времени
const onWsMessage = (event) => {
  const msg = event.detail
  if (!msg || !msg.peer_id) return

  const pIdStr = String(msg.peer_id)
  const ch = msg.channel || 'vk'

  // Ищем существующий диалог
  let found = dialogs.value.find(d => 
    d.channel === ch && String(d.peer_id) === pIdStr
  )

  const isCurrentActive = activeDialog.value && 
    activeDialog.value.channel === ch && 
    String(activeDialog.value.peer_id) === pIdStr && 
    isOpen.value && !isMinimized.value

  if (found) {
    found.text = msg.text || found.text
    found.created_at = msg.created_at || new Date().toISOString()
    found.direction = msg.direction || 'inbound'
    if (msg.peer_name && !msg.peer_name.toLowerCase().startsWith('пользователь')) {
      found.peer_name = msg.peer_name
    }
    if (msg.peer_avatar) {
      found.peer_avatar = msg.peer_avatar
    }
    if (msg.direction === 'inbound') {
      if (isCurrentActive) {
        found.is_read = true
        found.unread_count = 0
      } else {
        found.is_read = false
        found.unread_count = (found.unread_count || 0) + 1
        showToastNotification(found, msg.text)
      }
    }
  } else {
    // Создаем новый диалог в списке
    const isUnread = msg.direction === 'inbound' && !isCurrentActive
    const newDiag = {
      channel: ch,
      peer_id: pIdStr,
      peer_name: msg.peer_name || `Чат ${pIdStr}`,
      peer_avatar: msg.peer_avatar || null,
      text: msg.text || '',
      direction: msg.direction || 'inbound',
      is_read: !isUnread,
      unread_count: isUnread ? 1 : 0,
      created_at: msg.created_at || new Date().toISOString()
    }
    dialogs.value.unshift(newDiag)
    if (isUnread) {
      showToastNotification(newDiag, msg.text)
    }
  }

  // Добавляем сообщение в централизованный реактивный кэш
  chatStore.appendMessageToCache(ch, pIdStr, msg)

  // Если открыт этот самый диалог — мгновенно добавляем сообщение в переписку
  if (activeDialog.value && 
      activeDialog.value.channel === ch && 
      String(activeDialog.value.peer_id) === pIdStr) {
    if (!messages.value.some(m => String(m.id) === String(msg.id))) {
      messages.value.push(msg)
      scrollToBottom()
    }
  }
}

// Внешний метод для открытия диалога прямо из строки заказа
const openChatWithCustomer = (channel, peerId, customerName = null, avatar = null) => {
  isOpen.value = true
  isMinimized.value = false

  const pIdStr = String(peerId)
  let d = dialogs.value.find(item => 
    item.channel === channel && String(item.peer_id) === pIdStr
  )

  if (!d) {
    d = {
      channel: channel || 'vk',
      peer_id: pIdStr,
      peer_name: customerName || `Клиент ${pIdStr}`,
      peer_avatar: avatar || null,
      text: '',
      direction: 'inbound',
      is_read: true,
      unread_count: 0,
      created_at: new Date().toISOString()
    }
    dialogs.value.unshift(d)
  }

  selectDialog(d)
}

// Переход на полную страницу Мультичата
const goToFullMultichat = () => {
  router.push('/admin/multichat')
}

// Жизненный цикл
onMounted(() => {
  fetchDialogs()
  window.addEventListener('multichat-message-event', onWsMessage)
})

onUnmounted(() => {
  window.removeEventListener('multichat-message-event', onWsMessage)
  // Очищаем таймеры тостов
  chatToasts.value.forEach(t => {
    if (t.timeoutId) clearTimeout(t.timeoutId)
  })
  chatToasts.value = []
})

// Экспортируем наружу
defineExpose({
  openChatWithCustomer,
  fetchDialogs,
  markAllAsRead,
  isOpen
})
</script>

<template>
  <div class="floating-multichat-root">
    <!-- Всплывающие уведомления (тосты) о новых сообщениях в стиле ВКонтакте (таймер 80 секунд) -->
    <div class="vk-toasts-container">
      <TransitionGroup name="vk-toast">
        <div
          v-for="toast in chatToasts"
          :key="toast.key"
          class="vk-toast-card"
          @click="onToastClick(toast)"
        >
          <!-- Аватарка с мини-бейжем соцсети -->
          <div class="position-relative flex-shrink-0">
            <VAvatar size="44" color="primary" variant="tonal" class="vk-toast-avatar">
              <VImg v-if="toast.peer_avatar" :src="toast.peer_avatar" referrerpolicy="no-referrer" />
              <VIcon v-else :icon="getChannelIcon(toast.channel)" size="22" />
            </VAvatar>
            <div
              class="vk-toast-channel-badge"
              :style="{ backgroundColor: getChannelColor(toast.channel) }"
              :title="getChannelLabel(toast.channel)"
            >
              <VIcon :icon="getChannelIcon(toast.channel)" size="11" color="white" />
            </div>
          </div>

          <!-- Текстовое содержимое плашки -->
          <div class="vk-toast-body flex-grow-1 overflow-hidden">
            <div class="d-flex align-center justify-space-between gap-1 mb-1">
              <span class="vk-toast-name text-truncate">
                {{ toast.peer_name }}
              </span>
              <div class="d-flex align-center gap-1.5 flex-shrink-0">
                <span class="vk-toast-time">{{ toast.time }}</span>
                <button
                  type="button"
                  class="vk-toast-close-btn"
                  title="Закрыть уведомление"
                  @click.stop="removeToast(toast.id)"
                >
                  <VIcon icon="bx-x" size="16" />
                </button>
              </div>
            </div>

            <div class="vk-toast-message">
              {{ toast.text || 'Новое входящее сообщение' }}
            </div>
          </div>

          <!-- Тонкая анимированная полоска обратного отсчета (80 секунд) -->
          <div
            class="vk-toast-progress-bar"
            :style="{ backgroundColor: getChannelColor(toast.channel) }"
          />
        </div>
      </TransitionGroup>
    </div>

    <!-- Кнопка-док в правом нижнем углу (когда окно закрыто или свернуто) -->
    <div v-if="!isOpen || isMinimized" class="floating-dock-wrapper">
      <VBtn
        color="primary"
        size="large"
        elevation="8"
        class="floating-dock-button text-none font-weight-bold"
        rounded="pill"
        @click="isOpen = true; isMinimized = false"
      >
        <VBadge
          v-if="unreadCount > 0"
          :content="unreadCount"
          color="error"
          offset-x="-4"
          offset-y="-4"
        >
          <VIcon icon="bx-chat" size="24" start />
        </VBadge>
        <VIcon v-else icon="bx-chat" size="24" start />
        <span class="ms-1">Мультичат</span>
        <VChip
          v-if="unreadCount > 0"
          size="x-small"
          color="error"
          variant="flat"
          class="ms-2 font-weight-black shadow-sm"
        >
          {{ unreadCount }} нов.
        </VChip>
      </VBtn>
    </div>

    <!-- Развернутое плавающее окно чатов (100% НЕПРОЗРАЧНОЕ) -->
    <div
      v-if="isOpen && !isMinimized"
      class="floating-window-card"
      :class="{ 'is-expanded': isExpanded }"
    >
      <!-- Шапка окна (Сплошной контрастный фон) -->
      <div class="floating-window-header d-flex align-center justify-space-between px-4 py-2.5">
        <div class="d-flex align-center gap-2">
          <div class="chat-header-icon-box">
            <VIcon icon="bx-conversation" color="primary" size="20" />
          </div>
          <span class="font-weight-bold text-subtitle-1 text-slate-800">Мультичат (Real-Time)</span>
          <VChip
            v-if="unreadCount > 0"
            size="small"
            color="error"
            variant="flat"
            class="font-weight-bold ms-1"
          >
            {{ unreadCount }} непрочитанных
          </VChip>
        </div>

        <div class="d-flex align-center gap-1">
          <VBtn
            icon="bx-refresh"
            size="small"
            variant="text"
            color="secondary"
            title="Обновить список диалогов"
            :loading="loadingDialogs"
            @click="fetchDialogs"
          />
          <VBtn
            icon="bx-link-external"
            size="small"
            variant="text"
            color="secondary"
            title="Открыть на отдельной странице"
            @click="goToFullMultichat"
          />
          <VBtn
            :icon="isExpanded ? 'bx-collapse-alt' : 'bx-expand-alt'"
            size="small"
            variant="text"
            color="secondary"
            :title="isExpanded ? 'Обычный размер' : 'Развернуть на весь экран'"
            @click="isExpanded = !isExpanded"
          />
          <VBtn
            icon="bx-minus"
            size="small"
            variant="text"
            color="secondary"
            title="Свернуть в кнопку"
            @click="isMinimized = true"
          />
          <VBtn
            icon="bx-x"
            size="small"
            variant="text"
            color="secondary"
            title="Закрыть"
            @click="isOpen = false"
          />
        </div>
      </div>

      <!-- Основное тело окна: Левая колонка диалогов + Правая колонка чата -->
      <div class="floating-window-body d-flex flex-grow-1 overflow-hidden">
        <!-- Левая панель (Список диалогов, 100% непрозрачный) -->
        <div class="floating-dialogs-sidebar d-flex flex-column">
          <!-- Поиск и кнопка "Прочитать все" -->
          <div class="sidebar-top-bar px-3 pt-3 pb-2">
            <div class="d-flex align-center gap-2 mb-2">
              <VTextField
                v-model="searchQuery"
                placeholder="Поиск по диалогам..."
                density="compact"
                variant="outlined"
                hide-details
                prepend-inner-icon="bx-search"
                class="search-input flex-grow-1"
              />

              <VBtn
                size="small"
                variant="tonal"
                color="primary"
                class="text-none font-weight-bold px-2 mark-read-btn"
                :loading="markingAllAsRead"
                title="Отметить все диалоги как прочитанные"
                @click="markAllAsRead"
              >
                <VIcon icon="bx-check-double" size="18" class="me-1" />
                <span class="d-none d-sm-inline text-caption">Прочитать все</span>
              </VBtn>
            </div>

            <!-- Табы фильтров: Все / Новые / MAX / VK / TG -->
            <div class="d-flex align-center gap-1 overflow-x-auto pb-1 filters-row">
              <VBtn
                v-for="opt in channelOptions"
                :key="opt.value"
                size="x-small"
                :variant="selectedChannel === opt.value ? 'flat' : 'tonal'"
                :color="selectedChannel === opt.value ? (opt.value === 'unread' ? 'error' : 'primary') : 'default'"
                class="text-none font-weight-bold px-2 filter-tab-btn"
                @click="selectedChannel = opt.value"
              >
                {{ opt.label }}
              </VBtn>
            </div>
          </div>

          <!-- Список диалогов (НОВЫЕ ВВЕРХУ) -->
          <div class="flex-grow-1 overflow-y-auto dialogs-scroll-area">
            <div v-if="loadingDialogs && dialogs.length === 0" class="d-flex justify-center align-center pa-8">
              <VProgressCircular indeterminate size="28" color="primary" />
            </div>

            <div v-else-if="filteredDialogs.length === 0" class="pa-8 text-center text-slate-500 text-caption font-weight-medium">
              <VIcon icon="bx-chat" size="32" class="mb-2 text-slate-400 opacity-60" /><br />
              {{ searchQuery ? 'Ничего не найдено' : (selectedChannel === 'unread' ? 'Нет новых непрочитанных сообщений' : 'Диалоги отсутствуют') }}
            </div>

            <div v-else class="dialogs-list">
              <div
                v-for="d in filteredDialogs"
                :key="`${d.channel}_${d.peer_id}`"
                class="dialog-item px-3 py-2.5 cursor-pointer d-flex align-center gap-3"
                :class="{
                  'active-dialog': activeDialog && activeDialog.channel === d.channel && String(activeDialog.peer_id) === String(d.peer_id),
                  'unread-dialog': isDialogUnread(d),
                  'read-dialog': !isDialogUnread(d)
                }"
                @click="selectDialog(d)"
              >
                <!-- Аватарка с ярким бейджем канала -->
                <div class="position-relative flex-shrink-0">
                  <VAvatar size="42" color="primary" variant="tonal" class="dialog-avatar">
                    <VImg v-if="d.peer_avatar" :src="d.peer_avatar" referrerpolicy="no-referrer" />
                    <VIcon v-else :icon="getChannelIcon(d.channel)" size="22" />
                  </VAvatar>
                  <!-- Иконка канала в углу аватара -->
                  <div
                    class="channel-corner-badge"
                    :style="{ backgroundColor: getChannelColor(d.channel) }"
                    :title="getChannelLabel(d.channel)"
                  >
                    <VIcon :icon="getChannelIcon(d.channel)" size="11" color="white" />
                  </div>
                </div>

                <!-- Информация о клиенте и текст сообщения -->
                <div class="flex-grow-1 overflow-hidden" style="min-width: 0;">
                  <div class="d-flex align-center justify-space-between mb-0.5">
                    <span class="dialog-peer-name text-truncate">
                      {{ d.peer_name || `Чат ${d.peer_id}` }}
                    </span>
                    <span class="dialog-time ms-1 flex-shrink-0">
                      {{ formatTime(getDialogTime(d)) }}
                    </span>
                  </div>

                  <div class="d-flex align-center justify-space-between">
                    <span class="dialog-preview-text text-truncate">
                      <span v-if="isDialogOutbound(d)" class="outbound-prefix font-weight-bold">Вы: </span>
                      {{ getDialogText(d) || 'Вложение или медиафайл' }}
                    </span>

                    <!-- Яркий индикатор нового непрочитанного сообщения -->
                    <div v-if="isDialogUnread(d)" class="ms-1 flex-shrink-0">
                      <span class="unread-count-pill">
                        {{ getDialogUnreadCount(d) > 1 ? getDialogUnreadCount(d) : 'НОВОЕ' }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Правая панель (Активный чат, 100% непрозрачный) -->
        <div class="floating-chat-content d-flex flex-column flex-grow-1">
          <!-- Заглушка, если диалог не выбран -->
          <div v-if="!activeDialog" class="d-flex flex-column align-center justify-center flex-grow-1 pa-8 text-center empty-chat-state">
            <div class="empty-chat-icon-box mb-3">
              <VIcon icon="bx-conversation" size="48" color="primary" />
            </div>
            <div class="text-subtitle-1 font-weight-bold text-slate-700 mb-1">Выберите диалог</div>
            <div class="text-body-2 text-slate-500" style="max-width: 320px;">
              Выберите диалог из списка слева или нажмите на иконку 💬 в строке любого заказа
            </div>
          </div>

          <!-- Активный диалог с историей и полем ввода ответа -->
          <template v-else>
            <!-- Шапка активного диалога -->
            <div class="active-dialog-header d-flex align-center justify-space-between px-4 py-2.5">
              <div class="d-flex align-center gap-3">
                <div class="position-relative flex-shrink-0">
                  <VAvatar size="42" color="primary" variant="tonal">
                    <VImg v-if="activeDialog.peer_avatar" :src="activeDialog.peer_avatar" referrerpolicy="no-referrer" />
                    <VIcon v-else :icon="getChannelIcon(activeDialog.channel)" size="22" />
                  </VAvatar>
                  <div
                    class="channel-corner-badge"
                    :style="{ backgroundColor: getChannelColor(activeDialog.channel) }"
                  >
                    <VIcon :icon="getChannelIcon(activeDialog.channel)" size="11" color="white" />
                  </div>
                </div>

                <div>
                  <div class="d-flex align-center gap-2">
                    <span class="font-weight-bold text-subtitle-1 text-slate-900 leading-tight">
                      {{ guestSummary?.customer_name || activeDialog.peer_name || `Чат ${activeDialog.peer_id}` }}
                    </span>
                    <VChip
                      size="x-small"
                      variant="flat"
                      :style="{ backgroundColor: getChannelColor(activeDialog.channel) }"
                      class="text-white font-weight-bold px-2 py-0.5 rounded-pill"
                    >
                      {{ getChannelLabel(activeDialog.channel) }}
                    </VChip>
                  </div>

                  <!-- Номер телефона гостя (если привязан к анкете) -->
                  <div class="d-flex align-center gap-2 mt-0.5 flex-wrap">
                    <div v-if="guestSummary?.phone || activeDialog.phone" class="d-flex align-center gap-1">
                      <VIcon icon="bx-phone-call" size="15" color="success" />
                      <a
                        :href="`tel:${guestSummary?.raw_phone || activeDialog.phone}`"
                        class="text-caption font-weight-bold text-success text-decoration-none"
                        title="Позвонить клиенту"
                      >
                        {{ guestSummary?.phone || activeDialog.phone }}
                      </a>
                      <VChip
                        v-if="guestSummary?.bonus_points > 0"
                        size="x-small"
                        color="warning"
                        variant="tonal"
                        class="ms-1 px-1 font-weight-bold"
                        style="height: 18px; font-size: 10px;"
                      >
                        ⭐ {{ guestSummary.bonus_points }} б.
                      </VChip>
                    </div>
                    <div v-else class="text-caption text-slate-400">
                      Телефон не привязан к анкете
                    </div>
                    <span class="text-slate-300">•</span>
                    <span class="text-caption text-slate-400">ID: {{ activeDialog.peer_id }}</span>
                  </div>
                </div>
              </div>

              <!-- Правая часть: кнопка последнего заказа и закрытие -->
              <div class="d-flex align-center gap-2">
                <!-- Кнопка перехода к последнему заказу гостя -->
                <div v-if="guestSummary?.last_order" class="d-flex align-center">
                  <VBtn
                    size="small"
                    variant="flat"
                    color="primary"
                    class="text-none font-weight-bold px-3 text-caption rounded-lg shadow-sm"
                    title="Открыть состав и детали последнего заказа гостя"
                    @click="viewLastOrder(guestSummary.last_order)"
                  >
                    <VIcon icon="bx-receipt" size="16" start />
                    <span>Заказ #{{ guestSummary.last_order.order_number }}</span>
                    <VChip size="x-small" color="white" variant="flat" class="text-primary font-weight-black ms-1.5 px-1.5">
                      {{ guestSummary.last_order.total_amount }} ₽
                    </VChip>
                  </VBtn>
                </div>
                <div v-else-if="loadingGuestSummary" class="d-flex align-center px-2">
                  <VProgressCircular indeterminate size="18" width="2" color="primary" />
                </div>
                <div v-else class="text-caption text-slate-400 me-1">
                  Заказов нет
                </div>

                <VBtn
                  icon="bx-x"
                  size="small"
                  variant="text"
                  color="secondary"
                  title="Закрыть переписку"
                  @click="activeDialog = null"
                />
              </div>
            </div>

            <!-- Список сообщений (Сплошной контрастный фон) -->
            <div ref="messagesContainerRef" class="floating-messages-area flex-grow-1 pa-4 overflow-y-auto">
              <div v-if="loadingMessages" class="d-flex justify-center align-center py-10">
                <VProgressCircular indeterminate size="28" color="primary" />
              </div>

              <div v-else-if="messages.length === 0" class="text-center text-slate-400 text-body-2 py-12">
                История сообщений пока пуста.<br />Напишите клиенту прямо сейчас!
              </div>

              <div v-else class="messages-stream d-flex flex-column gap-3">
                <div
                  v-for="m in messages"
                  :key="m.id"
                  class="message-bubble-row d-flex"
                  :class="m.direction === 'outbound' ? 'justify-end' : 'justify-start'"
                >
                  <div
                    class="message-bubble px-3.5 py-2.5 rounded-xl"
                    :class="m.direction === 'outbound' ? 'message-outbound' : 'message-inbound'"
                  >
                    <div class="message-text">
                      {{ m.text }}
                    </div>

                    <!-- Вложения / фото (если есть) -->
                    <div v-if="m.attachments && m.attachments.length > 0" class="mt-2 d-flex flex-wrap gap-1">
                      <img
                        v-for="(att, attIdx) in m.attachments"
                        :key="attIdx"
                        :src="att.url || att.preview_url"
                        referrerpolicy="no-referrer"
                        class="rounded border"
                        style="max-width: 140px; max-height: 100px; object-fit: cover;"
                      />
                    </div>

                    <div class="message-meta d-flex align-center justify-end gap-1 mt-1">
                      <span class="message-time">{{ formatTime(m.created_at) }}</span>
                      <VIcon
                        v-if="m.direction === 'outbound'"
                        :icon="m.is_read ? 'bx-check-double' : 'bx-check'"
                        size="14"
                        :class="m.is_read ? 'text-emerald-300' : 'opacity-75'"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Поле ввода ответа клиенту (100% непрозрачный белый фон) -->
            <div class="floating-input-panel px-3 py-2.5 d-flex align-end gap-2">
              <VTextarea
                v-model="replyText"
                placeholder="Написать ответ клиенту... (Enter для отправки)"
                rows="1"
                max-rows="4"
                auto-grow
                density="compact"
                variant="outlined"
                hide-details
                class="reply-textarea flex-grow-1"
                @keydown="handleKeydown"
              />
              <VBtn
                color="primary"
                icon="bx-send"
                size="large"
                elevation="2"
                class="send-message-btn rounded-lg"
                :disabled="!replyText.trim() || sending"
                :loading="sending"
                title="Отправить сообщение (Enter)"
                @click="sendMessage"
              />
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.floating-multichat-root {
  position: relative;
  z-index: 10001;
}

.floating-dock-wrapper {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 10001;
}

.floating-dock-button {
  background: #6366f1 !important;
  color: #ffffff !important;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.45) !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  height: 48px !important;
  padding: 0 22px !important;
}

.floating-dock-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(99, 102, 241, 0.55) !important;
}

/* Плавающее окно (СТРОГО 100% НЕПРОЗРАЧНОЕ) */
.floating-window-card {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 820px;
  height: 600px;
  max-width: calc(100vw - 32px);
  max-height: calc(100vh - 48px);
  background-color: #ffffff !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 16px;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.35), 0 4px 12px rgba(0, 0, 0, 0.1) !important;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 10002;
  opacity: 1 !important;
  animation: floatWindowFadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.floating-window-card.is-expanded {
  width: calc(100vw - 48px);
  height: calc(100vh - 48px);
  bottom: 24px;
  right: 24px;
  border-radius: 12px;
}

@keyframes floatWindowFadeIn {
  from {
    opacity: 0;
    transform: translateY(16px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Шапка окна */
.floating-window-header {
  background-color: #f8fafc !important;
  border-bottom: 1px solid #e2e8f0 !important;
  user-select: none;
  opacity: 1 !important;
}

.chat-header-icon-box {
  width: 32px;
  height: 32px;
  background: #e0e7ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.text-slate-800 {
  color: #1e293b !important;
}

.text-slate-900 {
  color: #0f172a !important;
}

.text-slate-700 {
  color: #334155 !important;
}

.text-slate-500 {
  color: #64748b !important;
}

.text-slate-400 {
  color: #94a3b8 !important;
}

/* Левая панель диалогов */
.floating-dialogs-sidebar {
  width: 320px;
  min-width: 320px;
  max-width: 320px;
  background-color: #f8fafc !important;
  border-right: 1px solid #e2e8f0 !important;
  opacity: 1 !important;
}

.sidebar-top-bar {
  background-color: #ffffff !important;
  border-bottom: 1px solid #e2e8f0;
}

.search-input :deep(.v-field) {
  border-radius: 8px !important;
  background-color: #f8fafc !important;
  font-size: 13px !important;
}

.mark-read-btn {
  height: 38px !important;
  min-width: 38px !important;
  border-radius: 8px !important;
}

.filter-tab-btn {
  font-size: 11px !important;
  height: 24px !important;
  border-radius: 6px !important;
}

.dialogs-scroll-area {
  background-color: #f8fafc !important;
}

/* Элемент диалога в списке */
.dialog-item {
  border-bottom: 1px solid #eef2f6 !important;
  transition: all 0.15s ease;
  position: relative;
}

/* Прочитанный диалог (чистый белый фон, спокойные тона текста) */
.dialog-item.read-dialog {
  background-color: #ffffff !important;
  border-left: 4px solid transparent !important;
}

.dialog-item.read-dialog:hover {
  background-color: #f8fafc !important;
}

.dialog-item.read-dialog .dialog-peer-name {
  color: #334155 !important;
  font-weight: 600 !important;
}

.dialog-item.read-dialog .dialog-preview-text {
  color: #64748b !important;
  font-weight: 400 !important;
}

.dialog-item.read-dialog .dialog-time {
  color: #94a3b8 !important;
  font-weight: 500 !important;
}

/* Непрочитанный диалог (контрастный нежно-синий фон, синяя акцентная полоса, жирный шрифт) */
.dialog-item.unread-dialog {
  background-color: #eff6ff !important;
  border-left: 4px solid #2563eb !important;
}

.dialog-item.unread-dialog:hover {
  background-color: #dbeafe !important;
}

.dialog-item.unread-dialog .dialog-peer-name {
  color: #1e40af !important;
  font-weight: 800 !important;
}

.dialog-item.unread-dialog .dialog-preview-text {
  color: #0f172a !important;
  font-weight: 700 !important;
}

.dialog-item.unread-dialog .dialog-time {
  color: #2563eb !important;
  font-weight: 700 !important;
}

/* Активный выбранный диалог */
.dialog-item.active-dialog {
  background-color: #e0e7ff !important;
  border-left: 4px solid #4f46e5 !important;
}

.dialog-item.unread-dialog.active-dialog {
  background-color: #dbeafe !important;
  border-left: 4px solid #2563eb !important;
}

.outbound-prefix {
  color: #2563eb !important;
}

.dialog-avatar {
  border: 1px solid #e2e8f0;
}

.channel-corner-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 17px;
  height: 17px;
  border-radius: 50%;
  border: 2px solid #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.dialog-peer-name {
  font-size: 13px;
}

.dialog-time {
  font-size: 11px;
}

.dialog-preview-text {
  font-size: 12px;
  line-height: 1.35;
}

.unread-count-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  background-color: #ef4444;
  color: #ffffff;
  font-size: 10px;
  font-weight: 800;
  border-radius: 10px;
  letter-spacing: 0.3px;
  box-shadow: 0 1px 3px rgba(239, 68, 68, 0.4);
}

/* Правая панель (Чат) */
.floating-chat-content {
  background-color: #ffffff !important;
  opacity: 1 !important;
}

.empty-chat-state {
  background-color: #ffffff !important;
}

.empty-chat-icon-box {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background-color: #e0e7ff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.active-dialog-header {
  background-color: #ffffff !important;
  border-bottom: 1px solid #e2e8f0 !important;
  opacity: 1 !important;
}

/* Область сообщений (Светлый приятный фон) */
.floating-messages-area {
  background-color: #f1f5f9 !important;
  opacity: 1 !important;
}

.message-bubble {
  max-width: 78%;
  font-size: 13px;
  line-height: 1.4;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.message-inbound {
  background-color: #ffffff !important;
  color: #0f172a !important;
  border: 1px solid #cbd5e1 !important;
  border-bottom-left-radius: 3px !important;
}

.message-outbound {
  background-color: #4f46e5 !important;
  color: #ffffff !important;
  border-bottom-right-radius: 3px !important;
  box-shadow: 0 2px 6px rgba(79, 70, 229, 0.35) !important;
}

.message-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.message-meta {
  font-size: 10px;
}

.message-inbound .message-time {
  color: #64748b;
}

.message-outbound .message-time {
  color: rgba(255, 255, 255, 0.85);
}

.text-emerald-300 {
  color: #6ee7b7 !important;
}

/* Панель ввода ответа */
.floating-input-panel {
  background-color: #ffffff !important;
  border-top: 1px solid #e2e8f0 !important;
  opacity: 1 !important;
}

.reply-textarea :deep(.v-field) {
  border-radius: 10px !important;
  background-color: #f8fafc !important;
  font-size: 13px !important;
}

.send-message-btn {
  height: 40px !important;
  min-width: 40px !important;
  width: 40px !important;
  background-color: #4f46e5 !important;
}

/* =========================================================================
   ВСПЛЫВАЮЩИЕ ПЛАШКИ-УВЕДОМЛЕНИЯ В СТИЛЕ ВКОНТАКТЕ (ТАЙМЕР 80 СЕКУНД)
   ========================================================================= */
.vk-toasts-container {
  position: fixed;
  bottom: 84px;
  right: 24px;
  z-index: 10006;
  display: flex;
  flex-direction: column-reverse;
  gap: 10px;
  pointer-events: none;
  max-width: 360px;
  width: calc(100vw - 32px);
}

.vk-toast-card {
  pointer-events: auto;
  background-color: #ffffff !important;
  border-radius: 12px;
  border: 1px solid #cbd5e1;
  box-shadow: 0 10px 25px -4px rgba(15, 23, 42, 0.2), 0 4px 6px -2px rgba(15, 23, 42, 0.08);
  padding: 12px 14px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  user-select: none;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease, border-color 0.2s ease;
}

.vk-toast-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px -4px rgba(15, 23, 42, 0.25), 0 6px 10px -2px rgba(15, 23, 42, 0.1);
  border-color: #94a3b8;
}

.vk-toast-avatar {
  border: 1px solid #e2e8f0;
}

.vk-toast-channel-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 17px;
  height: 17px;
  border-radius: 50%;
  border: 2px solid #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.vk-toast-name {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}

.vk-toast-time {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
}

.vk-toast-close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
  padding: 0;
}

.vk-toast-close-btn:hover {
  background-color: #f1f5f9;
  color: #0f172a;
}

.vk-toast-message {
  font-size: 12.5px;
  color: #334155;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.vk-toast-progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2.5px;
  animation: vkToastProgress 80s linear forwards;
  opacity: 0.85;
}

@keyframes vkToastProgress {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}

.vk-toast-enter-active,
.vk-toast-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.vk-toast-enter-from {
  opacity: 0;
  transform: translateY(16px) scale(0.96);
}

.vk-toast-leave-to {
  opacity: 0;
  transform: translateX(36px) scale(0.94);
}
</style>
