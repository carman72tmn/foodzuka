<template>
  <div>
    <!-- Заголовок страницы -->
    <VCard class="mb-6">
      <VCardItem>
        <template #prepend>
          <VAvatar color="primary" variant="tonal" rounded size="44">
            <VIcon icon="bx-extension" size="28" />
          </VAvatar>
        </template>
        <VCardTitle class="text-h5 font-weight-bold">
          Модульная архитектура (Modular Monolith)
        </VCardTitle>
        <VCardSubtitle>
          Динамический реестр плагинов и модулей ядра. Изоляция функционала, защита от сбоев (Error Boundaries) и runtime-контроль.
        </VCardSubtitle>
        <template #append>
          <div class="d-flex gap-2">
            <VBtn
              color="secondary"
              variant="tonal"
              prepend-icon="bx-refresh"
              :loading="isRescanning"
              @click="rescanModules"
            >
              Пересканировать модули
            </VBtn>
            <VBtn
              color="primary"
              prepend-icon="bx-sync"
              :loading="isLoading"
              @click="fetchModules"
            >
              Обновить
            </VBtn>
          </div>
        </template>
      </VCardItem>
    </VCard>

    <!-- Вкладки: Реестр модулей и Хаб интеграций (Пилотный модуль) -->
    <VTabs v-model="activeTab" class="mb-6">
      <VTab value="registry">
        <VIcon icon="bx-list-ul" class="me-2" />
        Реестр модулей ({{ modules.length }})
      </VTab>
      <VTab value="pilot_integrations">
        <VIcon icon="bx-git-merge" class="me-2" />
        Пилотный модуль: Хаб интеграций
      </VTab>
      <VTab value="architecture">
        <VIcon icon="bx-shield-quarter" class="me-2" />
        Архитектура и отказоустойчивость
      </VTab>
    </VTabs>

    <VWindow v-model="activeTab">
      <!-- Вкладка 1: Таблица реестра модулей -->
      <VWindowItem value="registry">
        <VCard>
          <VCardText class="d-flex flex-wrap gap-4 align-center justify-space-between">
            <div class="d-flex align-center gap-3" style="max-width: 320px; width: 100%;">
              <VTextField
                v-model="searchQuery"
                placeholder="Поиск по названию или slug..."
                density="compact"
                variant="outlined"
                prepend-inner-icon="bx-search"
                hide-details
                clearable
              />
            </div>
            <div class="d-flex align-center gap-2">
              <VChip
                color="info"
                variant="tonal"
                size="small"
              >
                Всего модулей: {{ modules.length }}
              </VChip>
              <VChip
                color="success"
                variant="tonal"
                size="small"
              >
                Активно: {{ activeCount }}
              </VChip>
            </div>
          </VCardText>

          <VDivider />

          <VTable class="text-no-wrap">
            <thead>
              <tr>
                <th class="text-uppercase">Модуль</th>
                <th class="text-uppercase">Категория</th>
                <th class="text-uppercase">Версия / Автор</th>
                <th class="text-uppercase">Статус загрузки</th>
                <th class="text-uppercase">API Префикс</th>
                <th class="text-uppercase text-center">Активность</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isLoading">
                <td colspan="6" class="text-center py-6">
                  <VProgressCircular indeterminate color="primary" class="me-2" />
                  Загрузка модулей...
                </td>
              </tr>
              <tr v-else-if="filteredModules.length === 0">
                <td colspan="6" class="text-center py-6 text-disabled">
                  Модули не найдены
                </td>
              </tr>
              <tr v-for="mod in filteredModules" :key="mod.slug">
                <td>
                  <div class="d-flex align-center">
                    <VAvatar
                      :color="mod.is_system ? 'secondary' : 'primary'"
                      variant="tonal"
                      rounded
                      size="38"
                      class="me-3"
                    >
                      <VIcon :icon="mod.icon || 'bx-cube'" size="22" />
                    </VAvatar>
                    <div>
                      <div class="font-weight-medium text-high-emphasis d-flex align-center gap-2">
                        {{ mod.name }}
                        <VChip
                          v-if="mod.is_system"
                          size="x-small"
                          color="error"
                          variant="tonal"
                        >
                          Ядро
                        </VChip>
                        <VChip
                          v-else
                          size="x-small"
                          color="primary"
                          variant="tonal"
                        >
                          Плагин
                        </VChip>
                      </div>
                      <div class="text-caption text-disabled font-monospace">
                        {{ mod.slug }}
                      </div>
                      <div v-if="mod.description" class="text-caption text-secondary mt-1">
                        {{ mod.description }}
                      </div>
                    </div>
                  </div>
                </td>
                <td>
                  <VChip
                    size="small"
                    :color="getCategoryColor(mod.category)"
                    variant="tonal"
                  >
                    {{ mod.category || 'general' }}
                  </VChip>
                </td>
                <td>
                  <div class="text-body-2 font-weight-medium">v{{ mod.version || '1.0.0' }}</div>
                  <div class="text-caption text-disabled">{{ mod.author || 'VezuRoll Core' }}</div>
                </td>
                <td>
                  <div class="d-flex align-center gap-1">
                    <VBadge
                      dot
                      :color="mod.is_loaded ? 'success' : 'warning'"
                      class="me-1"
                    />
                    <span class="text-caption">
                      {{ mod.is_loaded ? 'Загружен в рантайм' : 'Только в БД' }}
                    </span>
                  </div>
                </td>
                <td>
                  <code class="text-caption bg-light px-2 py-1 rounded">
                    /api/v1/modules/{{ mod.slug.replace(/_/g, '-') }}
                  </code>
                </td>
                <td class="text-center">
                  <VSwitch
                    v-model="mod.is_enabled"
                    :disabled="mod.is_system || isToggling[mod.slug]"
                    :loading="isToggling[mod.slug]"
                    color="success"
                    hide-details
                    density="compact"
                    class="d-inline-flex"
                    @update:model-value="(val) => toggleModule(mod, val)"
                  />
                </td>
              </tr>
            </tbody>
          </VTable>
        </VCard>
      </VWindowItem>

      <!-- Вкладка 2: Пилотный модуль «Хаб внешних интеграций» -->
      <VWindowItem value="pilot_integrations">
        <VRow>
          <VCol cols="12" md="8">
            <VCard class="mb-4">
              <VCardItem>
                <template #prepend>
                  <VAvatar color="info" variant="tonal" rounded>
                    <VIcon icon="bx-git-merge" size="24" />
                  </VAvatar>
                </template>
                <VCardTitle>Диагностика связей хаба интеграций</VCardTitle>
                <VCardSubtitle>
                  Модуль: <code>integrations_hub</code> | Эндпоинт: <code>/api/v1/modules/integrations-hub/status</code>
                </VCardSubtitle>
                <template #append>
                  <VBtn
                    color="primary"
                    variant="tonal"
                    prepend-icon="bx-pulse"
                    :loading="isCheckingPilot"
                    @click="checkPilotStatus"
                  >
                    Проверить соединения
                  </VBtn>
                </template>
              </VCardItem>
              <VDivider />
              <VCardText>
                <div v-if="isCheckingPilot" class="py-6 text-center">
                  <VProgressCircular indeterminate color="primary" class="me-2" />
                  Опрос внешних сервисов...
                </div>
                <div v-else-if="pilotStatus">
                  <VRow>
                    <VCol
                      v-for="(service, name) in pilotStatus.services"
                      :key="name"
                      cols="12"
                      sm="6"
                    >
                      <VCard variant="outlined" class="h-100">
                        <VCardItem>
                          <div class="d-flex justify-space-between align-center">
                            <div class="font-weight-bold text-capitalize">
                              {{ getServiceName(name) }}
                            </div>
                            <VChip
                              :color="service.status === 'ok' || service.status === 'configured' ? 'success' : (service.status === 'error' ? 'error' : 'warning')"
                              size="small"
                              variant="tonal"
                            >
                              {{ service.status }}
                            </VChip>
                          </div>
                          <div class="text-caption text-disabled mt-2">
                            <div v-for="(v, k) in service" :key="k">
                              <span class="font-weight-medium">{{ k }}:</span> {{ v }}
                            </div>
                          </div>
                        </VCardItem>
                      </VCard>
                    </VCol>
                  </VRow>
                  <div class="text-caption text-disabled mt-4 text-end">
                    Последняя проверка: {{ pilotStatus.timestamp }}
                  </div>
                </div>
                <div v-else class="text-center py-6 text-disabled">
                  Нажмите кнопку «Проверить соединения» для запуска диагностики
                </div>
              </VCardText>
            </VCard>
          </VCol>

          <VCol cols="12" md="4">
            <VCard>
              <VCardItem>
                <VCardTitle class="text-base font-weight-bold">
                  О пилотном модуле
                </VCardTitle>
              </VCardItem>
              <VDivider />
              <VCardText class="text-body-2">
                <p>
                  <strong>Хаб внешних интеграций</strong> — первый эталонный модуль, переведенный на новую архитектуру <em>Modular Monolith</em>.
                </p>
                <p>
                  Он изолирован в каталоге <code>backend/app/modules/integrations_hub/</code> и регистрирует свои роуты динамически через <code>BaseModule</code>.
                </p>
                <p class="mb-0 text-caption text-secondary">
                  При необходимости модуль можно выключить в таблице реестра без остановки или перезапуска основного монолита.
                </p>
              </VCardText>
            </VCard>
          </VCol>
        </VRow>
      </VWindowItem>

      <!-- Вкладка 3: Архитектура и отказоустойчивость -->
      <VWindowItem value="architecture">
        <VRow>
          <VCol cols="12" md="6">
            <VCard class="h-100">
              <VCardItem>
                <template #prepend>
                  <VAvatar color="success" variant="tonal" rounded>
                    <VIcon icon="bx-shield-check" size="24" />
                  </VAvatar>
                </template>
                <VCardTitle>Предохранители UI (Error Boundaries)</VCardTitle>
              </VCardItem>
              <VCardText class="text-body-2">
                <p>
                  В админ-панели внедрен компонент <code>ModuleErrorBoundary.vue</code>, оборачивающий вывод всех страниц через хук Vue <code>onErrorCaptured</code>.
                </p>
                <p>
                  Если в отдельном компоненте возникает JavaScript-ошибка (например, неопределенная функция или неверный формат ответа), вместо белого экрана отображается аккуратная изолированная плашка с сообщением об ошибке и кнопкой перезагрузки страницы.
                </p>
                <VAlert color="success" variant="tonal" density="compact" class="mt-3">
                  Ядро админки, боковое меню и навигация остаются полностью работоспособными при сбое в любой из вкладок.
                </VAlert>
              </VCardText>
            </VCard>
          </VCol>

          <VCol cols="12" md="6">
            <VCard class="h-100">
              <VCardItem>
                <template #prepend>
                  <VAvatar color="warning" variant="tonal" rounded>
                    <VIcon icon="bx-layer" size="24" />
                  </VAvatar>
                </template>
                <VCardTitle>Стандартизация BaseModule</VCardTitle>
              </VCardItem>
              <VCardText class="text-body-2">
                <p>
                  Каждый модуль бэкенда наследуется от <code>BaseModule</code>:
                </p>
                <ul class="ps-4 mb-3">
                  <li><code>slug</code>: уникальный идентификатор</li>
                  <li><code>get_router()</code>: изолированный FastAPI APIRouter</li>
                  <li><code>on_load(app)</code> / <code>on_unload(app)</code>: хуки жизненного цикла</li>
                  <li>Автоматическая синхронизация с таблицей <code>system_modules</code></li>
                </ul>
                <p class="mb-0 text-caption text-secondary">
                  Модули могут разрабатываться и тестироваться независимо, не затрагивая монолитные файлы <code>main.py</code>.
                </p>
              </VCardText>
            </VCard>
          </VCol>
        </VRow>
      </VWindowItem>
    </VWindow>

    <!-- Снэкбар уведомлений -->
    <VSnackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="3000"
      location="top end"
    >
      {{ snackbar.text }}
    </VSnackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const activeTab = ref('registry')
