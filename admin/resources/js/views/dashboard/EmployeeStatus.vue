<script setup>
import { ref, onMounted } from 'vue'

const openShifts = ref([])
const loading = ref(false)

const fetchOpenShifts = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/v1/employees/shifts/open')
    const data = await res.json()
    if (data.status === 'success') {
      openShifts.value = data.data
    }
  } catch (error) {
    console.error('Error fetching open shifts:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

onMounted(fetchOpenShifts)
</script>

<template>
  <VCard title="Кто на смене" subtitle="Активные сотрудники">
    <template #append>
      <VBtn icon="bx-refresh" variant="text" size="small" @click="fetchOpenShifts" :loading="loading" />
    </template>

    <VCardText>
      <VList v-if="openShifts.length" lines="two">
        <VListItem
          v-for="shift in openShifts"
          :key="shift.id"
          :title="shift.employee_name"
          :subtitle="`Начал в ${formatDate(shift.date_open)}`"
        >
          <template #prepend>
            <VAvatar color="success" variant="tonal" size="32">
              <VIcon icon="bx-user" size="18" />
            </VAvatar>
          </template>
        </VListItem>
      </VList>
      <div v-else-if="!loading" class="text-center py-4 text-disabled">
        Нет активных смен
      </div>
      <div v-else class="text-center py-4">
        <VProgressCircular indeterminate size="24" color="primary" />
      </div>
    </VCardText>
  </VCard>
</template>
