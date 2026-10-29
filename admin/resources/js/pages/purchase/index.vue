<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { getAuthHeaders, hasPermission } from '@/utils/auth'
import { useToast } from 'vue-toastification'

const toast = useToast()

// Состояния
const purchaseTabs = computed(() => {
  const allTabs = [
    { value: 'shop', title: 'Магазин', permission: 'purchase_tab_shop_view' },
    { value: 'household', title: 'Хозка', permission: 'purchase_tab_household_view' },
    { value: 'supply', title: 'Поставки', permission: 'purchase_tab_supply_view' }
  ]
  return allTabs.filter(t => hasPermission(t.permission))
})
const activeTab = ref(null)
const lists = ref([])
const loading = ref(true)
const search = ref('')

// Диалоги
const isCreateDialogVisible = ref(false)
const isDetailDialogVisible = ref(false)
const isDeletingList = ref(false)
const deleteListDialog = ref(false)
const listToDelete = ref(null)

const savingList = ref(false)
const sendingList = ref(false)

// Состояние детального просмотра списка
const currentList = ref(null)
const detailSearch = ref('')
const showOnlyFilled = ref(false)

// Данные формы создания списка закупа
const createForm = ref({
  category: 'shop',
  date: '',
  name: ''
})

// Настройки таблицы списков закупа
const listHeaders = [
  { title: 'Название списка', key: 'name' },
  { title: 'Дата поставки', key: 'date' },
  { title: 'Позиций к закупу', key: 'items_count' },
  { title: 'Статус', key: 'status' },
  { title: 'Создан', key: 'created_at' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'end' }
]

// Получение списка закупа
const fetchLists = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/purchase/lists', {
      headers: getAuthHeaders()
    })
    if (response.ok) {
      lists.value = await response.json()
    } else {
      toast.error('Не удалось загрузить списки закупа')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка сети при загрузке списков')
  } finally {
    loading.value = false
  }
}

// Фильтрация списков закупа по вкладке направления
const filteredLists = computed(() => {
  return lists.value.filter(lst => {
    const matchesCategory = lst.category === activeTab.value
    const matchesSearch = lst.name.toLowerCase().includes(search.value.toLowerCase())
    return matchesCategory && matchesSearch
  })
})

// Открытие списка закупа детально
const openListDetails = async (listId) => {
  loading.value = true
  try {
    const response = await fetch(`/api/v1/purchase/lists/${listId}`, {
      headers: getAuthHeaders()
    })
    if (response.ok) {
      currentList.value = await response.json()
      detailSearch.value = ''
      showOnlyFilled.value = false
      isDetailDialogVisible.value = true
    } else {
      toast.error('Не удалось загрузить детали списка')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка загрузки данных списка')
  } finally {
    loading.value = false
  }
}

// Группировка элементов детального списка по подкатегориям
const groupedItems = computed(() => {
  const groups = {}
  if (!currentList.value || !currentList.value.items) return groups
  
  let itemsToGroup = currentList.value.items
  
  // Поиск по ключевому слову
  if (detailSearch.value) {
    const q = detailSearch.value.toLowerCase()
    itemsToGroup = itemsToGroup.filter(item => 
      item.position?.name.toLowerCase().includes(q) ||
      (item.position?.subcategory && item.position.subcategory.toLowerCase().includes(q)) ||
      (item.position?.supplier?.name && item.position.supplier.name.toLowerCase().includes(q))
    )
  }
  
  // Фильтр "Только выбранные"
  if (showOnlyFilled.value) {
    itemsToGroup = itemsToGroup.filter(item => item.quantity > 0)
  }
  
  // Группируем по subcategory
  itemsToGroup.forEach(item => {
    const subcat = item.position?.subcategory || 'Без категории'
    if (!groups[subcat]) {
      groups[subcat] = []
    }
    groups[subcat].push(item)
  })
  
  return groups
})

// Открытие диалога создания списка
const openCreateDialog = () => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  createForm.value.date = tomorrow.toISOString().substr(0, 10)
  createForm.value.category = activeTab.value
  
  updateCreateListName()
  isCreateDialogVisible.value = true
}

const updateCreateListName = () => {
  const directionName = getCategoryLabel(createForm.value.category)
  const formattedDate = formatDateString(createForm.value.date)
  createForm.value.name = `Закуп ${directionName} на ${formattedDate}`
}

watch([() => createForm.value.category, () => createForm.value.date], () => {
  updateCreateListName()
})

