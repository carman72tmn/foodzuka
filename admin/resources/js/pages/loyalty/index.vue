<script setup>
import { ref, onMounted } from "vue"
import { formatDateTime } from "@/utils/date"

const activeTab = ref("statuses")

// ==================== Статусы ====================
const statuses = ref([])
const loadingStatuses = ref(false)
const statusDialog = ref(false)
const editingStatus = ref(null)

const statusForm = ref({
  name: "",
  max_discount: 0,
  min_status_points: 0,
  sort_order: 0,
  is_active: true,
})

const statusHeaders = [
  { title: "ID", key: "id", width: 60 },
  { title: "Название", key: "name" },
  { title: "Макс. скидка %", key: "max_discount", width: 140 },
  { title: "Мин. статусных баллов", key: "min_status_points", width: 180 },
  { title: "Порядок", key: "sort_order", width: 100 },
  { title: "Активен", key: "is_active", width: 100 },
  { title: "Действия", key: "actions", width: 120, sortable: false },
]

// ==================== Правила ====================
const rules = ref([])
const loadingRules = ref(false)
const ruleDialog = ref(false)
const editingRule = ref(null)

const ruleForm = ref({
  title: "",
  loyalty_status_id: null,
  rule_type: "cashback",
  cashback_percent: 0,
  bonus_ttl_days: 0,
  status_ttl_days: 0,
  is_active: true,
})

const ruleHeaders = [
  { title: "ID", key: "id", width: 60 },
  { title: "Заголовок", key: "title" },
  { title: "Статус", key: "loyalty_status_id", width: 130 },
  { title: "Кэшбек %", key: "cashback_percent", width: 110 },
  { title: "Бонусы (дни)", key: "bonus_ttl_days", width: 120 },
  { title: "Статус (дни)", key: "status_ttl_days", width: 120 },
  { title: "Действия", key: "actions", width: 120, sortable: false },
]

const ruleTypes = [
  { title: "Кэшбек", value: "cashback" },
  { title: "Приветственный бонус", value: "welcome" },
  { title: "День рождения", value: "birthday" },
]

// ==================== Транзакции ====================
const transactions = ref([])
const loadingTx = ref(false)
const txDialog = ref(false)

const txForm = ref({
  transaction_type: "credit",
  phone: "",
  points: 0,
  ttl_days: 0,
  comment: "",
})

const balancePhone = ref("")
const balanceResult = ref(null)

const txHeaders = [
  { title: "ID", key: "id", width: 60 },
  { title: "Тип", key: "transaction_type", width: 100 },
  { title: "Телефон", key: "phone", width: 140 },
  { title: "Баллов", key: "points", width: 100 },
  { title: "Срок (дни)", key: "ttl_days", width: 100 },
  { title: "Комментарий", key: "comment" },
  { title: "Дата", key: "created_at", width: 160 },
]

// ==================== Snackbar ====================
const snackbar = ref(false)
const snackbarText = ref("")
const snackbarColor = ref("success")

const showMsg = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const API = "/api/v1/loyalty"

// ==================== Статусы API ====================
const loadStatuses = async () => {
  loadingStatuses.value = true
  try {
    const res = await fetch(`${API}/statuses`)
    if (res.ok) statuses.value = await res.json()
  } finally {
    loadingStatuses.value = false
  }
}

const openStatusDialog = (item = null) => {
  editingStatus.value = item
  if (item) {
    Object.assign(statusForm.value, item)
  } else {
    statusForm.value = {
      name: "",
      max_discount: 0,
      min_status_points: 0,
      sort_order: 0,
      is_active: true,
    }
  }
  statusDialog.value = true
}

const saveStatus = async () => {
  const method = editingStatus.value ? "PUT" : "POST"

  const url = editingStatus.value
    ? `${API}/statuses/${editingStatus.value.id}`
    : `${API}/statuses`

  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(statusForm.value),
  })

  if (res.ok) {
    showMsg(editingStatus.value ? "Статус обновлён" : "Статус создан")
    statusDialog.value = false
    await loadStatuses()
  } else {
    showMsg("Ошибка сохранения", "error")
  }
}

