<script setup>
import { ref, onMounted } from 'vue'
import { formatDateTime } from '@/utils/date'

const tab = ref('system')
const loading = ref(false)
const systemLogs = ref([])
const auditLogs = ref([])
const codeHistory = ref([])

const API_BASE = '/api/v1/logs'

const fetchSystemLogs = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/system/`)
    if (res.ok) systemLogs.value = await res.json()
  } finally {
    loading.value = false
  }
}

const fetchAuditLogs = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/audit/`)
    if (res.ok) auditLogs.value = await res.json()
  } finally {
    loading.value = false
  }
}

const fetchCodeHistory = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/code-history/`)
    if (res.ok) codeHistory.value = await res.json()
  } finally {
    loading.value = false
  }
}

const loadData = () => {
  if (tab.value === 'system') fetchSystemLogs()
  if (tab.value === 'audit') fetchAuditLogs()
  if (tab.value === 'code') fetchCodeHistory()
}

onMounted(loadData)

const formatDate = (dateStr) => {
  return formatDateTime(dateStr)
}

const formatGitDate = (timestamp) => {
  return formatDateTime(new Date(timestamp * 1000))
}

const getLevelColor = (level) => {
  const map = {
    CRITICAL: 'error',
    ERROR: 'warning',
    WARNING: 'info',
    INFO: 'success'
  }
  return map[level] || 'grey'
}
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard title="Логи и история системы">
        <VTabs v-model="tab" @update:model-value="loadData">
          <VTab value="system">Ошибки и сбои</VTab>
          <VTab value="audit">История правок</VTab>
          <VTab value="code">Изменения кода</VTab>
        </VTabs>

        <VWindow v-model="tab">
          <!-- Системные логи -->
          <VWindowItem value="system">
            <VCardText>
              <VDataTable
                :items="systemLogs"
                :loading="loading"
                :headers="[
                  { title: 'Дата', key: 'created_at' },
                  { title: 'Уровень', key: 'level' },
                  { title: 'Модуль', key: 'module' },
                  { title: 'Сообщение', key: 'message' },
                  { title: 'Детали', key: 'actions', sortable: false }
                ]"
              >
                <template #item.created_at="{ item }">
                  {{ formatDate(item.created_at) }}
                </template>
                <template #item.level="{ item }">
                  <VChip :color="getLevelColor(item.level)" size="small">
                    {{ item.level }}
                  </VChip>
                </template>
                <template #item.actions="{ item }">
                  <VDialog max-width="800">
                    <template #activator="{ props }">
                      <VBtn v-bind="props" size="x-small" variant="text">Подробнее</VBtn>
                    </template>
                    <VCard title="Детали ошибки">
                      <VCardText>
                        <div class="mb-4"><strong>Сообщение:</strong> {{ item.message }}</div>
                        <div v-if="item.stack_trace">
                          <strong>Stack Trace:</strong>
                          <pre class="bg-grey-lighten-4 p-4 mt-2 rounded overflow-auto" style="max-height: 400px; font-size: 12px;">{{ item.stack_trace }}</pre>
                        </div>
                      </VCardText>
                    </VCard>
                  </VDialog>
                </template>
              </VDataTable>
            </VCardText>
          </VWindowItem>

          <!-- Логи аудита -->
          <VWindowItem value="audit">
            <VCardText>
              <VDataTable
                :items="auditLogs"
                :loading="loading"
                :headers="[
                  { title: 'Дата', key: 'created_at' },
                  { title: 'Действие', key: 'action' },
                  { title: 'Ресурс', key: 'resource_type' },
                  { title: 'ID', key: 'resource_id' },
                  { title: 'Описание', key: 'message' }
                ]"
              >
                <template #item.created_at="{ item }">
                  {{ formatDate(item.created_at) }}
                </template>
                <template #item.action="{ item }">
                  <VChip :color="item.action === 'UPDATE' ? 'info' : 'success'" size="small">
                    {{ item.action }}
                  </VChip>
                </template>
              </VDataTable>
            </VCardText>
          </VWindowItem>

          <!-- История кода -->
          <VWindowItem value="code">
            <VCardText>
              <VDataTable
                :items="codeHistory"
                :loading="loading"
                :headers="[
                  { title: 'Дата', key: 'date' },
                  { title: 'Хеш', key: 'hash' },
                  { title: 'Автор', key: 'author' },
                  { title: 'Сообщение', key: 'message' }
                ]"
              >
                <template #item.date="{ item }">
                  {{ formatGitDate(item.date) }}
                </template>
                <template #item.hash="{ item }">
                  <code>{{ item.hash }}</code>
                </template>
              </VDataTable>
            </VCardText>
          </VWindowItem>
        </VWindow>
      </VCard>
    </VCol>
  </VRow>
</template>