// Сохранение нового списка закупа
const saveNewList = async () => {
  if (!createForm.value.date) {
    toast.warning('Выберите дату поставки')
    return
  }
  
  try {
    const response = await fetch('/api/v1/purchase/lists', {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(createForm.value)
    })
    
    if (response.ok) {
      const newList = await response.json()
      toast.success('Список закупа успешно создан')
      isCreateDialogVisible.value = false
      await fetchLists()
      // Сразу открываем его для заполнения количества
      await openListDetails(newList.id)
    } else {
      const err = await response.json()
      toast.error(err.detail || 'Не удалось создать список закупа')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка сети при создании списка')
  }
}

// Сохранение списка как черновика
const saveListDraft = async (silent = false) => {
  if (!currentList.value) return
  
  savingList.value = true
  try {
    const itemsToSave = currentList.value.items.map(item => ({
      position_id: item.position_id,
      quantity: Number(item.quantity) || 0,
      comment: item.comment || '',
      is_urgent: !!item.is_urgent
    }))
    
    const response = await fetch(`/api/v1/purchase/lists/${currentList.value.id}`, {
      method: 'PATCH',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: currentList.value.name,
        date: currentList.value.date,
        items: itemsToSave
      })
    })
    
    if (response.ok) {
      if (!silent) {
        toast.success('Черновик списка сохранен')
      }
      await fetchLists()
      // Обновляем текущий список свежими данными
      currentList.value = await response.json()
      return true
    } else {
      const err = await response.json()
      toast.error(err.detail || 'Не удалось сохранить список')
      return false
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка сети при сохранении')
    return false
  } finally {
    savingList.value = false
  }
}

