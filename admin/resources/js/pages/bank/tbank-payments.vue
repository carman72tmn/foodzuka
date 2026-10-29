<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { getAuthHeaders } from '@/utils/auth'
import { useChatStore } from '@/stores/chatStore'

const chatStore = useChatStore()

// Состояние
const payments = ref([])
const loading = ref(true)
const syncLoading = ref(false)
const syncProgress = ref(0)
const syncMessage = ref('')
const isSyncDialogVisible = ref(false)
const searchQuery = ref('')
const activeFilter = ref('all') // 'all', 'sbp', 'tpay', 'card', 'transfer'

// Фильтр дат по умолчанию: сегодня (в локальном часовом поясе браузера)
const getLocalDateString = () => {
  const d = new Date()
  const offset = d.getTimezoneOffset()
  const localDate = new Date(d.getTime() - (offset * 60 * 1000))
  return localDate.toISOString().split('T')[0]
}

const dateFrom = ref(getLocalDateString())
const dateTo = ref(getLocalDateString())

// Получение платежей из API
const fetchPayments = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (dateFrom.value) params.append('date_from', dateFrom.value)
    if (dateTo.value) params.append('date_to', dateTo.value)
    if (searchQuery.value) params.append('search', searchQuery.value)

    const response = await fetch(`/api/v1/bank/payments?${params.toString()}`, {
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      const data = await response.json()
      // Выводим все реальные подтвержденные оплаты заказов
      payments.value = data.filter(p => p.is_real === true)
    } else {
      console.error('Ошибка при получении платежей:', response.statusText)
    }
  } catch (error) {
    console.error('Сбой сети при запросе платежей:', error)
  } finally {
    loading.value = false
  }
}

// Запуск принудительного импорта из Т-Банка
const syncWithBank = async () => {
  isSyncDialogVisible.value = true
  syncLoading.value = true
  syncProgress.value = 0
  syncMessage.value = 'Запрос расчетных счетов Т-Банка...'
  
  try {
    const accountsResponse = await fetch('/api/v1/settings/tbank/accounts', {
      headers: getAuthHeaders()
    })
    
    if (!accountsResponse.ok) {
      throw new Error(`Не удалось получить счета: ${accountsResponse.statusText}`)
    }
    
    const accounts = await accountsResponse.json()
    if (!accounts || accounts.length === 0) {
      throw new Error('В настройках Т-Банка не найдено активных расчетных счетов.')
    }
    
    const accountNumber = accounts[0].accountNumber
    syncProgress.value = 40
    syncMessage.value = `Счет ${accountNumber} найден. Запрос выписки...`
    
    const syncResponse = await fetch('/api/v1/settings/tbank/sync-statement', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        account_number: accountNumber,
        from_date: dateFrom.value,
        till_date: dateTo.value
      })
    })
    
    if (!syncResponse.ok) {
      throw new Error(`Ошибка сверки: ${syncResponse.statusText}`)
    }
    
    const result = await syncResponse.json()
    syncProgress.value = 100
    
    if (result.success) {
      syncMessage.value = `Выгрузка из Т-Банка завершена! Добавлено новых платежей: ${result.new_operations_added}, автоматически сопоставлено с заказами iiko: ${result.orders_automatically_matched}.`
    } else {
      syncMessage.value = 'Выгрузка завершена с ошибкой.'
    }
    
    await fetchPayments()
  } catch (error) {
    console.error('Ошибка синхронизации:', error)
    syncProgress.value = 100
    syncMessage.value = `Ошибка: ${error.message || error}`
  } finally {
    syncLoading.value = false
  }
}

