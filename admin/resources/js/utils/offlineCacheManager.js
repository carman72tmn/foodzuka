import { reactive, ref } from 'vue'

// 4 часа в миллисекундах (14 400 000 мс)
export const CACHE_TTL_4H_MS = 4 * 60 * 60 * 1000

export const CACHE_KEYS = {
  COURIER_ORDERS_4H: 'ft_cache_courier_orders_4h',
  ADMIN_ORDERS_4H: 'ft_cache_admin_orders_4h',
  PAYMENT_TYPES: 'ft_cache_payment_types',
  SHIFT_STATUS: 'ft_cache_shift_status',
  OUTBOX_QUEUE: 'ft_outbox_queue',
  LAST_ONLINE_AT: 'ft_last_online_at'
}

// Реактивное состояние сетевого подключения для UI компонентов
export const networkStatus = reactive({
  isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
  mode: 'online', // 'online' | 'offline' | 'direct_gateway'
  lastSync: new Date(),
  queueCount: 0,
  isSyncing: false,
  message: ''
})

/**
 * Проверка, является ли заказ активным (в работе)
 */
export function isOrderActiveStatus(order) {
  if (!order || !order.status) return false
  const st = String(order.status).toLowerCase()
  return !['closed', 'cancelled', 'delivered'].includes(st)
}

/**
 * Сохранение данных в 4-часовой скользящий кэш
 */
export function saveCache4h(key, data) {
  try {
    const now = Date.now()
    let payloadToStore = data

    // Если это список заказов, сохраняем активные всегда, а завершенные - строго за последние 4 часа
    if (Array.isArray(data)) {
      payloadToStore = data.filter(item => {
        if (isOrderActiveStatus(item)) return true
        const orderTime = item.actual_time || item.updated_at || item.created_at
        if (!orderTime) return true
        const itemTs = new Date(orderTime).getTime()
        if (isNaN(itemTs)) return true
        return (now - itemTs) < CACHE_TTL_4H_MS
      })
    }

    const envelope = {
      savedAt: now,
      version: 2,
      data: payloadToStore
    }

    localStorage.setItem(key, JSON.stringify(envelope))
  } catch (err) {
    console.warn('[OfflineCache] Failed to save 4h cache:', key, err)
  }
}

/**
 * Чтение данных из 4-часового кэша
 */
export function loadCache4h(key) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return null

    const envelope = JSON.parse(raw)
    if (!envelope || typeof envelope !== 'object') return null

    const now = Date.now()
    const savedAt = Number(envelope.savedAt || 0)

    // Если кэш старше 4 часов и это не массив (например справочники)
    if (!Array.isArray(envelope.data) && (now - savedAt) > CACHE_TTL_4H_MS) {
      return null
    }

    // Если это массив заказов, отсекаем закрытые заказы старше 4 часов
    if (Array.isArray(envelope.data)) {
      const filtered = envelope.data.filter(item => {
        if (isOrderActiveStatus(item)) return true
        const orderTime = item.actual_time || item.updated_at || item.created_at
        if (!orderTime) return true
        const itemTs = new Date(orderTime).getTime()
        if (isNaN(itemTs)) return true
        return (now - itemTs) < CACHE_TTL_4H_MS
      })
      return filtered
    }

    return envelope.data
  } catch (err) {
    console.warn('[OfflineCache] Failed to load 4h cache:', key, err)
    return null
  }
}

/**
 * Получение очереди отложенных действий Outbox
 */
export function getOutboxQueue() {
  try {
    const raw = localStorage.getItem(CACHE_KEYS.OUTBOX_QUEUE)
    if (!raw) return []
    const queue = JSON.parse(raw)
    return Array.isArray(queue) ? queue : []
  } catch (e) {
    return []
  }
}

/**
 * Добавление действия в очередь Outbox
 */