// Сохранение и отправка списка в системную рассылку
const saveAndSendList = async () => {
  if (!currentList.value) return
  
  // Сначала сохраняем черновик
  const saved = await saveListDraft(true)
  if (!saved) return
  
  sendingList.value = true
  try {
    const response = await fetch(`/api/v1/purchase/lists/${currentList.value.id}/send`, {
      method: 'POST',
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      toast.success('Список закупа успешно отправлен в рассылки!')
      await fetchLists()
      isDetailDialogVisible.value = false
    } else {
      const err = await response.json()
      toast.error(err.detail || 'Не удалось отправить список')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка сети при отправке списка')
  } finally {
    sendingList.value = false
  }
}

// Диалог подтверждения удаления списка
const confirmDeleteList = (item) => {
  listToDelete.value = item
  deleteListDialog.value = true
}

// Удаление списка закупа
const deleteList = async () => {
  isDeletingList.value = true
  try {
    const response = await fetch(`/api/v1/purchase/lists/${listToDelete.value.id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      toast.success('Список закупа удален')
      await fetchLists()
      deleteListDialog.value = false
    } else {
      toast.error('Не удалось удалить список закупа')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка сети при удалении')
  } finally {
    isDeletingList.value = false
  }
}

// Хелперы
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

const getStatusLabel = (status) => {
  switch (status) {
    case 'draft': return 'Черновик'
    case 'sent': return 'Отправлен'
    default: return status
  }
}

const getStatusColor = (status) => {
  switch (status) {
    case 'draft': return 'secondary'
    case 'sent': return 'success'
    default: return 'primary'
  }
}

const formatDateString = (dateStr) => {
  if (!dateStr) return ''
  const [year, month, day] = dateStr.split('-')
  return `${day}.${month}.${year}`
}

const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return ''
  const date = new Date(dateTimeStr)
  return date.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// --- Состояния для режима просмотра и аудита ---
const isViewDialogVisible = ref(false)
const currentViewList = ref(null)
const viewSearch = ref('')
const viewShowAll = ref(false)
const changes = ref([])
const changesLoading = ref(false)
const viewTimer = ref(null)

// Загрузка логов изменений
const fetchListChanges = async (listId) => {
  changesLoading.value = true
  try {
    const response = await fetch(`/api/v1/purchase/lists/${listId}/changes`, {
      headers: getAuthHeaders()
    })
    if (response.ok) {
      changes.value = await response.json()
    }
  } catch (e) {
    console.error('Ошибка загрузки логов изменений:', e)
  } finally {
    changesLoading.value = false
  }
}

// Открытие режима просмотра
const openListView = async (listId) => {
  loading.value = true
  try {
    const response = await fetch(`/api/v1/purchase/lists/${listId}`, {
      headers: getAuthHeaders()
    })
    if (response.ok) {
      currentViewList.value = await response.json()
      viewSearch.value = ''
      viewShowAll.value = false
      await fetchListChanges(listId)
      isViewDialogVisible.value = true

      // Настройка фонового автообновления каждые 5 секунд
      if (viewTimer.value) clearInterval(viewTimer.value)
      viewTimer.value = setInterval(async () => {
        try {
          const res = await fetch(`/api/v1/purchase/lists/${listId}`, {
            headers: getAuthHeaders()
          })
          if (res.ok) {
            currentViewList.value = await res.json()
          }
          // Автообновление логов
          const resChanges = await fetch(`/api/v1/purchase/lists/${listId}/changes`, {
            headers: getAuthHeaders()
          })
          if (resChanges.ok) {
            changes.value = await resChanges.json()
          }
        } catch (err) {
          console.error('Ошибка фонового автообновления:', err)
        }
      }, 5000)
    } else {
      toast.error('Не удалось загрузить данные списка')
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка при открытии просмотра')
  } finally {
    loading.value = false
  }
}

// Закрытие режима просмотра
const closeListView = () => {
  if (viewTimer.value) {
    clearInterval(viewTimer.value)
    viewTimer.value = null
  }
  isViewDialogVisible.value = false
  currentViewList.value = null
  changes.value = []
}

// Переключение статуса покупки
const toggleItemBoughtStatus = async (item) => {
  try {
    const response = await fetch(`/api/v1/purchase/lists/${currentViewList.value.id}/items/${item.position_id}/toggle_bought?is_bought=${item.is_bought}`, {
      method: 'POST',
      headers: getAuthHeaders()
    })
    if (response.ok) {
      // Обновляем лог изменений
      await fetchListChanges(currentViewList.value.id)
    } else {
      toast.error('Не удалось обновить статус покупки')
      item.is_bought = !item.is_bought
    }
  } catch (e) {
    console.error(e)
    toast.error('Ошибка соединения при обновлении статуса')
    item.is_bought = !item.is_bought
  }
}

// Вычисляемые списки позиций в режиме просмотра: активные и купленные
const viewActiveGroupedItems = computed(() => {
  const groups = {}
  if (!currentViewList.value || !currentViewList.value.items) return groups
  
  let itemsToGroup = currentViewList.value.items.filter(item => !item.is_bought)
  
  if (!viewShowAll.value) {
    itemsToGroup = itemsToGroup.filter(item => item.quantity > 0)
  }
  
  if (viewSearch.value) {
    const q = viewSearch.value.toLowerCase()
    itemsToGroup = itemsToGroup.filter(item => 
      item.position?.name.toLowerCase().includes(q) ||
      (item.position?.subcategory && item.position.subcategory.toLowerCase().includes(q))
    )
  }
  
  itemsToGroup.forEach(item => {
    const subcat = item.position?.subcategory || 'Без категории'
    if (!groups[subcat]) groups[subcat] = []
    groups[subcat].push(item)
  })
  
  return groups
})

const viewBoughtGroupedItems = computed(() => {
  const groups = {}
  if (!currentViewList.value || !currentViewList.value.items) return groups
  
  let itemsToGroup = currentViewList.value.items.filter(item => item.is_bought)
  
  if (!viewShowAll.value) {
    itemsToGroup = itemsToGroup.filter(item => item.quantity > 0)
  }
  
  if (viewSearch.value) {
    const q = viewSearch.value.toLowerCase()
    itemsToGroup = itemsToGroup.filter(item => 
      item.position?.name.toLowerCase().includes(q) ||
      (item.position?.subcategory && item.position.subcategory.toLowerCase().includes(q))
    )
  }
  
  itemsToGroup.forEach(item => {
    const subcat = item.position?.subcategory || 'Без категории'
    if (!groups[subcat]) groups[subcat] = []
    groups[subcat].push(item)
  })
  
  return groups
})

const onQuantityFocus = (item, event) => {
  event.target.select()
  if (item.quantity === 0 || item.quantity === '0') {
    item.quantity = ''
  }
}

const onQuantityBlur = (item) => {
  if (item.quantity === '' || item.quantity === null || isNaN(item.quantity)) {
    item.quantity = 0
  }
}

const canEditCurrentList = computed(() => {
  if (!hasPermission('purchase_lists_edit')) return false
  if (!currentList.value) return false
  const cat = currentList.value.category
  if (cat === 'shop') return hasPermission('purchase_tab_shop_edit')
  if (cat === 'household') return hasPermission('purchase_tab_household_edit')
  if (cat === 'supply') return hasPermission('purchase_tab_supply_edit')
  return false
})

onMounted(() => {
  fetchLists()
  activeTab.value = purchaseTabs.value.length ? purchaseTabs.value[0].value : null
})
</script>

<template>
  <div class="purchase-page">
    <VRow class="align-center mb-6">
      <VCol cols="12" sm="6">
        <h1 class="text-h4 font-weight-bold d-flex align-center gap-2">
          <VIcon icon="ri-shopping-bag-3-line" color="primary" />
          Списки закупа
        </h1>
      </VCol>
      <VCol cols="12" sm="6" class="text-sm-end">
        <VBtn
          v-if="hasPermission('purchase_lists_edit')"
          color="primary"
          prepend-icon="ri-add-line"
          @click="openCreateDialog"
        >
          Создать список
        </VBtn>
      </VCol>
    </VRow>

    <VCard class="mb-6">
      <VCardText class="pa-4 pt-3 pb-3">
        <VRow class="align-center">
          <VCol cols="12" sm="6" md="4">
            <VTextField
              v-model="search"
              placeholder="Поиск списка по названию..."
              prepend-inner-icon="ri-search-line"
              variant="outlined"
              density="comfortable"
              hide-details
            />
          </VCol>
        </VRow>
      </VCardText>
    </VCard>

    <VTabs v-model="activeTab" class="mb-4" v-if="purchaseTabs.length">
      <VTab
        v-for="tab in purchaseTabs"
        :key="tab.value"
        :value="tab.value"
      >
        {{ tab.title }}
      </VTab>
    </VTabs>

    <VCard class="bg-transparent border-0 elevation-0">
      <!-- Десктопная версия (таблица) -->
      <div class="d-none d-md-block bg-var-theme-surface rounded border elevation-1">
        <VDataTable
          :headers="listHeaders"
          :items="filteredLists"
          :loading="loading"
          hover
          no-data-text="Списки закупа не найдены"
          loading-text="Загрузка списков..."
        >
          <!-- Формат даты поставки -->
          <template #item.date="{ item }">
            <span class="font-weight-medium text-body-2">{{ formatDateString(item.date) }}</span>
          </template>

          <!-- Статус -->
          <template #item.status="{ item }">
            <VChip
              :color="getStatusColor(item.status)"
              size="small"
              label
              class="font-weight-bold"
            >
              {{ getStatusLabel(item.status) }}
            </VChip>
          </template>

          <!-- Дата создания -->
          <template #item.created_at="{ item }">
            <span class="text-caption text-muted">{{ formatDateTime(item.created_at) }}</span>
          </template>

          <!-- Количество позиций -->
          <template #item.items_count="{ item }">
            <VChip color="light" size="small" class="font-weight-bold">
              {{ item.items_count || 0 }}
            </VChip>
          </template>

          <!-- Действия -->
          <template #item.actions="{ item }">
            <div class="d-flex justify-end gap-1">
              <VBtn
                icon="ri-eye-line"
                size="small"
                variant="text"
                color="success"
                title="Посмотреть список закупа"
                @click="openListView(item.id)"
              />
              <VBtn
                icon="ri-edit-line"
                size="small"
                variant="text"
                color="primary"
                title="Открыть список"
                @click="openListDetails(item.id)"
              />
              <VBtn
                v-if="hasPermission('purchase_lists_edit')"
                icon="ri-delete-bin-line"
                size="small"
                variant="text"
                color="error"
                title="Удалить список"
                @click="confirmDeleteList(item)"
              />
            </div>
          </template>
        </VDataTable>
      </div>

      <!-- Мобильная версия (карточки) -->
      <div class="d-block d-md-none">
        <div v-if="filteredLists.length === 0" class="d-flex flex-column align-center my-8 py-8 bg-var-theme-surface rounded border elevation-1">
          <VIcon icon="ri-inbox-line" size="48" color="disabled" class="mb-2" />
          <div class="text-body-1 text-disabled">Списки закупа не найдены</div>
        </div>
        <div v-else>
          <VCard
            v-for="item in filteredLists"
            :key="item.id"
            class="mb-4 border rounded-lg elevation-1 pa-4 purchase-mobile-list-card"
          >
            <div class="d-flex justify-space-between align-start mb-2">
              <div>
                <div class="font-weight-bold text-subtitle-1 text-primary">{{ item.name }}</div>
                <div class="text-caption text-muted">Создан: {{ formatDateTime(item.created_at) }}</div>
              </div>
              <VChip
                :color="getStatusColor(item.status)"
                size="small"
                label
                class="font-weight-bold"
              >
                {{ getStatusLabel(item.status) }}
              </VChip>
            </div>
            
            <VDivider class="my-2" />
            
            <div class="d-flex justify-space-between align-center mb-4 text-body-2">
              <div>
                Дата поставки: <strong class="text-high-emphasis">{{ formatDateString(item.date) }}</strong>
              </div>
              <div>
                Позиций: <VChip size="x-small" color="primary" variant="tonal" class="font-weight-bold ms-1">{{ item.items_count || 0 }}</VChip>
              </div>
            </div>
            
            <div class="d-flex gap-2">
              <VBtn
                color="success"
                variant="flat"
                prepend-icon="ri-eye-line"
                size="small"
                class="flex-grow-1"
                @click="openListView(item.id)"
              >
                Просмотр
              </VBtn>
              <VBtn
                color="primary"
                variant="outlined"
                prepend-icon="ri-edit-line"
                size="small"
                class="flex-grow-1"
                @click="openListDetails(item.id)"
              >
                Править
              </VBtn>
              <VBtn
                v-if="hasPermission('purchase_manage')"
                color="error"
                variant="outlined"
                icon="ri-delete-bin-line"
                size="small"
                @click="confirmDeleteList(item)"
              />
            </div>
          </VCard>
        </div>
      </div>
    </VCard>

    <!-- ДИАЛОГ СОЗДАНИЯ СПИСКА -->
    <VDialog
      v-model="isCreateDialogVisible"
      max-width="500px"
      content-class="purchase-dialog"
    >
      <VCard>
        <VCardTitle class="purchase-dialog-title d-flex align-center gap-2 pa-4">
          <VIcon icon="ri-add-circle-line" color="primary" />
          Создать новый список закупа
        </VCardTitle>
        <VCardText class="pa-4 pt-0">
          <VRow>
            <!-- Выбор направления -->
            <VCol cols="12" sm="6">
              <VSelect
                v-model="createForm.category"
                :items="[
                  { title: 'Магазин', value: 'shop' },
                  { title: 'Хозка', value: 'household' },
                  { title: 'Поставки', value: 'supply' }
                ]"
                item-title="title"
                item-value="value"
                label="Направление"
                variant="outlined"
                density="comfortable"
              />
            </VCol>

            <!-- Дата закупа -->
            <VCol cols="12" sm="6">
              <VTextField
                v-model="createForm.date"
                label="Дата поставки"
                type="date"
                variant="outlined"
                density="comfortable"
              />
            </VCol>

            <!-- Название списка -->
            <VCol cols="12">
              <VTextField
                v-model="createForm.name"
                label="Название списка закупа"
                placeholder="Закуп Магазин на 16.06.2026"
                variant="outlined"
                density="comfortable"
              />
            </VCol>
          </VRow>
        </VCardText>
        <VCardActions class="pa-4 pt-0 d-flex justify-end gap-2">
          <VBtn variant="text" color="secondary" @click="isCreateDialogVisible = false">Отмена</VBtn>
          <VBtn color="primary" variant="flat" @click="saveNewList">Создать</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- ДЕТАЛЬНЫЙ ПРОСМОТР И ЗАПОЛНЕНИЕ СПИСКА ЗАКУПА (FULLSCREEN) -->
    <VDialog
      v-model="isDetailDialogVisible"
      fullscreen
      transition="dialog-bottom-transition"
    >
      <VCard class="rounded-0">
        <!-- Тулбар -->
        <VToolbar
          dark
          color="primary"
          density="comfortable"
        >
          <VBtn
            icon
            dark
            title="Закрыть"
            @click="isDetailDialogVisible = false"
          >
            <VIcon icon="ri-close-line" />
          </VBtn>
          <VToolbarTitle class="font-weight-bold">
            <span class="d-none d-sm-inline">{{ currentList?.name }}</span>
            <span class="d-inline d-sm-none">{{ currentList?.category === 'shop' ? 'Магазин' : (currentList?.category === 'household' ? 'Хозка' : 'Поставки') }}</span>
            <VChip
              :color="getStatusColor(currentList?.status)"
              size="small"
              class="ms-2 font-weight-bold text-white"
            >
              {{ getStatusLabel(currentList?.status) }}
            </VChip>
          </VToolbarTitle>
          <VSpacer />
          <VToolbarItems class="gap-2 align-center px-4 d-none d-md-flex">
            <VBtn
              color="white"
              variant="text"
              prepend-icon="ri-close-line"
              @click="isDetailDialogVisible = false"
            >
              Закрыть
            </VBtn>
            <VBtn
              color="white"
              variant="outlined"
              prepend-icon="ri-save-line"
              :loading="savingList"
              v-if="canEditCurrentList"
              @click="saveListDraft(false)"
            >
              Сохранить черновик
            </VBtn>
            <VBtn
              color="success"
              variant="flat"
              prepend-icon="ri-send-plane-line"
              :loading="sendingList"
              v-if="canEditCurrentList"
              @click="saveAndSendList"
            >
              Сохранить и Отправить
            </VBtn>
          </VToolbarItems>
        </VToolbar>

        <VCardText class="pa-6 bg-var-theme-background fill-height overflow-y-auto dialog-content-with-bottom-bar">
          <!-- Фильтры и мета-данные -->
          <VRow class="mb-4 align-center">
            <VCol cols="12" md="6" class="d-flex gap-4 flex-wrap">
              <VTextField
                v-model="detailSearch"
                placeholder="Быстрый поиск в списке..."
                prepend-inner-icon="ri-search-line"
                variant="outlined"
                density="compact"
                hide-details
                style="max-width: 350px"
              />
              <VSwitch
                v-model="showOnlyFilled"
                label="Только заполненные позиций (>0)"
                color="primary"
                hide-details
                inset
                class="mt-1"
              />
            </VCol>
            <VCol cols="12" md="6" class="text-md-end text-body-2 text-muted">
              Дата поставки: <strong class="text-high-emphasis">{{ formatDateString(currentList?.date) }}</strong>
              <span class="mx-2">|</span>
              Создан: <strong>{{ formatDateTime(currentList?.created_at) }}</strong>
            </VCol>
          </VRow>

          <!-- Вывод позиций, сгруппированных по подкатегориям -->
          <div v-if="Object.keys(groupedItems).length === 0" class="d-flex flex-column align-center my-12 py-12">
            <VIcon icon="ri-inbox-line" size="64" color="disabled" class="mb-4" />
            <div class="text-h6 text-disabled">Нет позиций для отображения</div>
            <div class="text-body-2 text-muted mt-1">Попробуйте изменить поисковый запрос или фильтры</div>
          </div>

          <div v-else>
            <div v-for="(items, subcat) in groupedItems" :key="subcat" class="purchase-subcat-group mb-6">
              <div class="purchase-subcat-header d-flex align-center py-2 px-4 bg-var-theme-surface rounded-t border-b font-weight-bold">
                <VIcon icon="ri-folder-open-line" class="me-2 text-primary" size="20" />
                {{ subcat }}
                <VSpacer />
                <VChip size="x-small" color="primary" variant="tonal" class="font-weight-bold">
                  Позиций: {{ items.length }}
                </VChip>
              </div>
              <!-- Десктопная версия (таблица) -->
              <div class="d-none d-md-block">
                <VTable density="comfortable" class="purchase-subcat-table border-x border-b rounded-b">
                  <thead>
                    <tr>
                      <th style="width: 8%; text-align: center;">Срочно</th>
                      <th style="width: 32%">Название позиции</th>
                      <th style="width: 20%">Поставщик</th>
                      <th style="width: 15%">Количество</th>
                      <th style="width: 25%">Комментарий</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in items" :key="item.id" :class="{ 'urgent-row': item.is_urgent }">
                      <td class="text-center">
                        <VCheckbox
                          v-model="item.is_urgent"
                          color="error"
                          hide-details
                          density="compact"
                          class="d-inline-flex"
                        />
                      </td>
                      <td>
                        <div class="d-flex align-center">
                          <VIcon v-if="item.is_urgent" icon="ri-error-warning-fill" color="error" class="me-2" size="20" />
                          <div>
                            <div class="font-weight-semibold text-body-1">{{ item.position?.name }}</div>
                            <div class="text-caption text-muted">Ед. изм.: {{ item.position?.unit }}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span class="text-body-2 text-high-emphasis font-weight-medium">
                          {{ item.position?.supplier?.name || '—' }}
                        </span>
                      </td>
                      <td>
                        <div class="d-flex align-center gap-1">
                          <VTextField
                            v-model.number="item.quantity"
                            type="number"
                            min="0"
                            step="any"
                            density="compact"
                            variant="outlined"
                            hide-details
                            class="purchase-quantity-input font-weight-bold text-center"
                            style="width: 90px;"
                            :disabled="!canEditCurrentList"
                            @focus="onQuantityFocus(item, $event)"
                            @blur="onQuantityBlur(item)"
                          />
                          <span class="text-body-2 text-muted font-weight-medium ms-1">{{ item.position?.unit }}</span>
                        </div>
                      </td>
                      <td>
                        <VTextField
                          v-model="item.comment"
                          placeholder="Примечание к закупке..."
                          density="compact"
                          variant="outlined"
                          hide-details
                          class="purchase-comment-input"
                        />
                      </td>
                    </tr>
                  </tbody>
                </VTable>
              </div>

              <!-- Мобильная версия (карточки) -->
              <div class="d-block d-md-none border-x border-b rounded-b bg-var-theme-background pa-3">
                <VCard
                  v-for="item in items"
                  :key="item.id"
                  class="mb-3 border rounded-lg elevation-1 pa-3"
                  :class="{ 'urgent-row': item.is_urgent }"
                >
                  <div class="d-flex align-start justify-space-between mb-2">
                    <div class="d-flex align-center">
                      <VIcon v-if="item.is_urgent" icon="ri-error-warning-fill" color="error" class="me-2" size="20" />
                      <div>
                        <div class="font-weight-semibold text-body-1">{{ item.position?.name }}</div>
                        <div class="text-caption text-muted">
                          Ед. изм.: {{ item.position?.unit }} 
                          <span v-if="item.position?.supplier?.name"> | {{ item.position.supplier.name }}</span>
                        </div>
                      </div>
                    </div>
                    
                    <VBtn
                      :color="item.is_urgent ? 'error' : 'secondary'"
                      :variant="item.is_urgent ? 'flat' : 'outlined'"
                      size="x-small"
                      class="font-weight-bold"
                      :disabled="!canEditCurrentList"
                      @click="item.is_urgent = !item.is_urgent"
                    >
                      🚨 {{ item.is_urgent ? 'Срочно!' : 'Обычный' }}
                    </VBtn>
                  </div>
                  
                  <VRow dense class="align-center mt-1">
                    <VCol cols="5">
                      <VTextField
                        v-model.number="item.quantity"
                        type="number"
                        min="0"
                        step="any"
                        label="Кол-во"
                        density="compact"
                        variant="outlined"
                        hide-details
                        :disabled="!canEditCurrentList"
                        class="purchase-quantity-input font-weight-bold text-center"
                        @focus="onQuantityFocus(item, $event)"
                        @blur="onQuantityBlur(item)"
                      />
                    </VCol>
                    <VCol cols="7">
                      <VTextField
                        v-model="item.comment"
                        placeholder="Примечание..."
                        label="Примечание"
                        density="compact"
                        variant="outlined"
                        hide-details
                        class="purchase-comment-input"
                      />
                    </VCol>
                  </VRow>
                </VCard>
              </div>
            </div>
          </div>

          <!-- Кнопка закрытия внизу для десктопа -->
          <div class="d-none d-md-flex justify-center mt-8 mb-4">
            <VBtn
              color="secondary"
              variant="outlined"
              prepend-icon="ri-close-line"
              size="large"
              style="min-width: 200px"
              @click="isDetailDialogVisible = false"
            >
              Закрыть список
            </VBtn>
          </div>
        </VCardText>

        <!-- Фиксированный Bottom Bar на мобильных устройствах -->
        <div class="d-flex d-md-none mobile-bottom-bar bg-var-theme-surface border-t">
          <VBtn
            color="secondary"
            variant="outlined"
            prepend-icon="ri-close-line"
            @click="isDetailDialogVisible = false"
          >
            Закрыть
          </VBtn>
          <VBtn
            color="primary"
            variant="tonal"
            prepend-icon="ri-save-line"
            :loading="savingList"
            v-if="canEditCurrentList"
            @click="saveListDraft(false)"
          >
            Черновик
          </VBtn>
          <VBtn
            color="success"
            variant="flat"
            prepend-icon="ri-send-plane-line"
            :loading="sendingList"
            v-if="canEditCurrentList"
            @click="saveAndSendList"
          >
            Отправить
          </VBtn>
        </div>
      </VCard>
    </VDialog>

    <!-- ДИАЛОГ ПРОСМОТРА И ОТМЕТКИ КУПЛЕННЫХ ТОВАРОВ (FULLSCREEN) -->
    <VDialog
      v-model="isViewDialogVisible"
      fullscreen
      transition="dialog-bottom-transition"
    >
      <VCard class="rounded-0">
        <!-- Тулбар -->
        <VToolbar
          dark
          color="success"
          density="comfortable"
        >
          <VBtn
            icon
            dark
            title="Закрыть"
            @click="closeListView"
          >
            <VIcon icon="ri-close-line" />
          </VBtn>
          <VToolbarTitle class="font-weight-bold">
            <span>Просмотр: {{ currentViewList?.name }}</span>
            <VChip
              color="white"
              size="small"
              class="ms-2 font-weight-bold text-success"
            >
              {{ currentViewList?.status === 'draft' ? 'Черновик' : 'Отправлен' }}
            </VChip>
          </VToolbarTitle>
          <VSpacer />
          <VToolbarItems class="gap-2 align-center px-4">
            <VBtn
              color="white"
              variant="text"
              prepend-icon="ri-close-line"
              @click="closeListView"
            >
              Закрыть
            </VBtn>
          </VToolbarItems>
        </VToolbar>

        <VCardText class="pa-6 bg-var-theme-background fill-height overflow-y-auto dialog-content-with-bottom-bar">
          <VRow>
            <!-- Левая колонка: списки товаров -->
            <VCol cols="12" md="8">
              <!-- Фильтры -->
              <VCard class="mb-4">
                <VCardText class="d-flex gap-4 flex-wrap align-center pa-4">
                  <VTextField
                    v-model="viewSearch"
                    placeholder="Поиск товаров в списке..."
                    prepend-inner-icon="ri-search-line"
                    variant="outlined"
                    density="compact"
                    hide-details
                    style="max-width: 350px"
                    class="flex-grow-1"
                  />
                  <VSwitch
                    v-model="viewShowAll"
                    label="Показать все (включая количество 0)"
                    color="success"
                    hide-details
                    inset
                  />
                </VCardText>
              </VCard>

              <!-- Раздел 1: Активные товары к покупке -->
              <VCard class="mb-6 border">
                <div class="pa-4 bg-var-theme-surface border-b font-weight-bold text-subtitle-1 d-flex align-center gap-2">
                  <VIcon icon="ri-shopping-basket-line" color="success" />
                  📋 Список к покупке (активные)
                </div>
                <VCardText class="pa-0">
                  <div v-if="Object.keys(viewActiveGroupedItems).length === 0" class="pa-6 text-center text-muted">
                    Все позиции приобретены или нет товаров по фильтру
                  </div>
                  <div v-else>
                    <div v-for="(items, subcat) in viewActiveGroupedItems" :key="subcat" class="border-b last-no-border">
                      <div class="bg-light pa-2 px-4 font-weight-semibold text-caption text-uppercase text-muted d-flex align-center">
                        <VIcon icon="ri-folder-line" size="14" class="me-1" />
                        {{ subcat }}
                      </div>
                      <VList class="pa-0">
                        <VListItem
                          v-for="item in items"
                          :key="item.id"
                          class="py-2 px-4"
                          :class="{ 'urgent-row': item.is_urgent }"
                        >
                          <template #prepend>
                            <VCheckbox
                              v-model="item.is_bought"
                              color="success"
                              hide-details
                              class="me-3"
                              @change="toggleItemBoughtStatus(item)"
                            />
                          </template>
                          <VListItemTitle class="font-weight-semibold text-body-1">
                            <VIcon v-if="item.is_urgent" icon="ri-error-warning-fill" color="error" class="me-1" size="18" />
                            {{ item.position?.name }}
                          </VListItemTitle>
                          <VListItemSubtitle class="text-caption" v-if="item.comment || item.position?.supplier?.name">
                            <span v-if="item.position?.supplier?.name" class="font-weight-bold text-primary">{{ item.position.supplier.name }}</span>
                            <span v-if="item.position?.supplier?.name && item.comment"> | </span>
                            <span v-if="item.comment" class="text-italic">«{{ item.comment }}»</span>
                          </VListItemSubtitle>
                          <template #append>
                            <VChip color="primary" class="font-weight-bold" size="small">
                              {{ item.quantity }} {{ item.position?.unit }}
                            </VChip>
                          </template>
                        </VListItem>
                      </VList>
                    </div>
                  </div>
                </VCardText>
              </VCard>

              <!-- Раздел 2: Уже приобретено (ушли вниз) -->
              <VCard class="border bg-var-theme-surface">
                <div class="pa-4 border-b font-weight-bold text-subtitle-1 d-flex align-center gap-2 text-muted">
                  <VIcon icon="ri-checkbox-circle-line" color="disabled" />
                  ✅ Приобретено (смещено вниз)
                </div>
                <VCardText class="pa-0">
                  <div v-if="Object.keys(viewBoughtGroupedItems).length === 0" class="pa-6 text-center text-muted">
                    Ничего еще не приобретено
                  </div>
                  <div v-else>
                    <div v-for="(items, subcat) in viewBoughtGroupedItems" :key="subcat" class="border-b last-no-border">
                      <div class="bg-light pa-2 px-4 font-weight-semibold text-caption text-uppercase text-muted d-flex align-center">
                        <VIcon icon="ri-folder-line" size="14" class="me-1" />
                        {{ subcat }}
                      </div>
                      <VList class="pa-0 bg-transparent text-disabled">
                        <VListItem
                          v-for="item in items"
                          :key="item.id"
                          class="py-2 px-4 bought-item-row"
                        >
                          <template #prepend>
                            <VCheckbox
                              v-model="item.is_bought"
                              color="success"
                              hide-details
                              class="me-3"
                              @change="toggleItemBoughtStatus(item)"
                            />
                          </template>
                          <VListItemTitle class="text-decoration-line-through text-body-1 text-muted">
                            {{ item.position?.name }}
                          </VListItemTitle>
                          <VListItemSubtitle class="text-caption text-muted" v-if="item.comment">
                            «{{ item.comment }}»
                          </VListItemSubtitle>
                          <template #append>
                            <VChip color="secondary" variant="tonal" size="small" class="font-weight-bold text-decoration-line-through">
                              {{ item.quantity }} {{ item.position?.unit }}
                            </VChip>
                          </template>
                        </VListItem>
                      </VList>
                    </div>
                  </div>
                </VCardText>
              </VCard>
            </VCol>

            <!-- Правая колонка: метаданные и история изменений (аудит) -->
            <VCol cols="12" md="4">
              <!-- Сведения об авторах -->
              <VCard class="mb-4">
                <VCardText class="pa-4">
                  <div class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center gap-2">
                    <VIcon icon="ri-information-line" color="primary" />
                    Информация о списке
                  </div>
                  <div class="text-body-2 mb-2">
                    Создан: <strong>{{ formatDateTime(currentViewList?.created_at) }}</strong>
                  </div>
                  <div class="text-body-2 mb-2" v-if="currentViewList?.created_by">
                    Автор создания: <strong class="text-primary">{{ currentViewList.created_by.full_name || currentViewList.created_by.username }}</strong>
                  </div>
                  <VDivider class="my-3" />
                  <div class="text-body-2 mb-2">
                    Последнее изменение: <strong>{{ formatDateTime(currentViewList?.updated_at) }}</strong>
                  </div>
                  <div class="text-body-2" v-if="currentViewList?.updated_by">
                    Кто изменил: <strong class="text-primary">{{ currentViewList.updated_by.full_name || currentViewList.updated_by.username }}</strong>
                  </div>
                </VCardText>
              </VCard>

              <!-- Таймлайн логов изменений -->
              <VCard class="fill-height border">
                <div class="pa-4 bg-var-theme-surface border-b font-weight-bold text-subtitle-1 d-flex align-center gap-2">
                  <VIcon icon="ri-history-line" color="primary" />
                  📋 История изменений (Аудит)
                </div>
                <VCardText class="pa-4 overflow-y-auto" style="max-height: 550px;">
                  <div v-if="changesLoading" class="text-center py-4">
                    <VProgressCircular indeterminate color="primary" />
                  </div>
                  <div v-else-if="changes.length === 0" class="text-center py-4 text-muted text-body-2">
                    Записи об изменениях отсутствуют
                  </div>
                  <div v-else class="changes-timeline">
                    <div
                      v-for="ch in changes"
                      :key="ch.id"
                      class="change-log-item mb-4 pb-3 border-b last-no-border"
                    >
                      <div class="d-flex justify-space-between text-caption text-muted mb-1">
                        <span class="font-weight-bold text-primary d-flex align-center gap-1">
                          <VIcon icon="ri-user-settings-line" size="14" />
                          {{ ch.user?.full_name || ch.user?.username || 'Автоматически' }}
                        </span>
                        <span>{{ formatDateTime(ch.created_at) }}</span>
                      </div>
                      <div class="text-body-2 font-weight-medium text-high-emphasis" style="white-space: pre-line;">
                        {{ ch.details }}
                      </div>
                    </div>
                  </div>
                </VCardText>
              </VCard>
            </VCol>
          </VRow>
        </VCardText>

        <!-- Кнопка закрытия для мобильных -->
        <div class="d-flex d-md-none mobile-bottom-bar bg-var-theme-surface border-t justify-center py-2">
          <VBtn
            color="secondary"
            variant="outlined"
            prepend-icon="ri-close-line"
            size="large"
            class="w-75"
            @click="closeListView"
          >
            Закрыть просмотр
          </VBtn>
        </div>
      </VCard>
    </VDialog>

    <!-- ДИАЛОГ ПОДТВЕРЖДЕНИЯ УДАЛЕНИЯ СПИСКА -->
    <VDialog
      v-model="deleteListDialog"
      max-width="400px"
    >
      <VCard title="Подтверждение удаления">
        <VCardText class="pa-4 pt-0">
          Вы уверены, что хотите удалить список закупа <strong>{{ listToDelete?.name }}</strong>? 
          Все внесенные количества для позиций в рамках этого списка будут стерты безвозвратно.
        </VCardText>
        <VCardActions class="pa-4 pt-0 d-flex justify-end gap-2">
          <VBtn variant="text" color="secondary" @click="deleteListDialog = false">Отмена</VBtn>
          <VBtn color="error" variant="flat" :loading="isDeletingList" @click="deleteList">Удалить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>

<style scoped>
@import "@styles/purchase.css";
</style>