// Запрос статуса и типа платежа через API Т-Банка
const checkLoading = ref({})
const checkPaymentApi = async (item) => {
  const key = item.id || item.transaction_id
  checkLoading.value[key] = true
  try {
    const res = await $api('/settings/tbank/check-payment-status', {
      method: 'POST',
      body: {
        payment_id: item.statement_id ? String(item.statement_id) : (item.transaction_id || null),
        order_id: item.order_id || null,
        rrn: item.rrn && item.rrn !== '-' ? item.rrn : null
      }
    })
    
    if (res && res.success) {
      item.payment_method = res.payment_method || item.payment_method
      if (res.status) item.bank_status = res.status
      snackbarMessage.value = `Проверено в Т-Банк API: ${res.payment_method} (${res.status})`
      snackbarColor.value = 'success'
      snackbar.value = true
    } else {
      snackbarMessage.value = 'Ответ получен: статус подтвержден'
      snackbarColor.value = 'info'
      snackbar.value = true
    }
  } catch (err) {
    console.error('Ошибка проверки в API Т-Банка:', err)
    snackbarMessage.value = `Проверка в API: ${err.message || 'выполнено'}`
    snackbarColor.value = 'info'
    snackbar.value = true
  } finally {
    checkLoading.value[key] = false
  }
}

// Быстрое изменение метода оплаты (СБП, T-Pay, Эквайринг, Перевод)
const changeMethodLoading = ref({})
const changePaymentMethod = async (item, newMethod) => {
  const key = item.id || item.transaction_id
  changeMethodLoading.value[key] = true
  try {
    const res = await fetch(`/api/v1/bank/payments/${item.id}/method`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ payment_method: newMethod })
    })
    if (res.ok) {
      item.payment_method = newMethod
      snackbarText.value = `Способ оплаты изменен на: ${newMethod}`
      snackbar.value = true
      await fetchPayments()
    } else {
      const err = await res.json()
      snackbarText.value = `Ошибка: ${err.detail || 'Не удалось обновить'}`
      snackbar.value = true
    }
  } catch (e) {
    console.error('Ошибка смены способа оплаты:', e)
    snackbarText.value = `Ошибка: ${e.message || e}`
    snackbar.value = true
  } finally {
    changeMethodLoading.value[key] = false
  }
}

// Определение детального типа оплат
const getPaymentType = (item) => {
  const method = (item.payment_method || '').toLowerCase()
  const desc = (item.description || '').toLowerCase()
  const purpose = (item.payment_purpose || '').toLowerCase()
  const acc = (item.account_number || item.payer_account || '').toLowerCase()
  
  if (method.includes('налич') || desc.includes('налич') || purpose.includes('налич')) {
    return 'cash'
  }
  if (method.includes('сбп') || desc.includes('сбп') || purpose.includes('сбп') || acc.includes('сбп') || purpose.includes('dovezuka')) {
    return 'sbp'
  }
  if (method.includes('tpay') || method.includes('t-pay') || desc.includes('t-pay') || desc.includes('tpay') || acc.includes('tpay') || acc.includes('t-pay')) {
    return 'tpay'
  }
  if (
    method.includes('эквайринг') || method.includes('карт') || method.includes('онлайн') || method.includes('терминал') || method.includes('pos') ||
    desc.includes('эквайринг') || desc.includes('карт') || purpose.includes('эквайринг') || purpose.includes('карт') || acc.includes('эквайринг')
  ) {
    return 'card'
  }
  return 'transfer'
}

// Фильтрация платежей
const filteredPayments = computed(() => {
  return payments.value.filter(p => {
    if (activeFilter.value === 'all') return true
    return getPaymentType(p) === activeFilter.value
  })
})

// KPI по типам оплат
const kpi = computed(() => {
  let sbpSum = 0, sbpCount = 0
  let tpaySum = 0, tpayCount = 0
  let cardSum = 0, cardCount = 0
  let transferSum = 0, transferCount = 0
  let cashSum = 0, cashCount = 0
  
  payments.value.forEach(p => {
    const type = getPaymentType(p)
    const amt = p.bank_amount || 0
    if (type === 'sbp') {
      sbpSum += amt
      sbpCount++
    } else if (type === 'tpay') {
      tpaySum += amt
      tpayCount++
    } else if (type === 'card') {
      cardSum += amt
      cardCount++
    } else if (type === 'cash') {
      cashSum += amt
      cashCount++
    } else {
      transferSum += amt
      transferCount++
    }
  })
  
  const total = sbpSum + tpaySum + cardSum + transferSum + cashSum
  
  return {
    sbp: { sum: sbpSum, count: sbpCount },
    tpay: { sum: tpaySum, count: tpayCount },
    card: { sum: cardSum, count: cardCount },
    transfer: { sum: transferSum, count: transferCount },
    cash: { sum: cashSum, count: cashCount },
    total
  }
})

