<script setup>
import { ref, onMounted, computed } from "vue"

const loading = ref(false)
const products = ref([])
const allModifiersList = ref([])
const activeTab = ref('sizes')
const search = ref("")

const API_BASE = "/api/v1"

// Диалог подробностей группы
const groupDialog = ref(false)
const selectedGroup = ref(null)

const loadData = async () => {
  loading.value = true
  try {
    const [pRes, mRes] = await Promise.all([
      fetch(`${API_BASE}/products/?limit=1000`),
      fetch(`${API_BASE}/products/modifiers/all`)
    ])
    
    if (pRes.ok) products.value = await pRes.json()
    if (mRes.ok) allModifiersList.value = await mRes.json()
  } catch (e) {
    console.error("Ошибка загрузки данных", e)
  } finally {
    loading.value = false
  }
}

// Плоские списки для таблиц
const allSizes = computed(() => {
  const sizes = []
  products.value.forEach(p => {
    if (p.sizes && p.sizes.length > 0) {
      p.sizes.forEach(s => sizes.push({ ...s, product_name: p.name }))
    }
  })
  return sizes
})

const allModifierGroups = computed(() => {
  const groups = []
  products.value.forEach(p => {
    if (p.modifier_groups && p.modifier_groups.length > 0) {
      p.modifier_groups.forEach(mg => groups.push({ ...mg, product_name: p.name }))
    }
  })
  return groups
})

const openGroupDetails = (group) => {
  selectedGroup.value = group
  groupDialog.value = true
}

const formatPrice = (value) => {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(value)
}

