<script setup>
import { ref, onMounted, computed } from 'vue'
import { getAuthHeaders, hasPermission } from '@/utils/auth'
import { useToast } from 'vue-toastification'

const toast = useToast()

// Табы
const positionsTabs = computed(() => {
  const allTabs = [
    { value: 'positions', title: 'Позиции закупа', permission: 'purchase_positions_tab_positions_view' },
    { value: 'suppliers', title: 'Поставщики', permission: 'purchase_positions_tab_suppliers_view' },
    { value: 'subcategories', title: 'Подкатегории', permission: 'purchase_positions_tab_subcategories_view' }
  ]
  return allTabs.filter(t => hasPermission(t.permission))
})
const activeTab = ref(null)

// Состояния для позиций закупа
const positions = ref([])
const loading = ref(true)
const search = ref('')
const categoryFilter = ref('all')

// Состояния для поставщиков
const suppliers = ref([])
const suppliersLoading = ref(false)
const supplierSearch = ref('')

// Диалоги позиций
const isDialogVisible = ref(false)
const isDeleting = ref(false)
const deleteDialog = ref(false)
const positionToDelete = ref(null)

// Диалоги поставщиков
const isSupplierDialogVisible = ref(false)
const isSupplierDeleting = ref(false)
const supplierDeleteDialog = ref(false)
const supplierToDelete = ref(null)

// Настройки таблицы позиций
const headers = [
  { title: 'Название позиции', key: 'name' },
  { title: 'Направление', key: 'category' },
  { title: 'Подкатегория', key: 'subcategory' },
  { title: 'Поставщик', key: 'supplier.name' },
  { title: 'Ед. измерения', key: 'unit' },
  { title: 'Активна', key: 'is_active' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'end' }
]

// Настройки таблицы поставщиков
const supplierHeaders = [
  { title: 'Название поставщика', key: 'name' },
  { title: 'Телефон', key: 'phone' },
  { title: 'Email', key: 'email' },
  { title: 'Комментарий', key: 'comment' },
  { title: 'Активен', key: 'is_active' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'end' }
]

const unitOptions = ['шт', 'кг', 'л', 'упак', 'рулон', 'короб', 'банка', 'бутылка', 'пачка', 'м']

const subcategoryOptions = [
  'Молочка', 'Овощи', 'Крупы', 'Мясо', 'Морепродукты', 'Фрукты', 'Зелень', 'Бакалея', 
  'Напитки', 'Заморозка', 'Хлебобулочные', 'Соусы/Специи', 'Химия', 'Хозтовары', 'Канцелярия', 'Расходники'
]

// Редактируемые объекты
const editedItem = ref({
  id: null,
  name: '',
  category: 'shop',
  subcategory: '',
  unit: 'шт',
  supplier_id: null,
  is_active: true
})

const defaultItem = {
  id: null,
  name: '',
  category: 'shop',
  subcategory: '',
  unit: 'шт',
  supplier_id: null,
  is_active: true
}

const editedSupplier = ref({
  id: null,
  name: '',
  phone: '',
  email: '',
  comment: '',
  is_active: true
})

const defaultSupplier = {
  id: null,
  name: '',
  phone: '',
  email: '',
  comment: '',
  is_active: true
}

const formTitle = computed(() => editedItem.value.id ? 'Редактировать позицию' : 'Новая позиция')
const supplierFormTitle = computed(() => editedSupplier.value.id ? 'Редактировать поставщика' : 'Новый поставщик')

// Загрузка поставщиков
const fetchSuppliers = async () => {
  suppliersLoading.value = true
  try {
    const response = await fetch('/api/v1/purchase/suppliers', {
      headers: getAuthHeaders()
    })
    if (response.ok) {
      suppliers.value = await response.json()
    } else {
      toast.error('Не удалось загрузить справочник поставщиков')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка загрузки поставщиков')
  } finally {
    suppliersLoading.value = false
  }
}

// Загрузка позиций
const fetchPositions = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/purchase/positions', {
      headers: getAuthHeaders()
    })
    if (response.ok) {
      positions.value = await response.json()
    } else {
      toast.error('Не удалось загрузить справочник позиций')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка загрузки позиций')
  } finally {
    loading.value = false
  }
}

// Фильтрация позиций для отображения
const filteredPositions = computed(() => {
  return positions.value.filter(item => {
    const matchesCategory = categoryFilter.value === 'all' || item.category === categoryFilter.value
    const matchesSearch = item.name.toLowerCase().includes(search.value.toLowerCase()) || 
                          (item.subcategory && item.subcategory.toLowerCase().includes(search.value.toLowerCase()))
    return matchesCategory && matchesSearch
  })
})

