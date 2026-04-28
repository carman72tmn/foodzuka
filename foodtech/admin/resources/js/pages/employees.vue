<template>
  <div class="employees-page">
    <!-- Заголовок -->
    <div class="page-header">
      <h1>Сотрудники</h1>
      <v-btn color="primary" :loading="syncLoading" prepend-icon="bx-refresh" @click="syncAll">
        Синхронизировать
      </v-btn>
    </div>

    <!-- Главные вкладки -->
    <v-tabs v-model="mainTab" color="primary" class="mb-4">
      <v-tab value="list">📋 Список</v-tab>
      <v-tab value="couriers">🚴 Курьеры</v-tab>
      <v-tab value="admins">🏪 Администраторы</v-tab>
      <v-tab value="weekly">📅 Неделя</v-tab>
    </v-tabs>

    <v-window v-model="mainTab">
      <!-- =============================== СПИСОК =============================== -->
      <v-window-item value="list">
        <v-card class="pa-4">
          <div class="d-flex gap-4 mb-4 flex-wrap">
            <v-text-field v-model="search" label="Поиск" prepend-inner-icon="bx-search" hide-details density="compact" style="max-width:300px" clearable />
            <v-select v-model="selectedRole" :items="roleOptions" label="Роль" hide-details density="compact" style="max-width:200px" />
            <v-select v-model="selectedType" :items="typeOptions" label="Тип" hide-details density="compact" style="max-width:180px" />
          </div>

          <v-data-table
            :headers="listHeaders"
            :items="filteredEmployees"
            :loading="loading"
            :search="search"
            density="compact"
            @click:row="(_, {item}) => openDetails(item)"
          >
            <template #item.name="{ item }">
              <div class="d-flex align-center gap-2">
                <v-avatar size="32" :color="item.is_courier ? 'orange' : 'blue'" class="text-white text-caption">
                  {{ item.name[0] }}
                </v-avatar>
                {{ item.name }}
              </div>
            </template>
            <template #item.role="{ item }">
              <v-chip size="small" :color="item.is_courier ? 'orange' : item.is_admin ? 'blue' : 'grey'">
                {{ item.role || '—' }}
              </v-chip>
            </template>
            <template #item.status="{ item }">
              <v-chip size="small" :color="item.status === 'Active' ? 'success' : 'grey'">
                {{ item.status === 'Active' ? 'Активен' : 'Уволен' }}
              </v-chip>
            </template>
            <template #item.actions="{ item }">
              <v-btn icon size="small" variant="text" @click.stop="openDetails(item)">
                <v-icon>bx-show</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-window-item>

      <!-- =============================== КУРЬЕРЫ ============================== -->
      <v-window-item value="couriers">
        <v-card class="pa-4 mb-4">
          <div class="d-flex gap-4 align-center flex-wrap">
            <v-text-field v-model="reportDates.from" type="date" label="С" hide-details density="compact" style="max-width:180px" />
            <v-text-field v-model="reportDates.to" type="date" label="По" hide-details density="compact" style="max-width:180px" />
            <v-btn color="primary" :loading="reportLoading" @click="loadCourierReport">Загрузить</v-btn>
          </div>
        </v-card>

        <div v-if="courierReport.length === 0 && !reportLoading" class="text-center py-8 text-medium-emphasis">
          Выберите даты и нажмите «Загрузить»
        </div>

        <v-expansion-panels v-if="courierReport.length > 0" multiple>
          <v-expansion-panel v-for="courier in courierReport" :key="courier.courier_id">
            <v-expansion-panel-title>
              <div class="d-flex align-center gap-4 w-100">
                <v-avatar color="orange" size="36" class="text-white font-weight-bold">{{ courier.courier_name[0] }}</v-avatar>
                <div>
                  <div class="font-weight-bold">{{ courier.courier_name }}</div>
                  <div class="text-caption text-medium-emphasis">{{ courier.total_deliveries }} доставок · {{ formatRub(courier.total_revenue) }} · {{ courier.late_count }} опозданий</div>
                </div>
                <v-spacer />
                <div class="d-flex gap-2 mr-4">
                  <v-chip v-for="(cnt, zone) in courier.zones_summary" :key="zone" size="small" color="blue-lighten-4">
                    {{ zone }}: {{ cnt }}
                  </v-chip>
                </div>
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <div v-for="day in courier.days" :key="day.date" class="mb-4">
                <div class="d-flex align-center mb-2">
                  <span class="font-weight-medium">{{ formatDate(day.date) }}</span>
                  <v-chip size="x-small" class="ml-2" color="orange">{{ day.deliveries_count }} доставок</v-chip>
                  <v-chip size="x-small" class="ml-1" color="green">{{ formatRub(day.revenue) }}</v-chip>
                </div>
                <v-table density="compact">
                  <thead>
                    <tr>
                      <th>№</th><th>Адрес</th><th>Зона</th><th>Сумма</th>
                      <th>Отправлен</th><th>Доставлен</th><th>Ожидалось</th><th>Задержка</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="del in day.deliveries" :key="del.id">
                      <td>{{ del.order_num }}</td>
                      <td>{{ del.address || '—' }}</td>
                      <td><v-chip size="x-small" color="blue-lighten-4">{{ del.zone }}</v-chip></td>
                      <td>{{ formatRub(del.amount) }}</td>
                      <td>{{ del.departure_time || '—' }}</td>
                      <td>{{ del.arrival_time || '—' }}</td>
                      <td>{{ del.expected_time || '—' }}</td>
                      <td>
                        <v-chip v-if="del.delay_minutes !== null" size="x-small" :color="del.is_late ? 'red' : 'green'">
                          {{ del.is_late ? '+' : '' }}{{ del.delay_minutes }} мин
                        </v-chip>
                        <span v-else>—</span>
                      </td>
                    </tr>
                  </tbody>
                </v-table>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-window-item>

      <!-- =============================== АДМИНИСТРАТОРЫ ======================= -->
      <v-window-item value="admins">
        <v-card class="pa-4 mb-4">
          <div class="d-flex gap-4 align-center flex-wrap">
            <v-text-field v-model="adminDates.from" type="date" label="С" hide-details density="compact" style="max-width:180px" />
            <v-text-field v-model="adminDates.to" type="date" label="По" hide-details density="compact" style="max-width:180px" />
            <v-btn color="primary" :loading="adminLoading" @click="loadAdminShifts">Загрузить</v-btn>
          </div>
        </v-card>

        <v-card v-if="adminShifts.length > 0">
          <v-data-table :headers="adminHeaders" :items="adminShifts" density="compact">
            <template #item.employee_name="{ item }">
              <div class="d-flex align-center gap-2">
                <v-avatar size="28" color="blue" class="text-white text-caption">{{ item.employee_name[0] }}</v-avatar>
                {{ item.employee_name }}
              </div>
            </template>
            <template #item.status="{ item }">
              <v-chip size="x-small" :color="item.status === 'CLOSED' ? 'success' : 'warning'">
                {{ item.status === 'CLOSED' ? 'Закрыта' : 'Открыта' }}
              </v-chip>
            </template>
            <template #item.revenue_at_close="{ item }">
              <span class="font-weight-medium">{{ formatRub(item.revenue_at_close) }}</span>
            </template>
            <template #item.work_hours="{ item }">{{ item.work_hours }}ч</template>
          </v-data-table>
        </v-card>
        <div v-else-if="!adminLoading" class="text-center py-8 text-medium-emphasis">
          Выберите даты и нажмите «Загрузить»
        </div>
      </v-window-item>

      <!-- =============================== НЕДЕЛЯ =============================== -->
      <v-window-item value="weekly">
        <v-card class="pa-4 mb-4">
          <div class="d-flex align-center gap-4">
            <v-btn icon variant="text" @click="prevWeek"><v-icon>bx-chevron-left</v-icon></v-btn>
            <span class="font-weight-medium">{{ weekLabel }}</span>
            <v-btn icon variant="text" @click="nextWeek"><v-icon>bx-chevron-right</v-icon></v-btn>
            <v-btn size="small" variant="outlined" @click="goCurrentWeek">Текущая</v-btn>
            <v-btn color="primary" size="small" :loading="weeklyLoading" @click="loadWeekly">Обновить</v-btn>
          </div>
        </v-card>

        <v-card v-if="weeklyData" class="overflow-x-auto">
          <table class="weekly-grid">
            <thead>
              <tr>
                <th class="emp-col">Сотрудник</th>
                <th v-for="(label, i) in weeklyData.day_labels" :key="i" class="day-col">
                  <div>{{ label }}</div>
                  <div class="text-caption text-medium-emphasis">{{ formatDateShort(weeklyData.week_dates[i]) }}</div>
                </th>
                <th>Итого</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="emp in weeklyData.data" :key="emp.employee_id">
                <td class="emp-col">
                  <div class="d-flex align-center gap-2">
                    <v-avatar size="28" :color="emp.is_courier ? 'orange' : 'blue'" class="text-white text-caption">
                      {{ emp.employee_name[0] }}
                    </v-avatar>
                    <div>
                      <div class="text-body-2 font-weight-medium">{{ emp.employee_name }}</div>
                      <div class="text-caption text-medium-emphasis">{{ emp.employee_role }}</div>
                    </div>
                  </div>
                </td>
                <td v-for="day in emp.days" :key="day.date" class="day-cell" :class="{ 'worked': day.worked, 'off': !day.worked }">
                  <v-tooltip :text="dayTooltip(day, emp)" location="top">
                    <template #activator="{ props }">
                      <div v-bind="props" class="cell-inner">
                        <template v-if="day.worked">
                          <div class="text-caption font-weight-medium">{{ day.work_hours }}ч</div>
                          <div v-if="emp.is_courier && day.deliveries_count" class="text-caption">🚴 {{ day.deliveries_count }}</div>
                          <div v-if="day.revenue" class="text-caption text-green">{{ formatRubShort(day.revenue) }}</div>
                        </template>
                        <template v-else>
                          <div class="text-caption text-disabled">—</div>
                        </template>
                      </div>
                    </template>
                  </v-tooltip>
                </td>
                <td class="text-center">
                  <div class="text-caption font-weight-bold">{{ emp.total_hours }}ч</div>
                  <div v-if="emp.is_courier" class="text-caption text-orange">🚴 {{ emp.total_deliveries }}</div>
                  <div class="text-caption text-green">{{ formatRubShort(emp.total_revenue) }}</div>
                </td>
              </tr>
            </tbody>
          </table>
        </v-card>
        <div v-else-if="!weeklyLoading" class="text-center py-8 text-medium-emphasis">Нажмите «Обновить»</div>
      </v-window-item>
    </v-window>

    <!-- Диалог карточки сотрудника -->
    <v-dialog v-model="detailsDialog" max-width="700">
      <v-card v-if="selectedEmployee">
        <v-card-title class="d-flex align-center gap-3 pa-4">
          <v-avatar size="48" :color="selectedEmployee.is_courier ? 'orange' : 'blue'" class="text-white text-h6">
            {{ selectedEmployee.name[0] }}
          </v-avatar>
          <div>
            <div>{{ selectedEmployee.name }}</div>
            <div class="text-caption text-medium-emphasis">{{ selectedEmployee.role }}</div>
          </div>
        </v-card-title>

        <v-tabs v-model="detailsTab" density="compact">
          <v-tab value="info">Данные</v-tab>
          <v-tab value="stats">Статистика</v-tab>
        </v-tabs>

        <v-window v-model="detailsTab" class="pa-4">
          <v-window-item value="info">
            <v-list density="compact">
              <v-list-item title="Телефон" :subtitle="selectedEmployee.phone || '—'" prepend-icon="bx-phone" />
              <v-list-item title="Email" :subtitle="selectedEmployee.email || '—'" prepend-icon="bx-envelope" />
              <v-list-item title="Ставка" :subtitle="selectedEmployee.rate ? selectedEmployee.rate + ' ₽/ч' : '—'" prepend-icon="bx-money" />
              <v-list-item title="Статус" :subtitle="selectedEmployee.status === 'Active' ? 'Активен' : 'Уволен'" prepend-icon="bx-user" />
            </v-list>
          </v-window-item>

          <v-window-item value="stats">
            <div class="d-flex gap-2 mb-4">
              <v-btn-toggle v-model="statsMode" mandatory density="compact">
                <v-btn value="calendar" size="small">Текущая неделя</v-btn>
                <v-btn value="sliding" size="small">7 дней</v-btn>
              </v-btn-toggle>
            </div>
            <v-progress-circular v-if="statsLoading" indeterminate />
            <div v-else-if="employeeStats.daily_stats">
              <div class="d-flex gap-4 mb-4">
                <v-card variant="tonal" color="blue" class="pa-3 flex-1">
                  <div class="text-h6">{{ employeeStats.total_shifts }}</div>
                  <div class="text-caption">смен</div>
                </v-card>
                <v-card variant="tonal" color="green" class="pa-3 flex-1">
                  <div class="text-h6">{{ employeeStats.total_hours_period }}ч</div>
                  <div class="text-caption">часов</div>
                </v-card>
                <v-card variant="tonal" color="orange" class="pa-3 flex-1">
                  <div class="text-h6">{{ formatRub(employeeStats.total_revenue) }}</div>
                  <div class="text-caption">выручка</div>
                </v-card>
              </div>
              <div v-for="day in employeeStats.daily_stats" :key="day.date" class="mb-2">
                <div class="d-flex justify-space-between text-body-2">
                  <span>{{ formatDate(day.date) }}</span>
                  <span>{{ day.total_hours }}ч · {{ formatRub(day.revenue) }}</span>
                </div>
                <v-divider class="mt-1" />
              </div>
            </div>
          </v-window-item>
        </v-window>

        <v-card-actions>
          <v-spacer /><v-btn @click="detailsDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

