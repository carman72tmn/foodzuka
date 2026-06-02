<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import UserList from '@/views/pages/users/UserList.vue'
import RoleList from '@/views/pages/users/RoleList.vue'

const route = useRoute()
const activeTab = ref(route.query.tab || 'users')

const tabs = [
  {
    title: 'Пользователи',
    icon: 'ri-user-line',
    tab: 'users',
  },
  {
    title: 'Управление ролями',
    icon: 'ri-shield-user-line',
    tab: 'roles',
  },
]
</script>

<template>
  <div>
    <VTabs
      v-model="activeTab"
      class="v-tabs-pill mb-6"
    >
      <VTab
        v-for="item in tabs"
        :key="item.tab"
        :value="item.tab"
      >
        <VIcon
          size="20"
          start
          :icon="item.icon"
        />
        {{ item.title }}
      </VTab>
    </VTabs>

    <VWindow
      v-model="activeTab"
      class="disable-tab-transition"
    >
      <!-- Users -->
      <VWindowItem value="users">
        <UserList />
      </VWindowItem>

      <!-- Roles -->
      <VWindowItem value="roles">
        <RoleList />
      </VWindowItem>
    </VWindow>
  </div>
</template>
