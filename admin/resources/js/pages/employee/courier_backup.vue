<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { getAuthHeaders, authState } from '@/utils/auth'
import { useTheme } from 'vuetify'
import { useToast } from 'vue-toastification'
import { formatDate, formatTime, formatDateTime } from '@/utils/date'
import OrderArchiveCard from '@/components/OrderArchiveCard.vue'
import OrderDetailModal from '@/components/OrderDetailModal.vue'

const toast = useToast()

const theme = useTheme()
const activeTab = ref('orders')
const orders = ref([])
const archiveOrders = ref([])
const shifts = ref([])
const activeCouriers = ref([])
const loading = ref(false)
const error = ref(null)
const paymentTypes = ref([])
const selectedPaymentType = ref(null)
const showDetailsDialog = ref(false)
const showCloseDialog = ref(false)
const selectedOrder = ref(null)
const preferredNavigator = ref(localStorage.getItem('preferred_navigator') || 'yandex')

// Отслеживание индикаторов изменений (10 минут)
const indicatorsSeen = ref(JSON.parse(localStorage.getItem('courier_indicators_seen') || '{}'))

const saveIndicatorsSeen = () => {
  localStorage.setItem('courier_indicators_seen', JSON.stringify(indicatorsSeen.value))
}

const getActiveIndicators = order => {
  if (!order.change_indicators) return null
  
  const hasChanges = Object.values(order.change_indicators).some(v => v)
  if (!hasChanges) {
    // Если на бэкенде изменений нет, проверяем, не истекло ли время отображения старых
    const seen = indicatorsSeen.value[order.id]
    if (seen && Date.now() - seen.timestamp < 10 * 60 * 1000) {
      return seen.indicators
    }

    return null
  }

  // Если изменения есть на бэкенде, обновляем время "увидения"
  const currentSeen = indicatorsSeen.value[order.id]
  const indicatorsStr = JSON.stringify(order.change_indicators)
  
  if (!currentSeen || JSON.stringify(currentSeen.indicators) !== indicatorsStr) {
    indicatorsSeen.value[order.id] = {
      timestamp: Date.now(),
      indicators: order.change_indicators,
    }
    saveIndicatorsSeen()
  }

  return order.change_indicators
}

const formatDeliveryTime = order => {
  if (order.is_asap) return 'КАК МОЖНО СКОРЕЕ'
  if (!order.expected_time) return formatDateTime(order.iiko_creation_time || order.created_at, { day: undefined, month: undefined, year: undefined })
  
  const expected = new Date(order.expected_time)
  const today = new Date()
  const isToday = expected.getDate() === today.getDate() && 
                  expected.getMonth() === today.getMonth() && 
                  expected.getFullYear() === today.getFullYear()
  
  if (isToday) {
    return formatDateTime(order.expected_time, { day: undefined, month: undefined, year: undefined })
  }
  
  return formatDateTime(order.expected_time)
}

// Фильтры для архива
const formatDateLocal = date => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const getPaymentStatusText = order => {
  if (order.is_paid) return 'Оплачено'
  const left = parseFloat(order.left_to_pay || 0)
  const total = parseFloat(order.total_with_discount || order.sum || 0)
  if (left > 0 && left < total) return `Частично (ост. ${left} ₽)`

  return 'Ожидает оплаты'
}

const getPaymentStatusColor = order => {
  if (order.is_paid) return 'success'
  const left = parseFloat(order.left_to_pay || 0)
  const total = parseFloat(order.total_with_discount || order.sum || 0)
  if (left > 0 && left < total) return 'warning'

  return 'error'
}

const getPaymentStatusIcon = order => {
  if (order.is_paid) return 'bx-check-shield'
  const left = parseFloat(order.left_to_pay || 0)
  const total = parseFloat(order.total_with_discount || order.total_amount || order.sum || 0)
  if (left > 0 && left < total) return 'bx-adjust'

  return 'bx-error-circle'
}

const getPaymentTypeIcon = method => {
  if (!method) return 'bx-credit-card'
  const m = method.toLowerCase()
  if (m.includes('налич')) return 'bx-money'
  if (m.includes('карт') || m.includes('visa') || m.includes('master')) return 'bx-credit-card'
  if (m.includes('qr') || m.includes('сбп')) return 'bx-qr-scan'
  if (m.includes('сайт') || m.includes('онлайн')) return 'bx-globe'
  if (m.includes('бонус')) return 'bx-gift'

  return 'bx-wallet'
}

const formatPaymentMethods = order => {
  if (order.payments_details?.items?.length) {
    return order.payments_details.items
      .map(p => `${p.name}: ${p.sum} ₽`)
      .join(', ')
  }

  return order.payment_method || 'Не указан'
}

const selectedDate = ref(formatDateLocal(new Date()))
const archiveCourierFilter = ref(null)
const userSelectedSpecificDate = ref(false)
const showDatePicker = ref(false)

// [NEW] Tracking for button responsiveness
const buttonLocks = ref({}) // Tracks lockout for "Start Delivery" (10s)
const manualClickTimes = ref({}) // Tracks when "Start Delivery" was clicked (60s delay for "Delivered")

const isButtonLocked = orderId => {
  const lockTime = buttonLocks.value[orderId]
  if (!lockTime) return false
  
  const elapsed = Date.now() - lockTime
  if (elapsed >= 10000) {
    delete buttonLocks.value[orderId]
    return false
  }
  
  return true
}

const canShowDelivered = order => {
  // 1. Check local manual click time
  const clickTime = manualClickTimes.value[order.id]
  if (clickTime) {
    if ((Date.now() - clickTime) > 60000) return true
  }
  
  // 2. Check server-provided on_the_way_time
  if (order.on_the_way_time) {
    const onWayDate = new Date(order.on_the_way_time)
    if (!isNaN(onWayDate.getTime())) {
      if ((Date.now() - onWayDate.getTime()) > 60000) return true
    }
  }
  
  return false
}

// Пагинация и даты курьера
const archivePage = ref(1)
const archiveTotalPages = ref(1)
const archiveTotalItems = ref(0)
const archivePageSize = ref(24)
const courierDates = ref([])