// ── данные ──────────────────────────────────────────────
const employees = ref([])
const loading = ref(false)
const syncLoading = ref(false)
const search = ref('')
const mainTab = ref('list')

const selectedRole = ref('Все')
const selectedType = ref('Все')

const typeOptions = ['Все', 'Курьеры', 'Администраторы', 'Остальные']

const roleOptions = computed(() => {
  const rs = [...new Set(employees.value.map(e => e.role).filter(Boolean))]
  return ['Все', ...rs]
})

const filteredEmployees = computed(() => {
  let list = employees.value
  if (selectedRole.value !== 'Все') list = list.filter(e => e.role === selectedRole.value)
  if (selectedType.value === 'Курьеры') list = list.filter(e => e.is_courier)
  else if (selectedType.value === 'Администраторы') list = list.filter(e => e.is_admin)
  else if (selectedType.value === 'Остальные') list = list.filter(e => !e.is_courier && !e.is_admin)
  return list
})

const listHeaders = [
  { title: 'Имя', key: 'name' },
  { title: 'Телефон', key: 'phone' },
  { title: 'Роль', key: 'role' },
  { title: 'Ставка', key: 'rate' },
  { title: 'Статус', key: 'status' },
  { title: '', key: 'actions', sortable: false, align: 'end' },
]

