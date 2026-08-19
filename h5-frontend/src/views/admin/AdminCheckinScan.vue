<template>
  <div class="scan-page">
    <van-nav-bar :title="siteName || '签到核销'" left-arrow fixed placeholder @click-left="router.back()" />

    <!-- 场次选择 + 统计 -->
    <div class="session-bar">
      <div class="session-picker" @click="showSessionPicker = true">
        <van-tag type="primary" size="large" plain>场次</van-tag>
        <span class="session-name van-ellipsis">{{ currentSession ? currentSession.name : '选择签到场次' }}</span>
        <van-icon name="arrow-down" color="#969799" />
      </div>
      <div class="session-stat" v-if="currentSession">
        <span>已签到</span>
        <span class="stat-num">{{ currentSession.checked_in_count }}</span>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-bar">
      <van-button type="primary" icon="scan" block round @click="openScanner">扫码签到</van-button>
      <van-button type="default" icon="edit" block round plain @click="showManualCode = true">输入签到码</van-button>
      <van-button type="warning" icon="records" block round plain @click="openManualCheckin">补签</van-button>
    </div>

    <!-- 签到情况 -->
    <div class="records-header">
      <span>签到情况</span>
      <van-icon name="replay" :class="{ spinning: recordsLoading }" @click="refreshAll" />
    </div>

    <van-pull-refresh v-model="recordsRefreshing" @refresh="refreshAll" class="records-wrap">
      <div v-if="records.length === 0 && !recordsLoading" class="empty-wrap">
        <van-empty :description="currentSession ? '当前场次暂无签到记录' : '请先选择签到场次'" />
      </div>
      <div v-for="r in records" :key="r.id" class="record-card">
        <div class="record-avatar">{{ (r.user_name || '?').slice(0, 1) }}</div>
        <div class="record-info">
          <div class="record-name van-ellipsis">{{ r.user_name }}</div>
          <div class="record-meta">
            <span>{{ fmtTime(r.checkin_at) }}</span>
            <van-divider vertical />
            <span>{{ r.checkin_method === 'QR_SCAN' ? '扫码' : '补签' }}</span>
            <template v-if="!r.checkin_status">
              <van-divider vertical />
              <span class="revoked">已撤销</span>
            </template>
          </div>
        </div>
        <div class="record-mobile">{{ r.mobile_masked }}</div>
      </div>
      <div v-if="records.length > 0" class="list-end">
        {{ recordsFinished ? `共 ${recordsTotal} 条记录` : '上拉加载更多' }}
      </div>
    </van-pull-refresh>

    <!-- 场次选择弹层 -->
    <van-popup v-model:show="showSessionPicker" position="bottom" round>
      <div class="picker-title">选择签到场次</div>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: currentSessionId === s.id }"
          @click="selectSession(s)"
        >
          <div class="session-item-name">
            {{ s.name }}
            <van-tag v-if="!s.enabled" type="danger" plain style="margin-left: 6px">停用</van-tag>
          </div>
          <div class="session-item-meta">
            <span>{{ fmtWindow(s) }}</span>
            <span class="checked-num">已签 {{ s.checked_in_count }}</span>
          </div>
          <van-icon v-if="currentSessionId === s.id" name="success" color="#1989fa" />
        </div>
        <div v-if="sessions.length === 0" class="session-empty">尚未配置场次，请在后台管理端添加</div>
      </div>
    </van-popup>

    <!-- 手动输入签到码 -->
    <van-dialog
      v-model:show="showManualCode"
      title="输入签到码"
      show-cancel-button
      @confirm="submitManualCode"
      @open="manualCode = ''"
    >
      <van-field
        v-model="manualCode"
        placeholder="请输入用户签到码内容（ck1开头）"
        rows="2"
        autosize
        type="textarea"
        style="margin: 12px 0"
      />
    </van-dialog>

    <!-- 补签弹层 -->
    <van-popup v-model:show="showManualCheckinPopup" position="bottom" round :style="{ maxHeight: '80vh' }">
      <div class="picker-title">人工补签{{ currentSession ? ` · ${currentSession.name}` : '' }}</div>
      <van-search v-model="accountKeyword" placeholder="搜索姓名 / 手机号 / 账号" @search="doSearchAccounts" />
      <div class="account-list">
        <div
          v-for="a in accountOptions"
          :key="a.id"
          class="account-item"
          @click="confirmManualCheckin(a)"
        >
          <div class="account-name van-ellipsis">{{ a.nickname || a.username }}</div>
          <div class="account-meta">{{ a.phone || a.username }}</div>
        </div>
        <div v-if="accountSearched && accountOptions.length === 0" class="session-empty">未找到匹配的账号</div>
        <div v-else-if="!accountSearched" class="session-empty">输入关键词搜索账号后点击补签</div>
      </div>
    </van-popup>

    <!-- 扫码弹层 -->
    <van-popup v-model:show="showScanner" position="bottom" :style="{ height: '80vh' }" round @closed="stopScanner">
      <div class="scanner-title">将签到二维码对准取景框</div>
      <div class="scanner-body">
        <video ref="videoRef" class="scanner-video" playsinline muted></video>
        <div class="scanner-frame"></div>
      </div>
      <div v-if="scanError" class="scanner-error">{{ scanError }}</div>
      <div class="scanner-tip" v-else>支持用户的 H5 签到页静态二维码</div>
    </van-popup>

    <!-- 补签确认 -->
    <van-dialog
      v-model:show="showManualConfirm"
      :title="`补签确认${currentSession ? ' · ' + currentSession.name : ''}`"
      show-cancel-button
      :before-close="onManualConfirm"
    >
      <div class="manual-confirm-body">
        <div class="manual-user">
          为 <b>{{ pendingAccount ? (pendingAccount.nickname || pendingAccount.username) : '' }}</b> 补签
        </div>
        <van-field
          v-model="manualRemark"
          placeholder="补签原因（选填）"
          maxlength="100"
          show-word-limit
          type="textarea"
          rows="1"
          autosize
        />
      </div>
    </van-dialog>

    <!-- 签到结果 -->
    <van-overlay :show="showResult" @click="showResult = false">
      <div class="result-panel" @click.stop>
        <div class="result-icon" :class="resultType">
          <van-icon :name="resultIconName" size="48" color="#fff" />
        </div>
        <div class="result-title">{{ resultTitle }}</div>
        <div class="result-desc" v-if="resultDesc">{{ resultDesc }}</div>
        <van-button type="primary" round block style="margin-top: 20px" @click="showResult = false">
          继续签到
        </van-button>
      </div>
    </van-overlay>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import jsQR from 'jsqr'
