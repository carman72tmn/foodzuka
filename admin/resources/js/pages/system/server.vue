<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { getAuthHeaders } from '@/utils/auth'
import VueApexCharts from 'vue3-apexcharts'

const cpuSeries = ref([{ name: 'CPU', data: [] }])
const ramSeries = ref([{ name: 'RAM', data: [] }])

const cpuChartOptions = ref({
  chart: {
    type: 'line',
    animations: {
      enabled: true,
      easing: 'linear',
      dynamicAnimation: {
        speed: 1000
      }
    },
    toolbar: { show: false },
    zoom: { enabled: false }
  },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2 },
  xaxis: {
    type: 'datetime',
    range: 60000,
  },
  yaxis: {
    max: 100,
    min: 0,
    labels: { formatter: (val) => val.toFixed(0) + '%' }
  },
  colors: ['#00E396']
})

const ramChartOptions = ref({
  chart: {
    type: 'line',
    animations: {
      enabled: true,
      easing: 'linear',
      dynamicAnimation: {
        speed: 1000
      }
    },
    toolbar: { show: false },
    zoom: { enabled: false }
  },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2 },
  xaxis: {
    type: 'datetime',
    range: 60000,
  },
  yaxis: {
    max: 100,
    min: 0,
    labels: { formatter: (val) => val.toFixed(0) + '%' }
  },
  colors: ['#FF4560']
})

const status = ref(null)
const containers = ref([])
const error = ref(null)
const loadingAction = ref(false)
const actionMessage = ref('')
const snackbar = ref(false)
const snackbarColor = ref('success')
const isRebootDialogOpen = ref(false)
const isVacuumDialogOpen = ref(false)
let interval = null