const modules = ref([])
const isLoading = ref(false)
const isRescanning = ref(false)
const isCheckingPilot = ref(false)
const pilotStatus = ref(null)
const searchQuery = ref('')
const isToggling = ref({})

const snackbar = ref({
  show: false,
  color: 'success',
  text: '',
})

const showToast = (text, color = 'success') => {
  snackbar.value = {
    show: true,
    color,
    text,
  }
}

const activeCount = computed(() => {
  return modules.value.filter(m => m.is_enabled).length
})

const filteredModules = computed(() => {
  if (!searchQuery.value) return modules.value
  const q = searchQuery.value.toLowerCase()
  return modules.value.filter(m =>
    (m.name && m.name.toLowerCase().includes(q)) ||
    (m.slug && m.slug.toLowerCase().includes(q)) ||
    (m.category && m.category.toLowerCase().includes(q))
  )
})

const getCategoryColor = (cat) => {
  const map = {
    integrations: 'info',
    marketing: 'warning',
    orders: 'success',
    system: 'secondary',
    ai: 'purple',
  }
  return map[cat] || 'primary'
}

const getServiceName = (key) => {
  const map = {
    database: 'База данных (PostgreSQL)',
    iiko_cloud: 'iiko Cloud Transport API',
    tbank_api: 'Т-Банк (T-Bank API)',
    telegram_bot: 'Telegram Bot API',
    vk_bot: 'VK Bot API',
  }
  return map[key] || key
}

