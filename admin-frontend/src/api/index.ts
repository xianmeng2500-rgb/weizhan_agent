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
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        const auth = useAuthStore()
        auth.clear()
        ElMessage.error('登录已过期，请重新登录')
        window.location.href = '/admin/login'
      } else {
        ElMessage.error(data?.detail || '请求失败')
      }
    } else {
      ElMessage.error('网络错误')
    }
    return Promise.reject(error)
  }
)

export default request
