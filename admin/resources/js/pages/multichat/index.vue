<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useTheme, useDisplay } from 'vuetify'
import axios from 'axios'
import { useToast } from 'vue-toastification'
import { useChatStore } from '@/stores/chatStore'
import { hasPermission, getAuthHeaders } from '@/utils/auth'
import { formatTime as utilFormatTime, formatDate as utilFormatDate, appTimezone, appOffset } from '@/utils/date'

const chatStore = useChatStore()

// Вспомогательные функции каналов (объявлены в самом верху для предотвращения TDZ ReferenceError)
function isVkChannel(channel) {
  return channel === 'vk' || channel === 'vk_user'
}

function isMaxChannel(channel) {
  return channel === 'max' || channel === 'max_user' || channel === 'max_bot' || channel === 'max_account' || channel === 'max_bridge'
}

function isBotChannel(channel) {
  return channel === 'max_bot' || channel === 'max_account' || channel === 'vk' || channel === 'telegram_bot' || channel === 'telegram'
}

// Гарантированные заголовки авторизации для любых API вызовов
const getRequestHeaders = () => {
  const h = getAuthHeaders()
  const token = localStorage.getItem('access_token') || ''
  const deviceId = localStorage.getItem('device_id') || ''
  return {
    Authorization: h.Authorization || (token ? `Bearer ${token}` : ''),
    'X-Device-Id': h['X-Device-Id'] || deviceId,
    'Content-Type': 'application/json'
  }
}

const toast = useToast()
const vuetifyTheme = useTheme()
const { smAndDown } = useDisplay()
const isMobile = computed(() => smAndDown.value)
const isDark = computed(() => vuetifyTheme.global.current.value.dark)


// Состояния диалогов
const dialogs = ref([])
const activeDialog = ref(null)
const messages = ref([])
const searchQuery = ref('')
const selectedChannel = ref('all') // all, vk, whatsapp, max_account, max_bot, telegram_bot
const loadingDialogs = ref(false)
const loadingHistory = ref(false)
const sendingMessage = ref(false)
const replyText = ref('')
const messageContainer = ref(null)

// Фильтры
const unreadOnly = ref(false)
const showHiddenOnly = ref(false)
const selectedTagId = ref(null)
const startDate = ref('')
const endDate = ref('')
const showFilters = ref(false)

// Скрытые диалоги: множество ключей `channel_peer_id` для мгновенной фильтрации и отключения всех уведомлений
const hiddenDialogsKeys = ref(new Set())

const fetchHiddenKeys = async () => {
  try {
    const cached = localStorage.getItem('multichat_hidden_keys')
    if (cached) {
      try {
        const arr = JSON.parse(cached)
        if (Array.isArray(arr)) {
          hiddenDialogsKeys.value = new Set(arr)
        }
      } catch (e) {}
    }

    const res = await axios.get('/api/v1/multichat/hidden-keys', {
      headers: getRequestHeaders()
    })
    if (Array.isArray(res.data)) {
      const keys = new Set()
      res.data.forEach(k => {
        const s = String(k)
        keys.add(s)
        keys.add(s.replace(':', '_'))
      })
      hiddenDialogsKeys.value = keys
      localStorage.setItem('multichat_hidden_keys', JSON.stringify(Array.from(keys)))
    }
  } catch (e) {
    console.warn('[Multichat] Failed to fetch hidden keys:', e)
  }
}

const isDialogHidden = (channel, peerId, dialogObj = null) => {
  if (dialogObj && dialogObj.is_hidden !== undefined) {
    return dialogObj.is_hidden === true
  }
  if (!channel || !peerId) return false
  const pIdStr = String(peerId)

  const keyUnderscore = `${channel}_${pIdStr}`
  const keyColon = `${channel}:${pIdStr}`
  if (hiddenDialogsKeys.value.has(keyUnderscore) || hiddenDialogsKeys.value.has(keyColon)) {
    return true
  }

  // Альтернативные каналы
  let alts = []
  if (isVkChannel(channel)) {
    alts = ['vk', 'vk_user']
  } else if (isMaxChannel(channel)) {
    alts = ['max', 'max_user', 'max_bot', 'max_account', 'max_bridge']
  } else if (channel === 'whatsapp' || channel === 'whatsapp_user') {
    alts = ['whatsapp', 'whatsapp_user']
  }
  for (const alt of alts) {
    if (hiddenDialogsKeys.value.has(`${alt}_${pIdStr}`) || hiddenDialogsKeys.value.has(`${alt}:${pIdStr}`)) {
      return true
    }
  }

  return false
}


// Подсчет непрочитанных: скрытые диалоги полностью исключаются при открытом общем списке
const totalUnreadCount = computed(() => {
  return dialogs.value.filter(d => {
    if ((d.unread_count || 0) <= 0) return false
    if (!showHiddenOnly.value && (d.is_hidden === true || isDialogHidden(d.channel, d.peer_id, d))) {
      return false
    }
    return true
  }).length
})

const totalUnreadMessages = computed(() => {
  return dialogs.value.reduce((acc, d) => {
    if (!showHiddenOnly.value && (d.is_hidden === true || isDialogHidden(d.channel, d.peer_id, d))) {
      return acc
    }
    return acc + (d.unread_count || 0)
  }, 0)
})

const setFilterMode = (mode) => {
  if (mode === 'all') {
    unreadOnly.value = false
    showHiddenOnly.value = false
  } else if (mode === 'unread') {
    unreadOnly.value = true
    showHiddenOnly.value = false
  } else if (mode === 'hidden') {
    unreadOnly.value = false
    showHiddenOnly.value = true
  }

  // Если активный диалог не соответствует новому режиму (скрытый / видимый), закрываем его
  if (activeDialog.value) {
    const isActHidden = activeDialog.value.is_hidden || isDialogHidden(activeDialog.value.channel, activeDialog.value.peer_id, activeDialog.value)
    if (showHiddenOnly.value && !isActHidden) {
      activeDialog.value = null
      messages.value = []
    } else if (!showHiddenOnly.value && isActHidden) {
      activeDialog.value = null
      messages.value = []
    }
  }
}

// Поиск внутри текущего открытого чата (по тексту и дате/времени)
const showInChatSearch = ref(false)
const inChatSearchQuery = ref('')
const inChatSearchDate = ref('')
const currentSearchMatchIndex = ref(0)
const highlightedMessageId = ref(null)

// Глобальный поиск по сообщениям и пользователям архива
const showGlobalSearchModal = ref(false)
const globalSearchQuery = ref('')
const globalSearchChannel = ref('all')
const globalSearchResults = ref([])
const globalSearchTotal = ref(0)
const searchingGlobal = ref(false)

// Метки (Теги)
const allTags = ref([])
const showTagManager = ref(false)
const newTagName = ref('')
const newTagColor = ref('#757575')
const savingTag = ref(false)

// Быстрое создание метки прямо в меню чата
const quickTagName = ref('')
const quickTagColor = ref('#2196F3')
const creatingQuickTag = ref(false)
const activeTagMenuDialog = ref(null)
const tagMenuTarget = ref(null)
const showSingleTagMenu = ref(false)

const openTagMenu = (dialog, event) => {
  activeTagMenuDialog.value = dialog
  tagMenuTarget.value = event.currentTarget
  showSingleTagMenu.value = true
}

// Управление личными аккаунтами (QR / Токены)
const showAccountsModal = ref(false)
const accounts = ref([])
const loadingAccounts = ref(false)

// Telegram QR
const qrData = ref(null)
const loadingTelegramQr = ref(false)
const qrPollingInterval = ref(null)

// WhatsApp QR
const waQrData = ref(null)
const loadingWhatsAppQr = ref(false)
const waPollingInterval = ref(null)
const waAccountName = ref('')
const waAccountPhone = ref('')
const waGreenApiToken = ref('')
const confirmingWa = ref(false)

const newAccountType = ref('whatsapp_qr') // whatsapp_qr, telegram_qr, vk_user, max_user
const newAccountName = ref('')
const newAccountToken = ref('')
const newAccountPhone = ref('')
const savingAccount = ref(false)

// Библиотека звуковых уведомлений
const showSoundModal = ref(false)
const globalSound = ref(localStorage.getItem('multichat_global_sound') || 'icq')
const soundVolume = ref(parseFloat(localStorage.getItem('multichat_sound_volume') || '0.8'))

const soundLibrary = [
  { id: 'icq', name: 'ICQ «О-оу!» (Uh-oh)', icon: 'bx-bot', desc: 'Легендарный звук входящего сообщения ICQ' },
  { id: 'horn', name: 'Клаксон авто (Би-Бип!)', icon: 'bx-car', desc: 'Двойной автомобильный клаксон' },
  { id: 'car_alarm', name: 'Автомобильный сигнал / Гудок', icon: 'bx-alarm-exclamation', desc: 'Громкий выразительный сигнал автомобиля' },
  { id: 'chime', name: 'Нежный перезвон (Chime)', icon: 'bx-bell', desc: 'Приятный мягкий перелив' },
  { id: 'bell', name: 'Звонкий колокольчик', icon: 'bx-bell-plus', desc: 'Четкий звук колокольчика' },
  { id: 'push', name: 'Telegram / Push тон', icon: 'bxl-telegram', desc: 'Стандартный современный мессенджер-пуш' },
  { id: 'sonar', name: 'Сонар (VK Style)', icon: 'bxl-vk', desc: 'Короткий мелодичный импульс' },
  { id: 'water', name: 'Капля воды (Pop)', icon: 'bx-droplet', desc: 'Легкий и ненавязчивый звук клика' },
  { id: 'mute', name: 'Без звука (Mute)', icon: 'bx-volume-mute', desc: 'Уведомления отключены' }
]


// Всплывающие уведомления (Desktop Push / In-App Popups)
// По умолчанию отключено: false
const globalPopupsEnabled = ref(localStorage.getItem('multichat_global_popups') === 'true')
const showNotificationPopup = ref(false)
const currentPopupMessage = ref(null)

const toggleGlobalPopups = async () => {
  if (!globalPopupsEnabled.value) {
    globalPopupsEnabled.value = true
    localStorage.setItem('multichat_global_popups', 'true')
    if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'default') {
      const res = await Notification.requestPermission()
      if (res === 'granted') {
        toast.success('Всплывающие Desktop-уведомления включены!')
      } else {
        toast.info('Всплывающие окна включены внутри панели')
      }
    } else {
      toast.success('Всплывающие уведомления включены')
    }
  } else {
    globalPopupsEnabled.value = false
    localStorage.setItem('multichat_global_popups', 'false')
    toast.info('Всплывающие уведомления отключены')
  }
}

// Получить режим всплывающих уведомлений для активного диалога
const activeDialogPopup = computed(() => {
  if (!activeDialog.value) return 'default'
  const key = `multichat_popup_${activeDialog.value.channel}_${activeDialog.value.peer_id}`
  return localStorage.getItem(key) || 'default'
})

const setDialogPopup = (dialog, mode) => {
  if (!dialog) return
  const key = `multichat_popup_${dialog.channel}_${dialog.peer_id}`
  if (mode === 'default') {
    localStorage.removeItem(key)
    toast.success('Установлен режим всплывающих окон по умолчанию')
  } else {
    localStorage.setItem(key, mode)
    if (mode === 'always') {
      if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission()
      }
      toast.success('Всплывающие уведомления для этого чата включены')
    } else {
      toast.info('Всплывающие уведомления для этого чата отключены')
    }
  }
}

const isPopupEnabledForDialog = (channel, peer_id) => {
  const chatSetting = localStorage.getItem(`multichat_popup_${channel}_${peer_id}`)
  if (chatSetting === 'always') return true
  if (chatSetting === 'never') return false
  return globalPopupsEnabled.value === true
}

const triggerPopupNotification = (msg) => {
  if (!msg) return
  // СТРОГО: Для скрытых диалогов ВСЕ всплывающие уведомления (Desktop, Push, In-App Popup) отключены!
  if (msg.is_hidden === true || isDialogHidden(msg.channel, msg.peer_id, msg)) return
  if (!isPopupEnabledForDialog(msg.channel, msg.peer_id)) return

  // 1. Системное браузерное уведомление на рабочем столе (работает даже если открыта другая вкладка)
  if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted') {
    try {
      const title = `💬 ${msg.peer_name || ('Собеседник ' + msg.peer_id)}`
      const options = {
        body: msg.text || 'Новое сообщение',
        icon: msg.peer_avatar || '/favicon.ico',
        tag: `multichat-${msg.channel}-${msg.peer_id}`,
        renotify: true
      }
      const notif = new Notification(title, options)
      notif.onclick = () => {
        window.focus()
        openDialogFromNotification(msg)
        notif.close()
      }
    } catch (e) {
      console.warn('Desktop Notification error:', e)
    }
  }

  // 2. Всплывающее окно внутри интерфейса
  currentPopupMessage.value = msg
  showNotificationPopup.value = true
}

const openDialogFromNotification = async (msg) => {
  showNotificationPopup.value = false
  let dialog = dialogs.value.find(d => 
    (d.channel === msg.channel || 
     (isVkChannel(d.channel) && isVkChannel(msg.channel)) ||
     (isMaxChannel(d.channel) && isMaxChannel(msg.channel))) && 
    String(d.peer_id) === String(msg.peer_id)
  )
  if (dialog) {
    await fetchHistory(dialog)
  }
}

// Получить текущий персональный звук активного диалога
const activeDialogSound = computed(() => {
  if (!activeDialog.value) return 'default'
  const key = `multichat_sound_${activeDialog.value.channel}_${activeDialog.value.peer_id}`
  return localStorage.getItem(key) || 'default'
})

// Назначить персональный звук диалогу
const setDialogSound = (dialog, soundId) => {
  if (!dialog) return
  const key = `multichat_sound_${dialog.channel}_${dialog.peer_id}`
  if (soundId === 'default') {
    localStorage.removeItem(key)
    toast.success('Установлен звук по умолчанию')
  } else {
    localStorage.setItem(key, soundId)
    const found = soundLibrary.find(s => s.id === soundId)
    toast.success(`Для этого чата установлен звук: ${found ? found.name : soundId}`)
  }
}

// Сохранить глобальный звук
const saveGlobalSound = (soundId) => {
  globalSound.value = soundId
  localStorage.setItem('multichat_global_sound', soundId)
  if (soundId !== 'mute') {
    playNotificationSound(soundId)
  }
  toast.success('Звук уведомлений по умолчанию сохранен')
}



// ==========================================
// Динамическое управление источниками и ботами
// ==========================================
const vkBots = ref([])

const fetchVkBots = async () => {
  try {
    const res = await axios.get('/api/v1/vk/bots', {
      headers: getRequestHeaders()
    })
    vkBots.value = res.data || []
  } catch (e) {
    console.warn('[Multichat] Failed to fetch vk bots:', e)
  }
}

// Текущая выбранная категория источников: 'all' | 'personal' | 'bots'
const selectedSourceCategory = ref('all')

// Текущий выбранный конкретный источник (ключ)
const selectedSourceKey = ref('all')

// Динамический список всех доступных источников (аккаунты + боты + системные)
const availableSources = computed(() => {
  const list = [
    {
      key: 'all',
      type: 'all',
      title: 'Все источники',
      shortTitle: 'Все',
      icon: 'bx-layer',
      color: 'primary',
      channel: 'all'
    }
  ]

  // 1. Личные аккаунты
  // Личный MAX
  const maxAcc = (accounts.value || []).find(a => a.channel === 'max_user' || a.channel === 'max')
  list.push({
    key: 'max_user',
    type: 'personal',
    title: maxAcc?.name ? `MAX Личный (${maxAcc.name.trim()})` : 'MAX Личный',
    shortTitle: maxAcc?.name ? `MAX ${maxAcc.name.replace('MAX Пользователь', '').trim() || 'Личный'}` : 'MAX Личный',
    icon: 'max-custom',
    color: '#FF5722',
    isMax: true,
    channel: 'max_user'
  })

  // Личный VK
  const vkAcc = (accounts.value || []).find(a => a.channel === 'vk_user')
  list.push({
    key: 'vk_user',
    type: 'personal',
    title: vkAcc?.name ? `VK Личный (${vkAcc.name.trim()})` : 'VK Личный',
    shortTitle: vkAcc?.name ? `VK ${vkAcc.name.length > 15 ? vkAcc.name.substring(0, 15) + '…' : vkAcc.name}` : 'VK Личный',
    icon: 'bxl-vk',
    color: '#0077FF',
    channel: 'vk_user',
    channel_id: vkAcc?.id ? String(vkAcc.id) : null
  })

  // WhatsApp (Личный/Аккаунт)
  list.push({
    key: 'whatsapp',
    type: 'personal',
    title: 'WhatsApp',
    shortTitle: 'WhatsApp',
    icon: 'bxl-whatsapp',
    color: '#25D366',
    channel: 'whatsapp'
  })

  // Telegram (Личный)
  const tgAcc = (accounts.value || []).find(a => a.channel === 'telegram_user')
  if (tgAcc) {
    list.push({
      key: 'telegram_user',
      type: 'personal',
      title: tgAcc?.name ? `TG Личный (${tgAcc.name.trim()})` : 'TG Личный',
      shortTitle: 'TG Личный',
      icon: 'bxl-telegram',
      color: '#26A69A',
      channel: 'telegram_user',
      channel_id: String(tgAcc.id)
    })
  }

  // 2. Боты и Сообщества
  // Подключенные сообщества ВКонтакте
  if (vkBots.value && vkBots.value.length > 0) {
    vkBots.value.forEach(bot => {
      const gId = String(bot.vk_group_id || bot.id)
      list.push({
        key: `vk:${gId}`,
        type: 'bots',
        title: `VK: ${bot.name || `Группа ${gId}`}`,
        shortTitle: `VK: ${bot.name || gId}`,
        icon: 'bxl-vk',
        color: '#4C75A3',
        channel: 'vk',
        channel_id: gId
      })
    })
  } else {
    list.push({
      key: 'vk',
      type: 'bots',
      title: 'VK Сообщества',
      shortTitle: 'VK Группы',
      icon: 'bxl-vk',
      color: '#4C75A3',
      channel: 'vk'
    })
  }

  // MAX Бот
  list.push({
    key: 'max_bot',
    type: 'bots',
    title: 'MAX Бот',
    shortTitle: 'MAX Бот',
    icon: 'bx-bot',
    color: '#E64A19',
    isMax: true,
    isBot: true,
    channel: 'max_bot'
  })

  // Telegram Бот
  list.push({
    key: 'telegram_bot',
    type: 'bots',
    title: 'Telegram Бот',
    shortTitle: 'TG Бот',
    icon: 'bxl-telegram',
    color: '#0088CC',
    channel: 'telegram_bot'
  })

  return list
})

// Каналы для обратной совместимости
const channels = computed(() => availableSources.value)

// Источники, отфильтрованные по выбранной категории ('all' | 'personal' | 'bots')
const displayedSources = computed(() => {
  if (selectedSourceCategory.value === 'all') {
    return availableSources.value
  }
  if (selectedSourceCategory.value === 'personal') {
    return availableSources.value.filter(s => s.type === 'all' || s.type === 'personal')
  }
  if (selectedSourceCategory.value === 'bots') {
    return availableSources.value.filter(s => s.type === 'all' || s.type === 'bots' || s.type === 'bot')
  }
  return availableSources.value
})

// Подсчет непрочитанных сообщений для источника
const getSourceUnreadCount = (src) => {
  if (src.key === 'all') return totalUnreadCount.value
  return (dialogs.value || []).reduce((acc, d) => {
    if (d.is_hidden || isDialogHidden(d.channel, d.peer_id, d)) return acc
    if ((d.unread_count || 0) <= 0) return acc

    if (src.channel_id) {
      if (d.channel === src.channel && String(d.channel_id || '') === String(src.channel_id)) {
        return acc + (d.unread_count || 1)
      }
    } else {
      if (src.key === 'max_user' && (d.channel === 'max_user' || d.channel === 'max' || d.channel === 'max_bridge') && d.channel !== 'max_bot' && d.channel !== 'max_account') {
        return acc + (d.unread_count || 1)
      }
      if (src.key === 'max_bot' && (d.channel === 'max_bot' || d.channel === 'max_account')) {
        return acc + (d.unread_count || 1)
      }
      if (src.key === 'vk_user' && d.channel === 'vk_user') {
        return acc + (d.unread_count || 1)
      }
      if (src.key === 'vk' && d.channel === 'vk') {
        return acc + (d.unread_count || 1)
      }
      if (src.key === 'telegram_bot' && (d.channel === 'telegram_bot' || d.channel === 'telegram')) {
        return acc + (d.unread_count || 1)
      }
      if (src.key === 'telegram_user' && d.channel === 'telegram_user') {
        return acc + (d.unread_count || 1)
      }
      if (src.key === 'whatsapp' && (d.channel === 'whatsapp' || d.channel === 'whatsapp_user')) {
        return acc + (d.unread_count || 1)
      }
    }
    return acc
  }, 0)
}

// Подсчет непрочитанных по категориям:
const personalUnreadCount = computed(() => {
  return (dialogs.value || []).reduce((acc, d) => {
    if (d.is_hidden || isDialogHidden(d.channel, d.peer_id, d)) return acc
    if ((d.unread_count || 0) <= 0) return acc
    const isPersonal = d.channel === 'vk_user' || d.channel === 'max_user' || d.channel === 'max' || d.channel === 'whatsapp' || d.channel === 'telegram_user'
    return isPersonal ? acc + (d.unread_count || 1) : acc
  }, 0)
})

const botsUnreadCount = computed(() => {
  return (dialogs.value || []).reduce((acc, d) => {
    if (d.is_hidden || isDialogHidden(d.channel, d.peer_id, d)) return acc
    if ((d.unread_count || 0) <= 0) return acc
    const isBot = d.channel === 'vk' || d.channel === 'max_bot' || d.channel === 'max_account' || d.channel === 'telegram_bot' || d.channel === 'telegram'
    return isBot ? acc + (d.unread_count || 1) : acc
  }, 0)
})

// Функция выбора источника
const selectSource = (key) => {
  selectedSourceKey.value = key
  const src = availableSources.value.find(s => s.key === key)
  if (src) {
    selectedChannel.value = src.channel || 'all'
  } else {
    selectedChannel.value = 'all'
  }
}

// Функция смены категории источников
const selectSourceCategory = (cat) => {
  selectedSourceCategory.value = cat
  // Если текущий выбранный источник не принадлежит этой категории (и не 'all'), сбрасываем на 'all'
  if (cat !== 'all') {
    const cur = availableSources.value.find(s => s.key === selectedSourceKey.value)
    if (cur && cur.type !== 'all' && cur.type !== cat) {
      selectedSourceKey.value = 'all'
      selectedChannel.value = 'all'
    }
  }
}


const presetColors = [
  '#757575', '#F44336', '#E91E63', '#9C27B0', '#673AB7', 
  '#3F51B5', '#2196F3', '#00BCD4', '#009688', '#4CAF50', 
  '#8BC34A', '#CDDC39', '#FFEB3B', '#FFC107', '#FF9800', '#FF5722'
]

