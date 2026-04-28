<script setup>
import { ref, onMounted, computed } from 'vue'
import { authState } from '@/utils/auth.js'

const users = ref([])
const roles = ref([])
const employees = ref([])
const loading = ref(true)
const isDialogVisible = ref(false)
const isDeleting = ref(false)
const deleteDialog = ref(false)
const userToDelete = ref(null)

const headers = [
  { title: 'Логин', key: 'username' },
  { title: 'ФИО', key: 'full_name' },
  { title: 'Роль', key: 'role_name' },
  { title: 'Сотрудник iiko', key: 'employee_name' },
  { title: 'Активен', key: 'is_active' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'end' },
]

const editedItem = ref({
  id: null,
  username: '',
  password: '',
  full_name: '',
  role_id: null,
  iiko_id: null,
  is_active: true,
})

const defaultItem = {
  id: null,
  username: '',
  password: '',
  full_name: '',
  role_id: null,
  iiko_id: null,
  is_active: true,
}

const formTitle = computed(() => editedItem.value.id ? 'Редактировать пользователя' : 'Новый пользователь')

const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/users/', {
      headers: { 'Authorization': `Bearer ${authState.token}` }
    })
    if (response.ok) users.value = await response.json()
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchRoles = async () => {
  try {
    const response = await fetch('/api/v1/users/roles', {
      headers: { 'Authorization': `Bearer ${authState.token}` }
    })
    if (response.ok) roles.value = await response.json()
  } catch (e) { console.error(e) }
}

const fetchEmployees = async () => {
  try {
    const response = await fetch('/api/v1/users/employees', {
      headers: { 'Authorization': `Bearer ${authState.token}` }
    })
    if (response.ok) employees.value = await response.json()
  } catch (e) { console.error(e) }
}

const editItem = (item) => {
  editedItem.value = { ...item, password: '' }
  isDialogVisible.value = true
}

const close = () => {
  isDialogVisible.value = false
  editedItem.value = { ...defaultItem }
}

const save = async () => {
  const method = editedItem.value.id ? 'PATCH' : 'POST'
  const url = editedItem.value.id ? `/api/v1/users/${editedItem.value.id}` : '/api/v1/users/'
  
  // Remove password if empty on edit
  const payload = { ...editedItem.value }
  if (method === 'PATCH' && !payload.password) delete payload.password
  if (method === 'POST' && !payload.password) {
      alert('Пароль обязателен для нового пользователя')
      return
  }

  try {
    const response = await fetch(url, {
      method,
      headers: { 
        'Authorization': `Bearer ${authState.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    if (response.ok) {
      await fetchUsers()
      close()
    } else {
        const error = await response.json()
        alert(`Ошибка: ${error.detail || 'Не удалось сохранить'}`)
    }
  } catch (e) { console.error(e) }
}

const confirmDelete = (item) => {
  userToDelete.value = item
  deleteDialog.value = true
}

const deleteUser = async () => {
  isDeleting.value = true
  try {
    const response = await fetch(`/api/v1/users/${userToDelete.value.id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${authState.token}` }
    })
    if (response.ok) {
      await fetchUsers()
      deleteDialog.value = false
    }
  } catch (e) { console.error(e) }
  finally { isDeleting.value = false }
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
  fetchEmployees()
})
</script>

<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 class="text-h4 mb-0">Пользователи</h2>
      <VBtn
        color="primary"
        prepend-icon="ri-user-add-line"
        @click="isDialogVisible = true"
      >
        Добавить пользователя
      </VBtn>
    </div>

    <VCard>
      <VDataTable
        :headers="headers"
        :items="users"
        :loading="loading"
        hover
      >
        <template #item.username="{ item }">
          <div class="d-flex align-center">
            <VAvatar
              size="32"
              :color="item.role_name === 'SUPER_ADMIN' ? 'error' : 'primary'"
              variant="tonal"
              class="me-3"
            >
              <span class="text-xs">{{ item.username.substring(0, 2).toUpperCase() }}</span>
            </VAvatar>
            <span class="font-weight-medium">{{ item.username }}</span>
          </div>
        </template>

        <template #item.role_name="{ item }">
          <VChip
            :color="item.role_name === 'SUPER_ADMIN' ? 'error' : 'info'"
            size="small"
            label
          >
            {{ item.role_name }}
          </VChip>
        </template>

        <template #item.employee_name="{ item }">
          <span v-if="item.employee">{{ item.employee.name }}</span>
          <span v-else class="text-disabled">Не привязан</span>
        </template>

        <template #item.is_active="{ item }">
          <VIcon
            :icon="item.is_active ? 'ri-checkbox-circle-line' : 'ri-close-circle-line'"
            :color="item.is_active ? 'success' : 'error'"
          />
        </template>

        <template #item.actions="{ item }">
          <div class="d-flex justify-end">
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
              :disabled="item.username === '0001'"
              @click="confirmDelete(item)"
            />
          </div>
        </template>
      </VDataTable>
    </VCard>

    <!-- Edit/Add Dialog -->
    <VDialog
      v-model="isDialogVisible"
      max-width="600px"
    >
      <VCard :title="formTitle">
        <VCardText>
          <VRow>
            <VCol cols="12" md="6">
              <VTextField
                v-model="editedItem.username"
                label="Логин"
                placeholder="0001"
              />
            </VCol>
            <VCol cols="12" md="6">
              <VTextField
                v-model="editedItem.password"
                label="Пароль"
                :placeholder="editedItem.id ? 'Оставьте пустым, чтобы не менять' : '············'"
                type="password"
              />
            </VCol>
            <VCol cols="12">
              <VTextField
                v-model="editedItem.full_name"
                label="ФИО"
                placeholder="Иванов Иван Иванович"
              />
            </VCol>
            <VCol cols="12" md="6">
              <VSelect
                v-model="editedItem.role_id"
                :items="roles"
                item-title="name"
                item-value="id"
                label="Роль"
              />
            </VCol>
            <VCol cols="12" md="6">
              <VSelect
                v-model="editedItem.iiko_id"
                :items="employees"
                item-title="name"
                item-value="iiko_id"
                label="Сотрудник iiko"
                clearable
              />
            </VCol>
            <VCol cols="12">
              <VSwitch
                v-model="editedItem.is_active"
                label="Активен"
                color="success"
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

    <!-- Delete Confirmation -->
    <VDialog
      v-model="deleteDialog"
      max-width="400px"
    >
      <VCard title="Удаление пользователя">
        <VCardText>
          Вы уверены, что хотите удалить пользователя <strong>{{ userToDelete?.username }}</strong>?
          Это действие нельзя отменить.
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
            @click="deleteUser"
          >
            Удалить
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>
