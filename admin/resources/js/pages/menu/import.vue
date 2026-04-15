<script setup>
import { ref, onMounted, onUnmounted } from "vue"

const loading = ref({
  menu: false,
  prices: false,
  stops: false,
  sections: false
})

const settings = ref({
  organization_id: "—",
  external_menu_id: "—"
})

const syncLogs = ref([])
const logsLoading = ref(false)

const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const API_BASE = "/api/v1"

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const fetchSettings = async () => {
  try {
    const res = await fetch(`${API_BASE}/iiko/settings`)
    if (res.ok) {
      settings.value = await res.json()
    }
  } catch (e) {}
}

const fetchLogs = async () => {
  logsLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/iiko/sync-logs?limit=10`)
    if (res.ok) {
      syncLogs.value = await res.json()
    }
  } catch (e) {}
  finally { logsLoading.value = false }
}

const startSync = async (type, endpoint, isFastapiV1 = false) => {
  loading.value[type] = true
  const url = isFastapiV1 ? `${API_BASE}/${endpoint}` : `${API_BASE}/iiko/${endpoint}`
  
  try {
    const res = await fetch(url, { method: 'POST' })
    const data = await res.json()
    if (res.ok) {
      showMessage(data.message || "Задача запущена успешно")
      setTimeout(fetchLogs, 1000)
    } else {
      showMessage(data.detail || "Ошибка запуска задачи", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    loading.value[type] = false
  }
}

let logInterval = null
onMounted(() => {
  fetchSettings()
  fetchLogs()
  logInterval = setInterval(fetchLogs, 10000) // Обновляем логи каждые 10 сек
})

onUnmounted(() => {
  if (logInterval) clearInterval(logInterval)
})
</script>

<template>
  <VRow>
    <!-- Карточки управления -->
    <VCol cols="12" md="6" lg="3">
      <VCard class="text-center h-100 py-4 border shadow-sm">
        <VCardText>
          <VAvatar color="primary" variant="tonal" size="64" class="mb-4">
            <VIcon icon="mdi-sync" size="32" />
          </VAvatar>
          <h3 class="text-h6 font-weight-bold mb-2">Полное меню</h3>
          <p class="text-caption text-medium-emphasis mb-6 px-4">
            Загрузка всех товаров, категорий, модификаторов и фото.
          </p>
          <VBtn :loading="loading.menu" color="primary" @click="startSync('menu', 'sync-menu')" class="rounded-pill px-6">
            Запустить
          </VBtn>
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12" md="6" lg="3">
      <VCard class="text-center h-100 py-4 border shadow-sm">
        <VCardText>
          <VAvatar color="info" variant="tonal" size="64" class="mb-4">
            <VIcon icon="mdi-currency-rub" size="32" />
          </VAvatar>
          <h3 class="text-h6 font-weight-bold mb-2">Обновить цены</h3>
          <p class="text-caption text-medium-emphasis mb-6 px-4">
            Быстрая синхронизация только цен по External Menu API v2.
          </p>
          <VBtn :loading="loading.prices" color="info" @click="startSync('prices', 'sync-prices')" class="rounded-pill px-6">
            Обновить
          </VBtn>
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12" md="6" lg="3">
      <VCard class="text-center h-100 py-4 border shadow-sm">
        <VCardText>
          <VAvatar color="error" variant="tonal" size="64" class="mb-4">
            <VIcon icon="mdi-cancel" size="32" />
          </VAvatar>
          <h3 class="text-h6 font-weight-bold mb-2">Стоп-листы</h3>
          <p class="text-caption text-medium-emphasis mb-6 px-4">
            Загрузить актуальные остатки и блокировки филиалов из iiko.
          </p>
          <VBtn :loading="loading.stops" color="error" @click="startSync('stops', 'sync-stop-list', true)" class="rounded-pill px-6">
            Загрузить
          </VBtn>
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12" md="6" lg="3">
      <VCard class="text-center h-100 py-4 border shadow-sm">
        <VCardText>
          <VAvatar color="secondary" variant="tonal" size="64" class="mb-4">
            <VIcon icon="mdi-folder-sync" size="32" />
          </VAvatar>
          <h3 class="text-h6 font-weight-bold mb-2">Разделы (v2)</h3>
          <p class="text-caption text-medium-emphasis mb-6 px-4">
            Синхронизация структуры категорий, подкатегорий и их фото.
          </p>
          <VBtn :loading="loading.sections" color="secondary" @click="startSync('sections', 'categories/sync-from-iiko', true)" class="rounded-pill px-6">
            Обновить
          </VBtn>
        </VCardText>
      </VCard>
    </VCol>

    <!-- Настройки -->
    <VCol cols="12" md="4">
      <VCard class="elevation-2 border">
        <VCardTitle class="pa-4 font-weight-bold">
           <VIcon icon="mdi-cog-outline" class="me-2" /> Настройки iiko
        </VCardTitle>
        <VCardText class="pa-4">
           <div class="mb-4">
              <div class="text-caption text-medium-emphasis">Organization ID:</div>
              <div class="font-weight-medium">{{ settings.organization_id }}</div>
           </div>
           <div class="mb-4">
              <div class="text-caption text-medium-emphasis">External Menu ID:</div>
              <div class="font-weight-medium">{{ settings.external_menu_id }}</div>
           </div>
           <VDivider class="mb-4" />
           <VBtn block variant="tonal" to="/admin/settings" prepend-icon="mdi-pencil">Изменить в настройках</VBtn>
        </VCardText>
      </VCard>
    </VCol>

    <!-- Логи -->
    <VCol cols="12" md="8">
      <VCard class="elevation-2 border">
        <VCardTitle class="pa-4 d-flex align-center font-weight-bold">
           <VIcon icon="mdi-history" class="me-2" /> Последние синхронизации
           <VSpacer />
           <VBtn icon="mdi-refresh" variant="text" size="small" :loading="logsLoading" @click="fetchLogs" />
        </VCardTitle>
        <VCardText class="pa-0">
           <VDataTable
              :items="syncLogs"
              :headers="[
                 { title: 'Тип', key: 'sync_type' },
                 { title: 'Статус', key: 'status' },
                 { title: 'Детали', key: 'details' },
                 { title: 'Дата', key: 'created_at' }
              ]"
              density="compact"
              hide-default-footer
           >
              <template #item.sync_type="{ item }">
                 <span class="text-capitalize font-weight-medium">{{ item.sync_type }}</span>
              </template>
              <template #item.status="{ item }">
                 <VChip :color="item.status === 'success' ? 'success' : (item.status === 'running' ? 'warning' : 'error')" 
                        size="x-small" label class="font-weight-bold">
                    {{ item.status.toUpperCase() }}
                 </VChip>
              </template>
              <template #item.created_at="{ item }">
                 <span class="text-caption">{{ new Date(item.created_at).toLocaleString('ru-RU') }}</span>
              </template>
           </VDataTable>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <VSnackbar v-model="snackbar" :color="snackbarColor" :timeout="3000" location="top right">
    {{ snackbarText }}
  </VSnackbar>
</template>