const formatBytes = (bytes, decimals = 2) => {
  if (!bytes || bytes === 0) return '0 Bytes'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

const showNotify = (msg, color = 'success') => {
  actionMessage.value = msg
  snackbarColor.value = color
  snackbar.value = true
}

const fetchData = async () => {
  try {
    const { data } = await axios.get('/api/v1/system/server-status', {
      headers: getAuthHeaders()
    })
    if (data.status === 'success') {
      error.value = null
      status.value = data
      
      const now = new Date().getTime()
      
      // Update CPU
      const newCpuData = [...cpuSeries.value[0].data, [now, data.cpu.percent]]
      if (newCpuData.length > 60) newCpuData.shift()
      cpuSeries.value = [{ name: 'CPU', data: newCpuData }]
      
      // Update RAM
      const newRamData = [...ramSeries.value[0].data, [now, data.ram.percent]]
      if (newRamData.length > 60) newRamData.shift()
      ramSeries.value = [{ name: 'RAM', data: newRamData }]
    }
  } catch (err) {
    console.error('Error fetching server status:', err)
    error.value = 'Ошибка загрузки данных о сервере.'
  }
}

const fetchContainers = async () => {
  try {
    const { data } = await axios.get('/api/v1/system/server-containers', {
      headers: getAuthHeaders()
    })
    if (data.status === 'success') {
      containers.value = data.containers || []
    }
  } catch (err) {
    console.error('Error fetching containers:', err)
  }
}

// 1. Очистка диска
const handleCleanupDisk = async () => {
  loadingAction.value = true
  try {
    const { data } = await axios.post('/api/v1/system/server/cleanup-disk', {}, {
      headers: getAuthHeaders()
    })
    if (data.status === 'success') {
      const detailsMsg = data.details && data.details.length ? data.details.join('; ') : ''
      showNotify(`Очистка завершена! ${detailsMsg}`, 'success')
      await fetchData()
      await fetchContainers()
    }
  } catch (err) {
    showNotify(err.response?.data?.detail || 'Ошибка очистки диска', 'error')
  } finally {
    loadingAction.value = false
  }
}

// 2. Сжатие базы данных (VACUUM FULL)
const handleVacuumDb = async () => {
  isVacuumDialogOpen.value = false
  loadingAction.value = true
  try {
    const { data } = await axios.post('/api/v1/system/server/vacuum-db', {}, {
      headers: getAuthHeaders()
    })
    if (data.status === 'success') {
      showNotify(data.message || 'База данных успешно оптимизирована!', 'success')
      await fetchData()
    }
  } catch (err) {
    showNotify(err.response?.data?.detail || 'Ошибка сжатия БД', 'error')
  } finally {
    loadingAction.value = false
  }
}

// 3. Перезапуск служб приложения
const handleRestartServices = async () => {
  loadingAction.value = true
  try {
    const { data } = await axios.post('/api/v1/system/server/restart-services', {}, {
      headers: getAuthHeaders()
    })
    if (data.status === 'success') {
      showNotify('Службы Worker и Bot успешно перезапущены!', 'info')
      await fetchContainers()
    }
  } catch (err) {
    showNotify(err.response?.data?.detail || 'Ошибка перезапуска служб', 'error')
  } finally {
    loadingAction.value = false
  }
}

// 4. Перезапуск веб-сервера
const handleRestartWeb = async () => {
  loadingAction.value = true
  try {
    const { data } = await axios.post('/api/v1/system/server/restart-web', {}, {
      headers: getAuthHeaders()
    })
    if (data.status === 'success') {
      showNotify('Веб-серверы успешно перезапущены!', 'info')
      await fetchContainers()
    }
  } catch (err) {
    showNotify(err.response?.data?.detail || 'Ошибка перезапуска веб-серверов', 'error')
  } finally {
    loadingAction.value = false
  }
}

// 5. Перезагрузка сервера VPS
const handleReboot = async () => {
  isRebootDialogOpen.value = false
  loadingAction.value = true
  try {
    const { data } = await axios.post('/api/v1/system/server/reboot', {}, {
      headers: getAuthHeaders()
    })
    if (data.status === 'success') {
      showNotify('Команда принята! Сервер перезагружается, сайт станет доступен через 1-2 минуты.', 'warning')
    }
  } catch (err) {
    showNotify(err.response?.data?.detail || 'Ошибка отправки команды перезагрузки', 'error')
  } finally {
    loadingAction.value = false
  }
}

onMounted(() => {
  fetchData()
  fetchContainers()
  interval = setInterval(() => {
    fetchData()
  }, 4000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})
</script>

<template>
  <div>
    <!-- Заголовок и индикатор глобальной операции -->
    <div class="d-flex justify-space-between align-center mb-4 flex-wrap gap-2">
      <div>
        <h4 class="text-h4 font-weight-bold">Мониторинг и управление сервером</h4>
        <span class="text-caption text-disabled">VPS vezuroll.ru (IP: 178.212.13.48) • Автообновление каждые 4с</span>
      </div>
      <div class="d-flex align-center gap-2">
        <VBtn
          color="primary"
          variant="tonal"
          size="small"
          prepend-icon="bx-refresh"
          :loading="loadingAction"
          @click="() => { fetchData(); fetchContainers(); }"
        >
          Обновить
        </VBtn>
      </div>
    </div>
    
    <VAlert v-if="error" type="error" class="mb-4" closable>
      {{ error }}
    </VAlert>

    <!-- Основные метрики нагрузки -->
    <VRow v-if="status" class="mb-2">
      <!-- CPU Card -->
      <VCol cols="12" md="4">
        <VCard elevation="1" class="h-100">
          <VCardItem>
            <template #prepend>
              <VAvatar color="primary" variant="tonal" class="me-2" rounded>
                <i class="bx bx-chip text-h5" />
              </VAvatar>
            </template>
            <VCardTitle>Процессор (CPU)</VCardTitle>
            <template #append>
              <VChip color="primary" size="small" class="font-weight-bold">{{ status.cpu.percent }}%</VChip>
            </template>
          </VCardItem>
          <VCardText>
            <VueApexCharts
              type="line"
              height="180"
              :options="cpuChartOptions"
              :series="cpuSeries"
            />
          </VCardText>
        </VCard>
      </VCol>

      <!-- RAM & SWAP Card -->
      <VCol cols="12" md="4">
        <VCard elevation="1" class="h-100">
          <VCardItem>
            <template #prepend>
              <VAvatar color="error" variant="tonal" class="me-2" rounded>
                <i class="bx bx-microchip text-h5" />
              </VAvatar>
            </template>
            <VCardTitle>Память (RAM & SWAP)</VCardTitle>
            <template #append>
              <VChip color="error" size="small" class="font-weight-bold">{{ status.ram.percent }}%</VChip>
            </template>
          </VCardItem>
          <VCardText>
            <div class="d-flex justify-space-between mb-2">
              <div>
                <span class="text-caption d-block text-disabled">RAM занято</span>
                <span class="font-weight-medium">{{ formatBytes(status.ram.used) }}</span>
              </div>
              <div class="text-right">
                <span class="text-caption d-block text-disabled">Всего RAM</span>
                <span class="font-weight-medium">{{ formatBytes(status.ram.total) }}</span>
              </div>
            </div>
            <VueApexCharts
              type="line"
              height="140"
              :options="ramChartOptions"
              :series="ramSeries"
            />
            <!-- Swap Progress -->
            <div v-if="status.swap" class="mt-2 pt-2 border-t">
              <div class="d-flex justify-space-between text-caption mb-1">
                <span class="text-disabled">Файл подкачки (SWAP):</span>
                <span class="font-weight-medium">{{ formatBytes(status.swap.used) }} / {{ formatBytes(status.swap.total) }} ({{ status.swap.percent }}%)</span>
              </div>
              <VProgressLinear
                :model-value="status.swap.percent"
                color="info"
                height="6"
                rounded
              />
            </div>
          </VCardText>
        </VCard>
      </VCol>

      <!-- Disk Card -->
      <VCol cols="12" md="4">
        <VCard elevation="1" class="h-100">
          <VCardItem>
            <template #prepend>
              <VAvatar :color="status.disk.percent > 80 ? 'error' : 'warning'" variant="tonal" class="me-2" rounded>
                <i class="bx bx-hdd text-h5" />
              </VAvatar>
            </template>
            <VCardTitle>Диск SSD (Система)</VCardTitle>
            <template #append>
              <VChip :color="status.disk.percent > 80 ? 'error' : 'warning'" size="small" class="font-weight-bold">
                {{ status.disk.percent }}%
              </VChip>
            </template>
          </VCardItem>
          <VCardText>
            <div class="d-flex justify-space-between mb-3">
              <div>
                <span class="text-caption d-block text-disabled">Свободно</span>
                <span class="text-success font-weight-bold text-h6">{{ formatBytes(status.disk.free) }}</span>
              </div>
              <div class="text-right">
                <span class="text-caption d-block text-disabled">Всего на диске</span>
                <span class="font-weight-medium">{{ formatBytes(status.disk.total) }}</span>
              </div>
            </div>
            
            <VProgressLinear
              :model-value="status.disk.percent"
              :color="status.disk.percent > 80 ? 'error' : 'warning'"
              height="24"
              rounded
              class="mb-3"
            >
              <template v-slot:default="{ value }">
                <strong class="text-white text-caption">{{ value }}% занято ({{ formatBytes(status.disk.used) }})</strong>
              </template>
            </VProgressLinear>

            <div class="d-flex justify-space-between align-center p-2 rounded bg-var-theme-background">
              <span class="text-caption text-disabled">Размер базы данных:</span>
              <VChip size="x-small" color="primary" variant="flat" class="font-weight-bold">
                PostgreSQL: {{ status.db_size || 'N/A' }}
              </VChip>
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Блоки управления: Очистка и Перезагрузка -->
    <VRow class="mb-4">
      <!-- 1. Очистка и освобождение места -->
      <VCol cols="12" md="6">
        <VCard elevation="1" class="h-100">
          <VCardItem>
            <template #prepend>
              <VAvatar color="success" variant="tonal" class="me-2" rounded>
                <i class="bx bx-trash text-h5" />
              </VAvatar>
            </template>
            <VCardTitle class="font-weight-bold">Очистка и оптимизация диска</VCardTitle>
            <VCardSubtitle>Безопасное освобождение дискового пространства</VCardSubtitle>
          </VCardItem>
          <VCardText>
            <p class="text-body-2 text-medium-emphasis mb-4">
              Удаление временных кэшей Docker, старых журналов ОС и устаревших системных логов старше 30 дней. Все настройки, история заказов, клиенты и чаты сохраняются.
            </p>
            <div class="d-flex flex-wrap gap-3">
              <VBtn
                color="success"
                prepend-icon="bx-broom"
                :loading="loadingAction"
                @click="handleCleanupDisk"
              >
                Освободить лишнее место
              </VBtn>
              
              <VBtn
                color="warning"
                variant="outlined"
                prepend-icon="bx-data"
                :loading="loadingAction"
                @click="isVacuumDialogOpen = true"
              >
                Сжать базу данных (VACUUM)
              </VBtn>
            </div>
          </VCardText>
        </VCard>
      </VCol>

      <!-- 2. Управление службами и перезагрузка -->
      <VCol cols="12" md="6">
        <VCard elevation="1" class="h-100">
          <VCardItem>
            <template #prepend>
              <VAvatar color="info" variant="tonal" class="me-2" rounded>
                <i class="bx bx-power-off text-h5" />
              </VAvatar>
            </template>
            <VCardTitle class="font-weight-bold">Управление службами и перезагрузка</VCardTitle>
            <VCardSubtitle>Действия при сбоях и подвисаниях</VCardSubtitle>
          </VCardItem>
          <VCardText>
            <p class="text-body-2 text-medium-emphasis mb-4">
              <strong>Мягкий перезапуск</strong> сбрасывает зависшие задачи Celery и освобождает память без разрыва сайта. <strong>Перезагрузка VPS</strong> выполняет чистый рестарт операционной системы.
            </p>
            <div class="d-flex flex-wrap gap-2">
              <VBtn
                color="info"
                variant="tonal"
                size="small"
                prepend-icon="bx-refresh"
                :loading="loadingAction"
                @click="handleRestartServices"
              >
                Рестарт фоновых служб
              </VBtn>

              <VBtn
                color="secondary"
                variant="tonal"
                size="small"
                prepend-icon="bx-globe"
                :loading="loadingAction"
                @click="handleRestartWeb"
              >
                Рестарт веб-сервера
              </VBtn>

              <VBtn
                color="error"
                size="small"
                prepend-icon="bx-power-off"
                :loading="loadingAction"
                @click="isRebootDialogOpen = true"
              >
                Перезагрузить сервер (VPS)
              </VBtn>
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- 3. Список Docker контейнеров системы -->
    <VCard elevation="1" class="mb-4">
      <VCardItem>
        <template #prepend>
          <VAvatar color="primary" variant="tonal" class="me-2" rounded>
            <i class="bx bxl-docker text-h5" />
          </VAvatar>
        </template>
        <VCardTitle class="font-weight-bold">Контейнеры Docker на сервере</VCardTitle>
        <VCardSubtitle>Статус служб и компонентов инфраструктуры</VCardSubtitle>
      </VCardItem>
      <VCardText>
        <div v-if="containers.length === 0" class="text-center py-4 text-disabled">
          Загрузка списка контейнеров...
        </div>
        <VTable v-else density="compact" class="text-no-wrap">
          <thead>
            <tr>
              <th class="text-uppercase text-caption font-weight-bold">Контейнер</th>
              <th class="text-uppercase text-caption font-weight-bold">Образ</th>
              <th class="text-uppercase text-caption font-weight-bold">Состояние</th>
              <th class="text-uppercase text-caption font-weight-bold">Аптайм / Статус</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in containers" :key="c.id">
              <td class="font-weight-medium">
                <i class="bx bx-cube me-1 text-primary" />
                {{ c.name }}
              </td>
              <td class="text-caption text-disabled">{{ c.image }}</td>
              <td>
                <VChip
                  :color="c.state === 'running' ? 'success' : 'error'"
                  size="x-small"
                  class="font-weight-bold"
                >
                  {{ c.state === 'running' ? 'Работает' : c.state }}
                </VChip>
              </td>
              <td class="text-caption">{{ c.status }}</td>
            </tr>
          </tbody>
        </VTable>
      </VCardText>
    </VCard>

    <!-- Диалог подтверждения VACUUM FULL -->
    <VDialog v-model="isVacuumDialogOpen" max-width="500">
      <VCard>
        <VCardTitle class="d-flex align-center gap-2 pt-4">
          <i class="bx bx-data text-warning text-h4" />
          <span>Сжатие базы данных (VACUUM FULL)</span>
        </VCardTitle>
        <VCardText class="pt-2">
          <p class="text-body-2 mb-2">
            Эта операция физически перестраивает таблицы и дефрагментирует индексы PostgreSQL, возвращая диску ранее занятое пространство.
          </p>
          <VAlert type="info" variant="tonal" density="compact" class="mb-0">
            Все данные сохраняются полностью. Операция может занять 15–30 секунд.
          </VAlert>
        </VCardText>
        <VCardActions class="justify-end pb-4 pe-4">
          <VBtn variant="text" color="secondary" @click="isVacuumDialogOpen = false">Отмена</VBtn>
          <VBtn color="warning" variant="elevated" @click="handleVacuumDb">Запустить сжатие</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог подтверждения Перезагрузки VPS -->
    <VDialog v-model="isRebootDialogOpen" max-width="500">
      <VCard>
        <VCardTitle class="d-flex align-center gap-2 pt-4 text-error">
          <i class="bx bx-error-circle text-h4" />
          <span>Перезагрузка сервера VPS</span>
        </VCardTitle>
        <VCardText class="pt-2">
          <p class="text-body-2 mb-2">
            Вы собираетесь выполнить <strong>полную перезагрузку операционной системы сервера</strong> (VPS 178.212.13.48).
          </p>
          <VAlert type="warning" variant="tonal" density="compact" class="mb-0">
            Во время перезагрузки сайт и админ-панель будут кратковременно недоступны в течение 1-2 минут.
          </VAlert>
        </VCardText>
        <VCardActions class="justify-end pb-4 pe-4">
          <VBtn variant="text" color="secondary" @click="isRebootDialogOpen = false">Отмена</VBtn>
          <VBtn color="error" variant="elevated" @click="handleReboot">Да, перезагрузить сервер</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Всплывающее уведомление (Snackbar) -->
    <VSnackbar
      v-model="snackbar"
      :color="snackbarColor"
      timeout="5000"
      location="top right"
    >
      {{ actionMessage }}
      <template #actions>
        <VBtn variant="text" color="white" @click="snackbar = false">Закрыть</VBtn>
      </template>
    </VSnackbar>
  </div>
</template>