const deleteStatus = async id => {
  if (!confirm("Удалить статус?")) return
  await fetch(`${API}/statuses/${id}`, { method: "DELETE" })
  showMsg("Статус удалён")
  await loadStatuses()
}

// ==================== Правила API ====================
const loadRules = async () => {
  loadingRules.value = true
  try {
    const res = await fetch(`${API}/rules`)
    if (res.ok) rules.value = await res.json()
  } finally {
    loadingRules.value = false
  }
}

const openRuleDialog = (item = null) => {
  editingRule.value = item
  if (item) {
    Object.assign(ruleForm.value, item)
  } else {
    ruleForm.value = {
      title: "",
      loyalty_status_id: null,
      rule_type: "cashback",
      cashback_percent: 0,
      bonus_ttl_days: 0,
      status_ttl_days: 0,
      is_active: true,
    }
  }
  ruleDialog.value = true
}

const saveRule = async () => {
  const method = editingRule.value ? "PUT" : "POST"

  const url = editingRule.value
    ? `${API}/rules/${editingRule.value.id}`
    : `${API}/rules`

  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(ruleForm.value),
  })

  if (res.ok) {
    showMsg(editingRule.value ? "Правило обновлено" : "Правило создано")
    ruleDialog.value = false
    await loadRules()
  } else {
    showMsg("Ошибка сохранения", "error")
  }
}

const deleteRule = async id => {
  if (!confirm("Удалить правило?")) return
  await fetch(`${API}/rules/${id}`, { method: "DELETE" })
  showMsg("Правило удалено")
  await loadRules()
}

// ==================== Транзакции API ====================
const loadTransactions = async () => {
  loadingTx.value = true
  try {
    let url = `${API}/transactions`
    if (balancePhone.value)
      url += `?phone=${encodeURIComponent(balancePhone.value)}`
    const res = await fetch(url)
    if (res.ok) transactions.value = await res.json()
  } finally {
    loadingTx.value = false
  }
}

