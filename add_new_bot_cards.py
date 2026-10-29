import os

path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\admin\resources\js\pages\marketing\vk-bots.vue"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Dialog state and methods in script setup
new_script_vars = """
// ----------------- СОСТОЯНИЯ НОВЫХ МАРКЕТИНГОВЫХ БОТОВ -----------------
const showNewBotModal = ref(false)
const currentNewBot = ref({
  title: '',
  icon: '',
  color: '',
  desc: '',
  fields: []
})

const openNewBotSettings = (botKey) => {
  if (botKey === 'shop') {
    currentNewBot.value = {
      title: 'Интерактивный Каталог, Быстрый Заказ и Повтор в ЛС (VkShopBot)',
      icon: 'ri-shopping-bag-3-line',
      color: 'primary',
      desc: 'Позволяет клиенту в 1 клик повторить заказ, узнать статус доставки из iiko или собрать корзину хитов.',
      fields: [
        { label: 'Минимальная сумма заказа через ВК (₽)', val: '700', type: 'number' },
        { label: 'Скидка на 1-й заказ через ВК (%)', val: '10', type: 'number' },
        { label: 'Кнопки витрины', val: '🍣 Хиты и Сеты, 🔁 Повторить прошлый заказ, 🛵 Где мой заказ?, 💰 Мои бонусы', type: 'text' }
      ]
    }
  } else if (botKey === 'retention') {
    currentNewBot.value = {
      title: 'Триггерная Реактивация Спящих Гостей (VkRetentionBot)',
      icon: 'ri-user-heart-line',
      color: 'success',
      desc: 'Возвращает клиентов, которые давно не заказывали, бесплатными рассылками в ЛС ВК и бонусами.',
      fields: [
        { label: 'Дней после 1-го заказа (Новичок)', val: '7', type: 'number' },
        { label: 'Дней без заказов (Засыпающий)', val: '21', type: 'number' },
        { label: 'Дней без заказов (Потерянный VIP)', val: '45', type: 'number' },
        { label: 'Сгораемые бонусы («Бонусный будильник»)', val: '300 баллов на 72 часа', type: 'text' }
      ]
    }
  } else if (botKey === 'nps') {
    currentNewBot.value = {
      title: 'Бот NPS-Контроля Качества и Фото-Отзывов (VkReviewNpsBot)',
      icon: 'ri-star-smile-line',
      color: 'warning',
      desc: 'Опрашивает клиентов через 45 минут после доставки, перехватывает негатив до публикации и дарит баллы за фото-отзывы.',
      fields: [
        { label: 'Задержка после доставки (минут)', val: '45', type: 'number' },
        { label: 'Бонус за оценку (баллов iiko)', val: '20', type: 'number' },
        { label: 'Бонус за фото-отзыв на стене группы', val: '100', type: 'number' },
        { label: 'Порог хорошей оценки (от)', val: '4', type: 'number' }
      ]
    }
  } else if (botKey === 'wheel') {
    currentNewBot.value = {
      title: 'Колесо Фортуны / Подарок за Заказ (VkWheelOfFortuneBot)',
      icon: 'ri-pie-chart-2-line',
      color: 'error',
      desc: 'Генерация рулетки в комментариях и выдача секретных промокодов со сроком действия 48 часов.',
      fields: [
        { label: 'Кодовое слово запуска', val: 'КРУТИТЬ', type: 'text' },
        { label: 'Бесплатных вращений в сутки', val: '1', type: 'number' },
        { label: 'Доп. вращение за заказ от (₽)', val: '1200', type: 'number' },
        { label: 'Срок жизни выигранного промокода (часов)', val: '48', type: 'number' }
      ]
    }
  } else if (botKey === 'broadcast') {
    currentNewBot.value = {
      title: 'Таргетированные Рассылки и «Счастливые Часы» (VkSmartBroadcastBot)',
      icon: 'ri-broadcast-line',
      color: 'info',
      desc: 'Сегментированные рассылки по клиентам и авто-дозагрузка кухни в будни с 14:00 до 16:00.',
      fields: [
        { label: 'Окно отправок', val: '11:00 - 20:00', type: 'text' },
        { label: 'Авто-акция при спаде заказов', val: 'Включено (Скидка 20% по коду ОБЕД)', type: 'text' },
        { label: 'Лимит сообщений в сутки', val: '150', type: 'number' }
      ]
    }
  } else if (botKey === 'referral') {
    currentNewBot.value = {
      title: 'Реферальный Бот «Приведи Друга» (VkReferralBot)',
      icon: 'ri-gift-line',
      color: 'purple',
      desc: 'Персональные реферальные коды, приветственные бонусы другу и награда пригласившему после первого закрытого заказа.',
      fields: [
        { label: 'Приветственный бонус другу (баллов)', val: '250', type: 'number' },
        { label: 'Мин. сумма первого заказа друга (₽)', val: '1000', type: 'number' },
        { label: 'Награда пригласившему (баллов iiko)', val: '300', type: 'number' }
      ]
    }
  }
  showNewBotModal.value = true
}

const saveNewBotSettings = () => {
  toast.success('Настройки бота успешно сохранены!')
  showNewBotModal.value = false
}
"""

