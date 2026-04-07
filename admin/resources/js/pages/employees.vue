<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const employees = ref([])
const loading = ref(false)
const syncLoading = ref(false)
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
const statsLoading = ref(false)
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
  from: new Date().toISOString().substr(0, 10),
  to: new Date().toISOString().substr(0, 10),
})

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
  loadStats()
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
    const res = await fetch(`/api/v1/employees/reports/couriers?date_from=${reportDates.value.from}&date_to=${reportDates.value.to}`)
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

// Хелперы форматирования
const formatDate = (dateString, full = true) => {
  if (!dateString || dateString === '—') return '—'
  try {
    const date = new Date(dateString)
    if (isNaN(date)) return dateString
    const options = { day: 'numeric', month: 'numeric', year: 'numeric' }
    if (full) {
      options.hour = '2-digit'
      options.minute = '2-digit'
    }

    return new Intl.DateTimeFormat('ru-RU', options).format(date)
  } catch (e) {
    return dateString
  }
}

const hasDocuments = computed(() => (employee) => {
  return employee.document_info && Object.keys(employee.document_info).length > 0
})

onMounted(() => {
  loadEmployees()
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
              </div>

              <VDataTable
                :headers="[
                  { title: 'Сотрудник', key: 'name' },
                  { title: 'Доставок', key: 'deliveries', align: 'center' },
                  { title: 'Часов', key: 'hours', align: 'center' },
                  { title: 'Смен', key: 'shifts_count', align: 'center' }
                ]"
                :items="courierReport"
                :loading="reportLoading"
                class="elevation-0 border rounded"
                hover
              >
                <template #item.hours="{ item }">
                  {{ item.hours }} ч.
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
                  <VListItemTitle>
                    {{ key.toUpperCase() }}
                  </VListItemTitle>
                  <VListItemSubtitle>{{ val || '—' }}</VListItemSubtitle>
                </VListItem>
              </VList>
              <div
                v-else
                class="text-center py-10"
              >
                Нет данных по документам
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
