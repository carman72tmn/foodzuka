<template>
  <VDialog
    v-model="isVisible"
    max-width="1200px"
    scrollable
    transition="dialog-bottom-transition"
  >
    <VCard class="customer-detail-card overflow-hidden">
      <!-- Toolbar / Header -->
      <VToolbar
        color="primary"
        class="px-4"
        elevation="0"
      >
        <VAvatar
          size="40"
          color="white"
          variant="tonal"
          class="me-3"
        >
          <VImg :src="guestAvatar" />
        </VAvatar>
        
        <div class="d-flex flex-column">
          <span class="text-h6 font-weight-bold text-white line-height-1">
            {{ customer?.name || 'Гость' }} {{ customer?.surname || '' }}
          </span>
          <span class="text-caption text-white opacity-80">
            {{ customer?.phone || 'Нет телефона' }}
          </span>
        </div>

        <VSpacer />

        <VChip
          v-if="customer?.is_new_guest"
          color="success"
          size="small"
          class="me-4 font-weight-bold"
          variant="elevated"
        >
          НОВЫЙ ГОСТЬ
        </VChip>

        <VBtn
          icon="ri-close-line"
          variant="text"
          color="white"
          @click="close"
        />
      </VToolbar>

      <VDivider />

      <VCardText class="pa-0 flex-grow-1">
        <VRow no-gutters class="fill-height">
          <!-- Sidebar -->
          <VCol
            cols="12"
            md="3"
            class="bg-grey-lighten-5 border-e d-flex flex-column pa-4"
          >
            <div class="sidebar-analytics-box mb-6 pa-4 rounded-lg bg-white elevation-1">
              <div class="text-overline text-disabled mb-2">Общая аналитика</div>
              
              <div class="mb-4">
                <div class="text-caption text-muted">LTV (Выручка)</div>
                <div class="text-h6 font-weight-bold text-primary">
                  {{ formatPrice(customer?.total_purchases_sum || customer?.total_orders_amount || 0) }}
                </div>
              </div>

              <div class="mb-4">
                <div class="text-caption text-muted">Средний чек</div>
                <div class="text-h6 font-weight-bold">
                  {{ formatPrice(analytics?.average_check || 0) }}
                </div>
              </div>

              <div class="mb-4">
                <div class="text-caption text-muted">Всего заказов</div>
                <div class="text-h6 font-weight-bold">
                  {{ customer?.total_orders_count || 0 }}
                </div>
              </div>

              <div v-if="customer?.last_order_date">
                <div class="text-caption text-muted">Последний визит</div>
                <div class="text-body-2 font-weight-medium">
                  {{ formatDate(customer?.last_order_date) }}
                </div>
              </div>
            </div>

            <VBtn
              color="primary"
              block
              variant="tonal"
              prepend-icon="bx-sync"
              :loading="isSyncing"
              class="mt-auto"
              @click="syncFullData"
            >
              Синхронизировать
            </VBtn>
          </VCol>

          <!-- Main Content -->
          <VCol cols="12" md="9" class="d-flex flex-column">
            <VTabs
              v-model="activeTab"
              color="primary"
              align-tabs="start"
              density="compact"
              class="border-b"
            >
              <VTab
                v-for="tab in tabs"
                :key="tab.id"
                :value="tab.id"
                class="text-none"
              >
                <VIcon :icon="tab.icon" start />
                {{ tab.title }}
              </VTab>
            </VTabs>

            <VWindow v-model="activeTab" class="flex-grow-1 overflow-y-auto" style="height: 600px;">
              <!-- 1. Анкета -->
              <VWindowItem value="profile">
                <VContainer class="pa-6">
                  <VRow>
                    <VCol cols="12" md="6">
                      <VTextField v-model="form.name" label="Имя" variant="outlined" density="compact" />
                    </VCol>
                    <VCol cols="12" md="6">
                      <VTextField v-model="form.surname" label="Фамилия" variant="outlined" density="compact" />
                    </VCol>
                    <VCol cols="12" md="6">
                      <VTextField v-model="form.email" label="Email" variant="outlined" density="compact" />
                    </VCol>
                    <VCol cols="12" md="6">
                      <VTextField v-model="form.birthday" label="Дата рождения" type="date" variant="outlined" density="compact" />
                    </VCol>
                    <VCol cols="12">
                      <VTextarea v-model="form.iikoNotes" label="Заметки iiko / Комментарий" variant="outlined" density="compact" rows="3" />
                    </VCol>
                  </VRow>
                  <div class="d-flex justify-end mt-4">
                    <VBtn color="primary" @click="saveProfile">Сохранить изменения</VBtn>
                  </div>
                </VContainer>
              </VWindowItem>

              <!-- 2. Бонусы -->
              <VWindowItem value="bonuses">
                <VContainer class="pa-6">
                  <VRow>
                    <VCol cols="12" md="4">
                      <VCard variant="tonal" color="primary" class="pa-4 text-center">
                        <div class="text-h4 font-weight-bold">{{ customer?.bonus_points || 0 }}</div>
                        <div class="text-caption">Баланс баллов</div>
                      </VCard>
                    </VCol>
                  </VRow>
                  
                  <VRow class="mt-4">
                    <VCol cols="12">
                      <VCard variant="outlined" class="pa-4">
                        <div class="text-subtitle-1 font-weight-bold mb-3">Ручное изменение баланса</div>
                        <VRow>
                          <VCol cols="12" md="4">
                            <VTextField
                              v-model="bonusAdjustment.amount"
                              label="Сумма (±)"
                              type="number"
                              variant="outlined"
                              density="compact"
                              hint="Положительная для начисления, отрицательная для списания"
                              persistent-hint
                            />
                          </VCol>
                          <VCol cols="12" md="6">
                            <VTextField
                              v-model="bonusAdjustment.comment"
                              label="Комментарий для iiko"
                              variant="outlined"
                              density="compact"
                            />
                          </VCol>
                          <VCol cols="12" md="2" class="d-flex align-center">
                            <VBtn
                              color="primary"
                              block
                              :loading="isAdjustingBonuses"
                              :disabled="!bonusAdjustment.amount"
                              @click="adjustBonuses"
                            >
                              ОК
                            </VBtn>
                          </VCol>
                        </VRow>
                      </VCard>
                    </VCol>
                  </VRow>

                  <h3 class="text-h6 mt-6 mb-4">История транзакций</h3>
                  <VDataTable
                    :headers="[
                      { title: 'Дата', key: 'transaction_date' },
                      { title: 'Тип', key: 'type' },
                      { title: 'Сумма', key: 'amount', align: 'end' },
                      { title: 'Комментарий', key: 'comment' }
                    ]"
                    :items="bonusHistory"
                    density="compact"
                    class="elevation-0 border rounded"
                  >
                    <template #item.transaction_date="{ value }">{{ formatDate(value) }}</template>
                    <template #item.amount="{ value, item }">
                      <span :class="item.type === 'accrual' ? 'text-success' : 'text-error'">
                        {{ item.type === 'accrual' ? '+' : '-' }}{{ value }}
                      </span>
                    </template>
                  </VDataTable>
                </VContainer>
              </VWindowItem>

              <!-- 3. Заказы -->
              <VWindowItem value="orders">
                <VContainer class="pa-6">
                  <VDataTable
                    :headers="[
                      { title: 'Дата', key: 'date' },
                      { title: 'Сумма', key: 'sum', align: 'end' },
                      { title: 'Статус', key: 'status' },
                      { title: 'Тип', key: 'order_type' }
                    ]"
                    :items="ordersHistory"
                    density="compact"
                    class="elevation-0 border rounded"
                  >
                    <template #item.date="{ value }">{{ formatDate(value) }}</template>
                    <template #item.sum="{ value }">{{ formatPrice(value) }}</template>
                  </VDataTable>
                </VContainer>
              </VWindowItem>

              <!-- 4. Аналитика -->
              <VWindowItem value="analytics">
                <VContainer class="pa-6">
                  <VRow v-if="!olapLoading && !olapError">
                    <VCol cols="12" md="4" v-for="(stat, idx) in [
                      { label: 'Всего выручка (LTV)', value: formatPrice(analytics.total_sum || 0) },
                      { label: 'Средний чек', value: formatPrice(analytics.average_check || 0) },
                      { label: 'Заказов всего', value: analytics.total_count || 0 },
                      { label: 'Частота заказов (дн)', value: analytics.frequency_days || '-' },
                      { label: 'Дней с последнего заказа', value: analytics.days_since_last_order || '-' }
                    ]" :key="idx">
                      <VCard variant="outlined" class="pa-4">
                        <div class="text-caption text-muted">{{ stat.label }}</div>
                        <div class="text-h6 font-weight-bold">{{ stat.value }}</div>
                      </VCard>
                    </VCol>
                  </VRow>
                  <div v-else-if="olapLoading" class="text-center py-10">
                    <VProgressCircular indeterminate color="primary" />
                    <div class="mt-2 text-caption">Загрузка OLAP-аналитики...</div>
                  </div>
                  <VAlert v-else type="warning" variant="tonal" class="mt-4">
                    {{ olapError }}
                  </VAlert>
                </VContainer>
              </VWindowItem>

              <!-- 5. Риски -->
              <VWindowItem value="risks">
                <VContainer class="pa-6">
                  <VRow>
                    <VCol cols="12">
                      <VSwitch v-model="form.isHighRisk" label="Статус высокого риска" color="error" />
                      <VTextarea v-model="form.riskReason" label="Причина риска" variant="outlined" density="compact" rows="3" />
                    </VCol>
                  </VRow>
                  <div class="d-flex justify-end mt-4">
                    <VBtn color="error" @click="saveProfile">Обновить статус</VBtn>
                  </div>
                </VContainer>
              </VWindowItem>

              <!-- 6. Адреса -->
              <VWindowItem value="addresses">
                <VContainer class="pa-6">
                  <div class="d-flex justify-space-between align-center mb-4">
                    <h3 class="text-h6 mb-0">Связанные адреса</h3>
                    <VBtn
                      color="info"
                      variant="tonal"
                      size="small"
                      prepend-icon="ri-sync-line"
                      :loading="isSyncing"
                      @click="syncFullData"
                    >
                      Обновить из iiko
                    </VBtn>
                  </div>
                  <VList v-if="guestAddresses.length" density="compact">
                    <VListItem v-for="(addr, idx) in guestAddresses" :key="idx" :title="addr.address || addr" prepend-icon="ri-map-pin-2-line">
                      <template #subtitle v-if="addr.last_used_at">
                        Использован: {{ formatDate(addr.last_used_at) }}
                      </template>
                    </VListItem>
                  </VList>
                  <div v-else class="text-center py-10 text-disabled">Адреса не найдены</div>
                </VContainer>
              </VWindowItem>

              <!-- 7. Инфо -->
              <VWindowItem value="notifications">
                <VContainer class="pa-6">
                  <VList>
                    <VListItem title="Рекламная рассылка" :subtitle="customer?.is_marketing_consented ? 'Подписан' : 'Отписан'">
                      <template #prepend>
                        <VIcon :icon="customer?.is_marketing_consented ? 'ri-checkbox-circle-line' : 'ri-close-circle-line'" :color="customer?.is_marketing_consented ? 'success' : 'error'" />
                      </template>
                    </VListItem>
                    <VListItem title="Системные уведомления" subtitle="Активны (статусы заказов)">
                      <template #prepend>
                        <VIcon icon="ri-checkbox-circle-line" color="success" />
                      </template>
                    </VListItem>
                  </VList>
                </VContainer>
              </VWindowItem>

              <!-- 8. Лог -->
              <VWindowItem value="extra">
                <VContainer class="pa-6">
                  <pre class="bg-grey-darken-4 text-white pa-4 rounded text-caption overflow-x-auto">{{ JSON.stringify(customer, null, 2) }}</pre>
                </VContainer>
              </VWindowItem>
            </VWindow>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>
  </VDialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const props = defineProps({
  modelValue: Boolean,
  customer: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:modelValue', 'updated'])

const toast = useToast()

const activeTab = ref('profile')
const isSyncing = ref(false)
const olapLoading = ref(false)
const olapError = ref(null)
const analytics = ref({})
const bonusHistory = ref([])
const ordersHistory = ref([])
const guestAddresses = ref([])
const isAdjustingBonuses = ref(false)
const bonusAdjustment = ref({
  amount: 0,
  comment: 'Ручная корректировка из админ-панели'
})

const form = ref({
  name: '',
  surname: '',
  email: '',
  birthday: '',
  gender: 'NotSpecified',
  iikoNotes: '',
  isHighRisk: false,
  riskReason: '',
})

const tabs = [
  { id: 'profile', title: 'Анкета', icon: 'ri-id-card-line' },
  { id: 'bonuses', title: 'Бонусы', icon: 'ri-coin-line' },
  { id: 'orders', title: 'Заказы', icon: 'ri-shopping-bag-line' },
  { id: 'analytics', title: 'Аналитика', icon: 'ri-bar-chart-line' },
  { id: 'risks', title: 'Риски', icon: 'ri-error-warning-line' },
  { id: 'addresses', title: 'Адреса', icon: 'ri-map-pin-line' },
  { id: 'notifications', title: 'Инфо', icon: 'ri-notification-line' },
  { id: 'extra', title: 'Лог', icon: 'ri-code-line' },
]

const isVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const guestAvatar = computed(() => {
  const name = props.customer?.name || 'G'
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=c5a059&color=000&bold=true&size=128`
})

const close = () => {
  isVisible.value = false
}

const parseAddresses = () => {
  if (!props.customer?.addresses) {
    guestAddresses.value = []
    return
  }

  if (Array.isArray(props.customer.addresses)) {
    guestAddresses.value = props.customer.addresses
    return
  }

  try {
    guestAddresses.value = JSON.parse(props.customer.addresses)
  } catch {
    guestAddresses.value = [props.customer.addresses]
  }
}

const loadOlapStats = async () => {
  if (!props.customer?.id) return
  olapLoading.value = true
  olapError.value = null
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/olap-stats`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    
    const data = await response.json()
    if (data.error) {
      olapError.value = data.error === 'REST_API_LICENSE_REQUIRED'
        ? 'Отсутствует лицензия iiko Resto API'
        : data.message
    } else {
      analytics.value = data
    }
  } catch (error) {
    olapError.value = 'Не удалось загрузить аналитику'
    console.warn('OLAP Stats error:', error)
  } finally {
    olapLoading.value = false
  }
}

const loadOrderHistory = async () => {
  if (!props.customer?.id) return
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/history`)
    if (!response.ok) throw new Error('Failed to fetch history')
    const data = await response.json()
    ordersHistory.value = Array.isArray(data) ? data : []
  } catch (e) {
    ordersHistory.value = props.customer.orders_history || []
  }
}

const loadBonusHistory = async () => {
  if (!props.customer?.id) return
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/bonuses`)
    if (!response.ok) throw new Error('Failed to fetch bonuses')
    const data = await response.json()
    bonusHistory.value = data
  } catch (e) {
    console.warn('Bonus history failed')
  }
}

