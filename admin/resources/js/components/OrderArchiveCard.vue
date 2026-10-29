<script setup>
import { defineProps, defineEmits } from 'vue'
import { formatDate, formatTime, formatDateTime } from '@/utils/date'

const props = defineProps({
  order: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['openDetails'])

const getStatusColor = status => {
  const s = status ? status.toLowerCase() : ''

  if (s === 'delivered') return 'green-darken-2'
  if (s === 'onway' || s === 'delivering') return 'blue-darken-2'
  if (s === 'closed') return 'slate-900'
  if (s === 'cancelled') return 'red-darken-2'
  if (s === 'ready') return 'amber-darken-2'
  
  return 'grey'
}

const getStatusText = status => {
  const texts = {
    'DELIVERED': 'Доставлен',
    'ON_WAY': 'В пути',
    'WAITING': 'Ожидает',
    'CANCELLED': 'Отменен',
    'CLOSED': 'Закрыт',
    'Ready': 'Готов',
    'OnWay': 'В пути',
    'Delivered': 'Доставлен',
    'delivering': 'В пути',
  }

  return texts[status] || status
}

const getDuration = (start, end) => {
  if (!start || !end) return null

  const diff = Math.floor((new Date(end) - new Date(start)) / 60000)

  return diff > 0 ? `${diff} мин.` : '< 1 мин.'
}

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

const openMaps = (order, type = 'yandex') => {
  const addr = encodeURIComponent(formatAddress(order))

  if (type === 'yandex') {
    window.open(`https://yandex.ru/maps/?text=${addr}`, '_blank')
  } else if (type === '2gis') {
    window.open(`https://2gis.ru/search/${addr}`, '_blank')
  } else {
    window.open(`https://www.google.com/maps/search/?api=1&query=${addr}`, '_blank')
  }
}

const copyToClipboard = text => {
  if (!text || text === 'Адрес не указан') return

  navigator.clipboard.writeText(text)
}

const formatPrice = val => {
  if (val === null || val === undefined) return '0'

  const num = parseFloat(val)

  return isNaN(num) ? '0' : num.toLocaleString()
}

const getPaymentIcon = kind => {
  const icons = {
    Cash: 'bx-money',
    Card: 'bx-credit-card',
    Online: 'bx-globe',
    External: 'bx-link-external',
    IikoCard: 'bx-gift',
  }

  return icons[kind] || 'bx-wallet'
}

const getPaymentStatusText = order => {
  if (order.is_paid) return 'Оплачено'

  const left = parseFloat(order.left_to_pay || 0)
  const total = parseFloat(order.total_with_discount || order.sum || 0)

  if (left > 0 && left < total) return 'Частично'

  return 'Ожидает'
}

const getPaymentStatusColor = order => {
  if (order.is_paid) return 'success'

  const left = parseFloat(order.left_to_pay || 0)

  if (left > 0) return 'warning'

  return 'grey'
}
</script>

<template>
  <VCard
    class="delivery-card-premium archive-card d-flex flex-column"
    variant="flat"
  >
    <!-- 1. Header: Status & Timers -->
    <div class="card-header-compact d-flex align-center justify-space-between">
      <div class="d-flex align-center ga-2">
        <VChip 
          :color="getStatusColor(order.status)" 
          size="x-small" 
          variant="flat" 
          class="text-uppercase font-weight-black text-white"
        >
          {{ getStatusText(order.status) }}
        </VChip>
        <span class="text-card-caption font-weight-bold">
          {{ formatDate(order.iiko_creation_time || order.created_at) }}
        </span>
      </div>
      
      <div class="text-right">
        <div v-if="order.delay_minutes > 0" class="d-flex align-center justify-end ga-1">
          <VIcon icon="bx-alarm-exclamation" size="14" color="error" />
          <span class="text-card-small text-error font-weight-black">
            +{{ order.delay_minutes }} м
          </span>
        </div>
      </div>
    </div>

    <!-- 2. Identity -->
    <div class="section-compact py-1.5">
      <div class="d-flex justify-space-between align-center">
        <div>
          <div class="text-card-title" style="font-size: 1rem !important;">№{{ order.external_number || order.number || '???' }}</div>
          <div class="text-card-caption d-flex align-center ga-1 mt-0.5" style="font-size: 0.75rem !important;">
            <VIcon icon="bx-user" size="12" />
            <span class="text-truncate font-weight-medium">{{ order.courier_name || '—' }}</span>
          </div>
        </div>
        <VBtn
          icon="bx-dots-vertical-rounded"
          variant="text"
          color="medium-emphasis"
          size="small"
          @click="emit('open-details', order)"
        />
      </div>
    </div>

    <!-- 3. Client & Address -->
    <div class="section-compact py-1.5">
      <div class="d-flex align-center mb-1 ga-1.5">
        <VIcon icon="bx-user" size="14" color="primary" />
        <span class="text-card-body font-weight-bold text-truncate" style="font-size: 0.8125rem !important;">
          {{ order.customer_name || 'Гость' }}
        </span>
      </div>
      
      <div class="address-premium-box d-flex align-start ga-1.5 py-1 px-2" @click="openMaps(order)">
        <VIcon icon="bx-map" color="primary" class="mt-0.5" size="14" />
        <div class="text-card-caption font-weight-bold line-height-xs flex-grow-1 text-slate-800" style="font-size: 0.75rem !important;">
          {{ formatAddress(order) }}
        </div>
      </div>
    </div>

    <!-- 4. Time Metrics -->
    <div class="section-compact py-1 px-3" style="background: var(--courier-slate-100);">
      <div class="d-flex justify-space-between mb-0.5">
        <span class="text-card-small text-medium-emphasis" style="font-size: 0.65rem !important;">В пути:</span>
        <span class="text-card-caption font-weight-bold text-slate-800" style="font-size: 0.75rem !important;">{{ getDuration(order.on_the_way_time, order.actual_time) || '—' }}</span>
      </div>
      <div class="d-flex justify-space-between">
        <span class="text-card-small text-medium-emphasis" style="font-size: 0.65rem !important;">Завершено:</span>
        <span class="text-card-caption font-weight-bold text-success" style="font-size: 0.75rem !important;">{{ formatTime(order.actual_time) }}</span>
      </div>
    </div>

    <!-- 5. Payment Footer -->
    <div class="card-footer-compact mt-auto">
      <div class="d-flex justify-space-between align-center">
        <div class="d-flex flex-column">
          <span class="text-card-small text-medium-emphasis leading-none mb-0.5" style="font-size: 0.65rem !important;">Сумма</span>
          <span class="text-body-1 font-weight-black text-high-emphasis leading-none">
            {{ formatPrice(order.total_with_discount || order.sum) }} ₽
          </span>
        </div>
        <div class="text-right">
          <div class="d-flex align-center justify-end ga-1 mb-0.5">
            <VIcon icon="bx-wallet" size="12" class="text-medium-emphasis" />
            <span class="text-card-caption text-medium-emphasis font-weight-medium" style="font-size: 0.75rem !important;">{{ order.payment_method || '—' }}</span>
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
    </div>
  </VCard>
</template>

<style scoped>
@import "@styles/courier.css";

.archive-card {
  opacity: 0.9;
  transition: opacity 0.2s;
}

.archive-card:hover {
  opacity: 1;
}
</style>