// ── детали сотрудника ────────────────────────────────────
const detailsDialog = ref(false)
const selectedEmployee = ref(null)
const detailsTab = ref('info')
const employeeStats = ref({})
const statsLoading = ref(false)
const statsMode = ref('calendar')

const openDetails = (emp) => {
  selectedEmployee.value = emp
  detailsTab.value = 'info'
  detailsDialog.value = true
  loadStats()
}

const loadStats = async () => {
  if (!selectedEmployee.value) return
  statsLoading.value = true
  try {
    const res = await fetch(`/api/v1/employees/${selectedEmployee.value.id}/stats?mode=${statsMode.value}`)
    const data = await res.json()
    if (data.status === 'success') employeeStats.value = data.data
  } catch (e) { console.error(e) } finally { statsLoading.value = false }
}
watch(statsMode, loadStats)

// ── загрузка сотрудников ─────────────────────────────────
const loadEmployees = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/v1/employees/')
    const data = await res.json()
    if (data.status === 'success') employees.value = data.data
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const syncAll = async () => {
  syncLoading.value = true
  try {
    const res = await fetch('/api/v1/employees/sync/', { method: 'POST' })
    const data = await res.json()
    alert(data.message || 'Синхронизация запущена')
    setTimeout(loadEmployees, 6000)
  } catch (e) { alert('Ошибка синхронизации') } finally { syncLoading.value = false }
}

