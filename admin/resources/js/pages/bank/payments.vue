<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { getAuthHeaders } from '@/utils/auth'
import { useChatStore } from '@/stores/chatStore'

// Состояние
const chatStore = useChatStore()
const payments = ref([])
const loading = ref(true)
const syncLoading = ref(false)
const syncProgress = ref(0)
const syncMessage = ref('')
const isSyncDialogVisible = ref(false)
const selectedPayment = ref(null)
const isDetailsDialogVisible = ref(false)
const activeTab = ref('all') // 'all', 'sbp_tpay', 'card', 'transfer', 'attention'
const autoMatchLoading = ref(false)

// Диалог ручной привязки к заказу
const isMatchDialogVisible = ref(false)
const matchTargetPayment = ref(null)
const matchSearchQuery = ref('')
const matchingOrders = ref([])
const matchOrdersLoading = ref(false)
const matchActionLoading = ref(false)

// Уведомления (Snackbar)
const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

const showMessage = (text, color = 'success') => {
  snackbar.value.text = text
  snackbar.value.color = color
  snackbar.value.show = true
}

// Фильтры дат по умолчанию: последние 30 дней для удобного обзора
const getLocalDateStr = (daysOffset = 0) => {
  const d = new Date()
  d.setDate(d.getDate() - daysOffset)
  const offset = d.getTimezoneOffset()
  const localDate = new Date(d.getTime() - (offset * 60 * 1000))
  return localDate.toISOString().split('T')[0]
}

const dateFrom = ref(getLocalDateStr(30))
const dateTo = ref(getLocalDateStr(0))
const activeDatePreset = ref('30days')
const statusFilter = ref('all')
const searchQuery = ref('')

// Пресеты дат
const setDatePreset = (preset) => {
  activeDatePreset.value = preset
  if (preset === 'today') {
    dateFrom.value = getLocalDateStr(0)
    dateTo.value = getLocalDateStr(0)
  } else if (preset === 'yesterday') {
    dateFrom.value = getLocalDateStr(1)
    dateTo.value = getLocalDateStr(1)
  } else if (preset === '7days') {
    dateFrom.value = getLocalDateStr(7)
    dateTo.value = getLocalDateStr(0)
  } else if (preset === '30days') {
    dateFrom.value = getLocalDateStr(30)
    dateTo.value = getLocalDateStr(0)
  } else if (preset === 'all') {
    dateFrom.value = null
    dateTo.value = null
  }
}

// Варианты статусов сверки
const statusOptions = [
  { title: 'Все статусы', value: 'all' },
  { title: 'Сверено с iiko', value: 'matched' },
  { title: 'Несовпадение сумм', value: 'discrepancy' },
  { title: 'Платеж без заказа (Банк)', value: 'unmatched_bank' },
  { title: 'Заказ без оплаты (iiko)', value: 'unmatched_order' }
]

// Заголовки таблицы
const headers = [
  { title: 'Дата и время', key: 'date', sortable: true, width: '150px' },
  { title: 'Транзакция (ID / RRN)', key: 'txn_details', width: '160px' },
  { title: 'Клиент / Заказ', key: 'customer_name', minWidth: '180px' },
  { title: 'Способ оплаты', key: 'payment_method', width: '170px' },
  { title: 'Сумма (Банк)', key: 'bank_amount', align: 'end', sortable: true, width: '130px' },
  { title: 'Сумма (iiko)', key: 'order_amount', align: 'end', sortable: true, width: '130px' },
  { title: 'Разница', key: 'difference', align: 'end', width: '110px' },
  { title: 'Статус сверки', key: 'status', align: 'center', width: '140px' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'center', width: '100px' }
]

// Получение платежей из API
const fetchPayments = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (dateFrom.value) params.append('date_from', dateFrom.value)
    if (dateTo.value) params.append('date_to', dateTo.value)
    if (statusFilter.value && statusFilter.value !== 'all') params.append('status', statusFilter.value)
    if (searchQuery.value) params.append('search', searchQuery.value)

    const response = await fetch(`/api/v1/bank/payments?${params.toString()}`, {
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      payments.value = await response.json()
    } else {
      console.error('Ошибка при получении платежей:', response.statusText)
      showMessage('Не удалось загрузить платежи', 'error')
    }
  } catch (error) {
    console.error('Сбой сети при запросе платежей:', error)
    showMessage('Сбой сети при получении платежей', 'error')
  } finally {
    loading.value = false
  }
}

// Форматирование даты
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Форматирование валюты
const formatCurrency = (value) => {
  if (value === undefined || value === null) return '0.00 ₽'
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(value)
}

// Расчет разницы
const getDifference = (item) => {
  return (item.bank_amount || 0) - (item.order_amount || 0)
}

// Определение категории метода для табов
const getPaymentCategory = (item) => {
  const method = (item.payment_method || '').toLowerCase()
  const desc = (item.description || '').toLowerCase()
  const purp = (item.payment_purpose || '').toLowerCase()
  
  if (method.includes('сбп') || desc.includes('сбп') || purp.includes('сбп') || method.includes('qr') || purp.includes('qr') || method.includes('t-pay') || method.includes('tpay')) {
    return 'sbp_tpay'
  }
  if (method.includes('карт') || method.includes('эквайринг') || desc.includes('эквайринг') || purp.includes('эквайринг') || purp.includes('терминал')) {
    return 'card'
  }
  return 'transfer'
}