// Фильтрация поставщиков для отображения
const filteredSuppliers = computed(() => {
  return suppliers.value.filter(item => {
    return item.name.toLowerCase().includes(supplierSearch.value.toLowerCase()) ||
           (item.phone && item.phone.toLowerCase().includes(supplierSearch.value.toLowerCase())) ||
           (item.comment && item.comment.toLowerCase().includes(supplierSearch.value.toLowerCase()))
  })
})

// --- Методы для позиций ---
const editItem = (item) => {
  editedItem.value = { ...item }
  isDialogVisible.value = true
}

const close = () => {
  isDialogVisible.value = false
  editedItem.value = { ...defaultItem }
}

const save = async () => {
  if (!editedItem.value.name.trim()) {
    toast.warning('Название позиции обязательно для заполнения')
    return
  }

  const method = editedItem.value.id ? 'PATCH' : 'POST'
  const url = editedItem.value.id ? `/api/v1/purchase/positions/${editedItem.value.id}` : '/api/v1/purchase/positions'
  
  try {
    const response = await fetch(url, {
      method,
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(editedItem.value)
    })
    
    if (response.ok) {
      toast.success(editedItem.value.id ? 'Позиция обновлена' : 'Позиция создана')
      await fetchPositions()
      close()
    } else {
      const err = await response.json()
      toast.error(err.detail || 'Не удалось сохранить позицию')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка соединения с сервером')
  }
}

const confirmDelete = (item) => {
  positionToDelete.value = item
  deleteDialog.value = true
}

const deleteItem = async () => {
  isDeleting.value = true
  try {
    const response = await fetch(`/api/v1/purchase/positions/${positionToDelete.value.id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      toast.success('Позиция удалена из справочника')
      await fetchPositions()
      deleteDialog.value = false
    } else {
      toast.error('Не удалось удалить позицию. Возможно, она используется в списках закупа.')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка соединения')
  } finally {
    isDeleting.value = false
  }
}

// --- Методы для поставщиков ---
const editSupplier = (item) => {
  editedSupplier.value = { ...item }
  isSupplierDialogVisible.value = true
}

const closeSupplier = () => {
  isSupplierDialogVisible.value = false
  editedSupplier.value = { ...defaultSupplier }
}

const saveSupplier = async () => {
  if (!editedSupplier.value.name.trim()) {
    toast.warning('Название поставщика обязательно для заполнения')
    return
  }

  const method = editedSupplier.value.id ? 'PATCH' : 'POST'
  const url = editedSupplier.value.id ? `/api/v1/purchase/suppliers/${editedSupplier.value.id}` : '/api/v1/purchase/suppliers'
  
  try {
    const response = await fetch(url, {
      method,
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(editedSupplier.value)
    })
    
    if (response.ok) {
      toast.success(editedSupplier.value.id ? 'Поставщик обновлен' : 'Поставщик создан')
      await fetchSuppliers()
      await fetchPositions() // Обновим, чтобы подтянуть свежее имя поставщика в таблицы
      closeSupplier()
    } else {
      const err = await response.json()
      toast.error(err.detail || 'Не удалось сохранить поставщика')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка соединения с сервером')
  }
}

const confirmDeleteSupplier = (item) => {
  supplierToDelete.value = item
  supplierDeleteDialog.value = true
}

const deleteSupplierItem = async () => {
  isSupplierDeleting.value = true
  try {
    const response = await fetch(`/api/v1/purchase/suppliers/${supplierToDelete.value.id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      toast.success('Поставщик удален')
      await fetchSuppliers()
      await fetchPositions()
      supplierDeleteDialog.value = false
    } else {
      toast.error('Не удалось удалить поставщика. Возможно, он используется.')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка соединения')
  } finally {
    isSupplierDeleting.value = false
  }
}

// Хелперы отображения
const getCategoryLabel = (cat) => {
  switch (cat) {
    case 'supply': return 'Поставки'
    case 'shop': return 'Магазин'
    case 'household': return 'Хозка'
    default: return cat
  }
}

const getCategoryColor = (cat) => {
  switch (cat) {
    case 'supply': return 'primary'
    case 'shop': return 'success'
    case 'household': return 'warning'
    default: return 'secondary'
  }
}

// Состояния для подкатегорий закупа
const subcategories = ref([])
const subcategoriesLoading = ref(false)
const subcategorySearch = ref('')
const isSubcategoryDialogVisible = ref(false)
const subcategoryDeleteDialog = ref(false)
const subcategoryToDelete = ref(null)
const isSubcategoryDeleting = ref(false)

const editedSubcategory = ref({
  id: null,
  name: ''
})

const defaultSubcategory = {
  id: null,
  name: ''
}

const subcategoryFormTitle = computed(() => editedSubcategory.value.id ? 'Редактировать подкатегорию' : 'Новая подкатегория')

// Загрузка подкатегорий
const fetchSubcategories = async () => {
  subcategoriesLoading.value = true
  try {
    const response = await fetch('/api/v1/purchase/subcategories', {
      headers: getAuthHeaders()
    })
    if (response.ok) {
      subcategories.value = await response.json()
    } else {
      toast.error('Не удалось загрузить справочник подкатегорий')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка загрузки подкатегорий')
  } finally {
    subcategoriesLoading.value = false
  }
}

// Фильтрация подкатегорий для отображения
const filteredSubcategories = computed(() => {
  return subcategories.value.filter(item => {
    return item.name.toLowerCase().includes(subcategorySearch.value.toLowerCase())
  })
})

// Методы CRUD подкатегорий
const editSubcategory = (item) => {
  editedSubcategory.value = { ...item }
  isSubcategoryDialogVisible.value = true
}

const closeSubcategory = () => {
  isSubcategoryDialogVisible.value = false
  editedSubcategory.value = { ...defaultSubcategory }
}

const saveSubcategory = async () => {
  if (!editedSubcategory.value.name.trim()) {
    toast.warning('Название подкатегории обязательно для заполнения')
    return
  }

  const method = editedSubcategory.value.id ? 'PATCH' : 'POST'
  const url = editedSubcategory.value.id ? `/api/v1/purchase/subcategories/${editedSubcategory.value.id}` : '/api/v1/purchase/subcategories'
  
  try {
    const response = await fetch(url, {
      method,
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(editedSubcategory.value)
    })
    
    if (response.ok) {
      toast.success(editedSubcategory.value.id ? 'Подкатегория обновлена' : 'Подкатегория создана')
      await fetchSubcategories()
      closeSubcategory()
    } else {
      const err = await response.json()
      toast.error(err.detail || 'Не удалось сохранить подкатегорию')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка соединения с сервером')
  }
}

const confirmDeleteSubcategory = (item) => {
  subcategoryToDelete.value = item
  subcategoryDeleteDialog.value = true
}

const deleteSubcategoryItem = async () => {
  isSubcategoryDeleting.value = true
  try {
    const response = await fetch(`/api/v1/purchase/subcategories/${subcategoryToDelete.value.id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      toast.success('Подкатегория удалена')
      await fetchSubcategories()
      subcategoryDeleteDialog.value = false
    } else {
      toast.error('Не удалось удалить подкатегорию. Возможно, она используется.')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка соединения')
  } finally {
    isSubcategoryDeleting.value = false
  }
}

const canEditCurrentTab = computed(() => {
  if (!hasPermission('purchase_positions_edit')) return false
  if (activeTab.value === 'positions') return hasPermission('purchase_positions_tab_positions_edit')
  if (activeTab.value === 'suppliers') return hasPermission('purchase_positions_tab_suppliers_edit')
  if (activeTab.value === 'subcategories') return hasPermission('purchase_positions_tab_subcategories_edit')
  return false
})

onMounted(() => {
  fetchPositions()
  fetchSuppliers()
  fetchSubcategories()
  activeTab.value = positionsTabs.value.length ? positionsTabs.value[0].value : null
})
</script>

<template>
  <div class="positions-page">
    <VRow class="align-center mb-6">
      <VCol cols="12" sm="6">
        <h1 class="text-h4 font-weight-bold d-flex align-center gap-2">
          <VIcon icon="ri-file-list-3-line" color="primary" />
          Справочники закупа
        </h1>
      </VCol>
      <VCol cols="12" sm="6" class="text-sm-end">
        <VBtn
          v-if="canEditCurrentTab"
          color="primary"
          prepend-icon="ri-add-line"
          @click="activeTab === 'positions' ? (isDialogVisible = true) : (activeTab === 'suppliers' ? (isSupplierDialogVisible = true) : (isSubcategoryDialogVisible = true))"
        >
          {{ activeTab === 'positions' ? 'Создать позицию' : (activeTab === 'suppliers' ? 'Добавить поставщика' : 'Добавить подкатегорию') }}
        </VBtn>
      </VCol>
    </VRow>

    <VTabs v-model="activeTab" class="mb-6" v-if="positionsTabs.length">
      <VTab
        v-for="tab in positionsTabs"
        :key="tab.value"
        :value="tab.value"
      >
        {{ tab.title }}
      </VTab>
    </VTabs>

    <VWindow v-model="activeTab">
      <!-- ВКЛАДКА ПОЗИЦИЙ -->
      <VWindowItem value="positions">
        <VCard class="mb-6">
          <VCardText>
            <VRow>
              <VCol cols="12" sm="6" md="4">
                <VTextField
                  v-model="search"
                  placeholder="Поиск по названию или подкатегории..."
                  prepend-inner-icon="ri-search-line"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                />
              </VCol>
              <VCol cols="12" sm="6" md="4">
                <VSelect
                  v-model="categoryFilter"
                  :items="[
                    { title: 'Все направления', value: 'all' },
                    { title: 'Поставки', value: 'supply' },
                    { title: 'Магазин', value: 'shop' },
                    { title: 'Хозка', value: 'household' }
                  ]"
                  item-title="title"
                  item-value="value"
                  label="Фильтр по направлению"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                />
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <VCard class="bg-transparent border-0 elevation-0">
          <!-- Десктопная версия (таблица) -->
          <div class="d-none d-md-block bg-var-theme-surface rounded border elevation-1">
            <VDataTable
              :headers="headers"
              :items="filteredPositions"
              :loading="loading"
              hover
              no-data-text="Позиции закупа не найдены"
              loading-text="Загрузка позиций..."
            >
              <!-- Стилизация столбца категории -->
              <template #item.category="{ item }">
                <VChip
                  :color="getCategoryColor(item.category)"
                  size="small"
                  label
                  class="font-weight-medium"
                >
                  {{ getCategoryLabel(item.category) }}
                </VChip>
              </template>

              <!-- Стилизация подкатегории -->
              <template #item.subcategory="{ item }">
                <span class="font-weight-medium text-body-2 text-high-emphasis">
                  {{ item.subcategory || '—' }}
                </span>
              </template>

              <!-- Стилизация поставщика -->
              <template #item.supplier.name="{ item }">
                <span class="text-body-2 color-secondary">
                  {{ item.supplier?.name || '—' }}
                </span>
              </template>

              <!-- Стилизация единицы измерения -->
              <template #item.unit="{ item }">
                <span class="font-weight-medium">{{ item.unit }}</span>
              </template>

              <!-- Стилизация столбца активности -->
              <template #item.is_active="{ item }">
                <VIcon
                  :icon="item.is_active ? 'ri-checkbox-circle-line' : 'ri-close-circle-line'"
                  :color="item.is_active ? 'success' : 'error'"
                />
              </template>

              <!-- Столбец действий -->
              <template #item.actions="{ item }">
                <div class="d-flex justify-end gap-1">
                  <VBtn
                    v-if="hasPermission('purchase_positions_tab_positions_edit')"
                    icon="ri-edit-line"
                    size="small"
                    variant="text"
                    color="primary"
                    @click="editItem(item)"
                  />
                  <VBtn
                    v-if="hasPermission('purchase_positions_tab_positions_edit')"
                    icon="ri-delete-bin-line"
                    size="small"
                    variant="text"
                    color="error"
                    @click="confirmDelete(item)"
                  />
                </div>
              </template>
            </VDataTable>
          </div>

          <!-- Мобильная версия (карточки) -->
          <div class="d-block d-md-none">
            <div v-if="filteredPositions.length === 0" class="d-flex flex-column align-center my-8 py-8 bg-var-theme-surface rounded border elevation-1">
              <VIcon icon="ri-inbox-line" size="48" color="disabled" class="mb-2" />
              <div class="text-body-1 text-disabled">Позиции закупа не найдены</div>
            </div>
            <div v-else>
              <VCard
                v-for="item in filteredPositions"
                :key="item.id"
                class="mb-4 border rounded-lg elevation-1 pa-4"
              >
                <div class="d-flex justify-space-between align-start mb-2">
                  <div>
                    <div class="font-weight-bold text-subtitle-1 text-primary">{{ item.name }}</div>
                    <div class="text-caption text-muted">Ед. изм.: {{ item.unit }}</div>
                  </div>
                  <VChip
                    :color="getCategoryColor(item.category)"
                    size="small"
                    label
                    class="font-weight-bold"
                  >
                    {{ getCategoryLabel(item.category) }}
                  </VChip>
                </div>
                
                <VDivider class="my-2" />
                
                <div class="text-body-2 mb-4">
                  <div class="mb-1">
                    Подкатегория: <strong class="text-high-emphasis">{{ item.subcategory || '—' }}</strong>
                  </div>
                  <div class="mb-1">
                    Поставщик: <strong class="text-high-emphasis">{{ item.supplier?.name || '—' }}</strong>
                  </div>
                  <div class="d-flex align-center mt-2">
                    Статус: 
                    <VIcon
                      :icon="item.is_active ? 'ri-checkbox-circle-line' : 'ri-close-circle-line'"
                      :color="item.is_active ? 'success' : 'error'"
                      size="18"
                      class="ms-1 me-1 align-center"
                    />
                    <span class="font-weight-medium" :class="item.is_active ? 'text-success' : 'text-error'">
                      {{ item.is_active ? 'Активен' : 'Неактивен' }}
                    </span>
                  </div>
                </div>
                
                <div class="d-flex gap-2" v-if="hasPermission('purchase_positions_tab_positions_edit')">
                  <VBtn
                    color="primary"
                    variant="flat"
                    prepend-icon="ri-edit-line"
                    size="small"
                    class="flex-grow-1"
                    @click="editItem(item)"
                  >
                    Редактировать
                  </VBtn>
                  <VBtn
                    color="error"
                    variant="outlined"
                    icon="ri-delete-bin-line"
                    size="small"
                    @click="confirmDelete(item)"
                  />
                </div>
              </VCard>
            </div>
          </div>
        </VCard>
      </VWindowItem>

      <!-- ВКЛАДКА ПОСТАВЩИКОВ -->
      <VWindowItem value="suppliers">
        <VCard class="mb-6">
          <VCardText>
            <VRow>
              <VCol cols="12" sm="6" md="4">
                <VTextField
                  v-model="supplierSearch"
                  placeholder="Поиск поставщика..."
                  prepend-inner-icon="ri-search-line"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                />
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <VCard class="bg-transparent border-0 elevation-0">
          <!-- Десктопная версия (таблица) -->
          <div class="d-none d-md-block bg-var-theme-surface rounded border elevation-1">
            <VDataTable
              :headers="supplierHeaders"
              :items="filteredSuppliers"
              :loading="suppliersLoading"
              hover
              no-data-text="Поставщики не найдены"
              loading-text="Загрузка поставщиков..."
            >
              <!-- Стилизация столбца активности -->
              <template #item.is_active="{ item }">
                <VIcon
                  :icon="item.is_active ? 'ri-checkbox-circle-line' : 'ri-close-circle-line'"
                  :color="item.is_active ? 'success' : 'error'"
                />
              </template>

              <!-- Столбец действий -->
              <template #item.actions="{ item }">
                <div class="d-flex justify-end gap-1">
                  <VBtn
                    v-if="hasPermission('purchase_positions_tab_suppliers_edit')"
                    icon="ri-edit-line"
                    size="small"
                    variant="text"
                    color="primary"
                    @click="editSupplier(item)"
                  />
                  <VBtn
                    v-if="hasPermission('purchase_positions_tab_suppliers_edit')"
                    icon="ri-delete-bin-line"
                    size="small"
                    variant="text"
                    color="error"
                    @click="confirmDeleteSupplier(item)"
                  />
                </div>
              </template>
            </VDataTable>
          </div>

          <!-- Мобильная версия (карточки) -->
          <div class="d-block d-md-none">
            <div v-if="filteredSuppliers.length === 0" class="d-flex flex-column align-center my-8 py-8 bg-var-theme-surface rounded border elevation-1">
              <VIcon icon="ri-inbox-line" size="48" color="disabled" class="mb-2" />
              <div class="text-body-1 text-disabled">Поставщики не найдены</div>
            </div>
            <div v-else>
              <VCard
                v-for="item in filteredSuppliers"
                :key="item.id"
                class="mb-4 border rounded-lg elevation-1 pa-4"
              >
                <div class="d-flex justify-space-between align-start mb-2">
                  <div>
                    <div class="font-weight-bold text-subtitle-1 text-primary">{{ item.name }}</div>
                    <div class="text-caption text-muted" v-if="item.comment">Примечание: {{ item.comment }}</div>
                  </div>
                  <div class="d-flex align-center">
                    <VIcon
                      :icon="item.is_active ? 'ri-checkbox-circle-line' : 'ri-close-circle-line'"
                      :color="item.is_active ? 'success' : 'error'"
                      size="20"
                    />
                  </div>
                </div>
                
                <VDivider class="my-2" />
                
                <div class="text-body-2 mb-4">
                  <div class="mb-2 d-flex align-center gap-2" v-if="item.phone">
                    <VIcon icon="ri-phone-line" size="16" class="text-muted" />
                    <a :href="'tel:' + item.phone" class="text-primary font-weight-medium">{{ item.phone }}</a>
                  </div>
                  <div class="d-flex align-center gap-2" v-if="item.email">
                    <VIcon icon="ri-mail-line" size="16" class="text-muted" />
                    <a :href="'mailto:' + item.email" class="text-primary font-weight-medium">{{ item.email }}</a>
                  </div>
                </div>
                
                <div class="d-flex gap-2">
                  <VBtn
                    v-if="item.phone"
                    :href="'tel:' + item.phone"
                    color="success"
                    variant="tonal"
                    size="small"
                    prepend-icon="ri-phone-fill"
                    class="flex-grow-1"
                  >
                    Позвонить
                  </VBtn>
                  
                  <VBtn
                    v-if="hasPermission('purchase_positions_tab_suppliers_edit')"
                    color="primary"
                    variant="flat"
                    icon="ri-edit-line"
                    size="small"
                    @click="editSupplier(item)"
                  />
                  <VBtn
                    v-if="hasPermission('purchase_positions_tab_suppliers_edit')"
                    color="error"
                    variant="outlined"
                    icon="ri-delete-bin-line"
                    size="small"
                    @click="confirmDeleteSupplier(item)"
                  />
                </div>
              </VCard>
            </div>
          </div>
        </VCard>
      </VWindowItem>

      <!-- ВКЛАДКА ПОДКАТЕГОРИЙ -->
      <VWindowItem value="subcategories">
        <VCard class="mb-6">
          <VCardText>
            <VRow>
              <VCol cols="12" sm="6" md="4">
                <VTextField
                  v-model="subcategorySearch"
                  placeholder="Поиск подкатегории..."
                  prepend-inner-icon="ri-search-line"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                />
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <VCard class="bg-transparent border-0 elevation-0">
          <!-- Десктопная версия (таблица) -->
          <div class="d-none d-md-block bg-var-theme-surface rounded border elevation-1">
            <VDataTable
              :headers="[
                { title: 'Название подкатегории', key: 'name' },
                { title: 'Дата создания', key: 'created_at' },
                { title: 'Действия', key: 'actions', sortable: false, align: 'end' }
              ]"
              :items="filteredSubcategories"
              :loading="subcategoriesLoading"
              hover
              no-data-text="Подкатегории не найдены"
              loading-text="Загрузка подкатегорий..."
            >
              <!-- Стилизация даты создания -->
              <template #item.created_at="{ item }">
                <span>{{ item.created_at ? new Date(item.created_at).toLocaleDateString('ru-RU') : '—' }}</span>
              </template>

              <!-- Столбец действий -->
              <template #item.actions="{ item }">
                <div class="d-flex justify-end gap-1">
                  <VBtn
                    v-if="hasPermission('purchase_positions_tab_subcategories_edit')"
                    icon="ri-edit-line"
                    size="small"
                    variant="text"
                    color="primary"
                    @click="editSubcategory(item)"
                  />
                  <VBtn
                    v-if="hasPermission('purchase_positions_tab_subcategories_edit')"
                    icon="ri-delete-bin-line"
                    size="small"
                    variant="text"
                    color="error"
                    @click="confirmDeleteSubcategory(item)"
                  />
                </div>
              </template>
            </VDataTable>
          </div>

          <!-- Мобильная версия (карточки) -->
          <div class="d-block d-md-none">
            <div v-if="filteredSubcategories.length === 0" class="d-flex flex-column align-center my-8 py-8 bg-var-theme-surface rounded border elevation-1">
              <VIcon icon="ri-inbox-line" size="48" color="disabled" class="mb-2" />
              <div class="text-body-1 text-disabled">Подкатегории не найдены</div>
            </div>
            <div v-else>
              <VCard
                v-for="item in filteredSubcategories"
                :key="item.id"
                class="mb-4 border rounded-lg elevation-1 pa-4"
              >
                <div class="d-flex justify-space-between align-start mb-2">
                  <div>
                    <div class="font-weight-bold text-subtitle-1 text-primary">{{ item.name }}</div>
                    <div class="text-caption text-muted">Создана: {{ item.created_at ? new Date(item.created_at).toLocaleDateString('ru-RU') : '—' }}</div>
                  </div>
                </div>
                
                <VDivider class="my-2" />
                
                <div class="d-flex gap-2" v-if="hasPermission('purchase_positions_tab_subcategories_edit')">
                  <VBtn
                    color="primary"
                    variant="flat"
                    prepend-icon="ri-edit-line"
                    size="small"
                    class="flex-grow-1"
                    @click="editSubcategory(item)"
                  >
                    Редактировать
                  </VBtn>
                  <VBtn
                    color="error"
                    variant="outlined"
                    icon="ri-delete-bin-line"
                    size="small"
                    @click="confirmDeleteSubcategory(item)"
                  />
                </div>
              </VCard>
            </div>
          </div>
        </VCard>
      </VWindowItem>
    </VWindow>

    <!-- Диалог создания/редактирования позиции -->
    <VDialog
      v-model="isDialogVisible"
      max-width="500px"
      content-class="purchase-dialog"
    >
      <VCard>
        <VCardTitle class="purchase-dialog-title d-flex align-center gap-2 pa-4">
          <VIcon :icon="editedItem.id ? 'ri-edit-circle-line' : 'ri-add-circle-line'" color="primary" />
          {{ formTitle }}
        </VCardTitle>
        <VCardText class="pa-4 pt-0">
          <VRow>
            <!-- Название -->
            <VCol cols="12">
              <VTextField
                v-model="editedItem.name"
                label="Название позиции"
                placeholder="Например: Картофель очищенный"
                variant="outlined"
                density="comfortable"
              />
            </VCol>

            <!-- Направление -->
            <VCol cols="12" sm="6">
              <VSelect
                v-model="editedItem.category"
                :items="[
                  { title: 'Поставки', value: 'supply' },
                  { title: 'Магазин', value: 'shop' },
                  { title: 'Хозка', value: 'household' }
                ]"
                item-title="title"
                item-value="value"
                label="Направление"
                variant="outlined"
                density="comfortable"
              />
            </VCol>

            <!-- Подкатегория -->
            <VCol cols="12" sm="6">
              <VCombobox
                v-model="editedItem.subcategory"
                :items="subcategories.map(s => s.name)"
                label="Подкатегория"
                placeholder="Молочка, Овощи и т.д."
                variant="outlined"
                density="comfortable"
              />
            </VCol>

            <!-- Единица измерения -->
            <VCol cols="12" sm="6">
              <VCombobox
                v-model="editedItem.unit"
                :items="unitOptions"
                label="Ед. измерения"
                variant="outlined"
                density="comfortable"
              />
            </VCol>

            <!-- Поставщик -->
            <VCol cols="12" sm="6">
              <VSelect
                v-model="editedItem.supplier_id"
                :items="suppliers.filter(s => s.is_active)"
                item-title="name"
                item-value="id"
                label="Поставщик"
                placeholder="Выберите поставщика"
                variant="outlined"
                density="comfortable"
                clearable
              />
            </VCol>

            <!-- Переключатель активности -->
            <VCol cols="12">
              <VSwitch
                v-model="editedItem.is_active"
                label="Позиция активна для закупа"
                color="primary"
                hide-details
                inset
              />
            </VCol>
          </VRow>
        </VCardText>
        <VCardActions class="pa-4 pt-0 d-flex justify-end gap-2">
          <VBtn variant="text" color="secondary" @click="close">Отмена</VBtn>
          <VBtn color="primary" variant="flat" @click="save">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог создания/редактирования поставщика -->
    <VDialog
      v-model="isSupplierDialogVisible"
      max-width="500px"
      content-class="purchase-dialog"
    >
      <VCard>
        <VCardTitle class="purchase-dialog-title d-flex align-center gap-2 pa-4">
          <VIcon :icon="editedSupplier.id ? 'ri-edit-circle-line' : 'ri-add-circle-line'" color="primary" />
          {{ supplierFormTitle }}
        </VCardTitle>
        <VCardText class="pa-4 pt-0">
          <VRow>
            <!-- Название поставщика -->
            <VCol cols="12">
              <VTextField
                v-model="editedSupplier.name"
                label="Название поставщика / организации"
                placeholder="ИП Иванов А.А."
                variant="outlined"
                density="comfortable"
              />
            </VCol>

            <!-- Телефон -->
            <VCol cols="12" sm="6">
              <VTextField
                v-model="editedSupplier.phone"
                label="Телефон"
                placeholder="+7 (999) 123-45-67"
                variant="outlined"
                density="comfortable"
              />
            </VCol>

            <!-- Email -->
            <VCol cols="12" sm="6">
              <VTextField
                v-model="editedSupplier.email"
                label="Email"
                placeholder="supplier@example.com"
                variant="outlined"
                density="comfortable"
              />
            </VCol>

            <!-- Комментарий -->
            <VCol cols="12">
              <VTextarea
                v-model="editedSupplier.comment"
                label="Комментарий / Заметки"
                placeholder="Дни поставки, особенности работы..."
                variant="outlined"
                rows="3"
                density="comfortable"
              />
            </VCol>

            <!-- Переключатель активности -->
            <VCol cols="12">
              <VSwitch
                v-model="editedSupplier.is_active"
                label="Поставщик активен"
                color="primary"
                hide-details
                inset
              />
            </VCol>
          </VRow>
        </VCardText>
        <VCardActions class="pa-4 pt-0 d-flex justify-end gap-2">
          <VBtn variant="text" color="secondary" @click="closeSupplier">Отмена</VBtn>
          <VBtn color="primary" variant="flat" @click="saveSupplier">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог создания/редактирования подкатегории -->
    <VDialog
      v-model="isSubcategoryDialogVisible"
      max-width="500px"
      content-class="purchase-dialog"
    >
      <VCard>
        <VCardTitle class="purchase-dialog-title d-flex align-center gap-2 pa-4">
          <VIcon :icon="editedSubcategory.id ? 'ri-edit-circle-line' : 'ri-add-circle-line'" color="primary" />
          {{ subcategoryFormTitle }}
        </VCardTitle>
        <VCardText class="pa-4 pt-0">
          <VRow>
            <!-- Название подкатегории -->
            <VCol cols="12">
              <VTextField
                v-model="editedSubcategory.name"
                label="Название подкатегории"
                placeholder="Например: Упаковка"
                variant="outlined"
                density="comfortable"
              />
            </VCol>
          </VRow>
        </VCardText>
        <VCardActions class="pa-4 pt-0 d-flex justify-end gap-2">
          <VBtn variant="text" color="secondary" @click="closeSubcategory">Отмена</VBtn>
          <VBtn color="primary" variant="flat" @click="saveSubcategory">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог подтверждения удаления подкатегории -->
    <VDialog
      v-model="subcategoryDeleteDialog"
      max-width="400px"
    >
      <VCard title="Подтверждение удаления">
        <VCardText class="pa-4 pt-0">
          Вы уверены, что хотите удалить подкатегорию <strong>{{ subcategoryToDelete?.name }}</strong>? 
          Связанные с ней позиции закупа сохранят текстовое название подкатегории, но сама подкатегория будет стерта из справочника.
        </VCardText>
        <VCardActions class="pa-4 pt-0 d-flex justify-end gap-2">
          <VBtn variant="text" color="secondary" @click="subcategoryDeleteDialog = false">Отмена</VBtn>
          <VBtn color="error" variant="flat" :loading="isSubcategoryDeleting" @click="deleteSubcategoryItem">Удалить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог подтверждения удаления позиции -->
    <VDialog
      v-model="deleteDialog"
      max-width="400px"
    >
      <VCard title="Подтверждение удаления">
        <VCardText class="pa-4 pt-0">
          Вы уверены, что хотите удалить позицию <strong>{{ positionToDelete?.name }}</strong>? 
          Она будет навсегда стерта из справочника закупа.
        </VCardText>
        <VCardActions class="pa-4 pt-0 d-flex justify-end gap-2">
          <VBtn variant="text" color="secondary" @click="deleteDialog = false">Отмена</VBtn>
          <VBtn color="error" variant="flat" :loading="isDeleting" @click="deleteItem">Удалить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог подтверждения удаления поставщика -->
    <VDialog
      v-model="supplierDeleteDialog"
      max-width="400px"
    >
      <VCard title="Подтверждение удаления">
        <VCardText class="pa-4 pt-0">
          Вы уверены, что хотите удалить поставщика <strong>{{ supplierToDelete?.name }}</strong>? 
          Связанные с ним позиции закупа потеряют привязку к поставщику.
        </VCardText>
        <VCardActions class="pa-4 pt-0 d-flex justify-end gap-2">
          <VBtn variant="text" color="secondary" @click="supplierDeleteDialog = false">Отмена</VBtn>
          <VBtn color="error" variant="flat" :loading="isSupplierDeleting" @click="deleteSupplierItem">Удалить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>

<style scoped>
@import "@styles/purchase.css";
</style>