// ── отчёт курьеров ───────────────────────────────────────
const courierReport = ref([])
const reportLoading = ref(false)
const today = new Date().toISOString().substr(0, 10)
const weekAgo = new Date(Date.now() - 7 * 86400000).toISOString().substr(0, 10)
const reportDates = ref({ from: weekAgo, to: today })

const loadCourierReport = async () => {
  reportLoading.value = true
  try {
    const res = await fetch(`/api/v1/employees/reports/courier-detail?date_from=${reportDates.value.from}&date_to=${reportDates.value.to}`)
    const data = await res.json()
    if (data.status === 'success') courierReport.value = data.data
  } catch (e) { console.error(e) } finally { reportLoading.value = false }
}

// ── смены администраторов ────────────────────────────────
const adminShifts = ref([])
const adminLoading = ref(false)
const adminDates = ref({ from: weekAgo, to: today })

const adminHeaders = [
  { title: 'Сотрудник', key: 'employee_name' },
  { title: 'Роль', key: 'employee_role' },
  { title: 'Дата', key: 'date' },
  { title: 'День нед.', key: 'day_of_week' },
  { title: 'Открытие', key: 'time_open' },
  { title: 'Закрытие', key: 'time_close' },
  { title: 'Часов', key: 'work_hours' },
  { title: 'Выручка', key: 'revenue_at_close' },
  { title: 'Отмены', key: 'cancelled_orders_count' },
  { title: 'Статус', key: 'status' },
]

