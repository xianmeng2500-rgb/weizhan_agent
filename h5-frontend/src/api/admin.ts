/**
 * 手机端签到管理（管理员）API
 * 独立 axios 实例：token 与 H5 用户端(h5_token)隔离，存储 key 为 m_admin_token
 */
import axios from 'axios'

export const ADMIN_TOKEN_KEY = 'm_admin_token'
export const ADMIN_NICKNAME_KEY = 'm_admin_nickname'

export function getAdminToken(): string | null {
  return localStorage.getItem(ADMIN_TOKEN_KEY)
}

export function clearAdminAuth() {
  localStorage.removeItem(ADMIN_TOKEN_KEY)
  localStorage.removeItem(ADMIN_NICKNAME_KEY)
}

export const adminRequest = axios.create({ baseURL: '/api/v1', timeout: 30000 })

adminRequest.interceptors.request.use((config) => {
  const token = getAdminToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

adminRequest.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const { status, config } = error.response
      const url = config?.url || ''
      if (status === 401 && !url.includes('/auth/login')) {
        clearAdminAuth()
        window.location.href = '/m/login'
        return Promise.reject(error)
      }
    }
    return Promise.reject(error)
  }
)

export function errMsg(error: any, fallback = '请求失败，请重试'): string {
  return error?.response?.data?.detail || error?.message || fallback
}

// ---------- 认证 ----------
export function adminLogin(username: string, password: string) {
  return adminRequest.post<any, any>('/auth/login', { username, password })
}

// ---------- 签到管理 ----------
export function getCheckinProjects(params?: { page?: number; page_size?: number; keyword?: string }) {
  return adminRequest.get<any, any>('/checkin/projects', { params })
}

export function getCheckinSessions(siteId: number) {
  return adminRequest.get<any, any>(`/checkin/projects/${siteId}/sessions`)
}

export function getCheckinRecords(siteId: number, params?: {
  page?: number
  page_size?: number
  session_id?: number
  keyword?: string
}) {
  return adminRequest.get<any, any>(`/checkin/projects/${siteId}/records`, { params })
}

export function scanCheckin(siteId: number, code: string, sessionId?: number | null) {
  return adminRequest.post<any, any>(`/checkin/projects/${siteId}/scan`, {
    code,
    session_id: sessionId ?? undefined,
  })
}

export function manualCheckin(siteId: number, accountId: number, sessionId?: number | null, remark?: string) {
  return adminRequest.post<any, any>(`/checkin/projects/${siteId}/manual`, {
    account_id: accountId,
    session_id: sessionId ?? undefined,
    remark: remark || undefined,
  })
}

// 补签时远程搜索微站账号
export function searchSiteAccounts(siteId: number, keyword: string) {
  return adminRequest.get<any, any>(`/sites/${siteId}/accounts`, {
    params: { keyword, page: 1, page_size: 20 },
  })
}