const fetchModules = async () => {
  isLoading.value = true
  try {
    const res = await axios.get('/api/v1/system/modules')
    modules.value = res.data
  } catch (e) {
    showToast('Не удалось загрузить список модулей: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    isLoading.value = false
  }
}

const rescanModules = async () => {
  isRescanning.value = true
  try {
    const res = await axios.post('/api/v1/system/modules/rescan')
    showToast(`Сканирование завершено. Обнаружено модулей: ${res.data.total_modules}`)
    await fetchModules()
  } catch (e) {
    showToast('Ошибка при сканировании: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    isRescanning.value = false
  }
}

const toggleModule = async (mod, newVal) => {
  isToggling.value[mod.slug] = true
  try {
    await axios.post(`/api/v1/system/modules/${mod.slug}/toggle`, {
      is_enabled: newVal
    })
    showToast(`Модуль "${mod.name}" ${newVal ? 'включен' : 'отключен'}`)
  } catch (e) {
    mod.is_enabled = !newVal // откат
    showToast('Ошибка при изменении статуса: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    isToggling.value[mod.slug] = false
  }
}

const checkPilotStatus = async () => {
  isCheckingPilot.value = true
  try {
    const res = await axios.get('/api/v1/modules/integrations-hub/status')
    pilotStatus.value = res.data
    showToast('Диагностика хаба интеграций успешно завершена')
  } catch (e) {
    showToast('Ошибка при проверке статуса хаба: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    isCheckingPilot.value = false
  }
}

onMounted(() => {
  fetchModules()
  checkPilotStatus()
})
</script>

<style scoped>
.font-monospace {
  font-family: monospace;
}
</style>