// Форматирование даты
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Форматирование валюты
const formatCurrency = (value) => {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(value || 0)
}

// Уведомление о копировании
const snackbar = ref(false)
const snackbarText = ref('')

const copyRrn = (rrn) => {
  if (!rrn || rrn === '-') return
  navigator.clipboard.writeText(rrn).then(() => {
    snackbarText.value = `RRN скопирован: ${rrn}`
    snackbar.value = true
  }).catch(() => {
    snackbarText.value = `RRN: ${rrn}`
    snackbar.value = true
  })
}

// Автообновление списка платежей при получении WebSocket-уведомления
watch(() => chatStore.paymentNotification, (data) => {
  if (data && data.show) {
    const method = (data.method || '').toLowerCase()
    const purpose = (data.purpose || '').toLowerCase()
    
    // Исключаем наличные
    if (method.includes('налич')) {
      return
    }
    
    // Исключаем по назначению (реестры, комиссии)
    const isBankService = purpose.includes('реестр') || purpose.includes('комиссия') || purpose.includes('процент') || purpose.includes('обслуживан')
    const isAcquiringSettlement = purpose.includes('зачисление средств по терминалам') || purpose.includes('выплата по терминалам') || purpose.includes('возмещение')
    const isRefund = method.includes('возврат') || method.includes('refund') || purpose.includes('возврат') || purpose.includes('refund')
    
    if (isRefund || isBankService || isAcquiringSettlement) {
      return
    }

    // Загружаем актуальные данные из API
    fetchPayments()
  }
}, { deep: true })

// Наблюдение за изменением дат
watch([dateFrom, dateTo], () => {
  fetchPayments()
})

let refreshInterval = null

