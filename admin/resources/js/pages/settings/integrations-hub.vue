<script setup>
import { ref, onMounted } from "vue"

const loading = ref(false)
const statusData = ref(null)
const errorMsg = ref(null)

const fetchStatus = async () => {
  loading.value = true
  errorMsg.value = null
  try {
    const res = await fetch("/api/v1/modules/integrations/status")
    if (res.ok) {
      statusData.value = await res.json()
    } else {
      errorMsg.value = `Ошибка API: статус ${res.status}`
    }
  } catch (e) {
    errorMsg.value = `Сбой запроса: ${e.message}`
  } finally {
    loading.value = false
  }
}

const getStatusColor = (status) => {
  switch (status) {
    case "online":
      return "success"
    case "configured":
      return "info"
    case "disabled":
    case "unconfigured":
      return "secondary"
    default:
      return "error"
  }
}

const getStatusText = (status) => {
  switch (status) {
    case "online":
      return "В сети"
    case "configured":
      return "Настроен"
    case "disabled":
      return "Отключен"
    case "unconfigured":
      return "Не настроен"
    default:
      return "Ошибка"
  }
}

onMounted(() => {
  fetchStatus()
})
</script>

<template>
  <div>
    <!-- Шапка модуля -->
    <VRow class="mb-4 align-center">
      <VCol cols="12" md="8">
        <div class="d-flex align-center gap-2 mb-1">
          <VBtn
            to="/settings/modules"
            variant="text"
            icon="ri-arrow-left-line"
            density="comfortable"
          />
          <h2 class="text-h4 font-weight-bold d-flex align-center gap-2 mb-0">
            <VIcon icon="ri-cloud-line" color="primary" />
            Хаб внешних интеграций
          </h2>
        </div>
        <p class="text-body-1 text-medium-emphasis mb-0 ps-10">
          Пилотный динамический модуль: онлайн-мониторинг шлюзов iiko, Redis, VK и MAX Messenger
        </p>
      </VCol>

      <VCol cols="12" md="4" class="text-md-end">
        <VBtn
          color="primary"
          prepend-icon="ri-refresh-line"
          :loading="loading"
          @click="fetchStatus"
        >
          Проверить связь
        </VBtn>
      </VCol>
    </VRow>

    <VAlert v-if="errorMsg" type="error" variant="tonal" class="mb-4">
      {{ errorMsg }}
    </VAlert>

    <!-- Сетка сервисов -->
    <VRow v-if="statusData?.services">
      <VCol
        v-for="(svc, key) in statusData.services"
        :key="key"
        cols="12"
        md="6"
      >
        <VCard variant="outlined" class="h-100 pa-4">
          <div class="d-flex justify-space-between align-start mb-3">
            <div>
              <h3 class="text-h6 font-weight-bold mb-1">{{ svc.name }}</h3>
              <p class="text-body-2 text-medium-emphasis mb-0">{{ svc.details }}</p>
            </div>
            <VChip
              :color="getStatusColor(svc.status)"
              size="small"
              variant="flat"
            >
              {{ getStatusText(svc.status) }}
            </VChip>
          </div>

          <div v-if="svc.latency_ms !== null" class="d-flex align-center gap-2 mt-4 pt-2 border-t">
            <VIcon icon="ri-speed-line" size="18" color="medium-emphasis" />
            <span class="text-caption text-medium-emphasis">Время отклика:</span>
            <span class="text-caption font-weight-bold text-success">{{ svc.latency_ms }} мс</span>
          </div>
        </VCard>
      </VCol>
    </VRow>

    <VCard v-else-if="loading" class="pa-12 text-center" variant="outlined">
      <VProgressCircular indeterminate color="primary" size="48" class="mb-3" />
      <div class="text-body-1 text-medium-emphasis">Опрос внешних сервисов...</div>
    </VCard>
  </div>
</template>
