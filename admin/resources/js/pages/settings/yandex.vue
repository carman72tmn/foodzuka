<script setup>
import { ref, onMounted } from 'vue'

const settings = ref({
  api_key_js: '',
  api_key_suggest: '',
  api_key_matrix: '',
  api_key_monitoring: '',
  api_key_static: '',
  is_active: true
})

const loading = ref(false)
const testing = ref(null)
const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

const API_BASE = '/api/v1/yandex'

const fetchSettings = async () => {
  try {
    const response = await fetch(`${API_BASE}/settings`)
    if (response.ok) {
      settings.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching yandex settings:', error)
  }
}

const saveSettings = async () => {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings.value)
    })
    
    if (response.ok) {
      snackbar.value = {
        show: true,
        text: 'Настройки успешно сохранены',
        color: 'success'
      }
    } else {
      snackbar.value = {
        show: true,
        text: 'Ошибка при сохранении настроек',
        color: 'error'
      }
    }
  } catch (error) {
    snackbar.value = {
      show: true,
      text: 'Ошибка подключения к серверу',
      color: 'error'
    }
  } finally {
    loading.value = false
  }
}

const testKey = async (type, key) => {
  if (!key) return
  
  testing.value = type
  try {
    const response = await fetch(`${API_BASE}/test-key?key_type=${type}&api_key=${key}`, {
      method: 'POST'
    })
    
    const data = await response.json()
    if (response.ok) {
      snackbar.value = {
        show: true,
        text: data.message,
        color: 'success'
      }
    } else {
      snackbar.value = {
        show: true,
        text: data.detail || 'Ошибка проверки ключа',
        color: 'error'
      }
    }
  } catch (error) {
    snackbar.value = {
      show: true,
      text: 'Ошибка подключения к серверу',
      color: 'error'
    }
  } finally {
    testing.value = null
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard title="Интеграция с Яндекс Картами" subtitle="Настройка API ключей для геокодирования и мониторинга">
        <VCardText>
          <VForm @submit.prevent="saveSettings">
            <VRow>
              <!-- JS API -->
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.api_key_js"
                  label="JavaScript API и HTTP Геокодер"
                  placeholder="Введите API ключ"
                  persistent-placeholder
                  :append-inner-icon="testing === 'geocoder' ? 'mdi-loading mdi-spin' : 'mdi-check-circle-outline'"
                  @click:append-inner="testKey('geocoder', settings.api_key_js)"
                />
                <p class="text-caption mt-1">Используется для отображения карт и преобразования адресов в координаты.</p>
              </VCol>

              <!-- Suggest API -->
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.api_key_suggest"
                  label="API Геосаджеста"
                  placeholder="Введите API ключ"
                  persistent-placeholder
                />
                <p class="text-caption mt-1">Для быстрого автодополнения адресов при вводе.</p>
              </VCol>

              <!-- Matrix API -->
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.api_key_matrix"
                  label="Матрица расстояний"
                  placeholder="Введите API ключ"
                  persistent-placeholder
                />
                <p class="text-caption mt-1">Для расчета времени и стоимости доставки на основе маршрутов.</p>
              </VCol>

              <!-- Monitoring API -->
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.api_key_monitoring"
                  label="Маршрутизация и Мониторинг"
                  placeholder="Введите API ключ"
                  persistent-placeholder
                />
                <p class="text-caption mt-1">Для отслеживания курьеров в реальном времени.</p>
              </VCol>

              <VCol cols="12">
                <VSwitch
                  v-model="settings.is_active"
                  label="Активировать интеграцию"
                  color="primary"
                />
              </VCol>

              <VCol cols="12" class="d-flex gap-4">
                <VBtn
                  type="submit"
                  :loading="loading"
                  color="primary"
                >
                  Сохранить настройки
                </VBtn>
              </VCol>
            </VRow>
          </VForm>
        </VCardText>
      </VCard>
    </VCol>

    <!-- Инструкция -->
    <VCol cols="12">
      <VAlert
        color="info"
        variant="tonal"
        icon="mdi-information-outline"
      >
        <h4 class="text-h6 mb-2">Где взять ключи?</h4>
        <p class="mb-2">Ключи можно получить в <a href="https://apikeys.developer.yandex.ru/" target="_blank" class="text-primary font-weight-bold">Кабинете разработчика Яндекс</a>.</p>
        <ul class="ml-4">
          <li>Для карт выберите сервис "JavaScript API и HTTP Геокодер".</li>
          <li>Для подсказок — "API Геосаджеста".</li>
          <li>Для логистики — "Маршрутизация" и "Матрица расстояний".</li>
        </ul>
      </VAlert>
    </VCol>

    <VSnackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="3000"
    >
      {{ snackbar.text }}
    </VSnackbar>
  </VRow>
</template>

<style lang="scss" scoped>
.v-card {
  backdrop-filter: blur(10px);
  background: rgba(var(--v-theme-surface), 0.8);
}
</style>