// ==========================================
// Воспроизведение звука с поддержкой Web Audio API
// ==========================================
const playNotificationSound = (soundType = null, dialog = null) => {
  try {
    // СТРОГО: Если передан диалог или сообщение, и этот диалог скрыт — звук полностью отключен!
    if (dialog) {
      if (dialog.is_hidden === true || isDialogHidden(dialog.channel, dialog.peer_id, dialog)) {
        return
      }
    }

    let sound = soundType
    if (!sound && dialog) {
      sound = localStorage.getItem(`multichat_sound_${dialog.channel}_${dialog.peer_id}`)
    }
    if (!sound || sound === 'default') {
      sound = globalSound.value || 'icq'
    }
    
    if (sound === 'mute') return

    // 1. Попытка воспроизвести аудио файл из /sounds/
    const soundFileMap = {
      'icq': '/sounds/icq.mp3',
      'horn': '/sounds/horn.mp3',
      'car_alarm': '/sounds/car_alarm.mp3',
      'chime': '/sounds/chime.mp3',
      'bell': '/sounds/bell.mp3',
      'push': '/sounds/push.mp3',
      'sonar': '/sounds/sonar.mp3',
      'water': '/sounds/water.mp3'
    }

    if (soundFileMap[sound]) {
      const audio = new Audio(soundFileMap[sound])
      audio.volume = soundVolume.value
      audio.play().catch(() => {
        playSynthesizedSound(sound)
      })
    } else {
      playSynthesizedSound(sound)
    }
  } catch (e) {
    console.warn('Audio play error:', e)
  }
}

const playSynthesizedSound = (soundType) => {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext
    if (!AudioContext) return
    const ctx = new AudioContext()
    const vol = soundVolume.value
    
    if (soundType === 'icq') {
      // Легендарный звук ICQ "О-оу!" (Uh-oh)
      const now = ctx.currentTime
      const osc1 = ctx.createOscillator()
      const gain1 = ctx.createGain()
      osc1.type = 'sine'
      osc1.frequency.setValueAtTime(320, now)
      osc1.frequency.exponentialRampToValueAtTime(280, now + 0.09)
      gain1.gain.setValueAtTime(vol * 0.5, now)
      gain1.gain.exponentialRampToValueAtTime(0.01, now + 0.12)
      osc1.connect(gain1)
      gain1.connect(ctx.destination)
      osc1.start(now)
      osc1.stop(now + 0.12)

      const osc2 = ctx.createOscillator()
      const gain2 = ctx.createGain()
      osc2.type = 'sine'
      osc2.frequency.setValueAtTime(440, now + 0.13)
      osc2.frequency.exponentialRampToValueAtTime(680, now + 0.32)
      gain2.gain.setValueAtTime(vol * 0.6, now + 0.13)
      gain2.gain.exponentialRampToValueAtTime(0.01, now + 0.35)
      osc2.connect(gain2)
      gain2.connect(ctx.destination)
      osc2.start(now + 0.13)
      osc2.stop(now + 0.35)
    } else if (soundType === 'horn') {
      // Автомобильный клаксон (двойной сигнал Би-Бип!)
      const now = ctx.currentTime
      ;[0, 0.16].forEach(offset => {
        const o1 = ctx.createOscillator()
        const o2 = ctx.createOscillator()
        const g = ctx.createGain()
        
        o1.type = 'sawtooth'
        o2.type = 'sawtooth'
        o1.frequency.setValueAtTime(415, now + offset)
        o2.frequency.setValueAtTime(495, now + offset)
        
        g.gain.setValueAtTime(vol * 0.45, now + offset)
        g.gain.exponentialRampToValueAtTime(0.01, now + offset + 0.11)
        
        o1.connect(g)
        o2.connect(g)
        g.connect(ctx.destination)
        
        o1.start(now + offset)
        o2.start(now + offset)
        o1.stop(now + offset + 0.11)
        o2.stop(now + offset + 0.11)
      })
    } else if (soundType === 'car_alarm') {
      // Автомобильный сигнал / гудок автомобиля
      const now = ctx.currentTime
      const o1 = ctx.createOscillator()
      const o2 = ctx.createOscillator()
      const g = ctx.createGain()
      
      o1.type = 'triangle'
      o2.type = 'sawtooth'
      o1.frequency.setValueAtTime(392, now) // G4
      o2.frequency.setValueAtTime(523, now) // C5
      
      g.gain.setValueAtTime(vol * 0.55, now)
      g.gain.setValueAtTime(vol * 0.55, now + 0.28)
      g.gain.exponentialRampToValueAtTime(0.01, now + 0.45)
      
      o1.connect(g)
      o2.connect(g)
      g.connect(ctx.destination)
      
      o1.start(now)
      o2.start(now)
      o1.stop(now + 0.45)
      o2.stop(now + 0.45)
    } else if (soundType === 'bell') {
      const now = ctx.currentTime
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'triangle'
      osc.frequency.setValueAtTime(880, now)
      gain.gain.setValueAtTime(vol * 0.5, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(now)
      osc.stop(now + 0.6)
    } else if (soundType === 'water') {
      const now = ctx.currentTime
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.setValueAtTime(550, now)
      osc.frequency.exponentialRampToValueAtTime(1400, now + 0.08)
      gain.gain.setValueAtTime(vol * 0.6, now)
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.12)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(now)
      osc.stop(now + 0.12)
    } else {
      const now = ctx.currentTime
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.setValueAtTime(520, now)
      osc.frequency.setValueAtTime(660, now + 0.08)
      gain.gain.setValueAtTime(vol * 0.5, now)
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.25)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(now)
      osc.stop(now + 0.25)
    }
  } catch (err) {
    console.error(err)
  }
}


// Загрузка личных аккаунтов
const fetchAccounts = async () => {
  loadingAccounts.value = true
  try {
    const res = await axios.get('/api/v1/multichat/accounts', {
      headers: getRequestHeaders()
    })
    accounts.value = res.data
  } catch (e) {
    console.error('Ошибка загрузки аккаунтов:', e)
  } finally {
    loadingAccounts.value = false
  }
}

// Запуск инициализации QR-кода Telegram
const initTelegramQr = async () => {
  loadingTelegramQr.value = true
  try {
    const res = await axios.post('/api/v1/multichat/accounts/telegram/qr/init', {}, {
      headers: getRequestHeaders()
    })
    qrData.value = res.data
    
    if (qrPollingInterval.value) clearInterval(qrPollingInterval.value)
    qrPollingInterval.value = setInterval(async () => {
      if (!qrData.value) return
      try {
        const stRes = await axios.get(`/api/v1/multichat/accounts/telegram/qr/status/${qrData.value.session_id}`, {
          headers: getRequestHeaders()
        })
        if (stRes.data.status === 'active') {
          toast.success('Telegram аккаунт успешно подключен!')
          clearInterval(qrPollingInterval.value)
          qrData.value = null
          fetchAccounts()
        }
      } catch (err) {
        console.error(err)
      }
    }, 3000)
  } catch (e) {
    toast.error('Не удалось сгенерировать QR-код Telegram')
  } finally {
    loadingTelegramQr.value = false
  }
}

// Запуск инициализации QR-кода WhatsApp
const initWhatsAppQr = async () => {
  loadingWhatsAppQr.value = true
  try {
    const res = await axios.post('/api/v1/multichat/accounts/whatsapp/qr/init', {}, {
      headers: getRequestHeaders()
    })
    waQrData.value = res.data
    
    if (waPollingInterval.value) clearInterval(waPollingInterval.value)
    waPollingInterval.value = setInterval(async () => {
      if (!waQrData.value) return
      try {
        const stRes = await axios.get(`/api/v1/multichat/accounts/whatsapp/qr/status/${waQrData.value.session_id}`, {
          headers: getRequestHeaders()
        })
        if (stRes.data.status === 'active') {
          toast.success('WhatsApp аккаунт успешно подключен!')
          clearInterval(waPollingInterval.value)
          waQrData.value = null
          fetchAccounts()
        }
      } catch (err) {
        console.error(err)
      }
    }, 3000)
  } catch (e) {
    toast.error('Не удалось сгенерировать QR-код WhatsApp')
  } finally {
    loadingWhatsAppQr.value = false
  }
}

// Подтверждение привязки WhatsApp
const confirmWhatsApp = async () => {
  if (!waQrData.value) return
  confirmingWa.value = true
  try {
    await axios.post(`/api/v1/multichat/accounts/whatsapp/qr/confirm/${waQrData.value.session_id}`, {
      name: waAccountName.value.trim() || 'WhatsApp Аккаунт',
      phone: waAccountPhone.value.trim() || null,
      token: waGreenApiToken.value.trim() || null
    }, {
      headers: getRequestHeaders()
    })
    toast.success('WhatsApp аккаунт успешно добавлен!')
    waQrData.value = null
    fetchAccounts()
  } catch (e) {
    toast.error('Ошибка сохранения WhatsApp аккаунта')
  } finally {
    confirmingWa.value = false
  }
}

// Состояние входа в MAX (Web Instance Bridge)
const maxAuthTab = ref('qr') // 'qr' | 'sms' | 'token'
const maxQrData = ref(null)
const loadingMaxQr = ref(false)
const maxPollingInterval = ref(null)
const maxQrCountdownInterval = ref(null)
const maxQrTimeLeft = ref(90)
const maxQrStatus = ref('pending')

const maxPhone = ref('')
const maxSmsCode = ref('')
const maxSmsSessionId = ref('')
const maxSmsSent = ref(false)
const requestingMaxSms = ref(false)
const verifyingMaxSms = ref(false)
const maxAccountTitle = ref('')

const confirmingMaxBridge = ref(false)
const maxManualPhone = ref('')
const maxManualName = ref('')

// Инициализация динамического QR MAX Web Bridge
const initMaxQr = async () => {
  loadingMaxQr.value = true
  maxQrStatus.value = 'pending'
  try {
    const res = await axios.post('/api/v1/multichat/accounts/max/qr/init', {}, {
      headers: getRequestHeaders()
    })
    maxQrData.value = res.data
    maxQrTimeLeft.value = res.data.expires_in || 90

    if (maxQrCountdownInterval.value) clearInterval(maxQrCountdownInterval.value)
    maxQrCountdownInterval.value = setInterval(() => {
      if (maxQrTimeLeft.value > 0) {
        maxQrTimeLeft.value--
      } else {
        maxQrStatus.value = 'expired'
        clearInterval(maxQrCountdownInterval.value)
      }
    }, 1000)
    
    if (maxPollingInterval.value) clearInterval(maxPollingInterval.value)
    maxPollingInterval.value = setInterval(async () => {
      if (!maxQrData.value) return
      try {
        const stRes = await axios.get(`/api/v1/multichat/accounts/max/qr/status/${maxQrData.value.session_id}`, {
          headers: getRequestHeaders()
        })
        maxQrStatus.value = stRes.data.status
        if (stRes.data.status === 'active') {
          toast.success('MAX аккаунт успешно подключен!')
          clearInterval(maxPollingInterval.value)
          clearInterval(maxQrCountdownInterval.value)
          maxQrData.value = null
          fetchAccounts()
          fetchDialogs()
        } else if (stRes.data.status === 'expired') {
          clearInterval(maxPollingInterval.value)
          clearInterval(maxQrCountdownInterval.value)
        }
      } catch (err) {
        console.error(err)
      }
    }, 2500)
  } catch (e) {
    toast.error('Не удалось сгенерировать QR-код MAX')
  } finally {
    loadingMaxQr.value = false
  }
}

// Ручное подтверждение привязки MAX Web Bridge
const confirmMaxBridge = async () => {
  if (!maxQrData.value) return
  confirmingMaxBridge.value = true
  try {
    const res = await axios.post(`/api/v1/multichat/accounts/max/qr/confirm/${maxQrData.value.session_id}`, {
      phone: maxManualPhone.value.trim() || null,
      name: maxManualName.value.trim() || 'Личный аккаунт MAX'
    }, {
      headers: getRequestHeaders()
    })
    toast.success(res.data.message || 'Аккаунт MAX успешно подключен!')
    if (maxPollingInterval.value) clearInterval(maxPollingInterval.value)
    if (maxQrCountdownInterval.value) clearInterval(maxQrCountdownInterval.value)
    maxQrData.value = null
    maxManualPhone.value = ''
    maxManualName.value = ''
    fetchAccounts()
    fetchDialogs()
  } catch (e) {
    const detail = e.response?.data?.detail || 'Ошибка подтверждения сессии'
    toast.error(detail)
  } finally {
    confirmingMaxBridge.value = false
  }
}

// Запрос SMS для MAX
const requestMaxSms = async () => {

  if (!maxPhone.value.trim()) {
    toast.error('Введите номер телефона')
    return
  }
  requestingMaxSms.value = true
  try {
    const res = await axios.post('/api/v1/multichat/accounts/max/sms/request', {
      phone: maxPhone.value.trim()
    }, {
      headers: getRequestHeaders()
    })
    maxSmsSessionId.value = res.data.session_id
    maxSmsSent.value = true
    toast.success(res.data.message || 'SMS-код отправлен')
  } catch (e) {
    const detail = e.response?.data?.detail || 'Ошибка отправки SMS'
    toast.error(detail)
  } finally {
    requestingMaxSms.value = false
  }
}

// Подтверждение SMS для MAX
const verifyMaxSms = async () => {
  if (!maxSmsCode.value.trim()) {
    toast.error('Введите код из SMS')
    return
  }
  verifyingMaxSms.value = true
  try {
    const res = await axios.post('/api/v1/multichat/accounts/max/sms/verify', {
      session_id: maxSmsSessionId.value,
      code: maxSmsCode.value.trim(),
      name: maxAccountTitle.value.trim() || `MAX ${maxPhone.value.trim()}`
    }, {
      headers: getRequestHeaders()
    })
    toast.success(res.data.message || 'Аккаунт MAX успешно подключен!')
    maxSmsSent.value = false
    maxSmsCode.value = ''
    maxPhone.value = ''
    maxAccountTitle.value = ''
    fetchAccounts()
    fetchDialogs()
  } catch (e) {
    const detail = e.response?.data?.detail || 'Неверный код подтверждения'
    toast.error(detail)
  } finally {
    verifyingMaxSms.value = false
  }
}

// Состояние входа ВКонтакте
const vkDirectLogin = ref('')
const vkDirectPassword = ref('')
const vkDirectCode = ref('')
const vkDirectSid = ref('')
const vkNeed2Fa = ref(false)
const vk2FaMessage = ref('')
const vkAuthTab = ref('qr') // 'qr' | 'direct' | 'custom_app' | 'token'
const vkCustomAppId = ref('')
const loggingInVkDirect = ref(false)

// VK QR-код авторизация
const vkQrBase64 = ref('')
const vkQrAuthUrl = ref('')
const vkQrLoading = ref(false)
const vkQrTokenInput = ref('')
const vkQrConfirming = ref(false)

const initVkQr = async () => {
  vkQrLoading.value = true
  try {
    const res = await axios.post('/api/v1/multichat/accounts/vk/qr/init', {}, {
      headers: getRequestHeaders()
    })
    vkQrBase64.value = res.data.qr_code
    vkQrAuthUrl.value = res.data.oauth_url
  } catch (err) {
    toast.error('Не удалось сгенерировать QR-код ВКонтакте')
  } finally {
    vkQrLoading.value = false
  }
}

const confirmVkQr = async () => {
  if (!vkQrTokenInput.value.trim()) {
    toast.error('Вставьте скопированный токен или ссылку после авторизации')
    return
  }
  vkQrConfirming.value = true
  try {
    const res = await axios.post('/api/v1/multichat/accounts/vk/qr/confirm', {
      token_or_url: vkQrTokenInput.value.trim()
    }, {
      headers: getRequestHeaders()
    })
    toast.success(`Аккаунт ${res.data.name} успешно подключен!`)
    vkQrTokenInput.value = ''
    fetchAccounts()
    fetchDialogs()
  } catch (err) {
    const detail = err.response?.data?.detail || 'Ошибка авторизации VK'
    toast.error(detail)
  } finally {
    vkQrConfirming.value = false
  }
}

// Lightbox для полноразмерного просмотра изображений из сообщений
const previewImageUrl = ref(null)
const showImagePreviewModal = ref(false)
const openImagePreview = (url) => {
  if (!url) return
  previewImageUrl.value = url
  showImagePreviewModal.value = true
}

// Автоматический fallback на бэкенд-прокси при 403 Forbidden / CORS блокировках CDN
const onAttachmentImageError = (event, att) => {
  const target = event.target
  if (!target || target.dataset.fallbackDone === 'true') return
  target.dataset.fallbackDone = 'true'
  const rawUrl = att.url || att.preview_url
  if (rawUrl && !rawUrl.includes('/api/v1/multichat/proxy-image')) {
    target.src = `/api/v1/multichat/proxy-image?url=${encodeURIComponent(rawUrl)}`
  }
}

const onLightboxImageError = (event) => {
  const target = event.target
  if (!target || target.dataset.fallbackDone === 'true') return
  target.dataset.fallbackDone = 'true'
  if (previewImageUrl.value && !previewImageUrl.value.includes('/api/v1/multichat/proxy-image')) {
    target.src = `/api/v1/multichat/proxy-image?url=${encodeURIComponent(previewImageUrl.value)}`
  }
}


const openCustomAppOAuth = () => {

  const appId = vkCustomAppId.value.trim()
  if (!appId) {
    toast.error('Укажите ID Standalone-приложения ВКонтакте')
    return
  }
  const url = `https://oauth.vk.com/authorize?client_id=${appId}&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=messages,offline,photos,docs&response_type=token&v=5.131`
  window.open(url, '_blank')
}


const handleVkDirectAuth = async () => {
  if (!vkDirectLogin.value.trim() || !vkDirectPassword.value.trim()) {
    toast.error('Введите логин и пароль')
    return
  }
  loggingInVkDirect.value = true
  try {
    const res = await axios.post('/api/v1/multichat/accounts/vk/direct-login', {
      username: vkDirectLogin.value.trim(),
      password: vkDirectPassword.value.trim(),
      code: vkDirectCode.value.trim(),
      sid: vkDirectSid.value
    }, {
      headers: getRequestHeaders()
    })
    
    if (res.data.status === 'need_2fa') {
      vkNeed2Fa.value = true
      vkDirectSid.value = res.data.validation_sid
      vk2FaMessage.value = res.data.message
      toast.info(res.data.message)
    } else if (res.data.status === 'success') {
      toast.success(res.data.message || 'Аккаунт ВКонтакте подключен!')
      vkDirectLogin.value = ''
      vkDirectPassword.value = ''
      vkDirectCode.value = ''
      vkDirectSid.value = ''
      vkNeed2Fa.value = false
      fetchAccounts()
      fetchDialogs()
    }
  } catch (err) {
    const detail = err.response?.data?.detail || 'Ошибка авторизации'
    toast.error(detail)
  } finally {
    loggingInVkDirect.value = false
  }
}

// Запуск окна авторизации ВК
const openVkAuthWindow = (appType = 'vk_admin') => {
  const clientIds = {
    'vk_admin': '6121396', // VK Admin (Android)
    'vfeed': '4083558',    // VFeed (iOS/Standalone)
    'sferum': '7598572',   // Сферум Android
    'vk_host': 'vkhost'
  }
  
  if (appType === 'vk_host') {
    window.open('https://vkhost.github.io/', '_blank', 'width=750,height=600')
    return
  }
  
  const cid = clientIds[appType] || '6121396'
  const vkAuthUrl = `https://oauth.vk.com/authorize?client_id=${cid}&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=messages,offline,photos,docs,groups&response_type=token&v=5.131`
  window.open(vkAuthUrl, "_blank", "width=650,height=550")
}

// Сохранение личного аккаунта (VK / MAX)
const saveAccount = async () => {
  if (!newAccountToken.value.trim()) return
  savingAccount.value = true
  try {
    await axios.post('/api/v1/multichat/accounts', {
      channel: newAccountType.value,
      name: newAccountName.value,
      phone: newAccountPhone.value,
      token: newAccountToken.value
    }, {
      headers: getRequestHeaders()
    })
    toast.success('Личный аккаунт успешно подключен!')
    newAccountName.value = ''
    newAccountPhone.value = ''
    newAccountToken.value = ''
    fetchAccounts()
    fetchDialogs()
  } catch (e) {
    const detail = e.response?.data?.detail || 'Не удалось подключить аккаунт'
    toast.error(detail)
  } finally {
    savingAccount.value = false
  }
}

// Проверка состояния соединения аккаунта
const testingAccountId = ref(null)
const testAccountConnection = async (acc) => {
  testingAccountId.value = acc.id
  try {
    const res = await axios.post(`/api/v1/multichat/accounts/${acc.id}/test`, {}, {
      headers: getRequestHeaders()
    })
    if (res.data.status === 'ok') {
      toast.success(res.data.message || 'Соединение успешно проверено!')
    } else {
      toast.error(res.data.message || 'Ошибка подключения')
    }
  } catch (e) {
    const detail = e.response?.data?.detail || 'Не удалось проверить соединение'
    toast.error(detail)
  } finally {
    testingAccountId.value = null
  }
}

// Отключение личного аккаунта (история сообщений сохраняется)
const deleteAccount = async (accId) => {
  if (!confirm('Отключить этот аккаунт? История сообщений и диалогов останется в Мультичате.')) return
  try {
    await axios.delete(`/api/v1/multichat/accounts/${accId}`, {
      headers: getRequestHeaders()
    })
    await fetchAccounts()
    toast.success('Аккаунт отключен. Сообщения сохранены.')
  } catch (e) {
    toast.error('Не удалось отключить аккаунт')
  }
}

// Ручная очистка сообщений конкретного аккаунта по кнопке оператора
const clearingAccountMsgId = ref(null)
const clearAccountMessages = async (acc) => {
  if (!confirm(`Удалить все сообщения и диалоги, загруженные с аккаунта "${acc.name}"? Сам аккаунт останется подключенным.`)) return
  clearingAccountMsgId.value = acc.id
  try {
    const res = await axios.post(`/api/v1/multichat/accounts/${acc.id}/clear-messages`, {}, {
      headers: getRequestHeaders()
    })
    await fetchDialogs()
    if (activeDialog.value && (activeDialog.value.channel === acc.channel || activeDialog.value.channel_id === String(acc.id))) {
      activeDialog.value = null
      messages.value = []
    }
    toast.success(res.data.message || 'Сообщения аккаунта успешно удалены')
  } catch (e) {
    toast.error('Не удалось очистить сообщения аккаунта')
  } finally {
    clearingAccountMsgId.value = null
  }
}



// Закрепление / открепление диалога
const togglePin = async (dialog) => {
  if (!dialog) return
  try {
    const res = await axios.post(`/api/v1/multichat/dialogs/${dialog.channel}/${dialog.peer_id}/pin`, {}, {
      headers: getRequestHeaders()
    })
    dialog.is_pinned = res.data.is_pinned
    
    if (activeDialog.value && activeDialog.value.channel === dialog.channel && activeDialog.value.peer_id === dialog.peer_id) {
      activeDialog.value.is_pinned = res.data.is_pinned
    }
    
    // Пересортировываем список диалогов (закрепленные первыми)
    dialogs.value.sort((a, b) => {
      if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1
      return new Date(b.last_message_time || 0) - new Date(a.last_message_time || 0)
    })
    
    toast.success(dialog.is_pinned ? 'Чатик закреплен вверху' : 'Чатик откреплен')
  } catch (e) {
    toast.error('Не удалось изменить статус закрепления')
  }
}

