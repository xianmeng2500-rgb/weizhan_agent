<template>
  <div class="login-page">
    <div class="login-card">
      <h2>请先登录</h2>
      <van-form @submit="handleLogin">
        <van-cell-group inset>
          <van-field v-model="form.username" label="账号" placeholder="请输入账号" :rules="[{ required: true, message: '请输入账号' }]" />
          <van-field v-model="form.password" type="password" label="密码" placeholder="请输入密码" :rules="[{ required: true, message: '请输入密码' }]" />
        </van-cell-group>
        <div style="margin: 16px">
          <van-button round block type="primary" native-type="submit" :loading="loading">登 录</van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const code = route.params.code as string

const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function handleLogin() {
  loading.value = true
  try {
    const res: any = await api.post(`/p/sites/${code}/login`, form)
    localStorage.setItem('h5_token', res.access_token)
    localStorage.setItem('h5_nickname', res.nickname)
    showSuccessToast('登录成功')
    router.replace(`/s/${code}`)
  } catch {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #f5f5f5; }
.login-card { width: 90%; max-width: 400px; background: #fff; border-radius: 12px; padding: 30px 0; overflow: hidden; }
.login-card h2 { text-align: center; margin-bottom: 20px; color: #333; }
</style>
