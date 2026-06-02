<script setup>
import { onMounted } from 'vue'
import { useTheme } from 'vuetify'
import { appTimezone, appOffset } from '@/utils/date'

const { global: globalTheme } = useTheme()

onMounted(async () => {
  // Загрузка настроек iiko для синхронизации часового пояса
  try {
    const response = await fetch('/api/v1/iiko/settings/')
    if (response.ok) {
      const data = await response.json()
      
      if (data && data.timezone_name) {
        appTimezone.value = data.timezone_name
        localStorage.setItem('app_timezone', data.timezone_name)
      }
      
      if (data && data.manual_timezone) {
        const offsetMatch = data.manual_timezone.match(/([+-])(\d+)/)
        if (offsetMatch) {
          const sign = offsetMatch[1] === '-' ? -1 : 1
          const hours = parseInt(offsetMatch[2])
          
          appOffset.value = sign * hours
          localStorage.setItem('app_offset', appOffset.value.toString())
        }
      } else {
        appOffset.value = 0
        localStorage.setItem('app_offset', '0')
      }
    }
  } catch (error) {
    console.error('Failed to load iiko settings for timezone (Employee):', error)
  }
})
</script>

<template>
  <VApp>
    <RouterView />
  </VApp>
</template>

<style>
/* Можно добавить специфичные стили для панели сотрудников */
</style>
