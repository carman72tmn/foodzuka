<script setup>
import { ref, onMounted } from 'vue'

const openShifts = ref([])
const loading = ref(false)

const fetchOpenShifts = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/v1/employees/shifts/open/detailed')
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
        >
          <template #subtitle>
            <div class="d-flex flex-column">
              <span>{{ shift.employee_role || 'Персонал' }}</span>
              <span class="text-primary font-weight-bold">На смене: {{ shift.elapsed_text }} (с {{ shift.shift_start }})</span>
            </div>
          </template>

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