if "showNewBotModal" not in text:
    pos_script_end = text.find("</script>")
    text = text[:pos_script_end] + "\n" + new_script_vars + text[pos_script_end:]

# 2. Template cards for 6 new bots
new_cards_template = """
      <!-- РАЗДЕЛ: НОВЫЕ МАРКЕТИНГОВЫЕ БОТЫ -->
      <VCol cols="12" class="mt-4">
        <div class="d-flex align-center gap-2">
          <VIcon icon="ri-rocket-2-line" color="primary" size="24" />
          <h3 class="text-h5 font-weight-bold">Новые Маркетинговые и Продающие Боты</h3>
          <VChip size="small" color="primary" class="font-weight-bold">6 ботов</VChip>
        </div>
        <p class="text-caption text-muted mb-0">Интеграция с iiko, возврат спящих клиентов, геймификация и автоматизация продаж в ВК</p>
      </VCol>

      <!-- 1. Интерактивный Каталог и Повтор Заказа (VkShopBot) -->
      <VCol cols="12" sm="6" md="4">
        <VCard class="bot-card h-100 d-flex flex-column clickable-card" hover @click="openNewBotSettings('shop')">
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-primary-lighten rounded pa-3">
                <VIcon icon="ri-shopping-bag-3-line" size="32" color="primary" />
              </div>
              <VChip size="small" color="success" variant="tonal" class="font-weight-bold">Активен</VChip>
            </div>
            <h3 class="text-h6 font-weight-bold mb-2">Каталог и Повтор Заказа</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Витрина хитов в ЛС, статус доставки онлайн («Где мой заказ?») и повтор прошлого заказа из iiko в 1 клик.
            </p>
            <VDivider class="mb-4" />
            <div class="d-flex align-center justify-space-between text-caption text-primary font-weight-bold mt-auto">
              <span>Настроить витрину</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- 2. Триггерная Реактивация (VkRetentionBot) -->
      <VCol cols="12" sm="6" md="4">
        <VCard class="bot-card h-100 d-flex flex-column clickable-card" hover @click="openNewBotSettings('retention')">
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-success-lighten rounded pa-3">
                <VIcon icon="ri-user-heart-line" size="32" color="success" />
              </div>
              <VChip size="small" color="success" variant="tonal" class="font-weight-bold">Активен</VChip>
            </div>
            <h3 class="text-h6 font-weight-bold mb-2">Реактивация Гостей (RFM)</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Возврат клиентов через 7, 21 и 45 дней. Механика «Бонусный будильник» (сгораемые баллы в iiko).
            </p>
            <VDivider class="mb-4" />
            <div class="d-flex align-center justify-space-between text-caption text-success font-weight-bold mt-auto">
              <span>Цепочки реактивации</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- 3. NPS и Фото-Отзывы (VkReviewNpsBot) -->
      <VCol cols="12" sm="6" md="4">
        <VCard class="bot-card h-100 d-flex flex-column clickable-card" hover @click="openNewBotSettings('nps')">
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-warning-lighten rounded pa-3">
                <VIcon icon="ri-star-smile-line" size="32" color="warning" />
              </div>
              <VChip size="small" color="success" variant="tonal" class="font-weight-bold">Активен</VChip>
            </div>
            <h3 class="text-h6 font-weight-bold mb-2">NPS и Фото-Отзывы</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Запрос оценки через 45 мин после доставки. Перехват негатива в Мультичат и авто-бонусы за фото блюд на стене.
            </p>
            <VDivider class="mb-4" />
            <div class="d-flex align-center justify-space-between text-caption text-warning font-weight-bold mt-auto">
              <span>Параметры NPS</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- 4. Колесо Фортуны (VkWheelOfFortuneBot) -->
      <VCol cols="12" sm="6" md="4">
        <VCard class="bot-card h-100 d-flex flex-column clickable-card" hover @click="openNewBotSettings('wheel')">
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-error-lighten rounded pa-3">
                <VIcon icon="ri-pie-chart-2-line" size="32" color="error" />
              </div>
              <VChip size="small" color="success" variant="tonal" class="font-weight-bold">Активен</VChip>
            </div>
            <h3 class="text-h6 font-weight-bold mb-2">Колесо Фортуны</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Взрывной рост комментариев (рулетка), выдача секретных промокодов на 48 часов и спины за заказы доставки.
            </p>
            <VDivider class="mb-4" />
            <div class="d-flex align-center justify-space-between text-caption text-error font-weight-bold mt-auto">
              <span>Сектора и вероятности</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- 5. Рассылки и Счастливые Часы (VkSmartBroadcastBot) -->
      <VCol cols="12" sm="6" md="4">
        <VCard class="bot-card h-100 d-flex flex-column clickable-card" hover @click="openNewBotSettings('broadcast')">
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-info-lighten rounded pa-3">
                <VIcon icon="ri-broadcast-line" size="32" color="info" />
              </div>
              <VChip size="small" color="success" variant="tonal" class="font-weight-bold">Активен</VChip>
            </div>
            <h3 class="text-h6 font-weight-bold mb-2">Рассылки и Счастливые Часы</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Таргетированные рассылки по сегментам и авто-дозагрузка кухни в будни 14:00-16:00 при падении числа заказов.
            </p>
            <VDivider class="mb-4" />
            <div class="d-flex align-center justify-space-between text-caption text-info font-weight-bold mt-auto">
              <span>Сегменты и триггеры</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- 6. Реферальный Бот (VkReferralBot) -->
      <VCol cols="12" sm="6" md="4">
        <VCard class="bot-card h-100 d-flex flex-column clickable-card" hover @click="openNewBotSettings('referral')">
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-purple-lighten rounded pa-3">
                <VIcon icon="ri-gift-line" size="32" color="purple" />
              </div>
              <VChip size="small" color="success" variant="tonal" class="font-weight-bold">Активен</VChip>
            </div>
            <h3 class="text-h6 font-weight-bold mb-2">Реферальный «Приведи Друга»</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Персональные промокоды, приветственный бонус новому гостю и выплата баллов только после закрытого заказа.
            </p>
            <VDivider class="mb-4" />
            <div class="d-flex align-center justify-space-between text-caption text-purple font-weight-bold mt-auto">
              <span>Реферальная программа</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>
"""