const deleteAllModifiers = async () => {
  if (!confirm("Вы уверены, что хотите удалить все модификаторы и размеры?")) return
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/products/modifiers/all`, { method: 'DELETE' })
    if (res.ok) {
        loadData()
    }
  } catch (e) {
    console.error("Ошибка удаления", e)
  } finally {
    loading.value = false
  }
}

const forceSyncMenu = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/iiko/sync-menu`, { method: 'POST' })
    if (res.ok) {
        setTimeout(loadData, 2000)
    }
  } catch (e) {
    console.error("Ошибка синхронизации", e)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard class="elevation-2 border">
        <VCardTitle class="d-flex align-center py-4 px-6 bg-grey-lighten-4 border-b">
          <VIcon icon="mdi-tune-vertical" color="primary" class="me-3" size="32" />
          <div class="text-h5 font-weight-bold">Опции и модификаторы</div>
          <VSpacer />
          <VTextField
            v-model="search"
            prepend-inner-icon="mdi-magnify"
            label="Поиск по названию"
            variant="solo"
            flat
            density="compact"
            hide-details
            style="max-width: 300px"
          />
          <VBtn
            color="error"
            prepend-icon="mdi-delete-sweep"
            variant="tonal"
            class="ms-3"
            :loading="loading"
            @click="deleteAllModifiers"
          >
            Удалить всё
          </VBtn>
          <VBtn
            color="primary"
            prepend-icon="mdi-sync"
            variant="elevated"
            class="ms-2"
            :loading="loading"
            @click="forceSyncMenu"
          >
            Выгрузить из iiko
          </VBtn>
        </VCardTitle>

        <VTabs v-model="activeTab" color="primary" align-tabs="start" class="border-b">
          <VTab value="sizes" prepend-icon="mdi-arrow-expand-all">Размеры ({{ allSizes.length }})</VTab>
          <VTab value="groups" prepend-icon="mdi-layers-outline">Группы ({{ allModifierGroups.length }})</VTab>
          <VTab value="all_modifiers" prepend-icon="mdi-format-list-bulleted">Все модификаторы ({{ allModifiersList.length }})</VTab>
        </VTabs>

        <VCardText class="pa-0">
          <VWindow v-model="activeTab">
            <!-- Вкладка Размеры -->
            <VWindowItem value="sizes">
              <VDataTable
                :headers="[
                  { title: 'Товар', key: 'product_name', sortable: true },
                  { title: 'Размер', key: 'name', sortable: true },
                  { title: 'Цена', key: 'price', sortable: true },
                  { title: 'Стандартный', key: 'is_default', sortable: true, width: 150 },
                  { title: 'iiko ID', key: 'iiko_id', sortable: false }
                ]"
                :items="allSizes"
                :loading="loading"
                :search="search"
                hover
              >
                <template #item.price="{ item }">
                  <span class="font-weight-bold">{{ formatPrice(item.price) }}</span>
                </template>
                <template #item.is_default="{ item }">
                  <VChip :color="item.is_default ? 'success' : 'grey-lighten-1'" size="small" variant="flat">
                    {{ item.is_default ? "Да" : "Нет" }}
                  </VChip>
                </template>
                <template #item.iiko_id="{ item }">
                  <code class="text-caption text-medium-emphasis">{{ item.iiko_id.split('-')[0] }}...</code>
                </template>
              </VDataTable>
            </VWindowItem>

            <!-- Вкладка Группы -->
            <VWindowItem value="groups">
              <VDataTable
                :headers="[
                  { title: 'Товар', key: 'product_name', sortable: true },
                  { title: 'Название группы', key: 'name', sortable: true },
                  { title: 'Обязательно', key: 'is_required', sortable: true, width: 140 },
                  { title: 'Минимум', key: 'min_amount', width: 100 },
                  { title: 'Максимум', key: 'max_amount', width: 100 },
                  { title: 'Модификаторы', key: 'modifiers', sortable: false, width: 150 }
                ]"
                :items="allModifierGroups"
                :loading="loading"
                :search="search"
                hover
              >
                <template #item.is_required="{ item }">
                  <VChip :color="item.is_required ? 'error' : 'grey'" size="small" variant="tonal" label>
                    {{ item.is_required ? "Обязательно" : "Нет" }}
                  </VChip>
                </template>
                <template #item.modifiers="{ item }">
                  <VBtn
                    size="small"
                    variant="flat"
                    color="primary"
                    @click="openGroupDetails(item)"
                    prepend-icon="mdi-eye"
                  >
                    {{ item.modifiers?.length || 0 }} шт.
                  </VBtn>
                </template>
              </VDataTable>
            </VWindowItem>

            <!-- Вкладка Все модификаторы -->
            <VWindowItem value="all_modifiers">
              <VDataTable
                :headers="[
                   { title: 'Товар', key: 'product_name', sortable: true },
                   { title: 'Группа', key: 'name', sortable: true },
                   { title: 'Модификатор', key: 'modifier_name', sortable: true },
                   { title: 'Цена', key: 'price', sortable: true },
                   { title: 'iiko ID', key: 'iiko_id', sortable: false }
                ]"
                :items="allModifiersList.flatMap(g => g.modifiers.map(m => ({
                    product_id: g.product_id,
                    product_name: g.product_name,
                    group_name: g.name,
                    modifier_name: m.name,
                    price: m.price,
                    iiko_id: m.iiko_id
                })))"
                :loading="loading"
                :search="search"
                hover
              >
                <template #item.name="{ item }">
                   <span class="text-caption text-medium-emphasis">{{ item.group_name }}</span>
                </template>
                <template #item.price="{ item }">
                   <span class="font-weight-bold">+{{ formatPrice(item.price) }}</span>
                </template>
                <template #item.iiko_id="{ item }">
                   <code class="text-caption">{{ item.iiko_id.split('-')[0] }}...</code>
                </template>
              </VDataTable>
            </VWindowItem>
          </VWindow>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <!-- Диалог подробностей группы -->
  <VDialog v-model="groupDialog" max-width="600">
    <VCard v-if="selectedGroup">
      <VCardTitle class="bg-primary text-white pa-4">
        {{ selectedGroup.name }}
        <div class="text-caption opacity-80">Товар: {{ selectedGroup.product_name }}</div>
      </VCardTitle>
      <VCardText class="pa-0">
        <VList lines="two">
          <VListItem v-for="m in selectedGroup.modifiers" :key="m.id">
            <template #prepend>
              <VAvatar color="grey-lighten-4" size="40">
                <VIcon icon="mdi-food-apple" color="primary" />
              </VAvatar>
            </template>
            <VListItemTitle class="font-weight-bold">{{ m.name }}</VListItemTitle>
            <VListItemSubtitle>ID: {{ m.iiko_id }}</VListItemSubtitle>
            <template #append>
              <VChip color="primary" variant="flat">+{{ formatPrice(m.price) }}</VChip>
            </template>
          </VListItem>
        </VList>
      </VCardText>
      <VCardActions class="pa-4">
        <VSpacer />
        <VBtn variant="text" @click="groupDialog = false">Закрыть</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>
