/* eslint-disable camelcase */
<script setup>
import { ref, onMounted, watch } from 'vue'
import { formatDateTime, formatDate } from '@/utils/date'
import CustomerDetailModal from '@/components/CustomerDetailModal.vue'

const clients = ref([])
const totalClients = ref(0)
const loading = ref(true)
const search = ref('')
const page = ref(1)
const itemsPerPage = ref(20)

// Фильтры
const availableCategories = ref([])
const selectedCategories = ref([])
const filterDuplicatesPhone = ref(false)
const filterDuplicatesUid = ref(false)

const headers = [
  { title: 'ID / Имя', key: 'id_name' },
  { title: 'Телефон', key: 'phone' },
  { title: 'ЛОЯЛЬНОСТЬ', key: 'loyalty_summary' },
  { title: 'День рождения', key: 'birthday' },
  { title: 'Риск', key: 'is_risk', align: 'center' },
  { title: 'Статус / Категории', key: 'loyalty_categories' },
  { title: 'Заказы', key: 'total_orders_count', align: 'end' }, // Исправлен ключ
  { title: 'Сумма', key: 'total_orders_amount', align: 'end' }, // Исправлен ключ
  { title: 'Последний визит', key: 'last_order_date' },
  { title: 'Блок', key: 'is_blocked', align: 'center' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'end' },
]

const snackbar = ref({
  show: false,
  text: '',
  color: 'success',
})

const parseLoyaltyCategories = item => {
  const categories = item.loyalty_categories || item.categories
  if (!categories) return []
  
  // Если это уже массив
  if (Array.isArray(categories)) {
    return categories.map(c => typeof c === 'string' ? c : (c.name || ''))
  }
  
  if (typeof categories === 'string') {
    const trimmed = categories.trim()
    
    // Если это строка JSON (массив)
    if (trimmed.startsWith('[')) {
      try {
        const parsed = JSON.parse(trimmed)
        if (Array.isArray(parsed)) {
          return parsed.map(c => typeof c === 'string' ? c : (c.name || ''))
        }
      } catch (e) {
        // Fallback
      }
    }
    
    // Если это строка через запятую
    return trimmed.split(',').map(s => s.trim()).filter(Boolean)
  }
  
  return []
}

const fetchCategories = async () => {
  try {
    const response = await fetch('/api/v1/customers/categories-list')
    if (response.ok) {
      availableCategories.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching categories:', error)
  }
}

const fetchClients = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: page.value,
      limit: itemsPerPage.value,
    })

    if (search.value) {
      params.append('search', search.value)
    }

    if (selectedCategories.value && selectedCategories.value.length > 0) {
      selectedCategories.value.forEach(cat => {
        params.append('categories', cat)
      })
    }

    if (filterDuplicatesPhone.value) {
      params.append('filter_duplicates_phone', 'true')
    }

    if (filterDuplicatesUid.value) {
      params.append('filter_duplicates_uid', 'true')
    }

    const response = await fetch(`/api/v1/customers/?${params.toString()}`)
    const data = await response.json()
    console.log('Customers API data:', data)

    if (!data.items) {
      throw new Error('API response missing items array')
    }

    clients.value = data.items.map(c => ({ ...c, syncing: false }))
    totalClients.value = data.total || 0
  } catch (error) {
    console.error('Error fetching clients details:', error)
    snackbar.value = {
      show: true,
      text: 'Ошибка при загрузке клиентов',
      color: 'error',
    }
  } finally {
    loading.value = false
  }
}

// Следим за изменением страницы или поиска
watch([page, itemsPerPage, selectedCategories, filterDuplicatesPhone, filterDuplicatesUid], () => {
  fetchClients()
})

let searchTimeout = null
watch(search, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    page.value = 1
    fetchClients()
  }, 500)
})

