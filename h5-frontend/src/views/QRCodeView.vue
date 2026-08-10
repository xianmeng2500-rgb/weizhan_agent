<template>
  <div class="qrcode-page" :class="'tpl-' + siteTheme">
    <van-nav-bar
      :title="moduleTitle || '我的二维码'"
      left-arrow
      @click-left="goBack"
      :style="navBarStyle"
    />

    <van-loading v-if="loading" class="page-loading" size="32" color="var(--qrcode-accent, #667eea)" />

    <div v-else class="qrcode-body">
      <!-- 提示信息 -->
      <div v-if="hint" class="hint-banner">
        <van-icon name="info-o" size="16" />
        <span>{{ hint }}</span>
      </div>

      <!-- ===== 全部场次已签到 ===== -->
      <div v-if="status === 'done'" class="done-card">
        <div class="done-icon">
          <van-icon name="success" size="56" color="#07c160" />
        </div>
        <div class="done-title">全部场次已签到</div>
        <div class="done-tip">感谢您的参与</div>
      </div>

      <!-- ===== 无权限/未开启/未报名 状态 ===== -->
      <div v-else-if="status === 'not_registered'" class="state-card">
        <van-icon name="warning-o" size="48" color="#ee0a24" />
        <div class="state-title">暂未报名</div>
        <div class="state-tip">完成活动报名后，可出示二维码签到</div>
      </div>
      <div v-else-if="status === 'disabled'" class="state-card">
        <van-icon name="closed-eye" size="48" color="#969799" />
        <div class="state-title">签到未开启</div>
        <div class="state-tip">当前活动暂未开放签到</div>
      </div>
      <div v-else-if="status === 'no_sessions'" class="state-card">
        <van-icon name="info-o" size="48" color="#969799" />
        <div class="state-title">暂无签到场次</div>
        <div class="state-tip">管理员尚未配置签到场次</div>
      </div>

      <!-- ===== 有待签到场次：展示二维码 + 场次列表 ===== -->
      <template v-else>
        <!-- 二维码卡片 -->
        <div class="qrcode-card">
          <div class="qr-image-wrap">
            <img v-if="qrDataUrl" :src="qrDataUrl" alt="签到二维码" class="qr-image" />
            <div v-else class="qr-empty">
              <van-icon name="qr" size="48" color="#ccc" />
              <span>二维码加载中…</span>
            </div>
          </div>
          <div class="qr-tip">请向工作人员出示此二维码</div>
        </div>

        <!-- 场次列表 -->
        <div v-if="sessions.length > 0" class="sessions-card">
          <div class="sessions-title">签到场次</div>
          <div class="sessions-list">
            <div v-for="s in sessions" :key="s.id" class="session-item">
              <div class="session-left">
                <div class="session-name">{{ s.name }}</div>
                <div class="session-time" v-if="s.start_at || s.end_at">
                  {{ s.start_at ? fmtTime(s.start_at) : '不限' }} ~ {{ s.end_at ? fmtTime(s.end_at) : '不限' }}
                </div>
                <div class="session-time" v-else>不限时间</div>
              </div>
              <div class="session-right">
                <van-tag v-if="s.status === 'done'" type="success" size="medium">已签到</van-tag>
                <van-tag v-else-if="s.status === 'not_started'" type="warning" size="medium">未开始</van-tag>
                <van-tag v-else-if="s.status === 'ended'" type="default" size="medium">已结束</van-tag>
                <van-tag v-else-if="s.status === 'disabled'" type="default" size="medium">已停用</van-tag>
                <van-tag v-else type="primary" size="medium">待签到</van-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- 个人信息 -->
        <div v-if="displayFields.length" class="info-card">
          <div class="info-title">个人信息</div>
          <div class="info-list">
            <div v-if="displayFields.includes('username')" class="info-item">
              <span class="info-label">姓名/账号</span>
              <span class="info-value">{{ profile.username || '-' }}</span>
            </div>
            <div v-if="displayFields.includes('phone')" class="info-item">
              <span class="info-label">手机号</span>
              <span class="info-value">{{ maskPhone(profile.phone) }}</span>
            </div>
            <div v-if="displayFields.includes('nickname')" class="info-item">
              <span class="info-label">昵称</span>
              <span class="info-value">{{ profile.nickname || '-' }}</span>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div class="bottom-safe"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import QRCode from 'qrcode'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const moduleId = route.params.moduleId as string
const code = route.params.code as string

const loading = ref(true)
const moduleTitle = ref('')
const siteTheme = ref('classic')
const hint = ref('')
const displayFields = ref<string[]>([])
const profile = ref({ username: '', phone: '', nickname: '' })
const qrDataUrl = ref('')
const status = ref('pending')
const sessions = ref<any[]>([])

const navBarStyle = ref({})

function maskPhone(phone: string): string {
  if (!phone || phone.length < 7) return phone || '-'
  return phone.slice(0, 3) + '****' + phone.slice(-4)
}

function fmtTime(t: string | null): string {
  if (!t) return '-'
  return String(t).replace('T', ' ').slice(0, 16)
}

