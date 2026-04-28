<script setup>
import { ref, onMounted } from 'vue'
import { formatDateTime } from '@/utils/date'

const mailings = ref([])
const loading = ref(true)

const headers = [
  { title: 'ID', key: 'id' },
  { title: 'Название рассылки', key: 'title' },
  { title: 'Канал', key: 'channel' },
  { title: 'Статус', key: 'status' },
  { title: 'Аудитория', key: 'target_count', align: 'end' },
  { title: 'Отправлено', key: 'sent_count', align: 'end' },
  { title: 'Ошибок', key: 'error_count', align: 'end' },
  { title: 'Запланировано на', key: 'scheduled_at' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'end' },
]

const getStatusColor = (status) => {
    const colors = {
        draft: 'secondary',
        scheduled: 'info',
        running: 'warning',
        completed: 'success',
        cancelled: 'error'
    }
    return colors[status] || 'grey'
}

const getStatusName = (status) => {
    const names = {
        draft: 'Черновик',
        scheduled: 'Запланирована',
        running: 'В процессе',
        completed: 'Завершена',
        cancelled: 'Отменена'
    }
    return names[status] || status
}

const getChannelIcon = (channel) => {
    if (channel === 'telegram') return 'ri-telegram-line text-info'
    if (channel === 'sms') return 'ri-message-2-line text-success'
    if (channel === 'push') return 'ri-notification-3-line text-primary'
    return 'ri-mail-send-line'
}

const fetchMailings = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/mailings/')
    if (response.ok) {
        mailings.value = await response.json()
    } else {
        mailings.value = [
            { id: 1, title: 'Анонс нового меню весна 2026', channel: 'telegram', status: 'completed', target_count: 1540, sent_count: 1530, error_count: 10, scheduled_at: null },
            { id: 2, title: 'Скидка на 8 марта', channel: 'sms', status: 'scheduled', target_count: 500, sent_count: 0, error_count: 0, scheduled_at: '2026-03-08T10:00:00Z' },
            { id: 3, title: 'Реактивация "спящих" (30 дней)', channel: 'push', status: 'draft', target_count: 120, sent_count: 0, error_count: 0, scheduled_at: null },
        ]
    }
  } catch (error) {
    console.error('Error fetching mailings', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (val) => {
    return formatDateTime(val)
}

onMounted(() => {
    fetchMailings()
})
</script>

<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 class="text-h4 mb-0">Рассылки</h2>
      <div>
         <VBtn color="primary" prepend-icon="ri-add-line">
            Создать рассылку
         </VBtn>
      </div>
    </div>

    <VCard>
      <VCardText class="d-flex align-center flex-wrap gap-4">
        <div style="width: 200px;">
          <VSelect
            label="Канал"
            :items="['Все', 'Telegram', 'SMS', 'Push']"
            density="compact"
            hide-details
          />
        </div>
        <div style="width: 200px;">
          <VSelect
            label="Статус"
            :items="['Все', 'Черновики', 'Запланированные', 'Завершенные']"
            density="compact"
            hide-details
          />
        </div>
      </VCardText>
      <VDivider />

      <VDataTable
        :headers="headers"
        :items="mailings"
        :loading="loading"
        hover
      >
        <template #item.channel="{ item }">
            <div class="d-flex align-center gap-2">
                <VIcon :icon="getChannelIcon(item.channel)" size="small" />
                <span class="text-capitalize">{{ item.channel }}</span>
            </div>
        </template>
        
        <template #item.status="{ item }">
            <VChip size="small" :color="getStatusColor(item.status)">
                {{ getStatusName(item.status) }}
            </VChip>
        </template>
        
        <template #item.scheduled_at="{ item }">
             <span class="text-body-2">{{ formatDate(item.scheduled_at) }}</span>
        </template>

        <template #item.actions="{ item }">
             <VBtn icon="ri-edit-line" size="small" variant="text" color="primary" class="me-1" v-if="item.status === 'draft' || item.status === 'scheduled'" />
             <VBtn icon="ri-bar-chart-2-line" size="small" variant="text" color="info" title="Статистика" v-else />
             <VBtn icon="ri-delete-bin-line" size="small" variant="text" color="error" v-if="item.status === 'draft'" />
        </template>
      </VDataTable>
    </VCard>
  </div>
</template>
