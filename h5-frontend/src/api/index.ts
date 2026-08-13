import axios from 'axios'
import { showToast } from 'vant'

const request = axios.create({ baseURL: '', timeout: 30000 })

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('h5_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        // 已在登录页或登录接口返回 401，不跳转，由调用方处理
        const path = window.location.pathname
        const isLoginPage = path.includes('/login')
        const isLoginApi = (error.config?.url || '').includes('/login')
        if (isLoginPage || isLoginApi) {
          showToast(data?.detail || '登录失败')
          return Promise.reject(error)
        }
        // 需要登录 - 跳转登录页
        const code = path.match(/\/s\/([^/]+)/)?.[1] || ''
        if (code) {
          localStorage.removeItem('h5_token')
          localStorage.removeItem('h5_nickname')
          window.location.href = `/s/${code}/login`
          return Promise.reject(error)
        }
      }
      showToast(data?.detail || '请求失败')
    } else {
      showToast('网络错误')
    }
    return Promise.reject(error)
  }
)

export default request