const loadAdminShifts = async () => {
  adminLoading.value = true
  try {
    const res = await fetch(`/api/v1/employees/reports/admin-shifts?date_from=${adminDates.value.from}&date_to=${adminDates.value.to}`)
    const data = await res.json()
    if (data.status === 'success') adminShifts.value = data.data
  } catch (e) { console.error(e) } finally { adminLoading.value = false }
}

// ── еженедельная сетка ───────────────────────────────────
const weeklyData = ref(null)
const weeklyLoading = ref(false)
const weekStart = ref(getMonday(new Date()).toISOString().substr(0, 10))

function getMonday(d) {
  const day = d.getDay() || 7
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() - day + 1)
}

const weekLabel = computed(() => {
  if (!weekStart.value) return ''
  const ws = new Date(weekStart.value)
  const we = new Date(ws); we.setDate(we.getDate() + 6)
  return `${ws.toLocaleDateString('ru', { day: 'numeric', month: 'long' })} — ${we.toLocaleDateString('ru', { day: 'numeric', month: 'long', year: 'numeric' })}`
})

const prevWeek = () => {
  const d = new Date(weekStart.value); d.setDate(d.getDate() - 7)
  weekStart.value = d.toISOString().substr(0, 10)
  loadWeekly()
}
const nextWeek = () => {
  const d = new Date(weekStart.value); d.setDate(d.getDate() + 7)
  weekStart.value = d.toISOString().substr(0, 10)
  loadWeekly()
}
const goCurrentWeek = () => {
  weekStart.value = getMonday(new Date()).toISOString().substr(0, 10)
  loadWeekly()
}

const loadWeekly = async () => {
  weeklyLoading.value = true
  try {
    const res = await fetch(`/api/v1/employees/reports/weekly?week_start=${weekStart.value}`)
    const data = await res.json()
    if (data.status === 'success') weeklyData.value = data
  } catch (e) { console.error(e) } finally { weeklyLoading.value = false }
}

// ── форматирование ───────────────────────────────────────
const formatRub = (v) => v ? Math.round(v).toLocaleString('ru') + ' ₽' : '—'
const formatRubShort = (v) => {
  if (!v) return '—'
  return v >= 1000 ? (v / 1000).toFixed(1) + 'к ₽' : Math.round(v) + ' ₽'
}
const formatDate = (iso) => {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('ru', { day: 'numeric', month: 'long', weekday: 'short' })
}
const formatDateShort = (iso) => {
  if (!iso) return ''
  return new Date(iso + 'T00:00:00').toLocaleDateString('ru', { day: 'numeric', month: 'short' })
}
const dayTooltip = (day, emp) => {
  if (!day.worked) return 'Выходной'
  let t = `${day.work_hours}ч работы`
  if (emp.is_courier && day.deliveries_count) t += ` · ${day.deliveries_count} доставок`
  if (day.zones_str) t += ` · ${day.zones_str}`
  if (day.revenue) t += ` · ${formatRubShort(day.revenue)}`
  return t
}

onMounted(loadEmployees)
</script>

<style scoped>
.employees-page { padding: 24px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h1 { font-size: 1.5rem; font-weight: 700; margin: 0; }
.weekly-grid { width: 100%; border-collapse: collapse; min-width: 900px; }
.weekly-grid th, .weekly-grid td { border: 1px solid rgba(0,0,0,0.08); padding: 4px 8px; text-align: center; }
.weekly-grid thead th { background: rgba(0,0,0,0.04); font-size: 0.75rem; }
.emp-col { text-align: left !important; min-width: 180px; }
.day-col { min-width: 90px; }
.day-cell { min-height: 50px; vertical-align: top; }
.day-cell.worked { background: rgba(76, 175, 80, 0.08); }
.day-cell.off { background: transparent; }
.cell-inner { min-height: 44px; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: default; }
.text-orange { color: #fb8c00; }
.text-green { color: #4caf50; }
.flex-1 { flex: 1; }
</style>