import {
  getCheckinSessions,
  getCheckinRecords,
  scanCheckin,
  manualCheckin,
  searchSiteAccounts,
  errMsg,
} from '@/api/admin'

const router = useRouter()
const route = useRoute()
const siteId = Number(route.params.siteId)
const siteName = ref(String(route.query.name || ''))

// ---- 场次 ----
const sessions = ref<any[]>([])
const currentSessionId = ref<number | null>(null)
const showSessionPicker = ref(false)
const currentSession = computed(() => sessions.value.find((s) => s.id === currentSessionId.value) || null)

function selectSession(s: any) {
  currentSessionId.value = s.id
  showSessionPicker.value = false
  loadRecords(true)
}

function fmtWindow(s: any): string {
  if (!s.start_at && !s.end_at) return '不限时间'
  const fmt = (v: string) => (v ? v.replace('T', ' ').slice(5, 16) : '')
  return `${fmt(s.start_at) || '不限'} ~ ${fmt(s.end_at) || '不限'}`
}

async function loadSessions() {
  try {
    const data = await getCheckinSessions(siteId)
    sessions.value = data.items || []
    // 默认选中第一个启用的场次
    if (!currentSessionId.value && sessions.value.length) {
      const enabled = sessions.value.find((s) => s.enabled)
      currentSessionId.value = (enabled || sessions.value[0]).id
    }
  } catch (e) {
    showToast(errMsg(e))
  }
}

// ---- 签到记录 ----
const records = ref<any[]>([])
const recordsTotal = ref(0)
const recordsPage = ref(1)
const recordsFinished = ref(false)
const recordsLoading = ref(false)
const recordsRefreshing = ref(false)

async function loadRecords(reset = false) {
  if (recordsLoading.value) return
  recordsLoading.value = true
  try {
    const p = reset ? 1 : recordsPage.value + 1
    const data = await getCheckinRecords(siteId, {
      page: p,
      page_size: 20,
      session_id: currentSessionId.value ?? undefined,
    })
    if (reset) records.value = data.items
    else records.value.push(...data.items)
    recordsTotal.value = data.total
    recordsPage.value = p
    recordsFinished.value = records.value.length >= data.total
  } catch (e) {
    showToast(errMsg(e))
  } finally {
    recordsLoading.value = false
    recordsRefreshing.value = false
  }
}

async function refreshAll() {
  await Promise.all([loadSessions(), loadRecords(true)])
}

function fmtTime(v: string): string {
  return v ? v.replace('T', ' ').slice(5, 16) : '-'
}

// 触底加载
function onScroll() {
  if (recordsFinished.value || recordsLoading.value || records.value.length === 0) return
  const bottom = document.documentElement.scrollHeight - window.innerHeight - window.scrollY
  if (bottom < 60) loadRecords()
}

