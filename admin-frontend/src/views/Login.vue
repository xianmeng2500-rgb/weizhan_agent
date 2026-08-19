<template>
  <div class="login-page">
    <div class="login-left">
      <div class="brand">
        <h1>微站管理后台</h1>
        <p>一站式微站搭建与管理平台</p>
      </div>
    </div>
    <div class="login-right">
      <div class="login-card">
        <h2 class="login-title">欢迎登录</h2>
        <p class="login-subtitle">请输入您的账号信息</p>
        <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin" size="large">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" :prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
          </el-form-item>
          <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">
            登 录
          </el-button>
        </el-form>
        <div class="login-tip">
          <el-icon><InfoFilled /></el-icon>
          <span>如需帮助请联系:18391087372</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import api from '@/api'

const router = useRouter()
const auth = useAuthStore()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    // skipErrorToast: 登录失败的提示由本页显式处理（避免依赖全局拦截器）
    const res: any = await api.post('/auth/login', form, { skipErrorToast: true } as any)
    auth.setAuth(res.access_token, res.nickname, res.role)
    await auth.fetchMe()
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    ElMessage.error({ message: detail || '登录失败，请检查账号密码', zIndex: 3000 })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
}

/* 左侧品牌区 */
.login-left {
  flex: 1;
  background: linear-gradient(135deg, #1890ff 0%, #001529 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.login-left::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 30px 30px;
}
.brand {
  text-align: center;
  color: #fff;
  z-index: 1;
  padding: 40px;
}
.brand h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 12px;
  letter-spacing: 2px;
}
.brand p {
  font-size: 16px;
  opacity: 0.8;
  letter-spacing: 1px;
}

/* 右侧表单区 */
.login-right {
  width: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}
.login-card {
  width: 360px;
  padding: 20px;
}
.login-title {
  font-size: 26px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}
.login-subtitle {
  font-size: 14px;
  color: #909399;
  margin-bottom: 32px;
}
.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  letter-spacing: 4px;
  margin-top: 8px;
}
.login-tip {
  margin-top: 24px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #c0c4cc;
  font-size: 12px;
  justify-content: center;
}

/* 响应式 */
@media (max-width: 768px) {
  .login-left {
    display: none;
  }
  .login-right {
    width: 100%;
  }
}
</style>