const setPreferredNavigator = val => {
  preferredNavigator.value = val
  localStorage.setItem('preferred_navigator', val)
}

const detailsOrder = ref(null)
const lastUpdated = ref(null)
const currentTime = ref(new Date())
const refreshTimer = ref(null)
const countdownTimer = ref(null)

const isSuperAdmin = computed(() => authState.user?.is_superuser)

const fetchData = async (options = {}) => {
  const quiet = (typeof options === 'boolean') ? options : (options instanceof Event ? false : (options.quiet ?? false))
  
  if (!quiet) {
    loading.value = true
    error.value = null
  }

  try {
    // [OPTIMIZED] Убрана автоматическая синхронизация при каждой загрузке fetchData,
    // так как это перегружает RMS iiko. Данные синхронизируются фоновым воркером.
    // Для ручного обновления добавлена отдельная кнопка syncData.
    
    if (activeTab.value === 'orders') {
      await fetchOrders()
    } else if (activeTab.value === 'archive') {
      await fetchOrders(true)
    } else if (activeTab.value === 'shifts') {
      await fetchShifts()
    } else if (activeTab.value === 'couriers') {
      await fetchActiveCouriers()
    }
    lastUpdated.value = formatTime(new Date(), { second: '2-digit' })
  } catch (e) {
    if (!quiet) {
      error.value = 'Ошибка загрузки данных'
      console.error('Fetch error:', e)
    }
  } finally {
    if (!quiet) loading.value = false
  }
}
const syncData = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/v1/courier/sync', {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    const data = await res.json()
    if (data.status === 'success') {
      toast.success('Данные успешно обновлены из iiko')
      await fetchData(true)
    } else {
      toast.error('Ошибка синхронизации: ' + (data.message || 'неизвестная ошибка'))
    }
  } catch (e) {
    toast.error('Ошибка при обращении к серверу')
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchOrders = async (includeClosed = false) => {
  let url = '/api/v1/courier/orders'
  const params = new URLSearchParams()
  
  if (includeClosed) {
    params.append('include_closed', 'true')
    // Если выбран курьер и НЕ выбрана конкретная дата - НЕ шлем дату, чтобы бэкенд показал 7 дней
    // Иначе шлем selectedDate
    if (selectedDate.value && (!archiveCourierFilter.value || userSelectedSpecificDate.value)) {
      params.append('date_from', selectedDate.value)
      params.append('date_to', selectedDate.value)
    }
    
    if (archiveCourierFilter.value) {
      params.append('courier_filter', archiveCourierFilter.value)
    }
    params.append('page', archivePage.value)
    params.append('size', archivePageSize.value)
  }
  
  const queryString = params.toString()
  if (queryString) url += `?${queryString}`

  const res = await fetch(url, {
    headers: getAuthHeaders(),
  })
  const data = await res.json()
  console.log('Archive fetch result:', data)
  if (data.status === 'success') {
    if (includeClosed) {
      archiveOrders.value = data.data
      if (data.pagination) {
        archiveTotalPages.value = data.pagination.pages
        archiveTotalItems.value = data.pagination.total
      }
    } else {
      orders.value = data.data
    }
  } else {
    error.value = data.message || 'Ошибка загрузки заказов'
  }
}

const setArchiveDate = action => {
  userSelectedSpecificDate.value = true
  let d = new Date(selectedDate.value + 'T12:00:00')
  if (action === 'today') {
    selectedDate.value = formatDateLocal(new Date())
    // Для "Сегодня" можно сбросить флаг ручного выбора, если курьер не выбран
    if (!archiveCourierFilter.value) userSelectedSpecificDate.value = false
  } else if (action === 'yesterday') {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    selectedDate.value = formatDateLocal(yesterday)
  } else if (action === 'prev') {
    d.setDate(d.getDate() - 1)
    selectedDate.value = formatDateLocal(d)
  } else if (action === 'next') {
    d.setDate(d.getDate() + 1)
    selectedDate.value = formatDateLocal(d)
  }
  archivePage.value = 1 // Сброс страницы при смене даты
  fetchOrders(true)
}

const fetchCourierDates = async () => {
  if (!archiveCourierFilter.value) {
    courierDates.value = []
    return
  }
  
  try {
    const res = await fetch(`/api/v1/courier/dates?courier_name=${encodeURIComponent(archiveCourierFilter.value)}`, {
      headers: getAuthHeaders(),
    })
    const data = await res.json()
    if (data.status === 'success') {
      courierDates.value = data.data
    }
  } catch (e) {
    console.error('Failed to fetch courier dates', e)
  }
}

const selectCourierDate = (date) => {
  userSelectedSpecificDate.value = true
  selectedDate.value = date.split('T')[0]
  archivePage.value = 1
  fetchOrders(true)
}

const archiveCouriersList = computed(() => {
  const couriers = new Set()
  archiveOrders.value.forEach(o => {
    if (o.courier_name) couriers.add(o.courier_name)
  })
  return Array.from(couriers)
})

const archiveSortByCourier = ref(false)
const archiveGroupByCourier = ref(false)

const filteredArchiveOrders = computed(() => {
  let list = [...archiveOrders.value]

  if (archiveCourierFilter.value) {
    list = list.filter(o => o.courier_name === archiveCourierFilter.value)
  }

  if (archiveSortByCourier.value) {
    list.sort((a, b) => {
      const nameA = a.courier_name || ''
      const nameB = b.courier_name || ''
      if (nameA === nameB) {
        return new Date(b.created_at) - new Date(a.created_at)
      }
      return nameA.localeCompare(nameB)
    })
  } else {
    list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  }
  
  return list
})

const groupedArchiveOrders = computed(() => {
  if (!archiveGroupByCourier.value) return null
  
  const groups = {}
  filteredArchiveOrders.value.forEach(order => {
    const name = order.courier_name || 'Не назначен'
    if (!groups[name]) groups[name] = { name, orders: [], total: 0, count: 0 }
    groups[name].orders.push(order)
    groups[name].total += (order.sum || 0)
    groups[name].count += 1
  })
  
  return Object.values(groups).sort((a, b) => a.name.localeCompare(b.name))
})

const fetchShifts = async () => {
  const res = await fetch('/api/v1/courier/shifts', {
    headers: getAuthHeaders(),
  })
  const data = await res.json()
  if (data.status === 'success') {
    shifts.value = data.data
  } else {
    error.value = data.detail || 'Ошибка загрузки смен'
  }
}

const fetchActiveCouriers = async () => {
  const res = await fetch('/api/v1/courier/active-couriers', {
    headers: getAuthHeaders(),
  })
  const data = await res.json()
  if (data.status === 'success') {
    activeCouriers.value = data.data
  } else {
    error.value = data.detail || 'Ошибка загрузки курьеров'
  }
}

const fetchPaymentTypes = async () => {
  try {
    const res = await fetch('/api/v1/courier/payment-types', {
      headers: getAuthHeaders(),
    })
    const data = await res.json()
    if (data.status === 'success') {
      paymentTypes.value = data.data
    }
  } catch (e) {
    console.error('Failed to fetch payment types', e)
  }
}

const updateStatus = async (orderId, status, silent = false) => {
  // [NEW] Lockout and delay logic
  if (status === 'OnWay') {
    buttonLocks.value[orderId] = Date.now()
    manualClickTimes.value[orderId] = Date.now()
  }

  loading.value = true
  try {
    const res = await fetch(`/api/v1/courier/orders/${orderId}/status?status=${status}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })

    if (res.ok) {
      await fetchOrders()
      
      // Auto-open payment dialog only if NOT silent
      if (status === 'Delivered' && !silent) {
        const order = orders.value.find(o => o.id === orderId)
        if (order) openCloseDialog(order)
      }
    } else {
      const data = await res.json()
      alert(data.detail || 'Не удалось обновить статус')
    }
  } catch (e) {
    alert('Ошибка сети')
  } finally {
    loading.value = false
  }
}

const openCloseDialog = order => {
  selectedOrder.value = order
  if (order.payment_method) {
    const pt = paymentTypes.value.find(p => p.name.toLowerCase().includes(order.payment_method.toLowerCase()))
    if (pt) selectedPaymentType.value = pt.iiko_id
  }
  showCloseDialog.value = true
}

const closeOrderAction = async () => {
  if (!selectedPaymentType.value) {
    alert('Выберите тип оплаты')
    return
  }
  
  loading.value = true
  try {
    const orderId = selectedOrder.value.id
    const amount = selectedOrder.value.total_with_discount || selectedOrder.value.sum
    const ptId = selectedPaymentType.value
    
    const res = await fetch(`/api/v1/courier/orders/${orderId}/close?payment_type_id=${ptId}&amount=${amount}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    
    if (res.ok) {
      showCloseDialog.value = false
      selectedOrder.value = null
      selectedPaymentType.value = null
      await fetchOrders()
    } else {
      const data = await res.json()
      alert(data.detail || 'Ошибка при закрытии заказа')
    }
  } catch (e) {
    alert('Ошибка сети при закрытии заказа')
  } finally {
    loading.value = false
  }
}

const getStatusColor = status => {
  if (!status) return 'grey'
  switch (status.toLowerCase()) {
    case 'ready': return 'amber-darken-2' // Насыщенный оранжевый/желтый
    case 'delivering':
    case 'onway': return 'blue-darken-2' // Синий
    case 'delivered': return 'green-darken-2' // Зеленый
    case 'closed': return 'slate-900' // Темный
    case 'cancelled': return 'red-darken-2' // Красный
    case 'cooking': return 'cyan-darken-2' // Голубой
    default: return 'grey'
  }
}

const getStatusText = status => {
  if (!status) return 'Неизвестно'
  switch (status.toLowerCase()) {
    case 'ready': return 'Готов к отправке'
    case 'delivering':
    case 'onway': return 'В пути'
    case 'delivered': return 'Доставлен (у клиента)'
    case 'closed': return 'Закрыт'
    case 'cancelled': return 'Отменен'
    case 'cooking': return 'Готовится'
    default: return status
  }
}

const formatAddress = order => {
  if (!order.address) return 'Адрес не указан'
  const a = order.address
  if (typeof a === 'string') return a
  if (a.line1) return a.line1
  
  const parts = []
  if (a.city) parts.push(a.city)
  if (a.street) parts.push(a.street)
  if (a.house || a.home) parts.push(`д. ${a.house || a.home}`)
  return parts.join(', ') || 'Адрес не указан'
}

const openMaps = (order, provider = null) => {
  const addr = order.delivery_address || formatAddress(order)
  if (!addr || addr === 'Адрес не указан') {
    toast.error('Адрес не указан для этого заказа')
    return
  }
  const nav = provider || preferredNavigator.value
  let url = ''
  
  switch (nav) {
    case 'yandex':
      url = `https://yandex.ru/maps/?text=${encodeURIComponent(addr)}`
      break
    case '2gis':
      url = `https://2gis.ru/search/${encodeURIComponent(addr)}`
      break
    case 'google':
      url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(addr)}`
      break
    case 'petal':
      url = `https://www.petalmaps.com/search/?q=${encodeURIComponent(addr)}`
      break
    default:
      url = `https://yandex.ru/maps/?text=${encodeURIComponent(addr)}`
  }
  
  if (url) window.open(url, '_blank', 'noopener,noreferrer')
}

const copyToClipboard = async (text) => {
  if (!text || text === 'Адрес не указан') return
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      toast.success('Скопировано')
    } else {
      const textArea = document.createElement("textarea")
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      toast.success('Адрес скопирован')
    }
  } catch (err) {
    toast.error('Ошибка при копировании')
  }
}