// Скрытие / возвращение диалога в общий список
const toggleHide = async (dialog) => {
  if (!dialog) return
  try {
    const res = await axios.post(`/api/v1/multichat/dialogs/${dialog.channel}/${dialog.peer_id}/hide`, {}, {
      headers: getRequestHeaders()
    })
    const isHidden = res.data.is_hidden
    dialog.is_hidden = isHidden

    // Мгновенная синхронизация локального множества скрытых диалогов
    const pIdStr = String(dialog.peer_id)
    const keyUnderscore = `${dialog.channel}_${pIdStr}`
    const keyColon = `${dialog.channel}:${pIdStr}`
    
    let alts = [dialog.channel]
    if (dialog.channel === 'vk' || dialog.channel === 'vk_user') {
      alts = ['vk', 'vk_user']
    } else if (['max', 'max_user', 'max_bot', 'max_account'].includes(dialog.channel)) {
      alts = ['max', 'max_user', 'max_bot', 'max_account']
    } else if (dialog.channel === 'whatsapp' || dialog.channel === 'whatsapp_user') {
      alts = ['whatsapp', 'whatsapp_user']
    }

    if (isHidden) {
      alts.forEach(alt => {
        hiddenDialogsKeys.value.add(`${alt}_${pIdStr}`)
        hiddenDialogsKeys.value.add(`${alt}:${pIdStr}`)
      })
    } else {
      alts.forEach(alt => {
        hiddenDialogsKeys.value.delete(`${alt}_${pIdStr}`)
        hiddenDialogsKeys.value.delete(`${alt}:${pIdStr}`)
      })
    }
    try {
      localStorage.setItem('multichat_hidden_keys', JSON.stringify(Array.from(hiddenDialogsKeys.value)))
    } catch (e) {}
    
    if (activeDialog.value && 
        (activeDialog.value.channel === dialog.channel || (isVkChannel(activeDialog.value.channel) && isVkChannel(dialog.channel)) || (isMaxChannel(activeDialog.value.channel) && isMaxChannel(dialog.channel))) && 
        String(activeDialog.value.peer_id) === pIdStr) {
      activeDialog.value.is_hidden = isHidden
    }

    // Если находимся в основном списке и скрыли диалог — убираем его из видимого списка и закрываем, если он был открыт
    if (!showHiddenOnly.value && isHidden) {
      dialogs.value = dialogs.value.filter(d => !(
        (d.channel === dialog.channel || (isVkChannel(d.channel) && isVkChannel(dialog.channel)) || (isMaxChannel(d.channel) && isMaxChannel(dialog.channel))) && 
        String(d.peer_id) === pIdStr
      ))
      if (activeDialog.value && String(activeDialog.value.peer_id) === pIdStr) {
        activeDialog.value = null
        messages.value = []
      }
      try {
        const cached = localStorage.getItem('multichat_cached_dialogs')
        if (cached) {
          const parsed = JSON.parse(cached)
          const updated = parsed.filter(d => !(
            (d.channel === dialog.channel || (isVkChannel(d.channel) && isVkChannel(dialog.channel)) || (isMaxChannel(d.channel) && isMaxChannel(dialog.channel))) && 
            String(d.peer_id) === pIdStr
          ))
          localStorage.setItem('multichat_cached_dialogs', JSON.stringify(updated))
        }
      } catch (e) {}
    } else if (showHiddenOnly.value && !isHidden) {
      // Если находимся в списке скрытых и вернули диалог — убираем его из списка скрытых
      dialogs.value = dialogs.value.filter(d => !(
        (d.channel === dialog.channel || (isVkChannel(d.channel) && isVkChannel(dialog.channel)) || (isMaxChannel(d.channel) && isMaxChannel(dialog.channel))) && 
        String(d.peer_id) === pIdStr
      ))
      if (activeDialog.value && String(activeDialog.value.peer_id) === pIdStr) {
        activeDialog.value = null
        messages.value = []
      }
    }

    toast.success(isHidden ? 'Диалог скрыт из общего списка' : 'Диалог возвращен в общий список')
  } catch (e) {
    toast.error('Не удалось изменить статус скрытия диалога')
  }
}

// Получение списка всех меток
const fetchTags = async () => {
  try {
    const response = await axios.get('/api/v1/multichat/tags', {
      headers: getRequestHeaders()
    })
    allTags.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки меток:', error)
  }
}

// Создание новой метки из менеджера
const createTag = async () => {
  if (!newTagName.value.trim()) return
  savingTag.value = true
  try {
    const response = await axios.post('/api/v1/multichat/tags', {
      name: newTagName.value.trim(),
      color: newTagColor.value
    }, {
      headers: getRequestHeaders()
    })
    allTags.value.push(response.data)
    newTagName.value = ''
    toast.success('Метка успешно создана')
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Не удалось создать метку')
  } finally {
    savingTag.value = false
  }
}

// Быстрое создание метки прямо из выпадающего меню чата и моментальная привязка к диалогу
const createQuickTagAndAttach = async (targetDialog) => {
  if (!quickTagName.value.trim()) return
  creatingQuickTag.value = true
  try {
    const res = await axios.post('/api/v1/multichat/tags', {
      name: quickTagName.value.trim(),
      color: quickTagColor.value
    }, {
      headers: getRequestHeaders()
    })
    const newTag = res.data
    allTags.value.push(newTag)
    quickTagName.value = ''
    
    if (targetDialog) {
      await toggleDialogTag(targetDialog, newTag)
    }
    toast.success('Новая метка создана и привязана')
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Не удалось создать метку')
  } finally {
    creatingQuickTag.value = false
  }
}

// Удаление метки
const deleteTag = async (tagId) => {
  if (!confirm('Вы уверены, что хотите удалить эту метку?')) return
  try {
    await axios.delete(`/api/v1/multichat/tags/${tagId}`, {
      headers: getRequestHeaders()
    })
    allTags.value = allTags.value.filter(t => t.id !== tagId)
    if (selectedTagId.value === tagId) {
      selectedTagId.value = null
    }
    fetchDialogs()
    toast.success('Метка удалена')
  } catch (error) {
    toast.error('Не удалось удалить метку')
  }
}

// Переключение метки у диалога (присвоение / снятие)
const toggleDialogTag = async (dialog, tag) => {
  if (!dialog) return
  
  const tagsAttached = dialog.tags || []
  const hasTag = tagsAttached.some(t => t.id === tag.id)
  
  let newTagIds = []
  if (hasTag) {
    newTagIds = tagsAttached.filter(t => t.id !== tag.id).map(t => t.id)
  } else {
    newTagIds = [...tagsAttached.map(t => t.id), tag.id]
  }

  try {
    await axios.post(`/api/v1/multichat/dialogs/${dialog.channel}/${dialog.peer_id}/tags`, {
      tag_ids: newTagIds
    }, {
      headers: getRequestHeaders()
    })
    
    const updatedTags = hasTag 
      ? tagsAttached.filter(t => t.id !== tag.id) 
      : [...tagsAttached, tag]
      
    dialog.tags = updatedTags
    
    if (activeDialog.value && activeDialog.value.channel === dialog.channel && activeDialog.value.peer_id === dialog.peer_id) {
      activeDialog.value.tags = updatedTags
    }
    
    const dialogInList = dialogs.value.find(d => d.channel === dialog.channel && d.peer_id === dialog.peer_id)
    if (dialogInList) {
      dialogInList.tags = updatedTags
    }
    
    toast.success(hasTag ? `Метка "${tag.name}" снята` : `Метка "${tag.name}" присвоена`)
  } catch (error) {
    toast.error('Не удалось обновить метки диалога')
  }
}

// Получение списка диалогов с поддержкой моментального кэша
const fetchDialogs = async (silent = false) => {
  if (!silent && (!dialogs.value || dialogs.value.length === 0)) {
    loadingDialogs.value = true
  }
  try {
    const params = {}
    if (selectedSourceKey.value && selectedSourceKey.value !== 'all') {
      const src = availableSources.value.find(s => s.key === selectedSourceKey.value)
      if (src) {
        if (src.channel && src.channel !== 'all') params.channel = src.channel
        if (src.channel_id) params.channel_id = src.channel_id
      }
    } else if (selectedChannel.value && selectedChannel.value !== 'all') {
      params.channel = selectedChannel.value
    }

    if (selectedTagId.value) params.tag_id = selectedTagId.value
    if (showHiddenOnly.value) params.hidden_only = true
    if (unreadOnly.value) params.unread_only = true
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const response = await axios.get('/api/v1/multichat/dialogs', { 
      params,
      headers: getRequestHeaders()
    })
    const data = response.data || []
    mergeDialogsList(data)

    // Сохраняем в локальный кэш браузера для мгновенного отображения при следующем открытии страницы
    if (selectedSourceKey.value === 'all' && selectedChannel.value === 'all' && !selectedTagId.value && !showHiddenOnly.value && !unreadOnly.value && !startDate.value && !endDate.value) {
      try {
        const toCache = data.filter(d => !d.is_hidden && !isDialogHidden(d.channel, d.peer_id, d)).slice(0, 100)
        localStorage.setItem('multichat_cached_dialogs', JSON.stringify(toCache))
      } catch (e) {}
    }
  } catch (error) {
    if (!silent) toast.error('Не удалось загрузить диалоги')
    console.error(error)
  } finally {
    loadingDialogs.value = false
  }
}

// Пагинация и управление загрузкой истории
const hasMoreMessages = ref(true)
const loadingMoreMessages = ref(false)
const markingAllAsRead = ref(false)
let currentHistoryAbortController = null

// Загрузка истории выбранного диалога (мгновенно из кэша за 0 мс)
const fetchHistory = async (dialog, targetMessageId = null) => {
  if (currentHistoryAbortController) {
    currentHistoryAbortController.abort()
  }
  currentHistoryAbortController = new AbortController()

  activeDialog.value = dialog
  hasMoreMessages.value = true
  loadingMoreMessages.value = false

  // 1. Мгновенная загрузка из кэша (0 мс, без мерцаний и спиннера)
  const cached = chatStore.getCachedMessages(dialog.channel, dialog.peer_id)
  if (cached && cached.length > 0) {
    messages.value = [...cached]
    loadingHistory.value = false
    if (!targetMessageId) {
      scrollToBottom()
    }
  } else {
    loadingHistory.value = true
    messages.value = []
  }

  try {
    const response = await axios.get(`/api/v1/multichat/dialogs/${dialog.channel}/${dialog.peer_id}/history`, {
      params: { limit: 20 },
      headers: getRequestHeaders(),
      signal: currentHistoryAbortController.signal
    })
    const fetched = response.data || []
    messages.value = fetched
    chatStore.setCachedMessages(dialog.channel, dialog.peer_id, fetched)
    hasMoreMessages.value = fetched.length >= 20
    
    if (dialog.unread_count > 0) {
      markAsRead(dialog) // Асинхронно, не блокируя UI
    }
    
    if (targetMessageId) {
      nextTick(() => {
        setTimeout(() => {
          scrollToMessageId(targetMessageId)
        }, 50)
      })
    } else {
      scrollToBottom()
    }
  } catch (error) {
    if (axios.isCancel(error) || error.name === 'CanceledError' || error.name === 'AbortError') {
      return
    }
    toast.error('Не удалось загрузить историю переписки')
    console.error(error)
  } finally {
    loadingHistory.value = false
  }
}

// Дозагрузка старых сообщений при прокрутке вверх
const loadMoreMessages = async () => {
  if (loadingMoreMessages.value || !hasMoreMessages.value || !activeDialog.value || messages.value.length === 0) {
    return
  }

  const oldestMsg = messages.value[0]
  if (!oldestMsg || !oldestMsg.id) return

  loadingMoreMessages.value = true
  const container = messageContainer.value
  const previousScrollHeight = container ? container.scrollHeight : 0

  try {
    const response = await axios.get(`/api/v1/multichat/dialogs/${activeDialog.value.channel}/${activeDialog.value.peer_id}/history`, {
      params: {
        limit: 20,
        before_id: oldestMsg.id
      },
      headers: getRequestHeaders()
    })
    const olderMessages = response.data || []
    if (olderMessages.length < 20) {
      hasMoreMessages.value = false
    }

    if (olderMessages.length > 0) {
      const existingIds = new Set(messages.value.map(m => m.id).filter(Boolean))
      const uniqueOlder = olderMessages.filter(m => !m.id || !existingIds.has(m.id))

      if (uniqueOlder.length > 0) {
        messages.value = [...uniqueOlder, ...messages.value]

        // Сохраняем положение скролла без прыжков
        nextTick(() => {
          if (container) {
            const newScrollHeight = container.scrollHeight
            container.scrollTop = newScrollHeight - previousScrollHeight
          }
        })
      }
    }
  } catch (error) {
    console.error('Error loading older messages:', error)
  } finally {
    loadingMoreMessages.value = false
  }
}

// Обработчик прокрутки контейнера сообщений
const handleChatScroll = () => {
  if (!messageContainer.value) return
  if (messageContainer.value.scrollTop < 60 && !loadingMoreMessages.value && hasMoreMessages.value && !loadingHistory.value) {
    loadMoreMessages()
  }
}

const markAsRead = async (dialog) => {
  try {
    await axios.post(`/api/v1/multichat/dialogs/${dialog.channel}/${dialog.peer_id}/read`, {}, {
      headers: getRequestHeaders()
    })
    dialog.unread_count = 0
  } catch (error) {
    console.error('Error marking dialog as read:', error)
  }
}

// Массовая пометка всех чатов как прочитанных
const markAllAsRead = async () => {
  if (markingAllAsRead.value) return
  markingAllAsRead.value = true

  // Оптимистично обнуляем счетчики непрочитанных в списке диалогов
  dialogs.value.forEach(d => {
    d.unread_count = 0
  })

  try {
    await axios.post('/api/v1/multichat/dialogs/read-all', {
      channel: selectedChannel.value
    }, {
      headers: getRequestHeaders()
    })
    toast.success('Все чаты помечены как прочитанные')
  } catch (error) {
    toast.error('Не удалось пометить все чаты прочитанными')
    console.error(error)
    fetchDialogs()
  } finally {
    markingAllAsRead.value = false
  }
}

const sendMessage = async () => {
  if (!replyText.value.trim() || !activeDialog.value) return
  
  sendingMessage.value = true
  const dialog = activeDialog.value
  const textToSend = replyText.value
  replyText.value = ''
  
  try {
    const response = await axios.post(`/api/v1/multichat/dialogs/${dialog.channel}/${dialog.peer_id}/send`, {
      text: textToSend
    }, {
      headers: getRequestHeaders()
    })
    
    messages.value.push(response.data)
    chatStore.appendMessageToCache(dialog.channel, dialog.peer_id, response.data)
    
    const dialogInList = dialogs.value.find(d => d.channel === dialog.channel && d.peer_id === dialog.peer_id)
    if (dialogInList) {
      dialogInList.last_message = textToSend
      dialogInList.last_message_time = new Date().toISOString()
    }
    
    scrollToBottom(true)
  } catch (error) {
    replyText.value = textToSend
    toast.error('Не удалось отправить сообщение')
    console.error(error)
  } finally {
    sendingMessage.value = false
  }
}

// Гарантированная плавная и моментальная прокрутка в конец переписки
const scrollToBottom = (smooth = false) => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight + 10000
    }
    setTimeout(() => {
      if (messageContainer.value) {
        messageContainer.value.scrollTop = messageContainer.value.scrollHeight + 10000
      }
    }, 60)
    setTimeout(() => {
      if (messageContainer.value) {
        messageContainer.value.scrollTop = messageContainer.value.scrollHeight + 10000
      }
    }, 200)
  })
}

// ----------------------------------------------------
// Логика поиска внутри активного чата
// ----------------------------------------------------
const inChatSearchResults = computed(() => {
  if (!showInChatSearch.value || (!inChatSearchQuery.value.trim() && !inChatSearchDate.value)) {
    return []
  }
  const query = inChatSearchQuery.value.toLowerCase().trim()
  const dateFilter = inChatSearchDate.value.trim()
  
  return messages.value.filter(m => {
    let matchText = true
    let matchDate = true
    
    if (query) {
      matchText = Boolean(
        (m.text && m.text.toLowerCase().includes(query)) ||
        (m.peer_name && m.peer_name.toLowerCase().includes(query))
      )
    }
    
    if (dateFilter && m.created_at) {
      const msgDateStr = new Date(m.created_at).toISOString().split('T')[0]
      matchDate = (msgDateStr === dateFilter)
    }
    
    return matchText && matchDate
  })
})

