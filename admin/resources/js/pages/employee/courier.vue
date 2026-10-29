<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { getAuthHeaders, authState, hasPermission } from '@/utils/auth'
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
const showChangePaymentDialog = ref(false)
const changePaymentOrder = ref(null)
const isDeliveryConfirmation = ref(false)
const changePaymentMode = ref('single')
const singlePaymentType = ref(null)
const splitCashSum = ref(0)
const splitCardSum = ref(0)
const preferredNavigator = ref(localStorage.getItem('preferred_navigator') || 'yandex')
const sbpSuccessOrders = ref(new Set())

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

// Проверка, полностью ли оплачен заказ в iiko (или онлайн-предоплата)
const isOrderFullyPaid = order => {
  if (!order) return false

  // 1. Успешная оплата по СБП в текущей сессии
  if (sbpSuccessOrders.value && sbpSuccessOrders.value.has(order.id)) {
    return true
  }

  const left = parseFloat(order.left_to_pay ?? 0)
  const total = parseFloat(order.total_with_discount || order.sum || order.total_amount || 0)

  // 2. Флаг order.is_paid в базе данных при отсутствии остатка к доплате
  if (order.is_paid) {
    if (isNaN(left) || left <= 0) {
      return true
    }
  }

  // 3. Если в БД зафиксирован остаток к оплате (> 0.05 руб), заказ НЕ оплачен курьеру
  if (!isNaN(left) && left > 0.05) {
    return false
  }

  // 4. Проверка фактических онлайн-предоплат в payments_details из iiko Cloud
  if (order.payments_details && Array.isArray(order.payments_details.items) && order.payments_details.items.length > 0) {
    // Суммируем строго подтвержденные предоплаты (is_prepay) или проведенные платежи (is_processed)
    const prepaidSum = order.payments_details.items.reduce((acc, p) => {
      const isDone = p.is_processed === true || p.is_prepay === true
      return acc + (isDone ? (parseFloat(p.sum || p.amount || 0) || 0) : 0)
    }, 0)
    if (total > 0 && prepaidSum >= (total - 0.05)) {
      return true
    }
  }

  return false
}

const getPaymentStatusText = order => {
  if (isOrderFullyPaid(order)) return 'Оплачено'
  const left = parseFloat(order.left_to_pay || 0)
  const total = parseFloat(order.total_with_discount || order.sum || 0)
  if (left > 0 && left < total) return `Частично (ост. ${left} ₽)`

  return 'Ожидает оплаты'
}

const getPaymentStatusColor = order => {
  if (isOrderFullyPaid(order)) return 'success'
  const left = parseFloat(order.left_to_pay || 0)
  const total = parseFloat(order.total_with_discount || order.sum || 0)
  if (left > 0 && left < total) return 'warning'

  return 'error'
}

const getPaymentStatusIcon = order => {
  if (isOrderFullyPaid(order)) return 'bx-check-shield'
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
  // 1. Check local manual click time (10s minimal debounce against accidental double click)
  const clickTime = manualClickTimes.value[order.id]
  if (clickTime) {
    if ((Date.now() - clickTime) >= 10000) return true
    return false
  }
  
  // 2. Check server-provided on_the_way_time
  if (order.on_the_way_time) {
    const onWayDate = new Date(order.on_the_way_time)
    if (!isNaN(onWayDate.getTime())) {
      if ((Date.now() - onWayDate.getTime()) >= 10000) return true
    }
  }
  
  // If order is already in OnWay / delivering from server, allow delivery confirmation
  return true
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
const ws = ref(null)

const isSuperAdmin = computed(() => !!authState.user?.is_superuser)
const isAdmin = computed(() => isSuperAdmin.value || !!authState.user?.is_admin || hasPermission('couriers_manage') || hasPermission('courier_view'))

// Персональный статус смены курьера (п. 2 ТЗ)
const myShiftStatus = ref({
  is_courier: false,
  is_shift_open: false,
  courier_name: '',
  terminal_group_name: '',
  loading: false
})
const shiftOpening = ref(false)

const fetchMyShiftStatus = async () => {
  try {
    const res = await fetch('/api/v1/courier/my-shift-status', {
      headers: getAuthHeaders()
    })
    const data = await res.json()
    if (data.status === 'success') {
      myShiftStatus.value = {
        is_courier: data.is_courier,
        is_shift_open: data.is_shift_open,
        courier_name: data.courier_name,
        terminal_group_name: data.terminal_group_name || '',
        loading: false
      }
    }
  } catch (err) {
    console.error('Error fetching my shift status:', err)
  }
}

const openMyShift = async () => {
  shiftOpening.value = true
  try {
    const res = await fetch('/api/v1/courier/open-shift', {
      method: 'POST',
      headers: getAuthHeaders()
    })
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      toast.success('Смена в iiko успешно открыта!')
      myShiftStatus.value.is_shift_open = true
      await fetchMyShiftStatus()
      await fetchOrders()
    } else {
      toast.error(data.detail || data.message || 'Не удалось открыть смену в iiko')
    }
  } catch (err) {
    toast.error('Ошибка сети при открытии смены')
  } finally {
    shiftOpening.value = false
  }
}

// Принятие заказа курьером (п. 5 ТЗ)
const orderAccepting = ref({})
const acceptCourierDelivery = async (orderId) => {
  orderAccepting.value[orderId] = true
  try {
    const res = await fetch(`/api/v1/courier/orders/${orderId}/accept-order`, {
      method: 'POST',
      headers: getAuthHeaders()
    })
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      toast.success('Заказ принят!')
      const o = orders.value.find(ord => ord.id === orderId || ord.iiko_order_id === orderId)
      if (o) {
        o.courier_notification_status = 'accepted'
      }
    } else {
      toast.error(data.detail || data.message || 'Ошибка принятия заказа')
    }
  } catch (err) {
    toast.error('Ошибка сети при принятии заказа')
  } finally {
    orderAccepting.value[orderId] = false
  }
}

// Управление всеми курьерами для админов (п. 3 ТЗ)
const allCouriers = ref([])
const courierFilterTab = ref('all')
const courierSearch = ref('')
const adminShiftLoading = ref({})

const fetchAllCouriersWithShifts = async (force = false) => {
  try {
    const url = force ? '/api/v1/courier/all-couriers-shifts?force=true' : '/api/v1/courier/all-couriers-shifts'
    const res = await fetch(url, {
      headers: getAuthHeaders(),
    })
    const data = await res.json()
    if (data.status === 'success') {
      allCouriers.value = data.data || []
    }
  } catch (err) {
    console.error('Error fetching couriers with shifts:', err)
  }
}

// Стоп-слова для исключения системных и служебных аккаунтов на клиенте
const SYSTEM_COURIER_STOP_WORDS = [
  'администратор', 'пользователь', 'системный', 'системная', 
  'учетная', 'юзер', 'user', 'admin', 'админ', 'iiko'
]

const isSystemCourier = name => {
  if (!name) return false
  const lower = name.toLowerCase()
  return SYSTEM_COURIER_STOP_WORDS.some(w => lower.includes(w))
}

const activeVisibleCouriersCount = computed(() => allCouriers.value.filter(c => !isSystemCourier(c.name) && !c.is_hidden).length)
const openShiftCouriersCount = computed(() => allCouriers.value.filter(c => !isSystemCourier(c.name) && !c.is_hidden && c.is_shift_open).length)
const closedShiftCouriersCount = computed(() => allCouriers.value.filter(c => !isSystemCourier(c.name) && !c.is_hidden && !c.is_shift_open).length)
const hiddenCouriersCount = computed(() => allCouriers.value.filter(c => !isSystemCourier(c.name) && c.is_hidden).length)

const filteredCouriers = computed(() => {
  let list = allCouriers.value.filter(c => !isSystemCourier(c.name))

  if (courierFilterTab.value === 'hidden') {
    list = list.filter(c => c.is_hidden)
  } else {
    // В обычных табах скрытые не показываются
    list = list.filter(c => !c.is_hidden)
    if (courierFilterTab.value === 'open') {
      list = list.filter(c => c.is_shift_open)
    } else if (courierFilterTab.value === 'closed') {
      list = list.filter(c => !c.is_shift_open)
    }
  }

  if (courierSearch.value) {
    const q = courierSearch.value.toLowerCase().trim()
    list = list.filter(c => 
      (c.name && c.name.toLowerCase().includes(q)) || 
      (c.phone && c.phone.includes(q)) ||
      (c.code && String(c.code).includes(q))
    )
  }
  return list
})

// Скрытие и восстановление курьеров
const courierHideLoading = ref({})

const adminHideCourier = async (courier) => {
  const cId = courier.iiko_id
  if (!cId) return
  courierHideLoading.value[cId] = true
  try {
    const res = await fetch('/api/v1/courier/admin/hide-courier', {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ employee_iiko_id: cId })
    })
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      courier.is_hidden = true
      toast.info(`Курьер ${courier.name} перемещен в скрытые`)
    } else {
      toast.error(data.detail || data.message || 'Ошибка скрытия курьера')
    }
  } catch (err) {
    toast.error('Ошибка сети при скрытии курьера')
  } finally {
    courierHideLoading.value[cId] = false
  }
}

const adminUnhideCourier = async (courier) => {
  const cId = courier.iiko_id
  if (!cId) return
  courierHideLoading.value[cId] = true
  try {
    const res = await fetch('/api/v1/courier/admin/unhide-courier', {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ employee_iiko_id: cId })
    })
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      courier.is_hidden = false
      toast.success(`Курьер ${courier.name} возвращен в общий список`)
    } else {
      toast.error(data.detail || data.message || 'Ошибка восстановления курьера')
    }
  } catch (err) {
    toast.error('Ошибка сети при восстановлении курьера')
  } finally {
    courierHideLoading.value[cId] = false
  }
}

// Открытие/закрытие смены админом
const adminOpenCourierShift = async (courier) => {
  const cId = courier.iiko_id
  adminShiftLoading.value[cId] = true
  try {
    const res = await fetch('/api/v1/courier/admin/open-shift', {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ employee_iiko_id: cId })
    })
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      toast.success(`Смена курьера ${courier.name} открыта в iiko`)
      courier.is_shift_open = true
      await fetchAllCouriersWithShifts(true)
    } else {
      toast.error(data.detail || data.message || 'Ошибка открытия смены')
    }
  } catch (err) {
    toast.error('Ошибка сети при открытии смены')
  } finally {
    adminShiftLoading.value[cId] = false
  }
}

const adminCloseCourierShift = async (courier) => {
  const cId = courier.iiko_id
  adminShiftLoading.value[cId] = true
  try {
    const res = await fetch('/api/v1/courier/admin/close-shift', {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ employee_iiko_id: cId })
    })
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      toast.success(`Смена курьера ${courier.name} закрыта в iiko`)
      courier.is_shift_open = false
      await fetchAllCouriersWithShifts(true)
    } else {
      toast.error(data.detail || data.message || 'Ошибка закрытия смены')
    }
  } catch (err) {
    toast.error('Ошибка сети при закрытии смены')
  } finally {
    adminShiftLoading.value[cId] = false
  }
}

// --- Детализированный отчет по доставкам курьера ---
const showCourierReportDialog = ref(false)
const reportCourier = ref(null)
const reportPeriod = ref('month')
const reportDateFrom = ref('')
const reportDateTo = ref('')
const reportLoading = ref(false)
const reportData = ref(null)
const expandedReportDays = ref([])

const openCourierReport = async (courier) => {
  reportCourier.value = courier
  reportPeriod.value = 'month'
  reportDateFrom.value = ''
  reportDateTo.value = ''
  showCourierReportDialog.value = true
  await fetchCourierReport()
}

const fetchCourierReport = async () => {
  if (!reportCourier.value) return
  reportLoading.value = true
  
  try {
    let df = ''
    let dt = ''
    const now = new Date()
    
    if (reportPeriod.value === 'today') {
      df = formatDateLocal(now)
      dt = formatDateLocal(now)
    } else if (reportPeriod.value === 'yesterday') {
      const y = new Date(now)
      y.setDate(y.getDate() - 1)
      df = formatDateLocal(y)
      dt = formatDateLocal(y)
    } else if (reportPeriod.value === '7days') {
      const d = new Date(now)
      d.setDate(d.getDate() - 6)
      df = formatDateLocal(d)
      dt = formatDateLocal(now)
    } else if (reportPeriod.value === '30days') {
      const d = new Date(now)
      d.setDate(d.getDate() - 29)
      df = formatDateLocal(d)
      dt = formatDateLocal(now)
    } else if (reportPeriod.value === 'month') {
      const y = now.getFullYear()
      const m = String(now.getMonth() + 1).padStart(2, '0')
      df = `${y}-${m}-01`
      dt = formatDateLocal(now)
    } else if (reportPeriod.value === 'custom') {
      df = reportDateFrom.value
      dt = reportDateTo.value
    }
    
    const params = new URLSearchParams()
    if (reportCourier.value.name) params.append('courier_name', reportCourier.value.name)
    if (reportCourier.value.iiko_id) params.append('courier_iiko_id', reportCourier.value.iiko_id)
    if (df) params.append('date_from', df)
    if (dt) params.append('date_to', dt)
    
    const res = await fetch(`/api/v1/courier/admin/courier-report?${params.toString()}`, {
      headers: getAuthHeaders()
    })
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      reportData.value = data.data
      if (data.data?.days?.length) {
        expandedReportDays.value = [data.data.days[0].date]
      } else {
        expandedReportDays.value = []
      }
    } else {
      toast.error(data.detail || data.message || 'Ошибка загрузки отчета')
    }
  } catch (err) {
    console.error('Error loading courier report:', err)
    toast.error('Ошибка сети при загрузке отчета')
  } finally {
    reportLoading.value = false
  }
}

