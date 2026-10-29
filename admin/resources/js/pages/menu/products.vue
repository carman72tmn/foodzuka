<script setup>
import { ref, onMounted, computed } from "vue"

const loading = ref(false)
const syncLoading = ref(false)
const stopSyncLoading = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const activeMainTab = ref("menu_products") // "menu_products" | "modifiers" | "uncategorized"

const search = ref("")
const selectedCategory = ref(null)
const filterStopList = ref(false)

const products = ref([])
const categories = ref([])
const branches = ref([])
const modifierGroups = ref([])

const API_BASE = "/api/v1"

// Диалог подробностей
const productDialog = ref(false)
const selectedProduct = ref(null)
const productDetails = ref(null)
const detailsLoading = ref(false)

// Редактирование товара
const isEditing = ref(false)
const saveLoading = ref(false)
const editForm = ref({
  name: "",
  price: 0,
  old_price: null,
  description: "",
  tags: "",
  is_available: true,
  is_popular: false,
  sort_order: 0
})

const startEdit = () => {
  if (!selectedProduct.value) return
  editForm.value = {
    name: selectedProduct.value.name,
    price: selectedProduct.value.price,
    old_price: selectedProduct.value.old_price,
    description: selectedProduct.value.description || "",
    tags: selectedProduct.value.tags || "",
    is_available: selectedProduct.value.is_available,
    is_popular: selectedProduct.value.is_popular || false,
    sort_order: selectedProduct.value.sort_order || 0
  }
  isEditing.value = true
}

const cancelEdit = () => {
  isEditing.value = false
}

