<script setup>

import { ref, onMounted, onUnmounted } from 'vue'

import { useRouter } from 'vue-router'

import NavItems from '@/layouts/components/NavItems.vue'

import logo from '@images/logo.svg?raw'

import VerticalNavLayout from '@layouts/components/VerticalNavLayout.vue'

import Footer from '@/layouts/components/Footer.vue'

import UserProfile from '@/layouts/components/UserProfile.vue'

import NavbarThemeSwitcher from '@/layouts/components/NavbarThemeSwitcher.vue'

import ChatDrawer from '@/components/ChatDrawer.vue'
import FloatingAiAssistant from '@/components/ai/FloatingAiAssistant.vue'

import { useChatStore } from '@/stores/chatStore.js'



import { formatDateTime } from '@/utils/date'



const router = useRouter()

const chatStore = useChatStore()

const currentTime = ref('')



const updateTime = () => {

  currentTime.value = formatDateTime(new Date(), { 

    hour: '2-digit', 

    minute: '2-digit',

    day: undefined,

    month: undefined,

    year: undefined

  })

}



// Pull to refresh logic

const pullDistance = ref(0)

const isPulling = ref(false)

const refreshThreshold = 150

const startY = ref(0)



const handleTouchStart = e => {

  if (window.scrollY === 0) {

    startY.value = e.touches[0].pageY

    isPulling.value = true

  }

}



const handleTouchMove = e => {

  if (!isPulling.value) return

  const currentY = e.touches[0].pageY

  const diff = currentY - startY.value

  if (diff > 0) {

    pullDistance.value = Math.min(diff * 0.5, refreshThreshold + 50)

    if (pullDistance.value > 10) {

      if (e.cancelable) e.preventDefault()

    }

  } else {

    isPulling.value = false

    pullDistance.value = 0

  }

}



const handleTouchEnd = () => {

  if (pullDistance.value >= refreshThreshold) {

    window.location.reload()

  }

  isPulling.value = false

  pullDistance.value = 0

}



const getNotificationIcon = (type) => {

  switch (type) {

    case 'new_order': return 'bx-receipt'

    case 'new_payment': return 'bx-credit-card'

    case 'courier_delivery':

    case 'courier_order_assigned': return 'bx-car'

    case 'courier_cooking_time_set': return 'bx-time-five'

    case 'courier_cooking_time_changed': return 'bx-history'

    case 'courier_status_changed': return 'bx-check-shield'

    case 'courier_amount_changed': return 'bx-money'

    case 'courier_address_changed': return 'bx-map-pin'

    case 'courier_changed_to_pickup': return 'bx-store'

    case 'courier_removed_from_delivery': return 'bx-x-circle'

    case 'courier_unassigned': return 'bx-user-x'

    case 'courier_delivery_time_changed': return 'bx-calendar-event'

    case 'chat_message': return 'bx-chat'

    case 'order_cancelled': return 'bx-x-circle'

    case 'order_changed': return 'bx-edit'

    case 'delivery_unassigned': return 'bx-package'

    default: return 'bx-bell'

  }

}



const getNotificationColor = (type) => {

  switch (type) {

    case 'new_order': return 'primary'

    case 'new_payment': return 'success'

    case 'courier_delivery':

    case 'courier_order_assigned': return 'warning'

    case 'courier_cooking_time_set': return 'info'

    case 'courier_cooking_time_changed': return 'primary'

    case 'courier_status_changed': return 'success'

    case 'courier_amount_changed': return 'teal'

    case 'courier_address_changed': return 'deep-purple'

    case 'courier_changed_to_pickup': return 'amber-darken-3'

    case 'courier_removed_from_delivery': return 'error'

    case 'courier_unassigned': return 'deep-orange'

    case 'courier_delivery_time_changed': return 'cyan-darken-3'

    case 'chat_message': return 'info'

    case 'order_cancelled': return 'error'

    case 'order_changed': return 'indigo'

    case 'delivery_unassigned': return 'warning'

    default: return 'secondary'

  }

}