export function enqueueOutboxAction(action) {
  try {
    const queue = getOutboxQueue()
    const actionItem = {
      id: `act_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      timestamp: Date.now(),
      clientDate: new Date().toISOString(),
      ...action
    }
    queue.push(actionItem)
    localStorage.setItem(CACHE_KEYS.OUTBOX_QUEUE, JSON.stringify(queue))
    networkStatus.queueCount = queue.length
    return actionItem
  } catch (err) {
    console.error('[OfflineCache] Failed to enqueue action:', err)
    return null
  }
}

/**
 * Удаление действия из очереди Outbox
 */
export function removeOutboxAction(actionId) {
  try {
    const queue = getOutboxQueue().filter(a => a.id !== actionId)
    localStorage.setItem(CACHE_KEYS.OUTBOX_QUEUE, JSON.stringify(queue))
    networkStatus.queueCount = queue.length
  } catch (err) {
    console.error('[OfflineCache] Failed to remove action:', err)
  }
}

/**
 * Запуск фоновой синхронизации накопившейся очереди Outbox
 */
export async function processOutboxQueue(getAuthHeaders) {
  const queue = getOutboxQueue()
  networkStatus.queueCount = queue.length
  if (!queue.length || networkStatus.isSyncing) return

  networkStatus.isSyncing = true
  console.log(`[OfflineCache] Processing outbox queue (${queue.length} actions)...`)

  try {
    const headers = typeof getAuthHeaders === 'function' ? getAuthHeaders() : {}

    // Отправляем пакет на бэкенд пакетной синхронизации
    const response = await fetch('/api/v1/courier/sync-offline-actions', {
      method: 'POST',
      headers: {
        ...headers,
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
      },
      body: JSON.stringify({ actions: queue })
    })

    if (response.ok) {
      const data = await response.json()
      if (data.status === 'success') {
        const processedIds = new Set(data.processed_ids || queue.map(q => q.id))
        const remaining = queue.filter(q => !processedIds.has(q.id))
        localStorage.setItem(CACHE_KEYS.OUTBOX_QUEUE, JSON.stringify(remaining))
        networkStatus.queueCount = remaining.length
        networkStatus.lastSync = new Date()
        networkStatus.mode = 'online'
        console.log('[OfflineCache] Outbox queue synchronized successfully')
      }
    }
  } catch (err) {
    console.warn('[OfflineCache] Sync outbox queue error, will retry later:', err.message)
  } finally {
    networkStatus.isSyncing = false
    networkStatus.queueCount = getOutboxQueue().length
  }
}

/**
 * Сетевой запрос с автоматическим 4-часовым фоллбэком и таймаутом
 */
export async function fetchWithFallback(url, options = {}, config = {}) {
  const timeoutMs = config.timeoutMs || 5000 // 5 секунд таймаут
  const cacheKey = config.cacheKey
  const method = (options.method || 'GET').toUpperCase()

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  const mergedHeaders = {
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    ...(options.headers || {})
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers: mergedHeaders,
      signal: controller.signal
    })
    clearTimeout(timeoutId)

    if (response.ok) {
      networkStatus.isOnline = true
      networkStatus.mode = 'online'
      networkStatus.lastSync = new Date()

      // Для GET запросов с указанным ключом кэша сохраняем свежий 4-часовой снимок
      if (method === 'GET' && cacheKey) {
        try {
          const clone = response.clone()
          const data = await clone.json()
          const list = data.data !== undefined ? data.data : data
          saveCache4h(cacheKey, list)
        } catch (e) {}
      }

      return response
    } else if (response.status >= 500 || response.status === 404) {
      throw new Error(`Server returned HTTP ${response.status}`)
    }

    return response
  } catch (err) {
    clearTimeout(timeoutId)
    console.warn(`[OfflineCache] Network request failed for ${url} (${err.name}):`, err.message)

    networkStatus.isOnline = false
    networkStatus.mode = 'offline'

    // Для GET запроса: возвращаем данные из 4-часового кэша в формате Response
    if (method === 'GET' && cacheKey) {
      const cachedData = loadCache4h(cacheKey)
      if (cachedData !== null) {
        console.log(`[OfflineCache] Returning 4h cached data for ${cacheKey}`)
        const mockBody = JSON.stringify({
          status: 'success',
          data: cachedData,
          _from_offline_cache: true
        })
        return new Response(mockBody, {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        })
      }
    }

    // Для действий курьера: если указано отложенное действие, ставим в Outbox
    if (config.outboxAction) {
      console.log('[OfflineCache] Enqueuing offline action into Outbox:', config.outboxAction.type)
      const queued = enqueueOutboxAction(config.outboxAction)
      const mockBody = JSON.stringify({
        status: 'queued',
        offline: true,
        action_id: queued?.id,
        message: 'Сохранено автономно (будет выгружено в iiko при появлении связи)'
      })
      return new Response(mockBody, {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      })
    }

    throw err
  }
}

// Инициализация глобальных слушателей событий сети
if (typeof window !== 'undefined') {
  networkStatus.queueCount = getOutboxQueue().length

  window.addEventListener('online', () => {
    console.log('[OfflineCache] Browser reports ONLINE')
    networkStatus.isOnline = true
    networkStatus.mode = 'online'
    networkStatus.lastSync = new Date()
  })

  window.addEventListener('offline', () => {
    console.log('[OfflineCache] Browser reports OFFLINE')
    networkStatus.isOnline = false
    networkStatus.mode = 'offline'
  })
}
