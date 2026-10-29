import re

file_path = "admin/resources/js/components/ai/FloatingAiAssistant.vue"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add allAssistants state and switchAssistant method
old_state = """// Состояние помощника
const isVisible = ref(false)
const isChatOpen = ref(false)
const isMinimized = ref(false)
const assistantData = ref(null)"""

new_state = """// Состояние помощника
const isVisible = ref(false)
const isChatOpen = ref(false)
const isMinimized = ref(false)
const assistantData = ref(null)
const allAssistants = ref([])

const getSkinIcon = (skin) => {
  const map = {
    chef_male: 'bx-restaurant',
    admin_female: 'bx-user-check',
    courier_male: 'bx-cycling',
    cyber_bot: 'bx-bot',
    fox_mascot: 'bx-smile',
    custom: 'bx-image'
  }
  return map[skin] || 'bx-bot'
}

const switchAssistant = (ast) => {
  if (!ast || ast.id === assistantData.value?.id) return
  assistantData.value = ast
  localStorage.setItem('preferred_assistant_id', String(ast.id))
  pollOperationalTips()
  loadChatHistory()
}

const loadAllActiveAssistants = async () => {
  try {
    const res = await axios.get('/api/v1/ai-assistants/all-active')
    if (res.data && Array.isArray(res.data)) {
      allAssistants.value = res.data
    }
  } catch (e) {
    console.debug('Failed to load active assistants', e)
  }
}"""

content = content.replace(old_state, new_state)

# 2. Update loadAssistantForCurrentPage to respect preferred_assistant_id and call loadAllActiveAssistants
old_load = """      // Загружаем сохраненную историю
      loadChatHistory()
    } else {
      isVisible.value = false
    }"""

new_load = """      await loadAllActiveAssistants()
      // Проверяем, есть ли сохраненный выбор пользователя
      const preferredId = localStorage.getItem('preferred_assistant_id')
      if (preferredId && allAssistants.value.length > 0) {
        const found = allAssistants.value.find(a => String(a.id) === String(preferredId))
        if (found) {
          assistantData.value = found
        }
      }
      // Загружаем сохраненную историю
      loadChatHistory()
    } else {
      isVisible.value = false
    }"""

content = content.replace(old_load, new_load)

# 3. In the chat header, add the interactive assistant switch dropdown & quick chips
old_header = """        <div class="assistant-header-info">
          <v-avatar size="32" color="rgba(115, 103, 240, 0.2)">
            <v-icon size="18" icon="bx-user-voice" color="primary" />
          </v-avatar>
          <div>
            <div class="assistant-header-title">{{ assistantData.name }}</div>
            <div class="assistant-header-subtitle">{{ assistantData.role_title }}</div>
          </div>
        </div>"""

new_header = """        <v-menu v-if="allAssistants.length > 1" offset-y>
          <template #activator="{ props }">
            <div class="assistant-header-info cursor-pointer d-flex align-center gap-2" v-bind="props" title="Нажмите, чтобы сменить помощника">
              <v-avatar size="32" color="rgba(115, 103, 240, 0.2)">
                <v-icon size="18" :icon="getSkinIcon(assistantData.avatar_skin)" color="primary" />
              </v-avatar>
              <div>
                <div class="assistant-header-title d-flex align-center gap-1 font-weight-bold">
                  <span>{{ assistantData.name }}</span>
                  <v-icon size="16" icon="bx-chevron-down" />
                </div>
                <div class="assistant-header-subtitle">{{ assistantData.role_title }}</div>
              </div>
            </div>
          </template>

          <v-list density="compact" class="py-1" style="min-width: 220px;">
            <v-list-subheader class="text-caption font-weight-bold">Сменить помощника:</v-list-subheader>
            <v-list-item
              v-for="ast in allAssistants"
              :key="ast.id"
              :active="ast.id === assistantData.id"
              class="cursor-pointer"
              @click="switchAssistant(ast)"
            >
              <template #prepend>
                <v-avatar size="28" :color="ast.id === assistantData.id ? 'primary' : 'secondary'" variant="tonal">
                  <v-icon size="16" :icon="getSkinIcon(ast.avatar_skin)" />
                </v-avatar>
              </template>
              <v-list-item-title class="font-weight-medium text-body-2">{{ ast.name }}</v-list-item-title>
              <v-list-item-subtitle class="text-caption text-truncate">{{ ast.role_title }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-menu>

        <div v-else class="assistant-header-info">
          <v-avatar size="32" color="rgba(115, 103, 240, 0.2)">
            <v-icon size="18" :icon="getSkinIcon(assistantData.avatar_skin)" color="primary" />
          </v-avatar>
          <div>
            <div class="assistant-header-title">{{ assistantData.name }}</div>
            <div class="assistant-header-subtitle">{{ assistantData.role_title }}</div>
          </div>
        </div>"""

content = content.replace(old_header, new_header)

# 4. Add quick selection chips under header
old_tips_start = """      <!-- Подсказки в реальном времени (если есть) -->"""
new_chips_and_tips = """      <!-- Быстрые чипы переключения между персонажами -->
      <div v-if="allAssistants.length > 1" class="px-3 py-1 d-flex gap-1 overflow-x-auto border-b" style="background: rgba(0,0,0,0.02); white-space: nowrap;">
        <v-chip
          v-for="ast in allAssistants"
          :key="ast.id"
          size="x-small"
          :color="ast.id === assistantData.id ? 'primary' : 'default'"
          :variant="ast.id === assistantData.id ? 'flat' : 'outlined'"
          class="cursor-pointer"
          @click="switchAssistant(ast)"
        >
          <v-icon start size="12" :icon="getSkinIcon(ast.avatar_skin)" />
          {{ ast.name }}
        </v-chip>
      </div>

      <!-- Подсказки в реальном времени (если есть) -->"""

content = content.replace(old_tips_start, new_chips_and_tips)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("FloatingAiAssistant.vue updated successfully!")
