<script setup>
import { ref, onMounted, computed, watch } from "vue"

const loading = ref(false)
const syncLoading = ref(false)
const stopSyncLoading = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const search = ref("")
const selectedCategory = ref(null)
const filterStopList = ref(false)

const products = ref([])
const categories = ref([])
const branches = ref([])

const API_BASE = "/api/v1"

// Диалог подробностей
const productDialog = ref(false)
const selectedProduct = ref(null)
const productDetails = ref(null)
const detailsLoading = ref(false)

const headers = [
  { title: "Товар", key: "name", sortable: true },
  { title: "Категория", key: "category_name", sortable: true },
  { title: "Цена", key: "price", sortable: true, width: 120 },
  { title: "Статус", key: "status", sortable: false, width: 150 },
  { title: "Действия", key: "actions", sortable: false, width: 120 },
]

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const formatPrice = (value) => {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(value)
}

const loadData = async () => {
  loading.value = true
  try {
    const [pRes, cRes, bRes] = await Promise.all([
      fetch(`${API_BASE}/products/?limit=1000`),
      fetch(`${API_BASE}/categories/`),
      fetch(`${API_BASE}/branches/`)
    ])
    
    if (pRes.ok) products.value = await pRes.json()
    if (cRes.ok) categories.value = await cRes.json()
    if (bRes.ok) branches.value = await bRes.json()
  } catch (e) {
    showMessage("Ошибка загрузки данных", "error")
  } finally {
    loading.value = false
  }
}

const filteredProducts = computed(() => {
  return products.value.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.value.toLowerCase()) || 
                         (p.article && p.article.toLowerCase().includes(search.value.toLowerCase()))
    const matchesCategory = !selectedCategory.value || p.category_id === selectedCategory.value
    const matchesStop = !filterStopList.value || p.is_on_stop_list
    return matchesSearch && matchesCategory && matchesStop
  }).map(p => ({
    ...p,
    category_name: categories.value.find(c => c.id === p.category_id)?.name || "—"
  }))
})

const syncMenu = async () => {
  syncLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/iiko/sync-menu`, { method: 'POST' })
    if (res.ok) {
      showMessage("Синхронизация меню запущена")
      loadData()
    }
  } finally {
    syncLoading.value = false
  }
}

const syncStopList = async () => {
  stopSyncLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/products/sync-stop-list`, { method: 'POST' })
    if (res.ok) {
      showMessage("Стоп-листы обновлены")
      loadData()
    }
  } finally {
    stopSyncLoading.value = false
  }
}

