<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const toast = useToast()
const cascades = ref([])
const isLoading = ref(false)
const isDialogOpen = ref(false)
const isStepDialogOpen = ref(false)

const currentCascade = ref({
  name: '',
  trigger_event: 'new_order',
  is_active: true,
  steps: []
})

const triggerEvents = [
  { title: 'Новый заказ', value: 'new_order' },
  { title: 'Заказ подтвержден', value: 'order_confirmed' },
  { title: 'Заказ готовится', value: 'order_cooking' },
  { title: 'Заказ готов', value: 'order_ready' },
  { title: 'Заказ в пути', value: 'order_delivering' },
  { title: 'Заказ доставлен', value: 'order_delivered' },
  { title: 'Заказ отменен', value: 'order_cancelled' },
]

const channels = [
  { title: 'VK', value: 'vk' },
  { title: 'MAX Messenger', value: 'max' },
  { title: 'Telegram', value: 'telegram' },
]

const conditions = [
  { title: 'Всегда', value: 'always' },
  { title: 'Если предыдущий не доставлен', value: 'if_previous_failed' },
]

const variables = [
  { name: '{order_number}', desc: 'Номер заказа' },
  { name: '{customer_name}', desc: 'Имя клиента' },
  { name: '{total_sum}', desc: 'Сумма заказа' },
  { name: '{items}', desc: 'Список товаров' },
  { name: '{address}', desc: 'Адрес доставки' },
  { name: '{status}', desc: 'Статус заказа' },
]

const fetchCascades = async () => {
  isLoading.ref = true
  try {
    const response = await axios.get('/api/v1/mailings/cascades')
    cascades.value = response.data
  } catch (error) {
    toast.error('Ошибка при загрузке каскадов')
  } finally {
    isLoading.value = false
  }
}

const openCreateDialog = () => {
  currentCascade.value = {
    name: '',
    trigger_event: 'new_order',
    is_active: true,
    steps: []
  }
  isDialogOpen.value = true
}

const editCascade = (cascade) => {
  currentCascade.value = JSON.parse(JSON.stringify(cascade))
  isDialogOpen.value = true
}

const addStep = () => {
  currentCascade.value.steps.push({
    channel: 'vk',
    delay_minutes: 0,
    template: 'Здравствуйте, {customer_name}! Ваш заказ №{order_number} на сумму {total_sum}р принят.',
    condition: 'always',
    priority: currentCascade.value.steps.length
  })
}

const removeStep = (index) => {
  currentCascade.value.steps.splice(index, 1)
  reorderSteps()
}

const moveStep = (index, direction) => {
  const newIndex = index + direction
  if (newIndex < 0 || newIndex >= currentCascade.value.steps.length) return
  
  const element = currentCascade.value.steps.splice(index, 1)[0]
  currentCascade.value.steps.splice(newIndex, 0, element)
  reorderSteps()
}

const reorderSteps = () => {
  currentCascade.value.steps.forEach((step, index) => {
    step.priority = index
  })
}

const saveCascade = async () => {
  try {
    if (currentCascade.value.id) {
      await axios.put(`/api/v1/mailings/cascades/${currentCascade.value.id}`, currentCascade.value)
      toast.success('Каскад обновлен')
    } else {
      await axios.post('/api/v1/mailings/cascades', currentCascade.value)
      toast.success('Каскад создан')
    }
    isDialogOpen.value = false
    fetchCascades()
  } catch (error) {
    toast.error('Ошибка при сохранении')
  }
}

const deleteCascade = async (id) => {
  if (!confirm('Вы уверены, что хотите удалить этот каскад?')) return
  try {
    await axios.delete(`/api/v1/mailings/cascades/${id}`)
    toast.success('Каскад удален')
    fetchCascades()
  } catch (error) {
    toast.error('Ошибка при удалении')
  }
}

const insertVariable = (stepIndex, variable) => {
  currentCascade.value.steps[stepIndex].template += variable
}