const scrollToMessageId = (msgId) => {
  highlightedMessageId.value = msgId
  nextTick(() => {
    const el = document.getElementById(`msg-${msgId}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  })
}

const prevSearchMatch = () => {
  if (inChatSearchResults.value.length === 0) return
  currentSearchMatchIndex.value = (currentSearchMatchIndex.value - 1 + inChatSearchResults.value.length) % inChatSearchResults.value.length
  const match = inChatSearchResults.value[currentSearchMatchIndex.value]
  if (match) scrollToMessageId(match.id || match.external_id)
}

const nextSearchMatch = () => {
  if (inChatSearchResults.value.length === 0) return
  currentSearchMatchIndex.value = (currentSearchMatchIndex.value + 1) % inChatSearchResults.value.length
  const match = inChatSearchResults.value[currentSearchMatchIndex.value]
  if (match) scrollToMessageId(match.id || match.external_id)
}

const toggleInChatSearch = () => {
  showInChatSearch.value = !showInChatSearch.value
  if (!showInChatSearch.value) {
    inChatSearchQuery.value = ''
    inChatSearchDate.value = ''
    highlightedMessageId.value = null
  } else {
    currentSearchMatchIndex.value = 0
  }
}

const isMessageHighlighted = (msg) => {
  if (highlightedMessageId.value && String(msg.id || msg.external_id) === String(highlightedMessageId.value)) {
    return true
  }
  if (!showInChatSearch.value) return false
  const q = inChatSearchQuery.value.toLowerCase().trim()
  const d = inChatSearchDate.value.trim()
  if (!q && !d) return false
  
  let matchText = true
  let matchDate = true
  if (q) {
    matchText = Boolean(msg.text && msg.text.toLowerCase().includes(q))
  }
  if (d && msg.created_at) {
    matchDate = (new Date(msg.created_at).toISOString().split('T')[0] === d)
  }
  return matchText && matchDate
}

// ----------------------------------------------------
// Логика глобального поиска сообщений по всем чатам
// ----------------------------------------------------
const searchGlobalMessages = async () => {
  if (!globalSearchQuery.value.trim()) return
  searchingGlobal.value = true
  try {
    const params = {
      q: globalSearchQuery.value.trim()
    }
    if (globalSearchChannel.value !== 'all') {
      params.channel = globalSearchChannel.value
    }
    const res = await axios.get('/api/v1/multichat/search-messages', {
      params,
      headers: getRequestHeaders()
    })
    globalSearchResults.value = res.data.items || []
    globalSearchTotal.value = res.data.total || 0
  } catch (err) {
    toast.error('Не удалось выполнить поиск по сообщениям')
    console.error(err)
  } finally {
    searchingGlobal.value = false
  }
}

const openDialogFromSearch = async (msg) => {
  showGlobalSearchModal.value = false
  let dialog = dialogs.value.find(d => 
    (d.channel === msg.channel || 
     (isVkChannel(d.channel) && isVkChannel(msg.channel)) ||
     (isMaxChannel(d.channel) && isMaxChannel(msg.channel))) && 
    String(d.peer_id) === String(msg.peer_id)
  )
  if (!dialog) {
    dialog = {
      channel: msg.channel,
      peer_id: msg.peer_id,
      peer_name: msg.peer_name || `Собеседник ${msg.peer_id}`,
      peer_avatar: msg.peer_avatar,
      last_message: msg.text,
      last_message_time: msg.created_at,
      unread_count: 0,
      is_pinned: false,
      tags: []
    }
    dialogs.value.unshift(dialog)
  }
  await fetchHistory(dialog, msg.id || msg.external_id)
}


const filteredDialogs = computed(() => {
  let list = [...(dialogs.value || [])]

  // Строгая изоляция скрытых диалогов:
  // Если выбран таб "Скрытые" - отображаем строго скрытые.
  // Во всех остальных вкладках ("Все", "Новые") скрытые чаты полностью исключаются из вывода!
  if (showHiddenOnly.value) {
    list = list.filter(d => d.is_hidden === true || isDialogHidden(d.channel, d.peer_id, d))
  } else {
    list = list.filter(d => d.is_hidden !== true && !isDialogHidden(d.channel, d.peer_id, d))
  }

  // 1. Фильтрация по категории источников
  if (selectedSourceCategory.value === 'personal') {
    list = list.filter(d => d.channel === 'vk_user' || d.channel === 'max_user' || d.channel === 'max' || d.channel === 'max_bridge' || d.channel === 'whatsapp' || d.channel === 'whatsapp_user' || d.channel === 'telegram_user')
  } else if (selectedSourceCategory.value === 'bots') {
    list = list.filter(d => d.channel === 'vk' || d.channel === 'max_bot' || d.channel === 'max_account' || d.channel === 'telegram_bot' || d.channel === 'telegram')
  }

  // 2. Фильтрация по конкретному выбранному источнику
  if (selectedSourceKey.value && selectedSourceKey.value !== 'all') {
    const src = availableSources.value.find(s => s.key === selectedSourceKey.value)
    if (src) {
      if (src.channel_id) {
        list = list.filter(d => d.channel === src.channel && String(d.channel_id || '') === String(src.channel_id))
      } else if (src.key === 'max_user') {
        list = list.filter(d => (d.channel === 'max_user' || d.channel === 'max' || d.channel === 'max_bridge') && d.channel !== 'max_bot' && d.channel !== 'max_account')
      } else if (src.key === 'max_bot') {
        list = list.filter(d => d.channel === 'max_bot' || d.channel === 'max_account')
      } else if (src.key === 'vk_user') {
        list = list.filter(d => d.channel === 'vk_user')
      } else if (src.key === 'vk') {
        list = list.filter(d => d.channel === 'vk')
      } else if (src.key === 'telegram_bot') {
        list = list.filter(d => d.channel === 'telegram_bot' || d.channel === 'telegram')
      } else if (src.key === 'telegram_user') {
        list = list.filter(d => d.channel === 'telegram_user')
      } else if (src.key === 'whatsapp') {
        list = list.filter(d => d.channel === 'whatsapp' || d.channel === 'whatsapp_user')
      } else if (src.channel && src.channel !== 'all') {
        list = list.filter(d => d.channel === src.channel)
      }
    }
  } else if (selectedChannel.value !== 'all') {
    if (selectedChannel.value === 'max_user') {
      list = list.filter(d => (d.channel === 'max_user' || d.channel === 'max' || d.channel === 'max_bridge') && d.channel !== 'max_bot' && d.channel !== 'max_account')
    } else if (selectedChannel.value === 'max_bot') {
      list = list.filter(d => d.channel === 'max_bot' || d.channel === 'max_account')
    } else if (selectedChannel.value === 'vk_user') {
      list = list.filter(d => d.channel === 'vk_user')
    } else if (selectedChannel.value === 'vk') {
      list = list.filter(d => d.channel === 'vk')
    } else if (selectedChannel.value === 'telegram_bot') {
      list = list.filter(d => d.channel === 'telegram_bot' || d.channel === 'telegram')
    } else {
      list = list.filter(d => d.channel === selectedChannel.value)
    }
  }

  if (unreadOnly.value) {
    list = list.filter(d => (d.unread_count || 0) > 0)
  }

  if (selectedTagId.value) {
    list = list.filter(d => d.tags && d.tags.some(t => t.id === selectedTagId.value))
  }
  
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    list = list.filter(d => 
      (d.peer_name && d.peer_name.toLowerCase().includes(query)) || 
      (d.peer_id && String(d.peer_id).toLowerCase().includes(query)) ||
      (d.phone && d.phone.toLowerCase().includes(query)) ||
      (d.last_message && d.last_message.toLowerCase().includes(query))
    )
  }
  
  // Иерархическая сортировка:
  // 1. Закрепленные чаты (is_pinned) — всегда вверху
  // 2. Чаты с непрочитанными сообщениями (unread_count > 0) — сразу под закрепами, в порядке новизны
  // 3. Все остальные прочитанные чаты — по убыванию времени последнего сообщения
  list.sort((a, b) => {
    const aPinned = a.is_pinned ? 1 : 0
    const bPinned = b.is_pinned ? 1 : 0
    if (aPinned !== bPinned) return bPinned - aPinned

    const aUnread = (a.unread_count || 0) > 0 ? 1 : 0
    const bUnread = (b.unread_count || 0) > 0 ? 1 : 0
    if (aUnread !== bUnread) return bUnread - aUnread

    const aTime = a.last_message_time || ''
    const bTime = b.last_message_time || ''
    if (aTime > bTime) return -1
    if (aTime < bTime) return 1
    return 0
  })

  return list
})

// Пагинация диалогов в сайдбаре: ограничение DOM для сверхбыстрого рендера без микрофризов
const visibleDialogsLimit = ref(60)
const displayedDialogs = computed(() => {
  return filteredDialogs.value.slice(0, visibleDialogsLimit.value)
})

watch([selectedChannel, unreadOnly, showHiddenOnly, selectedTagId, searchQuery], () => {
  visibleDialogsLimit.value = 60
})




// Универсальный поиск пользователя по номеру телефона во всех каналах и CRM
const showPhoneSearchModal = ref(false)
const phoneSearchInput = ref('')
const searchingPhone = ref(false)
const phoneSearchResult = ref(null)

const searchByPhone = async () => {
  if (!phoneSearchInput.value.trim()) return
  searchingPhone.value = true
  phoneSearchResult.value = null
  try {
    const response = await axios.get('/api/v1/multichat/search-by-phone', {
      params: { phone: phoneSearchInput.value.trim() },
      headers: getRequestHeaders()
    })
    phoneSearchResult.value = response.data
  } catch (err) {
    phoneSearchResult.value = {
      found: false,
      error: err.response?.data?.detail || 'Ошибка выполнения поиска'
    }
  } finally {
    searchingPhone.value = false
  }
}

const openChannelChat = (ch) => {
  showPhoneSearchModal.value = false
  if (!ch.peer_id) return
  
  const existing = dialogs.value.find(d => d.channel === ch.channel && String(d.peer_id) === String(ch.peer_id))
  if (existing) {
    fetchHistory(existing)
  } else {
    const newDialog = {
      channel: ch.channel,
      peer_id: String(ch.peer_id),
      peer_name: ch.peer_name || phoneSearchResult.value?.name || ch.title,
      peer_avatar: ch.avatar_url,
      phone: phoneSearchResult.value?.phone,
      last_message: '',
      last_message_time: new Date().toISOString(),
      unread_count: 0,
      is_pinned: false,
      tags: []
    }
    dialogs.value.unshift(newDialog)
    fetchHistory(newDialog)
  }
}



// Форматирование времени и дат с учетом системного часового пояса
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return utilFormatTime(timeStr)
}

const getLocalizedDateString = (timeStr) => {
  if (!timeStr) return ''
  return utilFormatDate(timeStr, { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const shouldShowDateDivider = (msg, index) => {
  if (index === 0) return true
  const prevMsg = messages.value[index - 1]
  const currDate = getLocalizedDateString(msg.created_at)
  const prevDate = getLocalizedDateString(prevMsg.created_at)
  return currDate !== prevDate
}

const formatDateDivider = (timeStr) => {
  if (!timeStr) return ''
  const dateStr = getLocalizedDateString(timeStr)
  const todayStr = getLocalizedDateString(new Date().toISOString())
  
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  const yesterdayStr = getLocalizedDateString(yesterday.toISOString())
  
  if (dateStr === todayStr) {
    return 'Сегодня'
  } else if (dateStr === yesterdayStr) {
    return 'Вчера'
  } else {
    return utilFormatDate(timeStr, { day: 'numeric', month: 'long', year: 'numeric' })
  }
}


const getChannelIcon = (channel) => {
  if (channel === 'max_bot' || channel === 'max_account') return 'bx-bot'
  if (channel === 'max_user' || channel === 'max' || channel === 'max_bridge') return 'bx-chat'
  if (channel === 'vk' || channel === 'vk_user') return 'bxl-vk'
  if (channel === 'telegram' || channel === 'telegram_bot') return 'bxl-telegram'
  if (channel === 'whatsapp') return 'bxl-whatsapp'
  return 'bx-chat'
}

const getChannelColor = (channel) => {
  if (channel === 'max_bot' || channel === 'max_account') return '#E64A19'
  if (channel === 'max_user' || channel === 'max' || channel === 'max_bridge') return '#FF5722'
  if (channel === 'vk_user') return '#0077FF'
  if (channel === 'vk') return '#4C75A3'
  if (channel === 'telegram_bot' || channel === 'telegram') return '#26A69A'
  if (channel === 'whatsapp') return '#25D366'
  return '#757575'
}

const getChannelTitle = (channel) => {
  if (channel === 'max_bot' || channel === 'max_account') return 'MAX Бот'
  if (channel === 'max_user' || channel === 'max' || channel === 'max_bridge') return 'MAX Личный'
  if (channel === 'vk_user') return 'ВКонтакте (Личный)'
  if (channel === 'vk') return 'ВКонтакте (Сообщество)'
  if (channel === 'telegram_bot' || channel === 'telegram') return 'Telegram Бот'
  if (channel === 'telegram_user') return 'Telegram (Личный)'
  if (channel === 'whatsapp') return 'WhatsApp'
  const ch = channels.find(c => c.value === channel)
  return ch ? ch.title : (channel || 'Диалог')
}


const resetFilters = () => {
  unreadOnly.value = false
  showHiddenOnly.value = false
  selectedSourceCategory.value = 'all'
  selectedSourceKey.value = 'all'
  selectedChannel.value = 'all'
  selectedTagId.value = null
  startDate.value = ''
  endDate.value = ''
  fetchDialogs()
}

let ws = null
let pingTimer = null
let backgroundSyncTimer = null

// Интеллектуальное бесшовное обновление диалогов без разрушения DOM и сброса прокрутки
const mergeDialogsList = (newDialogs) => {
  if (!Array.isArray(newDialogs)) return

  // Если список был пуст — просто присваиваем
  if (!dialogs.value || dialogs.value.length === 0) {
    dialogs.value = newDialogs
    return
  }

  const existingMap = new Map()
  dialogs.value.forEach(d => {
    existingMap.set(`${d.channel}_${d.peer_id}`, d)
  })

  let hasStructuralChange = (newDialogs.length !== dialogs.value.length)
  const updatedList = []
  
  for (let i = 0; i < newDialogs.length; i++) {
    const nd = newDialogs[i]
    const key = `${nd.channel}_${nd.peer_id}`
    const existing = existingMap.get(key)
    
    if (existing) {
      if (existing.last_message !== nd.last_message) existing.last_message = nd.last_message
      if (existing.last_message_time !== nd.last_message_time) existing.last_message_time = nd.last_message_time
      if (existing.unread_count !== nd.unread_count) existing.unread_count = nd.unread_count
      if (existing.is_pinned !== nd.is_pinned) existing.is_pinned = nd.is_pinned
      if (nd.is_hidden !== undefined) existing.is_hidden = nd.is_hidden
      if (nd.peer_name && existing.peer_name !== nd.peer_name) existing.peer_name = nd.peer_name
      if (nd.peer_avatar && existing.peer_avatar !== nd.peer_avatar) existing.peer_avatar = nd.peer_avatar
      if (nd.phone && existing.phone !== nd.phone) existing.phone = nd.phone
      existing.tags = nd.tags
      updatedList.push(existing)
      
      if (dialogs.value[i] !== existing) {
        hasStructuralChange = true
      }
    } else {
      updatedList.push(nd)
      hasStructuralChange = true
    }

    if (nd.is_hidden) {
      hiddenDialogsKeys.value.add(`${nd.channel}_${nd.peer_id}`)
      hiddenDialogsKeys.value.add(`${nd.channel}:${nd.peer_id}`)
    }
  }

  if (hasStructuralChange) {
    dialogs.value = updatedList
  }
}

const silentSync = async () => {
  if (typeof document !== 'undefined' && document.hidden) {
    return // Экономим память и процессор когда вкладка браузера не активна
  }

  const wsActive = ws && ws.readyState === WebSocket.OPEN

  try {
    const params = {}
    if (selectedChannel.value !== 'all') params.channel = selectedChannel.value
    if (selectedTagId.value) params.tag_id = selectedTagId.value
    if (showHiddenOnly.value) params.hidden_only = true
    if (unreadOnly.value) params.unread_only = true
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const res = await axios.get('/api/v1/multichat/dialogs', { 
      params,
      headers: getRequestHeaders()
    })
    mergeDialogsList(res.data)

    // Если открыт конкретный чат и сокет отключен — подтягиваем свежую историю
    if (activeDialog.value && !wsActive) {
      const histRes = await axios.get(`/api/v1/multichat/dialogs/${activeDialog.value.channel}/${activeDialog.value.peer_id}/history`, {
        params: { limit: 10 },
        headers: getRequestHeaders()
      })
      if (histRes.data && histRes.data.length > 0) {
        const lastLocalId = messages.value.length > 0 ? (messages.value[messages.value.length - 1].id || 0) : 0
        const newMsgs = histRes.data.filter(m => m.id && m.id > lastLocalId)
        if (newMsgs.length > 0) {
          const hasNewInbound = newMsgs.some(m => m.direction === 'inbound')
          if (hasNewInbound) {
            const isHiddenActive = activeDialog.value?.is_hidden || isDialogHidden(activeDialog.value?.channel, activeDialog.value?.peer_id, activeDialog.value)
            if (!isHiddenActive) {
              playNotificationSound(null, activeDialog.value)
            }
          }
          messages.value = [...messages.value, ...newMsgs]
          scrollToBottom()
          markAsRead(activeDialog.value)
        }
      }
    }
  } catch (e) {
    // Игнорируем сетевые ошибки фоновой сверки
  }
}


const initWebSocket = () => {
  const token = localStorage.getItem('access_token') || ''
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/v1/chat/ws?token=${encodeURIComponent(token)}`
  
  try {
    if (ws) {
      ws.close()
    }
  } catch (e) {}

  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('Multichat WS Connected (Real-time active)')
    if (pingTimer) clearInterval(pingTimer)
    pingTimer = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'ping' }))
      }
    }, 15000)
  }
  
  ws.onmessage = async (event) => {
    try {
      const payload = JSON.parse(event.data)
      if (payload.type === 'multichat_message') {
        const msg = payload.data
        if (!msg) return

        // Сохраняем сообщение в централизованный реактивный кэш (доступ за 0 мс)
        chatStore.appendMessageToCache(msg.channel, msg.peer_id, msg)
        
        // Определяем, скрыт ли диалог
        const isHiddenMsg = msg.is_hidden === true || isDialogHidden(msg.channel, msg.peer_id, msg)

        // Воспроизводим звук входящего сообщения ТОЛЬКО если диалог НЕ скрыт
        if (msg.direction === 'inbound' && !isHiddenMsg) {
          playNotificationSound(null, msg)
        }

        // Проверяем, открыт ли сейчас этот диалог
        const isCurrentOpenChat = activeDialog.value && 
          (activeDialog.value.channel === msg.channel || 
           (isVkChannel(activeDialog.value.channel) && isVkChannel(msg.channel)) ||
           (isMaxChannel(activeDialog.value.channel) && isMaxChannel(msg.channel))) && 
          String(activeDialog.value.peer_id) === String(msg.peer_id)

        // Всплывающее уведомление (Desktop / Popup) ТОЛЬКО если не текущий открытый чат и диалог НЕ скрыт
        if (msg.direction === 'inbound' && !isCurrentOpenChat && !isHiddenMsg) {
          triggerPopupNotification(msg)
        }

        if (isCurrentOpenChat) {
          // Проверяем, нет ли уже такого сообщения в ленте
          const exists = messages.value.some(m => 
            (m.id && msg.id && m.id === msg.id) || 
            (m.external_id && msg.external_id && m.external_id === msg.external_id)
          )
          if (!exists) {
            messages.value.push(msg)
            await scrollToBottom()
          }
          
          if (msg.direction === 'inbound') {
            await markAsRead(activeDialog.value)
          }
        }
        
        // Находим диалог в списке
        const dialogIndex = dialogs.value.findIndex(d => 
          (d.channel === msg.channel || 
           (isVkChannel(d.channel) && isVkChannel(msg.channel)) ||
           (isMaxChannel(d.channel) && isMaxChannel(msg.channel))) && 
          String(d.peer_id) === String(msg.peer_id)
        )
        
        if (dialogIndex !== -1) {
          // Если пришло сообщение скрытого диалога, но открыт общий список ("Все" / "Новые"):
          // Немедленно удаляем его из dialogs.value, чтобы он не всплывал наверх!
          if (isHiddenMsg && !showHiddenOnly.value) {
            dialogs.value.splice(dialogIndex, 1)
            return
          }
          // Если пришло сообщение обычного диалога, а мы находимся во вкладке "Скрытые":
          if (!isHiddenMsg && showHiddenOnly.value) {
            dialogs.value.splice(dialogIndex, 1)
            return
          }

          const dialog = dialogs.value[dialogIndex]
          dialog.last_message = msg.text
          dialog.last_message_time = msg.created_at || new Date().toISOString()
          if (msg.is_hidden !== undefined) {
            dialog.is_hidden = msg.is_hidden
          }
          if (msg.peer_name && !msg.peer_name.startsWith('Пользователь ') && !msg.peer_name.startsWith('VK ')) {
            dialog.peer_name = msg.peer_name
          }
          if (msg.peer_avatar) dialog.peer_avatar = msg.peer_avatar
          if (msg.phone) dialog.phone = msg.phone
          
          if (msg.direction === 'inbound' && !isCurrentOpenChat) {
            // Для скрытых диалогов не увеличиваем unread_count в общем списке ("Все" / "Новые")
            if (!isHiddenMsg || showHiddenOnly.value) {
              dialog.unread_count = (dialog.unread_count || 0) + 1
            }
          }
        } else {
          // Диалог отсутствует в текущем списке
          // Для скрытых диалогов: если мы не во вкладке "Скрытые", НЕ добавляем его в общий список!
          if (isHiddenMsg && !showHiddenOnly.value) {
            return
          }
          // Для обычных диалогов: если мы во вкладке "Скрытые", НЕ добавляем в скрытые
          if (!isHiddenMsg && showHiddenOnly.value) {
            return
          }

          dialogs.value.unshift({
            channel: msg.channel,
            peer_id: msg.peer_id,
            peer_name: msg.peer_name || `Собеседник ${msg.peer_id}`,
            peer_avatar: msg.peer_avatar,
            phone: msg.phone || null,
            last_message: msg.text,
            last_message_time: msg.created_at || new Date().toISOString(),
            unread_count: (msg.direction === 'inbound' && !isCurrentOpenChat) ? 1 : 0,
            is_pinned: false,
            is_hidden: isHiddenMsg,
            tags: []
          })
        }
      }
    } catch (e) {
      console.error('Error handling WebSocket message:', e)
    }
  }
  
  ws.onclose = () => {
    if (pingTimer) clearInterval(pingTimer)
    setTimeout(initWebSocket, 3000)
  }

  ws.onerror = () => {
    if (ws) ws.close()
  }
}


const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible') {
    silentSync()
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      initWebSocket()
    }
  }
}

onMounted(() => {
  // 0. Мгновенная синхронная загрузка ключей скрытых чатов из кэша браузера
  try {
    const cachedKeys = localStorage.getItem('multichat_hidden_keys')
    if (cachedKeys) {
      const arr = JSON.parse(cachedKeys)
      if (Array.isArray(arr)) {
        hiddenDialogsKeys.value = new Set(arr)
      }
    }
  } catch (e) {}

  // 1. Моментальное восстановление списка диалогов из локального кэша за 0 мс С ИСКЛЮЧЕНИЕМ СКРЫТЫХ
  try {
    const cached = localStorage.getItem('multichat_cached_dialogs')
    if (cached) {
      const parsed = JSON.parse(cached)
      if (Array.isArray(parsed) && parsed.length > 0) {
        dialogs.value = parsed.filter(d => d.is_hidden !== true && !isDialogHidden(d.channel, d.peer_id, d))
        // Сразу перезаписываем кэш в очищенном виде
        localStorage.setItem('multichat_cached_dialogs', JSON.stringify(dialogs.value))
      }
    }
  } catch (e) {}

  fetchHiddenKeys()
  fetchTags()
  fetchAccounts()
  fetchVkBots()
  fetchDialogs(dialogs.value.length > 0)
  initWebSocket()
  
  // Автоматическая тихая сверка раз в 25 секунд (WebSocket доставляет все сообщения мгновенно)
  backgroundSyncTimer = setInterval(silentSync, 25000)
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  if (ws) ws.close()
  if (pingTimer) clearInterval(pingTimer)
  if (backgroundSyncTimer) clearInterval(backgroundSyncTimer)
  if (qrPollingInterval.value) clearInterval(qrPollingInterval.value)
  if (waPollingInterval.value) clearInterval(waPollingInterval.value)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})


watch([selectedSourceKey, selectedChannel, selectedTagId, unreadOnly, showHiddenOnly, startDate, endDate], () => {
  fetchDialogs()
})

watch([newAccountType, vkAuthTab], ([newType, newVkTab]) => {
  if (newType === 'vk_user' && newVkTab === 'qr' && !vkQrBase64.value) {
    initVkQr()
  }
})
</script>