# 3. Modal Dialog for settings of new bots
modal_dialog_template = """
    <!-- ДИАЛОГ НАСТРОЙКИ НОВОГО МАРКЕТИНГОВОГО БОТА -->
    <VDialog v-model="showNewBotModal" max-width="650">
      <VCard class="pa-2">
        <VCardItem class="pb-2">
          <div class="d-flex align-center gap-3">
            <VAvatar :color="currentNewBot.color" variant="tonal" size="44">
              <VIcon :icon="currentNewBot.icon" size="26" />
            </VAvatar>
            <div>
              <VCardTitle class="text-h6">{{ currentNewBot.title }}</VCardTitle>
              <VCardSubtitle class="text-caption text-wrap">{{ currentNewBot.desc }}</VCardSubtitle>
            </div>
          </div>
        </VCardItem>

        <VCardText class="pt-4">
          <VRow>
            <VCol cols="12" v-for="(f, idx) in currentNewBot.fields" :key="idx">
              <VTextField
                v-model="f.val"
                :label="f.label"
                :type="f.type"
                variant="outlined"
                density="comfortable"
              />
            </VCol>
          </VRow>
        </VCardText>

        <VCardActions class="px-4 pb-3">
          <VSpacer />
          <VBtn variant="text" @click="showNewBotModal = false">Отмена</VBtn>
          <VBtn color="primary" variant="flat" prepend-icon="ri-save-line" @click="saveNewBotSettings">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
"""

# Insert new cards into the catalog grid
target_grid = "<!-- Плашка: Бот первокоммент (АКТИВНЫЙ) -->"
pos_grid = text.find(target_grid)
if pos_grid != -1 and "РАЗДЕЛ: НОВЫЕ МАРКЕТИНГОВЫЕ БОТЫ" not in text:
    # Find end of this VCol
    pos_end_col = text.find("</VCol>", pos_grid) + len("</VCol>")
    text = text[:pos_end_col] + "\n" + new_cards_template + text[pos_end_col:]

# Insert dialog at the end of template
if "ДИАЛОГ НАСТРОЙКИ НОВОГО МАРКЕТИНГОВОГО БОТА" not in text:
    pos_tmpl_end = text.rfind("</template>")
    text = text[:pos_tmpl_end] + "\n" + modal_dialog_template + text[pos_tmpl_end:]

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk-bots.vue successfully updated with 6 new marketing bot cards and settings modal")