async function loadData() {
  loading.value = true
  try {
    const [mod, siteInfo, accountProfile]: any[] = await Promise.all([
      api.get(`/p/modules/${moduleId}`),
      api.get(`/p/sites/${code}`),
      api.get(`/p/sites/${code}/account/profile`).catch(() => null),
    ])

    moduleTitle.value = mod.title || '我的二维码'
    siteTheme.value = siteInfo.template || 'classic'

    navBarStyle.value = siteTheme.value === 'dark'
      ? { '--van-nav-bar-background': '#1a1a2e', '--van-nav-bar-text-color': '#e0e0e0', '--van-nav-bar-icon-color': '#e0e0e0' }
      : {}

    const config = mod.qrcode_config || {}
    hint.value = config.hint || ''
    displayFields.value = config.display_fields || []

    if (accountProfile) {
      profile.value = accountProfile
    }

    // 查询签到状态（多场次）
    let checkinInfo: any = null
    try {
      checkinInfo = await api.get(`/p/sites/${code}/checkin/status`)
    } catch (_) {
      checkinInfo = null
    }

    if (checkinInfo) {
      status.value = checkinInfo.status || 'pending'
      sessions.value = checkinInfo.sessions || []
    }

    // 待签到状态：获取后端生成的静态签到码并渲染二维码
    if (status.value === 'pending' || !checkinInfo) {
      let qrContent = ''
      if (checkinInfo) {
        try {
          const qrRes: any = await api.get(`/p/sites/${code}/checkin/qrcode`)
          qrContent = qrRes.code || ''
        } catch (_) {
          qrContent = ''
        }
      }
      if (!qrContent) {
        qrContent = `wz:${code}:${profile.value.username || ''}`
      }
      qrDataUrl.value = await QRCode.toDataURL(qrContent, {
        width: 260,
        margin: 2,
        color: { dark: '#1a1a1a', light: '#ffffff' },
      })
    }
  } catch (err: any) {
    if (err.response?.status === 401) {
      showToast('请先登录')
      router.push(`/s/${code}/login`)
    } else if (err.response?.status === 403) {
      showToast(err.response.data?.detail || '无权限访问')
    } else {
      showToast('加载失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push(`/s/${code}`)
}

onMounted(loadData)
</script>

<style scoped>
.qrcode-page {
  min-height: 100vh;
  background: #f5f7fa;
}

/* 主题 */
.tpl-classic { --qrcode-accent: #667eea; --qrcode-accent-light: #eef0fd; }
.tpl-dark {
  --qrcode-accent: #5dcaa5;
  --qrcode-accent-light: rgba(93, 202, 165, 0.12);
  background: #0f0f1a;
  color: #e0e0e0;
}
.tpl-festive {
  --qrcode-accent: #e74c3c;
  --qrcode-accent-light: rgba(231, 76, 60, 0.08);
}

.page-loading {
  display: flex;
  justify-content: center;
  padding-top: 120px;
}

/* ===== 主体 ===== */
.qrcode-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

/* ===== 提示横幅 ===== */
.hint-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  max-width: 360px;
  padding: 12px 16px;
  background: var(--qrcode-accent-light);
  border-radius: 10px;
  font-size: 14px;
  color: var(--qrcode-accent);
  line-height: 1.5;
}
.tpl-dark .hint-banner { color: #5dcaa5; }

/* ===== 二维码卡片 ===== */
.qrcode-card {
  width: 100%;
  max-width: 320px;
  background: #fff;
  border-radius: 20px;
  padding: 32px 24px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.tpl-dark .qrcode-card {
  background: #1a1a2e;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

.qr-image-wrap {
  width: 220px;
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  border: 3px solid var(--qrcode-accent);
  padding: 8px;
  background: #fff;
}

.qr-image {
  width: 100%;
  height: 100%;
}

.qr-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #ccc;
  font-size: 13px;
}

.qr-tip {
  margin-top: 16px;
  font-size: 13px;
  color: #999;
}

/* ===== 场次列表卡片 ===== */
.sessions-card {
  width: 100%;
  max-width: 360px;
  background: #fff;
  border-radius: 14px;
  padding: 16px 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.tpl-dark .sessions-card {
  background: #1a1a2e;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}

.sessions-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}
.tpl-dark .sessions-title { color: #e0e0e0; border-color: #2a2a3e; }

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.session-left {
  flex: 1;
  min-width: 0;
}

.session-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}
.tpl-dark .session-name { color: #e0e0e0; }

.session-time {
  margin-top: 2px;
  font-size: 12px;
  color: #999;
}

.session-right {
  flex-shrink: 0;
}

/* ===== 已签到结果态 ===== */
.done-card {
  width: 100%;
  max-width: 320px;
  background: #fff;
  border-radius: 20px;
  padding: 44px 24px 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.tpl-dark .done-card { background: #1a1a2e; }
.done-icon {
  width: 92px;
  height: 92px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(7, 193, 96, 0.1);
}
.done-title {
  margin-top: 16px;
  font-size: 20px;
  font-weight: 700;
  color: #07c160;
}
.done-tip {
  margin-top: 8px;
  font-size: 13px;
  color: #999;
}

/* ===== 状态卡片 ===== */
.state-card {
  width: 100%;
  max-width: 320px;
  background: #fff;
  border-radius: 20px;
  padding: 44px 24px 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.tpl-dark .state-card { background: #1a1a2e; }
.state-title {
  margin-top: 10px;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}
.tpl-dark .state-title { color: #e0e0e0; }
.state-tip {
  font-size: 13px;
  color: #999;
  text-align: center;
}

/* ===== 个人信息卡片 ===== */
.info-card {
  width: 100%;
  max-width: 320px;
  background: #fff;
  border-radius: 14px;
  padding: 16px 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}
.tpl-dark .info-card {
  background: #1a1a2e;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}

.info-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}
.tpl-dark .info-title { color: #e0e0e0; border-color: #2a2a3e; }

.info-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 14px;
  color: #999;
}

.info-value {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}
.tpl-dark .info-value { color: #e0e0e0; }

.bottom-safe {
  height: calc(24px + env(safe-area-inset-bottom));
}
</style>