<template>
  <VCard :class="['multichat-container d-flex flex-row fill-height', isDark ? 'multichat-dark' : 'multichat-light']" style="height: calc(100vh - 120px) !important;">
    <!-- Левая панель: Список диалогов и фильтры -->
    <div :class="['dialogs-sidebar d-flex flex-column border-end', isMobile && activeDialog ? 'mobile-hidden' : '']" style="width: 390px; min-width: 350px;">
      <!-- Строка поиска и кнопки управления -->
      <div class="pa-3 border-bottom d-flex align-center gap-2">
        <VTextField
          v-model="searchQuery"
          placeholder="Поиск собеседника..."
          variant="outlined"
          density="comfortable"
          hide-details
          prepend-inner-icon="bx-search"
          clearable
          class="flex-grow-1"
        />
        <VBtn
          :color="showFilters ? 'primary' : 'default'"
          variant="tonal"
          density="comfortable"
          icon
          @click="showFilters = !showFilters"
        >
          <VIcon icon="bx-slider-alt" />
          <VTooltip activator="parent" location="top">Фильтры</VTooltip>
        </VBtn>

        <VBtn
          v-if="hasPermission('multichat_accounts_manage')"
          color="primary"
          variant="tonal"
          density="comfortable"
          icon
          @click="showAccountsModal = true"
        >
          <VIcon icon="bx-user-plus" />
          <VTooltip activator="parent" location="top">Личные аккаунты (QR / Токены)</VTooltip>
        </VBtn>

        <!-- Кнопка глобального поиска сообщений по всем чатам архива -->
        <VBtn
          color="info"
          variant="tonal"
          density="comfortable"
          icon
          @click="showGlobalSearchModal = true"
        >
          <VIcon icon="bx-search-alt-2" />
          <VTooltip activator="parent" location="top">Глобальный поиск по сообщениям во всех чатах</VTooltip>
        </VBtn>

        <!-- Кнопка универсального поиска собеседника по номеру телефона по всем каналам -->
        <VBtn
          color="secondary"
          variant="tonal"
          density="comfortable"
          icon
          @click="showPhoneSearchModal = true"
        >
          <VIcon icon="bx-phone-call" />
          <VTooltip activator="parent" location="top">Найти собеседника по номеру телефона (все каналы)</VTooltip>
        </VBtn>
      </div>



      <!-- Быстрые фильтры статуса диалогов: Все / Непрочитанные / Скрытые + Звуки -->
      <div class="dialogs-toolbar px-3 py-2 border-bottom d-flex align-center gap-1">
        <VBtn
          :color="!unreadOnly && !showHiddenOnly ? 'primary' : 'default'"
          :variant="!unreadOnly && !showHiddenOnly ? 'flat' : 'outlined'"
          size="small"
          class="flex-grow-1 font-weight-medium px-2"
          @click="setFilterMode('all')"
        >
          <VIcon icon="bx-chat" class="mr-1" size="16" />
          Все
        </VBtn>

        <VBtn
          :color="unreadOnly ? 'error' : 'default'"
          :variant="unreadOnly ? 'flat' : 'outlined'"
          size="small"
          class="flex-grow-1 font-weight-medium px-2"
          @click="setFilterMode('unread')"
        >
          <VIcon icon="bx-envelope" class="mr-1" size="16" />
          Новые
          <VBadge
            v-if="totalUnreadCount > 0"
            :content="totalUnreadCount"
            color="error"
            inline
            class="ml-1"
          />
        </VBtn>

        <VBtn
          :color="showHiddenOnly ? 'warning' : 'default'"
          :variant="showHiddenOnly ? 'flat' : 'outlined'"
          size="small"
          class="flex-grow-1 font-weight-medium px-2"
          @click="setFilterMode('hidden')"
        >
          <VIcon icon="bx-hide" class="mr-1" size="16" />
          Скрытые
        </VBtn>

        <!-- Кнопка «Прочитать все чаты» -->
        <VBtn
          variant="tonal"
          icon
          size="small"
          color="success"
          :loading="markingAllAsRead"
          :disabled="totalUnreadCount === 0 && totalUnreadMessages === 0"
          @click="markAllAsRead"
        >
          <VIcon icon="bx-check-double" />
          <VTooltip activator="parent" location="top">Прочитать все чаты</VTooltip>
        </VBtn>

        <!-- Кнопка библиотеки звуковых уведомлений -->
        <VBtn
          variant="tonal"
          icon
          size="small"
          :color="globalSound === 'mute' ? 'grey' : 'primary'"
          @click="showSoundModal = true"
        >
          <VIcon :icon="globalSound === 'mute' ? 'bx-volume-mute' : 'bx-volume-full'" />
          <VTooltip activator="parent" location="top">Библиотека звуков уведомлений</VTooltip>
        </VBtn>
      </div>

      <!-- Дополнительная панель расширенной фильтрации -->
      <VExpandTransition>
        <div v-show="showFilters" class="pa-3 bg-grey-lighten-4 border-bottom">
          <div class="d-flex flex-column gap-3">
            <VSelect
              v-model="selectedSourceKey"
              :items="availableSources"
              item-title="title"
              item-value="key"
              label="Источник (Бот / Аккаунт / Мессенджер)"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              @update:model-value="(val) => selectSource(val || 'all')"
            >
              <template #item="{ props, item }">
                <VListItem v-bind="props" :title="item.raw.title">
                  <template #prepend>
                    <VIcon :icon="item.raw.icon || 'bx-chat'" :color="item.raw.color" size="18" class="mr-2" />
                  </template>
                  <template #append>
                    <VChip v-if="item.raw.type === 'personal'" size="x-small" color="indigo" variant="tonal">Личный</VChip>
                    <VChip v-else-if="item.raw.type === 'bot'" size="x-small" color="deep-purple" variant="tonal">Бот</VChip>
                  </template>
                </VListItem>
              </template>
            </VSelect>

            <div class="d-flex align-center gap-2">
              <VSelect
                v-model="selectedTagId"
                :items="allTags"
                item-title="name"
                item-value="id"
                label="Фильтр по метке"
                placeholder="Все метки"
                variant="outlined"
                density="compact"
                hide-details
                clearable
                class="flex-grow-1"
              />
              <VBtn 
                icon
                variant="text" 
                density="comfortable" 
                color="primary"
                @click="showTagManager = true"
              >
                <VIcon icon="bx-cog" />
                <VTooltip activator="parent" location="top">Управление метками</VTooltip>
              </VBtn>
            </div>

            <div class="d-flex align-center gap-2">
              <VTextField
                v-model="startDate"
                type="date"
                label="С даты"
                variant="outlined"
                density="compact"
                hide-details
              />
              <VTextField
                v-model="endDate"
                type="date"
                label="По дату"
                variant="outlined"
                density="compact"
                hide-details
              />
            </div>

            <VBtn 
              color="secondary" 
              variant="outlined" 
              size="small" 
              block 
              @click="resetFilters"
            >
              <VIcon icon="bx-refresh" class="mr-1" />
              Сбросить фильтры
            </VBtn>
          </div>
        </div>
      </VExpandTransition>

      <!-- Панель источников: Сегменты категорий + Горизонтальная лента чипсов -->
      <div class="sources-panel px-3 py-2 border-bottom bg-grey-lighten-5">
        <!-- Быстрый выбор категории источников -->
        <div class="d-flex align-center justify-space-between mb-1 gap-1">
          <VBtn
            size="x-small"
            :variant="selectedSourceCategory === 'all' ? 'flat' : 'text'"
            :color="selectedSourceCategory === 'all' ? 'primary' : 'default'"
            class="text-caption font-weight-medium flex-grow-1 px-1 rounded"
            @click="selectSourceCategory('all')"
          >
            Все ({{ availableSources.length - 1 }})
          </VBtn>
          <VBtn
            size="x-small"
            :variant="selectedSourceCategory === 'personal' ? 'flat' : 'text'"
            :color="selectedSourceCategory === 'personal' ? 'indigo' : 'default'"
            class="text-caption font-weight-medium flex-grow-1 px-1 rounded"
            @click="selectSourceCategory('personal')"
          >
            <VIcon icon="bx-user" size="13" class="mr-1" />
            Личные
            <VBadge
              v-if="personalUnreadCount > 0"
              :content="personalUnreadCount"
              color="error"
              inline
              class="ml-1"
            />
          </VBtn>
          <VBtn
            size="x-small"
            :variant="selectedSourceCategory === 'bots' ? 'flat' : 'text'"
            :color="selectedSourceCategory === 'bots' ? 'deep-purple' : 'default'"
            class="text-caption font-weight-medium flex-grow-1 px-1 rounded"
            @click="selectSourceCategory('bots')"
          >
            <VIcon icon="bx-bot" size="13" class="mr-1" />
            Боты / Группы
            <VBadge
              v-if="botsUnreadCount > 0"
              :content="botsUnreadCount"
              color="error"
              inline
              class="ml-1"
            />
          </VBtn>
        </div>

        <!-- Горизонтальная прокручиваемая лента чипсов конкретных источников -->
        <div class="sources-chips-scroll d-flex align-center gap-1 overflow-x-auto py-1">
          <VChip
            v-for="src in displayedSources"
            :key="src.key"
            size="small"
            :color="selectedSourceKey === src.key ? (src.color || 'primary') : 'default'"
            :variant="selectedSourceKey === src.key ? 'flat' : 'outlined'"
            class="source-chip cursor-pointer text-caption font-weight-medium"
            @click="selectSource(src.key)"
          >
            <!-- Фирменная иконка MAX -->
            <svg v-if="src.isMax && !src.isBot" viewBox="0 0 24 24" width="14" height="14" fill="none" class="mr-1">
              <path d="M12 2C6.48 2 2 6.25 2 11.5c0 2.92 1.41 5.53 3.61 7.21l-.92 3.32a.75.75 0 0 0 1.01.89l3.86-1.78c.78.23 1.6.36 2.44.36 5.52 0 10-4.25 10-9.5S17.52 2 12 2z" fill="#FF5722"/>
              <path d="M7 14.5V9.5a1 1 0 0 1 1.7-.7l3.3 3.3 3.3-3.3a1 1 0 0 1 1.7.7v5a1 1 0 1 1-2 0v-2.3l-2.3 2.3a1 1 0 0 1-1.4 0L8.7 12.2v2.3a1 1 0 0 1-1.7 0z" fill="#FFFFFF"/>
            </svg>
            <VIcon v-else :icon="src.icon || 'bx-chat'" size="15" class="mr-1" />
            
            <span>{{ src.shortTitle || src.title }}</span>

            <!-- Индивидуальный счетчик непрочитанных сообщений в источнике -->
            <span
              v-if="getSourceUnreadCount(src) > 0"
              class="source-unread-badge ml-1"
            >
              {{ getSourceUnreadCount(src) }}
            </span>

            <VTooltip activator="parent" location="top">
              {{ src.title }} ({{ src.type === 'personal' ? 'Личный аккаунт' : src.type === 'bot' ? 'Бот / Сообщество' : 'Все источники' }})
            </VTooltip>
          </VChip>
        </div>
      </div>

      <!-- Список диалогов (закрепленные выводятся компактно вверху) -->
      <VList class="overflow-y-auto flex-grow-1 py-0 dialogs-list" density="comfortable">
        <VListItem v-if="loadingDialogs" class="text-center py-5">
          <VProgressCircular indeterminate color="primary" />
        </VListItem>
        
        <VListItem v-else-if="filteredDialogs.length === 0" class="text-center text-grey py-8">
          Диалоги не найдены
        </VListItem>

        <template v-else>
          <VListItem
            v-for="dialog in displayedDialogs"
            :key="dialog.channel + '_' + dialog.peer_id"
            :active="activeDialog && activeDialog.channel === dialog.channel && activeDialog.peer_id === dialog.peer_id"
            color="primary"
            :class="[
              'dialog-item border-bottom px-3',
              dialog.is_pinned ? 'pinned-item py-1' : 'py-2',
              dialog.unread_count > 0 ? 'dialog-unread' : ''
            ]"
            @click="fetchHistory(dialog)"
          >
            <template #prepend>
              <div class="position-relative mr-3">
                <!-- Для закрепленных диалогов уменьшенный аватар 36px для компактности -->
                <VAvatar :size="dialog.is_pinned ? 36 : 48" class="border bg-grey-lighten-3">
                  <VImg v-if="dialog.peer_avatar" :src="dialog.peer_avatar" referrerpolicy="no-referrer" />
                  <VIcon v-else icon="bx-user" color="grey" />
                </VAvatar>

                <!-- Пульсирующая точка непрочитанного диалога -->
                <div v-if="dialog.unread_count > 0" class="unread-avatar-dot"></div>

                <!-- Фирменная оверлей-иконка мессенджера в правом нижнем углу аватарки -->
                <div 
                  class="channel-badge-avatar"
                  :style="{ backgroundColor: getChannelColor(dialog.channel) }"
                >
                  <svg v-if="isMaxChannel(dialog.channel)" viewBox="0 0 24 24" width="10" height="10" fill="none">
                    <path d="M12 2C6.48 2 2 6.25 2 11.5c0 2.92 1.41 5.53 3.61 7.21l-.92 3.32a.75.75 0 0 0 1.01.89l3.86-1.78c.78.23 1.6.36 2.44.36 5.52 0 10-4.25 10-9.5S17.52 2 12 2z" fill="white"/>
                    <path d="M7 14.5V9.5a1 1 0 0 1 1.7-.7l3.3 3.3 3.3-3.3a1 1 0 0 1 1.7.7v5a1 1 0 1 1-2 0v-2.3l-2.3 2.3a1 1 0 0 1-1.4 0L8.7 12.2v2.3a1 1 0 0 1-1.7 0z" fill="#FF5722"/>
                  </svg>
                  <VIcon v-else :icon="getChannelIcon(dialog.channel)" size="11" color="white" />
                </div>
              </div>
            </template>

            <VListItemTitle class="font-weight-medium d-flex align-center justify-between">
              <div class="text-truncate mr-2 d-flex align-center gap-1">
                <VIcon v-if="dialog.is_pinned" icon="bxs-pin" size="14" color="warning" class="mr-1 shrink-0" />
                <span class="text-truncate" :class="{ 'font-weight-bold': dialog.is_pinned || dialog.unread_count > 0 }">
                  {{ dialog.peer_name }}
                </span>

                <!-- Яркий бейдж счетчика непрочитанных сообщений -->
                <VChip
                  v-if="dialog.unread_count > 0"
                  size="x-small"
                  color="error"
                  variant="flat"
                  class="font-weight-bold px-1 text-white shrink-0 elevation-1 ml-1"
                  style="height: 18px; font-size: 10px; line-height: 1; letter-spacing: 0.5px;"
                >
                  +{{ dialog.unread_count }}
                </VChip>

                <!-- Отметка бота / канала -->
                <VChip
                  v-if="dialog.channel === 'max_bot' || dialog.channel === 'max_account'"
                  size="x-small"
                  color="deep-orange-darken-3"
                  variant="flat"
                  class="font-weight-bold px-1 text-uppercase text-white shrink-0"
                  style="height: 16px; font-size: 8px; line-height: 1; letter-spacing: 0.5px;"
                >
                  <VIcon icon="bx-bot" size="10" class="mr-0.5" />
                  БОТ MAX
                </VChip>
                <VChip
                  v-else-if="isMaxChannel(dialog.channel)"
                  size="x-small"
                  color="deep-orange"
                  variant="tonal"
                  class="font-weight-bold px-1 text-uppercase shrink-0"
                  style="height: 16px; font-size: 8px; line-height: 1; letter-spacing: 0.5px;"
                >
                  MAX
                </VChip>
                <VChip
                  v-else-if="dialog.channel === 'vk'"
                  size="x-small"
                  color="indigo"
                  variant="tonal"
                  class="font-weight-bold px-1 text-uppercase shrink-0"
                  style="height: 16px; font-size: 8px; line-height: 1;"
                >
                  VK ГРУППА
                </VChip>
              </div>
              <span :class="['text-caption ml-auto shrink-0', dialog.unread_count > 0 ? 'text-error font-weight-bold' : 'text-grey']" style="font-size: 10px;">
                {{ formatTime(dialog.last_message_time) }}
              </span>
            </VListItemTitle>

            <!-- Номер телефона клиента (если доступен) -->
            <div v-if="dialog.phone" class="text-caption text-primary font-weight-medium d-flex align-center gap-1" style="font-size: 11px;">
              <VIcon icon="bx-phone" size="12" />
              <span>{{ dialog.phone }}</span>
            </div>

            <!-- Фрагмент последнего сообщения (для всех диалогов включая закрепленные) -->
            <VListItemSubtitle 
              class="text-truncate text-caption mt-1 pr-6" 
              :class="{ 'font-weight-bold text-grey-darken-4': dialog.unread_count > 0, 'text-grey': dialog.unread_count === 0 }"
              :style="{ opacity: dialog.unread_count > 0 ? 1 : 0.8 }"
            >
              {{ dialog.last_message || '[Нет сообщений]' }}
            </VListItemSubtitle>





            <!-- Назначенные метки диалога -->
            <div v-if="dialog.tags && dialog.tags.length > 0" class="d-flex flex-wrap gap-1 mt-1 pr-6">
              <VChip
                v-for="tag in dialog.tags"
                :key="tag.id"
                size="x-small"
                :color="tag.color"
                variant="flat"
                class="text-white px-1 text-uppercase font-weight-bold"
                style="height: 16px; font-size: 8px; line-height: 1;"
              >
                {{ tag.name }}
              </VChip>
            </div>

            <template #append>
              <div class="d-flex flex-column align-end gap-1">
                <div class="d-flex align-center gap-1">
                  <!-- Кнопка Закрепить / Открепить -->
                  <VBtn
                    icon
                    variant="text"
                    size="x-small"
                    :color="dialog.is_pinned ? 'warning' : 'grey-darken-1'"
                    :title="dialog.is_pinned ? 'Открепить' : 'Закрепить вверху'"
                    @click.stop="togglePin(dialog)"
                  >
                    <VIcon :icon="dialog.is_pinned ? 'bxs-pin' : 'bx-pin'" size="16" />
                  </VBtn>

                  <!-- Кнопка Скрыть / Вернуть из скрытых -->
                  <VBtn
                    icon
                    variant="text"
                    size="x-small"
                    :color="dialog.is_hidden ? 'warning' : 'grey-darken-1'"
                    :title="dialog.is_hidden ? 'Вернуть в общий список' : 'Скрыть из общего списка'"
                    @click.stop="toggleHide(dialog)"
                  >
                    <VIcon :icon="dialog.is_hidden ? 'bx-show' : 'bx-hide'" size="16" />
                  </VBtn>

                  <!-- Кнопка быстрой привязки метки прямо из списка (единое меню) -->
                  <VBtn
                    icon
                    variant="text"
                    size="x-small"
                    color="grey-darken-1"
                    title="Присвоить метку"
                    @click.stop="openTagMenu(dialog, $event)"
                  >
                    <VIcon icon="bx-purchase-tag" size="16" />
                  </VBtn>

                  <VIcon 
                    :icon="getChannelIcon(dialog.channel)" 
                    :color="getChannelColor(dialog.channel)" 
                    size="16" 
                  />
                </div>
                
                <!-- Выразительный счетчик новых сообщений справа -->
                <VChip
                  v-if="dialog.unread_count > 0"
                  size="x-small"
                  color="error"
                  variant="flat"
                  class="font-weight-bold px-2 text-white elevation-2"
                  style="height: 20px; font-size: 11px; line-height: 1; letter-spacing: 0.5px;"
                >
                  +{{ dialog.unread_count }}
                </VChip>
              </div>
            </template>

          </VListItem>

          <!-- Кнопка подгрузки следующих диалогов -->
          <div v-if="filteredDialogs.length > visibleDialogsLimit" class="pa-3 text-center border-top">
            <VBtn
              variant="tonal"
              size="small"
              block
              color="primary"
              class="text-caption font-weight-medium rounded-lg"
              @click="visibleDialogsLimit += 60"
            >
              <VIcon icon="bx-chevron-down" class="mr-1" />
              Показать еще диалоги ({{ visibleDialogsLimit }} из {{ filteredDialogs.length }})
            </VBtn>
          </div>
        </template>
      </VList>
    </div>

    <!-- Правая панель: Окно переписки -->
    <div :class="['chat-area d-flex flex-column flex-grow-1', isMobile && !activeDialog ? 'mobile-hidden' : '']">
      <div v-if="!activeDialog" class="d-flex flex-column align-center justify-center fill-height text-grey">
        <VIcon icon="bx-message-square-detail" size="64" class="mb-3 text-grey-lighten-1" />
        <p class="text-body-1">Выберите диалог для начала общения</p>
      </div>

      <template v-else>
        <!-- Шапка чата -->
        <div class="chat-header border-bottom pa-3 d-flex align-center justify-space-between flex-wrap gap-2">

          <div class="d-flex align-center">
            <!-- Кнопка Назад к диалогам для мобильных -->
            <VBtn
              v-if="isMobile"
              icon
              variant="text"
              size="small"
              class="mr-2"
              @click="activeDialog = null"
            >
              <VIcon icon="bx-arrow-back" size="22" />
            </VBtn>
            <VAvatar size="40" class="mr-3 bg-grey-lighten-3">
              <VImg v-if="activeDialog.peer_avatar" :src="activeDialog.peer_avatar" referrerpolicy="no-referrer" />
              <VIcon v-else icon="bx-user" color="grey" />
            </VAvatar>
            <div>
              <div class="font-weight-medium text-subtitle-1 d-flex align-center flex-wrap gap-2">
                <VIcon v-if="activeDialog.is_pinned" icon="bxs-pin" size="16" color="warning" class="mr-1" />
                <span>{{ activeDialog.peer_name }}</span>

                <!-- Отметка канала и бота в шапке чата -->
                <VChip
                  v-if="activeDialog.channel === 'max_bot' || activeDialog.channel === 'max_account'"
                  size="small"
                  color="deep-orange-darken-3"
                  variant="flat"
                  class="text-white font-weight-bold"
                >
                  <VIcon icon="bx-bot" size="14" class="mr-1" />
                  MAX Бот
                </VChip>
                <VChip
                  v-else-if="isMaxChannel(activeDialog.channel)"
                  size="small"
                  color="deep-orange"
                  variant="tonal"
                  class="font-weight-bold d-flex align-center"
                >
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" class="mr-1">
                    <path d="M12 2C6.48 2 2 6.25 2 11.5c0 2.92 1.41 5.53 3.61 7.21l-.92 3.32a.75.75 0 0 0 1.01.89l3.86-1.78c.78.23 1.6.36 2.44.36 5.52 0 10-4.25 10-9.5S17.52 2 12 2z" fill="#FF5722"/>
                    <path d="M7 14.5V9.5a1 1 0 0 1 1.7-.7l3.3 3.3 3.3-3.3a1 1 0 0 1 1.7.7v5a1 1 0 1 1-2 0v-2.3l-2.3 2.3a1 1 0 0 1-1.4 0L8.7 12.2v2.3a1 1 0 0 1-1.7 0z" fill="#FFFFFF"/>
                  </svg>
                  MAX Личный
                </VChip>
                <VChip
                  v-else-if="activeDialog.channel === 'vk_user'"
                  size="small"
                  color="info"
                  variant="tonal"
                  class="font-weight-bold"
                >
                  <VIcon icon="bxl-vk" size="14" class="mr-1" />
                  VK Личный
                </VChip>
                <VChip
                  v-else-if="activeDialog.channel === 'vk'"
                  size="small"
                  color="primary"
                  variant="tonal"
                  class="font-weight-bold"
                >
                  <VIcon icon="bxl-vk" size="14" class="mr-1" />
                  VK Сообщество
                </VChip>

                <VChip
                  v-if="activeDialog.phone"
                  size="small"
                  color="primary"
                  variant="tonal"
                  class="font-weight-medium"
                >
                  <VIcon icon="bx-phone" size="12" class="mr-1" />
                  {{ activeDialog.phone }}
                </VChip>

                <VChip
                  v-if="activeDialog.is_hidden"
                  size="small"
                  color="warning"
                  variant="tonal"
                  class="font-weight-medium"
                >
                  <VIcon icon="bx-hide" size="12" class="mr-1" />
                  Скрытый чат
                </VChip>
              </div>
              <div class="text-caption text-grey d-flex align-center">
                <VIcon :icon="getChannelIcon(activeDialog.channel)" :color="getChannelColor(activeDialog.channel)" size="14" class="mr-1" />
                {{ getChannelTitle(activeDialog.channel) }} (ID: {{ activeDialog.peer_id }})
              </div>
            </div>


          </div>

          <!-- Кнопки управления шапки чата: Поиск в чате, Закреп, Скрыть, Звук чата, Всплывающие окна, Метки -->
          <div class="d-flex align-center gap-2">
            <!-- Поиск внутри текущего чата -->
            <VBtn
              :color="showInChatSearch ? 'primary' : 'default'"
              :variant="showInChatSearch ? 'flat' : 'outlined'"
              size="small"
              @click="toggleInChatSearch"
            >
              <VIcon icon="bx-search" class="mr-1" />
              Поиск в чате
            </VBtn>

            <!-- Закрепление -->
            <VBtn
              :color="activeDialog.is_pinned ? 'warning' : 'default'"
              variant="outlined"
              size="small"
              @click="togglePin(activeDialog)"
            >
              <VIcon :icon="activeDialog.is_pinned ? 'bxs-pin' : 'bx-pin'" class="mr-1" />
              {{ activeDialog.is_pinned ? 'Открепить' : 'Закрепить' }}
            </VBtn>

            <!-- Скрыть чат / Вернуть из скрытых -->
            <VBtn
              :color="activeDialog.is_hidden ? 'warning' : 'default'"
              variant="outlined"
              size="small"
              @click="toggleHide(activeDialog)"
            >
              <VIcon :icon="activeDialog.is_hidden ? 'bx-show' : 'bx-hide'" class="mr-1" />
              {{ activeDialog.is_hidden ? 'Вернуть в список' : 'Скрыть чат' }}
            </VBtn>

            <!-- Персональный звук этого чата -->
            <VMenu location="bottom end">
              <template #activator="{ props: soundProps }">
                <VBtn
                  variant="outlined"
                  size="small"
                  :color="activeDialogSound === 'mute' ? 'grey' : (activeDialogSound === 'default' ? 'default' : 'primary')"
                  v-bind="soundProps"
                >
                  <VIcon :icon="activeDialogSound === 'mute' ? 'bx-volume-mute' : 'bx-volume-full'" class="mr-1" />
                  Звук чата
                </VBtn>
              </template>
              <VCard min-width="260" class="pa-2">
                <div class="text-subtitle-2 pa-2 border-bottom font-weight-bold">Звук уведомлений для этого чата</div>
                <VList density="compact" class="py-1">
                  <VListItem
                    :active="activeDialogSound === 'default'"
                    @click="setDialogSound(activeDialog, 'default')"
                  >
                    <template #prepend>
                      <VIcon icon="bx-cog" size="18" class="mr-2" />
                    </template>
                    <VListItemTitle>По умолчанию (Глобальный)</VListItemTitle>
                  </VListItem>

                  <VDivider class="my-1" />

                  <VListItem
                    v-for="s in soundLibrary"
                    :key="s.id"
                    :active="activeDialogSound === s.id"
                    @click="setDialogSound(activeDialog, s.id)"
                  >
                    <template #prepend>
                      <VIcon :icon="s.icon" size="18" class="mr-2" />
                    </template>
                    <VListItemTitle>{{ s.name }}</VListItemTitle>
                    <template #append>
                      <VBtn 
                        v-if="s.id !== 'mute'" 
                        icon 
                        variant="text" 
                        size="x-small" 
                        @click.stop="playNotificationSound(s.id)"
                      >
                        <VIcon icon="bx-play" size="16" />
                      </VBtn>
                    </template>
                  </VListItem>
                </VList>
              </VCard>
            </VMenu>

            <!-- Всплывающие уведомления для этого чата -->
            <VMenu location="bottom end">
              <template #activator="{ props: popupProps }">
                <VBtn
                  variant="outlined"
                  size="small"
                  :color="activeDialogPopup === 'always' ? 'success' : (activeDialogPopup === 'never' ? 'grey' : 'default')"
                  v-bind="popupProps"
                >
                  <VIcon :icon="activeDialogPopup === 'always' ? 'bx-bell-ring' : (activeDialogPopup === 'never' ? 'bx-bell-off' : 'bx-window-alt')" class="mr-1" />
                  Всплывающее окно
                </VBtn>
              </template>
              <VCard min-width="270" class="pa-2">
                <div class="text-subtitle-2 pa-2 border-bottom font-weight-bold">Всплывающие окна для этого чата</div>
                <VList density="compact" class="py-1">
                  <VListItem
                    :active="activeDialogPopup === 'default'"
                    @click="setDialogPopup(activeDialog, 'default')"
                  >
                    <template #prepend>
                      <VIcon icon="bx-cog" size="18" class="mr-2" />
                    </template>
                    <VListItemTitle>По умолчанию</VListItemTitle>
                    <VListItemSubtitle class="text-caption text-grey">Как в общих настройках</VListItemSubtitle>
                  </VListItem>

                  <VListItem
                    :active="activeDialogPopup === 'always'"
                    @click="setDialogPopup(activeDialog, 'always')"
                  >
                    <template #prepend>
                      <VIcon icon="bx-check-circle" color="success" size="18" class="mr-2" />
                    </template>
                    <VListItemTitle class="text-success font-weight-medium">Всегда показывать</VListItemTitle>
                    <VListItemSubtitle class="text-caption text-grey">Даже если открыта другая вкладка</VListItemSubtitle>
                  </VListItem>

                  <VListItem
                    :active="activeDialogPopup === 'never'"
                    @click="setDialogPopup(activeDialog, 'never')"
                  >
                    <template #prepend>
                      <VIcon icon="bx-x-circle" color="error" size="18" class="mr-2" />
                    </template>
                    <VListItemTitle class="text-error">Отключить</VListItemTitle>
                    <VListItemSubtitle class="text-caption text-grey">Не показывать всплывающие окна</VListItemSubtitle>
                  </VListItem>
                </VList>
              </VCard>
            </VMenu>



            <!-- Метки чата -->
            <VMenu :close-on-content-click="false" location="bottom end">
              <template #activator="{ props }">
                <VBtn
                  color="primary"
                  variant="outlined"
                  size="small"
                  v-bind="props"
                >
                  <VIcon icon="bx-purchase-tag" class="mr-1" />
                  Метки чата
                </VBtn>
              </template>
              <VCard min-width="260" class="pa-3">
                <div class="text-subtitle-2 pa-1 border-bottom font-weight-bold">Метки этого диалога</div>
                
                <VList density="compact" class="py-1">
                  <VListItem v-if="allTags.length === 0" class="text-grey text-caption py-1">
                    Нет меток. Создайте первую ниже!
                  </VListItem>
                  <VListItem
                    v-for="tag in allTags"
                    :key="tag.id"
                    class="px-1"
                    @click="toggleDialogTag(activeDialog, tag)"
                  >
                    <template #prepend>
                      <VCheckboxBtn
                        :model-value="(activeDialog.tags || []).some(t => t.id === tag.id)"
                        color="primary"
                        density="compact"
                      />
                    </template>
                    <VListItemTitle class="d-flex align-center">
                      <VBadge dot :color="tag.color" class="mr-2" inline />
                      {{ tag.name }}
                    </VListItemTitle>
                  </VListItem>
                </VList>

                <VDivider class="my-2" />
                <div class="text-caption text-grey mb-1 font-weight-medium">Создать и привязать метку:</div>
                <div class="d-flex align-center gap-1">
                  <VTextField
                    v-model="quickTagName"
                    placeholder="Имя метки..."
                    variant="outlined"
                    density="compact"
                    hide-details
                    class="flex-grow-1"
                  />
                  <VBtn
                    color="primary"
                    size="small"
                    icon
                    :loading="creatingQuickTag"
                    :disabled="!quickTagName.trim()"
                    @click="createQuickTagAndAttach(activeDialog)"
                  >
                    <VIcon icon="bx-plus" />
                  </VBtn>
                </div>
              </VCard>
            </VMenu>
          </div>
        </div>

        <!-- Панель поиска внутри открытого диалога (по ключевому слову и дате/времени) -->
        <VExpandTransition>
          <div 
            v-if="showInChatSearch" 
            class="in-chat-search-bar px-3 py-2 border-bottom d-flex align-center gap-2 flex-wrap"
          >
            <VTextField
              v-model="inChatSearchQuery"
              placeholder="Поиск по тексту сообщения..."
              density="compact"
              variant="outlined"
              prepend-inner-icon="bx-search"
              hide-details
              clearable
              class="flex-grow-1"
              style="min-width: 220px;"
              @keyup.enter="nextSearchMatch"
            />

            <VTextField
              v-model="inChatSearchDate"
              type="date"
              label="Дата сообщения"
              density="compact"
              variant="outlined"
              hide-details
              clearable
              style="max-width: 170px;"
            />

            <div v-if="inChatSearchResults.length > 0" class="d-flex align-center gap-1 text-caption font-weight-bold text-primary">
              <span>{{ currentSearchMatchIndex + 1 }} из {{ inChatSearchResults.length }}</span>
              <VBtn icon size="x-small" variant="tonal" color="primary" @click="prevSearchMatch">
                <VIcon icon="bx-chevron-up" />
                <VTooltip activator="parent" location="top">Предыдущее совпадение</VTooltip>
              </VBtn>
              <VBtn icon size="x-small" variant="tonal" color="primary" @click="nextSearchMatch">
                <VIcon icon="bx-chevron-down" />
                <VTooltip activator="parent" location="top">Следующее совпадение</VTooltip>
              </VBtn>
            </div>
            <div v-else-if="inChatSearchQuery.trim() || inChatSearchDate" class="text-caption text-error font-weight-medium">
              Совпадений не найдено
            </div>

            <VBtn icon size="small" variant="text" color="grey" @click="showInChatSearch = false">
              <VIcon icon="bx-x" />
              <VTooltip activator="parent" location="top">Закрыть поиск</VTooltip>
            </VBtn>
          </div>
        </VExpandTransition>

        <!-- Сообщения чата с пагинацией и дозагрузкой при скролле вверх -->
        <div 
          ref="messageContainer" 
          class="chat-messages flex-grow-1 overflow-y-auto pa-4 d-flex flex-column"
          style="gap: 12px;"
          @scroll.passive="handleChatScroll"
        >
          <div v-if="loadingHistory" class="text-center py-8">
            <VProgressCircular indeterminate color="primary" />
          </div>

          <template v-else>
            <!-- Индикатор подгрузки старых сообщений сверху -->
            <div v-if="loadingMoreMessages" class="d-flex justify-center align-center py-2 gap-2 text-caption text-grey">
              <VProgressCircular indeterminate size="18" width="2" color="primary" />
              <span>Загрузка предыдущих сообщений...</span>
            </div>
            
            <!-- Плашка начала переписки, если все старые сообщения загружены -->
            <div v-else-if="!hasMoreMessages && messages.length > 0" class="d-flex justify-center my-2">
              <div class="chat-history-start-pill text-caption px-3 py-1 rounded-pill text-grey d-flex align-center gap-1">
                <VIcon icon="bx-history" size="14" />
                <span>Начало переписки</span>
              </div>
            </div>
            
            <!-- Кнопка быстрой подгрузки более ранних сообщений -->
            <div v-else-if="hasMoreMessages && messages.length > 0" class="d-flex justify-center my-1">
              <VBtn 
                size="x-small" 
                variant="text" 
                color="primary" 
                class="text-caption text-none"
                :loading="loadingMoreMessages"
                @click="loadMoreMessages"
              >
                <VIcon icon="bx-chevron-up" size="16" class="mr-1" />
                Показать более ранние сообщения
              </VBtn>
            </div>

            <template v-for="(msg, index) in messages" :key="msg.id || index">
              <div 
                v-if="shouldShowDateDivider(msg, index)" 
                class="d-flex justify-center my-3"
              >
                <div class="date-divider-pill rounded-pill shadow-xs">
                  {{ formatDateDivider(msg.created_at) }}
                </div>
              </div>

              <div 
                :id="'msg-' + (msg.id || msg.external_id)"
                :class="['d-flex mb-2', msg.direction === 'outbound' ? 'justify-end' : 'justify-start']"
              >
                <div 
                  :class="[
                    'message-bubble pa-3', 
                    msg.direction === 'outbound' ? 'message-outbound' : 'message-inbound',
                    { 'message-search-highlight': isMessageHighlighted(msg) }
                  ]"
                  style="max-width: 75%; min-width: 90px;"
                >
                  <!-- Вложения (изображения/фото) -->
                  <div v-if="msg.attachments && msg.attachments.length" class="message-attachments mb-2">
                    <div v-for="(att, aIdx) in msg.attachments" :key="aIdx" class="attachment-item mb-1">
                      <img 
                        v-if="att.type === 'image' || att.type === 'photo'" 
                        :src="att.preview_url || att.url" 
                        :alt="att.title || 'Изображение'" 
                        class="chat-image-preview rounded elevation-2 cursor-pointer" 
                        @click="openImagePreview(att.url || att.preview_url)"
                        @load="scrollToBottom(false)"
                        @error="onAttachmentImageError($event, att)"
                        referrerpolicy="no-referrer"
                        crossorigin="anonymous"
                        loading="lazy"
                        style="max-width: 100%; max-height: 280px; object-fit: contain; border-radius: 8px; display: block;"
                      />
                    </div>

                  </div>

                  <div v-if="msg.text" class="message-text text-pre-wrap">{{ msg.text }}</div>

                  <div 
                    :class="[
                      'message-meta text-caption d-flex align-center justify-end mt-1', 
                      msg.direction === 'outbound' ? 'meta-outbound' : 'meta-inbound'
                    ]"
                  >
                    <span>{{ formatTime(msg.created_at) }}</span>
                    <VIcon 
                      v-if="msg.direction === 'outbound'"
                      icon="bx-check-double" 
                      size="13" 
                      class="ml-1" 
                    />
                  </div>
                </div>
              </div>
            </template>
          </template>

        </div>

        <!-- Панель ввода сообщения -->
        <div class="chat-input-area border-top pa-3">
          <div class="d-flex align-center gap-2">

            <VTextarea
              v-model="replyText"
              placeholder="Напишите сообщение... (Ctrl + Enter для отправки)"
              variant="outlined"
              density="comfortable"
              hide-details
              rows="1"
              auto-grow
              max-rows="4"
              class="flex-grow-1"
              @keydown.ctrl.enter="sendMessage"
            />
            <VBtn
              color="primary"
              class="ml-2"
              elevation="1"
              :loading="sendingMessage"
              :disabled="!replyText.trim()"
              @click="sendMessage"
            >
              <VIcon icon="bx-paper-plane" />
            </VBtn>
          </div>
        </div>
      </template>
    </div>

    <!-- Модальное окно библиотеки звуковых уведомлений -->
    <VDialog v-model="showSoundModal" max-width="500">
      <VCard>
        <VCardTitle class="d-flex align-center justify-space-between border-bottom pa-4">
          <div class="d-flex align-center">
            <VIcon icon="bx-volume-full" color="primary" class="mr-2" />
            <span class="text-h6 font-weight-bold">Библиотека звуковых уведомлений</span>
          </div>
          <VBtn icon variant="text" @click="showSoundModal = false">
            <VIcon icon="bx-x" />
          </VBtn>
        </VCardTitle>

        <VCardText class="pa-4">
          <div class="text-caption text-grey mb-3">
            Выберите глобальный звук для входящих сообщений. Для любого чата можно также назначить персональный звук.
          </div>

          <VList class="border rounded mb-4" density="comfortable">
            <VListItem
              v-for="snd in soundLibrary"
              :key="snd.id"
              :active="globalSound === snd.id"
              color="primary"
              class="border-bottom cursor-pointer"
              @click="saveGlobalSound(snd.id)"
            >
              <template #prepend>
                <VRadioGroup :model-value="globalSound" hide-details class="ma-0 pa-0">
                  <VRadio :value="snd.id" color="primary" hide-details />
                </VRadioGroup>
              </template>
              <VListItemTitle class="font-weight-medium">{{ snd.name }}</VListItemTitle>
              <VListItemSubtitle class="text-caption text-grey">{{ snd.desc }}</VListItemSubtitle>
              <template #append>
                <VBtn
                  v-if="snd.id !== 'mute'"
                  icon
                  variant="tonal"
                  size="small"
                  color="primary"
                  @click.stop="playNotificationSound(snd.id)"
                >
                  <VIcon icon="bx-play" />
                  <VTooltip activator="parent" location="top">Прослушать</VTooltip>
                </VBtn>
              </template>
            </VListItem>
          </VList>

          <div class="d-flex align-center gap-3">
            <VIcon icon="bx-volume-low" color="grey" />
            <VSlider
              v-model="soundVolume"
              :min="0.1"
              :max="1.0"
              :step="0.05"
              label="Громкость"
              hide-details
              color="primary"
              @update:model-value="(v) => localStorage.setItem('multichat_sound_volume', v.toString())"
            />
            <VIcon icon="bx-volume-full" color="primary" />
          </div>

          <VDivider class="my-4" />

          <!-- Всплывающие уведомления (Desktop Push / Popups) -->
          <div class="d-flex align-center justify-space-between p-3 rounded border bg-grey-lighten-5">
            <div class="mr-3">
              <div class="font-weight-bold text-subtitle-2 d-flex align-center gap-1">
                <VIcon icon="bx-window-alt" color="primary" size="18" />
                Всплывающие уведомления на рабочем столе
              </div>
              <div class="text-caption text-grey">
                Показывать всплывающее окно о новых сообщениях (даже если открыта другая вкладка). По умолчанию: отключено.
              </div>
            </div>
            <VSwitch
              :model-value="globalPopupsEnabled"
              color="primary"
              hide-details
              density="compact"
              @update:model-value="toggleGlobalPopups"
            />
          </div>

        </VCardText>
      </VCard>
    </VDialog>


    <!-- Модальное окно управления личными аккаунтами -->
    <VDialog v-model="showAccountsModal" max-width="650">
      <VCard>
        <VCardTitle class="d-flex align-center justify-space-between border-bottom pa-4">
          <span class="text-h6 font-weight-bold">Подключение личных аккаунтов</span>
          <VBtn icon variant="text" @click="showAccountsModal = false">
            <VIcon icon="bx-x" />
          </VBtn>
        </VCardTitle>

        <VCardText class="pa-4">
          <VRadioGroup v-model="newAccountType" inline class="mb-4">
            <VRadio label="WhatsApp (по QR-коду)" value="whatsapp_qr" color="success" />
            <VRadio label="Telegram (по QR-коду)" value="telegram_qr" color="primary" />
            <VRadio label="ВКонтакте (Токен)" value="vk_user" color="primary" />
            <VRadio label="MAX (API Ключ)" value="max_user" color="primary" />
          </VRadioGroup>

          <!-- Секция 1: WhatsApp по QR-коду -->
          <div v-if="newAccountType === 'whatsapp_qr'" class="pa-4 bg-grey-lighten-4 border rounded text-center">
            <div class="text-subtitle-1 font-weight-bold mb-2 d-flex align-center justify-center">
              <VIcon icon="bxl-whatsapp" color="#25D366" class="mr-2" size="24" />
              Авторизация WhatsApp по QR-коду
            </div>
            <p class="text-caption text-grey mb-4">
              Откройте WhatsApp на телефоне: <b>Настройки (три точки) → Связанные устройства → Привязка устройства</b> и наведите камеру на QR-код.
            </p>

            <div v-if="!waQrData" class="py-4">
              <VBtn color="success" :loading="loadingWhatsAppQr" @click="initWhatsAppQr">
                <VIcon icon="bx-qr" class="mr-1" />
                Сгенерировать QR-код WhatsApp
              </VBtn>
            </div>

            <div v-else class="d-flex flex-column align-center">
              <div class="pa-3 bg-white border rounded mb-3 shadow-sm" style="display: inline-block;">
                <img v-if="waQrData.qr_base64" :src="waQrData.qr_base64" style="width: 200px; height: 200px; display: block;" alt="WhatsApp QR Code" />
                <VIcon v-else icon="bx-qr" size="160" color="success" />
              </div>
              <div class="text-caption text-grey mb-4">Сканируйте QR-код в приложении WhatsApp на смартфоне</div>

              <VCard class="pa-3 border text-left w-100 mb-2">
                <div class="text-subtitle-2 mb-2 font-weight-bold">Данные аккаунта WhatsApp</div>
                <VTextField
                  v-model="waAccountName"
                  placeholder="Имя аккаунта (например: WhatsApp Доставка)"
                  label="Название"
                  variant="outlined"
                  density="compact"
                  class="mb-2"
                />
                <VTextField
                  v-model="waAccountPhone"
                  placeholder="+79990001122"
                  label="Номер телефона WhatsApp"
                  variant="outlined"
                  density="compact"
                  class="mb-2"
                />
                <VTextField
                  v-model="waGreenApiToken"
                  placeholder="instanceId:apiToken (если используется Green-API / шлюз)"
                  label="Green-API / Токен шлюза (необязательно)"
                  variant="outlined"
                  density="compact"
                  class="mb-2"
                />
                <VBtn 
                  color="success" 
                  block 
                  :loading="confirmingWa"
                  @click="confirmWhatsApp"
                >
                  <VIcon icon="bx-check" class="mr-1" />
                  Подтвердить привязку WhatsApp
                </VBtn>
              </VCard>
            </div>
          </div>

          <!-- Секция 2: Telegram по QR-коду -->
          <div v-else-if="newAccountType === 'telegram_qr'" class="pa-4 bg-grey-lighten-4 border rounded text-center">
            <div class="text-subtitle-1 font-weight-bold mb-2 d-flex align-center justify-center">
              <VIcon icon="bxl-telegram" color="#26A69A" class="mr-2" size="24" />
              Авторизация Telegram по QR-коду
            </div>
            <p class="text-caption text-grey mb-4">
              Откройте приложение Telegram на телефоне: <b>Настройки → Устройства → Подключить устройство</b> и отсканируйте код.
            </p>

            <div v-if="!qrData" class="py-4">
              <VBtn color="primary" :loading="loadingTelegramQr" @click="initTelegramQr">
                <VIcon icon="bx-qr" class="mr-1" />
                Сгенерировать QR-код Telegram
              </VBtn>
            </div>

            <div v-else class="d-flex flex-column align-center">
              <div class="pa-3 bg-white border rounded mb-3 shadow-sm" style="display: inline-block;">
                <img v-if="qrData.qr_base64" :src="qrData.qr_base64" style="width: 200px; height: 200px; display: block;" alt="Telegram QR Code" />
                <VIcon v-else icon="bx-qr" size="160" color="primary" />
              </div>
              <div class="text-caption text-grey mb-2">Сканируйте QR-код в приложении Telegram (Настройки → Устройства → Подключить устройство)</div>
              
              <div v-if="qrData.qr_url" class="mt-2 text-caption">
                <a :href="qrData.qr_url" target="_blank" class="text-primary text-decoration-none">
                  <VIcon icon="bx-link-external" size="14" class="mr-1" />
                  Открыть прямую ссылку авторизации Telegram
                </a>
              </div>
            </div>
          </div>

          <!-- Секция 3: ВКонтакте -->
          <div v-else-if="newAccountType === 'vk_user'" class="pa-4 bg-grey-lighten-4 border rounded">
            <div class="text-subtitle-1 font-weight-bold mb-2 d-flex align-center">
              <VIcon icon="bxl-vk" color="#0077FF" class="mr-2" size="24" />
              Авторизация личного аккаунта ВКонтакте
            </div>

            <!-- Вкладки методов входа -->
            <VTabs v-model="vkAuthTab" density="compact" class="mb-3 border-bottom">
              <VTab value="qr">
                <VIcon icon="bx-qr-scan" size="16" class="mr-1" />
                Вход по QR-коду
              </VTab>
              <VTab value="direct">
                <VIcon icon="bx-user-check" size="16" class="mr-1" />
                По Логину и Паролю
              </VTab>
              <VTab value="custom_app">
                <VIcon icon="bx-code-block" size="16" class="mr-1" />
                Свое приложение (App ID)
              </VTab>
              <VTab value="token">
                <VIcon icon="bx-key" size="16" class="mr-1" />
                Ввод токена / VKHost
              </VTab>
            </VTabs>

            <!-- Вкладка 0: Вход по QR-коду -->
            <div v-if="vkAuthTab === 'qr'" class="pt-1 text-center">
              <div class="text-caption mb-3 text-grey-darken-1 text-left">
                Отсканируйте QR-код камерой телефона или в приложении ВКонтакте, нажмите <b>«Разрешить»</b>, затем скопируйте адрес страницы (или токен) и нажмите «Подтвердить вход».
              </div>

              <div v-if="vkQrLoading" class="py-6">
                <VProgressCircular indeterminate color="primary" />
                <div class="text-caption mt-2">Генерация QR-кода ВКонтакте...</div>
              </div>

              <div v-else-if="vkQrBase64" class="d-flex flex-column align-center mb-3">
                <div class="pa-2 bg-white rounded border elevation-1 mb-2">
                  <img :src="vkQrBase64" alt="VK QR Code" style="width: 200px; height: 200px; display: block;" />
                </div>
                <div class="d-flex gap-2">
                  <VBtn size="small" variant="text" color="primary" @click="initVkQr">
                    <VIcon icon="bx-refresh" class="mr-1" />
                    Обновить QR
                  </VBtn>
                  <VBtn size="small" variant="tonal" color="primary" :href="vkQrAuthUrl" target="_blank">
                    <VIcon icon="bx-link-external" class="mr-1" />
                    Открыть ссылку
                  </VBtn>
                </div>
              </div>

              <div class="mt-3 text-left">
                <VTextField
                  v-model="vkQrTokenInput"
                  placeholder="Вставьте ссылку после авторизации или access_token..."
                  label="Адрес страницы / Токен после сканирования"
                  variant="outlined"
                  density="compact"
                  class="mb-2"
                  hide-details
                  @keyup.enter="confirmVkQr"
                />
                <VBtn 
                  color="primary" 
                  block 
                  :loading="vkQrConfirming" 
                  :disabled="!vkQrTokenInput.trim()"
                  @click="confirmVkQr"
                  class="mt-2"
                >
                  <VIcon icon="bx-check-circle" class="mr-1" />
                  Подтвердить и подключить аккаунт
                </VBtn>
              </div>
            </div>

            <!-- Вкладка 1: Прямой вход с сервера -->
            <div v-else-if="vkAuthTab === 'direct'" class="pt-1">
              <VAlert type="success" variant="tonal" density="compact" class="mb-3 text-caption">
                <b>Рекомендуемый способ:</b> Сервер выполняет авторизацию напрямую со своего IP-адреса. Это исключает ошибки привязки к домашнему IP и дает полный доступ к переписке.
              </VAlert>


              <VTextField
                v-model="vkDirectLogin"
                placeholder="+79991234567 или email"
                label="Телефон или Email ВКонтакте"
                variant="outlined"
                density="compact"
                class="mb-2"
                :disabled="loggingInVkDirect"
              />

              <VTextField
                v-model="vkDirectPassword"
                type="password"
                placeholder="Ваш пароль от страницы VK"
                label="Пароль ВКонтакте"
                variant="outlined"
                density="compact"
                class="mb-2"
                :disabled="loggingInVkDirect"
              />

              <div v-if="vkNeed2Fa" class="pa-3 mb-3 bg-warning-lighten-5 border border-warning rounded">
                <div class="text-caption font-weight-bold text-warning mb-1">Двухфакторная аутентификация (2FA)</div>
                <div class="text-caption mb-2">{{ vk2FaMessage }}</div>
                <VTextField
                  v-model="vkDirectCode"
                  placeholder="123456"
                  label="Код из SMS или приложения"
                  variant="outlined"
                  density="compact"
                  class="mb-1"
                />
              </div>

              <VBtn 
                color="primary" 
                block 
                :loading="loggingInVkDirect"
                @click="handleVkDirectAuth"
              >
                <VIcon icon="bx-log-in" class="mr-1" />
                {{ vkNeed2Fa ? 'Подтвердить код и войти' : 'Войти и подключить профиль' }}
              </VBtn>
            </div>

            <!-- Вкладка 2: Собственное Standalone приложение -->
            <div v-else-if="vkAuthTab === 'custom_app'" class="pt-1">
              <VAlert type="info" variant="tonal" density="compact" class="mb-3 text-caption">
                <b>Официальный путь:</b> Создайте Standalone-приложение на 
                <a href="https://vk.com/apps?act=manage" target="_blank" class="text-primary font-weight-bold">vk.com/apps</a>
                (займет 1 минуту). Токены собственных приложений никогда не блокируются.
              </VAlert>

              <VTextField
                v-model="vkCustomAppId"
                placeholder="Например: 51874231"
                label="ID вашего Standalone-приложения (App ID)"
                variant="outlined"
                density="compact"
                class="mb-3"
              />

              <VBtn 
                color="primary" 
                block 
                variant="elevated" 
                class="mb-3"
                :disabled="!vkCustomAppId.trim()"
                @click="openCustomAppOAuth"
              >
                <VIcon icon="bx-link-external" class="mr-1" />
                1. Открыть окно входа для моего приложения
              </VBtn>

              <p class="text-caption text-grey mb-2">
                <b>2.</b> Нажмите «Разрешить», скопируйте адресную строку и вставьте в поле:
              </p>

              <VTextField
                v-model="newAccountToken"
                placeholder="Вставьте скопированную ссылку из адресной строки или access_token..."
                label="Ссылка из адресной строки браузера или access_token"
                variant="outlined"
                density="compact"
                class="mb-3"
              />

              <VBtn 
                color="success" 
                block 
                :loading="savingAccount"
                :disabled="!newAccountToken.trim()"
                @click="saveAccount"
              >
                Подключить аккаунт ВКонтакте
              </VBtn>
            </div>

            <!-- Вкладка 3: VKHost / Ручной ввод токена -->
            <div v-else class="pt-1">
              <VAlert type="info" variant="tonal" density="compact" class="mb-3 text-caption">
                <b>Инструкция:</b> В сервисе <b>VKHost</b> нажмите на карточку <b>«VK Admin»</b> или <b>«VFeed»</b>, нажмите «Разрешить» и скопируйте адресную строку.
              </VAlert>

              <div class="d-flex flex-column gap-2 mb-3">
                <VBtn 
                  color="primary" 
                  block 
                  variant="elevated" 
                  @click="openVkAuthWindow('vk_admin')"
                >
                  <VIcon icon="bxl-vk" class="mr-2" />
                  1. Войти через VK Admin (Прямая авторизация)
                </VBtn>

                <div class="d-flex gap-2">
                  <VBtn 
                    color="secondary" 
                    variant="tonal" 
                    size="small"
                    class="flex-grow-1"
                    @click="openVkAuthWindow('vfeed')"
                  >
                    Войти через VFeed
                  </VBtn>
                  <VBtn 
                    color="secondary" 
                    variant="tonal" 
                    size="small"
                    class="flex-grow-1"
                    @click="openVkAuthWindow('vk_host')"
                  >
                    <VIcon icon="bx-link-external" size="14" class="mr-1" />
                    Открыть сайт VKHost
                  </VBtn>
                </div>
              </div>

              <p class="text-caption text-grey mb-2">
                <b>2.</b> В открывшемся окне ВК нажмите <b>«Разрешить»</b>, скопируйте всю адресную строку браузера и вставьте в поле ниже:
              </p>

              <VTextField
                v-model="newAccountToken"
                placeholder="Вставьте скопированную ссылку из адресной строки или access_token..."
                label="Ссылка из адресной строки браузера или access_token"
                variant="outlined"
                density="compact"
                class="mb-3"
              />

              <VBtn 
                color="success" 
                block 
                :loading="savingAccount"
                :disabled="!newAccountToken.trim()"
                @click="saveAccount"
              >
                Подключить аккаунт ВКонтакте
              </VBtn>
            </div>
          </div>

          <!-- Секция 4: MAX -->
          <div v-else class="pa-4 bg-grey-lighten-4 border rounded">
            <div class="text-subtitle-1 font-weight-bold mb-2 d-flex align-center">
              <VIcon icon="bx-mobile-alt" color="#FF9800" class="mr-2" size="24" />
              Авторизация личного профиля MAX (МАКС)
            </div>

            <!-- Вкладки методов входа MAX -->
            <VTabs v-model="maxAuthTab" density="compact" class="mb-3 border-bottom">
              <VTab value="qr">
                <VIcon icon="bx-qr" size="16" class="mr-1" />
                Вход по QR-коду
              </VTab>
              <VTab value="sms">
                <VIcon icon="bx-message-rounded-dots" size="16" class="mr-1" />
                По номеру телефона (SMS)
              </VTab>
              <VTab value="token">
                <VIcon icon="bx-key" size="16" class="mr-1" />
                Ввод API Токена
              </VTab>
            </VTabs>

            <!-- Вкладка 1: QR-код MAX (Web Instance Bridge) -->
            <div v-if="maxAuthTab === 'qr'" class="pt-1 text-center">
              <VAlert type="info" variant="tonal" density="compact" class="mb-3 text-caption text-left">
                <b>Инструкция по подключению:</b> Откройте приложение <b>MAX на телефоне</b>, перейдите в <b>«Настройки» → «Связанные устройства»</b> (или «Веб-клиент») и наведите камеру на QR-код ниже.
              </VAlert>

              <div v-if="!maxQrData" class="py-4">
                <VBtn color="warning" size="large" :loading="loadingMaxQr" @click="initMaxQr">
                  <VIcon icon="bx-qr" class="mr-2" />
                  Сгенерировать динамический QR-код MAX
                </VBtn>
                <div class="text-caption text-grey mt-2">Будет создан защищенный канал веб-моста (Web Instance Bridge)</div>
              </div>

              <div v-else class="d-flex flex-column align-center">
                <!-- Статус и таймер жизни QR-кода -->
                <div class="d-flex align-center gap-2 mb-2">
                  <VChip 
                    :color="maxQrStatus === 'expired' ? 'error' : (maxQrStatus === 'scanned' ? 'info' : 'warning')" 
                    size="small" 
                    variant="flat"
                  >
                    <VIcon :icon="maxQrStatus === 'expired' ? 'bx-error-circle' : 'bx-loader-alt'" :class="{'spin-icon': maxQrStatus === 'pending'}" size="14" class="mr-1" />
                    {{ maxQrStatus === 'expired' ? 'QR-код истек' : (maxQrStatus === 'scanned' ? 'Отсканирован! Подключение...' : `Действителен еще ${maxQrTimeLeft} сек`) }}
                  </VChip>
                </div>

                <!-- Контейнер QR-кода с эффектом сканирования -->
                <div class="pa-3 bg-white border rounded mb-3 shadow-sm position-relative overflow-hidden" style="display: inline-block;">
                  <img v-if="maxQrData.qr_base64 && maxQrStatus !== 'expired'" :src="maxQrData.qr_base64" style="width: 220px; height: 220px; display: block;" alt="MAX QR Code" />
                  <div v-else-if="maxQrStatus === 'expired'" class="d-flex flex-column align-center justify-center" style="width: 220px; height: 220px;">
                    <VIcon icon="bx-time-five" size="64" color="error" class="mb-2" />
                    <div class="text-caption text-error font-weight-bold">Время действия истекло</div>
                    <VBtn color="warning" size="small" class="mt-2" @click="initMaxQr">
                      <VIcon icon="bx-refresh" size="14" class="mr-1" />
                      Обновить QR
                    </VBtn>
                  </div>
                  <VIcon v-else icon="bx-qr" size="180" color="warning" />
                  
                  <!-- Анимация лазерного сканирования -->
                  <div v-if="maxQrStatus === 'pending' && maxQrData.qr_base64" class="qr-scan-laser"></div>
                </div>

                <div class="text-caption text-grey mb-3">
                  Ожидание подтверждения в мобильном приложении MAX...
                </div>

                <!-- Кнопка ручной активации / фоллбэк -->
                <VExpansionPanels density="compact" class="mb-3" style="max-width: 400px;">
                  <VExpansionPanel title="Дополнительно: Ручное подтверждение привязки">
                    <VExpansionPanelText>
                      <VTextField
                        v-model="maxManualPhone"
                        label="Номер телефона профиля MAX"
                        placeholder="+7 (999) 000-00-00"
                        variant="outlined"
                        density="compact"
                        class="mb-2"
                      />
                      <VTextField
                        v-model="maxManualName"
                        label="Имя / название аккаунта"
                        placeholder="Например: Личный MAX Администратора"
                        variant="outlined"
                        density="compact"
                        class="mb-2"
                      />
                      <VBtn 
                        color="success" 
                        block 
                        size="small"
                        :loading="confirmingMaxBridge" 
                        @click="confirmMaxBridge"
                      >
                        <VIcon icon="bx-check" class="mr-1" />
                        Активировать сессию моста
                      </VBtn>
                    </VExpansionPanelText>
                  </VExpansionPanel>
                </VExpansionPanels>

                <div class="d-flex gap-2">
                  <VBtn variant="tonal" size="small" color="secondary" @click="initMaxQr">
                    <VIcon icon="bx-refresh" size="16" class="mr-1" />
                    Пересоздать QR-код
                  </VBtn>
                </div>
              </div>
            </div>


            <!-- Вкладка 2: Вход по номеру телефона и SMS -->
            <div v-else-if="maxAuthTab === 'sms'" class="pt-1">
              <VAlert type="success" variant="tonal" density="compact" class="mb-3 text-caption">
                <b>Быстрый вход:</b> Введите ваш номер телефона, получите SMS-код подтверждения и войдите в профиль.
              </VAlert>

              <VTextField
                v-model="maxPhone"
                placeholder="+7 (999) 123-45-67"
                label="Номер телефона профиля MAX"
                variant="outlined"
                density="compact"
                class="mb-2"
                :disabled="maxSmsSent"
              />

              <VTextField
                v-model="maxAccountTitle"
                placeholder="Например: Менеджер Алексей"
                label="Название аккаунта (необязательно)"
                variant="outlined"
                density="compact"
                class="mb-3"
              />

              <div v-if="!maxSmsSent">
                <VBtn 
                  color="warning" 
                  block 
                  :loading="requestingMaxSms" 
                  :disabled="!maxPhone.trim()"
                  @click="requestMaxSms"
                >
                  <VIcon icon="bx-send" class="mr-1" />
                  Получить SMS-код
                </VBtn>
              </div>

              <div v-else class="pa-3 bg-warning-lighten-5 border border-warning rounded mb-3">
                <div class="text-caption font-weight-bold text-warning mb-2">Код подтверждения отправлен на {{ maxPhone }}</div>
                <VTextField
                  v-model="maxSmsCode"
                  placeholder="Введите код из SMS"
                  label="SMS-код"
                  variant="outlined"
                  density="compact"
                  class="mb-3"
                />
                <div class="d-flex gap-2">
                  <VBtn 
                    color="success" 
                    class="flex-grow-1"
                    :loading="verifyingMaxSms" 
                    :disabled="!maxSmsCode.trim()"
                    @click="verifyMaxSms"
                  >
                    <VIcon icon="bx-check-double" class="mr-1" />
                    Подтвердить и войти
                  </VBtn>
                  <VBtn 
                    variant="tonal" 
                    color="secondary"
                    @click="maxSmsSent = false"
                  >
                    Изменить номер
                  </VBtn>
                </div>
              </div>
            </div>

            <!-- Вкладка 3: Ввод официального API Токена -->
            <div v-else class="pt-1">
              <VAlert type="info" variant="tonal" density="compact" class="mb-3 text-caption">
                <b>Официальный токен:</b> Получите API ключ в личном кабинете <a href="https://business.max.ru" target="_blank" class="text-primary font-weight-bold">business.max.ru</a> в разделе «Чат-боты и интеграции».
              </VAlert>

              <VTextField
                v-model="newAccountName"
                label="Название аккаунта (например: МАКС Доставка)"
                variant="outlined"
                density="compact"
                class="mb-3"
              />

              <VTextField
                v-model="newAccountPhone"
                label="Номер телефона (необязательно)"
                variant="outlined"
                density="compact"
                class="mb-3"
              />

              <VTextField
                v-model="newAccountToken"
                label="API Токен MAX"
                placeholder="Вставьте токен из business.max.ru..."
                variant="outlined"
                density="compact"
                class="mb-3"
              />

              <VBtn 
                color="warning" 
                block 
                :loading="savingAccount"
                :disabled="!newAccountName.trim() || !newAccountToken.trim()"
                @click="saveAccount"
              >
                Подключить аккаунт MAX
              </VBtn>
            </div>
          </div>

          <VDivider class="my-5" />

          <div class="text-subtitle-1 font-weight-bold mb-2">Подключенные аккаунты</div>
          <VList class="border rounded" style="max-height: 200px; overflow-y: auto;">
            <VListItem v-if="loadingAccounts" class="text-center py-3">
              <VProgressCircular indeterminate color="primary" />
            </VListItem>

            <VListItem v-else-if="accounts.length === 0" class="text-center text-grey py-3">
              Подключенных личных аккаунтов нет
            </VListItem>

            <VListItem
              v-for="acc in accounts"
              :key="acc.id"
              class="border-bottom"
            >
              <template #prepend>
                <VIcon 
                  :icon="acc.channel === 'whatsapp' ? 'bxl-whatsapp' : (acc.channel === 'telegram_user' ? 'bxl-telegram' : (acc.channel === 'vk_user' ? 'bxl-vk' : 'bx-mobile-alt'))" 
                  :color="acc.channel === 'whatsapp' ? '#25D366' : (acc.channel === 'telegram_user' ? '#26A69A' : (acc.channel === 'vk_user' ? '#0077FF' : '#FF9800'))" 
                  class="mr-3"
                />
              </template>
              <VListItemTitle class="font-weight-medium">{{ acc.name }}</VListItemTitle>
              <VListItemSubtitle class="text-caption text-grey">
                {{ acc.phone || 'Активен' }} (Статус: {{ acc.status }})
              </VListItemSubtitle>
              <template #append>
                <div class="d-flex align-center gap-1">
                  <VBtn 
                    icon
                    variant="tonal" 
                    color="primary" 
                    density="comfortable" 
                    :loading="testingAccountId === acc.id"
                    @click="testAccountConnection(acc)"
                  >
                    <VIcon icon="bx-check-shield" />
                    <VTooltip activator="parent" location="top">Проверить соединение</VTooltip>
                  </VBtn>
                  <VBtn 
                    icon
                    variant="text" 
                    color="warning" 
                    density="comfortable" 
                    :loading="clearingAccountMsgId === acc.id"
                    @click="clearAccountMessages(acc)"
                  >
                    <VIcon icon="bx-eraser" />
                    <VTooltip activator="parent" location="top">Удалить загруженные сообщения этого аккаунта</VTooltip>
                  </VBtn>
                  <VBtn 
                    icon
                    variant="text" 
                    color="error" 
                    density="comfortable" 
                    @click="deleteAccount(acc.id)"
                  >
                    <VIcon icon="bx-trash" />
                    <VTooltip activator="parent" location="top">Отключить аккаунт (сообщения сохранятся)</VTooltip>
                  </VBtn>
                </div>

              </template>
            </VListItem>
          </VList>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- Диалог управления метками (создание/удаление) -->
    <VDialog v-model="showTagManager" max-width="500">
      <VCard>
        <VCardTitle class="d-flex align-center justify-space-between border-bottom pa-4">
          <span class="text-h6 font-weight-bold">Управление метками диалогов</span>
          <VBtn icon variant="text" @click="showTagManager = false">
            <VIcon icon="bx-x" />
          </VBtn>
        </VCardTitle>

        <VCardText class="pa-4">
          <div class="text-subtitle-2 mb-2">Создать новую метку</div>
          <div class="d-flex align-center gap-2 mb-4">
            <VTextField
              v-model="newTagName"
              placeholder="Название метки"
              variant="outlined"
              density="compact"
              hide-details
              class="flex-grow-1"
            />
            <VMenu location="bottom end">
              <template #activator="{ props }">
                <div 
                  v-bind="props" 
                  class="border rounded cursor-pointer d-flex align-center justify-center" 
                  style="width: 40px; height: 40px;"
                  :style="{ backgroundColor: newTagColor }"
                >
                  <VIcon icon="bx-palette" :color="newTagColor === '#FFEB3B' || newTagColor === '#FFC107' ? 'black' : 'white'" />
                </div>
              </template>
              <VCard class="pa-2" max-width="180">
                <div class="d-flex flex-wrap gap-1">
                  <div
                    v-for="color in presetColors"
                    :key="color"
                    class="cursor-pointer border rounded-circle"
                    style="width: 24px; height: 24px;"
                    :style="{ backgroundColor: color }"
                    @click="newTagColor = color"
                  />
                </div>
              </VCard>
            </VMenu>

            <VBtn 
              color="primary" 
              density="comfortable" 
              icon
              :loading="savingTag"
              @click="createTag"
            >
              <VIcon icon="bx-plus" />
            </VBtn>
          </div>

          <VDivider class="my-4" />

          <div class="text-subtitle-2 mb-2">Существующие метки</div>
          <VList class="border rounded overflow-y-auto" style="max-height: 250px;">
            <VListItem v-if="allTags.length === 0" class="text-center text-grey py-4">
              Созданных меток нет
            </VListItem>
            <VListItem
              v-for="tag in allTags"
              :key="tag.id"
              class="border-bottom"
            >
              <template #prepend>
                <VBadge dot :color="tag.color" class="mr-3" inline />
              </template>
              <VListItemTitle>{{ tag.name }}</VListItemTitle>
              <template #append>
                <VBtn 
                  icon
                  variant="text" 
                  color="error" 
                  density="comfortable" 
                  @click="deleteTag(tag.id)"
                >
                  <VIcon icon="bx-trash" />
                </VBtn>
              </template>
            </VListItem>
          </VList>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- Модальное окно: Универсальный поиск собеседника по номеру телефона по всем каналам -->
    <VDialog v-model="showPhoneSearchModal" max-width="560">
      <VCard class="pa-4">
        <VCardTitle class="px-0 pt-0 d-flex justify-space-between align-center">
          <div class="d-flex align-center gap-2">
            <VIcon icon="bx-phone-call" color="primary" />
            <span class="font-weight-bold">Поиск собеседника по номеру телефона</span>
          </div>
          <VBtn icon variant="text" size="small" @click="showPhoneSearchModal = false">
            <VIcon icon="bx-x" />
          </VBtn>
        </VCardTitle>

        <VCardText class="px-0 py-2">
          <p class="text-caption text-grey mb-3">
            Введите номер телефона клиента для сквозного поиска по всем мессенджерам (MAX, ВКонтакте, Telegram, WhatsApp) и CRM-базе.
          </p>

          <div class="d-flex align-center gap-2">
            <VTextField
              v-model="phoneSearchInput"
              placeholder="+7 (999) 000-00-00"
              variant="outlined"
              density="compact"
              hide-details
              class="flex-grow-1"
              @keyup.enter="searchByPhone"
            />
            <VBtn
              color="primary"
              :loading="searchingPhone"
              :disabled="!phoneSearchInput.trim()"
              @click="searchByPhone"
            >
              <VIcon icon="bx-search" class="mr-1" />
              Найти
            </VBtn>
          </div>

          <!-- Результат поиска -->
          <div v-if="phoneSearchResult" class="mt-4">
            <!-- Карточка клиента / профиля -->
            <VCard variant="outlined" class="pa-3 mb-3 bg-grey-lighten-5">
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="font-weight-bold text-subtitle-1 d-flex align-center gap-2">
                    <span>{{ phoneSearchResult.name }}</span>
                    <VChip v-if="phoneSearchResult.customer" size="x-small" color="success" variant="tonal" class="font-weight-bold">
                      CRM ГОСТЬ #{{ phoneSearchResult.customer.id }}
                    </VChip>
                  </div>
                  <div class="text-caption text-primary font-weight-medium d-flex align-center gap-1 mt-1">
                    <VIcon icon="bx-phone" size="13" />
                    {{ phoneSearchResult.phone }}
                  </div>
                </div>

                <div v-if="phoneSearchResult.customer" class="text-right text-caption">
                  <div>Бонусы: <b class="text-success">{{ phoneSearchResult.customer.bonus_points }} ₽</b></div>
                  <div>Заказов: <b>{{ phoneSearchResult.customer.total_orders_count }}</b></div>
                </div>
              </div>
            </VCard>

            <div class="text-subtitle-2 font-weight-bold mb-2">Каналы связи для диалога:</div>

            <VList density="compact" class="border rounded pa-0">
              <VListItem
                v-for="ch in phoneSearchResult.channels"
                :key="ch.channel"
                class="border-bottom py-2 px-3"
              >
                <template #prepend>
                  <VAvatar size="36" class="mr-3 bg-grey-lighten-3 border">
                    <VImg v-if="ch.avatar_url" :src="ch.avatar_url" />
                    <VIcon v-else :icon="ch.icon" :color="ch.color" />
                  </VAvatar>
                </template>

                <VListItemTitle class="font-weight-medium d-flex align-center gap-2">
                  <span>{{ ch.title }}</span>
                  <span v-if="ch.peer_id" class="text-caption text-grey font-weight-regular">(ID: {{ ch.peer_id }})</span>
                </VListItemTitle>

                <VListItemSubtitle class="text-caption" :class="ch.available ? 'text-success font-weight-medium' : 'text-grey'">
                  {{ ch.status_text }}
                </VListItemSubtitle>

                <template #append>
                  <VBtn
                    :color="ch.available ? 'primary' : 'default'"
                    :variant="ch.available ? 'flat' : 'outlined'"
                    size="small"
                    :disabled="!ch.available"
                    @click="openChannelChat(ch)"
                  >
                    <VIcon icon="bx-message-dots" class="mr-1" />
                    Написать
                  </VBtn>
                </template>
              </VListItem>
            </VList>
          </div>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- Диалог просмотра изображений (Lightbox) -->
    <VDialog v-model="showImagePreviewModal" max-width="850">

      <VCard class="pa-2 bg-grey-darken-4 rounded-lg overflow-hidden">
        <div class="d-flex justify-space-between align-center px-3 py-1 text-white">
          <span class="text-caption font-weight-medium">Просмотр изображения</span>
          <VBtn icon size="small" variant="text" color="white" @click="showImagePreviewModal = false">
            <VIcon icon="bx-x" size="22" />
          </VBtn>
        </div>
        <div class="d-flex justify-center align-center pa-2">
          <img 
            v-if="previewImageUrl" 
            :src="previewImageUrl" 
            alt="Изображение" 
            referrerpolicy="no-referrer"
            crossorigin="anonymous"
            @error="onLightboxImageError($event)"
            style="max-width: 100%; max-height: 75vh; object-fit: contain; border-radius: 6px;" 
          />

        </div>
      </VCard>
    </VDialog>

    <!-- Модальное окно глобального поиска по всем сообщениям архива -->
    <VDialog v-model="showGlobalSearchModal" max-width="850">
      <VCard class="rounded-lg">
        <VCardTitle class="d-flex align-center justify-space-between border-bottom pa-4">
          <div class="d-flex align-center gap-2">
            <VIcon icon="bx-search-alt-2" color="primary" size="24" />
            <span class="text-h6 font-weight-bold">Глобальный поиск по сообщениям и пользователям</span>
          </div>
          <VBtn icon variant="text" size="small" @click="showGlobalSearchModal = false">
            <VIcon icon="bx-x" size="22" />
          </VBtn>
        </VCardTitle>

        <VCardText class="pa-4">
          <div class="d-flex align-center gap-2 mb-3">
            <VTextField
              v-model="globalSearchQuery"
              placeholder="Введите слово, фразу, телефон или имя собеседника..."
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="bx-search"
              hide-details
              clearable
              class="flex-grow-1"
              @keyup.enter="searchGlobalMessages"
            />
            <VSelect
              v-model="globalSearchChannel"
              :items="[
                { value: 'all', title: 'Все каналы' },
                { value: 'max_user', title: 'MAX Личный' },
                { value: 'max_bot', title: 'MAX Бот' },
                { value: 'vk_user', title: 'VK Личный' },
                { value: 'vk', title: 'VK Сообщество' },
                { value: 'telegram', title: 'Telegram' },
                { value: 'whatsapp', title: 'WhatsApp' }
              ]"
              item-title="title"
              item-value="value"
              variant="outlined"
              density="comfortable"
              hide-details
              style="max-width: 180px;"
            />
            <VBtn
              color="primary"
              :loading="searchingGlobal"
              :disabled="!globalSearchQuery.trim()"
              @click="searchGlobalMessages"
            >
              <VIcon icon="bx-search" class="mr-1" />
              Искать
            </VBtn>
          </div>

          <!-- Результаты глобального поиска -->
          <div v-if="searchingGlobal" class="text-center py-8">
            <VProgressCircular indeterminate color="primary" />
            <div class="text-caption text-grey mt-2">Поиск по всей базе сообщений...</div>
          </div>

          <div v-else-if="globalSearchResults.length > 0">
            <div class="text-caption text-grey font-weight-medium mb-2 d-flex align-center justify-space-between">
              <span>Найдено сообщений: <b>{{ globalSearchTotal }}</b></span>
              <span>Нажмите на результат для перехода в чат</span>
            </div>

            <VList density="compact" class="border rounded pa-0" style="max-height: 480px; overflow-y: auto;">
              <VListItem
                v-for="item in globalSearchResults"
                :key="item.id"
                class="border-bottom py-3 px-3 cursor-pointer search-result-item"
                @click="openDialogFromSearch(item)"
              >
                <template #prepend>
                  <VAvatar size="40" class="mr-3 bg-grey-lighten-3 border position-relative">
                    <VImg v-if="item.peer_avatar" :src="item.peer_avatar" referrerpolicy="no-referrer" />
                    <VIcon v-else :icon="getChannelIcon(item.channel)" :color="getChannelColor(item.channel)" />
                    <div 
                      class="channel-badge-avatar" 
                      :style="{ backgroundColor: getChannelColor(item.channel) }"
                    >
                      <VIcon :icon="getChannelIcon(item.channel)" size="10" color="white" />
                    </div>
                  </VAvatar>
                </template>

                <VListItemTitle class="font-weight-bold d-flex align-center justify-space-between mb-1">
                  <div class="d-flex align-center gap-2">
                    <span>{{ item.peer_name || ('Собеседник ' + item.peer_id) }}</span>
                    <VChip size="x-small" :color="getChannelColor(item.channel)" variant="tonal" class="font-weight-medium">
                      {{ getChannelTitle(item.channel) }}
                    </VChip>
                  </div>
                  <span class="text-caption text-grey font-weight-regular">{{ formatTime(item.created_at) }} · {{ formatDateDivider(item.created_at) }}</span>
                </VListItemTitle>

                <VListItemSubtitle class="text-body-2 text-pre-wrap text-grey-darken-2 line-clamp-2">
                  <span :class="item.direction === 'outbound' ? 'text-primary font-weight-medium' : 'text-grey-darken-4'">
                    {{ item.direction === 'outbound' ? 'Вы: ' : '' }}
                  </span>
                  {{ item.text }}
                </VListItemSubtitle>

                <template #append>
                  <VBtn icon size="small" variant="text" color="primary">
                    <VIcon icon="bx-chevron-right" size="20" />
                  </VBtn>
                </template>
              </VListItem>
            </VList>
          </div>

          <div v-else-if="globalSearchQuery.trim()" class="text-center py-8 text-grey">
            <VIcon icon="bx-search" size="48" class="mb-2 text-grey-lighten-1" />
            <div class="text-subtitle-2 font-weight-medium">По вашему запросу ничего не найдено</div>
            <div class="text-caption">Попробуйте изменить ключевое слово или выбрать другой канал</div>
          </div>

          <div v-else class="text-center py-8 text-grey">
            <VIcon icon="bx-conversation" size="48" class="mb-2 text-grey-lighten-1" />
            <div class="text-subtitle-2 font-weight-medium">Сквозной архивный поиск</div>
            <div class="text-caption">Введите любое слово, фразу или номер для поиска по всей истории переписки</div>
          </div>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- Всплывающее интерактивное окно нового входящего сообщения (Toast / Popup) -->
    <VSnackbar
      v-model="showNotificationPopup"
      location="bottom right"
      :timeout="8000"
      color="surface"
      elevation="10"
      class="custom-chat-popup rounded-lg"
      style="max-width: 420px;"
    >
      <div 
        v-if="currentPopupMessage" 
        class="d-flex align-center gap-3 cursor-pointer py-1" 
        @click="openDialogFromNotification(currentPopupMessage)"
      >
        <VAvatar size="44" class="border bg-grey-lighten-3 shrink-0 position-relative">
          <VImg v-if="currentPopupMessage.peer_avatar" :src="currentPopupMessage.peer_avatar" referrerpolicy="no-referrer" />
          <VIcon v-else :icon="getChannelIcon(currentPopupMessage.channel)" :color="getChannelColor(currentPopupMessage.channel)" />
        </VAvatar>
        <div class="flex-grow-1 overflow-hidden">
          <div class="d-flex align-center gap-2 mb-1">
            <span class="font-weight-bold text-subtitle-2 text-truncate">{{ currentPopupMessage.peer_name || ('Собеседник ' + currentPopupMessage.peer_id) }}</span>
            <VChip size="x-small" :color="getChannelColor(currentPopupMessage.channel)" variant="tonal" class="font-weight-medium">
              {{ getChannelTitle(currentPopupMessage.channel) }}
            </VChip>
          </div>
          <div class="text-caption text-grey-darken-3 text-truncate">
            {{ currentPopupMessage.text || '[Вложение / Медиа]' }}
          </div>
        </div>
      </div>

      <template #actions>
        <VBtn
          color="primary"
          variant="flat"
          size="small"
          class="font-weight-bold"
          @click="openDialogFromNotification(currentPopupMessage)"
        >
          Открыть чат
        </VBtn>
        <VBtn
          icon
          size="x-small"
          variant="text"
          color="grey"
          @click="showNotificationPopup = false"
        >
          <VIcon icon="bx-x" size="20" />
        </VBtn>
      </template>
    </VSnackbar>

    <!-- Единое всплывающее меню меток диалогов (оптимизация производительности DOM) -->
    <VMenu
      v-model="showSingleTagMenu"
      :target="tagMenuTarget"
      :close-on-content-click="false"
      location="left"
    >
      <VCard v-if="activeTagMenuDialog" min-width="260" class="pa-3">
        <div class="text-subtitle-2 pa-1 border-bottom font-weight-bold">Метки диалога</div>
        <VList density="compact" class="py-1">
          <VListItem v-if="allTags.length === 0" class="text-grey text-caption py-1">
            Нет меток. Создайте первую ниже!
          </VListItem>
          <VListItem
            v-for="tag in allTags"
            :key="tag.id"
            class="px-1"
            @click="toggleDialogTag(activeTagMenuDialog, tag)"
          >
            <template #prepend>
              <VCheckboxBtn
                :model-value="(activeTagMenuDialog.tags || []).some(t => t.id === tag.id)"
                color="primary"
                density="compact"
              />
            </template>
            <VListItemTitle class="d-flex align-center">
              <VBadge dot :color="tag.color" class="mr-2" inline />
              {{ tag.name }}
            </VListItemTitle>
          </VListItem>
        </VList>

        <VDivider class="my-2" />
        <div class="text-caption text-grey mb-1 font-weight-medium">Создать новую метку:</div>
        <div class="d-flex align-center gap-1">
          <VTextField
            v-model="quickTagName"
            placeholder="Имя метки..."
            variant="outlined"
            density="compact"
            hide-details
            class="flex-grow-1"
          />
          <VBtn
            color="primary"
            size="small"
            icon
            :loading="creatingQuickTag"
            :disabled="!quickTagName.trim()"
            @click="createQuickTagAndAttach(activeTagMenuDialog)"
          >
            <VIcon icon="bx-plus" />
          </VBtn>
        </div>
      </VCard>
    </VMenu>
  </VCard>