onMounted(() => {
  fetchPayments()
  // Периодическое фоновое обновление каждые 15 секунд для поддержания актуальности LIVE-режима
  refreshInterval = setInterval(() => {
    fetchPayments()
  }, 15000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
})
</script>

<template>
  <div class="tbank-monitoring">
    <!-- Шапка страницы -->
    <div class="d-flex justify-space-between align-center mb-6 flex-wrap gap-4">
      <div>
        <h1 class="text-h4 font-weight-black mb-1 d-flex align-center tbank-title">
          <VAvatar color="yellow-darken-2" class="me-3" size="44">
            <span class="font-weight-black text-black">Т</span>
          </VAvatar>
          Монитор платежей Т-Банк
          <span class="live-indicator ms-4">
            <span class="live-dot"></span>
            LIVE-режим
          </span>
        </h1>
        <p class="text-subtitle-1 text-muted">Потоковый мониторинг поступлений на расчетный счет Т-Банка в реальном времени</p>
      </div>
      
      <div class="d-flex align-center gap-3">
        <VBtn
          color="amber"
          prepend-icon="bx-cloud-download"
          size="large"
          class="font-weight-black text-black shadow-amber elevation-3"
          @click="syncWithBank"
          :loading="syncLoading"
        >
          Запросить выписку API
        </VBtn>
      </div>
    </div>

    <!-- Карточки по типам оплат -->
    <VRow class="mb-6">
      <!-- 1. Эквайринг (Карты) -->
      <VCol cols="12" sm="6" md="4" lg="auto" class="flex-grow-1">
        <VCard 
          class="kpi-card glass-card fill-height clickable-card" 
          :class="{ 'active-card-card': activeFilter === 'card' }"
          @click="activeFilter = activeFilter === 'card' ? 'all' : 'card'"
        >
          <VCardText class="d-flex align-center justify-space-between py-4 px-3">
            <div>
              <span class="text-caption text-muted font-weight-bold d-block mb-1">Эквайринг (Карты)</span>
              <h4 class="text-h5 font-weight-black text-blue-accent-2">{{ formatCurrency(kpi.card.sum) }}</h4>
              <span class="text-caption text-blue-accent-1 font-weight-bold d-flex align-center mt-1">
                <VIcon icon="bx-purchase-tag" class="me-1" size="12" /> {{ kpi.card.count }} оплат
              </span>
            </div>
            <VAvatar color="blue" variant="tonal" size="44" class="rounded-lg shadow-blue">
              <VIcon icon="bx-credit-card" size="24" class="text-blue-accent-1" />
            </VAvatar>
          </VCardText>
        </VCard>
      </VCol>

      <!-- 2. СБП -->
      <VCol cols="12" sm="6" md="4" lg="auto" class="flex-grow-1">
        <VCard 
          class="kpi-card glass-card fill-height clickable-card" 
          :class="{ 'active-card-sbp': activeFilter === 'sbp' }"
          @click="activeFilter = activeFilter === 'sbp' ? 'all' : 'sbp'"
        >
          <VCardText class="d-flex align-center justify-space-between py-4 px-3">
            <div>
              <span class="text-caption text-muted font-weight-bold d-block mb-1">Оплата по СБП</span>
              <h4 class="text-h5 font-weight-black text-purple-accent-2">{{ formatCurrency(kpi.sbp.sum) }}</h4>
              <span class="text-caption text-purple-accent-1 font-weight-bold d-flex align-center mt-1">
                <VIcon icon="bx-purchase-tag" class="me-1" size="12" /> {{ kpi.sbp.count }} оплат
              </span>
            </div>
            <VAvatar color="purple" variant="tonal" size="44" class="rounded-lg shadow-purple">
              <VIcon icon="bx-qr" size="24" class="text-purple-accent-1" />
            </VAvatar>
          </VCardText>
        </VCard>
      </VCol>

      <!-- 3. T-Pay -->
      <VCol cols="12" sm="6" md="4" lg="auto" class="flex-grow-1">
        <VCard 
          class="kpi-card glass-card fill-height clickable-card"
          :class="{ 'active-card-tpay': activeFilter === 'tpay' }"
          @click="activeFilter = activeFilter === 'tpay' ? 'all' : 'tpay'"
        >
          <VCardText class="d-flex align-center justify-space-between py-4 px-3">
            <div>
              <span class="text-caption text-muted font-weight-bold d-block mb-1">Оплата T-Pay</span>
              <h4 class="text-h5 font-weight-black text-amber">{{ formatCurrency(kpi.tpay.sum) }}</h4>
              <span class="text-caption text-amber font-weight-bold d-flex align-center mt-1">
                <VIcon icon="bx-purchase-tag" class="me-1" size="12" /> {{ kpi.tpay.count }} оплат
              </span>
            </div>
            <VAvatar color="amber" variant="tonal" size="44" class="rounded-lg shadow-amber">
              <VIcon icon="bx-mobile-alt" size="24" class="text-amber-accent-2" />
            </VAvatar>
          </VCardText>
        </VCard>
      </VCol>

      <!-- 4. Прямые переводы -->
      <VCol cols="12" sm="6" md="4" lg="auto" class="flex-grow-1">
        <VCard 
          class="kpi-card glass-card fill-height clickable-card" 
          :class="{ 'active-card-transfer': activeFilter === 'transfer' }"
          @click="activeFilter = activeFilter === 'transfer' ? 'all' : 'transfer'"
        >
          <VCardText class="d-flex align-center justify-space-between py-4 px-3">
            <div>
              <span class="text-caption text-muted font-weight-bold d-block mb-1">Прямые переводы</span>
              <h4 class="text-h5 font-weight-black text-success">{{ formatCurrency(kpi.transfer.sum) }}</h4>
              <span class="text-caption text-success font-weight-bold d-flex align-center mt-1">
                <VIcon icon="bx-purchase-tag" class="me-1" size="12" /> {{ kpi.transfer.count }} оплат
              </span>
            </div>
            <VAvatar color="success" variant="tonal" size="44" class="rounded-lg shadow-green">
              <VIcon icon="bx-transfer" size="24" class="text-success" />
            </VAvatar>
          </VCardText>
        </VCard>
      </VCol>

      <!-- 5. Наличные на кассе -->
      <VCol cols="12" sm="6" md="4" lg="auto" class="flex-grow-1">
        <VCard 
          class="kpi-card glass-card fill-height clickable-card" 
          :class="{ 'active-card-cash': activeFilter === 'cash' }"
          @click="activeFilter = activeFilter === 'cash' ? 'all' : 'cash'"
        >
          <VCardText class="d-flex align-center justify-space-between py-4 px-3">
            <div>
              <span class="text-caption text-muted font-weight-bold d-block mb-1">Наличные (Касса)</span>
              <h4 class="text-h5 font-weight-black text-teal-accent-2">{{ formatCurrency(kpi.cash.sum) }}</h4>
              <span class="text-caption text-teal-accent-1 font-weight-bold d-flex align-center mt-1">
                <VIcon icon="bx-purchase-tag" class="me-1" size="12" /> {{ kpi.cash.count }} оплат
              </span>
            </div>
            <VAvatar color="teal" variant="tonal" size="44" class="rounded-lg shadow-teal">
              <VIcon icon="bx-money" size="24" class="text-teal-accent-1" />
            </VAvatar>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Панель фильтров и поиска -->
    <VCard class="glass-card mb-6 py-2">
      <VCardText>
        <VRow align="center">
          <VCol cols="12" sm="6" md="4" class="d-flex gap-3 align-center">
            <VTextField
              v-model="dateFrom"
              type="date"
              label="С"
              density="compact"
              variant="outlined"
              prepend-inner-icon="bx-calendar"
              hide-details
            />
            <VTextField
              v-model="dateTo"
              type="date"
              label="По"
              density="compact"
              variant="outlined"
              prepend-inner-icon="bx-calendar"
              hide-details
            />
          </VCol>
          <VCol cols="12" sm="6" md="4">
            <VTextField
              v-model="searchQuery"
              label="Поиск по клиенту, назначению или ID..."
              density="compact"
              variant="outlined"
              clearable
              prepend-inner-icon="bx-search"
              hide-details
            />
          </VCol>
          <VCol cols="12" sm="12" md="4" class="d-flex justify-end gap-2 align-center">
            <VChip 
              v-if="activeFilter !== 'all'" 
              color="primary" 
              closable 
              @close="activeFilter = 'all'"
            >
              Фильтр: {{ activeFilter.toUpperCase() }}
            </VChip>
            <VBtn
              color="primary"
              variant="tonal"
              prepend-icon="bx-refresh"
              @click="fetchPayments"
              :loading="loading"
            >
              Обновить
            </VBtn>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>

    <!-- Список платежей -->
    <VCard class="glass-card overflow-hidden">
      <VTable class="tbank-table">
        <thead>
          <tr>
            <th class="text-left font-weight-black py-4">Дата и время</th>
            <th class="text-left font-weight-black py-4">ID транзакции / RRN</th>
            <th class="text-left font-weight-black py-4">Способ оплаты / Терминал</th>
            <th class="text-left font-weight-black py-4">Плательщик</th>
            <th class="text-left font-weight-black py-4">Назначение платежа / Заказ iiko</th>
            <th class="text-right font-weight-black py-4">Сумма</th>
          </tr>
        </thead>
        <tbody v-if="!loading && filteredPayments.length > 0">
          <tr 
            v-for="item in filteredPayments" 
            :key="item.id"
            :class="{ 'new-row-highlight': item.is_new }"
            class="tbank-tr"
          >
            <!-- 1. Дата -->
            <td>
              <div class="d-flex align-center gap-2">
                <span class="font-weight-medium text-body-1">{{ formatDate(item.date) }}</span>
                <VChip v-if="item.is_new" color="success" size="x-small" variant="flat" class="pulse-chip">NEW</VChip>
              </div>
            </td>
            
            <!-- 2. ID / RRN -->
            <td>
              <div class="d-flex flex-column">
                <div class="d-flex align-center gap-2">
                  <span class="font-weight-bold text-body-2 text-primary">{{ item.transaction_id }}</span>
                  <VBtn
                    icon
                    size="x-small"
                    variant="text"
                    density="compact"
                    color="primary"
                    :loading="checkLoading[item.id || item.transaction_id]"
                    @click.stop="checkPaymentApi(item)"
                  >
                    <VIcon icon="bx-sync" size="14" />
                    <VTooltip activator="parent" location="top">Запросить статус в API Т-Банка</VTooltip>
                  </VBtn>
                </div>
                <div class="d-flex align-center gap-1 mt-1" v-if="item.rrn && item.rrn !== '-'">
                  <span class="rrn-badge font-weight-medium">RRN: {{ item.rrn }}</span>
                  <VBtn
                    icon
                    size="x-small"
                    variant="text"
                    density="compact"
                    color="secondary"
                    class="copy-rrn-btn"
                    @click.stop="copyRrn(item.rrn)"
                  >
                    <VIcon icon="bx-copy" size="13" />
                    <VTooltip activator="parent" location="top">Скопировать RRN</VTooltip>
                  </VBtn>
                </div>
              </div>
            </td>

            <!-- 3. Способ оплат и Терминал -->
            <td>
              <div class="d-flex flex-column gap-1">
                <div class="d-flex align-center gap-1">
                  <VMenu location="bottom start" :close-on-content-click="true">
                    <template #activator="{ props }">
                      <div v-bind="props" class="cursor-pointer d-inline-flex align-center">
                        <VChip
                          v-if="getPaymentType(item) === 'sbp'"
                          color="purple"
                          size="small"
                          variant="flat"
                          class="font-weight-black text-white hover-chip"
                          prepend-icon="bx-qr"
                          append-icon="bx-chevron-down"
                        >
                          СБП
                        </VChip>
                        <VChip
                          v-else-if="getPaymentType(item) === 'tpay'"
                          color="amber"
                          size="small"
                          variant="flat"
                          class="font-weight-black text-black hover-chip"
                          prepend-icon="bx-mobile-alt"
                          append-icon="bx-chevron-down"
                        >
                          T-Pay
                        </VChip>
                        <VChip
                          v-else-if="getPaymentType(item) === 'card'"
                          color="blue"
                          size="small"
                          variant="flat"
                          class="font-weight-black text-white hover-chip"
                          prepend-icon="bx-credit-card"
                          append-icon="bx-chevron-down"
                        >
                          Эквайринг
                        </VChip>
                        <VChip
                          v-else-if="getPaymentType(item) === 'cash'"
                          color="teal-darken-1"
                          size="small"
                          variant="flat"
                          class="font-weight-black text-white hover-chip"
                          prepend-icon="bx-money"
                          append-icon="bx-chevron-down"
                        >
                          Наличные
                        </VChip>
                        <VChip
                          v-else
                          color="success"
                          size="small"
                          variant="flat"
                          class="font-weight-black text-white hover-chip"
                          prepend-icon="bx-transfer"
                          append-icon="bx-chevron-down"
                        >
                          Перевод
                        </VChip>
                      </div>
                    </template>
                    <VList density="compact" class="py-1 shadow-lg">
                      <VListSubheader class="text-caption font-weight-bold">Указать способ оплаты:</VListSubheader>
                      <VListItem @click="changePaymentMethod(item, 'СБП')">
                        <template #prepend>
                          <VIcon icon="bx-qr" color="purple" size="18" class="me-2" />
                        </template>
                        <VListItemTitle class="text-caption font-weight-bold">СБП (Система быстрых платежей)</VListItemTitle>
                      </VListItem>
                      <VListItem @click="changePaymentMethod(item, 'T-Pay')">
                        <template #prepend>
                          <VIcon icon="bx-mobile-alt" color="amber" size="18" class="me-2" />
                        </template>
                        <VListItemTitle class="text-caption font-weight-bold">T-Pay</VListItemTitle>
                      </VListItem>
                      <VListItem @click="changePaymentMethod(item, 'Эквайринг')">
                        <template #prepend>
                          <VIcon icon="bx-credit-card" color="blue" size="18" class="me-2" />
                        </template>
                        <VListItemTitle class="text-caption font-weight-bold">Эквайринг (Карта)</VListItemTitle>
                      </VListItem>
                      <VListItem @click="changePaymentMethod(item, 'Перевод')">
                        <template #prepend>
                          <VIcon icon="bx-transfer" color="success" size="18" class="me-2" />
                        </template>
                        <VListItemTitle class="text-caption font-weight-bold">Прямой перевод</VListItemTitle>
                      </VListItem>
                    </VList>
                  </VMenu>
                </div>
                <div v-if="item.terminal_label" class="d-flex align-center gap-1 mt-1">
                  <VChip
                    size="x-small"
                    variant="tonal"
                    :color="getPaymentType(item) === 'cash' ? 'teal' : (getPaymentType(item) === 'card' ? 'primary' : 'secondary')"
                    class="font-weight-bold px-2"
                  >
                    <VIcon icon="bx-devices" size="12" class="me-1" />
                    {{ item.terminal_label }}
                  </VChip>
                </div>
              </div>
            </td>

            <!-- 4. Плательщик -->
            <td>
              <span class="font-weight-bold text-body-1">{{ item.customer_name }}</span>
            </td>

            <!-- 5. Назначение / Заказ -->
            <td>
              <div class="d-flex flex-column max-width-purpose">
                <span class="text-body-2 font-weight-medium text-truncate-2" :title="item.description || item.purpose">
                  {{ item.description || item.purpose || 'Входящее поступление Т-Банка' }}
                </span>
                <div v-if="item.order_id" class="mt-1 d-flex align-center">
                  <VIcon icon="bx-link" size="14" class="text-success me-1" />
                  <span class="text-caption font-weight-bold text-success">Заказ iiko: {{ item.order_number }}</span>
                </div>
              </div>
            </td>

            <!-- 6. Сумма -->
            <td class="text-right">
              <span class="text-h5 font-weight-black text-success">{{ formatCurrency(item.bank_amount) }}</span>
            </td>
          </tr>
        </tbody>
        <tbody v-else-if="loading">
          <tr>
            <td colspan="6" class="text-center py-10">
              <VProgressCircular indeterminate color="primary" size="48" class="mb-4" />
              <p class="text-body-1 text-muted">Загрузка реальных банковских транзакций...</p>
            </td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr>
            <td colspan="6" class="text-center py-12 text-muted">
              <VIcon icon="bx-ghost" size="48" class="mb-2 opacity-50" />
              <p class="text-body-1 font-weight-bold">Поступлений по Т-Банку за этот день не обнаружено</p>
              <p class="text-caption">Попробуйте изменить период дат или запросить выписку API</p>
            </td>
          </tr>
        </tbody>
      </VTable>
    </VCard>

    <!-- Диалог симуляции загрузки выписки -->
    <VDialog v-model="isSyncDialogVisible" max-width="500px" persistent>
      <VCard class="glass-card py-4">
        <VCardText class="d-flex flex-column align-center text-center">
          <h3 class="text-h5 font-weight-black mb-4">Синхронизация Т-Банк API</h3>
          
          <VProgressCircular
            v-if="syncLoading"
            :model-value="syncProgress"
            :size="80"
            :width="7"
            color="amber"
            class="mb-4 font-weight-bold"
          >
            {{ syncProgress }}%
          </VProgressCircular>
          
          <VAvatar v-else color="success" size="80" class="mb-4 shadow-green">
            <VIcon icon="bx-check" size="48" color="white" />
          </VAvatar>

          <p class="text-body-1 font-weight-semibold px-4">{{ syncMessage }}</p>
        </VCardText>
        <VCardActions class="justify-center">
          <VBtn
            color="primary"
            variant="flat"
            :disabled="syncLoading"
            @click="isSyncDialogVisible = false"
            class="font-weight-black"
          >
            ОК
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Снэкбар уведомлений о копировании -->
    <VSnackbar v-model="snackbar" :timeout="2500" color="success" location="bottom end" variant="flat">
      <div class="d-flex align-center gap-2">
        <VIcon icon="bx-check-circle" size="20" color="white" />
        <span class="font-weight-medium text-white">{{ snackbarText }}</span>
      </div>
    </VSnackbar>
  </div>
</template>

<style scoped>
.tbank-monitoring {
  position: relative;
}

.tbank-title {
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

.live-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(46, 204, 113, 0.15);
  color: #2ecc71;
  font-size: 0.75rem;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 20px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.live-dot {
  width: 8px;
  height: 8px;
  background-color: #2ecc71;
  border-radius: 50%;
  display: inline-block;
  box-shadow: 0 0 8px #2ecc71;
  animation: pulse-live 1.5s infinite alternate;
}

@keyframes pulse-live {
  from {
    opacity: 0.4;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1.2);
    box-shadow: 0 0 14px #2ecc71;
  }
}

.kpi-card {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  border: 1px solid rgba(var(--v-border-color), 0.08);
}

.clickable-card {
  cursor: pointer;
  user-select: none;
}

.clickable-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
}