const toggleBlock = async item => {
  try {
    // В бэкенде нет отдельного /block, используем PATCH
    const response = await fetch(`/api/v1/customers/${item.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_blocked: item.is_blocked }),
    })

    if (!response.ok) throw new Error('Failed')

    snackbar.value = {
      show: true,
      text: item.is_blocked ? 'Клиент заблокирован' : 'Клиент разблокирован',
      color: item.is_blocked ? 'error' : 'success',
    }
  } catch (error) {
    item.is_blocked = !item.is_blocked
    snackbar.value = {
      show: true,
      text: 'Ошибка при изменении статуса',
      color: 'error',
    }
  }
}

const syncWithIiko = async item => {
  item.syncing = true
  try {
    const response = await fetch(`/api/v1/customers/${item.id}/sync`, { method: 'POST' })
    if (response.ok) {
      const updatedCustomer = await response.json()

      // Update local item
      Object.assign(item, updatedCustomer)

      snackbar.value = {
        show: true,
        text: `Данные клиента ${item.name} синхронизированы`,
        color: 'success',
      }
    } else {
      const error = await response.json()

      snackbar.value = {
        show: true,
        text: `Ошибка: ${error.detail || 'Не удалось синхронизировать'}`,
        color: 'error',
      }
    }
  } catch (error) {
    snackbar.value = {
      show: true,
      text: 'Ошибка сетевого соединения',
      color: 'error',
    }
  } finally {
    item.syncing = false
  }
}

const formatMoney = val => {
  if (val === undefined || val === null) return '0'

  return new Intl.NumberFormat('ru-RU').format(val)
}

const selectedCustomer = ref(null)
const isModalVisible = ref(false)
const syncAllLoading = ref(false)

const openCustomerDetails = (item) => {
  selectedCustomer.value = item
  isModalVisible.value = true
}

const syncAll = async () => {
  if (!confirm('Вы уверены, что хотите запустить полную синхронизацию всех клиентов? Существующие данные будут обновлены данными из iiko.')) return
  
  syncAllLoading.value = true
  try {
    const response = await fetch('/api/v1/customers/sync-all?force_update=true', {
      method: 'POST',
    })


    if (response.ok) {
      const data = await response.json()

      snackbar.value = {
        show: true,
        text: `Фоновая синхронизация запущена (ID: ${data.sync_id}). Процесс идет пачками по 50 клиентов.`,
        color: 'success',
      }
    } else {
      const error = await response.json()
      snackbar.value = {
        show: true,
        text: `Ошибка: ${error.detail || 'Массовая синхронизация не удалась'}`,
        color: 'error',
      }
    }
  } catch (error) {
    snackbar.value = {
      show: true,
      text: 'Ошибка при массовой синхронизации',
      color: 'error',
    }
  } finally {
    syncAllLoading.value = false
  }
}

const handleImport = async event => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  snackbar.value = {
    show: true,
    text: 'Загрузка файла...',
    color: 'info',
  }

  try {
    const response = await fetch('/api/v1/customers/import', {
      method: 'POST',
      body: formData,
    })

    if (response.ok) {
      const data = await response.json()
      snackbar.value = {
        show: true,
        text: `Импорт запущен. ID задачи: ${data.sync_id}. Процесс идет в фоновом режиме.`,
        color: 'success',
      }
    } else {
      const error = await response.json()
      snackbar.value = {
        show: true,
        text: `Ошибка: ${error.detail || 'Не удалось запустить импорт'}`,
        color: 'error',
      }
    }
  } catch (error) {
    snackbar.value = {
      show: true,
      text: 'Ошибка при загрузке файла',
      color: 'error',
    }
  } finally {
    event.target.value = '' // Сброс инпута
  }
}

const maintenanceLoading = ref(false)

const checkIds = async () => {
  maintenanceLoading.value = true
  try {
    const response = await fetch('/api/v1/customers/maintenance/check-ids')
    if (response.ok) {
      const data = await response.json()
      alert(`Проверка завершена. Найдено клиентов без ID: ${data.total_missing}`)
    }
  } catch (error) {
    console.error('Check IDs error:', error)
  } finally {
    maintenanceLoading.value = false
  }
}

const mergeByUid = async () => {
  if (!confirm('Вы уверены, что хотите запустить объединение по UID? Это действие необратимо.')) return
  maintenanceLoading.value = true
  try {
    const response = await fetch('/api/v1/customers/maintenance/merge-by-uid', { method: 'POST' })
    if (response.ok) {
      const data = await response.json()
      snackbar.value = {
        show: true,
        text: `Объединение по UID завершено. Обработано групп: ${data.groups_processed}`,
        color: 'success',
      }
      fetchClients()
    }
  } catch (error) {
    console.error('Merge UID error:', error)
  } finally {
    maintenanceLoading.value = false
  }
}

const mergeByPhone = async () => {
  if (!confirm('Вы уверены, что хотите запустить объединение по телефону? Это действие необратимо.')) return
  maintenanceLoading.value = true
  try {
    const response = await fetch('/api/v1/customers/maintenance/merge-by-phone', { method: 'POST' })
    if (response.ok) {
      const data = await response.json()
      snackbar.value = {
        show: true,
        text: `Объединение по телефону завершено. Обработано групп: ${data.groups_processed}`,
        color: 'success',
      }
      fetchClients()
    }
  } catch (error) {
    console.error('Merge phone error:', error)
  } finally {
    maintenanceLoading.value = false
  }
}

const deleteAllClients = async () => {
  if (!confirm('ВНИМАНИЕ! Вы уверены, что хотите УДАЛИТЬ ВСЕХ клиентов? Это действие необратимо и удалит все связанные данные (адреса, историю).')) return
  
  if (!confirm('ПОДТВЕРДИТЕ ЕЩЕ РАЗ: Удалить абсолютно всех клиентов из базы?')) return

  maintenanceLoading.value = true
  try {
    const response = await fetch('/api/clients/delete-all-force', {
      method: 'DELETE',
      headers: {
        'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content'),
        'Accept': 'application/json'
      }
    })

    if (response.ok) {
      snackbar.value = {
        show: true,
        text: 'Все клиенты успешно удалены',
        color: 'success',
      }
      fetchClients()
    } else {
      const error = await response.json()
      snackbar.value = {
        show: true,
        text: `Ошибка: ${error.error || 'Не удалось удалить клиентов'}`,
        color: 'error',
      }
    }
  } catch (error) {
    console.error('Delete all error:', error)
    snackbar.value = {
      show: true,
      text: 'Ошибка при удалении',
      color: 'error',
    }
  } finally {
    maintenanceLoading.value = false
  }
}

onMounted(() => {
  fetchClients()
  fetchCategories()
})
</script>

<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 class="text-h4 mb-0">
        Все клиенты
      </h2>
      <div>
        <VBtn
          color="primary"
          variant="tonal"
          prepend-icon="ri-download-line"
          class="me-2"
        >
          Экспорт
        </VBtn>
        <VBtn
          color="success"
          variant="tonal"
          prepend-icon="ri-upload-line"
          class="me-2"
          @click="$refs.fileInput.click()"
        >
          Импорт
        </VBtn>
        <input
          ref="fileInput"
          type="file"
          style="display: none"
          accept=".xlsx,.xml"
          @change="handleImport"
        >
        <VBtn
          color="warning"
          variant="tonal"
          prepend-icon="bx-sync"
          class="me-2"
          :loading="syncAllLoading"
          @click="syncAll"
        >
          Синхронизировать всех
        </VBtn>
        <VBtn
          color="error"
          variant="tonal"
          prepend-icon="bx-trash"
          class="me-2"
          :loading="maintenanceLoading"
          @click="deleteAllClients"
        >
          Удалить всех
        </VBtn>
        <VBtn
          color="primary"
          prepend-icon="ri-add-line"
        >
          Добавить клиента
        </VBtn>
      </div>
    </div>

    <!-- Панель обслуживания -->
    <VCard
      class="mb-6 maintenance-card"
      elevation="0"
    >
      <VCardText class="pa-0">
        <div class="d-flex flex-wrap align-center justify-space-between pa-4 maintenance-bg rounded-lg">
          <div class="d-flex align-center gap-4">
            <div class="maintenance-icon-wrapper d-flex align-center justify-center rounded-circle">
              <VIcon
                icon="ri-tools-line"
                color="white"
                size="24"
              />
            </div>
            <div>
              <div class="text-h6 font-weight-bold text-white mb-0">
                Обслуживание клиентской базы
              </div>
              <div class="text-caption text-white opacity-70">
                Инструменты для очистки дубликатов и проверки ID iiko
              </div>
            </div>
          </div>
          <div class="d-flex flex-wrap gap-2 mt-4 mt-sm-0">
            <VBtn
              color="white"
              variant="elevated"
              rounded="pill"
              class="maintenance-btn"
              prepend-icon="ri-shield-check-line"
              :loading="maintenanceLoading"
              @click="checkIds"
            >
              Проверить ID
            </VBtn>
            <VBtn
              color="white"
              variant="elevated"
              rounded="pill"
              class="maintenance-btn"
              prepend-icon="ri-group-line"
              :loading="maintenanceLoading"
              @click="mergeByUid"
            >
              Слияние по UID
            </VBtn>
            <VBtn
              color="white"
              variant="elevated"
              rounded="pill"
              class="maintenance-btn"
              prepend-icon="ri-phone-line"
              :loading="maintenanceLoading"
              @click="mergeByPhone"
            >
              Слияние по телефону
            </VBtn>
          </div>
        </div>
      </VCardText>
    </VCard>

    <VCard>
      <VCardText class="d-flex align-center flex-wrap gap-4">
        <div style="width: 350px;">
          <VTextField
            v-model="search"
            placeholder="Поиск по телефону, имени, фамилии или заметкам"
            prepend-inner-icon="ri-search-line"
            density="compact"
            hide-details
            clearable
          />
        </div>

        <div style="width: 300px;">
          <VSelect
            v-model="selectedCategories"
            :items="availableCategories"
            placeholder="Фильтр по категориям"
            multiple
            chips
            closable-chips
            density="compact"
            hide-details
            clearable
            prepend-inner-icon="ri-filter-3-line"
          />
        </div>

        <VBtn
          :color="filterDuplicatesPhone ? 'error' : 'secondary'"
          variant="tonal"
          :prepend-icon="filterDuplicatesPhone ? 'ri-close-line' : 'ri-user-search-line'"
          @click="filterDuplicatesPhone = !filterDuplicatesPhone"
        >
          Дубли по телефону
        </VBtn>

        <VBtn
          :color="filterDuplicatesUid ? 'error' : 'secondary'"
          variant="tonal"
          :prepend-icon="filterDuplicatesUid ? 'ri-user-settings-line' : 'ri-user-received-line'"
          @click="filterDuplicatesUid = !filterDuplicatesUid"
        >
          Дубли по UID
        </VBtn>

        <VSpacer />
        <div class="text-caption text-disabled">
          Всего записей: {{ totalClients }}
        </div>
      </VCardText>
      <VDivider />

      <VDataTableServer
        v-model:page="page"
        v-model:items-per-page="itemsPerPage"
        :headers="headers"
        :items="clients"
        :items-length="totalClients"
        :loading="loading"
        hover
        @update:options="fetchClients"
      >
        <template #header.loyalty_categories="{ column }">
          <div class="d-flex align-center">
            <span>{{ column.title }}</span>
            <VMenu :close-on-content-click="false" location="bottom">
              <template #activator="{ props }">
                <VBtn
                  icon="ri-filter-3-line"
                  variant="text"
                  size="x-small"
                  v-bind="props"
                  :color="selectedCategories.length > 0 ? 'primary' : 'default'"
                  class="ms-1"
                />
              </template>
              <VCard min-width="250" class="pa-2">
                <VSelect
                  v-model="selectedCategories"
                  :items="availableCategories"
                  label="Выберите категории"
                  multiple
                  chips
                  closable-chips
                  density="compact"
                  variant="outlined"
                  hide-details
                  clearable
                />
              </VCard>
            </VMenu>
          </div>
        </template>
        <template #item.id_name="{ item }">
          <div class="d-flex align-center py-2" style="cursor: pointer" @click="openCustomerDetails(item)">
            <VAvatar size="32" color="primary" variant="tonal" class="me-3">
              {{ (item.name || 'G').charAt(0) }}
            </VAvatar>
            <div class="d-flex flex-column align-start">
              <span class="font-weight-bold text-no-wrap">{{ item.name }} {{ item.surname }}</span>
              <span class="text-caption text-disabled">ID: {{ item.id }}</span>
            </div>
            <VIcon v-if="item.high_risk_status" icon="bx-error" color="error" size="18" class="ms-2" />
          </div>
        </template>

        <template #item.phone="{ item }">
          <span class="text-body-2 text-primary font-weight-medium">{{ item.phone }}</span>
        </template>
        
        <template #item.loyalty_summary="{ item }">
          <div class="d-flex flex-column align-start">
            <VChip v-if="item.is_new_guest" size="x-small" color="success" class="mb-1 font-weight-bold">НОВЫЙ ГОСТЬ</VChip>
            <div v-else-if="item.bonus_points" class="d-flex align-center">
              <VIcon icon="bx-coin" size="14" color="primary" class="me-1" />
              <span class="text-body-2 font-weight-medium">{{ item.bonus_points }} баллов</span>
            </div>
            <span v-else class="text-caption text-disabled">Активен</span>
          </div>
        </template>

        <template #item.loyalty_categories="{ item }">
          <div class="d-flex flex-wrap gap-1" style="max-width: 200px">
            <template v-if="parseLoyaltyCategories(item).length">
              <VChip
                v-for="(cat, idx) in parseLoyaltyCategories(item)"
                :key="idx"
                size="x-small"
                variant="tonal"
                color="secondary"
                class="text-capitalize"
              >
                {{ cat }}
              </VChip>
            </template>
            <span v-else class="text-caption text-disabled">-</span>
          </div>
        </template>

        <template #item.is_risk="{ item }">
          <VTooltip :text="item.high_risk_reason || 'Без описания'" v-if="item.high_risk_status">
            <template #activator="{ props }">
              <VIcon v-bind="props" icon="bx-error" color="error" />
            </template>
          </VTooltip>
          <VIcon v-else icon="bx-check-shield" color="success" />
        </template>

        <template #item.birthday="{ item }">
          <span class="text-body-2">{{ item.birthday ? formatDate(item.birthday) : '-' }}</span>
        </template>


        <template #item.bonus_points="{ item }">
          <span class="text-success font-weight-bold">{{ formatMoney(item.bonus_points) }}</span>
        </template>

        <template #item.total_orders_count="{ item }">
          <span>{{ item.total_orders_count }}</span>
        </template>

        <template #item.total_orders_amount="{ item }">
          <span>{{ formatMoney(item.total_orders_amount) }}</span>
        </template>

        <template #item.last_order_date="{ item }">
          <span class="text-body-2">{{ item.last_order_date ? formatDate(item.last_order_date) : '-' }}</span>
        </template>

        <template #item.is_blocked="{ item }">
          <VSwitch
            v-model="item.is_blocked"
            color="error"
            density="compact"
            hide-details
            @change="toggleBlock(item)"
          />
        </template>

        <template #item.actions="{ item }">
          <div class="d-flex justify-end ga-1">
            <VBtn
              icon="bx-show"
              size="x-small"
              variant="text"
              color="info"
              @click="openCustomerDetails(item)"
            />
            <VBtn
              icon="bx-sync"
              size="x-small"
              variant="text"
              color="primary"
              :loading="item.syncing"
              @click="syncWithIiko(item)"
            />
            <VBtn
              :icon="item.is_blocked ? 'bx-lock-open' : 'bx-lock'"
              size="x-small"
              variant="text"
              :color="item.is_blocked ? 'success' : 'error'"
              @click="item.is_blocked = !item.is_blocked; toggleBlock(item)"
            />
          </div>
        </template>
      </VDataTableServer>
    </VCard>

    <CustomerDetailModal
      v-model="isModalVisible"
      :customer="selectedCustomer"
      @updated="fetchClients"
    />

    <VSnackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      location="top right"
    >
      {{ snackbar.text }}
    </VSnackbar>
  </div>
</template>

<style scoped>
.maintenance-bg {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.maintenance-card {
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
}

.maintenance-icon-wrapper {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.maintenance-btn {
  text-transform: none !important;
  font-weight: 600 !important;
  letter-spacing: 0.3px !important;
  transition: all 0.2s ease !important;
  color: #764ba2 !important;
}

.maintenance-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
  background-color: #f8f9fa !important;
}

.opacity-70 {
  opacity: 0.7;
}

.gap-1 { gap: 4px; }
.gap-2 { gap: 8px; }
.gap-4 { gap: 16px; }
</style>
