import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { authState, fetchMe, isCourierUser } from '@/utils/auth'

export const useChatStore = defineStore('chat', () => {
  const contacts = ref([])
  const messages = ref([])
  const activeContactId = ref(null) // 0 for group, or user_id
  const isDrawerOpen = ref(false)
  const ws = ref(null)
  const currentUserId = computed(() => authState.user?.id || null)
  const isCourier = computed(() => isCourierUser())
  
  // Уведомления об операциях
  const notifications = ref([])
  const unreadNotificationsCount = computed(() => notifications.value.filter(n => !n.is_read).length)

  const paymentNotification = ref({ show: false, amount: 0, method: '', customer: '', orderId: null, timestamp: 0 })
  const orderNotification = ref({ show: false, amount: 0, customer: '', orderNumber: null, orderId: null })
  const courierNotification = ref({ show: false, orderNumber: null, address: '', amount: 0 })
  const orderCancelledNotification = ref({ show: false, orderNumber: null, customer: '' })
  const orderChangedNotification = ref({ show: false, orderNumber: null, customer: '' })
  
  // Постоянное всплывающее окно о доставке заказа (Snackbar :timeout="-1")
  const orderDeliveredAlert = ref({
    show: false,
    orderNumber: null,
    orderId: null,
    courierName: '',
    address: '',
    amount: 0,
    customerName: '',
    actualTime: '',
    url: '/admin/orders',
  })
  
  // Выделенное всплывающее окно для курьера (10 событий)
  const courierAlert = ref({
    show: false,
    type: '',
    title: '',
    body: '',
    orderNumber: null,
    orderId: null,
    url: '/pers/courier',
    address: '',
    amount: 0,
    cookingTimeMinutes: null,
    status: '',
    timestamp: null,
  })

  const lastOrderUpdate = ref(null)
  
  const notificationSettings = ref(null)
  const orderRepeatIntervalId = ref(null)

  // =========================================================================
  // РЕАКТИВНЫЙ КЭШ СООБЩЕНИЙ МУЛЬТИЧАТА (МГНОВЕННЫЙ ДОСТУП 0 мс)
  // =========================================================================
  const messagesCache = ref(new Map())

  function isMaxChannel(ch) {
    return ch === 'max' || ch === 'max_user' || ch === 'max_bot' || ch === 'max_account' || ch === 'max_bridge'
  }
  function isVkChannel(ch) {
    return ch === 'vk' || ch === 'vk_user'
  }

  const getCacheKey = (channel, peerId) => {
    if (!channel || !peerId) return ''
    let ch = String(channel).toLowerCase()
    if (isMaxChannel(ch)) ch = 'max'
    else if (isVkChannel(ch)) ch = 'vk'
    return `${ch}_${String(peerId)}`
  }

  const getCachedMessages = (channel, peerId) => {
    const key = getCacheKey(channel, peerId)
    if (!key) return []
    return messagesCache.value.get(key) || []
  }

  const setCachedMessages = (channel, peerId, msgs) => {
    const key = getCacheKey(channel, peerId)
    if (!key) return
    const list = Array.isArray(msgs) ? [...msgs] : []
    messagesCache.value.set(key, list)
  }

  const appendMessageToCache = (channel, peerId, msg) => {
    const key = getCacheKey(channel, peerId)
    if (!key || !msg) return
    const current = messagesCache.value.get(key) || []
    const msgIdStr = String(msg.id || msg.external_id || '')
    const exists = current.some(m => {
      if (msgIdStr && (String(m.id) === msgIdStr || String(m.external_id) === msgIdStr)) return true
      if (m.text === msg.text && Math.abs(new Date(m.created_at || 0) - new Date(msg.created_at || 0)) < 2000) return true
      return false
    })
    if (!exists) {
      current.push(msg)
      messagesCache.value.set(key, [...current])
    }
  }

  // =========================================================================
  // ПЛАВАЮЩИЕ ОКНА ДИАЛОГОВ (МУЛЬТИЧАТ REAL-TIME НА СТРАНИЦЕ ЗАКАЗОВ)
  // =========================================================================
  const floatingChats = ref([])

  const openFloatingChat = async (channel, peerId, peerName = null, peerAvatar = null) => {
    if (!channel || !peerId) return
    const pIdStr = String(peerId)
    let chat = floatingChats.value.find(c => 
      (c.channel === channel || (isMaxChannel(c.channel) && isMaxChannel(channel)) || (isVkChannel(c.channel) && isVkChannel(channel))) && 
      String(c.peer_id) === pIdStr
    )
    
    // Мгновенная выдача из кэша за 0 мс
    const cached = getCachedMessages(channel, pIdStr)

    if (!chat) {
      chat = {
        channel: channel,
        peer_id: pIdStr,
        peer_name: peerName || `Чат ${pIdStr}`,
        peer_avatar: peerAvatar || null,
        phone: null,
        messages: cached.length > 0 ? [...cached] : [],
        replyText: '',
        isMinimized: false,
        loading: cached.length === 0,
        sending: false
      }
      floatingChats.value.push(chat)
    } else {
      chat.isMinimized = false
      if (cached.length > 0 && chat.messages.length === 0) {
        chat.messages = [...cached]
      }
    }

    try {
      if (chat.messages.length === 0) {
        chat.loading = true
      }
      const res = await axios.get(`/api/v1/multichat/dialogs/${channel}/${pIdStr}/history`, {
        params: { limit: 15 },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`
        }
      })
      if (Array.isArray(res.data)) {
        chat.messages = res.data
        setCachedMessages(channel, pIdStr, res.data)
        if (res.data.length > 0) {
          const lastM = res.data[res.data.length - 1]
          if (lastM.peer_name && !lastM.peer_name.toLowerCase().startsWith('пользователь')) {
            chat.peer_name = lastM.peer_name
          }
          if (lastM.peer_avatar) {
            chat.peer_avatar = lastM.peer_avatar
          }
        }
      }
    } catch (e) {
      console.warn('[FloatingChat] History load error:', e)
    } finally {
      chat.loading = false
    }
  }

  const closeFloatingChat = (channel, peerId) => {
    const pIdStr = String(peerId)
    floatingChats.value = floatingChats.value.filter(c => !(c.channel === channel && String(c.peer_id) === pIdStr))
  }

  const toggleMinimizeFloatingChat = (channel, peerId) => {
    const pIdStr = String(peerId)
    const chat = floatingChats.value.find(c => c.channel === channel && String(c.peer_id) === pIdStr)
    if (chat) {
      chat.isMinimized = !chat.isMinimized
    }
  }

  const sendFloatingMessage = async (channel, peerId, text) => {
    if (!text || !text.trim()) return
    const pIdStr = String(peerId)
    const chat = floatingChats.value.find(c => c.channel === channel && String(c.peer_id) === pIdStr)
    if (!chat) return

    const cleanText = text.trim()
    chat.sending = true
    try {
      await axios.post(`/api/v1/multichat/dialogs/${channel}/${pIdStr}/send`, { text: cleanText }, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`
        }
      })
      chat.replyText = ''
      
      const outboundMsg = {
        id: Date.now(),
        channel: channel,
        peer_id: pIdStr,
        peer_name: chat.peer_name,
        peer_avatar: chat.peer_avatar,
        direction: 'outbound',
        text: cleanText,
        created_at: new Date().toISOString(),
        is_read: true
      }
      chat.messages.push(outboundMsg)
      appendMessageToCache(channel, pIdStr, outboundMsg)
    } catch (e) {
      console.error('[FloatingChat] Send error:', e)
    } finally {
      chat.sending = false
    }
  }

  const handleWsMultichatMessage = (msgData) => {
    if (!msgData || !msgData.peer_id) return
    const pIdStr = String(msgData.peer_id)
    const channel = msgData.channel || 'vk'

    // Мгновенно сохраняем входящее/исходящее сообщение в кэш
    appendMessageToCache(channel, pIdStr, msgData)

    let chat = floatingChats.value.find(c => 
      (c.channel === channel || (isMaxChannel(c.channel) && isMaxChannel(channel)) || (isVkChannel(c.channel) && isVkChannel(channel))) && 
      String(c.peer_id) === pIdStr
    )

    if (chat) {
      if (!chat.messages.some(m => String(m.id) === String(msgData.id))) {
        chat.messages.push(msgData)
      }
      chat.isMinimized = false
    }
  }

  const fetchNotificationSettings = async () => {
    // Пробуем сначала загрузить из кэша
    const cached = localStorage.getItem('user_notification_settings')
    if (cached) {
      try {
        notificationSettings.value = JSON.parse(cached)
      } catch (e) {}
    }
    
    try {
      const response = await axios.get('/api/v1/notifications/settings', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      })
      notificationSettings.value = response.data
      localStorage.setItem('user_notification_settings', JSON.stringify(response.data))
    } catch (error) {
      console.error('Failed to fetch notification settings:', error)
    }
  }

  const playNotificationSound = (filename) => {
    if (!filename) return
    const audio = new Audio(`/sounds/${filename}`)
    audio.play().catch(err => {
      console.warn('[Sound] Playback blocked by browser policy:', err)
    })
  }

  const defaultSoundForCourierEvent = (type) => {
    const map = {
      courier_order_assigned: 'chime.mp3',
      courier_cooking_time_set: 'bell.mp3',
      courier_cooking_time_changed: 'click.mp3',
      courier_status_changed: 'bell.mp3',
      courier_amount_changed: 'cash.mp3',
      courier_address_changed: 'doorbell.mp3',
      courier_changed_to_pickup: 'branch.mp3',
      courier_removed_from_delivery: 'error.mp3',
      courier_unassigned: 'sonar.mp3',
      courier_delivery_time_changed: 'water.mp3',
      courier_delivery: 'chime.mp3',
      delivery_assigned: 'chime.mp3',
    }
    return map[type] || 'bell.mp3'
  }

  const getCourierEventTitle = (type, data = {}) => {
    switch (type) {
      case 'courier_order_assigned': return 'Назначен заказ на доставку'
      case 'courier_cooking_time_set': return 'Установлено время приготовления'
      case 'courier_cooking_time_changed': return 'Изменено время приготовления'
      case 'courier_status_changed':
        if (data.status === 'ready') return 'Заказ готов к выдаче!'
        if (data.status === 'cancelled') return 'Заказ отменен!'
        if (data.courier_notification_status === 'accepted' || data.status === 'accepted') {
          return 'Заказ принят курьером'
        }
        return 'Изменение статуса заказа'
      case 'courier_amount_changed': return 'Изменение суммы заказа'
      case 'courier_address_changed': return 'Изменение адреса доставки'
      case 'courier_changed_to_pickup': return 'Заказ переведен на самовывоз!'
      case 'courier_removed_from_delivery': return 'Заказ убран из доставки!'
      case 'courier_unassigned': return 'Заказ снят с ваших доставок'
      case 'courier_delivery_time_changed': return 'Изменение времени доставки'
      default: return 'Уведомление по доставке'
    }
  }

  const getCourierEventBody = (type, data = {}) => {
    const num = data.order_number || data.order_num || data.order_id
    switch (type) {
      case 'courier_order_assigned':
        return `Заказ #${num} | Сумма: ${data.amount || 0} ₽ | Адрес: ${data.address || 'Не указан'}`
      case 'courier_cooking_time_set':
        return `Заказ #${num}. Время на кухне: ${data.cooking_time_minutes || 0} мин.`
      case 'courier_cooking_time_changed':
        return `Заказ #${num}. Новое время кухни: ${data.cooking_time_minutes || 0} мин.`
      case 'courier_status_changed':
        if (data.status === 'ready') return `Заказ #${num} приготовлен кухней. Можно забирать!`
        if (data.status === 'cancelled') return `Заказ #${num} был отменен!`
        if (data.courier_notification_status === 'accepted' || data.status === 'accepted') {
          return data.courier_name ? `Курьер ${data.courier_name} принял заказ #${num}` : `Заказ #${num} принят курьером`
        }
        return `Обновление по заказу #${num}`
      case 'courier_amount_changed':
        return `Сумма заказа #${num} изменена: ${data.amount || 0} ₽`
      case 'courier_address_changed':
        return `Адрес заказа #${num} изменен: ${data.address || ''}`
      case 'courier_changed_to_pickup':
        return `Заказ #${num} переведен на самовывоз. Доставка отменена.`
      case 'courier_removed_from_delivery':
        return `Заказ #${num} снят с доставки.`
      case 'courier_unassigned':
        return `Заказ #${num} убран из вашего списка доставок.`
      case 'courier_delivery_time_changed':
        return `Время доставки заказа #${num} было изменено.`
      default:
        return data.body || `Обновление по заказу #${num}`
    }
  }

  const fetchNotifications = async () => {
    try {
      const response = await axios.get('/api/v1/notifications', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      })
      notifications.value = response.data
    } catch (error) {
      console.error('Failed to fetch notifications history:', error)
    }
  }

  const markNotificationRead = async (id) => {
    try {
      await axios.post(`/api/v1/notifications/${id}/read`, {}, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      })
      const notif = notifications.value.find(n => n.id === id)
      if (notif) notif.is_read = true
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
    }
  }

  const markAllNotificationsRead = async () => {
    try {
      await axios.post('/api/v1/notifications/read-all', {}, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      })
      notifications.value.forEach(n => n.is_read = true)
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error)
    }
  }

  const addLocalNotification = (notif) => {
    notifications.value.unshift({
      id: Date.now(),
      title: notif.title,
      body: notif.body,
      url: notif.url,
      event_type: notif.event_type,
      is_read: false,
      created_at: new Date().toISOString()
    })
    // Ограничиваем локальный массив 40 элементами
    if (notifications.value.length > 40) {
      notifications.value = notifications.value.slice(0, 40)
    }
  }

  // Повторяющиеся звуки для новых заказов
  const startOrderSoundRepeat = () => {
    if (orderRepeatIntervalId.value) return
    const intervalSec = notificationSettings.value?.new_order_repeat_interval || 30
    orderRepeatIntervalId.value = setInterval(() => {
      if (orderNotification.value.show) {
        playNotificationSound(notificationSettings.value.new_order_sound_file || 'bell.mp3')
      } else {
        stopOrderSoundRepeat()
      }
    }, intervalSec * 1000)
  }

  const stopOrderSoundRepeat = () => {
    if (orderRepeatIntervalId.value) {
      clearInterval(orderRepeatIntervalId.value)
      orderRepeatIntervalId.value = null
    }
  }

  const fetchMe = async () => {
    if (currentUserId.value) return
    try {
      const response = await axios.get('/api/v1/users/me', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      })

      currentUserId.value = response.data.id
    } catch (error) {
      console.error('Failed to fetch profile:', error)
    }
  }

  const unreadCount = computed(() => {
    return contacts.value.reduce((acc, c) => acc + (c.unread_count || 0), 0)
  })

  const fetchContacts = async () => {
    try {
      const response = await axios.get('/api/v1/chat/contacts', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      })

      contacts.value = response.data
    } catch (error) {
      console.error('Failed to fetch contacts:', error)
    }
  }

  const fetchMessages = async (contactId, isGroup) => {
    try {
      const response = await axios.get('/api/v1/chat/messages', {
        params: {
          receiver_id: contactId > 0 ? contactId : undefined,
          is_group: isGroup,
          limit: 100,
        },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      })

      messages.value = response.data.messages
    } catch (error) {
      console.error('Failed to fetch messages:', error)
    }
  }

  const markRead = async (contactId, isGroup) => {
    const isGrp = !!isGroup
    if (contactId === null || contactId === undefined) {
      if (!isGrp) return
    }
    try {
      await axios.post('/api/v1/chat/read', {
        sender_id: contactId > 0 ? contactId : undefined,
        is_group: isGrp,
      }, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      })

      const contact = contacts.value.find(c => c.id === contactId)
      if (contact) contact.unread_count = 0
    } catch (error) {
      // Игнорируем ошибки markRead
    }
  }

  const sendMessage = (content, receiverId, isGroup) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({
        action: 'send',
        content,
        receiver_id: receiverId > 0 ? receiverId : null,
        is_group: isGroup,
      }))
    }
  }

  const showNativeNotification = async (title, body, url, tag) => {
    // Показываем нативное системное уведомление во всех режимах (даже при открытой вкладке),
    // если оно разрешено в системе и настройках.
    if (!('Notification' in window) || Notification.permission !== 'granted') return

    const options = {
      body: body,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      vibrate: [200, 100, 200],
      tag: tag || 'admin-notification',
      data: { url: url }
    }

    if ('serviceWorker' in navigator) {
      try {
        const reg = await navigator.serviceWorker.ready
        if (reg && 'showNotification' in reg) {
          await reg.showNotification(title, options)
          return
        }
      } catch (err) {
        console.warn('[Notification] SW showNotification failed, falling back to window.Notification:', err)
      }
    }

    try {
      const notif = new Notification(title, options)
      notif.onclick = () => {
        window.focus()
        if (url) {
          window.location.href = url
        }
        notif.close()
      }
    } catch (err) {
      console.warn('[Notification] Failed to show native notification in main thread:', err)
    }
  }

  const urlBase64ToUint8Array = (base64String) => {
    const padding = '='.repeat((4 - base64String.length % 4) % 4)
    const base64 = (base64String + padding)
      .replace(/\-/g, '+')
      .replace(/_/g, '/')

    const rawData = window.atob(base64)
    const outputArray = new Uint8Array(rawData.length)

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i)
    }
    return outputArray
  }

  const autoSubscribeToPush = async () => {
    if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) return
    if (Notification.permission !== 'granted') return

    try {
      const reg = await navigator.serviceWorker.ready
      const existingSub = await reg.pushManager.getSubscription()

      const keyRes = await axios.get('/api/v1/notifications/vapid-public-key', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      })
      const publicVapidKey = keyRes.data.public_key
      if (!publicVapidKey) return

      let sub = existingSub
      if (!sub) {
        sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(publicVapidKey)
        })
      }

      const subJson = sub.toJSON()
      await axios.post('/api/v1/notifications/subscribe', {
        endpoint: subJson.endpoint,
        keys: {
          p256dh: subJson.keys.p256dh,
          auth: subJson.keys.auth
        }
      }, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        }
      })
      console.log('[Push] Auto-subscribed successfully')
    } catch (e) {
      console.warn('[Push] Auto-subscription failed:', e)
    }
  }

  const connectWs = () => {
    if (ws.value && (ws.value.readyState === WebSocket.OPEN || ws.value.readyState === WebSocket.CONNECTING)) return

    const token = localStorage.getItem('access_token')
    if (!token) return

    fetchMe()
    fetchNotificationSettings()

    // Запрашиваем права на уведомления, если они еще не приняты
    if ('Notification' in window) {
      if (Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
          console.log('[Notification] Permission requested:', permission)
          if (permission === 'granted') {
            autoSubscribeToPush()
          }
        })
      } else if (Notification.permission === 'granted') {
        autoSubscribeToPush()
      }
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/chat/ws?token=${token}`

    ws.value = new WebSocket(wsUrl)

    ws.value.onmessage = event => {
      const data = JSON.parse(event.data)
      
      // Перехват событий заказа для live-обновления страниц в реальном времени
      const orderEvents = [
        'new_order', 'order_created', 'order_cancelled', 'order_changed', 
        'order_updated', 'orders_synced', 'order_status_changed', 'orders_batch_update',
        'delivery_unassigned', 'delivery_assigned', 
        'change_cooking_time', 'change_items', 
        'change_amount', 'change_payment', 'courier_delivery',
        'courier_order_assigned', 'courier_cooking_time_set',
        'courier_cooking_time_changed', 'courier_status_changed',
        'courier_amount_changed', 'courier_address_changed',
        'courier_changed_to_pickup', 'courier_removed_from_delivery',
        'courier_unassigned', 'courier_delivery_time_changed',
        'order_delivered'
      ]
      if (orderEvents.includes(data.type)) {
        lastOrderUpdate.value = {
          type: data.type,
          order_id: data.order_id || data.order_num || null,
          timestamp: Date.now()
        }
        window.dispatchEvent(new CustomEvent('order-updated-event', { detail: data }))
      }

      // =========================================================================
      // ГЛОБАЛЬНЫЕ МАСТЕР-ПЕРЕКЛЮЧАТЕЛИ УВЕДОМЛЕНИЙ В БРАУЗЕРЕ
      // =========================================================================
      // 1. Отключить уведомления в браузере для всех!
      if (notificationSettings.value?.disable_browser_notifications_all) {
        return
      }

      // 2. Отключить уведомления браузера для курьеров
      if (isCourier.value && notificationSettings.value?.disable_browser_notifications_couriers) {
        return
      }

      // =========================================================================
      // 0. ОПОВЕЩЕНИЕ О ДОСТАВКЕ ЗАКАЗА (ДЛЯ АДМИНИСТРАТОРОВ / ОПЕРАТОРОВ)
      // =========================================================================
      if (data.type === 'order_delivered') {
        if (isCourier.value) {
          return // Для курьеров это уведомление НЕ нужно
        }

        const orderNum = data.order_number || data.order_num || data.order_id
        const courier = data.courier_name || 'Не назначен'
        const addr = data.delivery_address || data.address || 'Не указан'
        const amt = data.total_amount || data.amount || 0
        const cust = data.customer_name || 'Гость'
        const actTime = data.actual_time || new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
        const targetUrl = '/admin/orders'

        // Стилизованное постоянное всплывающее окно (не исчезает пока не закроют)
        orderDeliveredAlert.value = {
          show: true,
          orderNumber: orderNum,
          orderId: data.order_id,
          courierName: courier,
          address: addr,
          amount: amt,
          customerName: cust,
          actualTime: actTime,
          url: targetUrl,
        }

        addLocalNotification({
          title: `Заказ #${orderNum} доставлен!`,
          body: `Курьер: ${courier} | Адрес: ${addr} | Сумма: ${amt} ₽`,
          url: targetUrl,
          event_type: 'order_delivered'
        })

        if (notificationSettings.value?.order_delivered_push_enabled !== false) {
          showNativeNotification(
            `Заказ #${orderNum} доставлен!`,
            `Курьер: ${courier} | Адрес: ${addr} | Сумма: ${amt} ₽`,
            targetUrl,
            `order-delivered-${data.order_id || Date.now()}`
          )
        }

        if (notificationSettings.value?.order_delivered_sound_enabled !== false) {
          playNotificationSound(notificationSettings.value?.order_delivered_sound_file || 'chime.mp3')
        }
        return
      }

      // =========================================================================
      // 1. ВЫДЕЛЕННЫЕ УВЕДОМЛЕНИЯ КУРЬЕРА (10 ТИПОВ) - ВСПЛЫВАЮЩЕЕ ОКНО, ЗВУК, ПУШ
      // =========================================================================
      const courierEventTypes = [
        'courier_order_assigned',
        'courier_cooking_time_set',
        'courier_cooking_time_changed',
        'courier_status_changed',
        'courier_amount_changed',
        'courier_address_changed',
        'courier_changed_to_pickup',
        'courier_removed_from_delivery',
        'courier_unassigned',
        'courier_delivery_time_changed',
        'courier_delivery',
        'delivery_assigned'
      ]

      if (courierEventTypes.includes(data.type)) {
        // Если это подтверждение принятия заказа курьером (кнопка в приложении, реакция или сообщение),
        // это не событие кухни для показа всплывающего алерта курьеру
        if (data.courier_notification_status || data.status === 'accepted') {
          return
        }

        const myId = authState.user?.id
        if (data.target_user_id && myId && Number(data.target_user_id) !== Number(myId)) {
          return // Уведомление адресовано другому курьеру
        }

        let normType = data.type
        if (normType === 'courier_delivery' || normType === 'delivery_assigned') {
          normType = 'courier_order_assigned'
        }

        const title = data.title || getCourierEventTitle(normType, data)
        const body = data.body || getCourierEventBody(normType, data)
        const orderNum = data.order_number || data.order_num || data.order_id
        const targetUrl = data.url || '/pers/courier'

        // Интерактивное всплывающее окно в браузере (Pop-up Toast / Alert)
        courierAlert.value = {
          show: true,
          type: normType,
          title: title,
          body: body,
          orderNumber: orderNum,
          orderId: data.order_id,
          url: targetUrl,
          address: data.address || '',
          amount: data.amount || 0,
          cookingTimeMinutes: data.cooking_time_minutes || null,
          status: data.status || '',
          timestamp: Date.now()
        }

        // Запись в колокольчик непрочитанных
        addLocalNotification({
          title: title,
          body: body,
          url: targetUrl,
          event_type: normType
        })

        // Нативное браузерное Web Push / Notification
        const pushEnabled = notificationSettings.value?.[`${normType}_push_enabled`] !== false
        if (pushEnabled) {
          showNativeNotification(
            title,
            body,
            targetUrl,
            `courier-${normType}-${data.order_id || Date.now()}`
          )
        }

        // Воспроизведение звука согласно настройкам
        const soundEnabled = notificationSettings.value?.[`${normType}_sound_enabled`] !== false
        if (soundEnabled) {
          const soundFile = notificationSettings.value?.[`${normType}_sound_file`] || data.sound_file || defaultSoundForCourierEvent(normType)
          playNotificationSound(soundFile)
        }
        return
      }

      // =========================================================================
      // 2. ДЛЯ КУРЬЕРОВ СКРЫВАЕМ ВСЕ БАЗОВЫЕ ОБЩИЕ УВЕДОМЛЕНИЯ АДМИНКИ
      // =========================================================================
      if (isCourier.value) {
        const generalAdminEvents = [
          'new_bank_payment', 'new_order', 'delivery_unassigned', 
          'order_cancelled', 'order_changed', 'change_cooking_time', 
          'change_items', 'change_amount', 'change_payment', 'change_address'
        ]
        if (generalAdminEvents.includes(data.type)) {
          const myId = authState.user?.id
          if (!data.target_user_id || Number(data.target_user_id) !== Number(myId)) {
            return // Полная тишина: курьер не видит чужих заказов, оплат и отмен
          }
        }
      }

      // Проверка области видимости (scope) уведомлений об изменениях в заказах
      const isOrderChangeType = [
        'order_changed', 'order_cancelled', 'change_cooking_time', 
        'change_items', 'change_amount', 'change_payment', 'change_address'
      ].includes(data.type)

      if (isOrderChangeType) {
        const scope = notificationSettings.value?.order_changed_scope || 'all'
        let shouldNotify = true
        if (scope === 'pickup' && data.order_type !== 'Самовывоз') {
          shouldNotify = false
        } else if (scope === 'delivery' && data.order_type !== 'Доставка') {
          shouldNotify = false
        } else if (scope === 'courier_assigned' && (data.order_type !== 'Доставка' || !data.courier_name || data.courier_name === 'Не назначен' || data.courier_name === '')) {
          shouldNotify = false
        }

        if (!shouldNotify) {
          return // Прерываем обработку: звук, пуш и локальный лог колокольчика не сработают
        }
      }
      if (data.type === 'new_bank_payment') {
        paymentNotification.value = {
          show: true,
          amount: data.amount,
          method: data.method,
          customer: data.customer,
          orderId: data.order_id,
          timestamp: Date.now()
        }
        addLocalNotification({
          title: 'Поступление оплаты',
          body: `Сумма: ${data.amount} ₽, способ: ${data.method}, клиент: ${data.customer}`,
          url: `/admin/bank/tbank-payments`,
          event_type: 'new_payment'
        })
        if (notificationSettings.value?.new_payment_push_enabled) {
          showNativeNotification(
            'Поступление оплаты',
            `Сумма: ${data.amount} ₽, способ: ${data.method}, клиент: ${data.customer}`,
            '/admin/bank/tbank-payments',
            `payment-${data.order_id || Date.now()}`
          )
        }
        if (notificationSettings.value?.new_payment_sound_enabled) {
          playNotificationSound(notificationSettings.value.new_payment_sound_file || 'cash.mp3')
        }
        return
      }
      
      // 2. Новый заказ
      if (data.type === 'new_order') {
        orderNotification.value = {
          show: true,
          amount: data.total_sum,
          customer: data.customer_name || 'Гость',
          orderNumber: data.order_number,
          orderId: data.order_id
        }
        addLocalNotification({
          title: `Новый заказ #${data.order_number}`,
          body: `Сумма: ${data.total_sum} ₽, клиент: ${data.customer_name || 'Гость'}`,
          url: `/admin/orders`,
          event_type: 'new_order'
        })
        if (notificationSettings.value?.new_order_push_enabled) {
          showNativeNotification(
            `Новый заказ #${data.order_number}`,
            `Сумма: ${data.total_sum} ₽, клиент: ${data.customer_name || 'Гость'}`,
            '/admin/orders',
            `order-${data.order_id}`
          )
        }
        if (notificationSettings.value?.new_order_sound_enabled) {
          playNotificationSound(notificationSettings.value.new_order_sound_file || 'bell.mp3')
          if (notificationSettings.value?.new_order_repeat_enabled) {
            startOrderSoundRepeat()
          }
        }
        return
      }

      // 3. Назначение доставки курьеру
      if (data.type === 'courier_delivery') {
        courierNotification.value = {
          show: true,
          orderNumber: data.order_num,
          address: data.address,
          amount: data.amount
        }
        addLocalNotification({
          title: `Назначение курьера #${data.order_num}`,
          body: `Адрес: ${data.address}, сумма: ${data.amount} ₽`,
          url: `/pers/courier`,
          event_type: 'courier_delivery'
        })
        if (notificationSettings.value?.courier_delivery_push_enabled) {
          showNativeNotification(
            `Назначение курьера #${data.order_num}`,
            `Адрес: ${data.address}, сумма: ${data.amount} ₽`,
            '/pers/courier',
            `courier-${data.order_num}`
          )
        }
        if (notificationSettings.value?.courier_delivery_sound_enabled) {
          playNotificationSound(notificationSettings.value.courier_delivery_sound_file || 'chime.mp3')
        }
        return
      }

      // 4. Отмена заказа
      if (data.type === 'order_cancelled') {
        orderCancelledNotification.value = {
          show: true,
          orderNumber: data.order_number,
          customer: data.customer_name || 'Гость'
        }
        addLocalNotification({
          title: `Заказ #${data.order_number} отменен`,
          body: `Клиент: ${data.customer_name || 'Гость'}`,
          url: `/admin/orders`,
          event_type: 'order_cancelled'
        })
        if (notificationSettings.value?.order_cancelled_push_enabled) {
          showNativeNotification(
            `Заказ #${data.order_number} отменен`,
            `Клиент: ${data.customer_name || 'Гость'}`,
            '/admin/orders',
            `order-cancel-${data.order_number}`
          )
        }
        if (notificationSettings.value?.order_cancelled_sound_enabled) {
          playNotificationSound(notificationSettings.value.order_cancelled_sound_file || 'bell.mp3')
        }
        return
      }

      // 5. Изменение заказа
      if (data.type === 'order_changed') {
        orderChangedNotification.value = {
          show: true,
          orderNumber: data.order_number,
          customer: data.customer_name || 'Гость'
        }
        addLocalNotification({
          title: `Заказ #${data.order_number} изменен`,
          body: `Клиент: ${data.customer_name || 'Гость'}`,
          url: `/admin/orders`,
          event_type: 'order_changed'
        })
        if (notificationSettings.value?.order_changed_push_enabled) {
          showNativeNotification(
            `Заказ #${data.order_number} изменен`,
            `Клиент: ${data.customer_name || 'Гость'}`,
            '/admin/orders',
            `order-change-${data.order_number}`
          )
        }
        if (notificationSettings.value?.order_changed_sound_enabled) {
          playNotificationSound(notificationSettings.value.order_changed_sound_file || 'bell.mp3')
        }
        return
      }

      // 5.1. Новая свободная доставка (без курьера)
      if (data.type === 'delivery_unassigned') {
        addLocalNotification({
          title: 'Новая свободная доставка!',
          body: `Сумма: ${data.total_sum} ₽ | Адрес: ${data.address}`,
          url: `/admin/orders`,
          event_type: 'delivery_unassigned'
        })
        if (notificationSettings.value?.delivery_unassigned_push_enabled) {
          showNativeNotification(
            'Новая свободная доставка!',
            `Сумма: ${data.total_sum} ₽ | Адрес: ${data.address}`,
            '/admin/orders',
            `unassigned-${data.order_id}`
          )
        }
        if (notificationSettings.value?.delivery_unassigned_sound_enabled) {
          playNotificationSound(notificationSettings.value.delivery_unassigned_sound_file || 'chime.mp3')
        }
        return
      }

      // 5.2. Назначена доставка (для конкретного курьера)
      if (data.type === 'delivery_assigned') {
        if (data.target_user_id && data.target_user_id !== currentUserId.value) {
          return
        }
        addLocalNotification({
          title: 'Вам назначена доставка!',
          body: `Адрес: ${data.address} | Сумма: ${data.amount} ₽`,
          url: `/pers/courier`,
          event_type: 'delivery_assigned'
        })
        if (notificationSettings.value?.delivery_assigned_push_enabled) {
          showNativeNotification(
            'Вам назначена доставка!',
            `Адрес: ${data.address} | Сумма: ${data.amount} ₽`,
            '/pers/courier',
            `assigned-${data.order_id}`
          )
        }
        if (notificationSettings.value?.delivery_assigned_sound_enabled) {
          playNotificationSound(notificationSettings.value.delivery_assigned_sound_file || 'chime.mp3')
        }
        return
      }

      // 5.3. Изменение времени готовности
      if (data.type === 'change_cooking_time') {
        addLocalNotification({
          title: `Время готовности заказа #${data.order_number} изменено`,
          body: `Новое время на кухне: ${data.cooking_time_minutes} мин.`,
          url: `/admin/orders`,
          event_type: 'change_cooking_time'
        })
        if (notificationSettings.value?.change_cooking_time_push_enabled) {
          showNativeNotification(
            `Время готовности заказа #${data.order_number} изменено`,
            `Новое время на кухне: ${data.cooking_time_minutes} мин.`,
            '/admin/orders',
            `cooking-time-${data.order_id}`
          )
        }
        if (notificationSettings.value?.change_cooking_time_sound_enabled) {
          playNotificationSound(notificationSettings.value.change_cooking_time_sound_file || 'click.mp3')
        }
        return
      }

      // 5.4. Изменение состава заказа
      if (data.type === 'change_items') {
        addLocalNotification({
          title: `Состав заказа #${data.order_number} изменен`,
          body: `Состав блюд был изменен в iiko`,
          url: `/admin/orders`,
          event_type: 'change_items'
        })
        if (notificationSettings.value?.change_items_push_enabled) {
          showNativeNotification(
            `Состав заказа #${data.order_number} изменен`,
            `Состав блюд был изменен в iiko`,
            '/admin/orders',
            `items-change-${data.order_id}`
          )
        }
        if (notificationSettings.value?.change_items_sound_enabled) {
          playNotificationSound(notificationSettings.value.change_items_sound_file || 'click.mp3')
        }
        return
      }

      // 5.5. Изменение суммы заказа
      if (data.type === 'change_amount') {
        addLocalNotification({
          title: `Сумма заказа #${data.order_number} изменена`,
          body: `Новая сумма к оплате: ${data.amount} ₽`,
          url: `/admin/orders`,
          event_type: 'change_amount'
        })
        if (notificationSettings.value?.change_amount_push_enabled) {
          showNativeNotification(
            `Сумма заказа #${data.order_number} изменена`,
            `Новая сумма к оплате: ${data.amount} ₽`,
            '/admin/orders',
            `amount-change-${data.order_id}`
          )
        }
        if (notificationSettings.value?.change_amount_sound_enabled) {
          playNotificationSound(notificationSettings.value.change_amount_sound_file || 'click.mp3')
        }
        return
      }

      // 5.6. Изменение способа оплаты
      if (data.type === 'change_payment') {
        addLocalNotification({
          title: `Способ оплаты заказа #${data.order_number} изменен`,
          body: `Новый способ: ${data.payment_method}`,
          url: `/admin/orders`,
          event_type: 'change_payment'
        })
        if (notificationSettings.value?.change_payment_push_enabled) {
          showNativeNotification(
            `Способ оплаты заказа #${data.order_number} изменен`,
            `Новый способ: ${data.payment_method}`,
            '/admin/orders',
            `payment-change-${data.order_id}`
          )
        }
        if (notificationSettings.value?.change_payment_sound_enabled) {
          playNotificationSound(notificationSettings.value.change_payment_sound_file || 'click.mp3')
        }
        return
      }

      // 5.7. Изменение адреса доставки
      if (data.type === 'change_address') {
        addLocalNotification({
          title: `Адрес доставки заказа #${data.order_number} изменен`,
          body: `Новый адрес: ${data.address}`,
          url: `/admin/orders`,
          event_type: 'change_address'
        })
        if (notificationSettings.value?.change_address_push_enabled) {
          showNativeNotification(
            `Адрес доставки заказа #${data.order_number} изменен`,
            `Новый адрес: ${data.address}`,
            '/admin/orders',
            `address-change-${data.order_id}`
          )
        }
        if (notificationSettings.value?.change_address_sound_enabled) {
          playNotificationSound(notificationSettings.value.change_address_sound_file || 'click.mp3')
        }
        return
      }
      
      // 6. Сообщения чата
      if (data.type === 'new_message') {
        const msg = data.message

        const isGroupMsg = msg.is_group
        let contactId = isGroupMsg ? 0 : msg.sender_id
        
        if (!isGroupMsg && msg.sender_id === currentUserId.value) {
          contactId = msg.receiver_id
        }

        const isCurrentlyChatting = activeContactId.value === contactId

        if (isCurrentlyChatting) {
          messages.value.push(msg)
          if (isDrawerOpen.value) {
            markRead(contactId, isGroupMsg)
          }
        } else {
          const contact = contacts.value.find(c => c.id === contactId)
          if (contact) {
            contact.unread_count = (contact.unread_count || 0) + 1
          } else {
            fetchContacts()
          }
        }

        // Звук сообщения (только если отправитель не мы)
        if (msg.sender_id !== currentUserId.value) {
          addLocalNotification({
            title: isGroupMsg ? 'Групповой чат' : `Сообщение от ${msg.sender_name || 'Сотрудник'}`,
            body: msg.content,
            url: `/admin/mailings/cascades`,
            event_type: 'chat_message'
          })
          if (notificationSettings.value?.chat_message_push_enabled) {
            showNativeNotification(
              isGroupMsg ? 'Групповой чат' : `Сообщение от ${msg.sender_name || 'Сотрудник'}`,
              msg.content,
              '/admin/mailings/cascades',
              `msg-${msg.id || Date.now()}`
            )
          }
          if (notificationSettings.value?.chat_message_sound_enabled) {
            playNotificationSound(notificationSettings.value.chat_message_sound_file || 'sonar.mp3')
          }
        }
      }

      // 7. Сообщения Мультичата (Live WebSocket поток)
      if (data.type === 'multichat_message') {
        const msgData = data.data || data.message || data
        handleWsMultichatMessage(msgData)
        window.dispatchEvent(new CustomEvent('multichat-message-event', { detail: msgData }))
      }
    }

    ws.value.onclose = () => {
      ws.value = null
      setTimeout(connectWs, 5000)
    }

    ws.value.onerror = err => {
      console.error('WS Error:', err)
      ws.value.close()
    }
  }

  return {
    contacts,
    messages,
    activeContactId,
    isDrawerOpen,
    unreadCount,
    currentUserId,
    paymentNotification,
    orderNotification,
    courierNotification,
    orderCancelledNotification,
    orderChangedNotification,
    orderDeliveredAlert,
    courierAlert,
    isCourier,
    lastOrderUpdate,
    notificationSettings,
    stopOrderSoundRepeat,
    fetchNotificationSettings,
    fetchMe,
    fetchContacts,
    fetchMessages,
    sendMessage,
    markRead,
    connectWs,
    notifications,
    unreadNotificationsCount,
    fetchNotifications,
    markNotificationRead,
    markAllNotificationsRead,
    floatingChats,
    openFloatingChat,
    closeFloatingChat,
    toggleMinimizeFloatingChat,
    sendFloatingMessage,
    messagesCache,
    getCachedMessages,
    setCachedMessages,
    appendMessageToCache,
  }
})

