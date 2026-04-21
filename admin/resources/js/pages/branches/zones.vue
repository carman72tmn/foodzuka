<script setup>
import { ref, onMounted, computed } from "vue"
import YandexDeliveryMap from "@/components/YandexDeliveryMap.vue"

const loading = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const branches = ref([])
const selectedBranch = ref(null)
const zones = ref([])
const polygons = ref([])
const fileInput = ref(null)
const yandexSettings = ref(null)
const deliveryMap = ref(null)

const API_BASE = "/api/v1"

const zoneHeaders = [
  { title: "ID", key: "id", sortable: true, width: 70 },
  { title: "Название", key: "name", sortable: true },
  { title: "Привязанные полигоны", key: "custom_polygons", sortable: false },
  { title: "Мин. заказ (₽)", key: "min_order_amount", sortable: true },
  { title: "Ст-ть доставки (₽)", key: "delivery_cost", sortable: true },
  { title: "Активна", key: "is_active", sortable: true, width: 100 },
]

const polygonHeaders = [
  { title: "Название полигона", key: "name", sortable: true },
  { title: "Зона iiko", key: "delivery_zone_id", sortable: true, width: 200 },
  { title: "Точек", key: "points_count", sortable: false, width: 100 },
  { title: "Действия", key: "actions", sortable: false, width: 120 },
]

const editDialog = ref(false)
const editedPolygon = ref({
  id: null,
  name: '',
  description: '',
  min_delivery_time: null,
  max_delivery_time: null,
  min_order_amount: 0,
  delivery_cost: 0,
  free_delivery_threshold: 0,
  fill_color: '#4caf50',
  priority: 0
})

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const loadData = async () => {
  loading.value = true
  try {
    const [branchesRes, yandexRes] = await Promise.all([
      fetch(`${API_BASE}/branches/`),
      fetch(`${API_BASE}/yandex/settings`)
    ])
    
    if (branchesRes.ok) {
      branches.value = await branchesRes.json()
      if (branches.value.length > 0) {
        selectedBranch.value = branches.value[0].id
        await loadBranchData(selectedBranch.value)
      }
    }
    
    if (yandexRes.ok) {
      yandexSettings.value = await yandexRes.json()
    }
  } catch (e) {
    showMessage("Ошибка загрузки данных", "error")
  } finally {
    loading.value = false
  }
}

const loadBranchData = async (branchId) => {
  if (!branchId) return
  loading.value = true
  try {
    const [zonesRes, polygonsRes] = await Promise.all([
      fetch(`${API_BASE}/branches/${branchId}/zones`),
      fetch(`${API_BASE}/branches/${branchId}/polygons`)
    ])
    
    if (zonesRes.ok) zones.value = await zonesRes.json()
    if (polygonsRes.ok) polygons.value = await polygonsRes.json()
  } catch (e) {
    showMessage("Ошибка загрузки зон доставки", "error")
  } finally {
    loading.value = false
  }
}

const onBranchChange = (newVal) => {
  loadBranchData(newVal)
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  const formData = new FormData()
  formData.append('file', file)
  
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/branches/${selectedBranch.value}/polygons/upload`, {
      method: 'POST',
      body: formData
    })
    
    if (res.ok) {
      showMessage("Полигоны успешно загружены")
      await loadBranchData(selectedBranch.value)
    } else {
      const err = await res.json()
      if (Array.isArray(err.detail)) {
        showMessage(`Ошибка валидации: ${err.detail[0].msg}`, "error")
      } else {
        showMessage(err.detail || "Ошибка загрузки файла", "error")
      }
    }
  } catch (e) {
    showMessage("Ошибка при отправке файла", "error")
  } finally {
    loading.value = false
    if (fileInput.value) fileInput.value.value = ""
  }
}

const assignPolygon = async (polygonId, zoneId) => {
  try {
    const res = await fetch(`${API_BASE}/branches/polygons/${polygonId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ delivery_zone_id: zoneId || null })
    })
    if (res.ok) {
      showMessage("Привязка обновлена")
      await loadBranchData(selectedBranch.value)
    }
  } catch (e) {
    showMessage("Ошибка при обновлении привязки", "error")
  }
}