// ---- 签到结果展示 ----
const showResult = ref(false)
const resultType = ref<'success' | 'warn'>('success')
const resultTitle = ref('')
const resultDesc = ref('')
const resultIconName = computed(() => (resultType.value === 'success' ? 'checked' : 'warning-o'))

function showScanResult(data: any) {
  const r = data?.result
  if (r === 'SUCCESS') {
    resultType.value = 'success'
    resultTitle.value = '签到成功'
    resultDesc.value = `${data.user_name || ''} ${data.mobile_masked || ''} · ${data.session_name || ''}`
    navigator.vibrate?.(80)
  } else if (r === 'ALREADY_CHECKED_IN') {
    resultType.value = 'warn'
    resultTitle.value = '已签到'
    resultDesc.value = data.message || ''
    navigator.vibrate?.([60, 60, 60])
  } else {
    resultType.value = 'warn'
    resultTitle.value = '签到失败'
    resultDesc.value = data?.message || '二维码无效'
    navigator.vibrate?.([60, 60, 60])
  }
  showResult.value = true
}

// ---- 扫码（jsQR + 摄像头）----
const showScanner = ref(false)
const videoRef = ref<HTMLVideoElement | null>(null)
const scanError = ref('')
let stream: MediaStream | null = null
let rafId = 0
let scanning = false

async function openScanner() {
  scanError.value = ''
  showScanner.value = true
  await startScanner()
}

async function startScanner() {
  const video = videoRef.value
  if (!video) return
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment' } },
      audio: false,
    })
    video.srcObject = stream
    await video.play()
    scanning = true
    tick()
  } catch (e: any) {
    scanError.value =
      e?.name === 'NotAllowedError'
        ? '摄像头权限被拒绝，请在浏览器设置中允许访问'
        : '无法打开摄像头，可使用「输入签到码」方式'
  }
}

function stopScanner() {
  scanning = false
  cancelAnimationFrame(rafId)
  stream?.getTracks().forEach((t) => t.stop())
  stream = null
}

const canvas = document.createElement('canvas')

function tick() {
  if (!scanning) return
  const video = videoRef.value
  if (video && video.readyState === video.HAVE_ENOUGH_DATA) {
    const w = 360
    const h = Math.round((video.videoHeight / video.videoWidth) * w) || 480
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    if (ctx) {
      ctx.drawImage(video, 0, 0, w, h)
      const img = ctx.getImageData(0, 0, w, h)
      const code = jsQR(img.data, img.width, img.height, { inversionAttempts: 'dontInvert' })
      if (code?.data) {
        handleScanned(code.data)
        return
      }
    }
  }
  rafId = requestAnimationFrame(tick)
}

let lastCode = ''
let lastTime = 0

async function handleScanned(code: string) {
  // 防重复：同一内容 3 秒内不重复处理
  const now = Date.now()
  if (code === lastCode && now - lastTime < 3000) {
    rafId = requestAnimationFrame(tick)
    return
  }
  lastCode = code
  lastTime = now
  scanning = false
  try {
    const data = await scanCheckin(siteId, code, currentSessionId.value)
    showScanResult(data)
    // 刷新签到情况
    loadSessions()
    loadRecords(true)
  } catch (e) {
    showScanResult({ result: 'ERROR', message: errMsg(e, '签到请求失败') })
  }
  // 停留结果页，关闭弹层时由 @closed 停流
  showScanner.value = false
  stopScanner()
}

// ---- 手动输入签到码 ----
const showManualCode = ref(false)
const manualCode = ref('')

async function submitManualCode() {
  const code = manualCode.value.trim()
  if (!code) {
    showToast('请输入签到码')
    return
  }
  try {
    const data = await scanCheckin(siteId, code, currentSessionId.value)
    showScanResult(data)
    loadSessions()
    loadRecords(true)
  } catch (e) {
    showToast(errMsg(e))
  }
}

// ---- 人工补签 ----
const showManualCheckinPopup = ref(false)
const accountKeyword = ref('')
const accountOptions = ref<any[]>([])
const accountSearched = ref(false)

function openManualCheckin() {
  if (!sessions.value.length) {
    showToast('尚未配置签到场次')
    return
  }
  accountKeyword.value = ''
  accountOptions.value = []
  accountSearched.value = false
  showManualCheckinPopup.value = true
}

async function doSearchAccounts() {
  const kw = accountKeyword.value.trim()
  if (!kw) {
    showToast('请输入关键词')
    return
  }
  try {
    const data = await searchSiteAccounts(siteId, kw)
    accountOptions.value = data.items || []
    accountSearched.value = true
  } catch (e) {
    showToast(errMsg(e))
  }
}

const showManualConfirm = ref(false)
const pendingAccount = ref<any>(null)
const manualRemark = ref('')