const getCourierAlertColor = (type, status) => {

  switch (type) {

    case 'courier_order_assigned': return 'warning'

    case 'courier_cooking_time_set': return 'info'

    case 'courier_cooking_time_changed': return 'primary'

    case 'courier_status_changed':

      return status === 'cancelled' ? 'error' : 'success'

    case 'courier_amount_changed': return 'teal'

    case 'courier_address_changed': return 'deep-purple'

    case 'courier_changed_to_pickup': return 'amber-darken-4'

    case 'courier_removed_from_delivery': return 'error'

    case 'courier_unassigned': return 'deep-orange'

    case 'courier_delivery_time_changed': return 'cyan-darken-3'

    default: return 'warning'

  }

}



const getCourierAlertIcon = (type, status) => {

  switch (type) {

    case 'courier_order_assigned': return 'bx-car'

    case 'courier_cooking_time_set': return 'bx-time-five'

    case 'courier_cooking_time_changed': return 'bx-history'

    case 'courier_status_changed':

      return status === 'cancelled' ? 'bx-x-circle' : 'bx-check-circle'

    case 'courier_amount_changed': return 'bx-money'

    case 'courier_address_changed': return 'bx-map-pin'

    case 'courier_changed_to_pickup': return 'bx-store'

    case 'courier_removed_from_delivery': return 'bx-x-circle'

    case 'courier_unassigned': return 'bx-user-x'

    case 'courier_delivery_time_changed': return 'bx-calendar-event'

    default: return 'bx-bell'

  }

}



const formatNotifTime = (isoString) => {

  if (!isoString) return ''

  const date = new Date(isoString)

  return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })

}



const navigateToUrl = (url) => {

  if (!url) return

  

  let targetUrl = url.trim()

  

  // Внешние ссылки с протоколом

  if (targetUrl.startsWith('http://') || targetUrl.startsWith('https://')) {

    window.location.href = targetUrl

    return

  }



  const path = window.location.pathname

  const isEmployeeSPA = path.startsWith('/pers')

  

  if (isEmployeeSPA) {

    if (targetUrl.startsWith('/pers/')) {

      targetUrl = targetUrl.substring(5)

    } else if (targetUrl === '/pers') {

      targetUrl = '/'

    } else if (targetUrl.startsWith('/admin')) {

      window.location.href = targetUrl

      return

    }

  } else {

    if (targetUrl.startsWith('/admin/')) {

      targetUrl = targetUrl.substring(6)

    } else if (targetUrl === '/admin') {

      targetUrl = '/'

    } else if (targetUrl.startsWith('/pers')) {

      window.location.href = targetUrl

      return

    }

  }



  if (!targetUrl.startsWith('/')) {

    targetUrl = '/' + targetUrl

  }



  router.push(targetUrl)

}



const handleNotificationClick = (notif) => {

  chatStore.markNotificationRead(notif.id)

  if (notif.url) {

    navigateToUrl(notif.url)

  }

}



let timer = null



onMounted(() => {

  updateTime()

  timer = setInterval(updateTime, 60000)

  

  // Загружаем историю уведомлений и подключаем вебсокет

  chatStore.fetchNotifications()

  chatStore.connectWs()



  window.addEventListener('touchstart', handleTouchStart, { passive: false })

  window.addEventListener('touchmove', handleTouchMove, { passive: false })

  window.addEventListener('touchend', handleTouchEnd)

})



onUnmounted(() => {

  if (timer) clearInterval(timer)

  window.removeEventListener('touchstart', handleTouchStart)

  window.removeEventListener('touchmove', handleTouchMove)

  window.removeEventListener('touchend', handleTouchEnd)

})

</script>



