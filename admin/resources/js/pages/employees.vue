<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { formatDateTime } from '@/utils/date'

const employees = ref([])
const loading = ref(false)
const syncLoading = ref(false)
const syncCourierLoading = ref(false)
const search = ref('')
const mainTab = ref('list')

const headers = [
  { title: 'Имя', key: 'name' },
  { title: 'Телефон', key: 'phone' },
  { title: 'Роль', key: 'role' },
  { title: 'Ставка', key: 'rate' },
  { title: 'Документы', key: 'documents', sortable: false },
  { title: 'Статус', key: 'status' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'end' },
]

// Документы и детали
const detailsDialog = ref(false)
const selectedEmployee = ref(null)
const detailsTab = ref('info')

const employeeStats = ref({})
const employeeShifts = ref([])
const statsLoading = ref(false)
const employeeShiftsLoading = ref(false)
const statsMode = ref('calendar')

// Состояния для фильтрации и отчетов
const selectedRole = ref('All')
const roles = computed(() => {
  const rs = [...new Set(employees.value.map(e => e.role).filter(Boolean))]

  return ['All', ...rs]
})

const filteredEmployees = computed(() => {
  if (selectedRole.value === 'All') return employees.value

  return employees.value.filter(e => e.role === selectedRole.value)
})

const courierReport = ref([])

const reportLoading = ref(false)
const reportDates = ref({
  from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().substr(0, 10),
  to: new Date().toISOString().substr(0, 10),
})

// Смены (все)
const allShifts = ref([])
const shiftsLoading = ref(false)
const shiftDates = ref({
  from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().substr(0, 10),
  to: new Date().toISOString().substr(0, 10),
})
const selectedEmployeeId = ref(null)

const loadAllShifts = async () => {
  shiftsLoading.value = true
  try {
    let url = `/api/v1/employees/shifts/all?date_from=${shiftDates.value.from}&date_to=${shiftDates.value.to}`
    if (selectedEmployeeId.value) url += `&employee_id=${selectedEmployeeId.value}`
    
    const res = await fetch(url)
    const data = await res.json()
    if (data.status === 'success') {
      allShifts.value = data.data
    }
  } catch (e) {
    console.error('Ошибка загрузки смен:', e)
  } finally {
    shiftsLoading.value = false
  }
}

// Загрузка сотрудников
const loadEmployees = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/employees')
    const data = await response.json()
    if (data.status === 'success') {
      employees.value = data.data
    }
  } catch (error) {
    console.error('Ошибка загрузки сотрудников:', error)
  } finally {
    loading.value = false
  }
}

// Ручная синхронизация
const syncEmployees = async () => {
  syncLoading.value = true
  try {
    const response = await fetch('/api/v1/employees/sync', { method: 'POST' })
    const data = await response.json()
    alert(data.message || 'Синхронизация запущена')

    // Перезагружаем через 5 сек
    setTimeout(loadEmployees, 5000)
  } catch (error) {
    console.error('Ошибка синхронизации:', error)
    alert('Ошибка при запуске синхронизации')
  } finally {
    syncLoading.value = false
  }
}

// Детали сотрудника
const openEmployeeDetails = (employee, tab = 'info') => {
  selectedEmployee.value = employee
  detailsTab.value = tab
  detailsDialog.value = true
  if (tab === 'stats') loadStats()
  if (tab === 'shifts') loadEmployeeShifts()
}

const loadEmployeeShifts = async () => {
  if (!selectedEmployee.value) return
  employeeShiftsLoading.value = true
  try {
    const res = await fetch(`/api/v1/employees/shifts/all?employee_id=${selectedEmployee.value.id}`)
    const data = await res.json()
    if (data.status === 'success') {
      employeeShifts.value = data.data
    }
  } catch (e) {
    console.error('Ошибка загрузки смен сотрудника:', e)
  } finally {
    employeeShiftsLoading.value = false
  }
}

const loadStats = async () => {
  if (!selectedEmployee.value) return
  statsLoading.value = true
  try {
    const res = await fetch(`/api/v1/employees/${selectedEmployee.value.id}/stats`)
    const data = await res.json()
    if (data.status === 'success') {
      employeeStats.value = data.data
    }
  } catch (e) {
    console.error('Ошибка статистики:', e)
  } finally {
    statsLoading.value = false
  }
}

