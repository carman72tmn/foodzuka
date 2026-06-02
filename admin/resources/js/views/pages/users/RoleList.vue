<script setup>
import { ref, onMounted, computed } from 'vue'
import { authState, getAuthHeaders } from '@/utils/auth.js'

const roles = ref([])
const permissions = ref([])
const loading = ref(true)
const isDialogVisible = ref(false)
const isPermissionDialogVisible = ref(false)
const isDeleting = ref(false)
const deleteDialog = ref(false)
const roleToDelete = ref(null)

const headers = [
  { title: 'Название', key: 'name' },
  { title: 'Код', key: 'code' },
  { title: 'Системная', key: 'is_system' },
  { title: 'Права', key: 'permissions_count' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'end' },
]

const editedItem = ref({
  id: null,
  name: '',
  code: '',
  description: '',
})

const defaultItem = {
  id: null,
  name: '',
  code: '',
  description: '',
}

const selectedRole = ref(null)
const selectedPermissions = ref([])

const formTitle = computed(() => editedItem.value.id ? 'Редактировать роль' : 'Новая роль')

// Группировка прав по категориям
const groupedPermissions = computed(() => {
  const groups = {}
  permissions.value.forEach(p => {
    if (!groups[p.category]) groups[p.category] = []
    groups[p.category].push(p)
  })
  return groups
})

const fetchRoles = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/users/roles', {
      headers: getAuthHeaders()
    })
    if (response.ok) roles.value = await response.json()
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchPermissions = async () => {
  try {
    const response = await fetch('/api/v1/users/permissions', {
      headers: getAuthHeaders()
    })
    if (response.ok) permissions.value = await response.json()
  } catch (e) { console.error(e) }
}

const editItem = (item) => {
  editedItem.value = { ...item }
  isDialogVisible.value = true
}

const openPermissions = (item) => {
  selectedRole.value = item
  selectedPermissions.value = item.permissions.map(p => p.id)
  isPermissionDialogVisible.value = true
}

const close = () => {
  isDialogVisible.value = false
  editedItem.value = { ...defaultItem }
}

const save = async () => {
  const method = editedItem.value.id ? 'PATCH' : 'POST'
  const url = editedItem.value.id ? `/api/v1/users/roles/${editedItem.value.id}` : '/api/v1/users/roles'
  
  try {
    const response = await fetch(url, {
      method,
      headers: getAuthHeaders(),
      body: JSON.stringify(editedItem.value)
    })
    if (response.ok) {
      await fetchRoles()
      close()
    } else {
        const error = await response.json()
        alert(`Ошибка: ${error.detail || 'Не удалось сохранить'}`)
    }
  } catch (e) { console.error(e) }
}

const savePermissions = async () => {
  try {
    const response = await fetch(`/api/v1/users/roles/${selectedRole.value.id}/permissions`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ permission_ids: selectedPermissions.value })
    })
    if (response.ok) {
      await fetchRoles()
      isPermissionDialogVisible.value = false
    }
  } catch (e) { console.error(e) }
}

const confirmDelete = (item) => {
  roleToDelete.value = item
  deleteDialog.value = true
}

