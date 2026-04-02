<script setup>
import { ref, onMounted, computed, watch } from 'vue'

const employees = ref([])
const loading = ref(false)
const syncLoading = ref(false)
const snackbar = ref({
  show: false,
  message: '',
  color: 'success',
})

// Столбцы главной таблицы
const headers = [
  { title: 'Имя', key: 'name' },
  { title: 'Телефон', key: 'phone' },
  { title: 'Роль', key: 'role' },
  { title: 'Документы', key: 'documents', sortable: false },
  { title: 'Статус', key: 'status' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'end' },
]

// Столбцы для таблицы смен
const shiftsHeaders = [
  { title: 'Открытие', key: 'date_open' },
  { title: 'Закрытие', key: 'date_close' },
  { title: 'Часы', key: 'work_hours' },
  { title: 'Доставки', key: 'deliveries_count' },
  { title: 'Статус', key: 'status' },
]

// Состояние модалки деталей сотрудника
const detailsDialog = ref(false)
const selectedEmployee = ref({})
const activeTab = ref('profile')

// Состояния смен и статистики
const employeeShifts = ref([])
const shiftsLoading = ref(false)

const employeeStats = ref({})
const statsLoading = ref(false)
const statsMode = ref('calendar') // 'calendar' или 'sliding'

// Загрузка сотрудников
const loadEmployees = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/v1/employees/')
    const data = await res.json()
    if (data.status === 'success') {
      employees.value = data.data
    }
  } catch (error) {
    console.error('Ошибка при загрузке сотрудников:', error)
    showSnackbar('Не удалось загрузить сотрудников', 'error')
  } finally {
    loading.value = false
  }
}

// Запуск синхронизации
const syncEmployees = async () => {
  syncLoading.value = true
  try {
    const res = await fetch('/api/v1/employees/sync/', { method: 'POST' })
    const data = await res.json()
    showSnackbar(data.message || 'Синхронизация запущена', 'success')
    setTimeout(loadEmployees, 3000)
  } catch (error) {
    console.error('Ошибка синхронизации:', error)
    showSnackbar('Ошибка синхронизации', 'error')
  } finally {
    syncLoading.value = false
  }
}

const showSnackbar = (text, color = 'success') => {
  snackbar.value = { show: true, message: text, color }
}

// Открытие карточки
const openEmployeeDetails = (employee, tab = 'profile') => {
  selectedEmployee.value = employee
  employeeShifts.value = []
  employeeStats.value = {}
  activeTab.value = tab
  detailsDialog.value = true
  loadShifts(employee.id)
  loadStats()
}

// Загрузка смен
const loadShifts = async (id) => {
  shiftsLoading.value = true
  try {
    const res = await fetch(`/api/v1/employees/${id}/shifts/`)
    const data = await res.json()
    if (data.status === 'success') {
      employeeShifts.value = data.data
    }
  } catch (error) {
    console.error('Ошибка загрузки смен:', error)
  } finally {
    shiftsLoading.value = false
  }
}

// Загрузка статистики
const loadStats = async () => {
  if (!selectedEmployee.value.id) return
  statsLoading.value = true
  try {
    const res = await fetch(`/api/v1/employees/${selectedEmployee.value.id}/stats?mode=${statsMode.value}`)
    const data = await res.json()
    if (data.status === 'success') {
      employeeStats.value = data.data
    }
  } catch (error) {
    console.error('Ошибка загрузки статистики:', error)
  } finally {
    statsLoading.value = false
  }
}

// Следим за сменой режима для статистики
watch(statsMode, () => {
  if (detailsDialog.value) loadStats()
})

// Хелперы форматирования
const formatDate = (dateString, full = true) => {
  if (!dateString) return '—'
  const date = new Date(dateString)
  const options = { day: 'numeric', month: 'numeric', year: 'numeric' }
  if (full) {
    options.hour = '2-digit'
    options.minute = '2-digit'
  }
  return new Intl.DateTimeFormat('ru-RU', options).format(date)
}

// Вычисляемые свойства для документов
const hasDocuments = computed(() => (employee) => {
  return employee.document_info && Object.keys(employee.document_info).length > 0
})

const currentDocs = computed(() => {
  return selectedEmployee.value.document_info || {}
})