// Фильтрация платежей по вкладкам
const filteredPayments = computed(() => {
  if (activeTab.value === 'all') {
    return payments.value
  }
  if (activeTab.value === 'sbp_tpay') {
    return payments.value.filter(p => getPaymentCategory(p) === 'sbp_tpay')
  }
  if (activeTab.value === 'card') {
    return payments.value.filter(p => getPaymentCategory(p) === 'card')
  }
  if (activeTab.value === 'transfer') {
    return payments.value.filter(p => getPaymentCategory(p) === 'transfer')
  }
  if (activeTab.value === 'attention') {
    return payments.value.filter(p => p.status === 'discrepancy' || p.status === 'unmatched_bank' || p.status === 'unmatched_order')
  }
  return payments.value
})

// KPI статистика
const kpi = computed(() => {
  let totalBankSum = 0
  let matchedCount = 0
  let discrepancyCount = 0
  let unmatchedCount = 0
  let unpaidCount = 0
  
  filteredPayments.value.forEach(p => {
    // В сумму банка считаем все фактически подтвержденные суммы
    if (p.is_real && p.bank_amount > 0) {
      totalBankSum += p.bank_amount
    }
    if (p.status === 'matched') matchedCount++
    else if (p.status === 'discrepancy') discrepancyCount++
    else if (p.status === 'unmatched_bank') unmatchedCount++
    else if (p.status === 'unmatched_order') unpaidCount++
  })

  return {
    totalSum: totalBankSum,
    matched: matchedCount,
    discrepancy: discrepancyCount,
    unmatched: unmatchedCount,
    unpaid: unpaidCount,
    totalCount: filteredPayments.value.length
  }
})

// Наблюдение за фильтрами
watch([dateFrom, dateTo, statusFilter], () => {
  fetchPayments()
})

// Поиск с дебаунсом (задержка 400мс)
let searchTimeout
watch(searchQuery, () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchPayments()
  }, 400)
})

// Сброс всех фильтров
const resetFilters = () => {
  dateFrom.value = null
  dateTo.value = null
  activeDatePreset.value = 'all'
  statusFilter.value = 'all'
  searchQuery.value = ''
  activeTab.value = 'all'
}

// Загрузка реальной выписки напрямую из Т-Банка
const startSyncSimulation = async () => {
  isSyncDialogVisible.value = true
  syncLoading.value = true
  syncProgress.value = 0
  syncMessage.value = 'Соединение с сервером Т-Банк API...'
  
  try {
    // 1. Получаем список расчетных счетов
    const accountsResponse = await fetch('/api/v1/settings/tbank/accounts', {
      headers: getAuthHeaders()
    })
    
    if (!accountsResponse.ok) {
      throw new Error(`Не удалось получить счета: ${accountsResponse.statusText}`)
    }
    
    const accounts = await accountsResponse.json()
    if (!accounts || accounts.length === 0) {
      throw new Error('В настройках Т-Банка не найдено активных расчетных счетов. Пожалуйста, укажите токен в настройках Т-Банка.')
    }
    
    const accountNumber = accounts[0].accountNumber
    syncProgress.value = 30
    syncMessage.value = `Счет ${accountNumber} определен. Запуск выгрузки операций...`
    
    // Форматируем даты для API (YYYY-MM-DD)
    const today = new Date().toISOString().split('T')[0]
    const defaultFrom = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    
    const fromDate = dateFrom.value || defaultFrom
    const tillDate = dateTo.value || today
    
    syncProgress.value = 60
    syncMessage.value = `Загрузка проводок за период с ${fromDate} по ${tillDate}...`
    
    // 2. Отправляем запрос на синхронизацию выписки
    const syncResponse = await fetch('/api/v1/settings/tbank/sync-statement', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        account_number: accountNumber,
        from_date: fromDate,
        till_date: tillDate
      })
    })
    
    if (!syncResponse.ok) {
      throw new Error(`Ошибка сверки выписки на сервере: ${syncResponse.statusText}`)
    }
    
    const result = await syncResponse.json()
    syncProgress.value = 100
    
    if (result.success) {
      syncMessage.value = `Синхронизация с банком завершена! Обработано транзакций: ${result.processed_operations}, добавлено новых: ${result.new_operations_added}, автоматически сопоставлено с заказами: ${result.orders_automatically_matched}.`
      showMessage('Выписка Т-Банка успешно загружена и сведена!')
    } else {
      syncMessage.value = 'Сервер вернул ошибку при сверке выписки.'
    }
    
    // Перезагружаем список
    await fetchPayments()
  } catch (error) {
    console.error('Ошибка синхронизации выписки Т-Банка:', error)
    syncProgress.value = 100
    syncMessage.value = `Ошибка сверки: ${error.message || error}`
    showMessage(`Ошибка: ${error.message || error}`, 'error')
  } finally {
    syncLoading.value = false
  }
}

// Открытие деталей платежа
const openDetails = (payment) => {
  selectedPayment.value = payment
  isDetailsDialogVisible.value = true
}

// Автообновление списка платежей при получении уведомления по WebSocket
watch(() => chatStore.paymentNotification, (data) => {
  if (data && data.show) {
    fetchPayments()
  }
}, { deep: true })

// Метод запуска авто-связки по терминалам и суммам
const runAutoMatch = async () => {
  autoMatchLoading.value = true
  try {
    const response = await fetch('/api/v1/bank/auto-match', {
      method: 'POST',
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        showMessage(`Авто-связка завершена! Сверено платежей: ${result.matched_count} из ${result.checked_unmatched} несвязанных.`, 'success')
        await fetchPayments()
      } else {
        showMessage('Произошла ошибка при выполнении авто-связки.', 'error')
      }
    } else {
      showMessage('Не удалось выполнить авто-связку на сервере', 'error')
    }
  } catch (error) {
    console.error('Ошибка при запуске авто-связки:', error)
    showMessage('Сбой сети при запуске авто-связки', 'error')
  } finally {
    autoMatchLoading.value = false
  }
}