const createTransaction = async () => {
  const res = await fetch(`${API}/transactions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(txForm.value),
  })

  if (res.ok) {
    showMsg("Транзакция создана")
    txDialog.value = false
    await loadTransactions()
  } else {
    showMsg("Ошибка создания", "error")
  }
}

const checkBalance = async () => {
  if (!balancePhone.value) return

  const res = await fetch(
    `${API}/balance/${encodeURIComponent(balancePhone.value)}`,
  )

  if (res.ok) {
    balanceResult.value = await res.json()
  }
}

const getStatusName = id => {
  const s = statuses.value.find(s => s.id === id)
  
  return s ? s.name : `#${id}`
}

const formatDate = d => formatDateTime(d)

// ==================== Инициализация ====================
onMounted(async () => {
  await loadStatuses()
  await loadRules()
  await loadTransactions()
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard>
        <VCardTitle class="d-flex align-center">
          <VIcon
            icon="mdi-star"
            class="me-2"
          />
          Программа лояльности
        </VCardTitle>
        <VCardText>
          <VTabs
            v-model="activeTab"
            color="primary"
          >
            <VTab value="statuses">
              Статусы
            </VTab>
            <VTab value="rules">
              Правила
            </VTab>
            <VTab value="transactions">
              Транзакции
            </VTab>
          </VTabs>

          <VWindow
            v-model="activeTab"
            class="mt-4"
          >
            <!-- ==================== Статусы ==================== -->
            <VWindowItem value="statuses">
              <div class="d-flex justify-end mb-3">
                <VBtn
                  color="primary"
                  prepend-icon="mdi-plus"
                  @click="openStatusDialog"
                >
                  Добавить статус
                </VBtn>
              </div>
              <VDataTable
                :headers="statusHeaders"
                :items="statuses"
                :loading="loadingStatuses"
                density="compact"
                class="elevation-1"
              >
                <template #item.is_active="{ item }">
                  <VChip
                    :color="item.is_active ? 'success' : 'grey'"
                    size="small"
                    variant="tonal"
                  >
                    {{ item.is_active ? "Да" : "Нет" }}
                  </VChip>
                </template>
                <template #item.actions="{ item }">
                  <VBtn
                    icon="mdi-pencil"
                    size="small"
                    variant="text"
                    @click="openStatusDialog(item)"
                  />
                  <VBtn
                    icon="mdi-delete"
                    size="small"
                    variant="text"
                    color="error"
                    @click="deleteStatus(item.id)"
                  />
                </template>
              </VDataTable>
            </VWindowItem>

            <!-- ==================== Правила ==================== -->
            <VWindowItem value="rules">
              <div class="d-flex justify-end mb-3">
                <VBtn
                  color="primary"
                  prepend-icon="mdi-plus"
                  @click="openRuleDialog"
                >
                  Добавить правило
                </VBtn>
              </div>
              <VDataTable
                :headers="ruleHeaders"
                :items="rules"
                :loading="loadingRules"
                density="compact"
                class="elevation-1"
              >
                <template #item.loyalty_status_id="{ item }">
                  <VChip
                    size="small"
                    variant="tonal"
                    color="primary"
                  >
                    {{ getStatusName(item.loyalty_status_id) }}
                  </VChip>
                </template>
                <template #item.actions="{ item }">
                  <VBtn
                    icon="mdi-pencil"
                    size="small"
                    variant="text"
                    @click="openRuleDialog(item)"
                  />
                  <VBtn
                    icon="mdi-delete"
                    size="small"
                    variant="text"
                    color="error"
                    @click="deleteRule(item.id)"
                  />
                </template>
              </VDataTable>
            </VWindowItem>

            <!-- ==================== Транзакции ==================== -->
            <VWindowItem value="transactions">
              <VRow class="mb-4">
                <VCol
                  cols="12"
                  md="4"
                >
                  <VTextField
                    v-model="balancePhone"
                    label="Телефон клиента"
                    prepend-inner-icon="mdi-phone"
                    density="compact"
                    clearable
                    @keyup.enter="checkBalance"
                  />
                </VCol>
                <VCol
                  cols="auto"
                  class="d-flex gap-2"
                >
                  <VBtn
                    color="info"
                    variant="outlined"
                    prepend-icon="mdi-magnify"
                    @click="checkBalance"
                  >
                    Баланс
                  </VBtn>
                  <VBtn
                    color="secondary"
                    variant="outlined"
                    prepend-icon="mdi-filter"
                    @click="loadTransactions"
                  >
                    Фильтровать
                  </VBtn>
                  <VBtn
                    color="primary"
                    prepend-icon="mdi-plus"
                    @click="txDialog = true"
                  >
                    Начислить / Списать
                  </VBtn>
                </VCol>
              </VRow>

              <VAlert
                v-if="balanceResult"
                type="info"
                variant="tonal"
                class="mb-4"
                closable
                @click:close="balanceResult = null"
              >
                <strong>{{ balanceResult.phone }}</strong>: баланс <strong>{{ balanceResult.balance }}</strong> баллов
                ({{ balanceResult.transactions_count }} транзакций)
              </VAlert>

              <VDataTable
                :headers="txHeaders"
                :items="transactions"
                :loading="loadingTx"
                density="compact"
                class="elevation-1"
                :items-per-page="25"
              >
                <template #item.transaction_type="{ item }">
                  <VChip
                    :color="
                      item.transaction_type === 'credit' ? 'success' : 'error'
                    "
                    size="small"
                    variant="tonal"
                  >
                    {{
                      item.transaction_type === "credit"
                        ? "Зачисление"
                        : "Списание"
                    }}
                  </VChip>
                </template>
                <template #item.created_at="{ item }">
                  {{ formatDate(item.created_at) }}
                </template>
              </VDataTable>
            </VWindowItem>
          </VWindow>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <!-- ==================== Диалог Статуса ==================== -->
  <VDialog
    v-model="statusDialog"
    max-width="500"
  >
    <VCard :title="editingStatus ? 'Редактировать статус' : 'Новый статус'">
      <VCardText>
        <VTextField
          v-model="statusForm.name"
          label="Название"
          class="mb-3"
        />
        <VSlider
          v-model="statusForm.max_discount"
          label="Макс. скидка %"
          :min="0"
          :max="100"
          :step="1"
          thumb-label="always"
          class="mb-3"
        />
        <VTextField
          v-model.number="statusForm.min_status_points"
          label="Мин. статусных баллов"
          type="number"
          class="mb-3"
        />
        <VTextField
          v-model.number="statusForm.sort_order"
          label="Порядок сортировки"
          type="number"
          class="mb-3"
        />
        <VSwitch
          v-model="statusForm.is_active"
          label="Активен"
          color="primary"
        />
      </VCardText>
      <VCardActions>
        <VSpacer />
        <VBtn
          variant="text"
          @click="statusDialog = false"
        >
          Отмена
        </VBtn>
        <VBtn
          color="primary"
          @click="saveStatus"
        >
          Сохранить
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- ==================== Диалог Правила ==================== -->
  <VDialog
    v-model="ruleDialog"
    max-width="500"
  >
    <VCard :title="editingRule ? 'Редактировать правило' : 'Новое правило'">
      <VCardText>
        <VTextField
          v-model="ruleForm.title"
          label="Заголовок"
          class="mb-3"
        />
        <VSelect
          v-model="ruleForm.loyalty_status_id"
          :items="statuses.map((s) => ({ title: s.name, value: s.id }))"
          label="Для статуса"
          class="mb-3"
        />
        <VSelect
          v-model="ruleForm.rule_type"
          :items="ruleTypes"
          label="Тип правила"
          class="mb-3"
        />
        <VSlider
          v-model="ruleForm.cashback_percent"
          label="Кэшбек %"
          :min="0"
          :max="50"
          :step="0.5"
          thumb-label="always"
          class="mb-3"
        />
        <VTextField
          v-model.number="ruleForm.bonus_ttl_days"
          label="Срок жизни бонусов (дни, 0 = бессрочно)"
          type="number"
          class="mb-3"
        />
        <VTextField
          v-model.number="ruleForm.status_ttl_days"
          label="Срок жизни статусных баллов (дни)"
          type="number"
          class="mb-3"
        />
        <VSwitch
          v-model="ruleForm.is_active"
          label="Активно"
          color="primary"
        />
      </VCardText>
      <VCardActions>
        <VSpacer />
        <VBtn
          variant="text"
          @click="ruleDialog = false"
        >
          Отмена
        </VBtn>
        <VBtn
          color="primary"
          @click="saveRule"
        >
          Сохранить
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- ==================== Диалог Транзакции ==================== -->
  <VDialog
    v-model="txDialog"
    max-width="500"
  >
    <VCard title="Новая транзакция">
      <VCardText>
        <VBtnToggle
          v-model="txForm.transaction_type"
          mandatory
          color="primary"
          class="mb-4"
        >
          <VBtn value="credit">
            Зачисление
          </VBtn>
          <VBtn value="debit">
            Списание
          </VBtn>
        </VBtnToggle>
        <VTextField
          v-model="txForm.phone"
          label="Телефон клиента"
          prepend-inner-icon="mdi-phone"
          class="mb-3"
        />
        <VTextField
          v-model.number="txForm.points"
          label="Количество баллов"
          type="number"
          class="mb-3"
        />
        <VTextField
          v-model.number="txForm.ttl_days"
          label="Срок жизни (дни, 0 = бессрочно)"
          type="number"
          class="mb-3"
        />
        <VTextarea
          v-model="txForm.comment"
          label="Комментарий"
          rows="2"
        />
      </VCardText>
      <VCardActions>
        <VSpacer />
        <VBtn
          variant="text"
          @click="txDialog = false"
        >
          Отмена
        </VBtn>
        <VBtn
          color="primary"
          @click="createTransaction"
        >
          Создать
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- Snackbar -->
  <VSnackbar
    v-model="snackbar"
    :color="snackbarColor"
    :timeout="3000"
    location="top"
  >
    {{ snackbarText }}
  </VSnackbar>
</template>
