<script setup>
import { computed } from 'vue'

const props = defineProps({
  botType: {
    type: String,
    required: true
  },
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const cfg = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// Хелпер для форматирования массива телефонов в комбобоксе
const adminPhones = computed({
  get: () => {
    const phones = cfg.value.test_admin_phones
    if (Array.isArray(phones)) return phones
    if (typeof phones === 'string') return [phones]
    return ['79220079019']
  },
  set: (val) => {
    cfg.value.test_admin_phones = Array.isArray(val) ? val : [val]
  }
})

const npsAlertPhones = computed({
  get: () => {
    const phones = cfg.value.max_alert_admin_phones
    if (Array.isArray(phones)) return phones
    if (typeof phones === 'string') return [phones]
    return []
  },
  set: (val) => {
    cfg.value.max_alert_admin_phones = Array.isArray(val) ? val : [val]
  }
})
</script>

<template>
  <div class="d-flex flex-column gap-5">
    <!-- Блок статуса и параметров шлюза MAX -->
    <VCard variant="outlined" class="pa-4 border bg-surface">
      <div class="d-flex align-center justify-space-between mb-3 flex-wrap gap-2">
        <div class="d-flex align-center gap-2">
          <VAvatar color="success" variant="tonal" size="36">
            <VIcon icon="ri-chat-voice-line" size="20" />
          </VAvatar>
          <div>
            <div class="text-subtitle-2 font-weight-bold">Канал Мессенджера MAX (Личный номер)</div>
            <div class="text-caption text-medium-emphasis">Прямая отправка клиентам по номеру телефона через Web Bridge</div>
          </div>
        </div>

        <div class="d-flex align-center gap-2 bg-light px-3 py-1 rounded border">
          <span class="text-caption font-weight-bold">Статус отправки в MAX:</span>
          <VSwitch
            v-model="cfg.max_enabled"
            color="success"
            density="compact"
            hide-details
          />
        </div>
      </div>

      <VAlert
        v-if="cfg.max_enabled"
        type="success"
        variant="tonal"
        density="compact"
        class="text-caption mb-3"
      >
        Канал активен. Сообщения клиентам будут отправляться с авторизованного личного аккаунта MAX (режим <code>bridge_only</code>).
      </VAlert>
      <VAlert
        v-else
        type="info"
        variant="tonal"
        density="compact"
        class="text-caption mb-3"
      >
        Канал MAX отключен. Уведомления и рассылки отправляются только через ВКонтакте.
      </VAlert>

      <VRow dense>
        <VCol cols="12" sm="4">
          <VTextField
            v-model.number="cfg.max_daily_limit"
            type="number"
            label="Лимит в сутки (защита от бана)"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="ri-shield-check-line"
            suffix="сообщ."
          />
        </VCol>

        <VCol cols="12" sm="4">
          <VTextField
            v-model.number="cfg.max_delay_seconds"
            type="number"
            label="Пауза между отправками"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="ri-time-line"
            suffix="сек."
          />
        </VCol>

        <VCol cols="12" sm="4">
          <VCombobox
            v-model="adminPhones"
            multiple
            chips
            closable-chips
            label="Телефон админа для теста"
            placeholder="79220079019 + Enter"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="ri-phone-line"
            hint="На этот номер уходит тестовое сообщение"
            persistent-hint
          />
        </VCol>
      </VRow>
    </VCard>

    <!-- ==================== ШАБЛОНЫ ДЛЯ SHOP BOT ==================== -->
    <div v-if="botType === 'shop'" class="d-flex flex-column gap-4">
      <VAlert type="info" variant="tonal" density="compact" class="text-caption">
        💡 <b>Особенность MAX для личного номера:</b> в личных чатах недоступны VK-кнопки клавиатуры. Гость может отвечать цифрами или словами: <code>1</code> или <code>меню</code> — каталог, <code>2</code> — повтор заказа, <code>3</code> — акции, <code>4</code> — статус заказа, <code>5</code> — баланс бонусов.
      </VAlert>

      <VTextarea
        v-model="cfg.max_welcome_message_verified"
        label="Приветствие в MAX для клиента с телефоном (с именем)"
        variant="outlined"
        rows="3"
        density="comfortable"
        hint="Теги: {first_name}, {last_name}, {bonus_balance}"
        persistent-hint
      />

      <VTextarea
        v-model="cfg.max_welcome_message_guest"
        label="Приветствие в MAX для нового гостя"
        variant="outlined"
        rows="3"
        density="comfortable"
        hint="Текст при первом обращении гостя в мессенджере MAX"
        persistent-hint
      />

      <VTextarea
        v-model="cfg.max_status_check_template"
        label="Шаблон статуса заказа в MAX (ответ на '4' или 'где заказ?')"
        variant="outlined"
        rows="2"
        density="comfortable"
        hint="Теги: {order_number}, {status_human}, {courier_name}"
        persistent-hint
      />
    </div>

    <!-- ==================== ШАБЛОНЫ ДЛЯ RETENTION BOT ==================== -->
    <div v-else-if="botType === 'retention'" class="d-flex flex-column gap-4">
      <!-- Цепочка 1: Новичок -->
      <VCard variant="outlined" class="pa-4 border">
        <div class="d-flex align-center justify-space-between mb-2">
          <span class="text-subtitle-2 font-weight-bold">Цепочка «Новичок» (через 7 дней в MAX)</span>
          <VSwitch v-model="cfg.max_newbie_enabled" color="success" density="compact" hide-details />
        </div>
        <VTextarea
          v-model="cfg.max_newbie_template"
          label="Шаблон сообщения в MAX для новичка"
          rows="2"
          variant="outlined"
          density="comfortable"
          hint="Теги: {first_name}, {promo_code}"
          persistent-hint
        />
      </VCard>

      <!-- Цепочка 2: Засыпающий -->
      <VCard variant="outlined" class="pa-4 border">
        <div class="d-flex align-center justify-space-between mb-2">
          <span class="text-subtitle-2 font-weight-bold">Цепочка «Засыпающий» (через 21 день в MAX)</span>
          <VSwitch v-model="cfg.max_sleeping_enabled" color="success" density="compact" hide-details />
        </div>
        <VTextarea
          v-model="cfg.max_sleeping_template"
          label="Шаблон сообщения в MAX для засыпающего"
          rows="2"
          variant="outlined"
          density="comfortable"
          hint="Теги: {first_name}, {promo_code}"
          persistent-hint
        />
      </VCard>

      <!-- Цепочка 3: Потерянный VIP -->
      <VCard variant="outlined" class="pa-4 border">
        <div class="d-flex align-center justify-space-between mb-2">
          <span class="text-subtitle-2 font-weight-bold">Цепочка «VIP-гость» (через 45 дней в MAX)</span>
          <VSwitch v-model="cfg.max_lost_vip_enabled" color="success" density="compact" hide-details />
        </div>
        <VTextarea
          v-model="cfg.max_lost_vip_template"
          label="Шаблон сообщения в MAX для VIP"
          rows="2"
          variant="outlined"
          density="comfortable"
          hint="Теги: {first_name}, {promo_code}"
          persistent-hint
        />
      </VCard>

      <!-- Цепочка 4: Будильник бонусов -->
      <VCard variant="outlined" class="pa-4 border">
        <div class="d-flex align-center justify-space-between mb-2">
          <span class="text-subtitle-2 font-weight-bold">Будильник сгорания бонусов в MAX (за 24ч)</span>
          <VSwitch v-model="cfg.max_burn_reminder_enabled" color="success" density="compact" hide-details />
        </div>
        <VTextarea
          v-model="cfg.max_burn_reminder_template"
          label="Шаблон напоминания о сгорании бонусов в MAX"
          rows="2"
          variant="outlined"
          density="comfortable"
          hint="Теги: {first_name}, {expiring_bonus_amount}"
          persistent-hint
        />
      </VCard>
    </div>

    <!-- ==================== ШАБЛОНЫ ДЛЯ NPS BOT ==================== -->
    <div v-else-if="botType === 'nps'" class="d-flex flex-column gap-4">
      <VAlert type="warning" variant="tonal" density="compact" class="text-caption">
        Клиент получает сообщение с личного номера MAX после доставки и отправляет в ответ цифру от 1 до 5. Система автоматически парсит входящую цифру и регистрирует оценку.
      </VAlert>

      <VTextarea
        v-model="cfg.max_msg_ask_rating"
        label="Текст запроса оценки в MAX (после доставки заказа)"
        rows="2"
        variant="outlined"
        density="comfortable"
        hint="Теги: {order_number}, {first_name}. Например: Оцените заказ №{order_number} от 1 до 5 в ответном сообщении"
        persistent-hint
      />

      <VTextarea
        v-model="cfg.max_msg_positive"
        label="Ответ в MAX при высокой оценке (4–5 ⭐)"
        rows="2"
        variant="outlined"
        density="comfortable"
        hint="Текст благодарности гостю за отличную оценку"
        persistent-hint
      />

      <VTextarea
        v-model="cfg.max_msg_negative"
        label="Ответ в MAX при низкой оценке (1–3 ⭐) — Перехват негатива"
        rows="2"
        variant="outlined"
        density="comfortable"
        hint="Извинения и просьба описать детали для управляющего"
        persistent-hint
      />

      <VCombobox
        v-model="npsAlertPhones"
        multiple
        chips
        closable-chips
        label="Номера телефонов управляющих для алертов в MAX о негативе"
        placeholder="79220079019 + Enter"
        variant="outlined"
        density="comfortable"
        prepend-inner-icon="ri-alarm-warning-line"
        hint="При оценке 1-3 ⭐ управляющим в MAX мгновенно придет уведомление"
        persistent-hint
      />
    </div>

    <!-- ==================== ШАБЛОНЫ ДЛЯ WHEEL BOT ==================== -->
    <div v-else-if="botType === 'wheel'" class="d-flex flex-column gap-4">
      <VTextarea
        v-model="cfg.max_msg_dm_win_template"
        label="Текст вручения выигранного промокода в MAX"
        rows="3"
        variant="outlined"
        density="comfortable"
        hint="Теги: {first_name}, {prize_name}, {promo_code}"
        persistent-hint
      />

      <VTextarea
        v-model="cfg.max_msg_dm_reminder_template"
        label="Напоминание об истечении промокода в MAX за 24ч"
        rows="2"
        variant="outlined"
        density="comfortable"
        hint="Теги: {first_name}, {prize_name}, {promo_code}"
        persistent-hint
      />
    </div>

    <!-- ==================== ШАБЛОНЫ ДЛЯ BROADCAST BOT ==================== -->
    <div v-else-if="botType === 'broadcast'" class="d-flex flex-column gap-4">
      <VCard variant="outlined" class="pa-4 border">
        <div class="text-subtitle-2 font-weight-bold mb-2">Канал отправки рассылки:</div>
        <VRadioGroup v-model="cfg.channel_target" inline density="compact">
          <VRadio label="Только ВКонтакте (VK)" value="vk" color="primary" />
          <VRadio label="Только MAX (Личный номер)" value="max" color="success" />
          <VRadio label="Оба канала (VK + MAX)" value="both" color="info" />
        </VRadioGroup>
      </VCard>

      <VTextarea
        v-model="cfg.max_broadcast_text"
        label="Текст массовой рассылки для мессенджера MAX"
        rows="3"
        variant="outlined"
        density="comfortable"
        hint="Теги: {first_name}"
        persistent-hint
      />

      <VTextarea
        v-model="cfg.max_happy_hours_template"
        label="Текст акции «Счастливые Часы» для MAX"
        rows="2"
        variant="outlined"
        density="comfortable"
        hint="Теги: {first_name}"
        persistent-hint
      />
    </div>

    <!-- ==================== ШАБЛОНЫ ДЛЯ REFERRAL BOT ==================== -->
    <div v-else-if="botType === 'referral'" class="d-flex flex-column gap-4">
      <VTextarea
        v-model="cfg.max_msg_ambassador_info"
        label="Текст для амбассадора в MAX (с персональным реферальным кодом)"
        rows="3"
        variant="outlined"
        density="comfortable"
        hint="Теги: {referral_code}, {friend_bonus_points}, {referrer_reward_points}"
        persistent-hint
      />

      <VTextarea
        v-model="cfg.max_msg_friend_welcome"
        label="Приветствие приглашенного друга в MAX"
        rows="2"
        variant="outlined"
        density="comfortable"
        hint="Теги: {friend_bonus_points}"
        persistent-hint
      />

      <VTextarea
        v-model="cfg.max_msg_referrer_reward_paid"
        label="Уведомление амбассадору в MAX о начислении бонусов за друга"
        rows="2"
        variant="outlined"
        density="comfortable"
        hint="Теги: {friend_name}, {referrer_reward_points}"
        persistent-hint
      />
    </div>
  </div>
</template>