<template>

  <VerticalNavLayout>

    <!-- 👉 Pull to refresh indicator -->

    <div 

      v-if="pullDistance > 0"

      class="pull-to-refresh-indicator"

      :style="{ transform: `translateY(${pullDistance - 60}px)`, opacity: Math.min(pullDistance / refreshThreshold, 1) }"

    >

      <VProgressCircular

        :model-value="Math.min((pullDistance / refreshThreshold) * 100, 100)"

        :rotate="-90"

        :size="40"

        :width="4"

        :color="pullDistance >= refreshThreshold ? 'primary' : 'grey-lighten-1'"

      >

        <VIcon

          v-if="pullDistance < refreshThreshold"

          icon="bx-down-arrow-alt"

          size="24"

        />

        <VIcon

          v-else

          icon="bx-refresh"

          class="rotate-animation"

          size="24"

        />

      </VProgressCircular>

    </div>



    <!-- 👉 navbar -->

    <template #navbar="{ toggleVerticalOverlayNavActive, isNavCollapsed, toggleIsNavCollapsed }">

      <div class="d-flex h-100 align-center">

        <!-- 👉 Vertical nav toggle in overlay mode -->

        <IconBtn

          class="ms-n3 d-lg-none"

          @click="toggleVerticalOverlayNavActive(true)"

        >

          <VIcon icon="bx-menu" />

        </IconBtn>



        <!-- 👉 Vertical nav collapse/expand toggle on desktop -->

        <IconBtn

          class="ms-n3 d-none d-lg-block me-2 text-primary"

          @click="toggleIsNavCollapsed"

        >

          <VIcon :icon="isNavCollapsed ? 'bx-menu-alt-left' : 'bx-menu'" />

        </IconBtn>



        <!-- 👉 Search -->

        <div

          class="d-flex align-center cursor-pointer ms-lg-n3"

          style="user-select: none;"

        >

          <!-- 👉 Search Trigger button -->

          <IconBtn>

            <VIcon icon="bx-search" />

          </IconBtn>



          <span class="d-none d-md-flex align-center text-disabled ms-2">

            <span class="me-2">Поиск</span>

            <span class="meta-key">&#8984;K</span>

          </span>

        </div>



        <VSpacer />



        <!-- Bell Notification Menu -->

        <VMenu :close-on-content-click="false" location="bottom end" transition="slide-y-transition">

          <template #activator="{ props }">

            <IconBtn v-bind="props" class="text-primary">

              <VBadge

                v-if="chatStore.unreadNotificationsCount > 0"

                color="error"

                :content="chatStore.unreadNotificationsCount"

                offset-x="2"

                offset-y="2"

              >

                <VIcon icon="bx-bell" />

              </VBadge>

              <VIcon v-else icon="bx-bell" />

            </IconBtn>

          </template>



          <VCard width="360" class="elevation-10">

            <VCardItem class="py-3 px-4 bg-var-theme-background">

              <div class="d-flex align-center justify-space-between">

                <span class="font-weight-bold text-subtitle-1">Уведомления</span>

                <VBtn 

                  v-if="chatStore.unreadNotificationsCount > 0"

                  variant="text" 

                  density="compact" 

                  color="primary"

                  prepend-icon="bx-check-double"

                  class="text-caption font-weight-black"

                  @click="chatStore.markAllNotificationsRead()"

                >

                  Прочитать все

                </VBtn>

              </div>

            </VCardItem>

            

            <VDivider />



            <VList class="py-0" style="max-height: 360px; overflow-y: auto;">

              <VListItem v-if="chatStore.notifications.length === 0" class="text-center py-6 text-disabled text-body-2">

                Нет новых уведомлений

              </VListItem>

              

              <template v-else v-for="notif in chatStore.notifications" :key="notif.id">

                <VListItem 

                  :value="notif"

                  class="py-3 cursor-pointer" 

                  :class="{'bg-var-theme-background': !notif.is_read}"

                  @click="handleNotificationClick(notif)"

                >

                  <template #prepend>

                    <VAvatar 

                      :color="getNotificationColor(notif.event_type)" 

                      variant="tonal" 

                      size="36" 

                      class="me-3"

                    >

                      <VIcon :icon="getNotificationIcon(notif.event_type)" size="20" />

                    </VAvatar>

                  </template>



                  <VListItemTitle class="font-weight-bold text-body-2">

                    {{ notif.title }}

                  </VListItemTitle>

                  <VListItemSubtitle class="text-caption text-wrap mt-1 pr-6" style="line-height: 1.3;">

                    {{ notif.body }}

                  </VListItemSubtitle>



                  <template #append>

                    <div class="d-flex flex-column align-end">

                      <span class="text-xxs text-disabled">{{ formatNotifTime(notif.created_at) }}</span>

                      <VBadge

                        v-if="!notif.is_read"

                        color="primary"

                        dot

                        inline

                        class="mt-2"

                        @click.stop="chatStore.markNotificationRead(notif.id)"

                        title="Пометить как прочитанное"

                      />

                    </div>

                  </template>

                </VListItem>

                <VDivider />

              </template>

            </VList>

          </VCard>

        </VMenu>



        <NavbarThemeSwitcher class="me-1" />



        <IconBtn

          class="me-2"

          @click="chatStore.isDrawerOpen = true"

        >

          <VBadge

            v-if="chatStore.unreadCount > 0"

            color="error"

            :content="chatStore.unreadCount"

            offset-x="2"

            offset-y="2"

          >

            <VIcon icon="bx-chat" />

          </VBadge>

          <VIcon

            v-else

            icon="bx-chat"

          />

        </IconBtn>



        <UserProfile />



        <div class="ms-4 font-weight-bold text-body-1 text-primary d-flex align-center">

          <VIcon icon="bx-time-five" size="20" class="me-1" />

          {{ currentTime }}

        </div>

      </div>

    </template>



    <template #vertical-nav-header="{ toggleIsOverlayNavActive, isNavCollapsed, toggleIsNavCollapsed }">

      <RouterLink

        to="/"

        class="app-logo app-title-wrapper"

      >

        <!-- eslint-disable vue/no-v-html -->

        <div

          class="d-flex"

          v-html="logo"

        />

        <!-- eslint-enable -->



        <h1 class="app-logo-title">

          FoodTech

        </h1>

      </RouterLink>



      <IconBtn

        class="d-none d-lg-block text-primary nav-pin-button"

        @click="toggleIsNavCollapsed"

      >

        <VIcon :icon="isNavCollapsed ? 'bx-radio-circle' : 'bx-radio-circle-marked'" />

      </IconBtn>



      <IconBtn

        class="d-block d-lg-none"

        @click="toggleIsOverlayNavActive(false)"

      >

        <VIcon icon="bx-x" />

      </IconBtn>

    </template>



    <template #vertical-nav-content>

      <NavItems />

    </template>



    <!-- 👉 Pages -->

    <slot />



    <!-- 👉 Footer -->

    <template #footer>

      <Footer />

    </template>



    <!-- 👉 Chat Drawer -->

    <ChatDrawer />

    <!-- 👉 Floating Interactive AI Assistant -->
    <FloatingAiAssistant />



    <!-- 👉 Global Payment Notification -->

    <VSnackbar

      v-model="chatStore.paymentNotification.show"

      color="success"

      location="top right"

      :timeout="8000"

      elevation="24"

      class="payment-toast"

    >

      <div class="d-flex align-center py-1">

        <VAvatar color="white" class="me-3 font-weight-black elevation-2" size="40">

          <VIcon icon="bx-credit-card" color="success" size="24" />

        </VAvatar>

        <div class="d-flex flex-column">

          <span class="font-weight-black text-body-1 text-white">Новое поступление денег!</span>

          <span class="text-body-2 font-weight-bold text-white">

            Сумма: {{ chatStore.paymentNotification.amount }} ₽ (через {{ chatStore.paymentNotification.method }})

          </span>

          <span class="text-caption text-white opacity-80">

            От: {{ chatStore.paymentNotification.customer }} | Заказ: {{ chatStore.paymentNotification.orderId ? '#' + chatStore.paymentNotification.orderId : '---' }}

          </span>

        </div>

      </div>

      <template #actions>

        <VBtn

          color="white"

          variant="text"

          class="font-weight-black"

          @click="() => { navigateToUrl('/admin/bank/tbank-payments'); chatStore.paymentNotification.show = false }"

        >

          СМОТРЕТЬ

        </VBtn>

        <VBtn

          color="white"

          variant="text"

          @click="chatStore.paymentNotification.show = false"

        >

          ОК

        </VBtn>

      </template>

    </VSnackbar>



    <!-- 👉 Global Order Notification -->

    <VSnackbar

      v-model="chatStore.orderNotification.show"

      color="info"

      location="top right"

      :timeout="chatStore.notificationSettings?.new_order_repeat_enabled ? 0 : 10000"

      elevation="24"

      class="order-toast"

      @update:model-value="val => { if(!val) chatStore.stopOrderSoundRepeat() }"

    >

      <div class="d-flex align-center py-1">

        <VAvatar color="white" class="me-3 font-weight-black elevation-2" size="40">

          <VIcon icon="bx-receipt" color="info" size="24" />

        </VAvatar>

        <div class="d-flex flex-column">

          <span class="font-weight-black text-body-1 text-white">Поступил новый заказ!</span>

          <span class="text-body-2 font-weight-bold text-white">

            Сумма: {{ chatStore.orderNotification.amount }} ₽

          </span>

          <span class="text-caption text-white opacity-80">

            Клиент: {{ chatStore.orderNotification.customer }} | Заказ: {{ chatStore.orderNotification.orderNumber ? '#' + chatStore.orderNotification.orderNumber : '---' }}

          </span>

        </div>

      </div>

      <template #actions>

        <VBtn

          color="white"

          variant="text"

          class="font-weight-black"

          @click="() => { navigateToUrl('/admin/orders'); chatStore.orderNotification.show = false; chatStore.stopOrderSoundRepeat() }"

        >

          СМОТРЕТЬ

        </VBtn>

        <VBtn

          color="white"

          variant="text"

          @click="() => { chatStore.orderNotification.show = false; chatStore.stopOrderSoundRepeat() }"

        >

          ОК

        </VBtn>

      </template>

    </VSnackbar>



    <!-- 👉 Courier Delivery Notification -->

    <VSnackbar

      v-model="chatStore.courierNotification.show"

      color="warning"

      location="top right"

      :timeout="12000"

      elevation="24"

    >

      <div class="d-flex align-center py-1">

        <VAvatar color="white" class="me-3 font-weight-black elevation-2" size="40">

          <VIcon icon="bx-car" color="warning" size="24" />

        </VAvatar>

        <div class="d-flex flex-column">

          <span class="font-weight-black text-body-1 text-white">Вам назначена доставка!</span>

          <span class="text-body-2 font-weight-bold text-white">

            Заказ: #{{ chatStore.courierNotification.orderNumber }} | Сумма: {{ chatStore.courierNotification.amount }} ₽

          </span>

          <span class="text-caption text-white opacity-80">

            Адрес: {{ chatStore.courierNotification.address }}

          </span>

        </div>

      </div>

      <template #actions>

        <VBtn

          color="white"

          variant="text"

          class="font-weight-black"

          @click="() => { navigateToUrl('/pers/courier'); chatStore.courierNotification.show = false }"

        >

          СМОТРЕТЬ

        </VBtn>

        <VBtn

          color="white"

          variant="text"

          @click="chatStore.courierNotification.show = false"

        >

          ОК

        </VBtn>

      </template>

    </VSnackbar>



    <!-- 👉 Dedicated Courier Alert Pop-up Notification (10 Событий для курьера) -->

    <VSnackbar

      v-model="chatStore.courierAlert.show"

      :color="getCourierAlertColor(chatStore.courierAlert.type, chatStore.courierAlert.status)"

      location="top center"

      :timeout="15000"

      elevation="24"

      min-width="320"

      max-width="520"

    >

      <div class="d-flex align-start py-1">

        <VAvatar color="white" class="me-3 elevation-2 mt-1" size="42">

          <VIcon

            :icon="getCourierAlertIcon(chatStore.courierAlert.type, chatStore.courierAlert.status)"

            :color="getCourierAlertColor(chatStore.courierAlert.type, chatStore.courierAlert.status)"

            size="26"

          />

        </VAvatar>

        <div class="d-flex flex-column flex-grow-1">

          <div class="d-flex align-center justify-space-between mb-1">

            <span class="font-weight-black text-body-1 text-white">{{ chatStore.courierAlert.title }}</span>

            <VChip

              v-if="chatStore.courierAlert.orderNumber"

              size="x-small"

              color="white"

              variant="flat"

              class="text-black font-weight-black ms-2"

            >

              #{{ chatStore.courierAlert.orderNumber }}

            </VChip>

          </div>

          <span class="text-body-2 text-white font-weight-medium">

            {{ chatStore.courierAlert.body }}

          </span>

          <div v-if="chatStore.courierAlert.address" class="text-caption text-white opacity-90 mt-1 d-flex align-center">

            <VIcon icon="bx-map" size="14" class="me-1" />

            <span class="text-truncate">{{ chatStore.courierAlert.address }}</span>

          </div>

        </div>

      </div>

      <template #actions>

        <VBtn

          color="white"

          variant="flat"

          class="font-weight-black text-dark me-1"

          size="small"

          @click="() => { navigateToUrl(chatStore.courierAlert.url || '/pers/courier'); chatStore.courierAlert.show = false }"

        >

          СМОТРЕТЬ ЗАКАЗ

        </VBtn>

        <VBtn

          color="white"

          variant="text"

          size="small"

          @click="chatStore.courierAlert.show = false"

        >

          ЗАКРЫТЬ

        </VBtn>

      </template>

    </VSnackbar>



    <!-- 👉 Order Cancelled Notification -->

    <VSnackbar

      v-model="chatStore.orderCancelledNotification.show"

      color="error"

      location="top right"

      :timeout="8000"

      elevation="24"

    >

      <div class="d-flex align-center py-1">

        <VAvatar color="white" class="me-3 font-weight-black elevation-2" size="40">

          <VIcon icon="bx-x-circle" color="error" size="24" />

        </VAvatar>

        <div class="d-flex flex-column">

          <span class="font-weight-black text-body-1 text-white">Заказ отменен!</span>

          <span class="text-body-2 text-white font-weight-bold">

            Заказ: #{{ chatStore.orderCancelledNotification.orderNumber }}

          </span>

          <span class="text-caption text-white opacity-80">

            Клиент: {{ chatStore.orderCancelledNotification.customer }}

          </span>

        </div>

      </div>

      <template #actions>

        <VBtn

          color="white"

          variant="text"

          @click="chatStore.orderCancelledNotification.show = false"

        >

          ОК

        </VBtn>

      </template>

    </VSnackbar>



    <!-- 👉 Order Changed Notification -->

    <VSnackbar

      v-model="chatStore.orderChangedNotification.show"

      color="indigo"

      location="top right"

      :timeout="8000"

      elevation="24"

    >

      <div class="d-flex align-center py-1">

        <VAvatar color="white" class="me-3 font-weight-black elevation-2" size="40">

          <VIcon icon="bx-edit" color="indigo" size="24" />

        </VAvatar>

        <div class="d-flex flex-column">

          <span class="font-weight-black text-body-1 text-white">Заказ изменен!</span>

          <span class="text-body-2 text-white font-weight-bold">

            Заказ: #{{ chatStore.orderChangedNotification.orderNumber }}

          </span>

          <span class="text-caption text-white opacity-80">

            Клиент: {{ chatStore.orderChangedNotification.customer }}

          </span>

        </div>

      </div>

      <template #actions>

        <VBtn

          color="white"

          variant="text"

          class="font-weight-black"

          @click="() => { navigateToUrl('/admin/orders'); chatStore.orderChangedNotification.show = false }"

        >

          СМОТРЕТЬ

        </VBtn>

        <VBtn

          color="white"

          variant="text"

          @click="chatStore.orderChangedNotification.show = false"

        >

          ОК

        </VBtn>

      </template>

    </VSnackbar>



    <!-- 👉 Order Delivered Notification (Заказ доставлен курьером - не пропадает пока не закроют) -->

    <VSnackbar

      v-model="chatStore.orderDeliveredAlert.show"

      color="success"

      location="top center"

      :timeout="-1"

      elevation="24"

      min-width="340"

      max-width="540"

    >

      <div class="d-flex align-start py-1">

        <VAvatar color="white" class="me-3 elevation-2 mt-1" size="42">

          <VIcon icon="bx-check-double" color="success" size="28" />

        </VAvatar>

        <div class="d-flex flex-column flex-grow-1">

          <div class="d-flex align-center justify-space-between mb-1">

            <span class="font-weight-black text-body-1 text-white">Заказ доставлен!</span>

            <VChip

              v-if="chatStore.orderDeliveredAlert.orderNumber"

              size="x-small"

              color="white"

              variant="flat"

              class="text-success font-weight-black ms-2"

            >

              #{{ chatStore.orderDeliveredAlert.orderNumber }}

            </VChip>

          </div>

          <div class="text-body-2 text-white font-weight-medium">

            Курьер: <strong class="text-white font-weight-bold">{{ chatStore.orderDeliveredAlert.courierName || 'Не указан' }}</strong>

            <span v-if="chatStore.orderDeliveredAlert.amount" class="ms-2">| Сумма: {{ chatStore.orderDeliveredAlert.amount }} ₽</span>

          </div>

          <div v-if="chatStore.orderDeliveredAlert.address" class="text-caption text-white opacity-90 mt-1 d-flex align-center">

            <VIcon icon="bx-map" size="14" class="me-1" />

            <span class="text-truncate">{{ chatStore.orderDeliveredAlert.address }}</span>

          </div>

          <div v-if="chatStore.orderDeliveredAlert.actualTime" class="text-caption text-white opacity-80 mt-1">

            Время доставки: {{ chatStore.orderDeliveredAlert.actualTime }}

          </div>

        </div>

      </div>

      <template #actions>

        <VBtn

          color="white"

          variant="flat"

          class="font-weight-black text-success me-1"

          size="small"

          @click="() => { navigateToUrl('/admin/orders'); chatStore.orderDeliveredAlert.show = false }"

        >

          В ЗАКАЗЫ

        </VBtn>

        <VBtn

          color="white"

          variant="text"

          size="small"

          @click="chatStore.orderDeliveredAlert.show = false"

        >

          ЗАКРЫТЬ

        </VBtn>

      </template>

    </VSnackbar>

  </VerticalNavLayout>