const openEditPolygon = (item) => {
  editedPolygon.value = { ...item }
  editDialog.value = true
}

const savePolygonEdit = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/branches/polygons/${editedPolygon.value.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editedPolygon.value)
    })
    
    if (res.ok) {
      showMessage("Данные полигона обновлены")
      editDialog.value = false
      await loadBranchData(selectedBranch.value)
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка сохранения", "error")
    }
  } catch (e) {
    showMessage("Ошибка при сохранении", "error")
  } finally {
    loading.value = false
  }
}

const deletePolygon = async (id) => {
  if (!confirm("Удалить этот полигон?")) return
  try {
    const res = await fetch(`${API_BASE}/branches/polygons/${id}`, {
      method: 'DELETE'
    })
    if (res.ok) {
      showMessage("Полигон удален")
      await loadBranchData(selectedBranch.value)
    }
  } catch (e) {
    showMessage("Ошибка при удалении", "error")
  }
}

const focusOnPolygon = (poly) => {
  if (deliveryMap.value) {
    deliveryMap.value.focusOnPolygon('custom', poly.id)
  }
}

onMounted(loadData)
</script>

<template>
  <VRow>
    <!-- Map Section -->
    <VCol cols="12">
      <VCard class="mb-6">
        <VCardTitle class="d-flex align-center py-4">
          <VIcon icon="bx-map" class="me-2" />
          Карта зон доставки
          <VSpacer />
          <VChip v-if="yandexSettings?.api_key_js" color="success" size="small" variant="tonal">
            Яндекс.Карты подключены
          </VChip>
          <VChip v-else color="error" size="small" variant="tonal">
            Яндекс.Карты не настроены
          </VChip>
        </VCardTitle>
        <VCardText>
          <YandexDeliveryMap 
            v-if="yandexSettings?.api_key_js"
            ref="deliveryMap"
            :zones="zones"
            :custom-polygons="polygons"
            :api-key="yandexSettings.api_key_js"
          />
          <VAlert v-else type="warning" variant="tonal">
            Для визуализации зон необходимо указать JavaScript API ключ в настройках Яндекса.
          </VAlert>
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12">
      <VCard class="mb-6">
        <VCardTitle class="d-flex align-center py-4">
          <VIcon icon="bx-map-alt" class="me-2" />
          Зоны доставки iiko
          <VSpacer />
          <div style="width: 300px" class="me-4">
             <VSelect
              v-model="selectedBranch"
              :items="branches"
              item-title="name"
              item-value="id"
              label="Выберите филиал"
              density="compact"
              hide-details
              @update:modelValue="onBranchChange"
            />
          </div>
          <VBtn color="primary" @click="loadBranchData(selectedBranch)" class="me-2" :loading="loading" variant="tonal" size="small">
            <VIcon icon="bx-refresh" /> Обновить
          </VBtn>
        </VCardTitle>
        
        <VCardText>
          <VDataTable
            :headers="zoneHeaders"
            :items="zones"
            :loading="loading"
            class="elevation-1"
            density="compact"
          >
            <template #item.custom_polygons="{ item }">
              <div class="d-flex flex-wrap gap-1 py-1">
                <VChip v-for="p in polygons.filter(poly => poly.delivery_zone_id === item.id)" 
                  :key="p.id" size="x-small" :color="p.fill_color || 'info'" variant="flat">
                  {{ p.name }}
                </VChip>
                <span v-if="!polygons.some(poly => poly.delivery_zone_id === item.id)" class="text-caption text-grey">
                  Нет полигонов
                </span>
              </div>
            </template>
            <template #item.is_active="{ item }">
              <VChip :color="item.is_active ? 'success' : 'error'" variant="tonal" size="small">
                {{ item.is_active ? "Активна" : "Пассивна" }}
              </VChip>
            </template>
          </VDataTable>
        </VCardText>
      </VCard>

      <VCard>
        <VCardTitle class="d-flex align-center py-4">
          <VIcon icon="bx-layer" class="me-2" />
          Загруженные полигоны (KML/GeoJSON)
          <VSpacer />
          <input type="file" ref="fileInput" @change="handleFileUpload" accept=".kml,.json,.geojson" style="display: none">
          <VBtn color="success" size="small" @click="fileInput.click()" :disabled="!selectedBranch" class="me-2">
            <VIcon icon="bx-upload" class="me-1" /> Загрузить файл
          </VBtn>
        </VCardTitle>
        
        <VCardText>
          <VDataTable
            :headers="polygonHeaders"
            :items="polygons"
            :loading="loading"
            class="elevation-1"
            density="compact"
          >
            <template #item.name="{ item }">
               <div class="d-flex align-center">
                 <div :style="{ backgroundColor: item.fill_color || '#4caf50', width: '12px', height: '12px', borderRadius: '50%' }" class="me-2"></div>
                 {{ item.name }}
               </div>
            </template>
            <template #item.points_count="{ item }">
              {{ item.coordinates ? item.coordinates.length : 0 }} точек
            </template>
            <template #item.delivery_zone_id="{ item }">
              <VSelect
                v-model="item.delivery_zone_id"
                :items="zones"
                item-title="name"
                item-value="id"
                label="Привязать к зоне"
                density="compact"
                hide-details
                clearable
                @update:modelValue="(val) => assignPolygon(item.id, val)"
                variant="underlined"
                class="mt-0"
              />
            </template>
            <template #item.actions="{ item }">
              <div class="d-flex gap-1">
                <VBtn icon="bx-show" variant="text" size="small" color="primary" title="Показать на карте" @click="focusOnPolygon(item)"></VBtn>
                <VBtn icon="bx-edit" variant="text" size="small" color="info" title="Редактировать" @click="openEditPolygon(item)"></VBtn>
                <VBtn icon="bx-trash" variant="text" size="small" color="error" title="Удалить" @click="deletePolygon(item.id)"></VBtn>
              </div>
            </template>
          </VDataTable>
          
          <VAlert type="info" variant="tonal" class="mt-4" density="compact">
            Загрузите KML или GeoJSON файл. Затем сопоставьте каждый полигон с соответствующей зоной доставки из iiko. 
            Одной зоне iiko можно назначить несколько полигонов.
          </VAlert>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <!-- Edit Polygon Dialog -->
  <VDialog v-model="editDialog" max-width="600px">
    <VCard>
      <VCardTitle class="py-4">
        Редактирование полигона: {{ editedPolygon.name }}
      </VCardTitle>
      <VCardText>
        <VRow>
          <VCol cols="12" md="6">
            <VTextField v-model="editedPolygon.name" label="Название" density="compact" />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField v-model="editedPolygon.fill_color" label="Цвет заливки (HEX)" density="compact" type="color" />
          </VCol>
          <VCol cols="12">
            <VTextarea v-model="editedPolygon.description" label="Описание" density="compact" rows="2" />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField v-model.number="editedPolygon.min_delivery_time" label="Мин. время доставки (мин)" density="compact" type="number" />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField v-model.number="editedPolygon.max_delivery_time" label="Макс. время доставки (мин)" density="compact" type="number" />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField v-model.number="editedPolygon.min_order_amount" label="Мин. сумма заказа (₽)" density="compact" type="number" />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField v-model.number="editedPolygon.delivery_cost" label="Стоимость доставки (₽)" density="compact" type="number" />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField v-model.number="editedPolygon.free_delivery_threshold" label="Бесплатная доставка от (₽)" density="compact" type="number" />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField v-model.number="editedPolygon.priority" label="Приоритет (чем выше, тем главнее)" density="compact" type="number" hint="Используется для наложения полигонов друг на друга" persistent-hint />
          </VCol>
        </VRow>
      </VCardText>
      <VCardActions class="pa-4">
        <VSpacer />
        <VBtn variant="text" @click="editDialog = false">Отмена</VBtn>
        <VBtn color="primary" variant="elevated" @click="savePolygonEdit" :loading="loading">Сохранить</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <VSnackbar v-model="snackbar" :color="snackbarColor" :timeout="3000" location="top">
    {{ snackbarText }}
  </VSnackbar>
</template>

<style scoped>
.gap-1 {
  display: flex;
  gap: 4px;
}
</style>
