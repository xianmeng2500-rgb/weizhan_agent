import axios from 'axios'
import { useAuthStore } from '@/store/auth'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 请求拦截: 添加token
request.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// 响应拦截: 统一错误处理
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 调用方显式标记 skipErrorToast 的错误不在此统一提示（由调用方自行处理）
    if ((error.config as any)?.skipErrorToast) {
      return Promise.reject(error)
    }
    if (error.response) {
      const { status, data } = error.response
      // 登录接口 401（用户名/密码错误）不应触发「登录已过期」跳转
      const isLoginReq = String(error.config?.url || '').includes('/auth/login')
      if (status === 401 && !isLoginReq) {
        const auth = useAuthStore()
        auth.clear()
        ElMessage.error('登录已过期，请重新登录')
        window.location.href = '/admin/login'
      } else {
        // 去掉后端计费错误码前缀（如 CREDIT_INSUFFICIENT:xxx）
        const detail = String(data?.detail || '').replace(/^(CREDIT_INSUFFICIENT|MEMBERSHIP_EXPIRED|INSUFFICIENT_BALANCE):/, '')
        ElMessage.error({ message: detail || '请求失败', zIndex: 3000 })
      }
    } else if (error.code === 'ECONNABORTED' || /timeout/i.test(String(error.message))) {
      ElMessage.error({ message: '请求超时，AI 生图通常需 10-60 秒，请稍后重试', zIndex: 3000 })
    } else {
      ElMessage.error({ message: '网络错误，请检查网络后重试', zIndex: 3000 })
    }
    return Promise.reject(error)
  }
)

export default request