</template>



<style lang="scss" scoped>

.meta-key {

  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));

  border-radius: 6px;

  block-size: 1.5625rem;

  line-height: 1.3125rem;

  padding-block: 0.125rem;

  padding-inline: 0.25rem;

}



.app-logo {

  display: flex;

  align-items: center;

  column-gap: 0.75rem;



  .app-logo-title {

    font-size: 1.25rem;

    font-weight: 500;

    line-height: 1.75rem;

    text-transform: uppercase;

  }

}



.pull-to-refresh-indicator {

  position: fixed;

  top: 0;

  left: 0;

  right: 0;

  display: flex;

  justify-content: center;

  align-items: center;

  z-index: 9999;

  pointer-events: none;

  height: 60px;

  background: transparent;

}



.rotate-animation {

  animation: rotate 1s linear infinite;

}



@keyframes rotate {

  from {

    transform: rotate(0deg);

  }



  to {

    transform: rotate(360deg);

  }

}



.app-logo-title {

  transition: opacity 0.2s ease-in-out, visibility 0.2s ease-in-out;

}



:global(.layout-vertical-nav-collapsed .layout-vertical-nav:not(.hovered)) {

  .app-logo-title {

    opacity: 0 !important;

    visibility: hidden !important;

    width: 0 !important;

    overflow: hidden;

  }

  .nav-pin-button {

    opacity: 0 !important;

    visibility: hidden !important;

  }

}

</style>

