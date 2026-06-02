<script setup>
import { useChatStore } from '@/stores/chatStore'
import { ref, watch, onMounted, nextTick, computed } from 'vue'
import { useDisplay } from 'vuetify'
import { formatDate, formatDateTime, formatTime } from '@/utils/date'

const chatStore = useChatStore()
const { mobile, mdAndUp, width } = useDisplay()

const newMessage = ref('')
const messageContainer = ref(null)

const drawerWidth = computed(() => {
  if (mobile.value) return width.value // 100% of viewport width
  if (mdAndUp.value) return 450
  
  return 400
})

const activeContact = computed(() => {
  if (chatStore.activeContactId === null) return null
  
  return chatStore.contacts.find(c => c.id === chatStore.activeContactId)
})

const selectContact = async contact => {
  chatStore.activeContactId = contact.id
  await chatStore.fetchMessages(contact.id, contact.id === 0)
  chatStore.markRead(contact.id, contact.id === 0)
  scrollToBottom()
}

const send = () => {
  if (!newMessage.value.trim()) return
  chatStore.sendMessage(newMessage.value, chatStore.activeContactId, chatStore.activeContactId === 0)
  newMessage.value = ''
  scrollToBottom()
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight
    }
  })
}

watch(() => chatStore.messages.length, scrollToBottom)

watch(() => chatStore.isDrawerOpen, val => {
  if (val) {
    chatStore.fetchContacts()
    chatStore.fetchMe()
    if (chatStore.activeContactId !== null) {
      chatStore.markRead(chatStore.activeContactId, chatStore.activeContactId === 0)
    }
  }
})

onMounted(() => {
  chatStore.connectWs()
})

</script>

<template>
  <VNavigationDrawer
    v-model="chatStore.isDrawerOpen"
    location="right"
    temporary
    scrim
    :width="drawerWidth"
    class="chat-drawer"
  >
    <div class="d-flex flex-column h-100">
      <!-- Header -->
      <VToolbar
        color="primary"
        density="compact"
      >
        <VBtn
          v-if="chatStore.activeContactId !== null"
          icon="bx-chevron-left"
          @click="chatStore.activeContactId = null"
        />
        <VToolbarTitle>
          {{ chatStore.activeContactId === null ? 'Чат сотрудников' : (activeContact?.full_name || 'Чат') }}
        </VToolbarTitle>
        <VSpacer />
        <VBtn
          icon="bx-x"
          @click="chatStore.isDrawerOpen = false"
        />
      </VToolbar>

      <!-- Contact List -->
      <VList
        v-if="chatStore.activeContactId === null"
        class="flex-grow-1 overflow-y-auto"
      >
        <VListItem
          v-for="contact in chatStore.contacts"
          :key="contact.id"
          :title="contact.full_name"
          :subtitle="contact.id === 0 ? 'Группа для всех' : (contact.is_online ? 'В сети' : `Был: ${formatDate(contact.last_login_at)}`)"
          @click="selectContact(contact)"
        >
          <template #prepend>
            <VAvatar
              v-if="contact.id === 0"
              color="secondary"
              icon="bx-group"
              class="me-3"
            />
            <VBadge
              v-else
              dot
              :color="contact.is_online ? 'success' : 'grey'"
              location="bottom right"
              offset-x="3"
              offset-y="3"
            >
              <VAvatar
                color="primary"
                variant="tonal"
              >
                {{ contact.full_name?.charAt(0) || '?' }}
              </VAvatar>
            </VBadge>
          </template>
          <template #append>
            <VBadge
              v-if="contact.unread_count > 0"
              color="error"
              :content="contact.unread_count"
              inline
            />
          </template>
        </VListItem>
      </VList>

      <!-- Chat Window -->
      <div
        v-else
        class="flex-grow-1 d-flex flex-column overflow-hidden"
      >
        <div
          ref="messageContainer"
          class="flex-grow-1 overflow-y-auto pa-4 message-list"
        >
          <div
            v-for="msg in chatStore.messages"
            :key="msg.id"
            class="d-flex mb-4"
            :class="[msg.sender_id === chatStore.currentUserId ? 'justify-end' : 'justify-start']"
          >
            <div
              class="message-bubble pa-3 rounded-lg"
              :class="[msg.sender_id === chatStore.currentUserId ? 'bg-primary text-white' : 'bg-grey-lighten-3']"
            >
              <div
                v-if="chatStore.activeContactId === 0 && msg.sender_id !== chatStore.currentUserId"
                class="text-caption font-weight-bold mb-1"
              >
                {{ msg.sender?.full_name || 'Сотрудник' }}
              </div>
              <div class="message-content text-body-2">
                {{ msg.content }}
              </div>
              <div class="text-right text-caption mt-1 opacity-70">
                {{ formatTime(msg.created_at) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <VDivider />
        <div class="pa-3 bg-grey-lighten-4">
          <VTextField
            v-model="newMessage"
            placeholder="Введите сообщение..."
            hide-details
            variant="solo"
            density="compact"
            @keyup.enter="send"
          >
            <template #append-inner>
              <VBtn
                icon="bx-send"
                variant="text"
                color="primary"
                :disabled="!newMessage.trim()"
                @click="send"
              />
            </template>
          </VTextField>
        </div>
      </div>
    </div>
  </VNavigationDrawer>
</template>

<style scoped>
.chat-drawer {
  z-index: 2400 !important;
}
.message-list {
  background-color: #f8f9fa;
  display: flex;
  flex-direction: column;
}
.message-bubble {
  max-width: 85%;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}
</style>