// Диалог ручной привязки к заказу
const openManualMatchDialog = (payment) => {
  matchTargetPayment.value = payment
  matchSearchQuery.value = ''
  isDetailsDialogVisible.value = false
  isMatchDialogVisible.value = true
  searchOrdersForMatch()
}

// Поиск заказов для ручной привязки
const searchOrdersForMatch = async () => {
  matchOrdersLoading.value = true
  try {
    const params = new URLSearchParams()
    if (matchSearchQuery.value) {
      params.append('query', matchSearchQuery.value)
    } else if (matchTargetPayment.value?.bank_amount) {
      params.append('amount', matchTargetPayment.value.bank_amount)
    }
    
    const res = await fetch(`/api/v1/bank/search-orders-for-match?${params.toString()}`, {
      headers: getAuthHeaders()
    })
    if (res.ok) {
      matchingOrders.value = await res.json()
    } else {
      matchingOrders.value = []
    }
  } catch (e) {
    console.error('Ошибка поиска заказов:', e)
    matchingOrders.value = []
  } finally {
    matchOrdersLoading.value = false
  }
}

// Выполнение ручной привязки
const executeManualMatch = async (order) => {
  if (!matchTargetPayment.value?.statement_id) {
    showMessage('Для данного типа платежа привязка не требуется', 'warning')
    return
  }
  matchActionLoading.value = true
  try {
    const res = await fetch('/api/v1/bank/manual-match', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        statement_id: matchTargetPayment.value.statement_id,
        order_id: order.id
      })
    })
    
    if (res.ok) {
      const data = await res.json()
      showMessage(data.message || 'Платеж успешно привязан к заказу!')
      isMatchDialogVisible.value = false
      await fetchPayments()
    } else {
      const err = await res.json()
      showMessage(err.detail || 'Не удалось привязать платеж', 'error')
    }
  } catch (e) {
    console.error('Ошибка привязки:', e)
    showMessage('Сбой сети при привязке к заказу', 'error')
  } finally {
    matchActionLoading.value = false
  }
}

// Выполнение отвязки от заказа
const executeUnmatch = async (payment) => {
  if (!payment.statement_id) return
  try {
    const res = await fetch('/api/v1/bank/unmatch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        statement_id: payment.statement_id
      })
    })
    
    if (res.ok) {
      showMessage('Транзакция успешно отвязана от заказа')
      isDetailsDialogVisible.value = false
      await fetchPayments()
    } else {
      const err = await res.json()
      showMessage(err.detail || 'Не удалось отвязать транзакцию', 'error')
    }
  } catch (e) {
    console.error('Ошибка отвязки:', e)
    showMessage('Сбой сети при отвязке', 'error')
  }
}

