<template>
  <div class="login-page" :class="'tpl-' + (site.template || 'classic')" :style="pageStyle">
    <!-- KV 区域 -->
    <div class="kv-area" v-if="site.kv_image">
      <img :src="site.kv_image" class="kv-image" />
    </div>

    <!-- 登录卡片 -->
    <div class="login-card" :class="{ 'has-kv': !!site.kv_image }">
      <div class="brand" v-if="!site.kv_image">
        <div class="brand-logo" v-if="!site.kv_image">{{ (site.name || '微站').charAt(0) }}</div>
        <h1 class="brand-title">{{ site.name || '欢迎登录' }}</h1>
        <p class="brand-sub">请登录后继续访问</p>
      </div>
      <div class="brand compact" v-else>
        <h1 class="brand-title">{{ site.name || '欢迎登录' }}</h1>
        <p class="brand-sub">请登录后继续访问</p>
      </div>

      <van-form @submit="handleLogin">
        <template v-if="loginFields.length">
          <div class="field-wrap" v-for="(field, idx) in loginFields" :key="field.key">
            <van-field
              v-model="loginInputs[idx]"
              label=""
              :placeholder="`请输入${field.display_name}`"
              :left-icon="field.key === 'phone' ? 'phone-o' : 'user-o'"
              :type="field.type === 'number' ? 'number' : 'text'"
              :rules="[{ required: true, message: `请输入${field.display_name}` }]"
            />
          </div>
        </template>
        <div class="field-wrap" v-if="requirePassword">
          <van-field
            v-model="form.password"
            type="password"
            label=""
            placeholder="请输入密码"
            left-icon="lock"
            :rules="[{ required: true, message: '请输入密码' }]"
          />
        </div>

        <div class="submit-wrap">
          <van-button round block type="primary" native-type="submit" :loading="loading" class="login-btn">
            登 录
          </van-button>
        </div>
      </van-form>

      <p class="footer-tip" v-if="loadError">微站信息加载失败，仍可尝试登录</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const code = route.params.code as string

const loading = ref(false)
const loadError = ref(false)
const requirePassword = ref(true)
const loginFields = ref<Array<any>>([])
const loginInputs = reactive<string[]>([])
const form = reactive({ username: '', password: '' })
const site = ref<any>({
  template: 'classic',
  name: '',
  kv_image: '',
  background_image: '',
  background_color: '',
})

const pageStyle = computed(() => {
  const s = site.value
  if (s.background_image) {
    return {
      backgroundImage: `linear-gradient(rgba(0,0,0,0.18), rgba(0,0,0,0.18)), url(${s.background_image})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
    }
  }
  if (s.background_color) {
    return { background: s.background_color }
  }
  return {}
})

async function loadSite() {
  try {
    const res: any = await api.get(`/p/sites/${code}`)
    site.value = res
    requirePassword.value = res.login_require_password !== false
    loginFields.value = res.login_fields_config || [{ key: 'username', display_name: '账号', type: 'text' }]
    // 初始化输入数组
    loginInputs.length = 0
    loginFields.value.forEach(() => loginInputs.push(''))
  } catch {
    loadError.value = true
    // 加载失败时使用默认账号登录
    loginFields.value = [{ key: 'username', display_name: '账号', type: 'text' }]
    loginInputs.length = 0
    loginInputs.push('')
  }
}

async function handleLogin() {
  // 检查至少填写了一个登录字段
  const hasValue = loginInputs.some((v) => v && v.trim())
  if (!hasValue) {
    showFailToast('请至少填写一个登录字段')
    return
  }
  if (requirePassword.value && !form.password) {
    showFailToast('请输入密码')
    return
  }

  loading.value = true
  try {
    const reqData: any = {}
    if (requirePassword.value) reqData.password = form.password
    const customFields: Record<string, string> = {}

    // 遍历所有配置的登录字段，收集用户输入
    loginFields.value.forEach((field: any, idx: number) => {
      const val = (loginInputs[idx] || '').trim()
      if (!val) return

      if (field.key === 'username') {
        reqData.username = val
      } else if (field.key === 'phone') {
        // 如果后端没有 username，用 phone 作为主标识
        if (!reqData.username) reqData.username = val
        reqData.login_field = reqData.login_field || 'phone'
      } else {
        // 自定义字段
        if (!reqData.username) reqData.username = val
        reqData.login_field = reqData.login_field || 'custom'
        customFields[field.custom_key || field.key] = val
      }
    })

    if (Object.keys(customFields).length) {
      reqData.custom_fields = customFields
    }

    const res: any = await api.post(`/p/sites/${code}/login`, reqData)
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

onMounted(loadSite)
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20px 40px;
  position: relative;
  overflow-x: hidden;
}

/* 模板背景 */
.tpl-classic { background: linear-gradient(160deg, #667eea 0%, #764ba2 100%); }
.tpl-dark { background: linear-gradient(160deg, #1a1a2e 0%, #16213e 100%); }
.tpl-festive { background: linear-gradient(160deg, #c0392b 0%, #e74c3c 100%); }

/* KV 区域 */
.kv-area {
  width: 100vw;
  margin-left: calc(50% - 50vw);
  max-height: 42vh;
  overflow: hidden;
  border-bottom-left-radius: 28px;
  border-bottom-right-radius: 28px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.25);
}
.kv-image { width: 100%; display: block; object-fit: cover; max-height: 42vh; }

/* 登录卡片 */
.login-card {
  width: 100%;
  max-width: 380px;
  margin-top: 36px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 28px 22px 24px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.22);
}
.login-card.has-kv { margin-top: -38px; position: relative; z-index: 2; }

.brand { text-align: center; margin-bottom: 22px; }
.brand.compact { margin-bottom: 18px; }
.brand-logo {
  width: 64px; height: 64px; margin: 0 auto 12px;
  border-radius: 18px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff; font-size: 28px; font-weight: bold;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.45);
}
.brand-title { font-size: 22px; font-weight: 700; color: #1f2330; letter-spacing: 1px; }
.brand-sub { margin-top: 6px; font-size: 13px; color: #8a8f9c; }

/* 表单 */
.field-wrap {
  background: #f4f5f8;
  border-radius: 12px;
  margin-bottom: 14px;
  overflow: hidden;
}
.field-wrap :deep(.van-field) { background: transparent; padding: 12px 14px; }
.field-wrap :deep(.van-field__left-icon) { color: #667eea; margin-right: 8px; }

.submit-wrap { margin-top: 8px; }
.login-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 4px;
  height: 46px;
  box-shadow: 0 10px 24px rgba(102, 126, 234, 0.4);
}
.login-btn:active { opacity: 0.9; }

.footer-tip { margin-top: 14px; text-align: center; font-size: 12px; color: #b0b4be; }
</style>