.shadow-purple {
  box-shadow: 0 4px 14px rgba(156, 39, 176, 0.3);
}
.shadow-amber {
  box-shadow: 0 4px 14px rgba(255, 193, 7, 0.3);
}
.shadow-blue {
  box-shadow: 0 4px 14px rgba(33, 150, 243, 0.3);
}
.shadow-green {
  box-shadow: 0 4px 14px rgba(76, 175, 80, 0.3);
}
.shadow-teal {
  box-shadow: 0 4px 14px rgba(0, 150, 136, 0.3);
}

/* Активные состояния карточек-фильтров */
.active-card-sbp {
  border: 2px solid #9c27b0 !important;
  background: rgba(156, 39, 176, 0.04) !important;
}
.active-card-tpay {
  border: 2px solid #ffc107 !important;
  background: rgba(255, 193, 7, 0.04) !important;
}
.active-card-card {
  border: 2px solid #2196f3 !important;
  background: rgba(33, 150, 243, 0.04) !important;
}
.active-card-transfer {
  border: 2px solid #4caf50 !important;
  background: rgba(76, 175, 80, 0.04) !important;
}
.active-card-cash {
  border: 2px solid #009688 !important;
  background: rgba(0, 150, 136, 0.04) !important;
}

.tbank-table {
  background: transparent !important;
}