// Экспорт таблицы в CSV
const exportToCSV = () => {
  if (!filteredPayments.value.length) {
    showMessage('Нет данных для экспорта', 'warning')
    return
  }
  
  const headersRow = ['ID', 'Дата и время', 'Транзакция', 'RRN', 'Клиент', 'Телефон', 'Способ оплаты', 'Банк', 'Сумма (Банк)', 'Сумма (iiko)', 'Разница', 'Номер заказа', 'Статус']
  const rows = filteredPayments.value.map(p => [
    p.id,
    formatDate(p.date),
    `"${(p.transaction_id || '').replace(/"/g, '""')}"`,
    `"${(p.rrn || '').replace(/"/g, '""')}"`,
    `"${(p.customer_name || '').replace(/"/g, '""')}"`,
    `"${(p.customer_phone || '').replace(/"/g, '""')}"`,
    `"${(p.payment_method || '').replace(/"/g, '""')}"`,
    `"${(p.bank_name || '').replace(/"/g, '""')}"`,
    (p.bank_amount || 0).toFixed(2),
    (p.order_amount || 0).toFixed(2),
    getDifference(p).toFixed(2),
    `"${(p.order_number || '').replace(/"/g, '""')}"`,
    `"${p.status === 'matched' ? 'Сверено' : (p.status === 'discrepancy' ? 'Расхождение' : (p.status === 'unmatched_bank' ? 'Без заказа' : 'Не оплачен'))}"`
  ])
  
  const csvContent = '\uFEFF' + [headersRow.join(';'), ...rows.map(r => r.join(';'))].join('\r\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `bank_payments_${new Date().toISOString().split('T')[0]}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  showMessage('Файл CSV успешно сформирован!')
}

let refreshInterval = null

onMounted(() => {
  fetchPayments()
  // Периодическое фоновое обновление каждые 20 секунд
  refreshInterval = setInterval(() => {
    fetchPayments()
  }, 20000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
})
</script>

<template>
  <div>
    <!-- Шапка страницы -->
    <div class="d-flex flex-wrap justify-space-between align-center gap-4 mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1 d-flex align-center">
          <VIcon icon="bx-credit-card" color="primary" class="me-2" size="36" />
          Операции банка — Входящие платежи
        </h1>
        <p class="text-subtitle-1 text-muted mb-0">Полный реестр входящих платежей, эквайринга, СБП и авто-сверка с заказами iiko</p>
      </div>
      
      <div class="d-flex flex-wrap gap-2">
        <VBtn
          color="secondary"
          variant="outlined"
          prepend-icon="bx-download"
          size="default"
          class="font-weight-bold elevation-1"
          @click="exportToCSV"
        >
          Экспорт в CSV
        </VBtn>

        <VBtn
          color="secondary"
          variant="outlined"
          prepend-icon="bx-link-external"
          size="default"
          class="font-weight-bold elevation-1"
          :loading="autoMatchLoading"
          @click="runAutoMatch"
        >
          Авто-связка с заказами
        </VBtn>
        
        <VBtn
          color="primary"
          prepend-icon="bx-sync"
          size="default"
          class="gradient-btn font-weight-bold elevation-2"
          @click="startSyncSimulation"
        >
          Загрузить выписку Т-Банка
        </VBtn>
      </div>
    </div>

    <!-- Карточки KPI -->
    <VRow class="mb-6">
      <!-- 1. Сумма поступлений -->
      <VCol cols="12" sm="6" md="4" lg="" class="flex-grow-1 flex-shrink-0" style="min-width: 210px">
        <VCard class="kpi-card glass-card fill-height" ripple @click="activeTab = 'all'">
          <VCardText class="d-flex align-center justify-space-between py-4">
            <div>
              <span class="text-subtitle-2 text-muted d-block mb-1">Сумма поступлений</span>
              <h3 class="text-h4 font-weight-bold text-primary">{{ formatCurrency(kpi.totalSum) }}</h3>
              <span class="text-caption text-success font-weight-semibold d-flex align-center mt-1">
                <VIcon icon="bx-check-circle" class="me-1" size="14" /> Всего операций: {{ kpi.totalCount }}
              </span>
            </div>
            <VAvatar color="primary" variant="tonal" size="52" class="rounded-lg">
              <VIcon icon="bx-wallet" size="28" />
            </VAvatar>
          </VCardText>
        </VCard>
      </VCol>

      <!-- 2. Сверено -->
      <VCol cols="12" sm="6" md="4" lg="" class="flex-grow-1 flex-shrink-0" style="min-width: 210px">
        <VCard class="kpi-card glass-card fill-height" ripple @click="statusFilter = 'matched'">
          <VCardText class="d-flex align-center justify-space-between py-4">
            <div>
              <span class="text-subtitle-2 text-muted d-block mb-1">Успешно сверено</span>
              <h3 class="text-h4 font-weight-bold text-success">{{ kpi.matched }}</h3>
              <span class="text-caption text-muted d-block mt-1">Транзакции без расхождений</span>
            </div>
            <VAvatar color="success" variant="tonal" size="52" class="rounded-lg">
              <VIcon icon="bx-check-double" size="28" />
            </VAvatar>
          </VCardText>
        </VCard>
      </VCol>

      <!-- 3. Расхождения -->
      <VCol cols="12" sm="6" md="4" lg="" class="flex-grow-1 flex-shrink-0" style="min-width: 210px">
        <VCard class="kpi-card glass-card fill-height" ripple @click="statusFilter = 'discrepancy'">
          <VCardText class="d-flex align-center justify-space-between py-4">
            <div>
              <span class="text-subtitle-2 text-muted d-block mb-1">Несовпадение сумм</span>
              <h3 class="text-h4 font-weight-bold text-warning">{{ kpi.discrepancy }}</h3>
              <span class="text-caption text-warning font-weight-semibold d-flex align-center mt-1">
                <VIcon icon="bx-info-circle" class="me-1" size="14" /> Разница в сумме
              </span>
            </div>
            <VAvatar color="warning" variant="tonal" size="52" class="rounded-lg">
              <VIcon icon="bx-error" size="28" />
            </VAvatar>
          </VCardText>
        </VCard>
      </VCol>

      <!-- 4. Без заказа -->
      <VCol cols="12" sm="6" md="4" lg="" class="flex-grow-1 flex-shrink-0" style="min-width: 210px">
        <VCard class="kpi-card glass-card fill-height" ripple @click="statusFilter = 'unmatched_bank'">
          <VCardText class="d-flex align-center justify-space-between py-4">
            <div>
              <span class="text-subtitle-2 text-muted d-block mb-1">Платежи без заказов</span>
              <h3 class="text-h4 font-weight-bold text-error">{{ kpi.unmatched }}</h3>
              <span class="text-caption text-error font-weight-semibold d-flex align-center mt-1">
                <VIcon icon="bx-help-circle" class="me-1" size="14" /> Требуют привязки
              </span>
            </div>
            <VAvatar color="error" variant="tonal" size="52" class="rounded-lg">
              <VIcon icon="bx-question-mark" size="28" />
            </VAvatar>
          </VCardText>
        </VCard>
      </VCol>

      <!-- 5. Не оплачено -->
      <VCol cols="12" sm="6" md="4" lg="" class="flex-grow-1 flex-shrink-0" style="min-width: 210px">
        <VCard class="kpi-card glass-card fill-height" ripple @click="statusFilter = 'unmatched_order'">
          <VCardText class="d-flex align-center justify-space-between py-4">
            <div>
              <span class="text-subtitle-2 text-muted d-block mb-1">Заказы без оплат</span>
              <h3 class="text-h4 font-weight-bold text-deep-orange-darken-1">{{ kpi.unpaid }}</h3>
              <span class="text-caption text-deep-orange font-weight-semibold d-flex align-center mt-1">
                <VIcon icon="bx-x-circle" class="me-1" size="14" /> Ожидают подтверждения
              </span>
            </div>
            <VAvatar color="deep-orange" variant="tonal" size="52" class="rounded-lg">
              <VIcon icon="bx-money" size="28" style="color: #ff5722 !important" />
            </VAvatar>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Вкладки (Tabs) -->
    <div class="d-flex flex-wrap justify-space-between align-center mb-4">
      <VTabs v-model="activeTab" color="primary" class="border-bottom">
        <VTab value="all">
          <VIcon icon="bx-list-ul" class="me-2" />
          Все платежи ({{ payments.length }})
        </VTab>
        <VTab value="sbp_tpay">
          <VIcon icon="bx-qr" class="me-2" />
          СБП & T-Pay
        </VTab>
        <VTab value="card">
          <VIcon icon="bx-credit-card" class="me-2" />
          Эквайринг (Карты)
        </VTab>
        <VTab value="transfer">
          <VIcon icon="bx-transfer" class="me-2" />
          Переводы и Наличные
        </VTab>
        <VTab value="attention">
          <VIcon icon="bx-bell" class="me-2" color="warning" />
          Требуют внимания ({{ kpi.discrepancy + kpi.unmatched + kpi.unpaid }})
        </VTab>
      </VTabs>

      <!-- Быстрые фильтры дат -->
      <div class="d-flex gap-1 mt-2 mt-md-0">
        <VBtn
          size="small"
          :variant="activeDatePreset === 'today' ? 'flat' : 'tonal'"
          :color="activeDatePreset === 'today' ? 'primary' : 'default'"
          @click="setDatePreset('today')"
        >
          Сегодня
        </VBtn>
        <VBtn
          size="small"
          :variant="activeDatePreset === 'yesterday' ? 'flat' : 'tonal'"
          :color="activeDatePreset === 'yesterday' ? 'primary' : 'default'"
          @click="setDatePreset('yesterday')"
        >
          Вчера
        </VBtn>
        <VBtn
          size="small"
          :variant="activeDatePreset === '7days' ? 'flat' : 'tonal'"
          :color="activeDatePreset === '7days' ? 'primary' : 'default'"
          @click="setDatePreset('7days')"
        >
          7 дней
        </VBtn>
        <VBtn
          size="small"
          :variant="activeDatePreset === '30days' ? 'flat' : 'tonal'"
          :color="activeDatePreset === '30days' ? 'primary' : 'default'"
          @click="setDatePreset('30days')"
        >
          30 дней
        </VBtn>
        <VBtn
          size="small"
          :variant="activeDatePreset === 'all' ? 'flat' : 'tonal'"
          :color="activeDatePreset === 'all' ? 'primary' : 'default'"
          @click="setDatePreset('all')"
        >
          Все время
        </VBtn>
      </div>
    </div>

    <!-- Панель Фильтров -->
    <VCard class="glass-card mb-6 py-2">
      <VCardText>
        <VRow align="center">
          <!-- Период дат -->
          <VCol cols="12" sm="6" md="3">
            <VTextField
              v-model="dateFrom"
              type="date"
              label="Дата С"
              density="compact"
              clearable
              variant="outlined"
              prepend-inner-icon="bx-calendar"
              hide-details
            />
          </VCol>
          <VCol cols="12" sm="6" md="3">
            <VTextField
              v-model="dateTo"
              type="date"
              label="Дата По"
              density="compact"
              clearable
              variant="outlined"
              prepend-inner-icon="bx-calendar"
              hide-details
            />
          </VCol>
          
          <!-- Статус сверки -->
          <VCol cols="12" sm="6" md="3">
            <VSelect
              v-model="statusFilter"
              :items="statusOptions"
              label="Статус сверки"
              density="compact"
              variant="outlined"
              hide-details
            />
          </VCol>

          <!-- Поиск -->
          <VCol cols="12" sm="6" md="3">
            <VTextField
              v-model="searchQuery"
              label="Поиск по клиенту, заказу, сумме..."
              density="compact"
              variant="outlined"
              clearable
              prepend-inner-icon="bx-search"
              hide-details
            />
          </VCol>
        </VRow>
        
        <div class="d-flex justify-end mt-2" v-if="dateFrom || dateTo || statusFilter !== 'all' || searchQuery || activeTab !== 'all'">
          <VBtn
            size="small"
            variant="text"
            color="secondary"
            prepend-icon="bx-x"
            @click="resetFilters"
          >
            Сбросить все фильтры
          </VBtn>
        </div>
      </VCardText>
    </VCard>

    <!-- Основная таблица -->
    <VCard class="glass-card">
      <VDataTable
        :headers="headers"
        :items="filteredPayments"
        :loading="loading"
        :items-per-page-options="[10, 25, 50, 100, 200, { value: -1, title: 'Все' }]"
        items-per-page="25"
        hover
        no-data-text="Платежи за выбранный период не найдены"
        loading-text="Загрузка списка банковских транзакций..."
        class="payments-table"
      >
        <!-- Форматирование даты -->
        <template #item.date="{ item }">
          <div class="d-flex flex-column">
            <span class="font-weight-medium text-body-2">{{ formatDate(item.date) }}</span>
            <span class="text-caption text-muted" v-if="item.source_type === 'bank_statement'">Выписка банка</span>
            <span class="text-caption text-muted" v-else>Заказ iiko</span>
          </div>
        </template>

        <!-- Транзакция (ID / RRN) -->
        <template #item.txn_details="{ item }">
          <div class="d-flex flex-column">
            <span class="font-weight-bold text-body-2 font-monospace">{{ item.transaction_id }}</span>
            <span class="text-caption text-muted" v-if="item.rrn && item.rrn !== '-'">RRN: {{ item.rrn }}</span>
          </div>
        </template>

        <!-- Имя клиента / Заказ -->
        <template #item.customer_name="{ item }">
          <div class="d-flex flex-column">
            <div class="d-flex align-center">
              <span class="font-weight-bold text-body-2 me-2">{{ item.customer_name }}</span>
              <VChip
                v-if="item.order_number && item.order_number !== '-'"
                size="x-small"
                variant="outlined"
                color="primary"
                class="font-weight-bold"
              >
                №{{ item.order_number }}
              </VChip>
            </div>
            <span class="text-caption text-muted" v-if="item.customer_phone">{{ item.customer_phone }}</span>
            <span class="text-caption text-muted text-truncate" style="max-width: 220px;" v-else-if="item.payment_purpose">{{ item.payment_purpose }}</span>
          </div>
        </template>

        <!-- Способ оплаты -->
        <template #item.payment_method="{ item }">
          <div class="d-flex align-center">
            <VIcon 
              :icon="item.payment_method === 'СБП' ? 'bx-qr' : (item.payment_method === 'T-Pay' ? 'bx-mobile' : (item.payment_method === 'Перевод' ? 'bx-transfer' : 'bx-credit-card'))" 
              :color="item.payment_method === 'СБП' ? 'info' : (item.payment_method === 'T-Pay' ? 'warning' : (item.payment_method === 'Перевод' ? 'success' : 'primary'))" 
              class="me-2" 
              size="20" 
            />
            <div>
              <span class="font-weight-medium text-body-2">{{ item.payment_method }}</span>
              <span class="d-block text-caption text-muted">{{ item.bank_name }}</span>
            </div>
          </div>
        </template>

        <!-- Сумма Банка -->
        <template #item.bank_amount="{ item }">
          <span v-if="item.bank_amount > 0" class="font-weight-bold text-primary text-body-1">{{ formatCurrency(item.bank_amount) }}</span>
          <span v-else class="text-disabled text-caption">0.00 ₽</span>
        </template>

        <!-- Сумма iiko -->
        <template #item.order_amount="{ item }">
          <span v-if="item.order_amount > 0" class="font-weight-medium text-body-2">{{ formatCurrency(item.order_amount) }}</span>
          <span v-else class="text-disabled">—</span>
        </template>

        <!-- Разница -->
        <template #item.difference="{ item }">
          <template v-if="getDifference(item) === 0">
            <span class="text-muted text-caption">0.00 ₽</span>
          </template>
          <template v-else-if="getDifference(item) > 0">
            <span class="text-success font-weight-bold text-caption">+{{ formatCurrency(getDifference(item)) }}</span>
          </template>
          <template v-else>
            <span class="text-error font-weight-bold text-caption">{{ formatCurrency(getDifference(item)) }}</span>
          </template>
        </template>

        <!-- Статус сверки (чипы) -->
        <template #item.status="{ item }">
          <VChip
            v-if="item.status === 'matched'"
            color="success"
            size="small"
            variant="tonal"
            label
            class="font-weight-bold"
            prepend-icon="bx-check"
          >
            Сверено
          </VChip>
          <VChip
            v-else-if="item.status === 'discrepancy'"
            color="warning"
            size="small"
            variant="tonal"
            label
            class="font-weight-bold"
            prepend-icon="bx-error-circle"
          >
            Расхождение
          </VChip>
          <VChip
            v-else-if="item.status === 'unmatched_bank'"
            color="error"
            size="small"
            variant="tonal"
            label
            class="font-weight-bold"
            prepend-icon="bx-help-circle"
          >
            Без заказа
          </VChip>
          <VChip
            v-else-if="item.status === 'unmatched_order'"
            color="deep-orange"
            size="small"
            variant="tonal"
            label
            class="font-weight-bold"
            prepend-icon="bx-x-circle"
          >
            Не оплачен
          </VChip>
        </template>

        <!-- Действия -->
        <template #item.actions="{ item }">
          <div class="d-flex align-center justify-center gap-1">
            <VBtn
              icon="bx-show"
              size="small"
              variant="text"
              color="primary"
              @click="openDetails(item)"
              title="Просмотр деталей"
            />
            <VBtn
              v-if="item.statement_id && item.status !== 'matched'"
              icon="bx-link"
              size="small"
              variant="text"
              color="warning"
              @click="openManualMatchDialog(item)"
              title="Привязать к заказу"
            />
          </div>
        </template>
      </VDataTable>
    </VCard>

    <!-- Диалог симуляции загрузки выписки -->
    <VDialog v-model="isSyncDialogVisible" max-width="520px" persistent>
      <VCard class="glass-card py-4">
        <VCardText class="d-flex flex-column align-center text-center">
          <h3 class="text-h5 font-weight-bold mb-4">Синхронизация с Т-Банком</h3>
          
          <VProgressCircular
            v-if="syncLoading"
            :model-value="syncProgress"
            :size="80"
            :width="8"
            color="primary"
            class="mb-4"
          >
            {{ syncProgress }}%
          </VProgressCircular>
          
          <VAvatar v-else color="success" variant="tonal" size="80" class="mb-4">
            <VIcon icon="bx-check" size="48" color="success" />
          </VAvatar>

          <p class="text-body-1 font-weight-medium mb-2">{{ syncMessage }}</p>
          <p class="text-caption text-muted" v-if="syncLoading">Пожалуйста, не закрывайте это окно</p>
        </VCardText>
        <VCardActions class="justify-center">
          <VBtn
            v-if="!syncLoading"
            color="primary"
            variant="flat"
            @click="isSyncDialogVisible = false"
            class="px-6 font-weight-bold"
          >
            Понятно
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог деталей транзакции -->
    <VDialog v-model="isDetailsDialogVisible" max-width="640px">
      <VCard class="glass-card" v-if="selectedPayment">
        <VCardTitle class="d-flex align-center justify-space-between border-bottom py-4 px-6">
          <span class="text-h5 font-weight-bold">Детали платежа / транзакции</span>
          <VBtn icon="bx-x" variant="text" @click="isDetailsDialogVisible = false" />
        </VCardTitle>
        
        <VCardText class="py-6 px-6">
          <!-- Карточка со статусом и суммами -->
          <div class="d-flex justify-space-between align-center p-4 rounded-lg bg-light-gradient mb-6">
            <div>
              <span class="text-caption text-muted d-block">Сумма в банке</span>
              <span class="text-h4 font-weight-black text-primary">{{ formatCurrency(selectedPayment.bank_amount) }}</span>
            </div>
            
            <div class="text-right">
              <span class="text-caption text-muted d-block">Статус сверки</span>
              <VChip
                v-if="selectedPayment.status === 'matched'"
                color="success"
                variant="flat"
                size="small"
                label
                class="font-weight-bold mt-1"
              >
                Сверено успешно
              </VChip>
              <VChip
                v-else-if="selectedPayment.status === 'discrepancy'"
                color="warning"
                variant="flat"
                size="small"
                label
                class="font-weight-bold mt-1"
              >
                Расхождение сумм
              </VChip>
              <VChip
                v-else-if="selectedPayment.status === 'unmatched_bank'"
                color="error"
                variant="flat"
                size="small"
                label
                class="font-weight-bold mt-1"
              >
                Платеж без заказа
              </VChip>
              <VChip
                v-else-if="selectedPayment.status === 'unmatched_order'"
                color="deep-orange"
                variant="flat"
                size="small"
                label
                class="font-weight-bold mt-1"
              >
                Заказ не оплачен
              </VChip>
            </div>
          </div>

          <!-- Список параметров -->
          <VList class="details-list bg-transparent pa-0">
            <!-- ID транзакции -->
            <VListItem class="px-0 py-2 border-bottom">
              <template #prepend>
                <span class="font-weight-semibold text-muted text-body-2" style="width: 160px">ID транзакции:</span>
              </template>
              <span class="font-weight-bold text-body-2">{{ selectedPayment.transaction_id }}</span>
            </VListItem>

            <!-- RRN -->
            <VListItem class="px-0 py-2 border-bottom" v-if="selectedPayment.rrn && selectedPayment.rrn !== '-'">
              <template #prepend>
                <span class="font-weight-semibold text-muted text-body-2" style="width: 160px">RRN код / Счет:</span>
              </template>
              <span class="font-weight-medium text-body-2">{{ selectedPayment.rrn }}</span>
            </VListItem>

            <!-- Дата -->
            <VListItem class="px-0 py-2 border-bottom">
              <template #prepend>
                <span class="font-weight-semibold text-muted text-body-2" style="width: 160px">Дата и время:</span>
              </template>
              <span class="text-body-2">{{ formatDate(selectedPayment.date) }}</span>
            </VListItem>

            <!-- Банк и способ -->
            <VListItem class="px-0 py-2 border-bottom">
              <template #prepend>
                <span class="font-weight-semibold text-muted text-body-2" style="width: 160px">Банк / Метод:</span>
              </template>
              <span class="text-body-2">{{ selectedPayment.bank_name }} — {{ selectedPayment.payment_method }}</span>
            </VListItem>

            <!-- Заказ iiko -->
            <VListItem class="px-0 py-2 border-bottom">
              <template #prepend>
                <span class="font-weight-semibold text-muted text-body-2" style="width: 160px">Заказ в iiko:</span>
              </template>
              <div v-if="selectedPayment.order_id" class="d-flex align-center">
                <VBtn
                  variant="text"
                  color="primary"
                  class="pa-0 font-weight-bold text-body-2 text-decoration-none min-width-0"
                  :to="`/orders`"
                >
                  {{ selectedPayment.order_number }}
                </VBtn>
                <span class="text-caption text-muted ms-2">(ID: {{ selectedPayment.order_id }})</span>
              </div>
              <span v-else class="text-error font-weight-medium text-body-2">Отсутствует привязка к заказу</span>
            </VListItem>

            <!-- Сумма в iiko -->
            <VListItem class="px-0 py-2 border-bottom" v-if="selectedPayment.order_amount > 0">
              <template #prepend>
                <span class="font-weight-semibold text-muted text-body-2" style="width: 160px">Сумма заказа:</span>
              </template>
              <span class="text-body-2">{{ formatCurrency(selectedPayment.order_amount) }}</span>
            </VListItem>

            <!-- Плательщик / Клиент -->
            <VListItem class="px-0 py-2 border-bottom">
              <template #prepend>
                <span class="font-weight-semibold text-muted text-body-2" style="width: 160px">Плательщик:</span>
              </template>
              <div class="d-flex flex-column">
                <span class="text-body-2 font-weight-medium">{{ selectedPayment.customer_name }}</span>
                <span class="text-caption text-muted" v-if="selectedPayment.customer_phone">Тел: {{ selectedPayment.customer_phone }}</span>
                <span class="text-caption text-muted" v-if="selectedPayment.payer_inn">ИНН: {{ selectedPayment.payer_inn }}</span>
              </div>
            </VListItem>

            <!-- Назначение платежа -->
            <VListItem class="px-0 py-2 border-bottom" v-if="selectedPayment.payment_purpose">
              <template #prepend>
                <span class="font-weight-semibold text-muted text-body-2" style="width: 160px">Назначение:</span>
              </template>
              <span class="text-body-2">{{ selectedPayment.payment_purpose }}</span>
            </VListItem>

            <!-- Описание системы сверки -->
            <VListItem class="px-0 py-3">
              <div class="d-flex flex-column">
                <span class="font-weight-semibold text-muted text-body-2 mb-1">Статус и примечание:</span>
                <VAlert
                  :color="selectedPayment.status === 'matched' ? 'success' : (selectedPayment.status === 'discrepancy' ? 'warning' : 'error')"
                  variant="tonal"
                  class="mt-1 text-body-2 py-2 px-3 border-0 rounded"
                  density="compact"
                >
                  {{ selectedPayment.description }}
                </VAlert>
              </div>
            </VListItem>
          </VList>
        </VCardText>
        
        <VCardActions class="px-6 pb-6">
          <VSpacer />
          <!-- Кнопка ручной привязки -->
          <VBtn
            v-if="selectedPayment.statement_id && selectedPayment.status !== 'matched'"
            color="primary"
            variant="flat"
            class="font-weight-bold me-2"
            prepend-icon="bx-link"
            @click="openManualMatchDialog(selectedPayment)"
          >
            Привязать к заказу
          </VBtn>

          <!-- Кнопка отвязки -->
          <VBtn
            v-if="selectedPayment.statement_id && selectedPayment.order_id"
            color="error"
            variant="tonal"
            class="font-weight-bold me-2"
            prepend-icon="bx-unlink"
            @click="executeUnmatch(selectedPayment)"
          >
            Отвязать от заказа
          </VBtn>

          <VBtn
            color="secondary"
            variant="outlined"
            @click="isDetailsDialogVisible = false"
            class="font-weight-bold"
          >
            Закрыть
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог выбора заказа для ручной привязки -->
    <VDialog v-model="isMatchDialogVisible" max-width="700px">
      <VCard class="glass-card" v-if="matchTargetPayment">
        <VCardTitle class="d-flex align-center justify-space-between border-bottom py-4 px-6">
          <div>
            <h3 class="text-h5 font-weight-bold">Привязка платежа к заказу iiko</h3>
            <span class="text-caption text-muted">
              Сумма: {{ formatCurrency(matchTargetPayment.bank_amount) }} | {{ matchTargetPayment.payment_method }} | {{ formatDate(matchTargetPayment.date) }}
            </span>
          </div>
          <VBtn icon="bx-x" variant="text" @click="isMatchDialogVisible = false" />
        </VCardTitle>

        <VCardText class="py-4 px-6">
          <!-- Поле поиска -->
          <VTextField
            v-model="matchSearchQuery"
            label="Поиск по номеру заказа, телефону или имени гостя..."
            density="compact"
            variant="outlined"
            prepend-inner-icon="bx-search"
            clearable
            class="mb-4"
            @keyup.enter="searchOrdersForMatch"
          >
            <template #append-inner>
              <VBtn
                size="small"
                color="primary"
                variant="flat"
                :loading="matchOrdersLoading"
                @click="searchOrdersForMatch"
              >
                Найти
              </VBtn>
            </template>
          </VTextField>

          <!-- Список найденных заказов -->
          <div v-if="matchOrdersLoading" class="text-center py-6">
            <VProgressCircular indeterminate color="primary" />
            <p class="text-caption text-muted mt-2">Поиск подходящих заказов...</p>
          </div>

          <div v-else-if="matchingOrders.length === 0" class="text-center py-6 text-muted">
            <VIcon icon="bx-search-alt" size="48" class="mb-2" />
            <p class="text-body-1 font-weight-medium mb-1">Заказы не найдены</p>
            <p class="text-caption">Попробуйте ввести другой номер заказа или телефон в строку поиска</p>
          </div>

          <VList v-else class="bg-transparent pa-0 max-height-350 overflow-y-auto">
            <VListItem
              v-for="order in matchingOrders"
              :key="order.id"
              class="border rounded-lg mb-2 pa-3"
            >
              <div class="d-flex justify-space-between align-center">
                <div>
                  <div class="d-flex align-center gap-2 mb-1">
                    <span class="font-weight-bold text-body-1 text-primary">Заказ {{ order.external_number }}</span>
                    <VChip size="x-small" :color="order.is_paid ? 'success' : 'warning'" variant="tonal" label>
                      {{ order.is_paid ? 'Оплачен' : 'Не оплачен' }}
                    </VChip>
                    <span class="text-caption text-muted">{{ order.created_at }}</span>
                  </div>
                  <div class="text-body-2 font-weight-medium">
                    {{ order.customer_name }} <span class="text-muted font-weight-regular" v-if="order.customer_phone">({{ order.customer_phone }})</span>
                  </div>
                  <div class="text-caption text-muted mt-1" v-if="order.delivery_address">
                    Адрес: {{ order.delivery_address }}
                  </div>
                </div>

                <div class="text-right">
                  <div class="text-h6 font-weight-black text-primary mb-1">
                    {{ formatCurrency(order.total_amount) }}
                  </div>
                  <VBtn
                    size="small"
                    color="primary"
                    variant="flat"
                    class="font-weight-bold"
                    prepend-icon="bx-check"
                    :loading="matchActionLoading"
                    @click="executeManualMatch(order)"
                  >
                    Привязать
                  </VBtn>
                </div>
              </div>
            </VListItem>
          </VList>
        </VCardText>

        <VCardActions class="px-6 pb-4">
          <VSpacer />
          <VBtn
            color="secondary"
            variant="outlined"
            @click="isMatchDialogVisible = false"
          >
            Отмена
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Всплывающее уведомление -->
    <VSnackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="4000"
      location="top right"
    >
      {{ snackbar.text }}
      <template #actions>
        <VBtn
          variant="text"
          @click="snackbar.show = false"
        >
          Закрыть
        </VBtn>
      </template>
    </VSnackbar>
  </div>
</template>

<style scoped>
/* Стеклянные карточки */
.glass-card {
  background: rgba(var(--v-theme-surface), 0.7) !important;
  backdrop-filter: blur(10px) !important;
  border: 1px solid rgba(var(--v-border-color), 0.08) !important;
  border-radius: 12px !important;
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

/* Эффект наведения на карточки KPI */
.kpi-card {
  cursor: pointer;
}
.kpi-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(var(--v-theme-primary), 0.12) !important;
}

/* Красивая кнопка с градиентом */
.gradient-btn {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 1) 0%, rgba(var(--v-theme-secondary), 0.9) 100%) !important;
  color: white !important;
  border: none !important;
}

/* Тонкая рамка разделения элементов списка */
.border-bottom {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.08);
}

/* Градиентный фон блока информации в диалоговом окне */
.bg-light-gradient {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.05) 0%, rgba(var(--v-theme-secondary), 0.03) 100%);
  border: 1px solid rgba(var(--v-theme-primary), 0.08);
}

.payments-table :deep(tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.02) !important;
}

.max-height-350 {
  max-height: 350px;
}
</style>