</template>


<style scoped>
.multichat-container {
  overflow: hidden;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.dialog-item {
  content-visibility: auto;
  contain-intrinsic-size: 72px;
}

.text-pre-wrap {
  white-space: pre-wrap;
  word-break: break-word;
}

/* Подсветка найденных сообщений */
.message-search-highlight {
  box-shadow: 0 0 0 3px #ff9800, 0 0 15px rgba(255, 152, 0, 0.5) !important;
  animation: search-pulse 1.5s ease-in-out infinite alternate;
}

@keyframes search-pulse {
  0% { transform: scale(1); }
  100% { transform: scale(1.02); }
}

.in-chat-search-bar {
  background-color: #f1f5f9;
}

.chat-history-start-pill {
  background-color: rgba(100, 116, 139, 0.12);
  border: 1px dashed rgba(100, 116, 139, 0.25);
  font-weight: 500;
  user-select: none;
}

.search-result-item:hover {
  background-color: rgba(33, 150, 243, 0.08) !important;
}


/* ========================================================
   СВЕТЛАЯ ТЕМА (LIGHT THEME)
   ======================================================== */
.multichat-light {
  background-color: #ffffff;
  color: #0f172a;
}

.multichat-light .border-end {
  border-right: 1px solid #e2e8f0 !important;
}

.multichat-light .border-bottom {
  border-bottom: 1px solid #e2e8f0 !important;
}

.multichat-light .border-top {
  border-top: 1px solid #e2e8f0 !important;
}

.multichat-light .dialogs-sidebar,
.multichat-light .dialogs-list,
.multichat-light .dialogs-toolbar,
.multichat-light .chat-header,
.multichat-light .chat-input-area {
  background-color: #ffffff !important;
  color: #0f172a !important;
}

.multichat-light .dialog-item {
  background-color: #ffffff !important;
  border-bottom: 1px solid #f1f5f9 !important;
  color: #0f172a !important;
}

.multichat-light .dialog-item:hover {
  background-color: #f8fafc !important;
}

.multichat-light .dialog-item.v-list-item--active {
  background-color: #eff6ff !important;
  border-left: 4px solid #2563eb !important;
}

.multichat-light .pinned-item {
  background-color: #fffbeb !important;
  border-left: 4px solid #f59e0b !important;
}

.multichat-light .pinned-item:hover {
  background-color: #fef3c7 !important;
}

.multichat-light .pinned-item.dialog-unread {
  background-color: #fef2f2 !important;
  border-left: 4px solid #ef4444 !important;
}

.multichat-light .pinned-item.dialog-unread:hover {
  background-color: #fee2e2 !important;
}


.multichat-light .chat-messages {
  background-color: #f1f5f9;
  background-image: radial-gradient(#cbd5e1 0.75px, transparent 0.75px);
  background-size: 20px 20px;
  scroll-behavior: smooth;
}

.multichat-light .message-bubble {
  position: relative;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04);
}

.multichat-light .message-inbound {
  background-color: #ffffff !important;
  color: #0f172a !important;
  border: 1px solid #e2e8f0 !important;
  border-bottom-left-radius: 4px !important;
}

.multichat-light .message-inbound .message-text {
  color: #0f172a !important;
  font-size: 14px;
  font-weight: 450;
  line-height: 1.48;
}

.multichat-light .meta-inbound {
  color: #64748b !important;
  font-size: 11px !important;
  font-weight: 500;
}

.multichat-light .message-outbound {
  background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
  color: #ffffff !important;
  border: 1px solid rgba(29, 78, 216, 0.4) !important;
  border-bottom-right-radius: 4px !important;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25);
}

