<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { getAuthHeaders, authState } from '@/utils/auth'
import { useTheme } from 'vuetify'
import { useToast } from 'vue-toastification'
import OrderArchiveCard from '@/components/OrderArchiveCard.vue'

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

// Фильтры для архива
const selectedDate = ref(new Date().toISOString().substr(0, 10))
const archiveCourierFilter = ref(null)
const showDatePicker = ref(false)

const setPreferredNavigator = (val) => {
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
    if (!quiet) {
      const syncRes = await fetch('/api/v1/courier/sync', {
        method: 'POST',
        headers: getAuthHeaders(),
      })
      const syncData = await syncRes.json()
      if (syncData.status === 'success') {
        toast.success('Синхронизация с iiko завершена')
      }
    }

    if (activeTab.value === 'orders') {
      await fetchOrders()
    } else if (activeTab.value === 'archive') {
      await fetchOrders(true)
    } else if (activeTab.value === 'shifts') {
      await fetchShifts()
    } else if (activeTab.value === 'couriers') {
      await fetchActiveCouriers()
    }
    lastUpdated.value = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch (e) {
    if (!quiet) {
      error.value = 'Ошибка загрузки данных'
      console.error('Fetch error:', e)
    }
  } finally {
    if (!quiet) loading.value = false
  }
}

const fetchOrders = async (includeClosed = false) => {
  let url = '/api/v1/courier/orders'
  const params = new URLSearchParams()
  
  if (includeClosed) {
    params.append('include_closed', 'true')
    if (selectedDate.value) {
      params.append('date_from', selectedDate.value)
      params.append('date_to', selectedDate.value)
    }
    if (archiveCourierFilter.value) {
      params.append('courier_filter', archiveCourierFilter.value)
    }
  }
  
  const queryString = params.toString()
  if (queryString) url += `?${queryString}`

  const res = await fetch(url, {
    headers: getAuthHeaders(),
  })
  const data = await res.json()
  if (data.status === 'success') {
    if (includeClosed) {
      archiveOrders.value = data.data
    } else {
      orders.value = data.data
    }
  } else {
    error.value = data.message || 'Ошибка загрузки заказов'
  }
}

