import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useChatStore = defineStore('chat', () => {
  const contacts = ref([])
  const messages = ref([])
  const activeContactId = ref(null) // 0 for group, or user_id
  const isDrawerOpen = ref(false)
  const ws = ref(null)
  const currentUserId = ref(null)

  const fetchMe = async () => {
    if (currentUserId.value) return
    try {
      const response = await axios.get('/api/v1/users/me', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      })

      currentUserId.value = response.data.id
    } catch (error) {
      console.error('Failed to fetch profile:', error)
    }
  }

  const unreadCount = computed(() => {
    return contacts.value.reduce((acc, c) => acc + (c.unread_count || 0), 0)
  })

  const fetchContacts = async () => {
    try {
      const response = await axios.get('/api/v1/chat/contacts', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      })

      contacts.value = response.data
    } catch (error) {
      console.error('Failed to fetch contacts:', error)
    }
  }

  const fetchMessages = async (contactId, isGroup) => {
    try {
      const response = await axios.get('/api/v1/chat/messages', {
        params: {
          receiver_id: contactId > 0 ? contactId : undefined,
          is_group: isGroup,
          limit: 100,
        },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      })

      messages.value = response.data.messages
    } catch (error) {
      console.error('Failed to fetch messages:', error)
    }
  }

  const markRead = async (contactId, isGroup) => {
    const isGrp = !!isGroup
    if (contactId === null || contactId === undefined) {
      if (!isGrp) return
    }
    try {
      await axios.post('/api/v1/chat/read', {
        sender_id: contactId > 0 ? contactId : undefined,
        is_group: isGrp,
      }, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      })

      const contact = contacts.value.find(c => c.id === contactId)
      if (contact) contact.unread_count = 0
    } catch (error) {
      // Игнорируем ошибки markRead, чтобы не забивать консоль
      // console.error('Failed to mark read:', error)
    }
  }

  const sendMessage = (content, receiverId, isGroup) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({
        action: 'send',
        content,
        receiver_id: receiverId > 0 ? receiverId : null,
        is_group: isGroup,
      }))
    }
  }

  const connectWs = () => {
    if (ws.value && (ws.value.readyState === WebSocket.OPEN || ws.value.readyState === WebSocket.CONNECTING)) return

    const token = localStorage.getItem('access_token')
    if (!token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/chat/ws?token=${token}`

    ws.value = new WebSocket(wsUrl)

    ws.value.onmessage = event => {
      const data = JSON.parse(event.data)
      if (data.type === 'new_message') {
        const msg = data.message

        const isGroupMsg = msg.is_group
        let contactId = isGroupMsg ? 0 : msg.sender_id
        
        // Если мы сами отправили сообщение, то ID контакта - это ID получателя
        if (!isGroupMsg && msg.sender_id === currentUserId.value) {
          contactId = msg.receiver_id
        }

        // If it's the current chat
        const isCurrentlyChatting = activeContactId.value === contactId

        if (isCurrentlyChatting) {
          messages.value.push(msg)
          if (isDrawerOpen.value) {
            markRead(contactId, isGroupMsg)
          }
        } else {
          // Update unread count in contacts list
          const contact = contacts.value.find(c => c.id === contactId)
          if (contact) {
            contact.unread_count = (contact.unread_count || 0) + 1
          } else {
            fetchContacts()
          }
        }
      }
    }

    ws.value.onclose = () => {
      ws.value = null
      setTimeout(connectWs, 5000)
    }

    ws.value.onerror = err => {
      console.error('WS Error:', err)
      ws.value.close()
    }
  }

  return {
    contacts,
    messages,
    activeContactId,
    isDrawerOpen,
    unreadCount,
    currentUserId,
    fetchMe,
    fetchContacts,
    fetchMessages,
    sendMessage,
    markRead,
    connectWs,
  }
})