// Загрузка отчета по курьерам
const loadCourierReport = async () => {
  reportLoading.value = true
  try {
    const res = await fetch(`/api/v1/employees/reports/courier-detail?date_from=${reportDates.value.from}&date_to=${reportDates.value.to}`)
    const data = await res.json()
    if (data.status === 'success') {
      courierReport.value = data.data
    }
  } catch (error) {
    console.error('Ошибка загрузки отчета:', error)
  } finally {
    reportLoading.value = false
  }
}

const syncCourierReports = async () => {
  syncCourierLoading.value = true
  try {
    const response = await fetch('/api/v1/employees/sync/couriers', { method: 'POST' })
    const data = await response.json()
    alert(data.message || 'Синхронизация доставок запущена')
  } catch (error) {
    console.error('Ошибка синхронизации доставок:', error)
    alert('Ошибка при запуске синхронизации доставок')
  } finally {
    syncCourierLoading.value = false
  }
}

// Хелперы форматирования
const formatDate = (dateString, full = true) => {
  if (!dateString || dateString === '—') return '—'
  const options = full 
    ? { hour: '2-digit', minute: '2-digit' }
    : {}
  
  return formatDateTime(dateString, options)
}

const hasDocuments = computed(() => (employee) => {
  return employee.document_info && Object.keys(employee.document_info).length > 0
})

const getDocLabel = (key) => {
  const labels = {
    'inn': 'ИНН',
    'snils': 'СНИЛС',
    'code': 'Табельный номер',
    'cardNumber': 'Номер карты / Браслета',
    'birthday': 'Дата рождения'
  }

  return labels[key] || key.toUpperCase()
}

onMounted(() => {
  loadEmployees()
})

