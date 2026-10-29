<script setup>
import { ref, onMounted, computed } from "vue"

const loading = ref(false)
const syncLoading = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const search = ref("")
const categories = ref([])

const API_BASE = "/api/v1"

// Поля для редактирования
const editDialog = ref(false)
const editingCategory = ref(null)
const saveLoading = ref(false)

// Групповое удаление
const deleteDialog = ref(false)
const deleteLoading = ref(false)

const headers = [
  { title: "ID", key: "id", sortable: true, width: 70 },
  { title: "Название", key: "name", sortable: true },
  { title: "Описание", key: "description", sortable: false },
  { title: "iiko ID", key: "iiko_id", sortable: false, width: 100 },
  { title: "Товаров", key: "products_count", sortable: true, width: 90 },
  { title: "Опций", key: "modifiers_count", sortable: true, width: 90 },
  { title: "Активна", key: "is_active", sortable: true, width: 100 },
  { title: "Действия", key: "actions", sortable: false, width: 100 },
]

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const loadCategories = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/categories/tree`)
    if (res.ok) {
      categories.value = await res.json()
    }
  } catch (e) {
    showMessage("Ошибка загрузки категорий", "error")
  } finally {
    loading.value = false
  }
}

const syncFromIiko = async () => {
  syncLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/categories/sync-from-iiko`, { method: 'POST' })
    const data = await res.json()
    if (res.ok) {
      showMessage(data.message || "Синхронизация категорий завершена")
      loadCategories()
    } else {
      showMessage(data.detail || "Ошибка синхронизации", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети при синхронизации", "error")
  } finally {
    syncLoading.value = false
  }
}

const deleteAllCategories = async () => {
  deleteLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/categories/all`, { method: 'DELETE' })
    if (res.ok) {
      showMessage("Все категории удалены", "warning")
      deleteDialog.value = false
      loadCategories()
    } else {
      showMessage("Ошибка при удалении", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    deleteLoading.value = false
  }
}

const openEdit = (item) => {
  editingCategory.value = { ...item }
  editDialog.value = true
}

const singleDeleteDialog = ref(false)
const singleDeleteLoading = ref(false)
const categoryToDelete = ref(null)

const confirmDelete = (item) => {
  categoryToDelete.value = item
  singleDeleteDialog.value = true
}

const deleteCategory = async (id) => {
  singleDeleteLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/categories/${id}`, { method: 'DELETE' })
    if (res.ok) {
      showMessage("Категория удалена")
      singleDeleteDialog.value = false
      loadCategories()
    } else {
      showMessage("Ошибка удаления", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    singleDeleteLoading.value = false
  }
}

