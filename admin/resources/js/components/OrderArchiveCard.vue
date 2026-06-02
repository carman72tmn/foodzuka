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
  if (!order.address && !order.delivery_address) return 'Адрес не указан'

  const a = order.address || order.delivery_address
  if (typeof a === 'string') return a
  if (a.line1) return a.line1
  
  const parts = []

  if (a.city) parts.push(a.city)
  if (a.street) parts.push(a.street)
  if (a.house || a.home) parts.push(`д. ${a.house || a.home}`)

  return parts.join(', ') || 'Адрес не указан'
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
    <div class="card-header-status d-flex align-center justify-space-between">
      <div class="d-flex align-center ga-2">
        <VChip 
          :color="getStatusColor(order.status)" 
          size="x-small" 
          variant="flat" 
          class="text-uppercase font-weight-black text-white"
        >
          {{ getStatusText(order.status) }}
        </VChip>
        <span class="text-card-small text-slate-400">
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
    <div class="section-divider">
      <div class="d-flex justify-space-between align-center">
        <div>
          <div class="text-card-title">№{{ order.external_number || order.number || '???' }}</div>
          <div class="text-card-caption d-flex align-center ga-1 mt-1">
            <VIcon icon="bx-user" size="14" />
            <span class="text-truncate">{{ order.courier_name || '—' }}</span>
          </div>
        </div>
        <VBtn
          icon="bx-dots-vertical-rounded"
          variant="text"
          color="slate-400"
          size="small"
          @click="emit('open-details', order)"
        />
      </div>
    </div>

    <!-- 3. Client & Address -->
    <div class="section-divider">
      <div class="d-flex align-center mb-3">
        <VAvatar size="32" color="primary-lighten-5" class="me-2">
          <VIcon icon="bx-user" size="16" color="primary" />
        </VAvatar>
        <span class="text-card-body font-weight-bold text-truncate">
          {{ order.customer_name || 'Гость' }}
        </span>
      </div>
      
      <div class="address-premium-box d-flex align-start ga-2" @click="openMaps(order)">
        <VIcon icon="bx-map" color="primary" class="mt-1" size="16" />
        <div class="text-card-caption font-weight-bold line-height-sm flex-grow-1">
          {{ formatAddress(order) }}
        </div>
      </div>
    </div>

    <!-- 4. Time Metrics -->
    <div class="section-divider bg-slate-50 py-2">
      <div class="d-flex justify-space-between mb-1">
        <span class="text-card-small text-slate-400">В пути:</span>
        <span class="text-card-small font-weight-bold">{{ getDuration(order.on_the_way_time, order.actual_time) || '—' }}</span>
      </div>
      <div class="d-flex justify-space-between">
        <span class="text-card-small text-slate-400">Завершено:</span>
        <span class="text-card-small font-weight-bold text-success">{{ formatTime(order.actual_time) }}</span>
      </div>
    </div>

    <!-- 5. Payment Footer -->
    <div class="card-footer-payment mt-auto">
      <div class="d-flex justify-space-between align-center">
        <div class="d-flex flex-column">
          <span class="text-card-small text-slate-400 leading-none mb-1">Сумма</span>
          <span class="text-body-1 font-weight-black text-slate-900 leading-none">
            {{ formatPrice(order.total_with_discount || order.sum) }} ₽
          </span>
        </div>
        <div class="text-right">
          <div class="d-flex align-center justify-end ga-1 mb-1">
            <VIcon icon="bx-wallet" size="14" color="slate-400" />
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
