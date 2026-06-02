<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
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
    range: 60000, // 60 seconds range
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
    range: 60000, // 60 seconds range
  },
  yaxis: {
    max: 100,
    min: 0,
    labels: { formatter: (val) => val.toFixed(0) + '%' }
  },
  colors: ['#FF4560']
})

const status = ref(null)
const error = ref(null)
let interval = null

const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

const fetchData = async () => {
  try {
    const { data } = await axios.get('/api/v1/system/server-status')
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
    error.value = 'Ошибка загрузки данных о сервере. Убедитесь, что бэкенд обновлен (psutil установлен).'
  }
}

onMounted(() => {
  fetchData()
  interval = setInterval(fetchData, 3000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})
</script>

<template>
  <div>
    <h4 class="text-h4 mb-4">Нагрузка сервера</h4>
    
    <VAlert v-if="error" type="error" class="mb-4" closable>
      {{ error }}
    </VAlert>

    <VRow v-if="status">
      <!-- CPU Card -->
      <VCol cols="12" md="4">
        <VCard>
          <VCardItem>
            <VCardTitle>Процессор (CPU)</VCardTitle>
            <template #append>
              <VChip color="primary" size="small">{{ status.cpu.percent }}%</VChip>
            </template>
          </VCardItem>
          <VCardText>
            <VueApexCharts
              type="line"
              height="200"
              :options="cpuChartOptions"
              :series="cpuSeries"
            />
          </VCardText>
        </VCard>
      </VCol>

      <!-- RAM Card -->
      <VCol cols="12" md="4">
        <VCard>
          <VCardItem>
            <VCardTitle>Память (RAM)</VCardTitle>
            <template #append>
              <VChip color="error" size="small">{{ status.ram.percent }}%</VChip>
            </template>
          </VCardItem>
          <VCardText>
            <div class="d-flex justify-space-between mb-4">
              <div>
                <span class="text-caption d-block text-disabled">Использовано</span>
                <span class="font-weight-medium">{{ formatBytes(status.ram.used) }}</span>
              </div>
              <div class="text-right">
                <span class="text-caption d-block text-disabled">Всего</span>
                <span class="font-weight-medium">{{ formatBytes(status.ram.total) }}</span>
              </div>
            </div>
            <VueApexCharts
              type="line"
              height="200"
              :options="ramChartOptions"
              :series="ramSeries"
            />
          </VCardText>
        </VCard>
      </VCol>

      <!-- Disk Card -->
      <VCol cols="12" md="4">
        <VCard>
          <VCardItem>
            <VCardTitle>Диск (SSD/HDD)</VCardTitle>
            <template #append>
              <VChip color="warning" size="small">{{ status.disk.percent }}%</VChip>
            </template>
          </VCardItem>
          <VCardText>
            <div class="d-flex justify-space-between mb-4">
              <div>
                <span class="text-caption d-block text-disabled">Осталось</span>
                <span class="text-success font-weight-medium">{{ formatBytes(status.disk.free) }}</span>
              </div>
              <div class="text-right">
                <span class="text-caption d-block text-disabled">Всего</span>
                <span class="font-weight-medium">{{ formatBytes(status.disk.total) }}</span>
              </div>
            </div>
            
            <VProgressLinear
              :model-value="status.disk.percent"
              color="warning"
              height="24"
              rounded
              class="mb-2"
            >
              <template v-slot:default="{ value }">
                <strong class="text-white">{{ value }}% занято</strong>
              </template>
            </VProgressLinear>
            <div class="text-caption text-center text-disabled">
              Использовано: {{ formatBytes(status.disk.used) }}
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>
    
    <div v-else-if="!error" class="d-flex justify-center align-center mt-10">
      <VProgressCircular indeterminate color="primary" />
    </div>
  </div>
</template>