const deleteEmptyLoading = ref(false)
const deleteEmptyCategories = async () => {
  if (!confirm("Вы уверены, что хотите удалить все разделы, в которых нет товаров и подкатегорий?")) return
  deleteEmptyLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/categories/empty`, { method: 'DELETE' })
    if (res.ok) {
      const data = await res.json()
      showMessage(`Удалено пустых разделов: ${data.deleted_count}`)
      loadCategories()
    } else {
      showMessage("Ошибка удаления пустых разделов", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    deleteEmptyLoading.value = false
  }
}

const saveCategory = async () => {
  if (!editingCategory.value) return
  saveLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/categories/${editingCategory.value.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: editingCategory.value.name,
        description: editingCategory.value.description,
        is_active: editingCategory.value.is_active,
        sort_order: editingCategory.value.sort_order,
        lock_name: editingCategory.value.lock_name,
        lock_description: editingCategory.value.lock_description,
        lock_image: editingCategory.value.lock_image,
        lock_parent: editingCategory.value.lock_parent,
        hide_category_only: editingCategory.value.hide_category_only,
        hide_category_and_products: editingCategory.value.hide_category_and_products,
        parent_id: editingCategory.value.parent_id
      })
    })
    if (res.ok) {
      showMessage("Категория сохранена")
      editDialog.value = false
      loadCategories()
    } else {
      showMessage("Ошибка сохранения", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    saveLoading.value = false
  }
}

onMounted(loadCategories)
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard class="elevation-2 border">
        <VCardTitle class="d-flex align-center py-4 px-6">
          <VIcon icon="mdi-shape-outline" color="primary" class="me-3" size="32" />
          <div class="text-h5 font-weight-bold">Дерево категорий</div>
          <VSpacer />
          
          <VTextField
            v-model="search"
            prepend-inner-icon="mdi-magnify"
            label="Поиск категорий"
            variant="solo-filled"
            flat
            density="compact"
            hide-details
            class="me-4"
            style="max-width: 300px"
          />

          <VBtn
            v-if="categories.length > 0"
            color="warning"
            variant="tonal"
            prepend-icon="mdi-delete-outline"
            class="me-2 rounded-pill"
            :loading="deleteEmptyLoading"
            @click="deleteEmptyCategories"
          >
            Удалить пустые
          </VBtn>

          <VBtn
            v-if="categories.length > 0"
            color="error"
            variant="tonal"
            prepend-icon="mdi-delete-sweep"
            class="me-2 rounded-pill"
            @click="deleteDialog = true"
          >
            Удалить все
          </VBtn>

          <VBtn
            color="primary"
            prepend-icon="mdi-sync"
            :loading="syncLoading"
            @click="syncFromIiko"
            class="rounded-pill"
          >
            Синхронизировать
          </VBtn>
        </VCardTitle>

        <VCardText class="pa-0">
          <VDataTable
            :headers="headers"
            :items="categories"
            :loading="loading"
            :search="search"
            :items-per-page="-1"
            hide-default-footer
            hover
          >
            <!-- Стилизованное название с отступом для вложенности -->
            <template #item.name="{ item }">
              <div :style="{ paddingLeft: item.parent_id ? '32px' : '0px' }" class="d-flex align-center">
                <VAvatar v-if="item.image_url" size="32" class="me-3 border">
                  <VImg :src="item.image_url" cover />
                </VAvatar>
                <VIcon v-else :icon="item.parent_id ? 'mdi-subdirectory-arrow-right' : 'mdi-folder'" 
                       :color="item.parent_id ? 'grey' : 'primary'" class="me-2" />
                <span :class="{'font-weight-bold': !item.parent_id}">{{ item.name }}</span>
              </div>
            </template>

            <!-- Счётчики -->
            <template #item.products_count="{ item }">
              <VChip v-if="item.products_count > 0" color="info" size="small" variant="flat">
                {{ item.products_count }}
              </VChip>
              <span v-else class="text-medium-emphasis">—</span>
            </template>

            <template #item.modifiers_count="{ item }">
              <VChip v-if="item.modifiers_count > 0" color="secondary" size="small" variant="flat">
                {{ item.modifiers_count }}
              </VChip>
              <span v-else class="text-medium-emphasis">—</span>
            </template>

            <!-- Статус -->
            <template #item.is_active="{ item }">
              <VChip
                :color="item.is_active ? 'success' : 'grey-lighten-1'"
                variant="tonal"
                size="small"
                label
                class="text-uppercase font-weight-bold"
              >
                {{ item.is_active ? "Активен" : "Скрыт" }}
              </VChip>
            </template>

            <!-- iiko ID -->
            <template #item.iiko_id="{ item }">
              <code class="text-caption" v-if="item.iiko_id">{{ item.iiko_id.split('-')[0] }}...</code>
              <VIcon v-else icon="mdi-alert-circle-outline" color="warning" size="small" />
            </template>

            <!-- Действия -->
            <template #item.actions="{ item }">
              <VBtn icon="mdi-pencil-outline" variant="text" size="small" color="primary" @click="openEdit(item)" class="me-1" />
              <VBtn icon="mdi-delete-outline" variant="text" size="small" color="error" @click="confirmDelete(item)" />
            </template>
          </VDataTable>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <!-- Диалог редактирования -->
  <VDialog v-model="editDialog" max-width="500">
    <VCard v-if="editingCategory">
      <VCardTitle class="pa-4 bg-primary text-white">Редактирование категории</VCardTitle>
      <VCardText class="pa-4 pt-6">
        <VTextField v-model="editingCategory.name" label="Название" variant="outlined" class="mb-4" />
        <VTextarea v-model="editingCategory.description" label="Описание" variant="outlined" rows="3" class="mb-4" />
        
        <!-- Выбор родительской категории -->
        <VSelect
          v-model="editingCategory.parent_id"
          :items="categories.filter(c => c.id !== editingCategory.id)"
          item-title="name"
          item-value="id"
          label="Родительская категория"
          variant="outlined"
          density="compact"
          clearable
          class="mb-4"
        />

        <VTextField v-model.number="editingCategory.sort_order" label="Порядок сортировки" type="number" variant="outlined" class="mb-4" />
        
        <div class="text-subtitle-2 font-weight-bold text-grey-darken-1 mb-2">Отображение на сайте:</div>
        <VSwitch v-model="editingCategory.is_active" label="Активна (is_active)" color="success" density="compact" class="mb-1" />
        <VSwitch v-model="editingCategory.hide_category_only" label="Скрыть только раздел (hide_category_only)" color="primary" density="compact" class="mb-1" />
        <VSwitch v-model="editingCategory.hide_category_and_products" label="Скрыть раздел и все товары (hide_category_and_products)" color="primary" density="compact" class="mb-1" />

        <div class="text-subtitle-2 font-weight-bold text-grey-darken-1 mb-2 mt-3">Настройки синхронизации IIKO:</div>
        <VSwitch v-model="editingCategory.lock_name" label="Защитить название от перезаписи из iiko" color="warning" density="compact" class="mb-1" />
        <VSwitch v-model="editingCategory.lock_description" label="Защитить описание от перезаписи из iiko" color="warning" density="compact" class="mb-1" />
        <VSwitch v-model="editingCategory.lock_image" label="Защитить изображение от перезаписи из iiko" color="warning" density="compact" class="mb-1" />
        <VSwitch v-model="editingCategory.lock_parent" label="Защитить родительскую категорию от iiko" color="warning" density="compact" class="mb-1" />
      </VCardText>
      <VCardActions class="pa-4 bg-grey-lighten-4">
        <VSpacer />
        <VBtn variant="text" @click="editDialog = false">Отмена</VBtn>
        <VBtn color="primary" variant="flat" :loading="saveLoading" @click="saveCategory">Сохранить</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- Диалог подтверждения удаления одной категории -->
  <VDialog v-model="singleDeleteDialog" max-width="400">
    <VCard v-if="categoryToDelete">
      <VCardTitle class="pa-4 bg-error text-white d-flex align-center">
        <VIcon icon="mdi-alert-thick" class="me-2" />
        Удаление категории
      </VCardTitle>
      <VCardText class="pa-4 pt-6 text-center">
        Вы действительно хотите удалить категорию <b>{{ categoryToDelete.name }}</b>?
        <div class="text-caption text-error mt-2">
          Товары останутся в базе, но потеряют привязку к этой категории.
        </div>
      </VCardText>
      <VCardActions class="pa-4">
        <VSpacer />
        <VBtn variant="text" @click="singleDeleteDialog = false">Отмена</VBtn>
        <VBtn
          color="error"
          variant="flat"
          :loading="singleDeleteLoading"
          @click="deleteCategory(categoryToDelete.id)"
        >
          Да, удалить
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- Диалог подтверждения удаления -->
  <VDialog v-model="deleteDialog" max-width="400">
    <VCard>
      <VCardTitle class="pa-4 bg-error text-white d-flex align-center">
        <VIcon icon="mdi-alert-thick" class="me-2" />
        Подтверждение удаления
      </VCardTitle>
      <VCardText class="pa-4 pt-6 text-center">
        Вы уверены, что хотите удалить <b>все категории</b>?
        <div class="text-caption text-error mt-2">
          Товары останутся в базе, но потеряют привязку к категориям.
        </div>
      </VCardText>
      <VCardActions class="pa-4">
        <VSpacer />
        <VBtn variant="text" @click="deleteDialog = false">Отмена</VBtn>
        <VBtn
          color="error"
          variant="flat"
          :loading="deleteLoading"
          @click="deleteAllCategories"
        >
          Да, удалить всё
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <VSnackbar v-model="snackbar" :color="snackbarColor" :timeout="3000" location="top right">
    {{ snackbarText }}
  </VSnackbar>
</template>

<style scoped>
.v-data-table :deep(tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.03) !important;
}
</style>