const deleteRole = async () => {
  isDeleting.value = true
  try {
    const response = await fetch(`/api/v1/users/roles/${roleToDelete.value.id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    if (response.ok) {
      await fetchRoles()
      deleteDialog.value = false
    } else {
        const error = await response.json()
        alert(`Ошибка: ${error.detail || 'Не удалось удалить'}`)
    }
  } catch (e) { console.error(e) }
  finally { isDeleting.value = false }
}

const syncIikoRoles = async () => {
    loading.value = true
    try {
        const response = await fetch('/api/v1/users/sync-iiko-roles', {
            method: 'POST',
            headers: getAuthHeaders()
        })
        if (response.ok) {
            await fetchRoles()
            alert('Синхронизация завершена')
        }
    } catch (e) { console.error(e) }
    finally { loading.value = false }
}

onMounted(() => {
  fetchRoles()
  fetchPermissions()
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard title="Управление ролями">
        <template #append>
          <div class="d-flex gap-2">
            <VBtn
              color="info"
              variant="tonal"
              prepend-icon="ri-refresh-line"
              @click="syncIikoRoles"
            >
              Синхронизация iiko
            </VBtn>
            <VBtn
              color="primary"
              prepend-icon="ri-add-line"
              @click="isDialogVisible = true"
            >
              Добавить роль
            </VBtn>
          </div>
        </template>

        <VDataTable
          :headers="headers"
          :items="roles"
          :loading="loading"
          hover
        >
          <template #item.is_system="{ item }">
            <VChip
              :color="item.is_system ? 'secondary' : 'default'"
              size="small"
              label
            >
              {{ item.is_system ? 'Системная' : 'Пользовательская' }}
            </VChip>
          </template>

          <template #item.permissions_count="{ item }">
            <VBtn
              variant="text"
              size="small"
              color="primary"
              @click="openPermissions(item)"
            >
              {{ item.permissions?.length || 0 }} прав
            </VBtn>
          </template>

          <template #item.actions="{ item }">
            <div class="d-flex justify-end">
              <VBtn
                icon="ri-shield-keyhole-line"
                size="small"
                variant="text"
                color="warning"
                title="Настроить права"
                @click="openPermissions(item)"
              />
              <VBtn
                icon="ri-edit-line"
                size="small"
                variant="text"
                color="primary"
                @click="editItem(item)"
              />
              <VBtn
                icon="ri-delete-bin-line"
                size="small"
                variant="text"
                color="error"
                :disabled="item.is_system"
                @click="confirmDelete(item)"
              />
            </div>
          </template>
        </VDataTable>
      </VCard>
    </VCol>

    <!-- Edit/Add Dialog -->
    <VDialog
      v-model="isDialogVisible"
      max-width="500px"
    >
      <VCard :title="formTitle">
        <VCardText>
          <VRow>
            <VCol cols="12">
              <VTextField
                v-model="editedItem.name"
                label="Название роли"
                placeholder="Менеджер филиала"
              />
            </VCol>
            <VCol cols="12">
              <VTextField
                v-model="editedItem.code"
                label="Код роли"
                placeholder="BRANCH_MANAGER"
                :disabled="editedItem.is_system"
              />
            </VCol>
            <VCol cols="12">
              <VTextarea
                v-model="editedItem.description"
                label="Описание"
                rows="2"
              />
            </VCol>
          </VRow>
        </VCardText>

        <VCardActions>
          <VSpacer />
          <VBtn
            color="secondary"
            variant="tonal"
            @click="close"
          >
            Отмена
          </VBtn>
          <VBtn
            color="primary"
            @click="save"
          >
            Сохранить
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Permissions Dialog -->
    <VDialog
      v-model="isPermissionDialogVisible"
      max-width="800px"
      scrollable
    >
      <VCard :title="`Настройка прав: ${selectedRole?.name}`">
        <VCardText style="height: 500px;">
          <div v-for="(perms, category) in groupedPermissions" :key="category" class="mb-6">
            <h3 class="text-h6 mb-3 text-primary">{{ category }}</h3>
            <VRow>
              <VCol v-for="perm in perms" :key="perm.id" cols="12" sm="6" md="4">
                <VCheckbox
                  v-model="selectedPermissions"
                  :value="perm.id"
                  :label="perm.name"
                  :hint="perm.description"
                  persistent-hint
                  density="compact"
                />
              </VCol>
            </VRow>
            <VDivider class="mt-4" />
          </div>
        </VCardText>

        <VCardActions>
          <VSpacer />
          <VBtn
            color="secondary"
            variant="tonal"
            @click="isPermissionDialogVisible = false"
          >
            Отмена
          </VBtn>
          <VBtn
            color="success"
            @click="savePermissions"
          >
            Применить изменения
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Delete Confirmation -->
    <VDialog
      v-model="deleteDialog"
      max-width="400px"
    >
      <VCard title="Удаление роли">
        <VCardText>
          Вы уверены, что хотите удалить роль <strong>{{ roleToDelete?.name }}</strong>?
          Пользователи с этой ролью могут потерять доступ к системе.
        </VCardText>
        <VCardActions>
          <VSpacer />
          <VBtn
            color="secondary"
            variant="tonal"
            @click="deleteDialog = false"
          >
            Отмена
          </VBtn>
          <VBtn
            color="error"
            :loading="isDeleting"
            @click="deleteRole"
          >
            Удалить
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </VRow>
</template>
