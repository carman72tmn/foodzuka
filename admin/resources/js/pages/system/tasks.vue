<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { formatDateTime } from '@/utils/date'

const tab = ref('tasks')
const loading = ref(false)
const tasks = ref([])
const files = ref([])
const timer = ref(null)
const scheduledTasks = ref([])

const API_BASE = '/api/v1/system'

// Диалог запланированной задачи
const scheduledTaskDialog = ref(false)
const editTask = ref({
  name: '',
  task_name: '',
  trigger_type: 'interval',
  trigger_value: '{"minutes": 10}',
  args: '[]',
  kwargs: '{}',
  is_active: true,
  description: ''
})

// Диалог запуска задачи
const runTaskDialog = ref(false)
const newTask = ref({
  type: 'customers',
  params: {
    force_update: false,
    hours: 24
  }
})

const fetchTasks = async () => {
  try {
    const res = await fetch(`${API_BASE}/tasks`)
    if (res.ok) tasks.value = await res.json()
  } catch (e) {
    console.error('Error fetching tasks:', e)
  }
}

const fetchFiles = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/files`)
    if (res.ok) files.value = await res.json()
  } catch (e) {
    console.error('Error fetching files:', e)
  } finally {
    loading.value = false
  }
}

const loadData = () => {
  if (tab.value === 'tasks') fetchTasks()
  if (tab.value === 'files') fetchFiles()
  if (tab.value === 'scheduled') fetchScheduledTasks()
}

const fetchScheduledTasks = async () => {
  try {
    const res = await fetch(`${API_BASE}/scheduled-tasks`)
    if (res.ok) scheduledTasks.value = await res.json()
  } catch (e) {
    console.error('Error fetching scheduled tasks:', e)
  }
}

const saveScheduledTask = async () => {
  loading.value = true
  try {
    const isNew = !editTask.value.id
    const url = isNew ? `${API_BASE}/scheduled-tasks` : `${API_BASE}/scheduled-tasks/${editTask.value.id}`
    const method = isNew ? 'POST' : 'PUT'
    
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editTask.value)
    })
    
    if (res.ok) {
      scheduledTaskDialog.value = false
      fetchScheduledTasks()
    }
  } catch (e) {
    console.error('Error saving task:', e)
  } finally {
    loading.value = false
  }
}

const toggleScheduledTask = async (task) => {
  try {
    await fetch(`${API_BASE}/scheduled-tasks/${task.id}/toggle`, { method: 'POST' })
    fetchScheduledTasks()
  } catch (e) {
    console.error('Error toggling task:', e)
  }
}

const runScheduledTaskNow = async (task) => {
  try {
    const res = await fetch(`${API_BASE}/scheduled-tasks/${task.id}/run`, { method: 'POST' })
    if (res.ok) alert('Задача запущена успешно')
  } catch (e) {
    console.error('Error running task:', e)
  }
}

const deleteScheduledTask = async (task) => {
  if (!confirm(`Удалить задачу ${task.name}?`)) return
  try {
    await fetch(`${API_BASE}/scheduled-tasks/${task.id}`, { method: 'DELETE' })
    fetchScheduledTasks()
  } catch (e) {
    console.error('Error deleting task:', e)
  }
}

const openEditDialog = (task = null) => {
  if (task) {
    editTask.value = { ...task }
  } else {
    editTask.value = {
      name: '',
      task_name: '',
      trigger_type: 'interval',
      trigger_value: '{"minutes": 10}',
      args: '[]',
      kwargs: '{}',
      is_active: true,
      description: ''
    }
  }
  scheduledTaskDialog.value = true
}

const togglePause = async (task) => {
  try {
    await fetch(`${API_BASE}/tasks/${task.id}/pause`, { method: 'POST' })
    fetchTasks()
  } catch (e) {
    console.error('Error toggling pause:', e)
  }
}

const cancelTask = async (task) => {
  if (!confirm('Вы уверены, что хотите отменить задачу?')) return
  try {
    await fetch(`${API_BASE}/tasks/${task.id}/cancel`, { method: 'POST' })
    fetchTasks()
  } catch (e) {
    console.error('Error cancelling task:', e)
  }
}

const stopAllTasks = async () => {
  if (!confirm('Остановить все активные фоновые процессы?')) return
  try {
    await fetch(`${API_BASE}/tasks/stop-all`, { method: 'POST' })
    fetchTasks()
  } catch (e) {
    console.error('Error stopping all tasks:', e)
  }
}

const cleanupTasks = async () => {
  if (!confirm('Очистить историю завершенных и отмененных задач?')) return
  try {
    await fetch(`${API_BASE}/tasks/cleanup`, { method: 'POST' })
    fetchTasks()
  } catch (e) {
    console.error('Error cleaning up tasks:', e)
  }
}

const refreshTask = async (task) => {
  try {
    const res = await fetch(`${API_BASE}/tasks/${task.id}/refresh`, { method: 'POST' })
    if (res.ok) {
      const updated = await res.json()
      const idx = tasks.value.findIndex(t => t.id === task.id)
      if (idx !== -1) tasks.value[idx] = updated
    }
  } catch (e) {
    console.error('Error refreshing task:', e)
  }
}

const deleteTask = async (task) => {
  if (!confirm('Удалить запись о задаче?')) return
  try {
    await fetch(`${API_BASE}/tasks/${task.id}`, { method: 'DELETE' })
    fetchTasks()
  } catch (e) {
    console.error('Error deleting task:', e)
  }
}

const startTask = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/tasks/run?task_type=${newTask.value.type}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newTask.value.params)
    })
    if (res.ok) {
      runTaskDialog.value = false
      fetchTasks()
    }
  } catch (e) {
    console.error('Error starting task:', e)
  } finally {
    loading.value = false
  }
}

const deleteFile = async (file) => {
  if (!confirm(`Удалить файл ${file.name}?`)) return
  try {
    await fetch(`${API_BASE}/files/${file.name}`, { method: 'DELETE' })
    fetchFiles()
  } catch (e) {
    console.error('Error deleting file:', e)
  }
}

onMounted(() => {
  loadData()
  timer.value = setInterval(() => {
    if (tab.value === 'tasks') fetchTasks()
    if (tab.value === 'scheduled') fetchScheduledTasks()
  }, 3000)
})

onUnmounted(() => {
  if (timer.value) clearInterval(timer.value)
})

const getStatusColor = (status) => {
  const map = {
    running: 'primary',
    completed: 'success',
    error: 'error',
    cancelled: 'warning',
    pending: 'grey'
  }
  return map[status] || 'grey'
}

const getTaskTypeName = (type) => {
  const map = {
    import: 'Импорт из файла',
    customers: 'Синхронизация гостей',
    menu: 'Синхронизация меню',
    orders: 'Синхронизация заказов',
  }
  return map[type] || type
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard>
        <VCardTitle class="d-flex align-center py-4">
          <VIcon icon="bx-cog" class="me-3" color="primary" />
          Управление фоновыми процессами
          <VSpacer />
          <div class="d-flex gap-2">
            <VBtn
              color="error"
              variant="tonal"
              prepend-icon="bx-stop-circle"
              size="small"
              @click="stopAllTasks"
            >
              Остановить всё
            </VBtn>
            <VBtn
              color="secondary"
              variant="tonal"
              prepend-icon="bx-trash"
              size="small"
              @click="cleanupTasks"
            >
              Очистить историю
            </VBtn>
            <VBtn
              color="primary"
              prepend-icon="bx-plus"
              size="small"
              @click="runTaskDialog = true"
            >
              Новая задача
            </VBtn>
          </div>
        </VCardTitle>

        <VTabs v-model="tab" @update:model-value="loadData">
          <VTab value="tasks">Задачи (Celery)</VTab>
          <VTab value="scheduled">Автоматические задачи</VTab>
          <VTab value="files">Файлы импорта</VTab>
        </VTabs>

        <VWindow v-model="tab">
          <!-- Задачи -->
          <VWindowItem value="tasks">
            <VCardText>
              <VDataTable
                :items="tasks"
                :headers="[
                  { title: 'Время', key: 'updated_at' },
                  { title: 'Тип процесса', key: 'sync_type' },
                  { title: 'Статус', key: 'status' },
                  { title: 'Выполнение', key: 'progress' },
                  { title: 'Управление', key: 'actions', sortable: false }
                ]"
                density="comfortable"
              >
                <template #item.updated_at="{ item }">
                  <div class="text-no-wrap">{{ formatDateTime(item.updated_at) }}</div>
                </template>

                <template #item.sync_type="{ item }">
                  <div class="font-weight-medium">{{ getTaskTypeName(item.sync_type) }}</div>
                </template>
                
                <template #item.status="{ item }">
                  <div class="d-flex flex-column">
                    <div class="d-flex align-center">
                      <VChip :color="getStatusColor(item.status)" size="small" class="font-weight-bold">
                        <template #prepend>
                          <VIcon v-if="item.status === 'running'" icon="bx-loader-alt" class="bx-spin me-1" size="14" />
                        </template>
                        {{ item.status.toUpperCase() }}
                      </VChip>
                      <VChip v-if="item.is_paused" color="info" size="small" variant="elevated" class="ms-1">
                        PAUSED
                      </VChip>
                    </div>
                    <div v-if="item.details" class="text-caption text-truncate mt-1" style="max-width: 250px;">
                      {{ item.details }}
                      <VTooltip activator="parent" location="bottom">{{ item.details }}</VTooltip>
                    </div>
                  </div>
                </template>

                <template #item.progress="{ item }">
                  <div style="min-width: 180px" class="py-2">
                    <VProgressLinear
                      :model-value="item.total_count > 0 ? (item.processed_count / item.total_count * 100) : 0"
                      :color="getStatusColor(item.status)"
                      height="12"
                      rounded
                      striped
                      :active="item.status === 'running'"
                      indeterminate-active
                    >
                      <template v-slot:default="{ value }">
                        <span class="text-white font-weight-bold" style="font-size: 9px">{{ Math.ceil(value) }}%</span>
                      </template>
                    </VProgressLinear>
                    <div class="d-flex justify-space-between text-caption mt-1">
                      <span>{{ item.processed_count }} из {{ item.total_count }}</span>
                      <span class="text-success" v-if="item.added_count > 0">+{{ item.added_count }}</span>
                    </div>
                  </div>
                </template>

                <template #item.actions="{ item }">
                  <div class="d-flex gap-1">
                    <VBtn
                      v-if="item.status === 'running'"
                      icon="bx-refresh"
                      size="x-small"
                      variant="text"
                      color="primary"
                      @click="refreshTask(item)"
                    >
                      <VTooltip activator="parent" location="top">Синхрон. статус</VTooltip>
                    </VBtn>

                    <VBtn
                      v-if="item.status === 'running'"
                      :icon="item.is_paused ? 'bx-play' : 'bx-pause'"
                      size="x-small"
                      variant="text"
                      :color="item.is_paused ? 'success' : 'warning'"
                      @click="togglePause(item)"
                    >
                      <VTooltip activator="parent" location="top">{{ item.is_paused ? 'Продолжить' : 'Пауза' }}</VTooltip>
                    </VBtn>
                    
                    <VBtn
                      v-if="item.status === 'running' || item.status === 'pending'"
                      icon="bx-stop"
                      size="x-small"
                      variant="text"
                      color="error"
                      @click="cancelTask(item)"
                    >
                      <VTooltip activator="parent" location="top">Отменить</VTooltip>
                    </VBtn>

                    <VBtn
                      icon="bx-trash"
                      size="x-small"
                      variant="text"
                      color="grey-darken-1"
                      @click="deleteTask(item)"
                    >
                      <VTooltip activator="parent" location="top">Удалить из лога</VTooltip>
                    </VBtn>
                  </div>
                </template>
              </VDataTable>
            </VCardText>
          </VWindowItem>

          <!-- Автоматические задачи -->
          <VWindowItem value="scheduled">
            <VCardText>
              <div class="d-flex justify-end mb-4">
                <VBtn
                  color="primary"
                  prepend-icon="bx-plus"
                  @click="openEditDialog()"
                >
                  Создать расписание
                </VBtn>
              </div>

              <VDataTable
                :items="scheduledTasks"
                :headers="[
                  { title: 'Название', key: 'name' },
                  { title: 'Расписание', key: 'schedule' },
                  { title: 'Статус', key: 'is_active' },
                  { title: 'Последний запуск', key: 'last_run' },
                  { title: 'Следующий запуск', key: 'next_run' },
                  { title: 'Действия', key: 'actions', sortable: false }
                ]"
              >
                <template #item.name="{ item }">
                  <div class="font-weight-medium">{{ item.name }}</div>
                  <div class="text-caption text-grey">{{ item.description }}</div>
                </template>

                <template #item.schedule="{ item }">
                  <VChip size="x-small" :color="item.trigger_type === 'cron' ? 'purple' : 'info'" class="me-1">
                    {{ item.trigger_type.toUpperCase() }}
                  </VChip>
                  <span class="text-caption">{{ item.trigger_value }}</span>
                </template>

                <template #item.is_active="{ item }">
                  <VSwitch
                    v-model="item.is_active"
                    hide-details
                    density="compact"
                    @change="toggleScheduledTask(item)"
                    :color="item.is_active ? 'success' : 'grey'"
                  />
                </template>

                <template #item.last_run="{ item }">
                  <span class="text-caption">{{ item.last_run ? formatDateTime(item.last_run) : '---' }}</span>
                </template>

                <template #item.next_run="{ item }">
                  <span class="text-caption">{{ item.next_run ? formatDateTime(item.next_run) : '---' }}</span>
                </template>

                <template #item.actions="{ item }">
                  <div class="d-flex gap-1">
                    <VBtn
                      icon="bx-play"
                      size="x-small"
                      variant="text"
                      color="success"
                      @click="runScheduledTaskNow(item)"
                    >
                      <VTooltip activator="parent" location="top">Запустить сейчас</VTooltip>
                    </VBtn>
                    <VBtn
                      icon="bx-edit"
                      size="x-small"
                      variant="text"
                      color="primary"
                      @click="openEditDialog(item)"
                    >
                      <VTooltip activator="parent" location="top">Редактировать</VTooltip>
                    </VBtn>
                    <VBtn
                      icon="bx-trash"
                      size="x-small"
                      variant="text"
                      color="error"
                      @click="deleteScheduledTask(item)"
                    >
                      <VTooltip activator="parent" location="top">Удалить</VTooltip>
                    </VBtn>
                  </div>
                </template>
              </VDataTable>
            </VCardText>
          </VWindowItem>

          <!-- Файлы -->
          <VWindowItem value="files">
            <VCardText>
              <div class="d-flex justify-end mb-4">
                <VBtn
                  color="primary"
                  prepend-icon="bx-refresh"
                  :loading="loading"
                  @click="fetchFiles"
                >
                  Обновить список
                </VBtn>
              </div>
              <VDataTable
                :items="files"
                :headers="[
                  { title: 'Имя файла', key: 'name' },
                  { title: 'Размер', key: 'size' },
                  { title: 'Создан', key: 'created_at' },
                  { title: 'Действия', key: 'actions', sortable: false }
                ]"
              >
                <template #item.size="{ item }">
                  {{ formatSize(item.size) }}
                </template>
                <template #item.created_at="{ item }">
                  {{ formatDateTime(item.created_at) }}
                </template>
                <template #item.actions="{ item }">
                  <VBtn
                    icon="bx-trash"
                    size="x-small"
                    variant="text"
                    color="error"
                    @click="deleteFile(item)"
                  />
                </template>
              </VDataTable>
            </VCardText>
          </VWindowItem>
        </VWindow>
      </VCard>
    </VCol>
  </VRow>

  <!-- Диалог запуска новой задачи -->
  <VDialog v-model="runTaskDialog" max-width="500px">
    <VCard>
      <VCardTitle>Запуск новой фоновой задачи</VCardTitle>
      <VCardText>
        <VSelect
          v-model="newTask.type"
          label="Тип задачи"
          :items="[
            { title: 'Синхронизация гостей', value: 'customers' },
            { title: 'Синхронизация меню', value: 'menu' },
            { title: 'Синхронизация заказов', value: 'orders' }
          ]"
          class="mb-4"
        />

        <div v-if="newTask.type === 'customers'">
          <VSwitch
            v-model="newTask.params.force_update"
            label="Обновить существующих гостей (Force Update)"
            color="primary"
          />
          <p class="text-caption text-grey">
            Если выключено, будут загружены только новые гости.
          </p>
        </div>

        <div v-if="newTask.type === 'orders'">
          <VSlider
            v-model="newTask.params.hours"
            label="Глубина поиска (часов)"
            min="1"
            max="720"
            step="1"
            thumb-label="always"
          />
          <p class="text-caption text-grey">
            За какой период выгружать историю заказов из iiko.
          </p>
        </div>
      </VCardText>
      <VCardActions>
        <VSpacer />
        <VBtn variant="text" @click="runTaskDialog = false">Отмена</VBtn>
        <VBtn color="primary" :loading="loading" @click="startTask">Запустить</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>

<style scoped>
.gap-1 { gap: 4px; }
.gap-2 { gap: 8px; }
</style>