const getDuration = (startStr, endStr) => {
  if (!startStr || !endStr) return null
  const start = new Date(startStr)
  const end = new Date(endStr)
  const diff = Math.floor((end - start) / 60000)
  return diff > 0 ? `${diff} мин.` : '< 1 мин.'
}

const getLateness = (order) => {
  if (!order.expected_time) return null
  const target = new Date(order.expected_time)
  // Если заказ доставлен, используем actual_time, иначе текущее время
  const actual = (order.status === 'delivered' || order.status === 'closed' || order.actual_time) 
    ? new Date(order.actual_time || Date.now()) 
    : currentTime.value
  
  const diff = Math.floor((actual - target) / 60000)
  return diff > 0 ? diff : null
}

const openDetails = async (order) => {
  detailsOrder.value = order
  showDetailsDialog.value = true
  
  if (order.change_indicators && Object.values(order.change_indicators).some(v => v)) {
    try {
      await fetch(`/api/v1/courier/orders/${order.id}/acknowledge`, {
        method: 'POST',
        headers: getAuthHeaders(),
      })
      order.change_indicators = null
    } catch (e) {
      console.error('Failed to acknowledge changes', e)
    }
  }
}

const getCountdown = expectedTime => {
  if (!expectedTime) return null
  const diff = new Date(expectedTime) - currentTime.value
  const mins = Math.floor(diff / 60000)
  if (mins < -999) return null
  return mins
}

