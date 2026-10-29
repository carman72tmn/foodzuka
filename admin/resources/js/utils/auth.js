import { reactive } from 'vue'

export const authState = reactive({
  token: localStorage.getItem('access_token') || null,
  user: null,
})

export const getDeviceId = () => {
  let deviceId = localStorage.getItem('device_id')

  if (!deviceId) {
    deviceId = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2) + Date.now().toString(36)
    localStorage.setItem('device_id', deviceId)
  }

  return deviceId
}

export const login = async (username, password, remember = false) => {
  const deviceId = getDeviceId()
  const params = new URLSearchParams({
    username,
    password,
    grant_type: 'password',
    device_id: deviceId,
    remember: remember ? 'true' : 'false',
  })

  let response
  try {
    response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params.toString(),
    })
  } catch (networkErr) {
    throw new Error('Не удалось подключиться к серверу. Проверьте интернет-соединение.')
  }

  if (!response.ok) {
    let errorDetail = 'Ошибка авторизации'
    try {
      const errorData = await response.json()
      if (Array.isArray(errorData.detail)) {
        errorDetail = errorData.detail.map(d => d.msg || JSON.stringify(d)).join(', ')
      } else if (typeof errorData.detail === 'object' && errorData.detail !== null) {
        errorDetail = errorData.detail.message || JSON.stringify(errorData.detail)
      } else {
        errorDetail = errorData.detail || errorDetail
      }
    } catch {
      if (response.status === 502) {
        errorDetail = 'Сервер бэкенда временно недоступен (502 Bad Gateway). Пожалуйста, повторите попытку через минуту.'
      } else if (response.status === 504) {
        errorDetail = 'Время ожидания ответа от сервера истекло (504 Gateway Timeout).'
      } else if (response.status >= 500) {
        errorDetail = `Внутренняя ошибка сервера (${response.status}).`
      } else {
        errorDetail = `Ошибка авторизации (${response.status}).`
      }
    }
    throw new Error(errorDetail)
  }

  let data
  try {
    data = await response.json()
  } catch {
    throw new Error('Некорректный формат ответа от сервера.')
  }

  authState.token = data.access_token
  localStorage.setItem('access_token', data.access_token)

  return data
}

export const logout = () => {
  authState.token = null
  authState.user = null
  localStorage.removeItem('access_token')
}

export const fetchMe = async () => {
  if (!authState.token) return null
  
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 7000)

    const response = await fetch('/api/v1/auth/me', {
      headers: {
        ...getAuthHeaders(),
      },
      signal: controller.signal,
    })
    clearTimeout(timeoutId)
    
    if (response.ok) {
      try {
        const data = await response.json()
        authState.user = data
        return data
      } catch {
        return null
      }
    } else {
      if (response.status === 401 || response.status === 403) {
        logout()
      }
      return null
    }
  } catch (e) {
    console.error('fetchMe error:', e)
    return null
  }
}

export const getAuthHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  'X-Device-Id': getDeviceId(),
  'Content-Type': 'application/json'
})

export const hasPermission = code => {
  if (!authState.user) return false
  if (authState.user.is_superuser) return true
  
  const permissions = authState.user.role?.permissions || []

  return permissions.some(p => p.code === code)
}

export const isCourierUser = () => {
  if (!authState.user) return false
  if (authState.user.is_superuser) return false
  if (authState.user.is_courier) return true
  const roleName = (authState.user.role?.name || '').toLowerCase()
  const roleCode = (authState.user.role?.code || '').toUpperCase()
  if (roleCode === 'CUR' || roleCode === 'COURIER' || roleName.includes('курьер') || roleName.includes('courier')) return true
  if (authState.user.employee?.is_courier) return true
  const empRole = (authState.user.employee?.role || '').toLowerCase()
  if (empRole.includes('курьер') || empRole.includes('courier')) return true
  return false
}

export const syncVkLinking = async () => {
  const vkUserId = localStorage.getItem('vk_user_id') || new URLSearchParams(window.location.search).get('vk_user_id')
  if (vkUserId) {
    localStorage.setItem('vk_user_id', vkUserId)
    if (authState.token) {
      console.log('[VK Link] Found VK User ID. Syncing connection with account...', vkUserId)
      try {
        const response = await fetch('/api/v1/auth/link-vk', {
          method: 'POST',
          headers: {
            ...getAuthHeaders(),
          },
          body: JSON.stringify({ vk_user_id: parseInt(vkUserId) })
        })
        if (response.ok) {
          console.log('[VK Link] VK account linked successfully')
          
          // Получаем vk_group_id для подписки на сообщения
          const settingsRes = await fetch('/api/v1/auth/vk-settings', {
            headers: getAuthHeaders()
          })
          if (settingsRes.ok) {
            const settingsData = await settingsRes.json()
            if (window.vkBridge) {
              // Запрашиваем пуши приложения
              window.vkBridge.send("VKWebAppAllowNotifications")
                .then(() => console.log('[VK Link] Push notifications allowed'))
                .catch(err => console.error('[VK Link] Push notifications permission error:', err))

              // Запрашиваем сообщения от группы
              if (settingsData.vk_group_id) {
                console.log('[VK Link] Requesting messages permission for group:', settingsData.vk_group_id)
                window.vkBridge.send("VKWebAppAllowMessagesFromGroup", { group_id: parseInt(settingsData.vk_group_id) })
                  .then(() => console.log('[VK Link] Messages from group allowed'))
                  .catch(err => console.error('[VK Link] Messages from group permission error:', err))
              }
            }
          }
        } else {
          console.error('[VK Link] Failed to link VK account on server')
        }
      } catch (e) {
        console.error('[VK Link] Error syncing VK link:', e)
      }
    }
  }
}

export const loginWithVkMiniApp = async (queryParams) => {
  const response = await fetch('/api/v1/auth/vk-miniapp-login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query_params: queryParams })
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || 'Ошибка авторизации через VK Mini App')
  }

  const data = await response.json()
  
  if (data.status === 'success') {
    authState.token = data.access_token
    localStorage.setItem('access_token', data.access_token)
    await fetchMe()
  }

  return data
}

export const linkVkMiniApp = async (username, password, queryParams) => {
  const response = await fetch('/api/v1/auth/vk-miniapp-link', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username,
      password,
      query_params: queryParams
    })
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || 'Ошибка привязки аккаунта VK')
  }

  const data = await response.json()

  if (data.status === 'success') {
    authState.token = data.access_token
    localStorage.setItem('access_token', data.access_token)
    await fetchMe()
  }

  return data
}