const viewDetails = async (product) => {
  selectedProduct.value = product
  productDialog.value = true
  detailsLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/products/${product.id}/iiko-details`)
    if (res.ok) {
      productDetails.value = await res.json()
    } else {
      productDetails.value = null
    }
  } catch (e) {
    productDetails.value = null
  } finally {
    detailsLoading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard class="elevation-2 border">
        <VCardTitle class="d-flex align-center flex-wrap py-4 px-6 gap-4">
          <VIcon icon="mdi-food-variant" color="primary" size="32" class="me-2" />
          <div class="text-h5 font-weight-bold">Товары и меню</div>
          
          <VSpacer />
          
          <VBtn
            color="warning"
            prepend-icon="mdi-cancel"
            variant="tonal"
            :loading="stopSyncLoading"
            @click="syncStopList"
          >
            Стоп-лист iiko
          </VBtn>
          
          <VBtn
            color="primary"
            prepend-icon="mdi-sync"
            :loading="syncLoading"
            @click="syncMenu"
          >
            Синхронизировать меню
          </VBtn>
        </VCardTitle>

        <VCardText class="bg-grey-lighten-5 py-4 border-y">
          <VRow>
            <VCol cols="12" md="4">
              <VTextField
                v-model="search"
                label="Поиск по названию или артикулу"
                prepend-inner-icon="mdi-magnify"
                variant="outlined"
                density="compact"
                hide-details
                bg-color="white"
              />
            </VCol>
            <VCol cols="12" md="3">
              <VSelect
                v-model="selectedCategory"
                :items="categories"
                item-title="name"
                item-value="id"
                label="Категория"
                variant="outlined"
                density="compact"
                hide-details
                clearable
                bg-color="white"
              />
            </VCol>
            <VCol cols="12" md="3">
              <VCheckbox
                v-model="filterStopList"
                label="Только в стоп-листе"
                hide-details
                color="error"
              />
            </VCol>
          </VRow>
        </VCardText>

        <VDataTable
          :headers="headers"
          :items="filteredProducts"
          :loading="loading"
          :items-per-page="50"
          hover
        >
          <template #item.name="{ item }">
            <div class="d-flex align-center py-2">
              <VAvatar size="40" class="me-3 border">
                <VImg v-if="item.image_url" :src="item.image_url" cover />
                <VIcon v-else icon="mdi-food-apple-outline" color="grey" />
              </VAvatar>
              <div>
                <div class="font-weight-bold">{{ item.name }}</div>
                <div class="text-caption text-medium-emphasis">Арт: {{ item.article || '—' }}</div>
              </div>
            </div>
          </template>

          <template #item.price="{ item }">
            <div class="text-h6 font-weight-bold text-primary">{{ formatPrice(item.price) }}</div>
          </template>

          <template #item.status="{ item }">
            <div class="d-flex flex-column gap-1">
              <VChip
                v-if="item.is_on_stop_list"
                color="error"
                size="x-small"
                variant="flat"
                prepend-icon="mdi-cancel"
                class="font-weight-bold"
              >
                В СТОП-ЛИСТЕ
              </VChip>
              <VChip
                :color="item.is_available ? 'success' : 'grey'"
                size="x-small"
                variant="outlined"
              >
                {{ item.is_available ? 'Доступен' : 'Скрыт' }}
              </VChip>
            </div>
          </template>

          <template #item.actions="{ item }">
            <VBtn
              color="primary"
              variant="tonal"
              size="small"
              prepend-icon="mdi-eye-outline"
              @click="viewDetails(item)"
              class="rounded-pill"
            >
              Подробнее
            </VBtn>
          </template>
        </VDataTable>
      </VCard>
    </VCol>
  </VRow>

  <!-- Диалог подробностей -->
  <VDialog v-model="productDialog" max-width="900" scrollable>
    <VCard v-if="selectedProduct">
      <VCardTitle class="d-flex align-center bg-primary text-white pa-4">
        <span>{{ selectedProduct.name }}</span>
        <VSpacer />
        <VBtn icon="mdi-close" variant="text" @click="productDialog = false" />
      </VCardTitle>

      <VCardText class="pa-0">
        <VRow no-gutters>
          <VCol cols="12" md="4" class="pa-4 border-e bg-grey-lighten-4">
            <VImg
              v-if="selectedProduct.image_url"
              :src="selectedProduct.image_url"
              class="rounded-lg mb-4 border shadow-sm"
              cover
              aspect-ratio="1"
            />
            <div class="d-flex flex-column gap-2">
              <div class="text-subtitle-2 text-medium-emphasis">ID в iiko:</div>
              <code class="pa-2 bg-white rounded border">{{ selectedProduct.iiko_id }}</code>
              
              <div class="text-subtitle-2 text-medium-emphasis mt-2">Категория:</div>
              <div class="font-weight-bold">{{ selectedProduct.category_name }}</div>
              
              <VDivider class="my-4" />
              
              <div v-if="selectedProduct.weight_grams" class="d-flex justify-space-between align-center mb-2">
                <span class="text-medium-emphasis">Вес:</span>
                <span class="font-weight-bold">{{ selectedProduct.weight_grams }} г</span>
              </div>
              <div v-if="selectedProduct.volume_ml" class="d-flex justify-space-between align-center mb-2">
                <span class="text-medium-emphasis">Объем:</span>
                <span class="font-weight-bold">{{ selectedProduct.volume_ml }} мл</span>
              </div>
            </div>
          </VCol>

          <VCol cols="12" md="8" class="pa-4 bg-white">
            <div class="text-h6 mb-4 border-b pb-2">Описание продукта</div>
            <p class="text-body-1 mb-6 text-medium-emphasis">
              {{ selectedProduct.description || 'Описание отсутствует' }}
            </p>

            <!-- КБЖУ -->
            <div class="text-h6 mb-4 border-b pb-2">Пищевая ценность (на 100г)</div>
            <VRow class="mb-6">
              <VCol cols="3">
                <VCard variant="tonal" color="orange" class="text-center pa-2">
                  <div class="text-h6">{{ selectedProduct.calories || 0 }}</div>
                  <div class="text-caption">Ккал</div>
                </VCard>
              </VCol>
              <VCol cols="3">
                <VCard variant="tonal" color="green" class="text-center pa-2">
                  <div class="text-h6">{{ selectedProduct.proteins || 0 }}</div>
                  <div class="text-caption">Белки</div>
                </VCard>
              </VCol>
              <VCol cols="3">
                <VCard variant="tonal" color="blue" class="text-center pa-2">
                  <div class="text-h6">{{ selectedProduct.fats || 0 }}</div>
                  <div class="text-caption">Жиры</div>
                </VCard>
              </VCol>
              <VCol cols="3">
                <VCard variant="tonal" color="purple" class="text-center pa-2">
                  <div class="text-h6">{{ selectedProduct.carbohydrates || 0 }}</div>
                  <div class="text-caption">Углеводы</div>
                </VCard>
              </VCol>
            </VRow>

            <!-- Размеры и Модификаторы из локальной копии -->
            <VTabs color="primary" class="mb-4 border-b">
              <VTab value="sizes">Размеры и цены</VTab>
              <VTab value="modifiers">Модификаторы</VTab>
              <VTab value="stops">Стоп-лист</VTab>
            </VTabs>

            <div class="py-4">
              <!-- Размеры -->
              <VTable v-if="selectedProduct.sizes && selectedProduct.sizes.length > 0">
                <thead>
                  <tr>
                    <th>Название</th>
                    <th class="text-right">Цена</th>
                    <th class="text-center">По умолчанию</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="s in selectedProduct.sizes" :key="s.id">
                    <td>{{ s.name }}</td>
                    <td class="text-right font-weight-bold">{{ formatPrice(s.price) }}</td>
                    <td class="text-center">
                      <VIcon v-if="s.is_default" icon="mdi-check-circle" color="success" />
                      <span v-else>—</span>
                    </td>
                  </tr>
                </tbody>
              </VTable>

              <!-- Модификаторы -->
              <VExpansionPanels v-if="selectedProduct.modifier_groups && selectedProduct.modifier_groups.length > 0">
                <VExpansionPanel v-for="g in selectedProduct.modifier_groups" :key="g.id">
                  <VExpansionPanelTitle>
                    <div class="d-flex align-center gap-2">
                      <span class="font-weight-bold">{{ g.name }}</span>
                      <VChip size="x-small" color="primary" variant="tonal">
                        Мин: {{ g.min_amount }} / Макс: {{ g.max_amount }}
                      </VChip>
                      <VChip v-if="g.is_required" size="x-small" color="error" variant="flat">Обязательно</VChip>
                    </div>
                  </VExpansionPanelTitle>
                  <VExpansionPanelText>
                    <VList density="compact">
                      <VListItem v-for="m in g.modifiers" :key="m.id">
                        <template #prepend>
                          <VIcon icon="mdi-circle-small" />
                        </template>
                        <VListItemTitle>{{ m.name }}</VListItemTitle>
                        <template #append>
                          <span class="text-primary font-weight-bold">+{{ formatPrice(m.price) }}</span>
                        </template>
                      </VListItem>
                    </VList>
                  </VExpansionPanelText>
                </VExpansionPanel>
              </VExpansionPanels>

              <!-- Стоп-листы -->
              <div v-if="selectedProduct.is_on_stop_list" class="pa-4 bg-red-lighten-5 rounded border border-error mb-4">
                <div class="d-flex align-center mb-2">
                  <VIcon icon="mdi-alert-octagon" color="error" class="me-2" />
                  <span class="text-error font-weight-bold">ВНИМАНИЕ: ТОВАР В СТОП-ЛИСТЕ</span>
                </div>
                <div class="text-body-2">
                  Согласно данным из iiko, данный товар недоступен для заказа в следующих филиалах (ID):
                  <div class="d-flex flex-wrap gap-1 mt-2">
                    <VChip v-for="bid in selectedProduct.stop_list_branch_ids" :key="bid" size="x-small" color="error">
                      {{ bid }}
                    </VChip>
                  </div>
                </div>
              </div>
              <div v-else class="pa-4 bg-green-lighten-5 rounded border border-success mb-4 text-success text-center font-weight-bold">
                 ТОВАР ДОСТУПЕН ВО ВСЕХ ФИЛИАЛАХ
              </div>
            </div>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>
  </VDialog>

  <VSnackbar v-model="snackbar" :color="snackbarColor" :timeout="3000" location="top right">
    {{ snackbarText }}
  </VSnackbar>
</template>

<style scoped>
.gap-2 { gap: 8px; }
.gap-4 { gap: 16px; }
</style>
