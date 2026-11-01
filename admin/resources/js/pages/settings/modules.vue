<script setup>
import { ref, computed, onMounted } from "vue"

const modules = ref([])
const loading = ref(false)
const togglingSlug = ref(null)

const searchQuery = ref("")
const selectedCategory = ref("all")

const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const errorDialog = ref(false)
const selectedError = ref({ name: "", error: "" })

const showToast = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const loadModules = async () => {
  loading.value = true
  try {
    const res = await fetch("/api/v1/system/modules/")
    if (res.ok) {
      modules.value = await res.json()
    } else {
      showToast("Не удалось загрузить список модулей", "error")
    }
  } catch (err) {
    showToast("Ошибка подключения к серверу", "error")
  } finally {
    loading.value = false
  }
}

const toggleModule = async (mod) => {
  if (mod.is_system && mod.is_enabled) {
    showToast("Системный модуль ядра нельзя отключить", "warning")
    return
  }

  togglingSlug.value = mod.slug
  try {
    const res = await fetch(`/api/v1/system/modules/${mod.slug}/toggle`, {
      method: "POST",
    })
    const data = await res.json()
    if (res.ok) {
      showToast(data.message || "Статус модуля обновлен", "success")
      await loadModules()
    } else {
      showToast(data.detail || "Ошибка переключения модуля", "error")
    }
  } catch (err) {
    showToast("Сбой при отправке запроса", "error")
  } finally {
    togglingSlug.value = null
  }
}

const openErrorDialog = (mod) => {
  selectedError.value = {
    name: mod.name,
    error: mod.error || "Неизвестная ошибка инициализации"
  }
  errorDialog.value = true
}

const categories = [
  { title: "Все категории", value: "all" },
  { title: "Интеграции", value: "integrations" },
  { title: "Отчеты", value: "reports" },
  { title: "Маркетинг", value: "marketing" },
  { title: "Инструменты", value: "tools" },
  { title: "Общие", value: "general" },
]

const filteredModules = computed(() => {
  return modules.value.filter(m => {
    const matchesSearch =
      m.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (m.description && m.description.toLowerCase().includes(searchQuery.value.toLowerCase())) ||
      m.slug.toLowerCase().includes(searchQuery.value.toLowerCase())

    const matchesCategory =
      selectedCategory.value === "all" || m.category === selectedCategory.value

    return matchesSearch && matchesCategory
  })
})

const activeCount = computed(() => modules.value.filter(m => m.is_enabled && m.is_loaded).length)
const totalCount = computed(() => modules.value.length)

onMounted(() => {
  loadModules()
})
</script>