const canAcceptOrder = order => {
  const isUnassigned = !order.courier_name || order.courier_name === 'Не назначен'
  const hasAccess = isSuperAdmin.value || hasPermission('courier_view_unassigned')
  const isOrderStatusActive = ['new', 'confirmed', 'preparing', 'cooking', 'ready'].includes(order.status.toLowerCase())
  return isUnassigned && hasAccess && isOrderStatusActive
}

const acceptOrder = async orderId => {
  loading.value = true
  try {
    const res = await fetch(`/api/v1/courier/orders/${orderId}/accept`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })

    const data = await res.json()
    if (res.ok && data.status === 'success') {
      toast.success(data.message || 'Вы успешно назначены на доставку')
      await fetchOrders()
    } else {
      toast.error(data.detail || data.message || 'Не удалось взять доставку')
    }
  } catch (e) {
    toast.error('Ошибка сети при взятии доставки')
    console.error(e)
  } finally {
    loading.value = false
  }
}

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
    
    await fetchMyShiftStatus()
    if (activeTab.value === 'orders') {
      await fetchOrders()
    } else if (activeTab.value === 'archive') {
      await fetchOrders(true)
    } else if (activeTab.value === 'shifts') {
      await fetchShifts()
    } else if (activeTab.value === 'couriers') {
      await fetchAllCouriersWithShifts()
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
      
      // Auto-open payment dialog only if NOT silent and order is not fully paid
      if (status === 'Delivered' && !silent) {
        const order = orders.value.find(o => o.id === orderId)
        if (order && !isOrderFullyPaid(order)) await openCloseDialog(order)
      }
    } else {
      const data = await res.json()
      toast.error(data.detail || data.message || 'Не удалось обновить статус')
    }
  } catch (e) {
    toast.error('Ошибка сети при обновлении статуса')
  } finally {
    loading.value = false
  }
}

const openCloseDialog = async order => {
  if (isOrderFullyPaid(order)) {
    toast.info('Заказ уже полностью оплачен в iiko')
    return
  }
  await fetchPaymentTypes()
  selectedOrder.value = order
  selectedPaymentType.value = null
  if (order.payment_method) {
    const pt = paymentTypes.value.find(p => p.name.toLowerCase().includes(order.payment_method.toLowerCase()))
    if (pt) selectedPaymentType.value = pt.iiko_id
  }
  if (!selectedPaymentType.value && paymentTypes.value.length > 0) {
    const defaultPt = getCardPaymentType() || getCashPaymentType() || paymentTypes.value[0]
    if (defaultPt) selectedPaymentType.value = defaultPt.iiko_id
  }
  showCloseDialog.value = true
}