const getCountdownColor = mins => {
  if (mins === null) return 'grey'
  if (mins < 0) return 'red'
  if (mins < 15) return 'orange'
  return 'success'
}

const startTimers = () => {
  refreshTimer.value = setInterval(() => {
    fetchData(true)
  }, 30000)

  // Обновление локального времени каждую секунду для плавного обратного отсчета
  countdownTimer.value = setInterval(() => {
    currentTime.value = new Date()
  }, 1000)
}

const callCustomer = phone => {
  if (!phone) return
  window.location.href = `tel:${phone.replace(/[^\d+]/g, '')}`
}

watch(activeTab, (val) => {
  if (val === 'archive' && !archiveOrders.value.length) {
    fetchOrders(true)
  } else {
    fetchData()
  }
})

watch(archiveCourierFilter, () => {
  archivePage.value = 1
  userSelectedSpecificDate.value = false // Сброс при смене курьера
  fetchCourierDates()
  fetchOrders(true)
})

watch(selectedDate, () => {
  if (activeTab.value === 'archive') {
    archivePage.value = 1
    fetchOrders(true)
  }
})

watch(archivePage, () => {
  fetchOrders(true)
})

onMounted(() => {
  fetchData()
  fetchPaymentTypes()
  startTimers()
})

onUnmounted(() => {
  if (refreshTimer.value) clearInterval(refreshTimer.value)
  if (countdownTimer.value) clearInterval(countdownTimer.value)
})
</script>