.multichat-light .message-outbound .message-text {
  color: #ffffff !important;
  font-size: 14px;
  font-weight: 450;
  line-height: 1.48;
  text-shadow: 0 0.5px 1px rgba(0, 0, 0, 0.15);
}

.multichat-light .meta-outbound {
  color: rgba(255, 255, 255, 0.88) !important;
  font-size: 11px !important;
  font-weight: 500;
}

.multichat-light .date-divider-pill {
  background-color: rgba(241, 245, 249, 0.95) !important;
  color: #334155 !important;
  border: 1px solid #cbd5e1 !important;
  font-size: 11.5px !important;
  font-weight: 600 !important;
  padding: 4px 14px !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

/* ========================================================
   ТЕМНАЯ ТЕМА (DARK THEME)
   ======================================================== */
.multichat-dark {
  background-color: #1e1e2d !important;
  color: #f1f5f9 !important;
}

.multichat-dark .border-end {
  border-right: 1px solid #2e2e42 !important;
}

.multichat-dark .border-bottom {
  border-bottom: 1px solid #2e2e42 !important;
}

.multichat-dark .border-top {
  border-top: 1px solid #2e2e42 !important;
}

.multichat-dark .dialogs-sidebar,
.multichat-dark .dialogs-list,
.multichat-dark .dialogs-toolbar,
.multichat-dark .chat-header,
.multichat-dark .chat-input-area {
  background-color: #1e1e2d !important;
  color: #f1f5f9 !important;
}

.multichat-dark .dialog-item {
  background-color: #1e1e2d !important;
  border-bottom: 1px solid #28283c !important;
  color: #f1f5f9 !important;
}

.multichat-dark .dialog-item:hover {
  background-color: #28283e !important;
}

.multichat-dark .dialog-item.v-list-item--active {
  background-color: #1e293b !important; /* Slate 800 */
  border-left: 4px solid #3b82f6 !important;
}

.multichat-dark .pinned-item {
  background-color: #2e2518 !important; /* Dark amber */
  border-left: 4px solid #f59e0b !important;
}

.multichat-dark .pinned-item:hover {
  background-color: #3b301c !important;
}

.multichat-dark .pinned-item.dialog-unread {
  background-color: #3b181e !important;
  border-left: 4px solid #ef4444 !important;
}

.multichat-dark .pinned-item.dialog-unread:hover {
  background-color: #4a1d25 !important;
}


.multichat-dark .chat-messages {
  background-color: #14141f !important;
  background-image: radial-gradient(#2d2d44 0.75px, transparent 0.75px) !important;
  background-size: 20px 20px;
  scroll-behavior: smooth;
}

.multichat-dark .message-bubble {
  position: relative;
  border-radius: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}

.multichat-dark .message-inbound {
  background-color: #252538 !important;
  color: #f8fafc !important;
  border: 1px solid #383852 !important;
  border-bottom-left-radius: 4px !important;
}

.multichat-dark .message-inbound .message-text {
  color: #f8fafc !important;
  font-size: 14px;
  font-weight: 450;
  line-height: 1.48;
}

.multichat-dark .meta-inbound {
  color: #94a3b8 !important;
  font-size: 11px !important;
  font-weight: 500;
}

.multichat-dark .message-outbound {
  background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
  color: #ffffff !important;
  border: 1px solid rgba(59, 130, 246, 0.5) !important;
  border-bottom-right-radius: 4px !important;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);
}

.multichat-dark .message-outbound .message-text {
  color: #ffffff !important;
  font-size: 14px;
  font-weight: 450;
  line-height: 1.48;
  text-shadow: 0 0.5px 1px rgba(0, 0, 0, 0.2);
}

.multichat-dark .meta-outbound {
  color: rgba(255, 255, 255, 0.88) !important;
  font-size: 11px !important;
  font-weight: 500;
}

.multichat-dark .date-divider-pill {
  background-color: #252538 !important;
  color: #cbd5e1 !important;
  border: 1px solid #383852 !important;
  font-size: 11.5px !important;
  font-weight: 600 !important;
  padding: 4px 14px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

/* ========================================================
   ВЫДЕЛЕНИЕ НЕПРОЧИТАННЫХ ДИАЛОГОВ (UNREAD DIALOGS)
   ======================================================== */
.multichat-light .dialog-unread {
  background-color: #f0fdf4 !important;
  border-left: 4px solid #10b981 !important;
}

.multichat-light .dialog-unread:hover {
  background-color: #dcfce7 !important;
}

.multichat-dark .dialog-unread {
  background-color: #162a22 !important;
  border-left: 4px solid #10b981 !important;
}

.multichat-dark .dialog-unread:hover {
  background-color: #1c362c !important;
}

.unread-avatar-dot {
  position: absolute;
  top: -2px;
  left: -2px;
  width: 12px;
  height: 12px;
  background-color: #ef4444;
  border: 2px solid #ffffff;
  border-radius: 50%;
  box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  animation: unread-pulse 1.8s infinite;
  z-index: 2;
}

@keyframes unread-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(239, 68, 68, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
  }
}



.gap-1 {
  gap: 4px;
}

.gap-2 {
  gap: 8px;
}

.gap-3 {
  gap: 12px;
}

.cursor-pointer {
  cursor: pointer;
}

.spin-icon {
  animation: spin 1.2s linear infinite;
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}

.qr-scan-laser {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, transparent, #ff9800, #ff5722, transparent);
  box-shadow: 0 0 8px rgba(255, 152, 0, 0.8);
  animation: qr-scan-anim 2.2s ease-in-out infinite;
}

@keyframes qr-scan-anim {
  0% {
    top: 5%;
    opacity: 0.2;
  }
  50% {
    top: 92%;
    opacity: 1;
  }
  100% {
    top: 5%;
    opacity: 0.2;
  }
}

.channel-badge-avatar {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  z-index: 1;
}

.tab-bot-badge {
  position: absolute;
  top: -4px;
  right: -8px;
  font-size: 7px;
  font-weight: 800;
  background-color: #E64A19;
  color: #ffffff;
  padding: 1px 3px;
  border-radius: 4px;
  line-height: 1;
}

/* Стили панели источников и чипсов */
.sources-panel {
  user-select: none;
}
.sources-chips-scroll {
  scrollbar-width: thin;
  white-space: nowrap;
}
.sources-chips-scroll::-webkit-scrollbar {
  height: 4px;
}
.sources-chips-scroll::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
  border-radius: 4px;
}
.source-chip {
  flex-shrink: 0;
  transition: all 0.15s ease-in-out;
}
.source-unread-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: #f44336;
  color: #fff;
  border-radius: 10px;
  padding: 0 4px;
  font-size: 10px;
  font-weight: 700;
  min-width: 15px;
  height: 15px;
  line-height: 1;
}