async function confirmManualCheckin(account: any) {
  pendingAccount.value = account
  manualRemark.value = ''
  showManualConfirm.value = true
}

async function onManualConfirm(action: string) {
  if (action !== 'confirm') return true
  const account = pendingAccount.value
  if (!account) return true
  try {
    const data = await manualCheckin(siteId, account.id, currentSessionId.value, manualRemark.value.trim())
    showToast(data.message || '补签成功')
    showManualCheckinPopup.value = false
    loadSessions()
    loadRecords(true)
    return true
  } catch (e) {
    showToast(errMsg(e))
    return false
  }
}

onMounted(() => {
  loadSessions().then(() => loadRecords(true))
  window.addEventListener('scroll', onScroll)
})

onUnmounted(() => {
  stopScanner()
  window.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.scan-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: 30px;
}
/* 场次栏 */
.session-bar {
  margin: 10px 12px 0;
  padding: 12px 14px;
  background: #fff;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.session-picker {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.session-name {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
  max-width: 180px;
}
.session-stat {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-size: 12px;
  color: #969799;
}
.stat-num {
  font-size: 20px;
  font-weight: 700;
  color: #07c160;
}
/* 操作按钮 */
.action-bar {
  margin: 10px 12px;
  display: flex;
  gap: 8px;
}
/* 记录 */
.records-header {
  margin: 6px 16px 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: #323233;
}
.spinning {
  animation: spin 1s linear infinite;
  color: #1989fa;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.records-wrap {
  min-height: 50vh;
}
.record-card {
  margin: 8px 12px;
  padding: 12px 14px;
  background: #fff;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.record-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4a9df8, #2b6de0);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.record-info {
  flex: 1;
  min-width: 0;
}
.record-name {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}
.record-meta {
  margin-top: 4px;
  font-size: 12px;
  color: #969799;
  display: flex;
  align-items: center;
}
.revoked {
  color: #ee0a24;
}
.record-mobile {
  font-size: 12px;
  color: #969799;
  flex-shrink: 0;
}
.list-end {
  text-align: center;
  color: #c8c9cc;
  font-size: 12px;
  padding: 12px 0 20px;
}
.empty-wrap {
  padding-top: 8vh;
}
/* 弹层通用 */
.picker-title {
  text-align: center;
  font-size: 15px;
  font-weight: 600;
  padding: 14px 0 8px;
  color: #323233;
}
.session-list,
.account-list {
  max-height: 50vh;
  overflow-y: auto;
  padding-bottom: 16px;
}
.session-item {
  margin: 6px 16px;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid #ebedf0;
  display: flex;
  align-items: center;
  gap: 10px;
}
.session-item.active {
  border-color: #1989fa;
  background: #f0f7ff;
}
.session-item-name {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  font-weight: 600;
  color: #323233;
}
.session-item-meta {
  font-size: 12px;
  color: #969799;
  display: flex;
  gap: 10px;
  align-items: center;
}
.checked-num {
  color: #07c160;
}
.session-empty {
  text-align: center;
  color: #969799;
  font-size: 13px;
  padding: 24px 0;
}
.account-item {
  margin: 6px 16px;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid #ebedf0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.account-name {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
  max-width: 55%;
}
.account-meta {
  font-size: 12px;
  color: #969799;
}
.manual-confirm-body {
  padding: 12px 4px 4px;
}
.manual-user {
  text-align: center;
  font-size: 14px;
  color: #323233;
  margin-bottom: 10px;
}
/* 扫码 */
.scanner-title {
  text-align: center;
  padding: 14px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  background: #1a1a1a;
}
.scanner-body {
  position: relative;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 55vh;
  overflow: hidden;
}
.scanner-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.scanner-frame {
  position: absolute;
  width: 65vw;
  height: 65vw;
  max-width: 280px;
  max-height: 280px;
  border: 2px solid rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 0 0 100vmax rgba(0, 0, 0, 0.45);
}
.scanner-error {
  color: #ee0a24;
  text-align: center;
  padding: 20px 24px;
  font-size: 13px;
}
.scanner-tip {
  color: #969799;
  text-align: center;
  padding: 16px;
  font-size: 12px;
}
/* 结果面板 */
.result-panel {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 78vw;
  max-width: 320px;
  background: #fff;
  border-radius: 16px;
  padding: 28px 24px;
  text-align: center;
}
.result-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  margin: 0 auto 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.result-icon.success {
  background: #07c160;
}
.result-icon.warn {
  background: #ff976a;
}
.result-title {
  font-size: 18px;
  font-weight: 700;
  color: #323233;
}
.result-desc {
  margin-top: 8px;
  font-size: 13px;
  color: #969799;
  word-break: break-all;
}
</style>