const toggleModifierVisibility = async (modifier) => {
  try {
    const res = await fetch(`${API_BASE}/products/modifiers/${modifier.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_visible: modifier.is_visible })
    })
    if (res.ok) {
      showMessage("Видимость модификатора изменена")
    } else {
      modifier.is_visible = !modifier.is_visible
      showMessage("Ошибка изменения видимости", "error")
    }
  } catch (e) {
    modifier.is_visible = !modifier.is_visible
    showMessage("Ошибка сети", "error")
  }
}

const saveProduct = async () => {
  if (!selectedProduct.value) return
  saveLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/products/${selectedProduct.value.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: editForm.value.name,
        price: editForm.value.price,
        old_price: editForm.value.old_price,
        description: editForm.value.description,
        tags: editForm.value.tags,
        is_available: editForm.value.is_available,
        is_popular: editForm.value.is_popular,
        sort_order: editForm.value.sort_order
      })
    })
    if (res.ok) {
      const updated = await res.json()
      const idx = products.value.findIndex(p => p.id === selectedProduct.value.id)
      if (idx > -1) {
        products.value[idx] = { ...products.value[idx], ...updated }
      }
      selectedProduct.value = { ...selectedProduct.value, ...updated }
      showMessage("Товар успешно сохранен")
      isEditing.value = false
    } else {
      showMessage("Ошибка сохранения товара", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    saveLoading.value = false
  }
}

const headers = [
  { title: "Товар", key: "name", sortable: true },
  { title: "Категория", key: "category_name", sortable: true },
  { title: "Цена", key: "price", sortable: true, width: 120 },
  { title: "Статус", key: "status", sortable: false, width: 150 },
  { title: "Действия", key: "actions", sortable: false, width: 120 },
]

const modifierHeaders = [
  { title: "Модификатор", key: "name", sortable: true },
  { title: "Группа модификаторов", key: "group_name", sortable: true },
  { title: "Привязанный товар", key: "product_name", sortable: true },
  { title: "Цена", key: "price", sortable: true, width: 120 },
  { title: "Видимость на сайте", key: "is_visible", sortable: false, width: 160 },
]

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const formatPrice = (value) => {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(value || 0)
}

const loadData = async () => {
  loading.value = true
  try {
    const [pRes, cRes, bRes, mRes] = await Promise.all([
      fetch(`${API_BASE}/products/?limit=2000`),
      fetch(`${API_BASE}/categories/`),
      fetch(`${API_BASE}/branches/`),
      fetch(`${API_BASE}/products/modifiers/all`)
    ])
    
    if (pRes.ok) products.value = await pRes.json()
    if (cRes.ok) categories.value = await cRes.json()
    if (bRes.ok) branches.value = await bRes.json()
    if (mRes.ok) modifierGroups.value = await mRes.json()
  } catch (e) {
    showMessage("Ошибка загрузки данных", "error")
  } finally {
    loading.value = false
  }
}

// Фильтры товаров
const activeCategoryIds = computed(() => new Set(categories.value.filter(c => c.name !== 'Служебная').map(c => c.id)))

const menuProductsList = computed(() => {
  return products.value.filter(p => p.category_id && activeCategoryIds.value.has(p.category_id))
})

const uncategorizedProductsList = computed(() => {
  return products.value.filter(p => !p.category_id || !activeCategoryIds.value.has(p.category_id))
})

const filteredMenuProducts = computed(() => {
  return menuProductsList.value.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.value.toLowerCase()) || 
                         (p.article && p.article.toLowerCase().includes(search.value.toLowerCase()))
    const matchesCategory = !selectedCategory.value || p.category_id === selectedCategory.value
    const matchesStop = !filterStopList.value || p.is_stopped
    return matchesSearch && matchesCategory && matchesStop
  }).map(p => ({
    ...p,
    category_name: categories.value.find(c => c.id === p.category_id)?.name || "—"
  }))
})

const filteredUncategorizedProducts = computed(() => {
  return uncategorizedProductsList.value.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.value.toLowerCase()) || 
                         (p.article && p.article.toLowerCase().includes(search.value.toLowerCase()))
    const matchesStop = !filterStopList.value || p.is_stopped
    return matchesSearch && matchesStop
  }).map(p => ({
    ...p,
    category_name: categories.value.find(c => c.id === p.category_id)?.name || "Без категории"
  }))
})

// Модификаторы плоский список
const flatModifiersList = computed(() => {
  const list = []
  modifierGroups.value.forEach(g => {
    (g.modifiers || []).forEach(m => {
      list.push({
        id: m.id,
        iiko_id: m.iiko_id,
        name: m.name,
        group_name: g.name,
        product_name: g.product_name || "—",
        price: m.price,
        is_visible: m.is_visible !== false,
        raw_modifier: m
      })
    })
  })
  return list
})

const filteredModifiers = computed(() => {
  if (!search.value) return flatModifiersList.value
  const q = search.value.toLowerCase()
  return flatModifiersList.value.filter(m => 
    m.name.toLowerCase().includes(q) || 
    m.group_name.toLowerCase().includes(q) || 
    m.product_name.toLowerCase().includes(q)
  )
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
    const res = await fetch(`${API_BASE}/iiko/sync-stop-list`, { method: 'POST' })
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
  isEditing.value = false
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

const deleteAllProducts = async () => {
  if (!confirm("Вы уверены, что хотите БЕЗВОЗВРАТНО удалить все товары? Это очистит каталог.")) return
  
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/products/all`, { method: 'DELETE' })
    if (res.ok) {
      showMessage("Все товары удалены", "success")
      loadData()
    }
  } catch (e) {
    showMessage("Ошибка при удалении", "error")
  } finally {
    loading.value = false
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
          <div class="text-h5 font-weight-bold">Каталог товаров и модификаторов</div>
          
          <VSpacer />
          
          <VBtn
            color="warning"
            prepend-icon="mdi-cancel"
            variant="tonal"
            :loading="stopSyncLoading"
            @click="syncStopList"
          >
            Стоп-листы
          </VBtn>

          <VBtn
            color="error"
            prepend-icon="mdi-delete-sweep"
            variant="tonal"
            :loading="loading"
            @click="deleteAllProducts"
          >
            Удалить всё
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

        <!-- Переключатель категорий/модификаторов/прочего -->
        <VTabs v-model="activeMainTab" color="primary" class="border-b px-4 bg-grey-lighten-4">
          <VTab value="menu_products">
            <VIcon icon="mdi-silverware-fork-knife" class="me-2" />
            Блюда и товары меню ({{ menuProductsList.length }})
          </VTab>
          <VTab value="modifiers">
            <VIcon icon="mdi-tune-vertical" class="me-2" />
            Модификаторы iiko ({{ flatModifiersList.length }})
          </VTab>
          <VTab value="uncategorized">
            <VIcon icon="mdi-folder-question-outline" class="me-2" />
            Прочие позиции / Без категории ({{ uncategorizedProductsList.length }})
          </VTab>
        </VTabs>

        <VCardText class="bg-grey-lighten-5 py-4 border-y">
          <VRow>
            <VCol cols="12" md="4">
              <VTextField
                v-model="search"
                :label="activeMainTab === 'modifiers' ? 'Поиск модификатора или группы' : 'Поиск по названию или артикулу'"
                prepend-inner-icon="mdi-magnify"
                variant="outlined"
                density="compact"
                hide-details
                bg-color="white"
              />
            </VCol>
            <VCol cols="12" md="3" v-if="activeMainTab === 'menu_products'">
              <VSelect
                v-model="selectedCategory"
                :items="categories.filter(c => c.name !== 'Служебная')"
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
            <VCol cols="12" md="3" v-if="activeMainTab !== 'modifiers'">
              <VCheckbox
                v-model="filterStopList"
                label="Только в стоп-листе"
                hide-details
                color="error"
              />
            </VCol>
          </VRow>
        </VCardText>

        <!-- Таб 1: Блюда внешнего меню -->
        <div v-if="activeMainTab === 'menu_products'">
          <VDataTable
            :headers="headers"
            :items="filteredMenuProducts"
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
                  <div class="text-caption text-medium-emphasis mb-1">Арт: {{ item.article || '—' }}</div>
                  <div v-if="item.tags" class="d-flex flex-wrap gap-1">
                    <VChip 
                      v-for="t in item.tags.split(',').map(x => x.trim()).filter(Boolean)" 
                      :key="t" 
                      size="x-small" 
                      color="primary" 
                      variant="flat"
                    >
                      {{ t }}
                    </VChip>
                  </div>
                </div>
              </div>
            </template>

            <template #item.price="{ item }">
              <div class="text-h6 font-weight-bold text-primary">{{ formatPrice(item.price) }}</div>
              <div v-if="item.old_price" class="text-caption text-decoration-line-through text-medium-emphasis">
                {{ formatPrice(item.old_price) }}
              </div>
            </template>

            <template #item.status="{ item }">
              <div class="d-flex flex-column gap-1">
                <VChip
                  v-if="item.is_on_stop_list || item.is_stopped"
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
        </div>

        <!-- Таб 2: Модификаторы iiko -->
        <div v-else-if="activeMainTab === 'modifiers'">
          <VDataTable
            :headers="modifierHeaders"
            :items="filteredModifiers"
            :loading="loading"
            :items-per-page="50"
            hover
          >
            <template #item.name="{ item }">
              <div class="font-weight-bold py-2" :class="{ 'text-grey text-decoration-line-through': !item.is_visible }">
                {{ item.name }}
              </div>
              <div class="text-caption text-medium-emphasis">ID: {{ item.iiko_id || '—' }}</div>
            </template>

            <template #item.group_name="{ item }">
              <VChip size="small" color="secondary" variant="tonal">
                {{ item.group_name }}
              </VChip>
            </template>

            <template #item.product_name="{ item }">
              <span class="text-body-2">{{ item.product_name }}</span>
            </template>

            <template #item.price="{ item }">
              <span class="text-subtitle-1 font-weight-bold text-primary">+{{ formatPrice(item.price) }}</span>
            </template>

            <template #item.is_visible="{ item }">
              <VSwitch 
                v-model="item.is_visible" 
                density="compact" 
                color="success" 
                hide-details 
                @change="toggleModifierVisibility(item.raw_modifier)" 
              />
            </template>
          </VDataTable>
        </div>

        <!-- Таб 3: Прочие позиции iiko -->
        <div v-else-if="activeMainTab === 'uncategorized'">
          <VDataTable
            :headers="headers"
            :items="filteredUncategorizedProducts"
            :loading="loading"
            :items-per-page="50"
            hover
          >
            <template #item.name="{ item }">
              <div class="d-flex align-center py-2">
                <VAvatar size="40" class="me-3 border">
                  <VImg v-if="item.image_url" :src="item.image_url" cover />
                  <VIcon v-else icon="mdi-help-box-outline" color="grey" />
                </VAvatar>
                <div>
                  <div class="font-weight-bold">{{ item.name }}</div>
                  <div class="text-caption text-medium-emphasis">Арт: {{ item.article || '—' }}</div>
                </div>
              </div>
            </template>

            <template #item.price="{ item }">
              <div class="text-subtitle-1 font-weight-bold">{{ formatPrice(item.price) }}</div>
            </template>

            <template #item.status="{ item }">
              <VChip
                :color="item.is_available ? 'success' : 'grey'"
                size="x-small"
                variant="outlined"
              >
                {{ item.is_available ? 'Доступен' : 'Скрыт' }}
              </VChip>
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
        </div>

      </VCard>
    </VCol>
  </VRow>

  <!-- Диалог подробностей -->
  <VDialog v-model="productDialog" max-width="900" scrollable>
    <VCard v-if="selectedProduct">
      <VCardTitle class="d-flex align-center bg-primary text-white pa-4">
        <span>{{ isEditing ? 'Редактирование товара' : selectedProduct.name }}</span>
        <VSpacer />
        <VBtn
          v-if="!isEditing"
          color="white"
          variant="tonal"
          prepend-icon="mdi-pencil"
          class="me-2"
          @click="startEdit"
        >
          Редактировать
        </VBtn>
        <VBtn
          v-else
          color="success"
          variant="flat"
          prepend-icon="mdi-check"
          class="me-2"
          :loading="saveLoading"
          @click="saveProduct"
        >
          Сохранить
        </VBtn>
        <VBtn
          v-if="isEditing"
          color="white"
          variant="text"
          class="me-2"
          @click="cancelEdit"
        >
          Отмена
        </VBtn>
        <VBtn icon="mdi-close" variant="text" @click="productDialog = false" />
      </VCardTitle>

      <VCardText class="pa-0">
        <!-- Режим редактирования -->
        <VRow no-gutters v-if="isEditing" class="pa-6">
          <VCol cols="12" md="6" class="pe-md-4">
            <VTextField v-model="editForm.name" label="Название товара" variant="outlined" class="mb-4" />
            <VRow>
              <VCol cols="6">
                <VTextField v-model.number="editForm.price" label="Новая цена (Цена)" type="number" variant="outlined" class="mb-4" />
              </VCol>
              <VCol cols="6">
                <VTextField v-model.number="editForm.old_price" label="Старая цена" type="number" variant="outlined" class="mb-4" clearable />
              </VCol>
            </VRow>
            <VTextField v-model="editForm.tags" label="Метки / Бейджи (через запятую)" placeholder="Хит, Новинка, Острое, Веган" variant="outlined" class="mb-4" />
            <VTextField v-model.number="editForm.sort_order" label="Порядок сортировки в меню" type="number" variant="outlined" class="mb-4" />
            <div class="d-flex gap-4 mb-4">
              <VSwitch v-model="editForm.is_available" label="Доступен для заказа" color="success" />
              <VSwitch v-model="editForm.is_popular" label="Популярный (Popular)" color="primary" />
            </div>
          </VCol>
          <VCol cols="12" md="6" class="ps-md-4">
            <VTextarea v-model="editForm.description" label="Описание товара" variant="outlined" rows="8" class="mb-4" />
          </VCol>
        </VRow>

        <!-- Режим просмотра подробностей -->
        <VRow no-gutters v-else>
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
              <div class="d-flex justify-space-between align-center mb-2">
                <span class="text-medium-emphasis">Популярный (Popular):</span>
                <VIcon :icon="selectedProduct.is_popular ? 'mdi-star' : 'mdi-star-outline'" :color="selectedProduct.is_popular ? 'warning' : 'grey'" />
              </div>
              <div v-if="selectedProduct.tags" class="d-flex flex-column gap-1 mt-2">
                <span class="text-medium-emphasis text-caption">Метки:</span>
                <div class="d-flex flex-wrap gap-1 mt-1">
                  <VChip v-for="t in selectedProduct.tags.split(',').map(x => x.trim()).filter(Boolean)" :key="t" size="small" color="primary" variant="flat">
                    {{ t }}
                  </VChip>
                </div>
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

              <!-- Группы модификаторов -->
              <div class="text-subtitle-1 font-weight-bold mt-6 mb-2">Группы модификаторов</div>
              <VExpansionPanels v-if="selectedProduct.modifier_groups && selectedProduct.modifier_groups.length > 0" class="mb-4">
                <VExpansionPanel v-for="group in selectedProduct.modifier_groups" :key="group.id">
                  <VExpansionPanelTitle>
                    <div class="d-flex align-center">
                      <VIcon icon="mdi-view-list-outline" class="me-2" color="secondary" />
                      {{ group.name }}
                      <VChip size="x-small" variant="tonal" class="ms-2">
                        {{ group.iiko_id }}
                      </VChip>
                    </div>
                  </VExpansionPanelTitle>
                  <VExpansionPanelText>
                    <VTable density="compact" class="border rounded">
                      <thead>
                        <tr>
                          <th>Модификатор</th>
                          <th class="text-right">Цена</th>
                          <th class="text-center" style="width: 100px;">Видимость</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="mod in group.modifiers" :key="mod.id">
                          <td class="text-caption">
                            <span :class="{ 'text-grey text-decoration-line-through': mod.is_visible === false }">
                              {{ mod.name }} 
                            </span>
                            <span class="text-grey ms-1" v-if="mod.article">({{ mod.article }})</span>
                          </td>
                          <td class="text-right text-caption font-weight-bold">
                            {{ mod.price }} ₽
                          </td>
                          <td class="text-center">
                            <VSwitch 
                              v-model="mod.is_visible" 
                              density="compact" 
                              color="success" 
                              hide-details 
                              @change="toggleModifierVisibility(mod)" 
                            />
                          </td>
                        </tr>
                      </tbody>
                    </VTable>
                  </VExpansionPanelText>
                </VExpansionPanel>
              </VExpansionPanels>
              <VAlert v-else type="info" variant="tonal" density="compact" class="mb-4 text-caption">
                У данного товара нет групп модификаторов.
              </VAlert>

              <!-- Стоп-листы -->
              <div v-if="selectedProduct.is_on_stop_list || selectedProduct.is_stopped" class="pa-4 bg-red-lighten-5 rounded border border-error mb-4">
                <div class="d-flex align-center justify-space-between mb-2">
                  <div class="d-flex align-center">
                     <VIcon icon="mdi-alert-octagon" color="error" class="me-2" />
                     <span class="text-error font-weight-bold">ВНИМАНИЕ: ТОВАР В СТОП-ЛИСТЕ</span>
                  </div>
                  <div v-if="selectedProduct.stopped_at" class="text-caption text-error">
                    Дата: {{ new Date(selectedProduct.stopped_at).toLocaleString() }}
                  </div>
                </div>
                <div class="text-body-2">
                  Согласно данным из iiko, данный товар недоступен для заказа.
                  <div v-if="selectedProduct.stop_list_branch_ids && selectedProduct.stop_list_branch_ids.length" class="mt-2">
                    В филиалах (ID):
                    <div class="d-flex flex-wrap gap-1 mt-1">
                      <VChip v-for="bid in selectedProduct.stop_list_branch_ids" :key="bid" size="x-small" color="error">
                        {{ bid }}
                      </VChip>
                    </div>
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
.gap-1 { gap: 4px; }
.gap-2 { gap: 8px; }
.gap-4 { gap: 16px; }
</style>