/* Эстетичные стили мультичата в стилистике ИИ-агентов */
.multichat-container {
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(var(--v-border-color), 0.12) !important;
  border-radius: 12px !important;
  overflow: hidden;
}

.dialog-item.active-dialog,
.dialog-item.active {
  background: rgba(var(--v-theme-primary), 0.1) !important;
  border-left: 3px solid rgb(var(--v-theme-primary)) !important;
  transition: all 0.2s ease;
}

.multichat-light .message-outbound,
.multichat-dark .message-outbound {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)), #556ee6) !important;
  color: #ffffff !important;
  border-radius: 16px 16px 4px 16px !important;
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.22);
}

.multichat-light .message-inbound {
  background: #ffffff !important;
  border: 1px solid rgba(15, 23, 42, 0.08) !important;
  border-radius: 16px 16px 16px 4px !important;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}

.multichat-dark .message-inbound {
  background: #2b2c40 !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
  border-radius: 16px 16px 16px 4px !important;
}

.chat-input-area {
  background: rgba(var(--v-theme-surface), 0.95);
  backdrop-filter: blur(8px);
}

/* ========================================================
   АДАПТИВНОСТЬ ДЛЯ МОБИЛЬНЫХ УСТРОЙСТВ (MOBILE RESPONSIVE)
   ======================================================== */
@media (max-width: 768px) {
  .multichat-container {
    height: calc(100vh - 75px) !important;
    border-radius: 0 !important;
  }
  .dialogs-sidebar {
    width: 100% !important;
    min-width: 100% !important;
    border-right: none !important;
  }
  .dialogs-sidebar.mobile-hidden {
    display: none !important;
  }
  .chat-area {
    width: 100% !important;
    min-width: 100% !important;
  }
  .chat-area.mobile-hidden {
    display: none !important;
  }
  .chat-header {
    padding: 8px 12px !important;
  }
  .chat-header .d-flex.align-center.gap-2 {
    overflow-x: auto;
    max-width: 100%;
    padding-bottom: 2px;
  }
  .chat-input-area {
    padding: 8px 10px !important;
  }
  .message-content {
    max-width: 85% !important;
  }
}

</style>



