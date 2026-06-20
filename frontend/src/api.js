const API_PREFIX = '/api'

let accessToken = localStorage.getItem('dynamics_access_token') || ''

export function setAccessToken(token) {
  accessToken = token || ''
  if (accessToken) {
    localStorage.setItem('dynamics_access_token', accessToken)
  } else {
    localStorage.removeItem('dynamics_access_token')
  }
}

export function getAccessToken() {
  return accessToken
}

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`
  }
  const response = await fetch(`${API_PREFIX}${path}`, {
    credentials: 'include',
    ...options,
    headers,
  })
  if (response.status === 401 && path !== '/auth/refresh' && path !== '/auth/login') {
    const refreshed = await refresh()
    if (refreshed) {
      return request(path, options)
    }
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(data.detail || data.message || `请求失败(${response.status})`)
  }
  if (response.status === 204) {
    return null
  }
  return response.json()
}

export async function login(username, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  setAccessToken(data.access_token)
  return data
}

export async function refresh() {
  try {
    const data = await request('/auth/refresh', { method: 'POST' })
    setAccessToken(data.access_token)
    return data
  } catch {
    setAccessToken('')
    return null
  }
}

export async function logout() {
  try {
    await request('/auth/logout', { method: 'POST' })
  } finally {
    setAccessToken('')
  }
}

export async function me() {
  return request('/auth/me')
}

export async function getDashboard() {
  return request('/dashboard')
}

export async function listTargets() {
  return request('/targets')
}

export async function createTarget(payload) {
  return request('/targets', { method: 'POST', body: JSON.stringify(payload) })
}

export async function updateTarget(id, payload) {
  return request(`/targets/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export async function deleteTarget(id) {
  return request(`/targets/${id}`, { method: 'DELETE' })
}

export async function listSlugs() {
  return request('/slugs')
}

export async function createSlug(payload) {
  return request('/slugs', { method: 'POST', body: JSON.stringify(payload) })
}

export async function updateSlug(id, payload) {
  return request(`/slugs/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export async function deleteSlug(id) {
  return request(`/slugs/${id}`, { method: 'DELETE' })
}

export async function listTokens(targetId) {
  return request(`/targets/${targetId}/tokens`)
}

export async function createToken(targetId, payload) {
  return request(`/targets/${targetId}/tokens`, { method: 'POST', body: JSON.stringify(payload) })
}

export async function toggleToken(tokenId, enabled) {
  return request(`/tokens/${tokenId}`, { method: 'PATCH', body: JSON.stringify({ enabled }) })
}

export async function removeToken(tokenId) {
  return request(`/tokens/${tokenId}`, { method: 'DELETE' })
}

export async function listLogs(targetId) {
  return request(`/targets/${targetId}/logs`)
}