onMounted(() => {
  loadEmployees()
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <div class="d-flex justify-space-between align-center mb-6">
        <h2 class="text-h4 font-weight-bold">Сотрудники</h2>
        <VBtn
          color="primary"
          prepend-icon="bx-refresh"
          :loading="syncLoading"
          @click="syncEmployees"
        >
          Синхронизировать
        </VBtn>
      </div>

      <VCard>
        <VCardText>
          <VDataTable
            :headers="headers"
            :items="employees"
            :loading="loading"
            class="elevation-0"
            hover
          >
            <template #item.phone="{ item }">
              {{ item.phone || '—' }}
            </template>

            <template #item.documents="{ item }">
              <VChip
                :color="hasDocuments(item) ? 'success' : 'warning'"
                size="small"
                variant="outlined"
                style="cursor: pointer"
                @click="openEmployeeDetails(item, 'documents')"
                class="hover-elevation-2"
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
                prepend-icon="bx-log-in-circle"
                @click="openEmployeeDetails(item)"
              >
                Подробнее
              </VBtn>
            </template>
          </VDataTable>
        </VCardText>
      </VCard>
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
            <VChip size="small" class="ml-2" :color="selectedEmployee.status === 'Active' ? 'success' : 'error'">
              {{ selectedEmployee.status === 'Active' ? 'Активен' : 'Удален' }}
            </VChip>
          </div>
          <VBtn icon="bx-x" variant="text" @click="detailsDialog = false" />
        </VCardTitle>

        <VCardText class="pa-0">
          <VTabs v-model="activeTab" bg-color="transparent" class="px-5">
            <VTab value="profile">Профиль</VTab>
            <VTab value="documents">Документы</VTab>
            <VTab value="stats">Статистика</VTab>
            <VTab value="shifts">Смены ({{ employeeShifts.length }})</VTab>
          </VTabs>

          <VDivider />

          <VWindow v-model="activeTab" class="pa-5">
            
            <!-- ПРОФИЛЬ -->
            <VWindowItem value="profile">
              <VRow>
                <VCol cols="12" md="6">
                  <VList lines="two">
                    <VListItem>
                      <VListItemTitle class="font-weight-bold">Роль iiko</VListItemTitle>
                      <VListItemSubtitle>{{ selectedEmployee.role || '—' }}</VListItemSubtitle>
                    </VListItem>
                    <VListItem>
                      <VListItemTitle class="font-weight-bold">Телефон</VListItemTitle>
                      <VListItemSubtitle>{{ selectedEmployee.phone || '—' }}</VListItemSubtitle>
                    </VListItem>
                    <VListItem>
                      <VListItemTitle class="font-weight-bold">Email</VListItemTitle>
                      <VListItemSubtitle>{{ selectedEmployee.email || '—' }}</VListItemSubtitle>
                    </VListItem>
                  </VList>
                </VCol>
                <VCol cols="12" md="6">
                  <VList lines="two">
                    <VListItem>
                      <VListItemTitle class="font-weight-bold">Ставка (iiko)</VListItemTitle>
                      <VListItemSubtitle>{{ selectedEmployee.rate ? selectedEmployee.rate + ' ₽/ч' : 'Не указана' }}</VListItemSubtitle>
                    </VListItem>
                    <VListItem>
                      <VListItemTitle class="font-weight-bold">Адрес</VListItemTitle>
                      <VListItemSubtitle>{{ selectedEmployee.address || '—' }}</VListItemSubtitle>
                    </VListItem>
                  </VList>
                </VCol>
              </VRow>
            </VWindowItem>

            <!-- ДОКУМЕНТЫ -->
            <VWindowItem value="documents">
              <VAlert v-if="!hasDocuments(selectedEmployee)" type="info" variant="tonal">
                Конфиденциальные документы (ИНН, СНИЛС, Паспорт) в iiko не заполнены.
              </VAlert>
              <VRow v-else>
                <VCol cols="12" md="6">
                  <VTextField
                    label="ИНН"
                    :value="currentDocs.inn || '—'"
                    readonly
                    variant="underlined"
                    class="mb-3"
                  />
                  <VTextField
                    label="СНИЛС"
                    :value="currentDocs.snils || '—'"
                    readonly
                    variant="underlined"
                    class="mb-3"
                  />
                  <VTextField
                    label="Медкнижка"
                    :value="currentDocs.med_book_number || '—'"
                    readonly
                    variant="underlined"
                  />
                  <div class="text-caption text-medium-emphasis mt-n2 mb-4" v-if="currentDocs.med_book_expires">
                    Годен до: {{ formatDate(currentDocs.med_book_expires, false) }}
                  </div>
                </VCol>
                <VCol cols="12" md="6">
                  <h4 class="text-subtitle-1 font-weight-bold mb-2">Паспорт</h4>
                  <VTextField
                    label="Серия и номер"
                    :value="(currentDocs.passport_series || '') + ' ' + (currentDocs.passport_number || '')"
                    readonly
                    variant="underlined"
                    class="mb-3"
                  />
                  <div class="text-caption text-medium-emphasis mt-n2 mb-4">
                    Выдан: {{ formatDate(currentDocs.passport_issued_date, false) }} <br/>
                    Кем выдан: {{ currentDocs.passport_issued_by || '—' }} <br/>
                    Код подр: {{ currentDocs.passport_department_code || '—' }}
                  </div>
                  <VTextField
                    label="Гражданство"
                    :value="currentDocs.citizenship || '—'"
                    readonly
                    variant="underlined"
                  />
                </VCol>
              </VRow>
            </VWindowItem>

            <!-- СТАТИСТИКА -->
            <VWindowItem value="stats">
              <div class="d-flex align-center mb-6">
                <span class="mr-4 font-weight-bold">Режим расчета:</span>
                <VRadioGroup v-model="statsMode" inline hide-details>
                  <VRadio label="Текущая неделя (Пн-Вс)" value="calendar" />
                  <VRadio label="Последние 7 дней" value="sliding" />
                </VRadioGroup>
              </div>

              <VAlert v-if="statsLoading" color="primary" variant="tonal" class="mb-4">
                <VProgressCircular indeterminate size="20" class="mr-2" /> Загрузка статистики...
              </VAlert>

              <VRow v-else>
                <VCol cols="12" md="4">
                  <VCard variant="outlined" class="text-center py-4 bg-primary-lighten-5">
                    <div class="text-h3 text-primary mb-1">{{ employeeStats.total_hours?.toFixed(1) || 0 }}</div>
                    <div class="text-subtitle-2">Отработано часов</div>
                  </VCard>
                </VCol>
                <VCol cols="12" md="4">
                  <VCard variant="outlined" class="text-center py-4 bg-info-lighten-5">
                    <div class="text-h3 text-info mb-1">{{ employeeStats.total_shifts || 0 }}</div>
                    <div class="text-subtitle-2">Количество смен</div>
                  </VCard>
                </VCol>
                <VCol cols="12" md="4">
                  <VCard variant="outlined" class="text-center py-4 bg-success-lighten-5">
                    <div class="text-h3 text-success mb-1">{{ employeeStats.total_deliveries || 0 }}</div>
                    <div class="text-subtitle-2">Выполнено доставок</div>
                  </VCard>
                </VCol>
              </VRow>
            </VWindowItem>

            <!-- СМЕНЫ -->
            <VWindowItem value="shifts">
              <VDataTable
                :headers="shiftsHeaders"
                :items="employeeShifts"
                :loading="shiftsLoading"
                class="elevation-0 border rounded"
                :items-per-page="5"
              >
                <template #item.date_open="{ item }">
                  {{ formatDate(item.date_open) }}
                </template>
                <template #item.date_close="{ item }">
                  {{ formatDate(item.date_close) }}
                </template>
                <template #item.work_hours="{ item }">
                  {{ item.work_hours ? item.work_hours.toFixed(2) : '—' }}
                </template>
                <template #item.deliveries_count="{ item }">
                  {{ item.deliveries_count || '—' }}
                </template>
                <template #item.status="{ item }">
                  <VChip
                    :color="item.status === 'CLOSED' ? 'default' : 'success'"
                    size="small"
                  >
                    {{ item.status === 'CLOSED' ? 'Закрыта' : 'Открыта' }}
                  </VChip>
                </template>
              </VDataTable>
            </VWindowItem>

          </VWindow>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-4">
          <VSpacer />
          <VBtn color="secondary" variant="flat" @click="detailsDialog = false">Закрыть</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <VSnackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      location="top right"
      timeout="3000"
    >
      {{ snackbar.message }}
    </VSnackbar>
  </VRow>
</template>
