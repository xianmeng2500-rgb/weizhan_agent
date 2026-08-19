<template>
  <div class="admin-login-page">
    <div class="login-header">
      <div class="logo-circle">
        <van-icon name="passed" size="36" color="#fff" />
      </div>
      <h2>签到核销</h2>
      <p class="sub">请使用后台管理账号登录</p>
    </div>

    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="username"
          name="username"
          label="账号"
          placeholder="请输入管理账号"
          :rules="[{ required: true, message: '请输入账号' }]"
          clearable
        />
        <van-field
          v-model="password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请输入密码' }]"
          clearable
        />
      </van-cell-group>
      <div class="submit-wrap">
        <van-button round block type="primary" native-type="submit" :loading="loading">
          登 录
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { adminLogin, ADMIN_TOKEN_KEY, ADMIN_NICKNAME_KEY, errMsg } from '@/api/admin'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function onSubmit() {
  loading.value = true
  try {
    const data = await adminLogin(username.value.trim(), password.value)
    localStorage.setItem(ADMIN_TOKEN_KEY, data.access_token)
    localStorage.setItem(ADMIN_NICKNAME_KEY, data.nickname || '')
    showToast('登录成功')
    router.replace('/m/checkin')
  } catch (e) {
    showToast(errMsg(e, '登录失败'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-login-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #2b6de0 0%, #5c94e8 40%, #f5f6fa 100%);
  padding-top: 18vh;
}
.login-header {
  text-align: center;
  color: #fff;
  margin-bottom: 32px;
}
.logo-circle {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
}
.login-header h2 {
  margin: 0;
  font-size: 22px;
}
.sub {
  margin: 8px 0 0;
  font-size: 13px;
  opacity: 0.85;
}
.submit-wrap {
  margin: 24px 16px;
}
</style>