<template>
  <div>
    <!-- Шапка страницы -->
    <VRow class="mb-4 align-center">
      <VCol cols="12" md="8">
        <h2 class="text-h4 font-weight-bold mb-1 d-flex align-center gap-2">
          <VIcon icon="ri-puzzle-line" color="primary" />
          Модульный монолит и плагины
        </h2>
        <p class="text-body-1 text-medium-emphasis mb-0">
          Управление независимыми блоками и расширениями админ-панели без перезагрузки системы
        </p>
      </VCol>
      <VCol cols="12" md="4" class="text-md-end">
        <VBtn
          color="primary"
          prepend-icon="ri-refresh-line"
          :loading="loading"
          @click="loadModules"
        >
          Обновить реестр
        </VBtn>
      </VCol>
    </VRow>

    <!-- Сводная статистика -->
    <VRow class="mb-4">
      <VCol cols="12" sm="4">
        <VCard variant="tonal" color="primary" class="pa-4">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-caption font-weight-medium">Всего модулей в реестре</div>
              <div class="text-h4 font-weight-bold">{{ totalCount }}</div>
            </div>
            <VIcon icon="ri-apps-line" size="40" />
          </div>
        </VCard>
      </VCol>

      <VCol cols="12" sm="4">
        <VCard variant="tonal" color="success" class="pa-4">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-caption font-weight-medium">Активно и загружено</div>
              <div class="text-h4 font-weight-bold">{{ activeCount }}</div>
            </div>
            <VIcon icon="ri-checkbox-circle-line" size="40" />
          </div>
        </VCard>
      </VCol>

      <VCol cols="12" sm="4">
        <VCard variant="tonal" color="info" class="pa-4">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-caption font-weight-medium">Архитектура ядра</div>
              <div class="text-h6 font-weight-bold">Modular Monolith</div>
            </div>
            <VIcon icon="ri-shield-check-line" size="40" />
          </div>
        </VCard>
      </VCol>
    </VRow>

    <!-- Фильтры и поиск -->
    <VCard class="mb-6">
      <VCardText>
        <VRow dense align="center">
          <VCol cols="12" md="6">
            <VTextField
              v-model="searchQuery"
              placeholder="Поиск по названию, коду или описанию..."
              density="compact"
              variant="outlined"
              prepend-inner-icon="ri-search-line"
              clearable
              hide-details
            />
          </VCol>
          <VCol cols="12" md="6">
            <VSelect
              v-model="selectedCategory"
              :items="categories"
              item-title="title"
              item-value="value"
              density="compact"
              variant="outlined"
              prepend-inner-icon="ri-filter-line"
              hide-details
            />
          </VCol>
        </VRow>
      </VCardText>
    </VCard>

    <!-- Список модулей -->
    <VRow v-if="filteredModules.length > 0">
      <VCol
        v-for="mod in filteredModules"
        :key="mod.slug"
        cols="12"
        md="6"
        lg="4"
      >
        <VCard class="h-100 d-flex flex-column justify-space-between" variant="outlined">
          <VCardItem>
            <template #prepend>
              <VAvatar color="primary" variant="tonal" rounded size="44">
                <VIcon :icon="mod.icon || 'ri-puzzle-line'" size="26" />
              </VAvatar>
            </template>
            <VCardTitle class="text-h6 font-weight-bold">
              {{ mod.name }}
            </VCardTitle>
            <VCardSubtitle class="d-flex align-center gap-2 mt-1">
              <span>v{{ mod.version }}</span>
              <span>•</span>
              <span>{{ mod.author }}</span>
            </VCardSubtitle>
          </VCardItem>

          <VCardText class="flex-grow-1">
            <p class="text-body-2 text-medium-emphasis mb-3">
              {{ mod.description || 'Модуль расширения функционала админ-панели' }}
            </p>

            <div class="d-flex flex-wrap gap-2 align-center">
              <!-- Статус бейдж -->
              <VChip
                v-if="mod.error"
                color="error"
                size="small"
                variant="flat"
                prepend-icon="ri-error-warning-line"
                class="cursor-pointer"
                @click="openErrorDialog(mod)"
              >
                Ошибка загрузки
              </VChip>
              <VChip
                v-else-if="mod.is_enabled && mod.is_loaded"
                color="success"
                size="small"
                variant="flat"
                prepend-icon="ri-checkbox-circle-line"
              >
                Работает
              </VChip>
              <VChip
                v-else
                color="secondary"
                size="small"
                variant="tonal"
                prepend-icon="ri-pause-circle-line"
              >
                Отключен
              </VChip>

              <VChip
                v-if="mod.is_system"
                color="info"
                size="small"
                variant="outlined"
              >
                Ядро системы
              </VChip>

              <VChip size="small" variant="text" class="text-capitalize">
                {{ mod.category }}
              </VChip>
            </div>
          </VCardText>

          <VDivider />

          <VCardActions class="px-4 py-3 d-flex justify-space-between align-center">
            <div>
              <VBtn
                v-if="mod.route_path && mod.is_enabled"
                :to="mod.route_path"
                variant="text"
                color="primary"
                size="small"
                prepend-icon="ri-external-link-line"
              >
                Открыть
              </VBtn>
            </div>

            <div class="d-flex align-center gap-2">
              <span class="text-caption text-medium-emphasis">
                {{ mod.is_enabled ? 'Включен' : 'Выключен' }}
              </span>
              <VSwitch
                :model-value="mod.is_enabled"
                :disabled="mod.is_system || togglingSlug === mod.slug"
                :loading="togglingSlug === mod.slug"
                color="success"
                density="compact"
                hide-details
                @click.prevent="toggleModule(mod)"
              />
            </div>
          </VCardActions>
        </VCard>
      </VCol>
    </VRow>

    <VCard v-else-if="!loading" class="pa-12 text-center" variant="outlined">
      <VIcon icon="ri-inbox-line" size="64" color="medium-emphasis" class="mb-3" />
      <h3 class="text-h6 font-weight-medium mb-1">Модули не найдены</h3>
      <p class="text-body-2 text-medium-emphasis">
        По текущему фильтру или запросу ничего не найдено.
      </p>
    </VCard>

    <!-- Диалог деталей ошибки -->
    <VDialog v-model="errorDialog" max-width="600">
      <VCard>
        <VCardTitle class="d-flex align-center gap-2 text-error">
          <VIcon icon="ri-error-warning-line" />
          Ошибка модуля {{ selectedError.name }}
        </VCardTitle>
        <VCardText>
          <p class="text-body-2 mb-2">При загрузке или регистрации модуля возникло исключение:</p>
          <pre class="pa-3 bg-surface border rounded text-caption text-error overflow-auto" style="max-height: 250px; white-space: pre-wrap;">{{ selectedError.error }}</pre>
        </VCardText>
        <VCardActions class="justify-end">
          <VBtn variant="text" @click="errorDialog = false">Закрыть</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Уведомления -->
    <VSnackbar v-model="snackbar" :color="snackbarColor" timeout="3000" location="top right">
      {{ snackbarText }}
    </VSnackbar>
  </div>
</template>