watch(detailsTab, (newTab) => {
  if (newTab === 'stats') loadStats()
  if (newTab === 'shifts') loadEmployeeShifts()
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <div class="d-flex justify-space-between align-center mb-6">
        <h2 class="text-h4 font-weight-bold">
          Сотрудники
        </h2>
        <div class="d-flex ga-4">
          <VSelect
            v-model="selectedRole"
            :items="roles"
            label="Фильтр по должности"
            density="compact"
            style="width: 250px"
            hide-details
          />
          <VBtn
            color="primary"
            prepend-icon="bx-refresh"
            :loading="syncLoading"
            @click="syncEmployees"
          >
            Синхронизировать iiko
          </VBtn>
        </div>
      </div>

      <VTabs
        v-model="mainTab"
        class="mb-4"
      >
        <VTab value="list">
          Список сотрудников
        </VTab>
        <VTab
          value="reports"
          @click="loadCourierReport"
        >
          Отчеты по курьерам
        </VTab>
        <VTab
          value="all_shifts"
          @click="loadAllShifts"
        >
          История смен
        </VTab>
      </VTabs>

      <VWindow v-model="mainTab">
        <VWindowItem value="list">
          <VCard>
            <VCardText>
              <VDataTable
                :headers="headers"
                :items="filteredEmployees"
                :loading="loading"
                class="elevation-0"
                hover
              >
                <template #item.rate="{ item }">
                  {{ item.rate ? item.rate + ' ₽/ч' : '—' }}
                </template>
                <template #item.phone="{ item }">
                  {{ item.phone || '—' }}
                </template>

                <template #item.documents="{ item }">
                  <VChip
                    :color="hasDocuments(item) ? 'success' : 'warning'"
                    size="small"
                    variant="outlined"
                    style="cursor: pointer"
                    class="hover-elevation-2"
                    @click="openEmployeeDetails(item, 'documents')"
                  >
                    {{ hasDocuments(item) ? 'Загружены' : 'Нет данных' }}
                  </VChip>
                </template>
                
                <template #item.status="{ item }">
                  <VChip
                    :color="item.status === 'Active' ? 'success' : 'error'"
                    size="small"
                  >
                    {{ item.status === 'Active' ? 'Активен' : 'Удален' }}
                  </VChip>
                </template>
                
                <template #item.actions="{ item }">
                  <VBtn
                    variant="text"
                    color="primary"
                    size="small"
                    prepend-icon="bx-show"
                    @click="openEmployeeDetails(item)"
                  >
                    Подробнее
                  </VBtn>
                </template>
              </VDataTable>
            </VCardText>
          </VCard>
        </VWindowItem>

        <VWindowItem value="reports">
          <VCard>
            <VCardText>
              <div class="d-flex ga-4 mb-6 align-center">
                <VTextField
                  v-model="reportDates.from"
                  type="date"
                  label="С"
                  density="compact"
                  hide-details
                  style="max-width: 200px"
                />
                <VTextField
                  v-model="reportDates.to"
                  type="date"
                  label="По"
                  density="compact"
                  hide-details
                  style="max-width: 200px"
                />
                <VBtn
                  color="primary"
                  variant="tonal"
                  prepend-icon="bx-search"
                  :loading="reportLoading"
                  @click="loadCourierReport"
                >
                  Сформировать отчет
                </VBtn>
                <VBtn
                  color="secondary"
                  variant="tonal"
                  prepend-icon="bx-refresh"
                  :loading="syncCourierLoading"
                  @click="syncCourierReports"
                >
                  Обновить данные из iiko
                </VBtn>
              </div>

              <VDataTable
                :headers="[
                  { title: 'Сотрудник', key: 'courier_name' },
                  { title: 'Доставок', key: 'total_deliveries', align: 'center' },
                  { title: 'Выручка', key: 'total_revenue', align: 'center' },
                  { title: 'Опозданий', key: 'late_count', align: 'center' }
                ]"
                :items="courierReport"
                :loading="reportLoading"
                class="elevation-0 border rounded"
                hover
                show-expand
              >
                <template #item.total_revenue="{ item }">
                  <span class="text-success font-weight-bold">{{ item.total_revenue.toLocaleString('ru-RU') }} ₽</span>
                </template>
                <template #item.late_count="{ item }">
                  <VChip
                    v-if="item.late_count > 0"
                    color="error"
                    size="small"
                  >
                    {{ item.late_count }}
                  </VChip>
                  <span v-else class="text-disabled">0</span>
                </template>
                <template #expanded-row="{ columns, item }">
                  <tr>
                    <td :colspan="columns.length" class="pa-4 bg-light-primary">
                      <div class="mb-4">
                        <strong class="text-subtitle-1">Сводка по зонам:</strong> 
                        <div class="d-flex flex-wrap ga-2 mt-1">
                          <VChip 
                            v-for="(count, zone) in item.zones_summary" 
                            :key="zone"
                            color="info"
                            variant="tonal"
                            size="small"
                          >
                            {{ zone }}: <strong>{{ count }}</strong>
                          </VChip>
                        </div>
                      </div>

                      <div v-for="day in item.days" :key="day.date" class="mb-6">
                        <div class="d-flex align-center mb-2">
                          <VIcon icon="bx-calendar" size="small" class="mr-2" />
                          <strong class="text-h6">{{ day.date }}</strong>
                          <VChip size="x-small" color="primary" class="ml-4">{{ day.deliveries_count }} дост.</VChip>
                          <VChip size="x-small" color="success" class="ml-2">{{ day.revenue.toLocaleString('ru-RU') }} ₽</VChip>
                        </div>

                        <VTable density="compact" class="bg-white border rounded">
                          <thead>
                            <tr>
                              <th class="text-left">№ Заказа</th>
                              <th class="text-left">Адрес</th>
                              <th class="text-left">Клиент</th>
                              <th class="text-left">Зона</th>
                              <th class="text-center">Сумма</th>
                              <th class="text-center">Ожидалось</th>
                              <th class="text-center">Доставлено</th>
                              <th class="text-center">Опоздание</th>
                              <th class="text-left">Состав заказа</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="del in day.deliveries" :key="del.order_num">
                              <td><strong>{{ del.order_num }}</strong></td>
                              <td class="text-caption" style="max-width: 250px">{{ del.address }}</td>
                              <td class="text-caption">
                                 <div v-if="del.customer_name"><strong>{{ del.customer_name }}</strong></div>
                                 <div v-if="del.customer_phone" class="text-grey">{{ del.customer_phone }}</div>
                                 <div v-if="!del.customer_name && !del.customer_phone">—</div>
                               </td>
                              <td><VChip size="x-small" variant="outlined">{{ del.zone }}</VChip></td>
                              <td class="text-center">{{ del.amount }} ₽</td>
                              <td class="text-center text-caption">{{ formatDate(del.expected_time) }}</td>
                              <td class="text-center text-caption">{{ formatDate(del.actual_time) }}</td>
                              <td class="text-center">
                                <VChip 
                                  v-if="del.is_late" 
                                  color="error" 
                                  size="x-small" 
                                  variant="flat"
                                >
                                  +{{ del.delay_minutes }} мин
                                </VChip>
                                <VIcon v-else icon="bx-check-circle" color="success" size="small" />
                              </td>
                              <td class="text-caption" style="max-width: 300px">{{ del.description || '—' }}</td>
                            </tr>
                          </tbody>
                        </VTable>
                      </div>
                    </td>
                  </tr>
                </template>
              </VDataTable>
            </VCardText>
          </VCard>
        </VWindowItem>

        <VWindowItem value="all_shifts">
          <VCard>
            <VCardText>
              <div class="d-flex ga-4 mb-6 align-center flex-wrap">
                <VTextField
                  v-model="shiftDates.from"
                  type="date"
                  label="С"
                  density="compact"
                  hide-details
                  style="max-width: 180px"
                />
                <VTextField
                  v-model="shiftDates.to"
                  type="date"
                  label="По"
                  density="compact"
                  hide-details
                  style="max-width: 180px"
                />
                <VSelect
                  v-model="selectedEmployeeId"
                  :items="employees"
                  item-title="name"
                  item-value="id"
                  label="Сотрудник"
                  density="compact"
                  clearable
                  hide-details
                  style="min-width: 250px"
                />
                <VBtn
                  color="primary"
                  variant="tonal"
                  prepend-icon="bx-search"
                  :loading="shiftsLoading"
                  @click="loadAllShifts"
                >
                  Найти
                </VBtn>
              </div>

              <VDataTable
                :headers="[
                  { title: 'Дата/День', key: 'date', width: '130px' },
                  { title: 'Сотрудник', key: 'employee_name' },
                  { title: 'Роль', key: 'employee_role' },
                  { title: 'Ставка', key: 'employee_rate', align: 'center' },
                  { title: 'Открыта', key: 'time_open', align: 'center' },
                  { title: 'Закрыта', key: 'time_close', align: 'center' },
                  { title: 'Работа (ч)', key: 'work_hours', align: 'center' },
                  { title: 'Выручка (заведение)', key: 'revenue_at_close', align: 'end' },
                  { title: 'Отмены', key: 'cancelled_orders_count', align: 'center' },
                  { title: 'Статус', key: 'status', align: 'center' }
                ]"
                :items="allShifts"
                :loading="shiftsLoading"
                class="elevation-0 border rounded"
                hover
                density="compact"
              >
                <template #item.date="{ item }">
                  <div class="d-flex flex-column">
                    <span class="font-weight-bold">{{ item.date }}</span>
                    <span class="text-caption text-grey">{{ item.day_of_week }}</span>
                  </div>
                </template>

                <template #item.employee_rate="{ item }">
                  <span v-if="item.employee_rate">{{ item.employee_rate }} ₽/ч</span>
                  <span v-else class="text-disabled">—</span>
                </template>

                <template #item.time_open="{ item }">
                  <div class="d-flex flex-column">
                    <span>{{ item.time_open }}</span>
                    <span class="text-caption text-grey">iiko</span>
                  </div>
                </template>

                <template #item.time_close="{ item }">
                  <div v-if="item.time_close" class="d-flex flex-column">
                    <span>{{ item.time_close }}</span>
                    <span class="text-caption text-grey">iiko</span>
                  </div>
                  <span v-else class="text-disabled">—</span>
                </template>
                
                <template #item.revenue_at_close="{ item }">
                  <span v-if="item.revenue_at_close" class="font-weight-bold text-success">
                    {{ item.revenue_at_close.toLocaleString('ru-RU') }} ₽
                  </span>
                  <span v-else class="text-disabled">—</span>
                </template>
                
                <template #item.work_hours="{ item }">
                  {{ Math.floor(item.work_hours) }}ч {{ Math.round((item.work_hours % 1) * 60) }}м
                </template>
                
                <template #item.cancelled_orders_count="{ item }">
                  <VChip
                    v-if="item.cancelled_orders_count > 0"
                    color="error"
                    size="x-small"
                    variant="flat"
                  >
                    {{ item.cancelled_orders_count }}
                  </VChip>
                  <span v-else class="text-disabled">0</span>
                </template>
                
                <template #item.status="{ item }">
                  <VChip
                    :color="item.status === 'OPEN' ? 'warning' : 'success'"
                    size="x-small"
                    variant="tonal"
                  >
                    {{ item.status === 'OPEN' ? 'Открыта' : 'Закрыта' }}
                  </VChip>
                </template>
              </VDataTable>
            </VCardText>
          </VCard>
        </VWindowItem>
      </VWindow>
    </VCol>

    <!-- Модальное окно деталей сотрудника -->
    <VDialog
      v-model="detailsDialog"
      max-width="900px"
      scrollable
    >
      <VCard v-if="selectedEmployee">
        <VCardTitle class="d-flex justify-space-between align-center pa-5 pb-3">
          <div class="text-h5">
            {{ selectedEmployee.name }}
            <VChip
              size="small"
              class="ml-2"
              :color="selectedEmployee.status === 'Active' ? 'success' : 'error'"
            >
              {{ selectedEmployee.status === 'Active' ? 'Активен' : 'Удален' }}
            </VChip>
          </div>
          <VBtn
            icon="bx-x"
            variant="text"
            @click="detailsDialog = false"
          />
        </VCardTitle>

        <VDivider />

        <VTabs v-model="detailsTab">
          <VTab value="info">
            Инфо
          </VTab>
          <VTab value="documents">
            Документы
          </VTab>
          <VTab value="shifts">
            Смены
          </VTab>
          <VTab
            value="stats"
            @click="loadStats"
          >
            Статистика
          </VTab>
        </VTabs>

        <VCardText class="pa-5">
          <VWindow v-model="detailsTab">
            <VWindowItem value="info">
              <VList lines="two">
                <VListItem>
                  <template #prepend>
                    <VIcon icon="bx-phone" />
                  </template>
                  <VListItemTitle>Телефон</VListItemTitle>
                  <VListItemSubtitle>{{ selectedEmployee.phone || '—' }}</VListItemSubtitle>
                </VListItem>
                <VListItem>
                  <template #prepend>
                    <VIcon icon="bx-envelope" />
                  </template>
                  <VListItemTitle>Email</VListItemTitle>
                  <VListItemSubtitle>{{ selectedEmployee.email || '—' }}</VListItemSubtitle>
                </VListItem>
                <VListItem>
                  <template #prepend>
                    <VIcon icon="bx-briefcase" />
                  </template>
                  <VListItemTitle>Должность</VListItemTitle>
                  <VListItemSubtitle>{{ selectedEmployee.role }}</VListItemSubtitle>
                </VListItem>
                <VListItem>
                  <template #prepend>
                    <VIcon icon="bx-money" />
                  </template>
                  <VListItemTitle>Ставка</VListItemTitle>
                  <VListItemSubtitle>{{ selectedEmployee.rate ? selectedEmployee.rate + ' ₽/ч' : '—' }}</VListItemSubtitle>
                </VListItem>
                <VListItem>
                  <template #prepend>
                    <VIcon icon="bx-map" />
                  </template>
                  <VListItemTitle>Адрес</VListItemTitle>
                  <VListItemSubtitle>{{ selectedEmployee.address || '—' }}</VListItemSubtitle>
                </VListItem>
              </VList>
            </VWindowItem>

            <VWindowItem value="documents">
              <VList
                v-if="hasDocuments(selectedEmployee)"
                lines="two"
              >
                <VListItem
                  v-for="(val, key) in selectedEmployee.document_info"
                  :key="key"
                >
                  <template #prepend>
                    <VIcon
                      icon="bx-id-card"
                      size="small"
                      color="primary"
                    />
                  </template>
                  <VListItemTitle class="font-weight-bold">
                    {{ getDocLabel(key) }}
                  </VListItemTitle>
                  <VListItemSubtitle>{{ val || '—' }}</VListItemSubtitle>
                </VListItem>
              </VList>
              <div
                v-else
                class="text-center py-10"
              >
                <VIcon
                  icon="bx-info-circle"
                  size="large"
                  color="warning"
                  class="mb-2"
                />
                <div class="text-subtitle-1">
                  Нет данных по документам
                </div>
                <div class="text-caption">
                  Синхронизируйте данные из iiko для получения ИНН и СНИЛС
                </div>
              </div>
            </VWindowItem>

            <VWindowItem value="shifts">
              <VProgressLinear
                v-if="employeeShiftsLoading"
                indeterminate
                color="primary"
                class="mb-4"
              />
              <VTable
                v-else-if="employeeShifts.length"
                density="compact"
              >
                <thead>
                  <tr>
                    <th>Дата</th>
                    <th>День недели</th>
                    <th>Открыта</th>
                    <th>Закрыта</th>
                    <th>Работа (ч)</th>
                    <th>Выручка</th>
                    <th>Статус</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="shift in employeeShifts"
                    :key="shift.id"
                  >
                    <td>{{ shift.date }}</td>
                    <td>{{ shift.day_of_week }}</td>
                    <td>{{ shift.time_open }}</td>
                    <td>{{ shift.time_close || '—' }}</td>
                    <td>{{ shift.work_hours || '0' }}</td>
                    <td>{{ shift.revenue_at_close ? shift.revenue_at_close.toLocaleString('ru-RU') + ' ₽' : '—' }}</td>
                    <td>
                      <VChip
                        size="x-small"
                        :color="shift.status === 'OPEN' ? 'warning' : 'success'"
                      >
                        {{ shift.status === 'OPEN' ? 'Открыта' : 'Закрыта' }}
                      </VChip>
                    </td>
                  </tr>
                </tbody>
              </VTable>
              <div
                v-else
                class="text-center py-10 text-grey"
              >
                Смен не найдено
              </div>
            </VWindowItem>

            <VWindowItem value="stats">
              <div class="d-flex justify-space-between align-center mb-6">
                <div v-if="employeeStats.total_hours_period !== undefined">
                  <span class="text-h6 mr-4">Всего: <strong>{{ employeeStats.total_hours_period }} ч.</strong></span>
                  <span class="text-h6">Смен: <strong>{{ employeeStats.total_shifts }}</strong></span>
                </div>
                <VBtnToggle
                  v-model="statsMode"
                  density="compact"
                  mandatory
                  @update:model-value="loadStats"
                >
                  <VBtn value="calendar">
                    Текущая неделя
                  </VBtn>
                  <VBtn value="sliding">
                    За 7 дней
                  </VBtn>
                </VBtnToggle>
              </div>

              <VProgressLinear
                v-if="statsLoading"
                indeterminate
                color="primary"
                class="mb-4"
              />

              <div v-if="employeeStats.daily_stats && employeeStats.daily_stats.length">
                <VExpansionPanels variant="accordion">
                  <VExpansionPanel
                    v-for="day in employeeStats.daily_stats"
                    :key="day.date"
                  >
                    <VExpansionPanelTitle>
                      <div class="d-flex justify-space-between w-100 pr-4">
                        <span class="font-weight-bold">{{ formatDate(day.date, false) }}</span>
                        <div class="ga-4 d-flex">
                          <VChip size="x-small" color="primary" variant="tonal">{{ day.shifts.length }} смен</VChip>
                          <VChip size="x-small" color="success" variant="flat">{{ day.total_hours }} ч.</VChip>
                        </div>
                      </div>
                    </VExpansionPanelTitle>
                    <VExpansionPanelText>
                      <!-- Финансовые показатели -->
                      <div
                        v-if="day.financials"
                        class="d-flex ga-4 mb-4 border rounded pa-3 bg-light-primary"
                      >
                        <div class="d-flex flex-column">
                          <span class="text-caption text-grey">Выручка</span>
                          <span class="text-subtitle-1 font-weight-bold">{{ day.financials.revenue }} ₽</span>
                        </div>
                        <VDivider
                          vertical
                          class="mx-2"
                        />
                        <div class="d-flex flex-column">
                          <span class="text-caption text-grey">Скидки</span>
                          <span class="text-subtitle-1 text-error font-weight-bold">-{{ day.financials.discounts }} ₽</span>
                        </div>
                        <VDivider
                          vertical
                          class="mx-2"
                        />
                        <div class="d-flex flex-column">
                          <span class="text-caption text-grey">Чистая выручка</span>
                          <span class="text-subtitle-1 text-success font-weight-bold">{{ day.financials.net_revenue }} ₽</span>
                        </div>
                      </div>

                      <h4 class="text-subtitle-2 font-weight-bold mb-2">
                        Рабочие смены
                      </h4>
                      <VTable
                        density="compact"
                        class="mb-4"
                      >
                        <thead>
                          <tr>
                            <th>Открыта</th>
                            <th>Закрыта</th>
                            <th>Длительность</th>
                            <th>Статус</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr
                            v-for="shift in day.shifts"
                            :key="shift.id"
                          >
                            <td>{{ formatDate(shift.open, true).split(',')[1] }}</td>
                            <td>{{ shift.close ? formatDate(shift.close, true).split(',')[1] : '—' }}</td>
                            <td>{{ shift.hours }} ч.</td>
                            <td>
                              <VChip
                                size="x-small"
                                :color="shift.status === 'OPEN' ? 'warning' : 'success'"
                              >
                                {{ shift.status }}
                              </VChip>
                            </td>
                          </tr>
                        </tbody>
                      </VTable>

                      <!-- Доставки (для курьеров) -->
                      <div v-if="employeeStats.is_courier && day.deliveries && day.deliveries.length">
                        <h4 class="text-subtitle-2 font-weight-bold mb-2 mt-4">
                          Детализация доставок
                        </h4>
                        <VTable
                          density="compact"
                          class="border rounded"
                        >
                          <thead>
                            <tr>
                              <th>№</th>
                              <th>Сумма</th>
                              <th>Зона</th>
                              <th>Адрес</th>
                              <th>Выезд</th>
                              <th>Прибытие</th>
                              <th>План</th>
                              <th>Опоздание</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr
                              v-for="delivery in day.deliveries"
                              :key="delivery.id"
                            >
                              <td class="text-caption">
                                #{{ delivery.id.split('-')[0] }}
                              </td>
                              <td>{{ delivery.amount }} ₽</td>
                              <td>
                                <VChip
                                  size="x-small"
                                  variant="tonal"
                                >
                                  {{ delivery.zone || '—' }}
                                </VChip>
                              </td>
                              <td
                                class="text-caption"
                                style="max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
                              >
                                {{ delivery.address }}
                              </td>
                              <td class="text-caption">
                                {{ delivery.departure ? formatDate(delivery.departure, true).split(',')[1] : '—' }}
                              </td>
                              <td class="text-caption">
                                {{ delivery.arrival ? formatDate(delivery.arrival, true).split(',')[1] : '—' }}
                              </td>
                              <td class="text-caption">
                                {{ delivery.target_time ? formatDate(delivery.target_time, true).split(',')[1] : '—' }}
                              </td>
                              <td>
                                <VChip
                                  v-if="delivery.delay > 0"
                                  color="error"
                                  size="x-small"
                                >
                                  +{{ delivery.delay }} мин
                                </VChip>
                                <VChip
                                  v-else
                                  color="success"
                                  size="x-small"
                                  variant="tonal"
                                >
                                  Вовремя
                                </VChip>
                              </td>
                            </tr>
                          </tbody>
                        </VTable>
                      </div>
                    </VExpansionPanelText>
                  </VExpansionPanel>
                </VExpansionPanels>
              </div>
              <div v-else-if="!statsLoading" class="text-center py-10 text-grey">
                За указанный период смен не найдено
              </div>
            </VWindowItem>
          </VWindow>
        </VCardText>

        <VDivider />

        <VCardActions class="pa-4">
          <VSpacer />
          <VBtn
            color="secondary"
            variant="tonal"
            @click="detailsDialog = false"
          >
            Закрыть
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </VRow>
</template>

<style scoped>
pre {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 4px;
  overflow: auto;
}
.hover-elevation-2:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
</style>
