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

  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || 'Ошибка авторизации')
  }

  const data = await response.json()

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
  
  const response = await fetch('/api/v1/auth/me', {
    headers: {
      ...getAuthHeaders(),
    },
  })
  
  if (response.ok) {
    const data = await response.json()
    authState.user = data
    return data
  } else {
    logout()
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