const closeOrderAction = async () => {
  if (!selectedPaymentType.value) {
    toast.error('Выберите тип оплаты')
    return
  }
  
  loading.value = true
  try {
    const orderId = selectedOrder.value.id
    const amount = Number(selectedOrder.value.left_to_pay || selectedOrder.value.total_with_discount || selectedOrder.value.sum || 0)
    const ptId = selectedPaymentType.value
    
    const res = await fetch(`/api/v1/courier/orders/${orderId}/close?payment_type_id=${ptId}&amount=${amount}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      toast.success(data.message || 'Заказ успешно доставлен и закрыт')
      showCloseDialog.value = false
      selectedOrder.value = null
      selectedPaymentType.value = null
      await fetchData(true)
    } else {
      toast.error(data.detail || data.message || 'Ошибка при закрытии заказа')
    }
  } catch (e) {
    console.error('Close order error:', e)
    toast.error('Ошибка сети при закрытии заказа')
  } finally {
    loading.value = false
  }
}

const getCashPaymentType = () => {
  return paymentTypes.value.find(pt => pt.is_courier_cash)
}

const getCardPaymentType = () => {
  return paymentTypes.value.find(pt => pt.is_courier_card)
}

const currentPaymentKind = computed(() => {
  if (!changePaymentOrder.value) return null
  const details = changePaymentOrder.value.payments_details
  if (details && Array.isArray(details.items)) {
    const livePayments = details.items.filter(item => {
      const name = (item.name || '').toLowerCase()
      const kind = (item.kind || '').toLowerCase()
      return kind !== 'iikocard' && !name.includes('бонус') && !name.includes('bonus')
    })
    if (livePayments.length === 1) {
      const k = (livePayments[0].kind || '').toLowerCase()
      const n = (livePayments[0].name || '').toLowerCase()
      if (k === 'cash' || n.includes('нал')) return 'Cash'
      if (k === 'card' || n.includes('карт')) return 'Card'
      return livePayments[0].kind
    } else if (livePayments.length > 1) {
      return 'Split'
    }
  }
  const method = (changePaymentOrder.value.payment_method || '').toLowerCase()
  if (method.includes('нал')) return 'Cash'
  if (method.includes('карт')) return 'Card'
  return null
})

const openChangePaymentDialog = async (order, isDeliveryConfirm = false) => {
  if (isOrderFullyPaid(order)) {
    toast.info('Заказ уже полностью оплачен в iiko')
    return
  }
  await fetchPaymentTypes()
  changePaymentOrder.value = order
  isDeliveryConfirmation.value = isDeliveryConfirm
  changePaymentMode.value = 'single'
  splitCashSum.value = 0
  splitCardSum.value = 0
  
  // Автоматически отображаем активным способ оплаты, если таковой уже выбран в iiko / заказе
  const currentKind = currentPaymentKind.value
  const cashPt = getCashPaymentType()
  const cardPt = getCardPaymentType()
  
  if (currentKind === 'Cash') {
    singlePaymentType.value = cashPt ? cashPt.iiko_id : null
  } else if (currentKind === 'Card') {
    singlePaymentType.value = cardPt ? cardPt.iiko_id : null
  } else if (currentKind === 'Split') {
    changePaymentMode.value = 'split'
    if (order.payments_details?.items) {
      for (const it of order.payments_details.items) {
        const k = (it.kind || '').toLowerCase()
        const n = (it.name || '').toLowerCase()
        if (k === 'cash' || n.includes('нал')) splitCashSum.value = Number(it.sum || 0)
        if (k === 'card' || n.includes('карт')) splitCardSum.value = Number(it.sum || 0)
      }
    }
  } else {
    // Способ оплаты не выбран
    singlePaymentType.value = null
  }
  
  showChangePaymentDialog.value = true
}

const openSbpFromChangePayment = () => {
  const order = changePaymentOrder.value
  showChangePaymentDialog.value = false
  if (order) {
    openSbpPayment(order)
  }
}

const handleSplitSumChange = field => {
  const maxPaySum = Number(changePaymentOrder.value?.left_to_pay || 0)
  if (field === 'cash') {
    if (splitCashSum.value > maxPaySum) {
      splitCashSum.value = maxPaySum
    }
    splitCardSum.value = Number((maxPaySum - splitCashSum.value).toFixed(2))
  } else {
    if (splitCardSum.value > maxPaySum) {
      splitCardSum.value = maxPaySum
    }
    splitCashSum.value = Number((maxPaySum - splitCardSum.value).toFixed(2))
  }
}

const isSplitValid = computed(() => {
  if (!changePaymentOrder.value) return false
  const maxPaySum = Number(changePaymentOrder.value.left_to_pay || 0)
  const sum = Number(splitCashSum.value) + Number(splitCardSum.value)
  return Math.abs(sum - maxPaySum) < 0.01 && splitCashSum.value >= 0 && splitCardSum.value >= 0
})

const submitPaymentChange = async () => {
  if (!changePaymentOrder.value) return
  loading.value = true
  
  const targetOrder = changePaymentOrder.value
  const payload = { payments: [] }
  if (changePaymentMode.value === 'single') {
    if (!singlePaymentType.value) {
      toast.error('Выберите способ оплаты')
      loading.value = false
      return
    }
    payload.payments.push({
      payment_type_id: singlePaymentType.value,
      sum: Number(targetOrder.left_to_pay || targetOrder.sum || 0)
    })
  } else {
    if (!isSplitValid.value) {
      toast.error('Сумма платежей должна в точности быть равна остатку к оплате')
      loading.value = false
      return
    }
    const cashPt = getCashPaymentType()
    const cardPt = getCardPaymentType()
    
    if (splitCashSum.value > 0) {
      if (!cashPt) {
        toast.error('Тип оплаты "Наличные" не найден')
        loading.value = false
        return
      }
      payload.payments.push({
        payment_type_id: cashPt.iiko_id,
        sum: Number(splitCashSum.value)
      })
    }
    
    if (splitCardSum.value > 0) {
      if (!cardPt) {
        toast.error('Тип оплаты "Картой курьеру" не найден')
        loading.value = false
        return
      }
      payload.payments.push({
        payment_type_id: cardPt.iiko_id,
        sum: Number(splitCardSum.value)
      })
    }
  }
  
  try {
    const res = await fetch(`/api/v1/courier/orders/${targetOrder.id}/change-payment-type`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      if (isDeliveryConfirmation.value) {
        // Если выбор способа производился при нажатии кнопки "Доставлен" — переводим заказ в статус Delivered
        const statusRes = await fetch(`/api/v1/courier/orders/${targetOrder.id}/status?status=Delivered`, {
          method: 'POST',
          headers: getAuthHeaders(),
        })
        if (statusRes.ok) {
          toast.success('Способ оплаты сохранен, заказ успешно доставлен!')
        } else {
          toast.success('Способ оплаты сохранен в iiko')
        }
      } else {
        toast.success('Способ оплаты успешно изменен в iiko')
      }
      showChangePaymentDialog.value = false
      await fetchData(true)
    } else {
      toast.error(data.detail || 'Не удалось изменить способ оплаты')
    }
  } catch (e) {
    console.error('Error changing payment type:', e)
    toast.error('Ошибка сети при смене способа оплаты')
  } finally {
    loading.value = false
  }
}

// Проверка, указан ли у заказа способ оплаты
const hasOrderPaymentMethod = order => {
  if (!order) return false
  
  // Если заказ уже полностью оплачен в iiko или онлайн
  if (isOrderFullyPaid(order)) {
    return true
  }

  // Проверяем элементы платежей payments_details (исключая чисто бонусные списания)
  if (order.payments_details && Array.isArray(order.payments_details.items) && order.payments_details.items.length > 0) {
    const nonBonusPayments = order.payments_details.items.filter(item => {
      const name = (item.name || '').toLowerCase()
      const kind = (item.kind || '').toLowerCase()
      return kind !== 'iikocard' && !name.includes('бонус') && !name.includes('bonus')
    })
    if (nonBonusPayments.length > 0) {
      return true
    }
  }

  // Проверяем текстовую строку payment_method
  const method = (order.payment_method || '').trim().toLowerCase()
  if (!method || method === '-' || method === '—' || method === 'не указан' || method === 'не указано') {
    return false
  }

  // Если указано только списание бонусов без указания способа расчета
  if (method.includes('бонус') && !method.includes('нал') && !method.includes('карт') && !method.includes('сбп') && !method.includes('сайт')) {
    return false
  }

  return true
}

// Обработчик клика кнопки "Доставлен" курьером
const handleDeliveredClick = async order => {
  if (!order) return
  if (isOrderFullyPaid(order)) {
    await updateStatus(order.id, 'Delivered', true)
    return
  }
  // Для неоплаченных заказов курьер обязательно подтверждает способ расчета перед завершением доставки
  toast.info('Подтвердите способ оплаты для завершения доставки.')
  await openChangePaymentDialog(order, true)
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

// Проверка, находится ли заказ в статусе приготовлен (ready) или передан курьеру/в пути (delivering/onway)
const isOrderReadyOrDelivering = order => {
  if (!order || !order.status) return false
  const st = String(order.status).toLowerCase()
  return ['ready', 'readyfordelivery', 'waiting', 'delivering', 'onway'].includes(st)
}

// Заказы, которые еще не приготовлены и не в доставке (блеклый вид карточки)
const isOrderDimmed = order => {
  return !isOrderReadyOrDelivering(order)
}

// Определение точного времени перехода в статус (приготовлен или отправлен)
const getOrderStatusChangeTime = order => {
  if (!order) return 0
  const st = String(order.status || '').toLowerCase()
  
  // Для заказов в доставке ("передан курьеру / в пути")
  if (['delivering', 'onway'].includes(st)) {
    if (order.on_the_way_time) {
      const t = new Date(order.on_the_way_time).getTime()
      if (!isNaN(t) && t > 0) return t
    }
    if (Array.isArray(order.status_history) && order.status_history.length) {
      for (let i = order.status_history.length - 1; i >= 0; i--) {
        const h = order.status_history[i]
        const hStatus = String(h?.status || '').toLowerCase()
        if (['delivering', 'onway'].includes(hStatus) && h.time) {
          const t = new Date(h.time).getTime()
          if (!isNaN(t) && t > 0) return t
        }
      }
    }
  }

  // Для заказов в статусе "приготовлен / готов к отправке"
  if (['ready', 'readyfordelivery', 'waiting'].includes(st)) {
    if (order.ready_time) {
      const t = new Date(order.ready_time).getTime()
      if (!isNaN(t) && t > 0) return t
    }
    if (Array.isArray(order.status_history) && order.status_history.length) {
      for (let i = order.status_history.length - 1; i >= 0; i--) {
        const h = order.status_history[i]
        const hStatus = String(h?.status || '').toLowerCase()
        if (['ready', 'readyfordelivery', 'waiting'].includes(hStatus) && h.time) {
          const t = new Date(h.time).getTime()
          if (!isNaN(t) && t > 0) return t
        }
      }
    }
  }

  // Фолбэк на статусное время, время готовки или дату создания
  if (order.status_changed_at) {
    const t = new Date(order.status_changed_at).getTime()
    if (!isNaN(t) && t > 0) return t
  }
  if (Array.isArray(order.status_history) && order.status_history.length) {
    const last = order.status_history[order.status_history.length - 1]
    if (last?.time) {
      const t = new Date(last.time).getTime()
      if (!isNaN(t) && t > 0) return t
    }
  }
  if (order.cooking_time_updated_at) {
    const t = new Date(order.cooking_time_updated_at).getTime()
    if (!isNaN(t) && t > 0) return t
  }
  if (order.created_at) {
    const t = new Date(order.created_at).getTime()
    if (!isNaN(t) && t > 0) return t
  }
  return 0
}

// Сортировка доставок:
// 1. Вверху: заказы в статусе "приготовлен" или "передан курьеру (доставка)"
//    Очередность внутри: строго согласно порядку смены статуса (приготовлен или отправлен, FIFO)
// 2. Внизу: еще не приготовленные заказы (блеклые), отсортированные по ожидаемому времени готовности
const sortedOrders = computed(() => {
  if (!orders.value || !orders.value.length) return []

  const readyOrDelivering = []
  const pendingOrders = []

  for (const order of orders.value) {
    if (isOrderReadyOrDelivering(order)) {
      readyOrDelivering.push(order)
    } else {
      pendingOrders.push(order)
    }
  }

  // Сортировка готовых/в пути по времени перехода в этот статус (FIFO: кто раньше сменил статус, тот выше)
  readyOrDelivering.sort((a, b) => {
    const timeA = getOrderStatusChangeTime(a)
    const timeB = getOrderStatusChangeTime(b)
    if (timeA !== timeB) {
      return timeA - timeB
    }
    return (a.id || 0) - (b.id || 0)
  })

  // Сортировка неприготовленных по ожидаемому времени готовности или дате создания
  pendingOrders.sort((a, b) => {
    const timeA = a.expected_time ? new Date(a.expected_time).getTime() : (a.created_at ? new Date(a.created_at).getTime() : 0)
    const timeB = b.expected_time ? new Date(b.expected_time).getTime() : (b.created_at ? new Date(b.created_at).getTime() : 0)
    if (timeA !== timeB) {
      return timeA - timeB
    }
    return (a.id || 0) - (b.id || 0)
  })

  return [...readyOrDelivering, ...pendingOrders]
})


const formatAddress = order => {
  if (!order) return 'Адрес не указан'
  if (order.order_type === 'Самовывоз') return '🙍 Самовывоз'
  
  const a = (order.address && typeof order.address === 'object') ? order.address : {}
  const baseAddr = (order.delivery_address || (typeof order.address === 'string' ? order.address : (a.line1 || '')) || '').trim()

  const ent = (order.entrance || a.entrance || '').toString().trim()
  const flr = (order.floor || a.floor || '').toString().trim()
  const flt = (order.flat || a.flat || '').toString().trim()
  const dp = (order.doorphone || a.doorphone || '').toString().trim()

  if (baseAddr && baseAddr !== 'Самовывоз' && baseAddr !== 'Адрес не указан') {
    let resultAddr = baseAddr
    const extras = []

    if (ent && ent !== '0' && ent !== '-') {
      const hasEnt = new RegExp(`(?:под(?:ъезд|\\.|\\s*)|(?<=[,\\s])п\\.\\s*)\\s*${ent}\\b`, 'i').test(resultAddr)
      if (!hasEnt) extras.push(`под. ${ent}`)
    }
    if (flr && flr !== '0' && flr !== '-') {
      const hasFlr = new RegExp(`(?:эт(?:аж|\\.|\\s*)|(?<=[,\\s])э\\.\\s*)\\s*${flr}\\b`, 'i').test(resultAddr)
      if (!hasFlr) extras.push(`эт. ${flr}`)
    }
    if (flt && flt !== '0' && flt !== '-') {
      const hasFlt = new RegExp(`(?:кв(?:артира|\\.|\\s*)|оф(?:ис|\\.|\\s*)|пом(?:ещение|\\.|\\s*))\\s*${flt}\\b`, 'i').test(resultAddr)
      if (!hasFlt) extras.push(`кв. ${flt}`)
    }
    if (dp && dp !== '0' && dp !== '-') {
      const hasDp = new RegExp(`(?:код|домофон|д/ф|код\\s*домофона)\\s*[:#]?\\s*${dp}\\b`, 'i').test(resultAddr)
      if (!hasDp) extras.push(`код ${dp}`)
    }

    if (extras.length > 0) {
      resultAddr = `${resultAddr}, ${extras.join(', ')}`
    }
    return resultAddr
  }

  // Если baseAddr пустой, собираем из компонентов
  const parts = []
  const city = order.city || a.city
  if (city) {
    parts.push(city.toLowerCase().startsWith('г.') ? city : `г. ${city}`)
  }
  const street = order.street || a.street
  if (street) {
    if (!/ул\.|пр\.|пер\.|б-р|тракт|шоссе|проезд/i.test(street)) {
      parts.push(`ул. ${street}`)
    } else {
      parts.push(street)
    }
  }
  const house = order.house || a.house || a.home
  if (house && house !== '0' && house !== '-') parts.push(`д. ${house}`)
  if (ent && ent !== '0' && ent !== '-') parts.push(`под. ${ent}`)
  if (flr && flr !== '0' && flr !== '-') parts.push(`эт. ${flr}`)
  if (flt && flt !== '0' && flt !== '-') parts.push(`кв. ${flt}`)
  if (dp && dp !== '0' && dp !== '-') parts.push(`код ${dp}`)

  return parts.length > 0 ? parts.join(', ') : 'Адрес не указан'
}

const openMaps = (order, provider = null) => {
  const addr = formatAddress(order)
  if (!addr || addr === 'Адрес не указан' || addr.includes('Самовывоз')) {
    toast.error('Адрес не указан для этого заказа')
    return
  }
  const nav = provider || preferredNavigator.value
  if (provider) {
    setPreferredNavigator(provider)
  }
  
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent)
  const isAndroid = /Android/i.test(navigator.userAgent)
  
  let webUrl = ''
  let mobileScheme = ''
  
  switch (nav) {
    case 'yandex':
      webUrl = `https://yandex.ru/maps/?text=${encodeURIComponent(addr)}`
      mobileScheme = `yandexmaps://maps.yandex.ru/?text=${encodeURIComponent(addr)}`
      break
    case 'yandexnavi':
      webUrl = `https://yandex.ru/maps/?text=${encodeURIComponent(addr)}`
      mobileScheme = `yandexnavi://map_search?text=${encodeURIComponent(addr)}`
      break
    case '2gis':
      webUrl = `https://2gis.ru/search/${encodeURIComponent(addr)}`
      mobileScheme = `dgis://2gis.ru/search/${encodeURIComponent(addr)}`
      break
    case 'google':
      webUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(addr)}`
      if (isIOS) {
        mobileScheme = `comgooglemaps://?q=${encodeURIComponent(addr)}`
      } else if (isAndroid) {
        mobileScheme = `geo:0,0?q=${encodeURIComponent(addr)}`
      } else {
        mobileScheme = `comgooglemaps://?q=${encodeURIComponent(addr)}`
      }
      break
    case 'petal':
      webUrl = `https://www.petalmaps.com/search/?q=${encodeURIComponent(addr)}`
      mobileScheme = `petalmaps://search?q=${encodeURIComponent(addr)}`
      break
    default:
      webUrl = `https://yandex.ru/maps/?text=${encodeURIComponent(addr)}`
      mobileScheme = `yandexmaps://maps.yandex.ru/?text=${encodeURIComponent(addr)}`
  }
  
  if (isMobile && mobileScheme) {
    const start = Date.now()
    window.location.href = mobileScheme
    
    setTimeout(() => {
      if (Date.now() - start < 1500) {
        window.open(webUrl, '_blank', 'noopener,noreferrer')
      }
    }, 1000)
  } else {
    window.open(webUrl, '_blank', 'noopener,noreferrer')
  }
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
  } else if (val === 'couriers') {
    fetchAllCouriersWithShifts()
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

const connectWs = () => {
  if (ws.value && (ws.value.readyState === WebSocket.OPEN || ws.value.readyState === WebSocket.CONNECTING)) return

  const token = localStorage.getItem('access_token')
  if (!token) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/api/v1/chat/ws?token=${token}`

  ws.value = new WebSocket(wsUrl)

  ws.value.onmessage = event => {
    try {
      const data = JSON.parse(event.data)
      
      // Обработка изменения времени готовности
      if (data.type === 'change_cooking_time') {
        const orderId = data.order_id
        
        // Пытаемся найти заказ среди активных
        const order = orders.value.find(o => o.local_id === orderId || o.id === String(orderId))
        if (order) {
          order.cooking_time_minutes = data.cooking_time_minutes
          order.cooking_time_updated_at = data.cooking_time_updated_at
          toast.info(`Время готовности заказа №${order.number || order.id} изменено: ${data.cooking_time_minutes} мин.`)
        } else {
          fetchData(true)
        }
      }
      
      // Обработка назначения доставки курьеру
      if (data.type === 'courier_delivery' || data.type === 'delivery_assigned') {
        fetchData(true)
        toast.success(`Вам назначена новая доставка!`)
      }

      // Обработка других обновлений заказа
      if (['change_items', 'change_payments', 'order_cancelled', 'order_completed', 'new_order', 'delivery_unassigned', 'change_address', 'order_changed', 'order_status_changed', 'order_delivered'].includes(data.type)) {
        fetchData(true)
      }
    } catch (e) {
      console.error('Error handling WebSocket message:', e)
    }
  }

  ws.value.onclose = () => {
    // Реконнект через 5 секунд, если компонент еще смонтирован
    setTimeout(() => {
      if (activeTab.value) {
        connectWs()
      }
    }, 5000)
  }
}

const showKitchenTimer = order => {
  const activeStatuses = ['new', 'confirmed', 'preparing', 'cooking']
  return order.cooking_time_minutes > 0 && 
         order.cooking_time_updated_at && 
         activeStatuses.includes(order.status.toLowerCase())
}

const isKitchenReady = order => {
  const readyStatuses = ['ready', 'ready_for_pickup', 'delivering', 'onway', 'delivered', 'closed']
  return readyStatuses.includes(order.status.toLowerCase())
}

const getKitchenRemainingMs = order => {
  if (!order.cooking_time_updated_at || !order.cooking_time_minutes) return 0
  const updatedTime = new Date(order.cooking_time_updated_at).getTime()
  const endTime = updatedTime + order.cooking_time_minutes * 60 * 1000
  return endTime - currentTime.value.getTime()
}

const getKitchenTimerText = order => {
  const diffMs = getKitchenRemainingMs(order)
  const isLateness = diffMs < 0
  const absDiff = Math.abs(diffMs)
  const mins = Math.floor(absDiff / 60000)
  const secs = Math.floor((absDiff % 60000) / 1000)
  const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  
  return isLateness ? `Опоздание: -${timeStr}` : `Осталось: ${timeStr}`
}

const getKitchenTimerColor = order => {
  const diffMs = getKitchenRemainingMs(order)
  if (diffMs < 0) return 'error'
  if (diffMs < 5 * 60 * 1000) return 'orange'
  return 'primary'
}

// --- Логика СБП Т-Банка ---
const sbpDialog = ref(false)
const sbpLoading = ref(false)
const sbpQrData = ref(null) // Содержит {id, url, svg}
const sbpOrderStatus = ref('CREATED') // CREATED, PAID, etc.
const sbpOrder = ref(null)
const sbpInterval = ref(null)
const sharingQr = ref(null)

const shareQrCodeViaSocial = async (channel) => {
  if (!sbpQrData.value?.url || !sbpOrder.value) return
  sharingQr.value = channel
  const amount = sbpOrder.value.left_to_pay || sbpOrder.value.total_with_discount || sbpOrder.value.sum || 0
  
  try {
    const res = await fetch(`/api/v1/courier/orders/${sbpOrder.value.local_id}/share-qr`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        channel,
        qr_url: sbpQrData.value.url,
        amount: parseFloat(amount)
      })
    })
    
    if (res.ok) {
      toast.success('Ссылка и QR-код успешно отправлены клиенту')
    } else {
      const d = await res.json()
      toast.error(d.detail || 'Не удалось отправить СБП QR в соцсеть')
    }
  } catch (e) {
    console.error('Share QR error:', e)
    toast.error('Ошибка сети при отправке')
  } finally {
    sharingQr.value = null
  }
}

const openSbpPayment = async (order) => {
  // Закрываем диалог закрытия заказа, если он открыт
  showCloseDialog.value = false
  
  sbpOrder.value = order
  sbpOrderStatus.value = 'CREATED'
  sbpQrData.value = null
  sbpDialog.value = true
  sbpLoading.value = true
  
  const amount = order.left_to_pay || order.total_with_discount || order.sum || 0
  
  try {
    const res = await fetch(`/api/v1/courier/orders/${order.local_id}/sbp-qr`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ amount: parseFloat(amount) })
    })
    
    if (res.ok) {
      const data = await res.json()
      if (data.status === 'success' && data.data) {
        sbpQrData.value = data.data
        // Запускаем опрос статуса
        startSbpPolling()
      } else {
        toast.error('Не удалось сгенерировать QR-код СБП')
        sbpDialog.value = false
      }
    } else {
      const errData = await res.json()
      toast.error(errData.detail || 'Ошибка при запросе к серверу')
      sbpDialog.value = false
    }
  } catch (e) {
    console.error('Sbp error:', e)
    toast.error('Ошибка сети при генерации СБП QR')
    sbpDialog.value = false
  } finally {
    sbpLoading.value = false
  }
}

const startSbpPolling = () => {
  if (sbpInterval.value) clearInterval(sbpInterval.value)
  
  sbpInterval.value = setInterval(async () => {
    if (!sbpQrData.value?.id || !sbpOrder.value) return
    
    try {
      const res = await fetch(`/api/v1/courier/orders/${sbpOrder.value.local_id}/sbp-state/${sbpQrData.value.id}`, {
        headers: getAuthHeaders()
      })
      
      if (res.ok) {
        const data = await res.json()
        if (data.status === 'success' && data.data) {
          const status = data.data.status
          sbpOrderStatus.value = status
          
          if (status === 'PAID') {
            clearInterval(sbpInterval.value)
            sbpInterval.value = null
            
            // Добавляем в список успешных оплат
            sbpSuccessOrders.value.add(sbpOrder.value.id)
            
            toast.success('Оплата по СБП успешно получена!')
            
            // Обновляем данные заказа локально
            sbpOrder.value.is_paid = true
            sbpOrder.value.left_to_pay = 0
            
            // Запускаем обновление всего списка
            setTimeout(async () => {
              await fetchOrders()
            }, 500)
            
            // Автоматически закрываем диалог
            setTimeout(() => {
              closeSbpDialog()
            }, 2000)
          }
        }
      }
    } catch (e) {
      console.error('Error polling SBP status:', e)
    }
  }, 3000)
}

const checkSbpPaymentStatusManually = async () => {
  if (!sbpQrData.value?.id || !sbpOrder.value) return
  sbpLoading.value = true
  
  try {
    const res = await fetch(`/api/v1/courier/orders/${sbpOrder.value.local_id}/sbp-state/${sbpQrData.value.id}`, {
      headers: getAuthHeaders()
    })
    
    if (res.ok) {
      const data = await res.json()
      if (data.status === 'success' && data.data) {
        const status = data.data.status
        sbpOrderStatus.value = status
        
        if (status === 'PAID') {
          if (sbpInterval.value) {
            clearInterval(sbpInterval.value)
            sbpInterval.value = null
          }
          
          sbpSuccessOrders.value.add(sbpOrder.value.id)
          toast.success('Оплата по СБП подтверждена!')
          
          sbpOrder.value.is_paid = true
          sbpOrder.value.left_to_pay = 0
          
          setTimeout(async () => {
            await fetchOrders()
          }, 500)
          
          setTimeout(() => {
            closeSbpDialog()
          }, 1500)
        } else {
          toast.info('Оплата пока не поступила')
        }
      }
    }
  } catch (e) {
    toast.error('Ошибка сети при проверке статуса')
  } finally {
    sbpLoading.value = false
  }
}

const closeSbpDialog = () => {
  sbpDialog.value = false
  if (sbpInterval.value) {
    clearInterval(sbpInterval.value)
    sbpInterval.value = null
  }
}

onMounted(() => {
  fetchData()
  if (isSuperAdmin.value || isAdmin.value) {
    fetchAllCouriersWithShifts()
  }
  fetchPaymentTypes()
  startTimers()
  connectWs()
})

onUnmounted(() => {
  if (refreshTimer.value) clearInterval(refreshTimer.value)
  if (countdownTimer.value) clearInterval(countdownTimer.value)
  if (ws.value) {
    ws.value.close()
  }
})
</script>

<template>
  <VContainer fluid class="pa-0 courier-app-wrapper">
    <!-- Header -->
    <header class="app-header mb-4">
      <div class="d-flex align-center justify-space-between flex-wrap ga-2 px-2">
        <div>
          <h1 class="text-h5 font-weight-black main-title">
            {{ activeTab === 'archive' ? 'Архив доставок' : (activeTab === 'couriers' ? 'Курьеры и смены iiko' : 'Активные доставки') }}
          </h1>
          <p v-if="lastUpdated" class="text-caption text-grey-darken-1 mb-0">
            Обновлено: {{ lastUpdated }}
          </p>
        </div>

        <!-- Статус личной смены курьера и кнопки управления -->
        <div class="d-flex align-center flex-wrap ga-2">
          <!-- Индикатор смены для курьера -->
          <template v-if="myShiftStatus.is_courier">
            <VChip
              v-if="myShiftStatus.is_shift_open"
              color="success"
              variant="tonal"
              class="font-weight-bold"
            >
              <span class="pulse-dot me-1"></span>
              Смена в iiko открыта
            </VChip>
            <template v-else>
              <VChip
                color="warning"
                variant="tonal"
                class="font-weight-bold"
              >
                <VIcon icon="bx-time-five" class="me-1" />
                Смена не открыта
              </VChip>
              <VBtn
                color="success"
                variant="flat"
                class="rounded-pill px-4 font-weight-bold"
                :loading="shiftOpening"
                @click="openMyShift"
              >
                <VIcon icon="bx-play-circle" class="me-1" />
                Открыть смену
              </VBtn>
            </template>
          </template>

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
        <VTab v-if="isSuperAdmin || isAdmin" value="couriers" class="text-none">Курьеры ({{ activeVisibleCouriersCount }})</VTab>
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
              v-for="order in sortedOrders"
              :key="order.id"
              cols="12"
              sm="6"
              md="4"
              lg="3"
              class="pa-3"
            >
              <VCard
                class="delivery-card-premium d-flex flex-column"
                :class="{ 'delivery-card-dimmed': isOrderDimmed(order) }"
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

                <!-- 2. Компактная шапка -->
                <div class="card-header-compact d-flex flex-column ga-1">
                  <div class="d-flex justify-space-between align-center">
                    <div class="d-flex align-center ga-2">
                      <span class="text-card-title">№{{ order.external_number || order.number || '???' }}</span>
                      <VChip 
                        :color="getStatusColor(order.status)" 
                        size="x-small" 
                        variant="flat" 
                        class="text-uppercase font-weight-black text-white"
                      >
                        {{ getStatusText(order.status) }}
                      </VChip>
                    </div>
                    
                    <div v-if="order.status === 'delivering' || order.status === 'onway'" class="d-flex align-center ga-1">
                      <div class="pulse-dot"></div>
                      <span class="text-card-small text-primary">{{ getDuration(order.on_the_way_time, currentTime) }}</span>
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

                  <div class="d-flex justify-space-between align-center text-card-caption">
                    <div class="d-flex align-center ga-1">
                      <VIcon :icon="order.is_asap ? 'bx-bolt-circle' : 'bx-calendar-event'" size="14" :color="order.is_asap ? 'warning' : 'primary'" />
                      <span class="font-weight-bold" :class="order.is_asap ? 'text-amber-darken-3' : 'text-primary'">
                        {{ order.is_asap ? 'КАК МОЖНО СКОРЕЕ' : 'ЗАКАЗ НА ВРЕМЯ' }}
                      </span>
                    </div>
                    <div v-if="order.expected_time" class="font-weight-bold text-slate-700">
                      <span v-if="!order.is_asap" class="me-1">{{ formatDate(order.expected_time) }}</span>
                      <span>{{ formatTime(order.expected_time) }}</span>
                    </div>
                  </div>
                </div>

                <!-- 3. Urgent Indicators (Badges) -->
                <div v-if="getActiveIndicators(order)" class="px-3 pt-1 d-flex flex-wrap ga-1">
                  <VChip v-if="getActiveIndicators(order).items" color="error" size="x-small" variant="flat" class="animate-pulse">СОСТАВ!</VChip>
                  <VChip v-if="getActiveIndicators(order).amount" color="warning" size="x-small" variant="flat" class="animate-pulse">СУММА!</VChip>
                  <VChip v-if="getActiveIndicators(order).address" color="primary" size="x-small" variant="flat" class="animate-pulse">АДРЕС!</VChip>
                  <VChip v-if="getActiveIndicators(order).time" color="info" size="x-small" variant="flat" class="animate-pulse">ВРЕМЯ!</VChip>
                  <VChip v-if="getActiveIndicators(order).payment" color="success" size="x-small" variant="flat" class="animate-pulse">ОПЛАТА!</VChip>
                </div>

                <!-- 4. Время готовности кухни (Обратный отсчет) -->
                <div class="section-compact kitchen-status-bar d-flex align-center justify-space-between py-1 px-3">
                  <template v-if="showKitchenTimer(order)">
                    <div class="d-flex align-center ga-1">
                      <VIcon icon="bx-restaurant" size="14" :color="getKitchenTimerColor(order)" />
                      <span class="text-card-small text-slate-600 font-weight-bold">Кухня:</span>
                    </div>
                    <VChip
                      :color="getKitchenTimerColor(order)"
                      size="x-small"
                      variant="flat"
                      class="font-weight-black text-white px-2 py-0.5 rounded"
                    >
                      {{ getKitchenTimerText(order) }}
                    </VChip>
                  </template>
                  <template v-else-if="isKitchenReady(order)">
                    <div class="d-flex align-center ga-1">
                      <VIcon icon="bx-restaurant" size="14" color="success" />
                      <span class="text-card-small text-slate-600 font-weight-bold">Кухня:</span>
                    </div>
                    <VChip
                      color="success"
                      size="x-small"
                      variant="flat"
                      class="font-weight-black text-white px-2 py-0.5 rounded"
                    >
                      Готов
                    </VChip>
                  </template>
                  <template v-else>
                    <div class="d-flex align-center ga-1">
                      <VIcon icon="bx-restaurant" size="14" color="warning" />
                      <span class="text-card-small text-slate-600 font-weight-bold">Кухня:</span>
                    </div>
                    <span class="text-card-caption text-warning font-weight-bold" style="font-size: 0.75rem;">Ожидаем время</span>
                  </template>
                </div>

                <!-- 5. Courier Assignment (Компактный) -->
                <div 
                  class="courier-assignment-compact px-3 py-1.5 d-flex align-center justify-space-between"
                  :class="order.courier_name && order.courier_name !== 'Не назначен' ? 'assigned' : 'unassigned'"
                >
                  <div class="d-flex align-center ga-1 overflow-hidden">
                    <VIcon 
                      :icon="order.courier_name && order.courier_name !== 'Не назначен' ? 'bx-car' : 'bx-user-x'" 
                      size="16" 
                      :color="order.courier_name && order.courier_name !== 'Не назначен' ? 'info' : 'warning'" 
                    />
                    <span class="text-card-caption font-weight-bold text-truncate text-slate-800" style="font-size: 0.75rem;">
                      {{ order.courier_name && order.courier_name !== 'Не назначен' ? order.courier_name : 'Свободный заказ' }}
                    </span>
                  </div>
                  <VChip 
                    :color="order.courier_name && order.courier_name !== 'Не назначен' ? 'info' : 'warning'" 
                    size="x-small" 
                    variant="tonal" 
                    class="font-weight-black"
                  >
                    {{ order.courier_name && order.courier_name !== 'Не назначен' ? 'Назначен' : 'Свободен' }}
                  </VChip>
                </div>

                <!-- 6. Client Info & Phone -->
                <div class="section-compact d-flex align-center justify-space-between py-1.5">
                  <div class="d-flex align-center overflow-hidden ga-2">
                    <div class="d-flex flex-column overflow-hidden">
                      <span class="text-card-body font-weight-bold text-truncate leading-tight" style="font-size: 0.875rem !important;">
                        {{ order.customer_name || order.customer?.name || 'Гость' }}
                      </span>
                      <div class="d-flex align-center ga-1 mt-0.5">
                        <VIcon 
                          :icon="order.customer_info_details?.is_high_risk ? 'bx-shield-x' : 'bx-check-shield'" 
                          size="12" 
                          :color="order.customer_info_details?.is_high_risk ? 'error' : 'success'" 
                        />
                        <span class="text-card-small leading-none" :class="order.customer_info_details?.is_high_risk ? 'text-error' : 'text-success'" style="font-size: 0.65rem !important;">
                          {{ order.customer_info_details?.is_high_risk ? 'Риск' : 'Надежный' }}
                        </span>
                        <span class="text-card-small text-slate-400 ms-1" style="font-size: 0.65rem !important;">• {{ order.organization_name || 'Основная' }}</span>
                      </div>
                    </div>
                  </div>
                  <VBtn
                    icon="bx-phone"
                    size="32"
                    color="success"
                    variant="tonal"
                    class="rounded-lg"
                    @click.stop="callCustomer(order.customer_phone || order.customer?.phone)"
                  />
                </div>

                <!-- 7. Address & Navigator -->
                <div class="section-compact py-1.5 d-flex flex-column ga-1">
                  <div class="d-flex align-start ga-2" @click="openMaps(order)">
                    <VIcon icon="bx-map" color="primary" class="mt-0.5 flex-shrink-0" size="16" />
                    <div class="text-card-body font-weight-bold line-height-xs flex-grow-1 text-slate-800" style="font-size: 0.8125rem !important;">
                      {{ formatAddress(order) }}
                    </div>
                  </div>
                  
                  <div class="d-flex ga-2 mt-1.5">
                    <VMenu offset-y transition="scale-transition" location="bottom">
                      <template #activator="{ props: menuProps }">
                        <VBtn
                          v-bind="menuProps"
                          prepend-icon="bx-navigation"
                          color="primary"
                          variant="tonal"
                          size="small"
                          class="rounded-lg font-weight-bold flex-grow-1"
                          height="38"
                        >
                          Навигатор
                        </VBtn>
                      </template>
                      <VList density="compact" class="rounded-xl py-1 border shadow-lg">
                        <VListItem @click="openMaps(order, 'yandex')" class="py-2">
                          <template #prepend><VIcon icon="bx-map" color="orange" size="18" class="me-2" /></template>
                          <VListItemTitle class="font-weight-bold text-caption">Яндекс.Карты</VListItemTitle>
                        </VListItem>
                        <VListItem @click="openMaps(order, 'yandexnavi')" class="py-2">
                          <template #prepend><VIcon icon="bx-compass" color="red" size="18" class="me-2" /></template>
                          <VListItemTitle class="font-weight-bold text-caption">Яндекс.Навигатор</VListItemTitle>
                        </VListItem>
                        <VListItem @click="openMaps(order, '2gis')" class="py-2">
                          <template #prepend><VIcon icon="bx-navigation" color="blue" size="18" class="me-2" /></template>
                          <VListItemTitle class="font-weight-bold text-caption">2ГИС</VListItemTitle>
                        </VListItem>
                        <VListItem @click="openMaps(order, 'google')" class="py-2">
                          <template #prepend><VIcon icon="bx-globe" color="green" size="18" class="me-2" /></template>
                          <VListItemTitle class="font-weight-bold text-caption">Google Maps</VListItemTitle>
                        </VListItem>
                        <VListItem @click="openMaps(order, 'petal')" class="py-2">
                          <template #prepend><VIcon icon="bx-mobile-vibration" color="purple" size="18" class="me-2" /></template>
                          <VListItemTitle class="font-weight-bold text-caption">Petal Maps</VListItemTitle>
                        </VListItem>
                      </VList>
                    </VMenu>

                    <VBtn
                      prepend-icon="bx-copy"
                      variant="tonal"
                      size="small"
                      color="secondary"
                      class="rounded-lg font-weight-medium"
                      height="38"
                      @click.stop="copyToClipboard(formatAddress(order))"
                    >
                      Копировать
                    </VBtn>
                  </div>
                </div>

                <!-- 8. Comments (Optional) -->
                <div v-if="order.comment || order.courier_comment || order.address_comment || order.additional_info || order.other_info" class="courier-comments-box-compact">
                  <div v-if="order.comment" class="d-flex ga-1.5 mb-0.5">
                    <VIcon icon="bx-comment" size="12" color="amber-darken-3" class="mt-0.5" />
                    <div class="text-card-caption leading-tight" style="font-size: 0.75rem !important;"><strong>Заказ:</strong> {{ order.comment }}</div>
                  </div>
                  <div v-if="order.courier_comment" class="d-flex ga-1.5 mb-0.5">
                    <VIcon icon="bx-info-circle" size="12" color="primary" class="mt-0.5" />
                    <div class="text-card-caption leading-tight" style="font-size: 0.75rem !important;"><strong>Курьеру:</strong> {{ order.courier_comment }}</div>
                  </div>
                  <div v-if="order.address_comment" class="d-flex ga-1.5 mb-0.5">
                    <VIcon icon="bx-map-pin" size="12" color="success" class="mt-0.5" />
                    <div class="text-card-caption leading-tight" style="font-size: 0.75rem !important;"><strong>Прим. к адресу:</strong> {{ order.address_comment }}</div>
                  </div>
                  <div v-if="order.additional_info" class="d-flex ga-1.5 mb-0.5">
                    <VIcon icon="bx-plus-circle" size="12" color="info" class="mt-0.5" />
                    <div class="text-card-caption leading-tight" style="font-size: 0.75rem !important;"><strong>Доп. инфо:</strong> {{ order.additional_info }}</div>
                  </div>
                  <div v-if="order.other_info" class="d-flex ga-1.5">
                    <VIcon icon="bx-help-circle" size="12" color="secondary" class="mt-0.5" />
                    <div class="text-card-caption leading-tight" style="font-size: 0.75rem !important;"><strong>Прочее:</strong> {{ order.other_info }}</div>
                  </div>
                </div>

                <!-- 9. Composition -->
                <div class="composition-panel-compact">
                  <VExpansionPanels variant="accordion">
                    <VExpansionPanel elevation="0" class="border-b rounded-0">
                      <VExpansionPanelTitle class="px-3 py-1.5" min-height="32">
                        <template #default="{ expanded }">
                          <div class="d-flex align-center ga-1.5 w-100">
                            <VIcon icon="bx-package" size="14" color="slate-400" />
                            <span class="text-card-small text-slate-500 font-weight-bold" style="font-size: 0.7rem !important;">Состав ({{ order.items?.length || 0 }})</span>
                            <VSpacer />
                            <span v-if="!expanded" class="text-card-caption font-weight-bold text-truncate" style="max-width: 100px; font-size: 0.75rem !important;">
                              {{ order.items?.[0]?.name }}{{ order.items?.length > 1 ? '...' : '' }}
                            </span>
                          </div>
                        </template>
                      </VExpansionPanelTitle>
                      <VExpansionPanelText>
                        <div
                          v-for="item in order.items"
                          :key="item.id"
                          class="d-flex justify-space-between py-0.5 border-bottom-dashed text-card-caption"
                          style="font-size: 0.75rem !important;"
                        >
                          <span class="text-truncate me-2">{{ item.name }}</span>
                          <span class="font-weight-black flex-shrink-0 text-slate-900">{{ item.amount }} шт.</span>
                        </div>
                      </VExpansionPanelText>
                    </VExpansionPanel>
                  </VExpansionPanels>
                </div>

                <!-- 10. Payment & Primary Actions -->
                <div class="card-footer-compact d-flex flex-column ga-2">
                  <div class="d-flex justify-space-between align-center">
                    <div class="d-flex flex-column">
                      <span class="text-card-small text-slate-400 leading-none mb-0.5" style="font-size: 0.65rem !important;">Сумма</span>
                      <span class="text-body-1 font-weight-black text-slate-900 leading-none">
                        {{ (order.left_to_pay || order.total_with_discount || order.sum || 0).toLocaleString() }} ₽
                      </span>
                    </div>
                    <div class="text-right">
                      <div class="d-flex align-center justify-end ga-1 mb-0.5">
                        <VIcon :icon="getPaymentTypeIcon(order.payment_method)" size="12" color="slate-400" />
                        <span class="text-card-caption font-weight-bold text-slate-600" style="font-size: 0.75rem !important;">{{ order.payment_method || '—' }}</span>
                      </div>
                      <VChip 
                        :color="getPaymentStatusColor(order)" 
                        size="x-small" 
                        variant="flat" 
                        class="font-weight-black text-white"
                        style="height: 16px; font-size: 0.65rem !important;"
                      >
                        {{ getPaymentStatusText(order) }}
                      </VChip>
                    </div>
                  </div>

                  <!-- Кнопка "Принял заказ" (пункт 5 ТЗ) -->
                  <div v-if="order.courier_name && order.courier_name !== 'Не назначен'" class="mt-1">
                    <VBtn
                      v-if="order.courier_notification_status === 'accepted'"
                      disabled
                      block
                      color="success"
                      variant="tonal"
                      size="default"
                      height="34"
                      prepend-icon="bx-check-double"
                      class="rounded-lg font-weight-black text-uppercase text-caption opacity-80"
                    >
                      Заказ принят
                    </VBtn>
                    <VBtn
                      v-else
                      block
                      color="success"
                      variant="flat"
                      size="default"
                      height="34"
                      prepend-icon="bx-check-circle"
                      class="rounded-lg font-weight-black text-uppercase text-caption elevation-1"
                      :loading="orderAccepting[order.id]"
                      @click.stop="acceptCourierDelivery(order.id)"
                    >
                      Принял заказ
                    </VBtn>
                  </div>

                  <!-- Кнопки действий -->
                  <div class="d-flex ga-1.5 mt-1">
                    <VBtn
                      v-if="canAcceptOrder(order)"
                      prepend-icon="bx-user-plus"
                      color="primary"
                      variant="flat"
                      size="default"
                      height="36"
                      class="rounded-lg font-weight-black text-uppercase flex-grow-1 text-caption"
                      @click.stop="acceptOrder(order.id)"
                    >
                      Взять
                    </VBtn>

                    <VBtn
                      v-else-if="order.status.toLowerCase() === 'ready'"
                      prepend-icon="bx-run"
                      :color="isButtonLocked(order.id) ? 'secondary' : 'primary'"
                      :disabled="isButtonLocked(order.id)"
                      variant="flat"
                      size="default"
                      height="36"
                      class="rounded-lg font-weight-black text-uppercase flex-grow-1 text-caption"
                      @click.stop="updateStatus(order.id, 'OnWay')"
                    >
                      Начать
                    </VBtn>

                    <template v-else-if="order.status.toLowerCase() === 'onway' || order.status.toLowerCase() === 'delivering'">
                      <VBtn
                        v-if="canShowDelivered(order)"
                        prepend-icon="bx-check-double"
                        color="warning"
                        variant="flat"
                        size="default"
                        height="36"
                        class="rounded-lg font-weight-black text-uppercase flex-grow-1 text-caption"
                        @click.stop="handleDeliveredClick(order)"
                      >
                        Доставлен
                      </VBtn>
                      <VBtn
                        v-if="!isOrderFullyPaid(order)"
                        prepend-icon="bx-credit-card"
                        color="info"
                        variant="tonal"
                        size="default"
                        height="36"
                        class="rounded-lg font-weight-bold flex-grow-1 text-caption"
                        @click.stop="openChangePaymentDialog(order)"
                      >
                        Оплата
                      </VBtn>
                    </template>

                    <VBtn
                      v-else-if="order.status.toLowerCase() === 'onway' || order.status.toLowerCase() === 'delivering'"
                      prepend-icon="bx-info-circle"
                      variant="flat"
                      color="secondary"
                      size="default"
                      height="36"
                      class="rounded-lg font-weight-bold flex-grow-1 text-caption"
                      @click.stop="openDetails(order)"
                    >
                      Подробнее
                    </VBtn>
                    <VBtn
                      v-else-if="order.status.toLowerCase() === 'delivered' && !isOrderFullyPaid(order)"
                      prepend-icon="bx-wallet"
                      color="slate-900"
                      variant="flat"
                      size="default"
                      height="36"
                      class="rounded-lg font-weight-black text-uppercase text-white flex-grow-1 text-caption"
                      @click.stop="openCloseDialog(order)"
                    >
                      Оплатить
                    </VBtn>
                    <VBtn
                      v-else
                      prepend-icon="bx-info-circle"
                      variant="tonal"
                      color="secondary"
                      size="default"
                      height="36"
                      class="rounded-lg font-weight-bold flex-grow-1 text-caption"
                      @click.stop="openDetails(order)"
                    >
                      Подробнее
                    </VBtn>

                    <VBtn
                      v-if="canAcceptOrder(order) || order.status.toLowerCase() === 'ready' || (order.status.toLowerCase() === 'delivered' && !isOrderFullyPaid(order))"
                      icon="bx-info-circle"
                      variant="tonal"
                      color="secondary"
                      size="default"
                      height="36"
                      width="36"
                      class="rounded-lg flex-shrink-0"
                      @click.stop="openDetails(order)"
                    />
                  </div>

                  <!-- Кнопка оплаты по СБП -->
                  <div v-if="order.status.toLowerCase() !== 'closed' && order.status.toLowerCase() !== 'cancelled'" class="mt-1.5">
                    <VBtn
                      v-if="isOrderFullyPaid(order)"
                      color="success"
                      variant="flat"
                      size="default"
                      height="36"
                      block
                      readonly
                      class="rounded-lg font-weight-black text-uppercase text-caption text-white"
                      style="opacity: 0.9; pointer-events: none;"
                    >
                      <VIcon icon="bx-check" class="me-1" />
                      Оплачено
                    </VBtn>
                    <VBtn
                      v-else-if="(order.left_to_pay || order.sum) > 0"
                      prepend-icon="bx-qr-scan"
                      color="primary"
                      variant="tonal"
                      size="default"
                      height="36"
                      block
                      class="rounded-lg font-weight-black text-uppercase text-caption"
                      @click.stop="openSbpPayment(order)"
                    >
                      Оплата по СБП
                    </VBtn>
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
        <div class="archive-filters pa-4 border-b sticky-top">
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


      <!-- Вкладка: Курьеры (Все курьеры со сменами, скрытием и отчетами) -->
      <VWindowItem value="couriers">
        <div class="px-2 px-md-4 py-4">
          <!-- Фильтры и поиск -->
          <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-4">
            <!-- Табы фильтрации курьеров: Все / Со сменой / Без смены / Скрытые -->
            <div
              class="d-inline-flex flex-wrap align-center border rounded-lg pa-1 ga-1"
              style="background: rgba(var(--v-theme-on-surface), 0.04);"
            >
              <VBtn
                size="small"
                :variant="courierFilterTab === 'all' ? 'flat' : 'text'"
                :color="courierFilterTab === 'all' ? 'primary' : 'default'"
                class="text-none font-weight-bold px-3 rounded-md"
                height="32"
                @click="courierFilterTab = 'all'"
              >
                Все
              </VBtn>

              <VBtn
                size="small"
                :variant="courierFilterTab === 'open' ? 'flat' : 'text'"
                :color="courierFilterTab === 'open' ? 'success' : 'default'"
                class="text-none font-weight-bold px-3 rounded-md"
                height="32"
                @click="courierFilterTab = 'open'"
              >
                <span>Со сменой</span>
                <VChip
                  size="x-small"
                  :color="courierFilterTab === 'open' ? 'white' : 'success'"
                  :variant="courierFilterTab === 'open' ? 'elevated' : 'flat'"
                  class="ms-2 font-weight-black px-1.5"
                  style="height: 18px; min-width: 18px;"
                  :style="courierFilterTab === 'open' ? 'color: var(--v-theme-success) !important; background: white !important;' : ''"
                >
                  {{ openShiftCouriersCount }}
                </VChip>
              </VBtn>

              <VBtn
                size="small"
                :variant="courierFilterTab === 'closed' ? 'flat' : 'text'"
                :color="courierFilterTab === 'closed' ? 'secondary' : 'default'"
                class="text-none font-weight-bold px-3 rounded-md"
                height="32"
                @click="courierFilterTab = 'closed'"
              >
                <span>Без смены</span>
                <VChip
                  size="x-small"
                  :color="courierFilterTab === 'closed' ? 'white' : 'secondary'"
                  :variant="courierFilterTab === 'closed' ? 'elevated' : 'flat'"
                  class="ms-2 font-weight-black px-1.5"
                  style="height: 18px; min-width: 18px;"
                  :style="courierFilterTab === 'closed' ? 'color: var(--v-theme-secondary) !important; background: white !important;' : ''"
                >
                  {{ closedShiftCouriersCount }}
                </VChip>
              </VBtn>

              <VBtn
                size="small"
                :variant="courierFilterTab === 'hidden' ? 'flat' : 'text'"
                :color="courierFilterTab === 'hidden' ? 'warning' : 'default'"
                class="text-none font-weight-bold px-3 rounded-md"
                height="32"
                @click="courierFilterTab = 'hidden'"
              >
                <VIcon icon="bx-hide" size="16" class="me-1" />
                <span>Скрытые</span>
                <VChip
                  v-if="hiddenCouriersCount > 0"
                  size="x-small"
                  color="warning"
                  class="ms-2 font-weight-black px-1.5"
                  style="height: 18px; min-width: 18px;"
                >
                  {{ hiddenCouriersCount }}
                </VChip>
              </VBtn>
            </div>

            <VTextField
              v-model="courierSearch"
              prepend-inner-icon="bx-search"
              placeholder="Поиск курьера..."
              density="compact"
              variant="outlined"
              hide-details
              clearable
              style="max-width: 280px;"
              class="rounded-lg"
            />
          </div>

          <!-- Список курьеров -->
          <VRow v-if="filteredCouriers.length" class="ma-0">
            <VCol
              v-for="courier in filteredCouriers"
              :key="courier.iiko_id || courier.id"
              cols="12"
              sm="6"
              md="4"
              class="pa-2"
            >
              <VCard class="courier-status-card pa-4 rounded-xl border elevation-0 h-100 d-flex flex-column justify-space-between" :class="{'opacity-80 bg-grey-lighten-5': courier.is_hidden}">
                <div>
                  <div class="d-flex align-center justify-space-between mb-2">
                    <div class="d-flex align-center ga-3">
                      <VAvatar size="44" :color="courier.is_hidden ? 'grey' : (courier.is_shift_open ? 'success' : 'secondary')" variant="tonal">
                        <VIcon icon="bx-cycling" size="24" :color="courier.is_hidden ? 'grey' : (courier.is_shift_open ? 'success' : 'secondary')" />
                      </VAvatar>
                      <div>
                        <div class="d-flex align-center ga-1">
                          <h4 class="text-subtitle-1 font-weight-black mb-0 text-truncate" style="max-width: 150px;">
                            {{ courier.name }}
                          </h4>
                          <VChip v-if="courier.is_hidden" color="warning" size="x-small" variant="tonal">
                            Скрыт
                          </VChip>
                        </div>
                        <div class="d-flex align-center ga-1 text-caption text-medium-emphasis">
                          <VIcon icon="bx-phone" size="12" />
                          <span>{{ courier.phone || 'Телефон не указан' }}</span>
                        </div>
                      </div>
                    </div>

                    <div class="d-flex align-center ga-1">
                      <!-- Статус смены -->
                      <VChip
                        :color="courier.is_shift_open ? 'success' : 'secondary'"
                        size="x-small"
                        variant="flat"
                        class="font-weight-black text-white"
                      >
                        <span v-if="courier.is_shift_open" class="pulse-dot me-1"></span>
                        {{ courier.is_shift_open ? 'Смена открыта' : 'Смена закрыта' }}
                      </VChip>

                      <!-- Кнопка скрытия / восстановления -->
                      <VBtn
                        v-if="courier.is_hidden"
                        icon
                        variant="text"
                        color="primary"
                        size="x-small"
                        :loading="courierHideLoading[courier.iiko_id]"
                        @click="adminUnhideCourier(courier)"
                      >
                        <VIcon icon="bx-show" size="18" />
                        <VTooltip activator="parent">Вернуть в общий список</VTooltip>
                      </VBtn>
                      <VBtn
                        v-else
                        icon
                        variant="text"
                        color="grey-darken-1"
                        size="x-small"
                        :loading="courierHideLoading[courier.iiko_id]"
                        @click="adminHideCourier(courier)"
                      >
                        <VIcon icon="bx-hide" size="18" />
                        <VTooltip activator="parent">Скрыть курьера из списка</VTooltip>
                      </VBtn>
                    </div>
                  </div>

                  <div v-if="courier.code" class="text-caption text-disabled mb-2">
                    Табельный номер: <span class="font-weight-bold text-high-emphasis">{{ courier.code }}</span>
                  </div>
                </div>

                <!-- Кнопки управления и отчет по доставкам -->
                <div class="d-flex flex-column ga-2 mt-3 pt-3 border-t">
                  <div class="d-flex ga-2">
                    <!-- Кнопка отчета по курьеру -->
                    <VBtn
                      color="info"
                      variant="tonal"
                      size="small"
                      prepend-icon="bx-bar-chart-alt-2"
                      class="rounded-lg font-weight-bold flex-grow-1"
                      @click="openCourierReport(courier)"
                    >
                      Отчет по доставкам
                    </VBtn>
                  </div>

                  <div class="d-flex ga-2">
                    <!-- Кнопка смены -->
                    <VBtn
                      v-if="!courier.is_shift_open"
                      color="success"
                      variant="flat"
                      size="small"
                      prepend-icon="bx-play-circle"
                      class="rounded-lg font-weight-black text-uppercase flex-grow-1"
                      :loading="adminShiftLoading[courier.iiko_id]"
                      @click="adminOpenCourierShift(courier)"
                    >
                      Открыть смену
                    </VBtn>
                    <VBtn
                      v-else
                      color="error"
                      variant="tonal"
                      size="small"
                      prepend-icon="bx-stop-circle"
                      class="rounded-lg font-weight-black text-uppercase flex-grow-1"
                      :loading="adminShiftLoading[courier.iiko_id]"
                      @click="adminCloseCourierShift(courier)"
                    >
                      Закрыть смену
                    </VBtn>
                  </div>
                </div>
              </VCard>
            </VCol>
          </VRow>

          <div v-else class="text-center py-12">
            <VIcon size="64" color="grey-lighten-2" :icon="courierFilterTab === 'hidden' ? 'bx-hide' : 'bx-user-x'" />
            <p class="mt-4 text-grey font-weight-medium">
              {{ courierFilterTab === 'hidden' ? 'Скрытых курьеров нет' : 'Курьеры не найдены' }}
            </p>
          </div>
        </div>
      </VWindowItem>
    </VWindow>

    <!-- Диалог деталей заказа (Стандартизированный) -->
    <OrderDetailModal
      v-if="detailsOrder"
      v-model="showDetailsDialog"
      :order="detailsOrder"
      :is-read-only="false"
      @update:order="fetchData(true)"
    />

    <!-- Диалог закрытия заказа -->
    <VDialog v-model="showCloseDialog" max-width="450px" scrollable persistent>
      <VCard class="rounded-xl d-flex flex-column" style="max-height: 90vh;">
        <div class="bg-primary pa-4 pa-sm-6 text-white d-flex align-center flex-shrink-0">
          <VIcon icon="bx-wallet" size="32" class="me-3" />
          <div>
            <h3 class="text-h5 font-weight-bold">Оплата заказа</h3>
            <p class="text-caption mb-0 opacity-80">Финальный шаг доставки</p>
          </div>
          <VSpacer />
          <VBtn icon="bx-x" variant="text" color="white" @click="showCloseDialog = false" />
        </div>

        <VCardText class="pa-4 pa-sm-6 overflow-y-auto">
          <div class="d-flex justify-space-between align-center mb-6 pa-4 rounded-lg" style="background: rgba(var(--v-theme-primary), 0.08); border: 1px dashed rgba(var(--v-theme-primary), 0.25);">
            <span class="text-body-1 font-weight-bold text-primary">К ОПЛАТЕ:</span>
            <span class="text-h4 font-weight-black text-primary">{{ selectedOrder?.sum }} ₽</span>
          </div>
          
          <p class="text-subtitle-2 font-weight-bold mb-3 text-medium-emphasis text-uppercase">Выберите способ оплаты:</p>
          
          <VBtn
            block
            color="primary"
            variant="tonal"
            prepend-icon="bx-qr-scan"
            height="48"
            class="rounded-lg mb-4 font-weight-black text-uppercase"
            @click="openSbpPayment(selectedOrder)"
          >
            Сгенерировать СБП QR
          </VBtn>
          
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

        <VCardActions class="pa-4 pa-sm-6 pt-0 flex-shrink-0">
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

    <!-- Диалог оплаты по СБП -->
    <VDialog v-model="sbpDialog" max-width="400px" scrollable persistent>
      <VCard class="rounded-xl sbp-payment-card d-flex flex-column" style="max-height: 92vh;">
        <div class="sbp-header pa-4 pa-sm-6 text-white d-flex align-center flex-shrink-0">
          <div class="sbp-logo-wrap rounded-lg bg-white pa-1 me-3 d-flex align-center justify-center" style="width: 44px; height: 44px;">
            <VIcon icon="bx-qr-scan" color="primary" size="28" />
          </div>
          <div>
            <h3 class="text-h6 font-weight-black mb-0 leading-none">Оплата СБП</h3>
            <p class="text-caption mb-0 opacity-80 mt-1">Заказ №{{ sbpOrder?.number || sbpOrder?.id }}</p>
          </div>
          <VSpacer />
          <VBtn icon="bx-x" variant="text" color="white" @click="closeSbpDialog" />
        </div>

        <VCardText class="pa-4 pa-sm-6 text-center overflow-y-auto">
          <!-- Загрузка QR -->
          <div v-if="sbpLoading && !sbpQrData" class="py-12">
            <VProgressCircular indeterminate color="primary" size="48" />
            <p class="mt-4 text-body-2 font-weight-bold text-slate-600">Генерируем QR-код...</p>
          </div>

          <!-- Контент с QR -->
          <div v-else-if="sbpQrData">
            <!-- Сумма -->
            <div class="text-subtitle-2 text-slate-500 text-uppercase font-weight-bold mb-1">Сумма к оплате</div>
            <div class="text-h3 font-weight-black text-slate-900 mb-6">
              {{ (sbpOrder?.left_to_pay || sbpOrder?.total_with_discount || sbpOrder?.sum || 0).toLocaleString() }} ₽
            </div>

            <!-- Зона QR-кода -->
            <div class="qr-container-wrapper mb-6 mx-auto d-flex align-center justify-center position-relative">
              <div class="qr-border-corner top-left"></div>
              <div class="qr-border-corner top-right"></div>
              <div class="qr-border-corner bottom-left"></div>
              <div class="qr-border-corner bottom-right"></div>
              
              <!-- Анимация успешной оплаты -->
              <div v-if="sbpOrderStatus === 'PAID'" class="success-overlay d-flex flex-column align-center justify-center">
                <div class="success-checkmark-circle">
                  <VIcon icon="bx-check" size="48" color="success" class="success-icon animate-bounce" />
                </div>
                <div class="text-subtitle-1 font-weight-black text-success mt-4">Оплачено!</div>
              </div>

              <!-- Сам QR-код -->
              <div v-else class="qr-image-holder pa-2 bg-white rounded-xl">
                <img :src="'data:image/svg+xml;base64,' + sbpQrData.svg" class="sbp-qr-img" style="width: 220px; height: 220px; display: block;" />
                <!-- Сканирующий лазерный луч -->
                <div class="qr-scanner-line"></div>
              </div>
            </div>

            <div v-if="sbpOrderStatus !== 'PAID'">
              <!-- Кнопки отправки QR в соцсети -->
              <div class="mb-4">
                <div class="text-caption text-slate-500 mb-2 font-weight-bold">
                  Отправить ссылку и QR клиенту:
                </div>
                <div class="d-flex justify-space-between gap-2">
                  <VBtn
                    color="primary"
                    variant="tonal"
                    class="rounded-lg flex-grow-1"
                    style="min-width: 0;"
                    :loading="sharingQr === 'vk'"
                    :disabled="!!sharingQr"
                    prepend-icon="bxl-vk"
                    size="small"
                    @click="shareQrCodeViaSocial('vk')"
                  >
                    VK
                  </VBtn>
                  <VBtn
                    color="info"
                    variant="tonal"
                    class="rounded-lg flex-grow-1 mx-1"
                    style="min-width: 0;"
                    :loading="sharingQr === 'tg'"
                    :disabled="!!sharingQr"
                    prepend-icon="bxl-telegram"
                    size="small"
                    @click="shareQrCodeViaSocial('tg')"
                  >
                    Telegram
                  </VBtn>
                  <VBtn
                    color="success"
                    variant="tonal"
                    class="rounded-lg flex-grow-1"
                    style="min-width: 0;"
                    :loading="sharingQr === 'max'"
                    :disabled="!!sharingQr"
                    prepend-icon="bx-chat"
                    size="small"
                    @click="shareQrCodeViaSocial('max')"
                  >
                    MAX
                  </VBtn>
                </div>
              </div>

              <div class="d-flex align-center justify-center text-caption text-slate-500 mb-4 animate-pulse">
                <span class="pulse-dot me-2 bg-primary"></span>
                Ожидаем оплату клиентом...
              </div>

              <VBtn
                variant="tonal"
                color="secondary"
                block
                :loading="sbpLoading"
                class="rounded-lg text-caption font-weight-bold"
                height="36"
                @click="checkSbpPaymentStatusManually"
              >
                Проверить статус
              </VBtn>
            </div>
          </div>
        </VCardText>
      </VCard>
    </VDialog>
    <!-- Диалог смены способа оплаты / подтверждения оплаты при доставке -->
    <VDialog v-model="showChangePaymentDialog" max-width="450px" scrollable persistent>
      <VCard class="rounded-xl d-flex flex-column" style="max-height: 90vh;">
        <div :class="[isDeliveryConfirmation ? 'bg-warning' : 'bg-info', 'pa-4 pa-sm-6 text-white d-flex align-center flex-shrink-0']">
          <VIcon :icon="isDeliveryConfirmation ? 'bx-check-shield' : 'bx-credit-card'" size="32" class="me-3" />
          <div>
            <h3 class="text-h5 font-weight-bold">
              {{ isDeliveryConfirmation ? 'Подтверждение доставки' : 'Способ оплаты' }}
            </h3>
            <p class="text-caption mb-0 opacity-80">Заказ №{{ changePaymentOrder?.number || changePaymentOrder?.id }}</p>
          </div>
          <VSpacer />
          <VBtn icon="bx-x" variant="text" color="white" @click="showChangePaymentDialog = false" />
        </div>

        <VCardText class="pa-4 pa-sm-6 overflow-y-auto">
          <VAlert
            v-if="isDeliveryConfirmation"
            type="warning"
            variant="tonal"
            density="comfortable"
            class="mb-4 rounded-lg text-body-2"
          >
            У заказа <strong>не указан способ оплаты</strong>. Пожалуйста, выберите фактический способ расчета с клиентом для завершения доставки.
          </VAlert>

          <div class="d-flex justify-space-between align-center mb-6 pa-4 rounded-lg" style="background: rgba(var(--v-theme-info), 0.08); border: 1px dashed rgba(var(--v-theme-info), 0.25);">
            <div>
              <div class="text-caption text-medium-emphasis">Остаток к оплате:</div>
              <div class="text-h4 font-weight-black text-info">{{ changePaymentOrder?.left_to_pay }} ₽</div>
            </div>
            <div class="text-end" v-if="Number(changePaymentOrder?.bonus_spent) > 0">
              <div class="text-caption text-medium-emphasis">Оплачено бонусами:</div>
              <div class="text-subtitle-1 font-weight-bold text-success">{{ changePaymentOrder?.bonus_spent }} ₽</div>
            </div>
          </div>

          <VBtnToggle
            v-model="changePaymentMode"
            mandatory
            color="info"
            variant="outlined"
            class="d-flex mb-6 rounded-lg w-100"
          >
            <VBtn value="single" class="flex-grow-1 font-weight-bold">Один способ</VBtn>
            <VBtn value="split" class="flex-grow-1 font-weight-bold">Частями (сплит)</VBtn>
          </VBtnToggle>

          <!-- Одиночный выбор -->
          <div v-if="changePaymentMode === 'single'">
            <p class="text-subtitle-2 font-weight-bold mb-3 text-medium-emphasis text-uppercase">
              {{ isDeliveryConfirmation ? 'Выберите способ оплаты:' : 'Способ оплаты:' }}
            </p>
            
            <VList class="pa-0 bg-transparent">
              <!-- Наличные -->
              <VListItem
                :disabled="!getCashPaymentType()"
                :active="singlePaymentType === getCashPaymentType()?.iiko_id"
                color="info"
                variant="tonal"
                class="rounded-lg mb-2 py-3 border cursor-pointer"
                @click="singlePaymentType = getCashPaymentType()?.iiko_id"
              >
                <template #prepend>
                  <VIcon icon="bx-money" class="me-3" />
                </template>
                <VListItemTitle class="font-weight-bold d-flex align-center justify-space-between">
                  <span>Наличные</span>
                  <VChip
                    v-if="currentPaymentKind === 'Cash'"
                    size="x-small"
                    color="primary"
                    variant="tonal"
                    class="font-weight-bold"
                  >
                    Текущий в iiko
                  </VChip>
                </VListItemTitle>
                <template #append>
                  <VIcon v-if="singlePaymentType === getCashPaymentType()?.iiko_id" icon="bx-check-circle" color="info" />
                </template>
              </VListItem>

              <!-- Картой курьеру -->
              <VListItem
                :disabled="!getCardPaymentType()"
                :active="singlePaymentType === getCardPaymentType()?.iiko_id"
                color="info"
                variant="tonal"
                class="rounded-lg mb-2 py-3 border cursor-pointer"
                @click="singlePaymentType = getCardPaymentType()?.iiko_id"
              >
                <template #prepend>
                  <VIcon icon="bx-credit-card" class="me-3" />
                </template>
                <VListItemTitle class="font-weight-bold d-flex align-center justify-space-between">
                  <span>Картой курьеру</span>
                  <VChip
                    v-if="currentPaymentKind === 'Card'"
                    size="x-small"
                    color="primary"
                    variant="tonal"
                    class="font-weight-bold"
                  >
                    Текущий в iiko
                  </VChip>
                </VListItemTitle>
                <template #append>
                  <VIcon v-if="singlePaymentType === getCardPaymentType()?.iiko_id" icon="bx-check-circle" color="info" />
                </template>
              </VListItem>
            </VList>
          </div>

          <!-- Раздельный выбор (Сплит) -->
          <div v-else>
            <p class="text-subtitle-2 font-weight-bold mb-3 text-medium-emphasis text-uppercase">Укажите суммы оплат:</p>
            
            <VTextField
              v-model.number="splitCashSum"
              label="Наличными, ₽"
              type="number"
              min="0"
              :max="changePaymentOrder?.left_to_pay"
              @input="handleSplitSumChange('cash')"
              prepend-inner-icon="bx-money"
              class="mb-4"
              variant="outlined"
              color="info"
            />

            <VTextField
              v-model.number="splitCardSum"
              label="Картой курьеру, ₽"
              type="number"
              min="0"
              :max="changePaymentOrder?.left_to_pay"
              @input="handleSplitSumChange('card')"
              prepend-inner-icon="bx-credit-card"
              class="mb-4"
              variant="outlined"
              color="info"
            />

            <VAlert
              v-if="!isSplitValid"
              type="warning"
              variant="tonal"
              density="compact"
              class="text-caption rounded-lg"
            >
              Сумма оплат должна равняться остатку к оплате: <strong>{{ changePaymentOrder?.left_to_pay }} ₽</strong>
            </VAlert>
            <VAlert
              v-else
              type="success"
              variant="tonal"
              density="compact"
              class="text-caption rounded-lg"
            >
              Распределение корректно! Наличные: {{ splitCashSum }} ₽ + Картой: {{ splitCardSum }} ₽
            </VAlert>
          </div>

          <!-- Кнопка перехода к оплате по СБП (QR-код) -->
          <div v-if="(changePaymentOrder?.left_to_pay || changePaymentOrder?.sum) > 0" class="mt-4">
            <VBtn
              block
              variant="tonal"
              color="primary"
              prepend-icon="bx-qr-scan"
              class="rounded-lg font-weight-bold text-caption"
              @click="openSbpFromChangePayment"
            >
              Оплата по СБП (QR-код)
            </VBtn>
          </div>
        </VCardText>

        <VCardActions class="pa-4 pa-sm-6 pt-0 flex-shrink-0">
          <VBtn
            block
            :color="isDeliveryConfirmation ? 'warning' : 'info'"
            variant="flat"
            size="large"
            :disabled="loading || (changePaymentMode === 'single' && !singlePaymentType) || (changePaymentMode === 'split' && !isSplitValid)"
            :loading="loading"
            @click="submitPaymentChange"
            class="rounded-lg font-weight-bold text-uppercase"
          >
            <VIcon :icon="isDeliveryConfirmation ? 'bx-check-double' : 'bx-save'" class="me-2" />
            {{ isDeliveryConfirmation ? 'Подтвердить и доставить' : 'Сохранить изменения' }}
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог детального отчета по доставкам курьера -->
    <VDialog v-model="showCourierReportDialog" max-width="960px" scrollable>
      <VCard class="rounded-xl overflow-hidden">
        <!-- Заголовок диалога -->
        <div class="bg-primary pa-6 text-white d-flex align-center">
          <VAvatar size="48" color="white" variant="tonal" class="me-3">
            <VIcon icon="bx-bar-chart-alt-2" size="28" color="white" />
          </VAvatar>
          <div>
            <div class="d-flex align-center ga-2">
              <h3 class="text-h5 font-weight-bold mb-0">Отчет по доставкам: {{ reportCourier?.name }}</h3>
              <VChip v-if="reportCourier?.code" size="x-small" color="white" variant="outlined" class="font-weight-bold">
                № {{ reportCourier.code }}
              </VChip>
            </div>
            <p class="text-caption mb-0 opacity-80 d-flex align-center ga-2 mt-1">
              <span v-if="reportCourier?.phone"><VIcon icon="bx-phone" size="12" class="me-1" />{{ reportCourier.phone }}</span>
              <span>•</span>
              <span>Статус смены в iiko: <strong>{{ reportCourier?.is_shift_open ? 'Смена открыта' : 'Смена закрыта' }}</strong></span>
            </p>
          </div>
          <VSpacer />
          <VBtn icon="bx-x" variant="text" color="white" @click="showCourierReportDialog = false" />
        </div>

        <VCardText class="pa-6" style="max-height: 75vh;">
          <!-- Фильтр периодов -->
          <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-6 pa-4 bg-grey-lighten-5 rounded-xl border">
            <div>
              <div class="text-caption text-medium-emphasis font-weight-bold mb-2 text-uppercase">Период отчета:</div>
              <VBtnToggle
                v-model="reportPeriod"
                mandatory
                density="compact"
                color="primary"
                variant="outlined"
                class="rounded-pill flex-wrap"
                @update:model-value="fetchCourierReport"
              >
                <VBtn value="today" class="text-none font-weight-bold">Сегодня</VBtn>
                <VBtn value="yesterday" class="text-none font-weight-bold">Вчера</VBtn>
                <VBtn value="7days" class="text-none font-weight-bold">7 дней</VBtn>
                <VBtn value="30days" class="text-none font-weight-bold">30 дней</VBtn>
                <VBtn value="month" class="text-none font-weight-bold">Этот месяц</VBtn>
                <VBtn value="custom" class="text-none font-weight-bold">Период</VBtn>
              </VBtnToggle>
            </div>

            <!-- Выбор кастомных дат -->
            <div v-if="reportPeriod === 'custom'" class="d-flex align-center ga-2 flex-wrap mt-2 mt-md-0">
              <VTextField
                v-model="reportDateFrom"
                type="date"
                label="С"
                density="compact"
                variant="outlined"
                hide-details
                style="width: 140px;"
              />
              <VTextField
                v-model="reportDateTo"
                type="date"
                label="По"
                density="compact"
                variant="outlined"
                hide-details
                style="width: 140px;"
              />
              <VBtn
                color="primary"
                variant="flat"
                size="small"
                class="rounded-lg"
                height="40"
                @click="fetchCourierReport"
                :loading="reportLoading"
              >
                Применить
              </VBtn>
            </div>
          </div>

          <!-- Спиннер загрузки -->
          <div v-if="reportLoading" class="text-center py-12">
            <VProgressCircular indeterminate color="primary" size="48" />
            <p class="mt-4 text-grey font-weight-medium">Формируем отчет по доставкам...</p>
          </div>

          <!-- Данные отчета -->
          <div v-else-if="reportData && reportData.summary">
            <!-- 1. KPI Карточки сводки -->
            <VRow class="mb-6">
              <!-- Всего доставок -->
              <VCol cols="12" sm="6" md="4" lg="2-4">
                <VCard class="pa-4 rounded-xl border elevation-0 h-100 bg-primary-lighten-5">
                  <div class="d-flex align-center justify-space-between mb-1">
                    <span class="text-caption text-medium-emphasis font-weight-bold text-uppercase">Доставок</span>
                    <VIcon icon="bx-package" size="20" color="primary" />
                  </div>
                  <div class="text-h4 font-weight-black text-primary">{{ reportData.summary.total_orders }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">за {{ reportData.summary.work_days_count }} рабочих дней</div>
                </VCard>
              </VCol>

              <!-- Выручка -->
              <VCol cols="12" sm="6" md="4" lg="2-4">
                <VCard class="pa-4 rounded-xl border elevation-0 h-100 bg-success-lighten-5">
                  <div class="d-flex align-center justify-space-between mb-1">
                    <span class="text-caption text-medium-emphasis font-weight-bold text-uppercase">Выручка</span>
                    <VIcon icon="bx-wallet" size="20" color="success" />
                  </div>
                  <div class="text-h4 font-weight-black text-success">{{ Math.round(reportData.summary.total_revenue).toLocaleString() }} ₽</div>
                  <div class="text-caption text-medium-emphasis mt-1">общая сумма заказов</div>
                </VCard>
              </VCol>

              <!-- Средний чек -->
              <VCol cols="12" sm="6" md="4" lg="2-4">
                <VCard class="pa-4 rounded-xl border elevation-0 h-100 bg-info-lighten-5">
                  <div class="d-flex align-center justify-space-between mb-1">
                    <span class="text-caption text-medium-emphasis font-weight-bold text-uppercase">Средний чек</span>
                    <VIcon icon="bx-receipt" size="20" color="info" />
                  </div>
                  <div class="text-h4 font-weight-black text-info">{{ Math.round(reportData.summary.avg_check).toLocaleString() }} ₽</div>
                  <div class="text-caption text-medium-emphasis mt-1">на одну доставку</div>
                </VCard>
              </VCol>

              <!-- Вовремя / Опоздания -->
              <VCol cols="12" sm="6" md="4" lg="2-4">
                <VCard class="pa-4 rounded-xl border elevation-0 h-100" :class="reportData.summary.total_late > 0 ? 'bg-warning-lighten-5' : 'bg-success-lighten-5'">
                  <div class="d-flex align-center justify-space-between mb-1">
                    <span class="text-caption text-medium-emphasis font-weight-bold text-uppercase">Вовремя</span>
                    <VIcon :icon="reportData.summary.total_late > 0 ? 'bx-time' : 'bx-check-double'" size="20" :color="reportData.summary.total_late > 0 ? 'warning' : 'success'" />
                  </div>
                  <div class="text-h4 font-weight-black" :class="reportData.summary.total_late > 0 ? 'text-warning' : 'text-success'">
                    {{ reportData.summary.on_time_percent }}%
                  </div>
                  <div class="text-caption text-medium-emphasis mt-1">
                    Опозданий: <strong>{{ reportData.summary.total_late }}</strong>
                  </div>
                </VCard>
              </VCol>

              <!-- Рабочих смен/дней -->
              <VCol cols="12" sm="6" md="4" lg="2-4">
                <VCard class="pa-4 rounded-xl border elevation-0 h-100 bg-purple-lighten-5">
                  <div class="d-flex align-center justify-space-between mb-1">
                    <span class="text-caption text-medium-emphasis font-weight-bold text-uppercase">Смен/Дней</span>
                    <VIcon icon="bx-calendar" size="20" color="purple" />
                  </div>
                  <div class="text-h4 font-weight-black text-purple">{{ reportData.summary.work_days_count }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">активных дней работы</div>
                </VCard>
              </VCol>
            </VRow>

            <!-- 2. Сводные блоки: Зоны доставки и Способы оплаты (2 колонки) -->
            <VRow class="mb-6">
              <!-- Зоны доставки -->
              <VCol cols="12" md="6">
                <VCard class="pa-4 rounded-xl border elevation-0 h-100">
                  <div class="d-flex align-center justify-space-between mb-3">
                    <h4 class="text-subtitle-1 font-weight-bold d-flex align-center ga-2 mb-0">
                      <VIcon icon="bx-map-pin" color="primary" />
                      Разделение по зонам доставки
                    </h4>
                    <VChip size="x-small" color="primary" variant="tonal">
                      Зон: {{ Object.keys(reportData.summary.zones || {}).length }}
                    </VChip>
                  </div>

                  <div v-if="Object.keys(reportData.summary.zones || {}).length" class="d-flex flex-column ga-2">
                    <div
                      v-for="(zData, zName) in reportData.summary.zones"
                      :key="zName"
                      class="pa-3 rounded-lg border bg-grey-lighten-5 d-flex align-center justify-space-between"
                    >
                      <div>
                        <div class="font-weight-bold text-body-2">{{ zName }}</div>
                        <div class="text-caption text-medium-emphasis">
                          {{ Math.round((zData.count / (reportData.summary.total_orders || 1)) * 100) }}% от всех доставок
                        </div>
                      </div>
                      <div class="text-end">
                        <VChip color="primary" size="small" variant="flat" class="font-weight-bold me-1">
                          {{ zData.count }} зак.
                        </VChip>
                        <span class="text-caption font-weight-bold text-success">{{ Math.round(zData.revenue).toLocaleString() }} ₽</span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-caption text-grey text-center py-4">Нет данных по зонам</div>
                </VCard>
              </VCol>

              <!-- Способы оплаты -->
              <VCol cols="12" md="6">
                <VCard class="pa-4 rounded-xl border elevation-0 h-100">
                  <div class="d-flex align-center justify-space-between mb-3">
                    <h4 class="text-subtitle-1 font-weight-bold d-flex align-center ga-2 mb-0">
                      <VIcon icon="bx-credit-card" color="success" />
                      Разделение по способам оплат
                    </h4>
                    <VChip size="x-small" color="success" variant="tonal">
                      Типов: {{ Object.keys(reportData.summary.payments || {}).length }}
                    </VChip>
                  </div>

                  <div v-if="Object.keys(reportData.summary.payments || {}).length" class="d-flex flex-column ga-2">
                    <div
                      v-for="(pData, pName) in reportData.summary.payments"
                      :key="pName"
                      class="pa-3 rounded-lg border bg-grey-lighten-5 d-flex align-center justify-space-between"
                    >
                      <div class="d-flex align-center ga-2">
                        <VIcon
                          :icon="pName.includes('Нал') ? 'bx-money' : (pName.includes('СБП') ? 'bx-qr' : 'bx-credit-card')"
                          :color="pName.includes('Нал') ? 'warning' : 'success'"
                          size="20"
                        />
                        <div>
                          <div class="font-weight-bold text-body-2">{{ pName }}</div>
                          <div class="text-caption text-medium-emphasis">
                            {{ Math.round((pData.count / (reportData.summary.total_orders || 1)) * 100) }}% от оплат
                          </div>
                        </div>
                      </div>
                      <div class="text-end">
                        <VChip color="success" size="small" variant="flat" class="font-weight-bold me-1">
                          {{ pData.count }} зак.
                        </VChip>
                        <span class="text-caption font-weight-bold text-primary">{{ Math.round(pData.revenue).toLocaleString() }} ₽</span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-caption text-grey text-center py-4">Нет данных по оплатам</div>
                </VCard>
              </VCol>
            </VRow>

            <!-- 3. Детализация по дням -->
            <VCard class="rounded-xl border elevation-0">
              <div class="pa-4 bg-grey-lighten-5 border-b d-flex align-center justify-space-between flex-wrap ga-2">
                <h4 class="text-subtitle-1 font-weight-bold d-flex align-center ga-2 mb-0">
                  <VIcon icon="bx-calendar-event" color="primary" />
                  Детализация доставок по дням
                </h4>
                <div class="text-caption text-medium-emphasis">
                  Нажмите на день для просмотра списка заказов
                </div>
              </div>

              <div v-if="reportData.days && reportData.days.length" class="pa-2">
                <VExpansionPanels v-model="expandedReportDays" multiple variant="accordion">
                  <VExpansionPanel
                    v-for="day in reportData.days"
                    :key="day.date"
                    :value="day.date"
                    class="border rounded-lg mb-2"
                  >
                    <VExpansionPanelTitle class="py-3">
                      <div class="d-flex flex-wrap align-center justify-space-between w-100 pe-3 ga-2">
                        <!-- Дата и день недели -->
                        <div class="d-flex align-center ga-2">
                          <VAvatar size="32" color="primary" variant="tonal">
                            <span class="font-weight-bold text-caption">{{ day.date.split('-')[2] }}</span>
                          </VAvatar>
                          <div>
                            <div class="font-weight-bold text-subtitle-2">{{ day.date_formatted }}</div>
                            <div class="text-caption text-medium-emphasis">{{ day.weekday }}</div>
                          </div>
                        </div>

                        <!-- Сводка за день -->
                        <div class="d-flex align-center ga-2 flex-wrap">
                          <VChip size="small" color="primary" variant="flat" class="font-weight-bold">
                            {{ day.total_orders }} доставок
                          </VChip>
                          <VChip size="small" color="success" variant="tonal" class="font-weight-bold">
                            {{ Math.round(day.total_revenue).toLocaleString() }} ₽
                          </VChip>
                          <VChip
                            size="small"
                            :color="day.late_count > 0 ? 'warning' : 'success'"
                            variant="tonal"
                            class="font-weight-bold"
                          >
                            {{ day.late_count > 0 ? `Опозданий: ${day.late_count}` : 'Вовремя 100%' }}
                          </VChip>
                        </div>
                      </div>
                    </VExpansionPanelTitle>

                    <VExpansionPanelText class="pt-2">
                      <!-- Зоны и оплаты за этот день -->
                      <div class="d-flex flex-wrap ga-4 mb-4 pb-3 border-b">
                        <!-- Зоны дня -->
                        <div class="flex-grow-1">
                          <div class="text-caption text-disabled font-weight-bold text-uppercase mb-1">Зоны дня:</div>
                          <div class="d-flex flex-wrap ga-1">
                            <VChip
                              v-for="(zD, zN) in day.zones"
                              :key="zN"
                              size="x-small"
                              color="primary"
                              variant="outlined"
                            >
                              {{ zN }}: {{ zD.count }} ({{ Math.round(zD.revenue) }} ₽)
                            </VChip>
                          </div>
                        </div>

                        <!-- Оплаты дня -->
                        <div class="flex-grow-1">
                          <div class="text-caption text-disabled font-weight-bold text-uppercase mb-1">Способы оплаты:</div>
                          <div class="d-flex flex-wrap ga-1">
                            <VChip
                              v-for="(pD, pN) in day.payments"
                              :key="pN"
                              size="x-small"
                              color="success"
                              variant="outlined"
                            >
                              {{ pN }}: {{ pD.count }} ({{ Math.round(pD.revenue) }} ₽)
                            </VChip>
                          </div>
                        </div>
                      </div>

                      <!-- Таблица заказов за день -->
                      <div class="text-caption text-disabled font-weight-bold text-uppercase mb-2">Заказы курьера за день:</div>
                      <div class="table-responsive">
                        <table class="w-100 courier-day-orders-table">
                          <thead>
                            <tr class="text-caption text-medium-emphasis border-b">
                              <th class="text-start py-2">№ Заказа</th>
                              <th class="text-start py-2">Время</th>
                              <th class="text-start py-2">Адрес доставки</th>
                              <th class="text-start py-2">Зона</th>
                              <th class="text-start py-2">Оплата</th>
                              <th class="text-end py-2">Сумма</th>
                              <th class="text-center py-2">Статус</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="ord in day.orders_sample" :key="ord.id" class="border-b text-body-2">
                              <td class="py-2 font-weight-bold text-primary">№{{ ord.external_number }}</td>
                              <td class="py-2 text-medium-emphasis">{{ ord.created_time }}</td>
                              <td class="py-2 text-truncate" style="max-width: 250px;">{{ ord.address }}</td>
                              <td class="py-2">
                                <VChip size="x-small" variant="tonal" color="primary">{{ ord.zone }}</VChip>
                              </td>
                              <td class="py-2">
                                <span class="text-caption font-weight-medium">{{ ord.payment_method }}</span>
                              </td>
                              <td class="py-2 text-end font-weight-bold">{{ Math.round(ord.amount) }} ₽</td>
                              <td class="py-2 text-center">
                                <VChip v-if="ord.is_late" color="warning" size="x-small" variant="flat">
                                  +{{ ord.delay_minutes }} мин
                                </VChip>
                                <VChip v-else color="success" size="x-small" variant="tonal">
                                  Вовремя
                                </VChip>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </VExpansionPanelText>
                  </VExpansionPanel>
                </VExpansionPanels>
              </div>

              <div v-else class="text-center py-8 text-grey">
                За выбранный период доставок у курьера не найдено
              </div>
            </VCard>
          </div>

          <div v-else class="text-center py-12 text-grey">
            Нет данных по доставкам для данного курьера
          </div>
        </VCardText>

        <VCardActions class="pa-4 border-t bg-grey-lighten-5 d-flex justify-end">
          <VBtn color="primary" variant="flat" class="rounded-lg px-6 font-weight-bold" @click="showCourierReportDialog = false">
            Закрыть отчет
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </VContainer>
</template>

<style scoped>
@import "@styles/courier.css";

.courier-day-orders-table {
  border-collapse: collapse;
}
.courier-day-orders-table th,
.courier-day-orders-table td {
  padding: 8px 10px;
}
.courier-day-orders-table tr:last-child {
  border-bottom: none;
}
.opacity-80 {
  opacity: 0.8;
}

/* Адаптивность модальных окон оплаты для экранов с низким разрешением */
@media (max-height: 700px) {
  .sbp-qr-img {
    width: 170px !important;
    height: 170px !important;
  }
  .qr-container-wrapper {
    margin-bottom: 12px !important;
  }
}
@media (max-width: 480px) {
  .sbp-qr-img {
    width: 190px !important;
    height: 190px !important;
  }
}

</style>