<template>
  <VContainer fluid class="pa-0 courier-app-wrapper bg-slate-50">
    <!-- Header -->
    <header class="app-header mb-4">
      <div class="d-flex align-center justify-space-between px-2">
        <div>
          <h1 class="text-h5 font-weight-black main-title">
            {{ activeTab === 'archive' ? 'Архив доставок' : 'Активные доставки' }}
          </h1>
          <p v-if="lastUpdated" class="text-caption text-grey-darken-1">
            Обновлено: {{ lastUpdated }}
          </p>
        </div>
        <VBtn
            variant="flat"
            color="primary"
            class="rounded-pill px-4"
            @click="syncData"
            :loading="loading"
          >
            <VIcon icon="bx-sync" class="me-1" :class="{'bx-spin': loading}" />
            Обновить из iiko
          </VBtn>
      </div>


      <VTabs
        v-model="activeTab"
        color="primary"
        align-tabs="start"
        class="mt-2 custom-tabs-nav"
        density="compact"
      >
        <VTab value="orders" class="text-none">Доставки ({{ orders.length }})</VTab>
        <VTab value="archive" class="text-none">Архив доставок</VTab>
        <VTab v-if="isSuperAdmin" value="shifts" class="text-none">Смены</VTab>
        <VTab v-if="isSuperAdmin" value="couriers" class="text-none">Курьеры</VTab>
      </VTabs>
    </header>

    <!-- Error State -->
    <VAlert
      v-if="error"
      type="error"
      variant="tonal"
      closable
      class="mb-4 rounded-xl"
    >
      {{ error }}
    </VAlert>

    <!-- Content -->
    <VWindow v-model="activeTab">
      <!-- Active Orders -->
      <VWindowItem value="orders">
        <div v-if="loading && !orders.length" class="text-center py-12">
          <VProgressCircular indeterminate color="primary" size="48" />
          <p class="mt-4 text-body-2 text-grey">Получаем список доставок...</p>
        </div>

        <div v-else-if="!orders.length" class="empty-state text-center py-16">
          <VIcon size="64" color="grey-lighten-2" icon="bx-package" class="mb-4" />
          <h3 class="text-h6 font-weight-bold">Доставок нет</h3>
          <p class="text-body-2 text-grey">Как только появится заказ — он будет тут</p>
          <VBtn variant="tonal" color="primary" class="mt-4 rounded-pill" @click="fetchOrders">Проверить</VBtn>
        </div>

        <div v-else class="orders-list px-2 px-md-4 py-4">
          <VRow class="ma-0">
            <VCol
              v-for="order in orders"
              :key="order.id"
              cols="12"
              sm="6"
              md="4"
              lg="3"
              class="pa-3"
            >
              <VCard
                class="delivery-card-premium d-flex flex-column"
                variant="flat"
              >
                <!-- 1. Status Bar (Indicators) -->
                <div class="change-indicators-bar">
                  <template v-if="getActiveIndicators(order)">
                    <div v-if="getActiveIndicators(order).items" class="bg-error flex-grow-1"></div>
                    <div v-else-if="getActiveIndicators(order).amount" class="bg-warning flex-grow-1"></div>
                    <div v-else-if="getActiveIndicators(order).address" class="bg-primary flex-grow-1"></div>
                    <div v-else-if="getActiveIndicators(order).time" class="bg-info flex-grow-1"></div>
                    <div v-else-if="getActiveIndicators(order).payment" class="bg-success flex-grow-1"></div>
                  </template>
                </div>

                <!-- [NEW] Delivery Time Meta -->
                <div class="px-5 pt-3 d-flex justify-space-between align-center">
                  <div class="d-flex align-center ga-1">
                    <VIcon :icon="order.is_asap ? 'bx-bolt-circle' : 'bx-calendar-event'" size="16" :color="order.is_asap ? 'warning' : 'primary'" />
                    <span class="text-card-small font-weight-black" :class="order.is_asap ? 'text-amber-darken-3' : 'text-primary'">
                      {{ order.is_asap ? 'КАК МОЖНО СКОРЕЕ' : 'ЗАКАЗ НА ВРЕМЯ' }}
                    </span>
                  </div>
                  <div v-if="order.expected_time" class="text-card-small font-weight-black text-primary">
                    <span v-if="!order.is_asap" class="me-1">{{ formatDate(order.expected_time) }}</span>
                    <span>{{ formatTime(order.expected_time) }}</span>
                  </div>
                </div>

                <!-- 2. Header: Status & Timers -->
                <div class="card-header-status d-flex align-center justify-space-between">
                  <div class="d-flex align-center ga-2">
                    <VChip 
                      :color="getStatusColor(order.status)" 
                      size="x-small" 
                      variant="flat" 
                      class="text-uppercase font-weight-black"
                      :style="{ color: 'white', textShadow: '0 1px 2px rgba(0,0,0,0.2)' }"
                    >
                      {{ getStatusText(order.status) }}
                    </VChip>
                    <div v-if="order.status === 'delivering' || order.status === 'onway'" class="d-flex align-center ga-1">
                      <div class="pulse-dot"></div>
                      <span class="text-card-small text-primary">{{ getDuration(order.on_the_way_time, currentTime) }}</span>
                    </div>
                  </div>
                  
                  <div class="text-right">
                    <div v-if="getCountdown(order.expected_time) !== null && getCountdown(order.expected_time) >= 0" class="d-flex align-center justify-end ga-1">
                      <VIcon icon="bx-time" size="14" :color="getCountdownColor(getCountdown(order.expected_time))" />
                      <span class="text-card-small font-weight-bold" :class="'text-' + getCountdownColor(getCountdown(order.expected_time))">
                        До {{ formatTime(order.expected_time) }}
                      </span>
                    </div>
                    <div v-if="getLateness(order)" class="d-flex align-center justify-end ga-1">
                      <VIcon icon="bx-alarm-exclamation" size="14" color="error" />
                      <span class="text-card-small text-error font-weight-black animate-pulse">
                        +{{ getLateness(order) }} м
                      </span>
                    </div>
                  </div>
                </div>

                <!-- 3. Urgent Indicators (Badges) -->
                <div v-if="getActiveIndicators(order)" class="px-5 pt-3 d-flex flex-wrap ga-1">
                  <VChip v-if="getActiveIndicators(order).items" color="error" size="x-small" variant="flat" class="animate-pulse">СОСТАВ!</VChip>
                  <VChip v-if="getActiveIndicators(order).amount" color="warning" size="x-small" variant="flat" class="animate-pulse">СУММА!</VChip>
                  <VChip v-if="getActiveIndicators(order).address" color="primary" size="x-small" variant="flat" class="animate-pulse">АДРЕС!</VChip>
                  <VChip v-if="getActiveIndicators(order).time" color="info" size="x-small" variant="flat" class="animate-pulse">ВРЕМЯ!</VChip>
                  <VChip v-if="getActiveIndicators(order).payment" color="success" size="x-small" variant="flat" class="animate-pulse">ОПЛАТА!</VChip>
                </div>

                <!-- 4. Identity -->
                <div class="section-divider">
                  <div class="d-flex justify-space-between align-center">
                    <div>
                      <div class="text-card-title">№{{ order.external_number || order.number || '???' }}</div>
                      <div class="text-card-caption d-flex align-center ga-1 mt-1">
                        <VIcon icon="bx-store-alt" size="14" />
                        <span class="text-truncate">{{ order.organization_name || 'Основная' }}</span>
                      </div>
                    </div>
                    <VBtn
                      v-if="order.is_important"
                      icon="bx-star"
                      variant="text"
                      color="warning"
                      size="small"
                    />
                  </div>
                </div>

                <!-- 5. Client Info -->
                <div class="section-divider d-flex align-center justify-space-between">
                  <div class="d-flex align-center overflow-hidden">
                    <VAvatar size="36" color="primary-lighten-5" class="me-3">
                      <VIcon icon="bx-user" size="20" color="primary" />
                    </VAvatar>
                    <div class="d-flex flex-column overflow-hidden">
                      <span class="text-card-body font-weight-bold text-truncate">
                        {{ order.customer_name || order.customer?.name || 'Гость' }}
                      </span>
                      <div class="d-flex align-center ga-1">
                        <VIcon 
                          :icon="order.customer_info_details?.is_high_risk ? 'bx-shield-x' : 'bx-check-shield'" 
                          size="12" 
                          :color="order.customer_info_details?.is_high_risk ? 'error' : 'success'" 
                        />
                        <span class="text-card-small" :class="order.customer_info_details?.is_high_risk ? 'text-error' : 'text-success'">
                          {{ order.customer_info_details?.is_high_risk ? 'Риск' : 'Надежный' }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <VBtn
                    icon="bx-phone"
                    size="40"
                    color="success"
                    variant="tonal"
                    class="rounded-xl shadow-sm"
                    @click.stop="callCustomer(order.customer_phone || order.customer?.phone)"
                  />
                </div>

                <!-- 6. Address -->
                <div class="section-divider">
                  <div class="address-premium-box d-flex align-start ga-2" @click="openMaps(order)">
                    <VIcon icon="bx-map" color="primary" class="mt-1" size="18" />
                    <div class="text-card-body font-weight-bold line-height-sm flex-grow-1">
                      {{ order.delivery_address || formatAddress(order) }}
                    </div>
                    <VBtn
                      icon="bx-copy"
                      variant="text"
                      size="x-small"
                      color="grey"
                      class="ms-1"
                      @click.stop="copyToClipboard(order.delivery_address || formatAddress(order))"
                    />
                  </div>
                </div>

                <!-- 7. Comments (Optional) -->
                <div v-if="order.comment || order.courier_comment" class="section-divider bg-amber-50 py-2">
                  <div v-if="order.comment" class="d-flex ga-2 mb-1">
                    <VIcon icon="bx-comment" size="14" color="amber-darken-3" class="mt-1" />
                    <div class="text-card-caption text-slate-700"><strong>Заказ:</strong> {{ order.comment }}</div>
                  </div>
                  <div v-if="order.courier_comment" class="d-flex ga-2">
                    <VIcon icon="bx-info-circle" size="14" color="primary" class="mt-1" />
                    <div class="text-card-caption text-slate-700"><strong>Курьеру:</strong> {{ order.courier_comment }}</div>
                  </div>
                </div>

                <!-- 8. Composition -->
                <div class="composition-panel">
                  <VExpansionPanels variant="accordion">
                    <VExpansionPanel elevation="0" class="border-b rounded-0">
                      <VExpansionPanelTitle class="px-5">
                        <template #default="{ expanded }">
                          <div class="d-flex align-center ga-2 w-100">
                            <VIcon icon="bx-package" size="16" color="slate-400" />
                            <span class="text-card-small text-slate-500">Состав ({{ order.items?.length || 0 }})</span>
                            <VSpacer />
                            <span v-if="!expanded" class="text-card-caption font-weight-bold text-truncate" style="max-width: 120px;">
                              {{ order.items?.[0]?.name }}{{ order.items?.length > 1 ? '...' : '' }}
                            </span>
                          </div>
                        </template>
                      </VExpansionPanelTitle>
                      <VExpansionPanelText>
                        <div
                          v-for="item in order.items"
                          :key="item.id"
                          class="d-flex justify-space-between py-1 border-bottom-dashed text-card-caption"
                        >
                          <span class="text-truncate me-2">{{ item.name }}</span>
                          <span class="font-weight-black flex-shrink-0 text-slate-900">{{ item.amount }} шт.</span>
                        </div>
                      </VExpansionPanelText>
                    </VExpansionPanel>
                  </VExpansionPanels>
                </div>

                <!-- 9. Payment & Primary Actions -->
                <div class="card-footer-payment">
                  <div class="d-flex justify-space-between align-center mb-4">
                    <div class="d-flex flex-column">
                      <span class="text-card-small text-slate-400 leading-none mb-1">Сумма</span>
                      <span class="text-h6 font-weight-black text-slate-900 leading-none">
                        {{ (order.left_to_pay || order.total_with_discount || order.sum || 0).toLocaleString() }} ₽
                      </span>
                    </div>
                    <div class="text-right">
                      <div class="d-flex align-center justify-end ga-1 mb-1">
                        <VIcon :icon="getPaymentTypeIcon(order.payment_method)" size="14" color="slate-400" />
                        <span class="text-card-small text-slate-600">{{ order.payment_method || '—' }}</span>
                      </div>
                      <VChip 
                        :color="getPaymentStatusColor(order)" 
                        size="x-small" 
                        variant="flat" 
                        class="font-weight-black"
                      >
                        {{ getPaymentStatusText(order) }}
                      </VChip>
                    </div>
                  </div>

                  <!-- Buttons Row 1: Primary Action & Details -->
                  <div class="d-flex ga-2 mb-3">
                    <VBtn
                      v-if="order.status.toLowerCase() === 'ready'"
                      prepend-icon="bx-run"
                      :color="isButtonLocked(order.id) ? 'secondary' : 'primary'"
                      :disabled="isButtonLocked(order.id)"
                      variant="flat"
                      size="large"
                      class="rounded-xl font-weight-black text-uppercase flex-grow-1"
                      @click.stop="updateStatus(order.id, 'OnWay')"
                    >
                      Начать доставку
                    </VBtn>

                    <!-- ORANGE Delivered Button (60s after start) -->
                    <VBtn
                      v-else-if="(order.status.toLowerCase() === 'onway' || order.status.toLowerCase() === 'delivering') && canShowDelivered(order)"
                      prepend-icon="bx-check-double"
                      color="warning"
                      variant="flat"
                      size="large"
                      class="rounded-xl font-weight-black text-uppercase flex-grow-1"
                      @click.stop="updateStatus(order.id, 'Delivered', true)"
                    >
                      Доставлен
                    </VBtn>

                    <!-- Secondary Info Button (Before 60s passed) -->
                    <VBtn
                      v-else-if="order.status.toLowerCase() === 'onway' || order.status.toLowerCase() === 'delivering'"
                      prepend-icon="bx-info-circle"
                      variant="flat"
                      color="secondary"
                      size="large"
                      class="rounded-xl font-weight-bold flex-grow-1"
                      @click.stop="openDetails(order)"
                    >
                      Подробнее
                    </VBtn>
                    <VBtn
                      v-else-if="order.status.toLowerCase() === 'delivered'"
                      prepend-icon="bx-wallet"
                      color="slate-900"
                      variant="flat"
                      size="large"
                      class="rounded-xl font-weight-black text-uppercase text-white flex-grow-1"
                      @click.stop="openCloseDialog(order)"
                    >
                      Оплатить
                    </VBtn>
                    <VBtn
                      v-else
                      prepend-icon="bx-info-circle"
                      variant="tonal"
                      color="secondary"
                      size="large"
                      class="rounded-xl font-weight-bold flex-grow-1"
                      @click.stop="openDetails(order)"
                    >
                      Подробнее
                    </VBtn>

                    <!-- Иконка подробнее если основная кнопка другая -->
                    <VBtn
                      v-if="order.status.toLowerCase() === 'ready' || order.status.toLowerCase() === 'delivered'"
                      icon="bx-info-circle"
                      variant="tonal"
                      color="secondary"
                      size="large"
                      class="rounded-xl flex-shrink-0"
                      style="width: 56px;"
                      @click.stop="openDetails(order)"
                    />
                  </div>

                  <!-- Buttons Row 2: Secondary Actions (Maps) -->
                  <div class="d-flex ga-2">
                    <VMenu offset-y transition="scale-transition" location="top">
                      <template #activator="{ props: menuProps }">
                        <VBtn
                          v-bind="menuProps"
                          prepend-icon="bx-navigation"
                          color="primary"
                          variant="tonal"
                          size="small"
                          class="rounded-lg font-weight-bold flex-grow-1"
                        >
                          Открыть в навигаторе
                        </VBtn>
                      </template>
                      <VList density="compact" class="rounded-xl py-2 border shadow-lg">
                        <VListItem @click="openMaps(order, 'yandex')" class="py-2">
                          <template #prepend><VIcon icon="bx-map" color="orange" /></template>
                          <VListItemTitle class="font-weight-bold">Яндекс</VListItemTitle>
                        </VListItem>
                        <VListItem @click="openMaps(order, '2gis')" class="py-2">
                          <template #prepend><VIcon icon="bx-navigation" color="blue" /></template>
                          <VListItemTitle class="font-weight-bold">2ГИС</VListItemTitle>
                        </VListItem>
                        <VListItem @click="openMaps(order, 'google')" class="py-2">
                          <template #prepend><VIcon icon="bx-globe" color="green" /></template>
                          <VListItemTitle class="font-weight-bold">Google Maps</VListItemTitle>
                        </VListItem>
                      </VList>
                    </VMenu>
                  </div>
                </div>
              </VCard>
            </VCol>
          </VRow>
        </div>
      </VWindowItem>

      <!-- Архив доставок -->
      <VWindowItem value="archive">
        <!-- Фильтры архива -->
        <div class="archive-filters pa-4 bg-white border-b sticky-top">
          <div class="d-flex flex-wrap align-center gap-3">
            <div class="d-flex align-center gap-2">
              <VBtn 
                icon="bx-chevron-left"
                size="small" 
                variant="tonal" 
                color="primary" 
                @click="setArchiveDate('prev')"
                title="Предыдущий день"
              />
              <VBtn 
                size="small" 
                variant="tonal" 
                color="secondary" 
                @click="setArchiveDate('today')"
                class="rounded-lg"
              >Сегодня</VBtn>
              <VBtn 
                size="small" 
                variant="tonal" 
                color="secondary" 
                @click="setArchiveDate('yesterday')"
                class="rounded-lg"
              >Вчера</VBtn>
              <VBtn 
                icon="bx-chevron-right"
                size="small" 
                variant="tonal" 
                color="primary" 
                @click="setArchiveDate('next')"
                title="Следующий день"
              />
            </div>
            
            <VTextField
              v-model="selectedDate"
              type="date"
              label="Дата"
              density="compact"
              hide-details
              variant="outlined"
              class="max-width-200"
              @update:model-value="() => { userSelectedSpecificDate = true; fetchOrders(true); }"
            />

            <VSelect
              v-if="isSuperAdmin"
              v-model="archiveCourierFilter"
              :items="archiveCouriersList"
              label="Курьер"
              density="compact"
              hide-details
              variant="outlined"
              class="max-width-200"
              clearable
              placeholder="Все курьеры"
            />
          </div>

          <!-- Даты для выбранного курьера -->
          <div v-if="archiveCourierFilter && courierDates.length" class="mt-3 overflow-x-auto pb-2">
            <div class="d-flex gap-2" style="min-width: max-content;">
              <span class="text-caption text-grey-darken-1 align-self-center me-1">Даты курьера:</span>
              <VBtn
                v-for="date in courierDates"
                :key="date"
                size="x-small"
                variant="tonal"
                :color="selectedDate === date.split('T')[0] ? 'primary' : 'secondary'"
                class="rounded-lg"
                @click="selectCourierDate(date)"
              >
                {{ formatDate(date) }}
              </VBtn>
            </div>
          </div>
          
          <div v-if="filteredArchiveOrders.length" class="archive-summary mt-3 text-caption text-grey-darken-1 d-flex align-center flex-wrap gap-x-4 gap-y-2">
            <div class="d-flex align-center">
              <VIcon icon="bx-package" size="16" class="me-1" />
              Заказов: <span class="font-weight-bold ms-1 text-primary">{{ filteredArchiveOrders.length }}</span>
            </div>
            <div class="d-flex align-center">
              <VIcon icon="bx-wallet" size="16" class="me-1" />
              Сумма: <span class="font-weight-bold ms-1 text-primary">{{ filteredArchiveOrders.reduce((acc, o) => acc + parseFloat(o.total_with_discount || o.sum || 0), 0).toFixed(2) }} ₽</span>
            </div>
            <VSpacer />
            <div class="d-flex align-center">
              <VCheckbox
                v-model="archiveSortByCourier"
                label="Сортировка по курьеру"
                density="compact"
                hide-details
                color="primary"
                class="mt-n1"
              />
              <VCheckbox
                v-model="archiveGroupByCourier"
                label="Группировать"
                density="compact"
                hide-details
                color="primary"
                class="mt-n1 ms-2"
              />
            </div>
          </div>
        </div>

        <div v-if="loading && !archiveOrders.length" class="text-center py-12">
          <VProgressCircular indeterminate color="primary" size="48" />
        </div>
        <div 
          v-if="!filteredArchiveOrders.length && !loading" 
          class="empty-state text-center py-16"
        >
          <VIcon 
            size="64" 
            color="grey-lighten-2" 
            icon="bx-archive" 
            class="mb-4" 
          />
          <h3 class="text-h6 font-weight-bold">Архив пуст</h3>
          <p class="text-body-2 text-grey">
            {{ selectedDate === new Date().toISOString().substr(0, 10) ? 'Доставок за сегодня еще не было' : 'За выбранный период доставок не найдено' }}
          </p>
        </div>
        <!-- Список заказов (Обычный или Сгруппированный) -->
        <div v-if="archiveGroupByCourier && groupedArchiveOrders" class="pa-2">
          <div v-for="group in groupedArchiveOrders" :key="group.name" class="courier-group-section mb-8">
            <div class="d-flex align-center mb-4 bg-primary-lighten-5 pa-4 rounded-xl border-dashed">
               <VAvatar size="40" color="primary" class="me-3">
                 <VIcon icon="bx-user" color="white" />
               </VAvatar>
               <div>
                 <h3 class="text-h6 font-weight-bold mb-0">{{ group.name }}</h3>
                 <div class="text-caption text-primary font-weight-medium">Итоги за день</div>
               </div>
               <VSpacer />
               <div class="text-right">
                 <div class="d-flex align-center justify-end mb-1">
                   <VChip color="primary" size="small" variant="flat" class="me-2">{{ group.count }} заказов</VChip>
                   <VChip color="success" size="small" variant="flat">{{ group.total.toFixed(0) }} ₽</VChip>
                 </div>
               </div>
            </div>
            
            <VRow>
              <VCol
                v-for="order in group.orders"
                :key="order.id"
                cols="12"
                md="6"
                lg="4"
              >
                <OrderArchiveCard :order="order" @open-details="openDetails" />
              </VCol>
            </VRow>
          </div>
        </div>

        <VRow v-else class="pa-2">
          <VCol
            v-for="order in filteredArchiveOrders"
            :key="order.id"
            cols="12"
            md="6"
            lg="4"
          >
            <OrderArchiveCard :order="order" @open-details="openDetails" />
          </VCol>
        </VRow>

        <!-- Пагинация -->
        <div v-if="archiveTotalPages > 1" class="pa-4 d-flex justify-center">
          <VPagination
            v-model="archivePage"
            :length="archiveTotalPages"
            total-visible="5"
            rounded="circle"
            density="comfortable"
          />
        </div>
      </VWindowItem>

      <!-- Вкладка: Смены -->
      <VWindowItem value="shifts">
        <div v-if="shifts.length" class="shifts-list">
          <VCard
            v-for="shift in shifts"
            :key="shift.id"
            class="mb-3 rounded-xl border"
            elevation="0"
          >
            <VCardItem>
              <template #prepend>
                <div class="shift-icon-box bg-success-lighten-5 rounded-circle pa-3 me-3">
                  <VIcon icon="bx-store" color="success" />
                </div>
              </template>
              <VCardTitle class="text-body-1 font-weight-bold">
                Смена №{{ shift.id.substring(0, 8) }}
              </VCardTitle>
              <VCardSubtitle>Открыта: {{ formatDate(shift.openDate) }}</VCardSubtitle>
              <template #append>
                <VChip color="success" variant="flat" size="small">ОТКРЫТА</VChip>
              </template>
            </VCardItem>
          </VCard>
        </div>
        <div v-else class="text-center py-12">
          <VIcon size="64" color="grey-lighten-2" icon="bx-calendar-x" />
          <p class="mt-4 text-grey font-weight-medium">Активных смен нет</p>
        </div>
      </VWindowItem>

      <!-- Вкладка: Курьеры -->
      <VWindowItem value="couriers">
        <VRow v-if="activeCouriers.length">
          <VCol v-for="courier in activeCouriers" :key="courier.id" cols="12" sm="6">
            <VCard class="courier-status-card pa-4 rounded-xl border" elevation="0">
              <div class="d-flex align-center">
                <VAvatar size="48" color="primary-lighten-4" class="me-4">
                  <VIcon icon="bx-user" color="primary" />
                </VAvatar>
                <div>
                  <h4 class="text-h6 font-weight-bold mb-0">{{ courier.name || courier.id.substring(0,8) }}</h4>
                  <p class="text-caption text-success mb-0 font-weight-bold d-flex align-center">
                    <span class="pulse-dot me-1"></span> В сети
                  </p>
                </div>
              </div>
            </VCard>
          </VCol>
        </VRow>
        <div v-else class="text-center py-12">
          <VIcon size="64" color="grey-lighten-2" icon="bx-user-x" />
          <p class="mt-4 text-grey font-weight-medium">Нет курьеров онлайн</p>
        </div>
      </VWindowItem>
    </VWindow>

    <!-- Диалог деталей заказа (Стандартизированный) -->
    <OrderDetailModal
      v-if="detailsOrder"
      v-model="showDetailsDialog"
      :order="detailsOrder"
      :is-read-only="false"
      @status-updated="handleStatusUpdated"
    />

    <!-- Диалог закрытия заказа -->
    <VDialog v-model="showCloseDialog" max-width="450px" persistent>
      <VCard class="rounded-xl overflow-hidden">
        <div class="bg-primary pa-6 text-white d-flex align-center">
          <VIcon icon="bx-wallet" size="32" class="me-3" />
          <div>
            <h3 class="text-h5 font-weight-bold">Оплата заказа</h3>
            <p class="text-caption mb-0 opacity-80">Финальный шаг доставки</p>
          </div>
          <VSpacer />
          <VBtn icon="bx-x" variant="text" color="white" @click="showCloseDialog = false" />
        </div>

        <VCardText class="pa-6">
          <div class="d-flex justify-space-between align-center mb-6 pa-4 rounded-lg bg-primary-lighten-5">
            <span class="text-body-1 font-weight-bold text-primary">К ОПЛАТЕ:</span>
            <span class="text-h4 font-weight-black text-primary">{{ selectedOrder?.sum }} ₽</span>
          </div>
          
          <p class="text-subtitle-2 font-weight-bold mb-3 text-grey-darken-1 text-uppercase">Выберите способ оплаты:</p>
          
          <VList class="payment-type-list pa-0" bg-color="transparent">
            <VListItem
              v-for="pt in paymentTypes"
              :key="pt.iiko_id"
              :active="selectedPaymentType === pt.iiko_id"
              color="primary"
              variant="tonal"
              class="rounded-lg mb-2 py-3 border"
              @click="selectedPaymentType = pt.iiko_id"
            >
              <template #prepend>
                <VIcon :icon="pt.kind === 'Cash' ? 'bx-money' : 'bx-credit-card'" class="me-3" />
              </template>
              <VListItemTitle class="font-weight-bold">{{ pt.name }}</VListItemTitle>
              <template #append>
                <VIcon v-if="selectedPaymentType === pt.iiko_id" icon="bx-check-circle" color="primary" />
              </template>
            </VListItem>
          </VList>
        </VCardText>

        <VCardActions class="pa-6 pt-0">
          <VBtn
            block
            color="primary"
            variant="flat"
            size="x-large"
            :disabled="!selectedPaymentType || loading"
            :loading="loading"
            @click="closeOrderAction"
            class="rounded-lg font-weight-bold text-uppercase"
          >
            Завершить доставку
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </VContainer>
</template>

<style scoped>
@import "@styles/courier.css";
</style>