onMounted(fetchCascades)
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard title="Каскадные рассылки">
        <VCardText>
          Настройте цепочки уведомлений для различных событий. Система будет пытаться отправить сообщение по очереди согласно приоритетам и задержкам.
        </VCardText>
        
        <VCardText>
          <VBtn color="primary" @click="openCreateDialog">
            <VIcon start icon="bx-plus" />
            Создать каскад
          </VBtn>
        </VCardText>

        <VTable>
          <thead>
            <tr>
              <th>Название</th>
              <th>Событие-триггер</th>
              <th>Шагов</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cascade in cascades" :key="cascade.id">
              <td>{{ cascade.name }}</td>
              <td>
                <VChip size="small" color="info">
                  {{ triggerEvents.find(e => e.value === cascade.trigger_event)?.title || cascade.trigger_event }}
                </VChip>
              </td>
              <td>{{ cascade.steps?.length || 0 }}</td>
              <td>
                <VSwitch 
                  v-model="cascade.is_active" 
                  density="compact" 
                  readonly
                  color="success"
                  hide-details
                />
              </td>
              <td>
                <VBtn icon variant="text" size="small" @click="editCascade(cascade)">
                  <VIcon icon="bx-edit" />
                </VBtn>
                <VBtn icon variant="text" size="small" color="error" @click="deleteCascade(cascade.id)">
                  <VIcon icon="bx-trash" />
                </VBtn>
              </td>
            </tr>
            <tr v-if="cascades.length === 0">
              <td colspan="5" class="text-center py-4 text-muted">
                Каскады не настроены
              </td>
            </tr>
          </tbody>
        </VTable>
      </VCard>
    </VCol>

    <!-- Dialog for Create/Edit -->
    <VDialog v-model="isDialogOpen" max-width="900px">
      <VCard :title="currentCascade.id ? 'Редактирование каскада' : 'Новый каскад'">
        <VCardText>
          <VRow>
            <VCol cols="12" md="6">
              <VTextField v-model="currentCascade.name" label="Название каскада" placeholder="Напр: Основное уведомление о заказе" />
            </VCol>
            <VCol cols="12" md="4">
              <VSelect 
                v-model="currentCascade.trigger_event" 
                :items="triggerEvents" 
                label="Событие-триггер" 
              />
            </VCol>
            <VCol cols="12" md="2" class="d-flex align-center">
              <VSwitch v-model="currentCascade.is_active" label="Активен" color="success" />
            </VCol>
          </VRow>

          <div class="mt-6">
            <div class="d-flex align-center justify-space-between mb-4">
              <h3 class="text-h6">Шаги каскада</h3>
              <VBtn size="small" color="secondary" variant="outlined" @click="addStep">
                <VIcon start icon="bx-plus" /> Добавить шаг
              </VBtn>
            </div>

            <div v-if="currentCascade.steps.length === 0" class="text-center py-8 border-dashed rounded">
              Добавьте первый шаг для настройки каскада
            </div>

            <VCard v-for="(step, index) in currentCascade.steps" :key="index" variant="outlined" class="mb-4">
              <VCardText>
                <div class="d-flex align-center mb-4">
                  <div class="me-4 text-h5 text-primary font-weight-bold">#{{ index + 1 }}</div>
                  <VSelect 
                    v-model="step.channel" 
                    :items="channels" 
                    label="Канал" 
                    density="compact"
                    class="me-2"
                    hide-details
                  />
                  <VTextField 
                    v-model.number="step.delay_minutes" 
                    type="number" 
                    label="Задержка (мин)" 
                    density="compact"
                    style="max-width: 120px"
                    class="me-2"
                    hide-details
                  />
                  <VSpacer />
                  <VBtn icon variant="text" size="small" @click="moveStep(index, -1)" :disabled="index === 0">
                    <VIcon icon="bx-up-arrow-alt" />
                  </VBtn>
                  <VBtn icon variant="text" size="small" @click="moveStep(index, 1)" :disabled="index === currentCascade.steps.length - 1">
                    <VIcon icon="bx-down-arrow-alt" />
                  </VBtn>
                  <VBtn icon variant="text" size="small" color="error" @click="removeStep(index)">
                    <VIcon icon="bx-x" />
                  </VBtn>
                </div>

                <VTextarea 
                  v-model="step.template" 
                  label="Шаблон сообщения" 
                  rows="3"
                  hint="Поддерживаются переменные: {order_number}, {customer_name} и др."
                  persistent-hint
                />
                
                <div class="d-flex flex-wrap gap-2 mt-2">
                  <VBtn 
                    v-for="v in variables" 
                    :key="v.name" 
                    size="x-small" 
                    variant="tonal"
                    @click="insertVariable(index, v.name)"
                    :title="v.desc"
                  >
                    {{ v.name }}
                  </VBtn>
                </div>

                <VSelect 
                  v-model="step.condition" 
                  :items="conditions" 
                  label="Условие отправки" 
                  class="mt-4"
                  density="compact"
                />
              </VCardText>
            </VCard>
          </div>
        </VCardText>

        <VCardActions>
          <VSpacer />
          <VBtn color="secondary" variant="text" @click="isDialogOpen = false">Отмена</VBtn>
          <VBtn color="primary" @click="saveCascade">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </VRow>
</template>

<style scoped>
.border-dashed {
  border: 2px dashed rgba(var(--v-border-color), var(--v-border-opacity));
}
.gap-2 {
  gap: 8px;
}
</style>