const initData = async () => {
  if (!props.customer?.id) return

  form.value = {
    name: props.customer.name || '',
    surname: props.customer.surname || '',
    email: props.customer.email || '',
    birthday: props.customer.birthday ? String(props.customer.birthday).split('T')[0] : '',
    gender: props.customer.gender || 'NotSpecified',
    iikoNotes: props.customer.iiko_notes || props.customer.notes || '',
    isHighRisk: props.customer.is_high_risk || false,
    riskReason: props.customer.risk_reason || '',
  }

  parseAddresses()

  await Promise.all([
    loadOlapStats(),
    loadOrderHistory(),
    loadBonusHistory(),
  ])
}

const syncFullData = async () => {
  if (!props.customer?.id) return
  isSyncing.value = true
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/sync-premium`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Failed to sync data')
    const data = await response.json()
    emit('updated', data)
    toast.success('Данные синхронизированы')
    await initData()
  } catch (error) {
    toast.error('Ошибка: ' + error.message)
  } finally {
    isSyncing.value = false
  }
}

const saveProfile = async () => {
  if (!props.customer?.id) return
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    if (!response.ok) throw new Error('Failed to save profile')
    const data = await response.json()
    emit('updated', data)
    toast.success('Сохранено')
  } catch (error) {
    toast.error('Ошибка: ' + error.message)
  }
}

const adjustBonuses = async () => {
  if (!props.customer?.id || !bonusAdjustment.value.amount) return
  isAdjustingBonuses.value = true
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/adjust-bonuses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount: bonusAdjustment.value.amount,
        comment: bonusAdjustment.value.comment
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to adjust bonuses')
    }
    
    toast.success('Баланс изменен')
    bonusAdjustment.value.amount = 0
    // Перезагружаем данные
    await loadBonusHistory()
    await syncFullData() 
  } catch (error) {
    toast.error('Ошибка: ' + error.message)
  } finally {
    isAdjustingBonuses.value = false
  }
}

const formatPrice = (value) => {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(value || 0)
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

watch(() => props.modelValue, (newVal) => {
  if (newVal && props.customer?.id) {
    initData()
  }
})

onMounted(() => {
  if (props.modelValue && props.customer?.id) {
    initData()
  }
})
</script>

<style scoped>
.customer-detail-card {
  border-radius: 12px;
}
.line-height-1 {
  line-height: 1.2;
}
.opacity-80 {
  opacity: 0.8;
}
.text-muted {
  color: rgba(0, 0, 0, 0.6);
}
</style>
