<script setup>
import { ref, onErrorCaptured, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const hasError = ref(false)
const errorMessage = ref('')
const errorInfo = ref('')
const errorStack = ref('')
const showDetails = ref(false)

// Перехват любой ошибки дочерних компонентов
onErrorCaptured((err, instance, info) => {
  console.error('[ModuleErrorBoundary] Перехвачена ошибка в модуле/странице:', err, info)
  
  hasError.value = true
  errorMessage.value = err?.message || String(err)
  errorInfo.value = info || ''
  errorStack.value = err?.stack || ''

  // Возврат false предотвращает падение родительских компонентов и белый экран приложения
  return false
})

// При переходе на другую страницу автоматически сбрасываем состояние ошибки
watch(
  () => route.fullPath,
  () => {
    hasError.value = false
    errorMessage.value = ''
    errorInfo.value = ''
    errorStack.value = ''
    showDetails.value = false
  }
)

const retry = () => {
  hasError.value = false
  errorMessage.value = ''
  errorInfo.value = ''
  errorStack.value = ''
  showDetails.value = false
}

const goToDashboard = () => {
  hasError.value = false
  router.push('/dashboard')
}
</script>

<template>
  <div class="module-boundary-wrapper">
    <!-- Если внутри модуля произошла ошибка -->
    <div v-if="hasError" class="pa-6">
      <VCard color="error" variant="tonal" class="pa-6">
        <div class="d-flex align-center mb-4">
          <VIcon icon="ri-error-warning-line" size="36" color="error" class="me-3" />
          <div>
            <h3 class="text-h6 text-error font-weight-bold mb-1">
              Сбой при отображении раздела
            </h3>
            <p class="text-body-2 mb-0 text-medium-emphasis">
              В данном модуле возникло непредвиденное исключение. Ядро админ-панели и остальные разделы продолжают работать стабильно.
            </p>
          </div>
        </div>

        <VAlert type="error" variant="outlined" density="compact" class="mb-4">
          <span class="font-weight-medium">Ошибка:</span> {{ errorMessage }}
        </VAlert>

        <div class="d-flex flex-wrap gap-3 mb-4">
          <VBtn color="primary" prepend-icon="ri-refresh-line" @click="retry">
            Повторить попытку
          </VBtn>
          <VBtn variant="outlined" prepend-icon="ri-dashboard-line" @click="goToDashboard">
            На рабочий стол
          </VBtn>
          <VBtn
            variant="text"
            color="secondary"
            :prepend-icon="showDetails ? 'ri-arrow-up-s-line' : 'ri-arrow-down-s-line'"
            @click="showDetails = !showDetails"
          >
            {{ showDetails ? 'Скрыть технические детали' : 'Технические детали' }}
          </VBtn>
        </div>

        <!-- Детали ошибки для разработчика -->
        <VExpandTransition>
          <div v-if="showDetails" class="mt-4">
            <VCard variant="outlined" class="pa-4 bg-surface">
              <div class="text-caption font-weight-bold mb-1 text-primary">Жизненный цикл Vue:</div>
              <pre class="text-caption mb-3 text-medium-emphasis" style="white-space: pre-wrap;">{{ errorInfo }}</pre>

              <div class="text-caption font-weight-bold mb-1 text-error">Стек вызова:</div>
              <pre class="text-caption text-medium-emphasis overflow-auto" style="max-height: 200px; white-space: pre-wrap;">{{ errorStack }}</pre>
            </VCard>
          </div>
        </VExpandTransition>
      </VCard>
    </div>

    <!-- Нормальное отображение страницы/модуля -->
    <slot v-else />
  </div>
</template>

<style scoped>
.module-boundary-wrapper {
  width: 100%;
  height: 100%;
}
</style>
