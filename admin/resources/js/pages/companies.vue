<script setup>
import { ref, onMounted } from "vue"
import { formatDateTime } from "@/utils/date"

// =========================================================================
// Состояние
// =========================================================================

const loading = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

// Мои компании (Отчетность)
const organizations = ref([])
const selectedOrgForReport = ref(null)
const reportData = ref(null)
const loadingReport = ref(false)
const reportDateFrom = ref(new Date().toISOString().split('T')[0])
const reportDateTo = ref(new Date().toISOString().split('T')[0])
const topTab = ref('qty')

const API_BASE = "/api/v1/iiko"

// =========================================================================
// Методы
// =========================================================================

const loadOrganizations = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/organizations`)
    if (res.ok) {
      organizations.value = await res.json()
    }
  } catch (e) {
    showMessage("Ошибка при загрузке организаций", "error")
  } finally {
    loading.value = false
  }
}

const fetchOrganizationReport = async () => {
  if (!selectedOrgForReport.value) {
    showMessage("Выберите организацию", "warning")
    return
  }
  loadingReport.value = true
  reportData.value = null
  try {
    const from = `${reportDateFrom.value} 00:00:00.000`
    const to = `${reportDateTo.value} 23:59:59.999`
    const res = await fetch(`${API_BASE}/companies/report?organization_id=${selectedOrgForReport.value}&date_from=${from}&date_to=${to}`)
    const data = await res.json()
    if (res.ok) {
      reportData.value = data
      showMessage("Отчет сформирован")
    } else {
      showMessage(data.detail || "Ошибка при формировании отчета", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети при получении отчета", "error")
  } finally {
    loadingReport.value = false
  }
}

onMounted(() => {
  loadOrganizations()
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard class="mb-6">
        <VCardTitle>Панель управления организацией</VCardTitle>
        <VCardText>
          <VRow align="center">
            <VCol cols="12" md="4">
              <VSelect
                v-model="selectedOrgForReport"
                :items="organizations"
                item-title="name"
                item-value="id"
                label="Выберите организацию"
                density="compact"
                hide-details
                :loading="loading"
              />
            </VCol>
            <VCol cols="12" md="3">
              <VTextField
                v-model="reportDateFrom"
                type="date"
                label="От"
                density="compact"
                hide-details
              />
            </VCol>
            <VCol cols="12" md="3">
              <VTextField
                v-model="reportDateTo"
                type="date"
                label="До"
                density="compact"
                hide-details
              />
            </VCol>
            <VCol cols="12" md="2">
              <VBtn 
                block 
                color="primary" 
                :loading="loadingReport"
                @click="fetchOrganizationReport"
              >
                Сформировать
              </VBtn>
            </VCol>
          </VRow>
        </VCardText>
      </VCard>

      <template v-if="reportData">
        <!-- KPI Карточки -->
        <VRow class="mb-6">
          <VCol cols="12" md="2">
            <VCard color="deep-purple" theme="dark">
              <VCardText class="text-center">
                <div class="text-h6 font-weight-bold">{{ reportData.kpi.revenueTotal || 0 }} ₽</div>
                <div class="text-caption">Выручка (OLAP)</div>
              </VCardText>
            </VCard>
          </VCol>
          <VCol cols="12" md="2">
            <VCard color="primary" theme="dark">
              <VCardText class="text-center">
                <div class="text-h6 font-weight-bold">{{ reportData.kpi.ordersTotal || 0 }}</div>
                <div class="text-caption">Всего заказов</div>
              </VCardText>
            </VCard>
          </VCol>
          <VCol cols="12" md="2">
            <VCard color="teal" theme="dark">
              <VCardText class="text-center">
                <div class="text-h6 font-weight-bold">{{ reportData.kpi.avgCheck || 0 }} ₽</div>
                <div class="text-caption">Средний чек</div>
              </VCardText>
            </VCard>
          </VCol>
          <VCol cols="12" md="2">
            <VCard color="success" theme="dark">
              <VCardText class="text-center">
                <div class="text-h6 font-weight-bold">{{ reportData.kpi.kitchenAvgMin || 0 }} мин</div>
                <div class="text-caption">Средняя кухня</div>
              </VCardText>
            </VCard>
          </VCol>
          <VCol cols="12" md="2">
            <VCard color="info" theme="dark">
              <VCardText class="text-center">
                <div class="text-h6 font-weight-bold">{{ reportData.kpi.travelAvgMin || 0 }} мин</div>
                <div class="text-caption">Средняя доставка</div>
              </VCardText>
            </VCard>
          </VCol>
          <VCol cols="12" md="2">
            <VCard color="warning" theme="dark">
              <VCardText class="text-center">
                <div class="text-h6 font-weight-bold">{{ reportData.kpi.couriersTotal || 0 }}</div>
                <div class="text-caption">Всего сотрудников</div>
              </VCardText>
            </VCard>
          </VCol>
        </VRow>

        <VRow>
          <!-- Терминалы -->
          <VCol cols="12" md="6">
            <VCard title="Статус терминалов" class="fill-height">
              <VTable density="compact">
                <thead>
                  <tr>
                    <th>Название</th>
                    <th>Таймзона</th>
                    <th>Статус</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="t in reportData.terminals.flatList" :key="t.id">
                    <td>{{ t.name }}</td>
                    <td><code class="text-caption">{{ t.timeZone }}</code></td>
                    <td>
                      <VChip 
                        :color="t.isAlive ? 'success' : 'error'" 
                        size="x-small"
                      >
                        {{ t.isAlive ? 'В сети' : 'Оффлайн' }}
                      </VChip>
                    </td>
                  </tr>
                </tbody>
              </VTable>
            </VCard>
          </VCol>

          <!-- Топ товаров -->
          <VCol cols="12" md="6">
            <VCard title="Популярные товары" class="fill-height">
              <VTabs v-model="topTab" density="compact">
                <VTab value="qty">По количеству</VTab>
                <VTab value="sum">По сумме</VTab>
              </VTabs>
              <VCardText>
                <VWindow v-model="topTab">
                  <VWindowItem value="qty">
                    <VList density="compact">
                      <VListItem 
                        v-for="item in reportData.analytics.topItems.byQty" 
                        :key="item.name"
                      >
                        <template #prepend>
                          <VIcon icon="bx-package" size="small" class="me-2" />
                        </template>
                        <VListItemTitle>{{ item.name }}</VListItemTitle>
                        <template #append>
                          <span class="font-weight-bold text-primary">{{ item.value }} шт.</span>
                        </template>
                      </VListItem>
                    </VList>
                  </VWindowItem>
                  <VWindowItem value="sum">
                    <VList density="compact">
                      <VListItem 
                        v-for="item in reportData.analytics.topItems.bySum" 
                        :key="item.name"
                      >
                        <template #prepend>
                          <VIcon icon="bx-money" size="small" class="me-2" />
                        </template>
                        <VListItemTitle>{{ item.name }}</VListItemTitle>
                        <template #append>
                          <span class="font-weight-bold text-success">{{ item.value }} ₽</span>
                        </template>
                      </VListItem>
                    </VList>
                  </VWindowItem>
                </VWindow>
              </VCardText>
            </VCard>
          </VCol>

          <!-- Последние заказы -->
          <VCol cols="12">
            <VCard title="Последние заказы">
              <VTable density="compact">
                <thead>
                  <tr>
                    <th>Время</th>
                    <th>№</th>
                    <th>Клиент</th>
                    <th>Статус</th>
                    <th>Сумма</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="order in reportData.analytics.ordersShort" :key="order.id">
                    <td class="text-caption">{{ formatDateTime(order.whenCreated) }}</td>
                    <td class="font-weight-bold">{{ order.number }}</td>
                    <td>{{ order.customer }}</td>
                    <td>
                      <VChip size="x-small" label variant="tonal" color="primary">{{ order.status }}</VChip>
                    </td>
                    <td class="text-right">{{ order.sum }} ₽</td>
                  </tr>
                </tbody>
              </VTable>
            </VCard>
          </VCol>
        </VRow>
      </template>

      <VCard v-else-if="!loadingReport" class="text-center py-12" variant="tonal">
        <VIcon icon="mdi-chart-line" size="64" color="grey-lighten-1" class="mb-4" />
        <div class="text-h6 text-grey">Выберите организацию и нажмите "Сформировать"</div>
      </VCard>
    </VCol>
  </VRow>

  <VSnackbar v-model="snackbar" :color="snackbarColor" :timeout="3000">
    {{ snackbarText }}
  </VSnackbar>
</template>

<style scoped>
.gap-4 { gap: 16px; }
.gap-2 { gap: 8px; }
</style>
