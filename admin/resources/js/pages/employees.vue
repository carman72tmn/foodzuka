<script setup>
import { ref, onMounted } from 'vue'

const employees = ref([])
const loading = ref(false)
const syncLoading = ref(false)
const snackbar = ref({
  show: false,
  message: '',
  color: 'success',
})

// Столбцы таблицы
const headers = [
  { title: 'Имя', key: 'name' },
  { title: 'Телефон', key: 'phone' },
  { title: 'Роль', key: 'role' },
  { title: 'Статус', key: 'status' },
  { title: 'Смены', key: 'shifts', sortable: false },
]

const loadEmployees = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/v1/employees')
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

const syncEmployees = async () => {
  syncLoading.value = true
  try {
    const res = await fetch('/api/v1/employees/sync', { method: 'POST' })
    const data = await res.json()
    showSnackbar(data.message || 'Синхронизация запущена', 'success')
    // Можно обновить список с задержкой, так как синхронизация идет в фоне
    setTimeout(loadEmployees, 3000)
  } catch (error) {
    console.error('Ошибка синхронизации:', error)
    showSnackbar('Ошибка синхронизации', 'error')
  } finally {
    syncLoading.value = false
  }
}

const showSnackbar = (text, color = 'success') => {
  snackbar.value = {
    show: true,
    message: text,
    color,
  }
}

// Загрузка смен
const shiftsDialog = ref(false)
const selectedEmployee = ref({})
const shiftsLoading = ref(false)
const employeeShifts = ref([])

const shiftsHeaders = [
  { title: 'ID Смены', key: 'iiko_id' },
  { title: 'Открытие', key: 'date_open' },
  { title: 'Закрытие', key: 'date_close' },
  { title: 'Статус', key: 'status' },
]

const openShiftsDialog = async (employee) => {
  selectedEmployee.value = employee
  shiftsDialog.value = true
  shiftsLoading.value = true
  
  try {
    const res = await fetch(`/api/v1/employees/${employee.id}/shifts`)
    const data = await res.json()
    if (data.status === 'success') {
      employeeShifts.value = data.data
    }
  } catch (error) {
    console.error('Ошибка загрузки смен:', error)
    showSnackbar('Не удалось загрузить смены', 'error')
  } finally {
    shiftsLoading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '—'
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('ru-RU', { 
    day: 'numeric', month: 'numeric', year: 'numeric', 
    hour: 'numeric', minute: 'numeric' 
  }).format(date)
}

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
          Синхронизировать с iiko
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
            
            <template #item.status="{ item }">
              <VChip
                :color="item.status === 'Active' ? 'success' : 'error'"
                size="small"
                v-bind="props"
              >
                {{ item.status === 'Active' ? 'Активен' : 'Удален' }}
              </VChip>
            </template>
            
            <template #item.shifts="{ item }">
              <VBtn
                variant="text"
                color="info"
                size="small"
                prepend-icon="bx-calendar"
                @click="openShiftsDialog(item)"
              >
                Смены
              </VBtn>
            </template>
          </VDataTable>
        </VCardText>
      </VCard>
    </VCol>

    <!-- Диалоговое окно со сменами -->
    <VDialog
      v-model="shiftsDialog"
      max-width="800px"
    >
      <VCard>
        <VCardTitle class="d-flex justify-space-between align-center pa-4">
          <span>Смены: {{ selectedEmployee.name }}</span>
          <VBtn
            icon="bx-x"
            variant="text"
            @click="shiftsDialog = false"
          />
        </VCardTitle>
        <VCardText>
          <VDataTable
            :headers="shiftsHeaders"
            :items="employeeShifts"
            :loading="shiftsLoading"
            class="elevation-0"
          >
             <template #item.date_open="{ item }">
              {{ formatDate(item.date_open) }}
            </template>
             <template #item.date_close="{ item }">
              {{ formatDate(item.date_close) }}
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
        </VCardText>
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