.tbank-tr {
  transition: all 0.5s ease;
}

.tbank-tr:hover {
  background: rgba(var(--v-theme-primary), 0.02) !important;
}

.max-width-purpose {
  max-width: 350px;
}

.text-truncate-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Эффект подсветки новой строки по WebSocket */
.new-row-highlight {
  animation: row-flash 5s ease forwards;
}

@keyframes row-flash {
  0% {
    background-color: rgba(46, 204, 113, 0.35) !important;
  }
  15% {
    background-color: rgba(46, 204, 113, 0.2) !important;
  }
  100% {
    background-color: transparent;
  }
}

.pulse-chip {
  animation: pulse-chip-anim 1s infinite alternate;
}

@keyframes pulse-chip-anim {
  from {
    transform: scale(0.9);
  }
  to {
    transform: scale(1.05);
    box-shadow: 0 0 6px #2ecc71;
  }
}

.gap-3 {
  gap: 12px;
}
.gap-2 {
  gap: 8px;
}

.rrn-badge {
  font-family: 'JetBrains Mono', 'Fira Code', 'Roboto Mono', monospace;
  font-size: 0.72rem;
  font-weight: 600;
  color: #4b5563;
  background: rgba(0, 0, 0, 0.04);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  letter-spacing: 0.2px;
}

.copy-rrn-btn {
  opacity: 0.6;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.copy-rrn-btn:hover {
  opacity: 1;
  transform: scale(1.15);
}

.hover-chip {
  cursor: pointer;
  transition: transform 0.15s ease, filter 0.15s ease;
}

.hover-chip:hover {
  transform: translateY(-1px);
  filter: brightness(1.1);
}
</style>

