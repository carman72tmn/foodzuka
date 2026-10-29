path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\admin\resources\js\pages\marketing\vk-bots.vue"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Add Diagnostics block at the top of the template
diag_template = """
    <!-- ДИАГНОСТИКА ТОКЕНОВ И ПРАВ VK API -->
    <v-card class="mb-6" elevation="2" :color="diagStatusColor" variant="tonal">
      <v-card-item>
        <div class="d-flex justify-space-between align-center">
          <div>
            <v-card-title class="d-flex align-center">
              <v-icon :icon="diagStatusIcon" class="me-2" />
              Диагностика VK.RU API и Прав Токенов
            </v-card-title>
            <v-card-subtitle>
              Автоматическая верификация токена группы и токена пользователя (wall.*, manage, messages)
            </v-card-subtitle>
          </div>
          <v-btn
            color="primary"
            variant="flat"
            prepend-icon="mdi-refresh"
            :loading="isDiagnosticsLoading"
            @click="fetchDiagnostics"
          >
            Проверить права API
          </v-btn>
        </div>
      </v-card-item>

      <v-card-text v-if="diagnosticsData">
        <v-row>
          <v-col cols="12" md="6">
            <v-card variant="outlined" class="pa-3">
              <div class="font-weight-bold mb-2">Токен Сообщества (bot_token):</div>
              <v-chip size="small" :color="diagnosticsData.group_token?.is_valid ? 'success' : 'error'" class="mb-2">
                {{ diagnosticsData.group_token?.is_valid ? 'Токен валиден' : 'Ошибка токена' }}
              </v-chip>
              <div class="text-caption">Маска прав: {{ diagnosticsData.group_token?.mask }}</div>
              <div class="d-flex flex-wrap gap-2 mt-2">
                <v-chip size="x-small" :color="diagnosticsData.group_token?.permissions?.messages ? 'success' : 'error'">messages (ЛС)</v-chip>
                <v-chip size="x-small" :color="diagnosticsData.group_token?.permissions?.photos ? 'success' : 'error'">photos (Фото)</v-chip>
                <v-chip size="x-small" :color="diagnosticsData.group_token?.permissions?.wall ? 'success' : 'error'">wall (Стена)</v-chip>
                <v-chip size="x-small" :color="diagnosticsData.group_token?.permissions?.manage ? 'success' : 'error'">manage (Управление)</v-chip>
              </div>
              <v-alert v-if="diagnosticsData.group_token?.missing_critical?.length" type="warning" density="compact" class="mt-3">
                Не хватает прав сообщества: {{ diagnosticsData.group_token?.missing_critical.join(', ') }}
              </v-alert>
            </v-card>
          </v-col>

          <v-col cols="12" md="6">
            <v-card variant="outlined" class="pa-3">
              <div class="font-weight-bold mb-2">Токен Пользователя (vk_user_token для стены/лайков):</div>
              <v-chip size="small" :color="diagnosticsData.has_working_user_token ? 'success' : 'error'" class="mb-2">
                {{ diagnosticsData.has_working_user_token ? 'Рабочий токен доступен' : 'Токен недействителен (Error 5)' }}
              </v-chip>
              <div class="text-caption">Источник токена: {{ diagnosticsData.active_user_token_source }}</div>
              <v-alert v-if="!diagnosticsData.has_working_user_token" type="error" density="compact" class="mt-3">
                Пользовательский токен протух или отсутствует. Методы wall.post, likes.getList и конкурсы заблокированы VK API. Нажмите "Обновить токен VK".
              </v-alert>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
"""

# Let's inspect where to insert diag_template
if "<!-- ДИАГНОСТИКА ТОКЕНОВ И ПРАВ VK API -->" not in text:
    target_insert = "<v-container fluid"
    if target_insert in text:
        pos = text.find(">", text.find(target_insert)) + 1
        text = text[:pos] + "\n" + diag_template + text[pos:]

# Add script logic
script_target = "data() {"
script_addition = """    diagnosticsData: null,
    isDiagnosticsLoading: false,
"""
if "diagnosticsData:" not in text and script_target in text:
    text = text.replace(script_target, script_target + "\n" + script_addition, 1)

computed_target = "computed: {"
computed_addition = """    diagStatusColor() {
      if (!this.diagnosticsData) return 'surface'
      if (!this.diagnosticsData.has_working_user_token || this.diagnosticsData.group_token?.missing_critical?.length) return 'warning'
      return 'success'
    },
    diagStatusIcon() {
      if (!this.diagnosticsData) return 'mdi-information-outline'
      if (!this.diagnosticsData.has_working_user_token || this.diagnosticsData.group_token?.missing_critical?.length) return 'mdi-alert'
      return 'mdi-check-circle'
    },
"""
if "diagStatusColor()" not in text and computed_target in text:
    text = text.replace(computed_target, computed_target + "\n" + computed_addition, 1)

method_target = "methods: {"
method_addition = """    async fetchDiagnostics() {
      this.isDiagnosticsLoading = true
      try {
        const resp = await axios.get('/api/v1/vk/connections/1/diagnostics')
        this.diagnosticsData = resp.data
      } catch (err) {
        console.error('Failed to fetch VK diagnostics', err)
      } finally {
        this.isDiagnosticsLoading = false
      }
    },
"""
if "fetchDiagnostics()" not in text and method_target in text:
    text = text.replace(method_target, method_target + "\n" + method_addition, 1)

mounted_target = "mounted() {"
mounted_addition = """    this.fetchDiagnostics()
"""
if "this.fetchDiagnostics()" not in text and mounted_target in text:
    text = text.replace(mounted_target, mounted_target + "\n" + mounted_addition, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk-bots.vue updated with diagnostics card")