const formatDateLocal = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const setArchiveDate = (action) => {
  let d = new Date(selectedDate.value + 'T12:00:00')
  if (action === 'today') {
    selectedDate.value = formatDateLocal(new Date())
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

const updateStatus = async (orderId, status) => {
  loading.value = true
  try {
    const res = await fetch(`/api/v1/courier/orders/${orderId}/status?status=${status}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })

    if (res.ok) {
      await fetchOrders()
      if (status === 'Delivered') {
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
    case 'ready': return 'orange'
    case 'delivering':
    case 'onway': return 'blue'
    case 'delivered': return 'green'
    case 'closed': return 'grey'
    case 'cancelled': return 'red'
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
  return a.line1 || 'Адрес не указан'
}

const openMaps = (order, provider = null) => {
  const addr = formatAddress(order)
  if (addr === 'Адрес не указан') {
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
      url = `https://www.petalmaps.com/search/?query=${encodeURIComponent(addr)}`
      break
    default:
      url = `https://yandex.ru/maps/?text=${encodeURIComponent(addr)}`
  }
  
  if (url) window.open(url, '_blank')
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

const getLateness = minutes => {
  if (!minutes || minutes <= 0) return null
  return `${minutes} мин.`
}

const formatDate = dateStr => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

const openDetails = order => {
  detailsOrder.value = order
  showDetailsDialog.value = true
}

const getCountdown = expectedTime => {
  if (!expectedTime) return null
  const diff = new Date(expectedTime) - currentTime.value
  const mins = Math.floor(diff / 60000)
  if (mins < -999) return null // Слишком старый
  return mins
}

const getCountdownColor = mins => {
  if (mins === null) return 'grey'
  if (mins < 0) return 'red'
  if (mins < 15) return 'orange'
  return 'success'
}

const startTimers = () => {
  // Обновление данных каждые 30 секунд
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

watch(activeTab, () => {
  fetchData()
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
  <VContainer class="pa-2 pa-sm-4 courier-app-wrapper">
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
            icon="bx-refresh"
            variant="flat"
            color="primary"
            :loading="loading"
            class="rounded-pill px-4"
            @click="fetchData({ quiet: false, forceSync: true })"
          >
            <VIcon icon="bx-refresh" class="me-1" />
            Обновить
          </VBtn>
      </div>

      <div class="d-flex align-center bg-white px-4 py-2 border-b">
        <VIcon icon="bx-cog" size="20" color="grey" class="me-2" />
        <span class="text-caption font-weight-medium text-grey-darken-1 me-3">Навигатор по умолчанию:</span>
        <VSelect
          v-model="preferredNavigator"
          :items="[
            { title: 'Яндекс', value: 'yandex' },
            { title: '2ГИС', value: '2gis' },
            { title: 'Google', value: 'google' },
            { title: 'Petal', value: 'petal' }
          ]"
          variant="plain"
          density="compact"
          hide-details
          class="navigator-select"
          @update:model-value="setPreferredNavigator"
        />
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

        <div v-else class="orders-list">
          <VRow>
            <VCol
              v-for="order in orders"
              :key="order.id"
              cols="12"
              md="6"
              lg="4"
            >
              <VCard class="order-card-premium mb-4" elevation="0" border>
                <div :class="`status-strip bg-${getStatusColor(order.status)}`" />
                
                <VCardItem class="pb-2">
                  <div class="d-flex justify-space-between align-center mb-2">
                    <div class="d-flex flex-column">
                      <div class="d-flex align-center gap-2 mb-1">
                        <VChip
                          :color="getStatusColor(order.status)"
                          size="x-small"
                          variant="flat"
                          class="font-weight-bold"
                        >
                          {{ getStatusText(order.status) }}
                        </VChip>
                        <VChip
                          v-if="getCountdown(order.expected_time) !== null"
                          :color="getCountdownColor(getCountdown(order.expected_time))"
                          size="x-small"
                          variant="tonal"
                          class="font-weight-black"
                        >
                          <VIcon icon="bx-timer" size="14" class="me-1" />
                          {{ getCountdown(order.expected_time) }} мин
                        </VChip>
                      </div>
                      <div class="d-flex align-center gap-1">
                        <VIcon 
                          :icon="order.is_paid ? 'bx-check-shield' : 'bx-error-circle'" 
                          :color="order.is_paid ? 'success' : 'warning'" 
                          size="14" 
                        />
                        <span 
                          class="text-caption font-weight-bold" 
                          :class="order.is_paid ? 'text-success' : 'text-warning'"
                        >
                          {{ order.is_paid ? 'Оплачено' : 'Ожидает оплаты' }}
                        </span>
                      </div>
                    </div>
                    <div class="text-right">
                      <div class="text-h5 font-weight-black text-primary">
                        {{ order.sum }} ₽
                      </div>
                      <div class="text-caption text-grey-darken-1 font-weight-medium">
                        {{ order.payment_method || 'Способ не указан' }}
                      </div>
                    </div>
                  </div>
                  
                  <VCardTitle class="text-h6 font-weight-bold mb-1">
                    Заказ №{{ order.number || order.id.substring(0, 4) }}
                  </VCardTitle>
                  
                  <div class="address-box pa-2 rounded-lg bg-grey-lighten-4 mb-3 d-flex align-center cursor-pointer" @click="openMaps(order)">
                    <VIcon icon="bx-map" color="primary" class="me-2" />
                    <span class="text-body-2 font-weight-medium text-truncate flex-grow-1">
                      {{ formatAddress(order) }}
                    </span>
                    <VBtn
                      icon="bx-copy"
                      variant="text"
                      size="x-small"
                      color="grey-darken-1"
                      @click.stop="copyToClipboard(formatAddress(order))"
                      title="Копировать адрес"
                    />
                  </div>

                  <!-- Быстрая навигация -->
                  <div class="d-flex align-center gap-2 mb-4 px-1">
                    <span class="text-caption text-grey-darken-1 me-1">Навигатор:</span>
                    <VBtn
                      variant="tonal"
                      size="x-small"
                      color="warning"
                      class="rounded-lg"
                      @click.stop="openMaps(order, 'yandex')"
                    >
                      Яндекс
                    </VBtn>
                    <VBtn
                      variant="tonal"
                      size="x-small"
                      color="info"
                      class="rounded-lg"
                      @click.stop="openMaps(order, '2gis')"
                    >
                      2ГИС
                    </VBtn>
                    <VBtn
                      variant="tonal"
                      size="x-small"
                      color="success"
                      class="rounded-lg"
                      @click.stop="openMaps(order, 'google')"
                    >
                      Google
                    </VBtn>
                    <VBtn
                      variant="tonal"
                      size="x-small"
                      color="secondary"
                      class="rounded-lg"
                      @click.stop="openMaps(order, 'petal')"
                    >
                      Petal
                    </VBtn>
                  </div>
                </VCardItem>

                <VCardText class="py-2">
                  <div class="customer-info d-flex align-center justify-space-between mb-3">
                    <div class="d-flex align-center">
                      <VAvatar size="32" color="primary-lighten-5" class="me-2">
                        <VIcon icon="bx-user" color="primary" size="18" />
                      </VAvatar>
                      <span class="font-weight-bold text-body-2">{{ order.customer?.name || 'Гость' }}</span>
                    </div>
                    <VBtn
                      v-if="order.customer?.phone"
                      icon="bx-phone"
                      color="success"
                      variant="tonal"
                      size="small"
                      density="comfortable"
                      @click="callCustomer(order.customer.phone)"
                    />
                  </div>

                  <div v-if="order.items?.length" class="items-preview pa-3 rounded-lg bg-grey-lighten-5 mb-3 border">
                    <p class="text-caption text-primary mb-2 font-weight-bold d-flex align-center">
                      <VIcon icon="bx-list-ul" size="14" class="me-1" />
                      СОСТАВ ЗАКАЗА:
                    </p>
                    <div class="order-items-list">
                      <div 
                        v-for="(item, idx) in order.items" 
                        :key="idx"
                        class="d-flex flex-column mb-1 pb-1"
                        :class="idx < order.items.length - 1 ? 'border-bottom-dashed' : ''"
                      >
                        <div class="d-flex justify-space-between align-start">
                          <span class="text-body-2 font-weight-medium flex-grow-1">
                            {{ item.name }}
                          </span>
                          <span class="text-body-2 font-weight-bold text-no-wrap ms-2">
                            {{ item.amount }} шт.
                          </span>
                        </div>
                        <!-- Модификаторы -->
                        <div v-if="item.modifiers?.length" class="modifiers-list ps-3">
                          <div 
                            v-for="(mod, midx) in item.modifiers" 
                            :key="midx"
                            class="text-caption text-grey-darken-1"
                          >
                            • {{ mod.name }} ({{ mod.amount }} шт.)
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-if="isSuperAdmin && order.courier_name" class="admin-courier-tag pa-1 rounded d-flex align-center">
                    <VIcon icon="bx-bicycle" size="14" color="primary" class="me-1" />
                    <span class="text-caption font-weight-medium">Курьер: {{ order.courier_name }}</span>
                  </div>
                </VCardText>

                <VDivider class="mx-4" />

                <VCardActions class="pa-4">
                  <div class="w-100">
                    <template v-if="!isSuperAdmin">
                      <VBtn
                        v-if="order.status?.toLowerCase() === 'ready'"
                        block
                        color="blue"
                        variant="flat"
                        size="large"
                        prepend-icon="bx-navigation"
                        class="mb-2"
                        @click="updateStatus(order.id, 'OnWay')"
                      >
                        Взять в работу
                      </VBtn>

                      <VBtn
                        v-if="order.status?.toLowerCase() === 'delivering'"
                        block
                        color="green-darken-1"
                        variant="flat"
                        size="large"
                        prepend-icon="bx-check-double"
                        class="mb-2"
                        @click="updateStatus(order.id, 'Delivered')"
                      >
                        Доставил
                      </VBtn>

                      <VBtn
                        v-if="order.status?.toLowerCase() === 'delivered'"
                        block
                        color="primary"
                        variant="elevated"
                        size="large"
                        prepend-icon="bx-wallet"
                        class="mb-2"
                        @click="openCloseDialog(order)"
                      >
                        Оплатить и закрыть
                      </VBtn>
                    </template>
                    
                    <VBtn 
                      block 
                      variant="tonal" 
                      color="primary" 
                      prepend-icon="bx-detail"
                      @click="openDetails(order)"
                    >
                      Подробнее
                    </VBtn>
                  </div>
                </VCardActions>
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
              @update:model-value="fetchOrders(true)"
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
              @update:model-value="fetchOrders(true)"
            />
          </div>
          
          <div v-if="archiveOrders.length" class="archive-summary mt-3 text-caption text-grey-darken-1 d-flex align-center flex-wrap gap-x-4 gap-y-2">
            <div class="d-flex align-center">
              <VIcon icon="bx-package" size="16" class="me-1" />
              Заказов: <span class="font-weight-bold ms-1 text-primary">{{ archiveOrders.length }}</span>
            </div>
            <div class="d-flex align-center">
              <VIcon icon="bx-wallet" size="16" class="me-1" />
              Сумма: <span class="font-weight-bold ms-1 text-primary">{{ archiveOrders.reduce((sum, o) => sum + (o.sum || 0), 0).toFixed(2) }} ₽</span>
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
          v-if="!archiveOrders.length" 
          class="empty-state text-center py-16"
        >
          <VIcon 
            size="64" 
            color="grey-lighten-2" 
            icon="bx-archive" 
            class="mb-4" 
          />
          <h3 class="text-h6 font-weight-bold">Архив пуст</h3>
          <p class="text-body-2 text-grey">Здесь будут отображаться завершенные доставки</p>
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
                <OrderArchiveCard :order="order" />
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
            <OrderArchiveCard :order="order" />
          </VCol>
        </VRow>
        </VRow>
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

    <!-- Диалог деталей заказа -->
    <VDialog 
      v-model="showDetailsDialog" 
      max-width="600px" 
      scrollable
    >
      <VCard 
        v-if="detailsOrder"
        class="rounded-xl"
      >
        <VCardTitle class="d-flex justify-space-between align-center pa-4 bg-primary text-white">
          <div class="d-flex align-center">
            <VIcon icon="bx-receipt" class="me-2" />
            <span>Детали заказа №{{ detailsOrder.number || detailsOrder.id.substring(0, 4) }}</span>
          </div>
          <VBtn icon="bx-x" variant="text" color="white" @click="showDetailsDialog = false" />
        </VCardTitle>

        <VCardText class="pa-4">
          <div class="info-section mb-6">
            <h4 class="text-overline text-grey-darken-1 mb-2">Информация о клиенте</h4>
            <div class="d-flex align-center mb-2">
              <VAvatar color="primary-lighten-5" size="40" class="me-3">
                <VIcon icon="bx-user" color="primary" />
              </VAvatar>
              <div>
                <div class="text-subtitle-1 font-weight-bold">{{ detailsOrder.customer?.name || 'Гость' }}</div>
                <div class="text-body-2 text-grey-darken-1">{{ detailsOrder.customer?.phone || 'Телефон не указан' }}</div>
              </div>
            </div>
            <div class="d-flex align-center pa-3 rounded-lg bg-grey-lighten-4 mt-2 cursor-pointer" @click="openMaps(detailsOrder)">
              <VIcon icon="bx-map" color="primary" class="me-3" />
              <div class="text-body-2 font-weight-medium flex-grow-1">{{ formatAddress(detailsOrder) }}</div>
              <VBtn
                icon="bx-copy"
                variant="text"
                size="small"
                color="grey-darken-1"
                @click.stop="copyToClipboard(formatAddress(detailsOrder))"
              />
            </div>
            <div v-if="detailsOrder.comment" class="comment-box mt-3 pa-3 rounded-lg bg-amber-lighten-5 border-amber-lighten-3 border">
              <div class="text-caption text-amber-darken-4 font-weight-bold mb-1">КОММЕНТАРИЙ:</div>
              <div class="text-body-2">{{ detailsOrder.comment }}</div>
            </div>
          </div>

          <div class="items-section mb-6">
            <h4 class="text-overline text-grey-darken-1 mb-2">Состав заказа</h4>
            <VList density="compact" class="bg-transparent pa-0">
              <VListItem v-for="(item, idx) in detailsOrder.items" :key="idx" class="px-0 py-1">
                <template v-slot:prepend>
                  <VChip size="x-small" color="primary" variant="tonal" class="me-2">{{ item.amount }}x</VChip>
                </template>
                <VListItemTitle class="text-body-2 font-weight-bold">{{ item.name }}</VListItemTitle>
                <template v-slot:append>
                  <span class="text-body-2 font-weight-bold">{{ (item.price * item.amount).toFixed(2) }} ₽</span>
                </template>
              </VListItem>
            </VList>
          </div>

          <div class="payment-section pa-4 rounded-xl bg-grey-lighten-4">
            <h4 class="text-overline text-grey-darken-1 mb-3">Оплата и статус</h4>
            <div class="d-flex justify-space-between align-center mb-2">
              <span class="text-body-2">Сумма заказа:</span>
              <span class="text-body-1 font-weight-black">{{ detailsOrder.sum }} ₽</span>
            </div>
            <div class="d-flex justify-space-between align-center mb-2">
              <span class="text-body-2">Способ оплаты:</span>
              <span class="text-body-2 font-weight-bold text-primary">{{ detailsOrder.payment_method || 'Не указан' }}</span>
            </div>
            <div class="d-flex justify-space-between align-center mb-2">
              <span class="text-body-2">Статус оплаты:</span>
              <VChip :color="detailsOrder.is_paid ? 'success' : 'warning'" size="x-small" variant="flat">
                {{ detailsOrder.is_paid ? 'Оплачено' : 'Ожидает оплаты' }}
              </VChip>
            </div>
            <div v-if="!detailsOrder.is_paid && detailsOrder.left_to_pay > 0" class="d-flex justify-space-between align-center mt-3 pt-3 border-t">
              <span class="text-body-1 font-weight-bold text-error">К оплате:</span>
              <span class="text-h6 font-weight-black text-error">{{ detailsOrder.left_to_pay }} ₽</span>
            </div>
          </div>
        </VCardText>

        <VCardActions class="pa-4">
          <VBtn block color="primary" variant="flat" size="large" @click="showDetailsDialog = false">
            Закрыть
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

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
.courier-app-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
}

.main-title {
  color: #2c3e50;
  letter-spacing: -0.5px;
}

.order-card-premium {
  border-radius: 16px !important;
  transition: transform 0.2s, box-shadow 0.2s;
  background-color: #fff;
}

.order-card-premium:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12) !important;
}

.status-strip {
  height: 4px;
  width: 100%;
}

.address-box {
  transition: background-color 0.2s;
}

.address-box:hover {
  background-color: #f0f0f0 !important;
}

.action-btn-main {
  border-radius: 12px !important;
  text-transform: none !important;
  font-weight: 700 !important;
  letter-spacing: 0;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background-color: #4caf50;
  border-radius: 50%;
  display: inline-block;
  box-shadow: 0 0 0 rgba(76, 175, 80, 0.4);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(76, 175, 80, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
}

.custom-tabs-nav :deep(.v-tab) {
  font-weight: 700 !important;
}

.payment-type-list .v-list-item--active {
  border: 2px solid rgb(var(--v-theme-primary)) !important;
}
  .border-bottom-dashed {
    border-bottom: 1px dashed #e0e0e0;
  }
  
  .modifiers-list {
    border-left: 2px solid #eeeeee;
    margin-top: 2px;
  }
</style>
