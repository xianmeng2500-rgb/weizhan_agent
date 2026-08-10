<template>
  <div class="checkin-detail">
    <div class="page-head">
      <el-button :icon="ArrowLeft" link @click="$router.push('/checkin')">返回签到管理</el-button>
      <span class="head-title">{{ siteName }} · 签到管理</span>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- ============ 签到设置（场次管理） ============ -->
      <el-tab-pane label="签到设置" name="config">
        <div class="session-header">
          <span class="session-tip">配置签到场次（每场有独立时间窗，用户可签到多场）</span>
          <el-button type="primary" :icon="Plus" @click="openSessionDialog()">添加场次</el-button>
        </div>

        <el-table :data="sessions" v-loading="sessionsLoading" stripe style="width: 100%; margin-top: 12px">
          <el-table-column prop="sort_order" label="排序" width="70" align="center" />
          <el-table-column prop="name" label="场次名称" min-width="160" />
          <el-table-column label="签到时间窗" min-width="280">
            <template #default="{ row }">
              <span v-if="row.start_at || row.end_at">
                {{ row.start_at ? fmtTime(row.start_at) : '不限' }} ~ {{ row.end_at ? fmtTime(row.end_at) : '不限' }}
              </span>
              <span v-else class="text-muted">不限</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="row.enabled ? 'success' : 'info'" size="small">{{ row.enabled ? '启用' : '停用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="checked_in_count" label="已签到" width="90" align="center" />
          <el-table-column label="操作" width="160" fixed="right" align="center">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openSessionDialog(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="deleteSession(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="form-tip" style="margin-top: 16px">
          签到总开关在「微站管理 → 编辑微站」中控制（开启签到系统）。每场签到独立计时，用户可在不同场次分别签到。
        </div>
      </el-tab-pane>

      <!-- ============ 扫码签到 ============ -->
      <el-tab-pane label="扫码签到" name="scan">
        <div class="scan-session-bar">
          <span class="bar-label">当前核销场次：</span>
          <el-select v-model="scanSessionId" placeholder="选择场次" style="width: 240px" @change="onScanSessionChange">
            <el-option
              v-for="s in sessions"
              :key="s.id"
              :label="`${s.name}${s.enabled ? '' : '（已停用）'}`"
              :value="s.id"
            />
          </el-select>
          <el-tag v-if="currentSession" :type="sessionTimeTag" size="small" style="margin-left: 8px">
            {{ sessionTimeHint }}
          </el-tag>
        </div>

        <div class="scan-layout">
          <el-card shadow="never" class="scan-card">
            <template #header>
              <div class="scan-card-header">
                <span>扫码核销</span>
                <el-radio-group v-model="scanMode" size="small" @change="onScanModeChange">
                  <el-radio-button value="box">扫码盒子</el-radio-button>
                  <el-radio-button value="camera">摄像头</el-radio-button>
                </el-radio-group>
              </div>
            </template>

            <!-- 扫码盒子 -->
            <div v-if="scanMode === 'box'" class="box-mode" @click="focusBoxInput">
              <div class="box-icon">▣</div>
              <div class="box-hint">扫码盒子模式：对准二维码扫描，设备会自动输入并核销</div>
              <input
                ref="boxInputRef"
                v-model="boxInput"
                class="box-input"
                placeholder="扫码后自动识别…"
                @keyup.enter="submitBoxCode"
              />
              <el-button type="primary" size="small" style="margin-top: 12px" @click="focusBoxInput">聚焦输入框</el-button>
            </div>

            <!-- 摄像头 -->
            <div v-if="scanMode === 'camera'" class="camera-mode">
              <div v-if="cameraReady" class="camera-wrap">
                <video ref="videoRef" class="camera-video" autoplay muted playsinline></video>
                <div class="camera-tip">将二维码对准摄像头</div>
              </div>
              <div v-else class="camera-unavailable">
                <el-icon :size="40"><VideoCamera /></el-icon>
                <p>{{ cameraError || '当前浏览器不支持摄像头扫码，请使用扫码盒子模式' }}</p>
                <el-button size="small" @click="initCamera">重试</el-button>
              </div>
            </div>

            <!-- 手动输入备用 -->
            <div class="manual-row">
              <el-input v-model="manualCode" placeholder="无法扫码时，可在此手动输入二维码内容" clearable style="width: 300px" @keyup.enter="submitManualCode" />
              <el-button @click="submitManualCode">核销</el-button>
            </div>
          </el-card>

          <!-- 核验结果 -->
          <el-card shadow="never" class="result-card" :class="resultClass" v-if="result">
            <template #header>
              <div class="result-title">
                <el-icon v-if="result.result === 'SUCCESS'"><CircleCheckFilled style="color: #67c23a" /></el-icon>
                <el-icon v-else-if="result.result === 'ALREADY_CHECKED_IN'"><WarningFilled style="color: #e6a23c" /></el-icon>
                <el-icon v-else><CircleCloseFilled style="color: #f56c6c" /></el-icon>
                <span>{{ result.message }}</span>
              </div>
            </template>
            <div v-if="result.user_name" class="result-body">
              <div class="result-item" v-if="result.session_name"><span>场次</span>{{ result.session_name }}</div>
              <div class="result-item"><span>姓名</span>{{ result.user_name }}</div>
              <div class="result-item" v-if="result.mobile_masked"><span>手机号</span>{{ result.mobile_masked }}</div>
              <div class="result-item" v-if="result.checkin_at"><span>签到时间</span>{{ fmtTime(result.checkin_at) }}</div>
            </div>
            <div v-else class="result-body">
              <div class="result-item"><span>提示</span>{{ result.message }}</div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- ============ 签到记录 ============ -->
      <el-tab-pane label="签到记录" name="records">
        <div class="records-toolbar">
          <el-select v-model="recQuery.session_id" placeholder="全部场次" clearable style="width: 150px" @change="loadRecords(1)">
            <el-option v-for="s in sessions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
          <el-select v-model="recQuery.status" placeholder="全部状态" clearable style="width: 130px" @change="loadRecords(1)">
            <el-option label="有效" :value="1" />
            <el-option label="已撤销" :value="0" />
          </el-select>
          <el-select v-model="recQuery.method" placeholder="全部方式" clearable style="width: 140px" @change="loadRecords(1)">
            <el-option label="扫码签到" value="QR_SCAN" />
            <el-option label="人工补签" value="MANUAL" />
          </el-select>
          <el-input v-model="recQuery.keyword" placeholder="姓名/手机号" clearable style="width: 200px" @keyup.enter="loadRecords(1)" />
          <el-button type="primary" @click="loadRecords(1)">查询</el-button>
          <div class="toolbar-right">
            <el-button type="success" :icon="Plus" @click="openManual">人工补签</el-button>
            <el-button :icon="Download" @click="exportRecords">导出</el-button>
          </div>
        </div>

        <el-table :data="records" v-loading="recordsLoading" stripe style="width: 100%">
          <el-table-column prop="user_name" label="姓名" min-width="110" />
          <el-table-column prop="mobile_masked" label="手机号" width="130" />
          <el-table-column prop="session_name" label="场次" width="130" />
          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="row.checkin_status ? 'success' : 'info'" size="small">{{ row.checkin_status ? '已签到' : '已撤销' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="签到时间" width="170">
            <template #default="{ row }">{{ fmtTime(row.checkin_at) }}</template>
          </el-table-column>
          <el-table-column label="方式" width="100" align="center">
            <template #default="{ row }">{{ row.checkin_method === 'QR_SCAN' ? '扫码' : '人工补签' }}</template>
          </el-table-column>
          <el-table-column prop="operator_name" label="操作人" width="110" />
          <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
          <el-table-column label="操作" width="90" fixed="right" align="center">
            <template #default="{ row }">
              <el-button v-if="row.checkin_status" link type="danger" size="small" @click="openRevoke(row)">撤销</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="recPage"
          v-model:page-size="recPageSize"
          :total="recTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          class="pagination"
          @current-change="loadRecords()"
          @size-change="loadRecords(1)"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 场次新增/编辑弹窗 -->
    <el-dialog v-model="sessionDialog.visible" :title="sessionDialog.isEdit ? '编辑场次' : '添加场次'" width="480px">
      <el-form :model="sessionDialog.form" label-width="100px">
        <el-form-item label="场次名称" required>
          <el-input v-model="sessionDialog.form.name" placeholder="如：上午场、下午场、Day1" maxlength="64" show-word-limit />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker v-model="sessionDialog.form.start_at" type="datetime" placeholder="不限" value-format="YYYY-MM-DDTHH:mm:ss" clearable style="width: 240px" />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker v-model="sessionDialog.form.end_at" type="datetime" placeholder="不限" value-format="YYYY-MM-DDTHH:mm:ss" clearable style="width: 240px" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="sessionDialog.form.sort_order" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="sessionDialog.form.enabled" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sessionDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="sessionDialog.saving" @click="saveSession">保存</el-button>
      </template>
    </el-dialog>

    <!-- 人工补签弹窗 -->
    <el-dialog v-model="manualVisible" title="人工补签" width="460px">
      <el-form label-width="90px">
        <el-form-item label="签到场次">
          <el-select v-model="manualSessionId" placeholder="选择场次" style="width: 100%">
            <el-option v-for="s in sessions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="查找账号">
          <el-select
            v-model="manualAccountId"
            filterable
            remote
            :remote-method="searchAccounts"
            :loading="searchingAccounts"
            placeholder="输入姓名/账号/手机号搜索"
            style="width: 100%"
          >
            <el-option
              v-for="a in accountOptions"
              :key="a.id"
              :label="`${a.nickname || a.username}（${maskPhone(a.phone)}）`"
              :value="a.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="补签原因">
          <el-input v-model="manualRemark" type="textarea" :rows="2" placeholder="必填，例如：现场纸质名单核验通过" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="manualVisible = false">取消</el-button>
        <el-button type="primary" :loading="manualLoading" @click="submitManual">确认补签</el-button>
      </template>
    </el-dialog>

    <!-- 撤销弹窗 -->
    <el-dialog v-model="revokeVisible" title="撤销签到" width="460px">
      <el-form label-width="90px">
        <el-form-item label="撤销原因">
          <el-input v-model="revokeRemark" type="textarea" :rows="2" placeholder="必填，例如：误签，实际未到场" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="revokeVisible = false">取消</el-button>
        <el-button type="danger" :loading="revokeLoading" @click="submitRevoke">确认撤销</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, Download, CircleCheckFilled, WarningFilled, CircleCloseFilled, VideoCamera } from '@element-plus/icons-vue'
import request from '@/api'

const route = useRoute()
const siteId = Number(route.params.id)
const siteName = ref('')
const activeTab = ref('config')

// ---------- 场次管理 ----------
const sessions = ref<any[]>([])
const sessionsLoading = ref(false)
const sessionDialog = reactive({
  visible: false,
  isEdit: false,
  editId: null as number | null,
  saving: false,
  form: {
    name: '',
    start_at: null as string | null,
    end_at: null as string | null,
    enabled: true,
    sort_order: 0,
  },
})

async function loadSessions() {
  sessionsLoading.value = true
  try {
    const data: any = await request.get(`/checkin/projects/${siteId}/sessions`)
    sessions.value = data.items || []
  } finally {
    sessionsLoading.value = false
  }
}

function openSessionDialog(row?: any) {
  sessionDialog.visible = true
  sessionDialog.isEdit = !!row
  sessionDialog.editId = row?.id || null
  if (row) {
    sessionDialog.form = {
      name: row.name,
      start_at: row.start_at || null,
      end_at: row.end_at || null,
      enabled: row.enabled,
      sort_order: row.sort_order ?? 0,
    }
  } else {
    sessionDialog.form = { name: '', start_at: null, end_at: null, enabled: true, sort_order: sessions.value.length }
  }
}

async function saveSession() {
  if (!sessionDialog.form.name.trim()) { ElMessage.warning('请填写场次名称'); return }
  if (sessionDialog.form.start_at && sessionDialog.form.end_at && sessionDialog.form.start_at >= sessionDialog.form.end_at) {
    ElMessage.error('开始时间必须早于结束时间'); return
  }
  sessionDialog.saving = true
  try {
    if (sessionDialog.isEdit) {
      await request.put(`/checkin/sessions/${sessionDialog.editId}`, sessionDialog.form)
      ElMessage.success('场次已更新')
    } else {
      await request.post(`/checkin/projects/${siteId}/sessions`, sessionDialog.form)
      ElMessage.success('场次已创建')
    }
    sessionDialog.visible = false
    loadSessions()
  } finally {
    sessionDialog.saving = false
  }
}

async function deleteSession(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除场次「${row.name}」？已有签到记录的场次无法删除。`, '删除确认', { type: 'warning' })
    await request.delete(`/checkin/sessions/${row.id}`)
    ElMessage.success('场次已删除')
    loadSessions()
  } catch (_) { /* 取消 */ }
}

// ---------- 扫码 ----------
const scanSessionId = ref<number | null>(null)
const scanMode = ref('box')
const boxInputRef = ref<HTMLInputElement | null>(null)
const boxInput = ref('')
const manualCode = ref('')
const videoRef = ref<HTMLVideoElement | null>(null)
const cameraReady = ref(false)
const cameraError = ref('')
const result = ref<any>(null)
let cameraStream: MediaStream | null = null
let scanTimer: number | null = null
let detector: any = null

const currentSession = computed(() => sessions.value.find((s) => s.id === scanSessionId.value))

const sessionTimeHint = computed(() => {
  const s = currentSession.value
  if (!s) return '请选择场次'
  const now = new Date()
  const start = s.start_at ? new Date(s.start_at) : null
  const end = s.end_at ? new Date(s.end_at) : null
  if (!s.enabled) return '场次已停用'
  if (start && now < start) return `未开始（${fmtTime(s.start_at)}）`
  if (end && now > end) return `已结束（${fmtTime(s.end_at)}）`
  return '进行中'
})

const sessionTimeTag = computed(() => {
  const s = currentSession.value
  if (!s || !s.enabled) return 'info'
  const now = new Date()
  const start = s.start_at ? new Date(s.start_at) : null
  const end = s.end_at ? new Date(s.end_at) : null
  if (start && now < start) return 'warning'
  if (end && now > end) return 'info'
  return 'success'
})

function onScanSessionChange() {
  result.value = null
}

function focusBoxInput() {
  boxInputRef.value?.focus()
}

async function submitBoxCode() {
  const code = boxInput.value.trim()
  if (!code) return
  boxInput.value = ''
  await doScan(code)
  focusBoxInput()
}

async function submitManualCode() {
  const code = manualCode.value.trim()
  if (!code) return
  await doScan(code)
}

async function doScan(code: string) {
  if (!scanSessionId.value) {
    ElMessage.warning('请先选择核销场次')
    return
  }
  try {
    const data: any = await request.post(`/checkin/projects/${siteId}/scan`, {
      code,
      session_id: scanSessionId.value,
    })
    result.value = data
    // 声音反馈
    try {
      const ctx = new AudioContext()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.value = data.result === 'SUCCESS' ? 880 : 220
      gain.gain.value = 0.15
      osc.start()
      osc.stop(ctx.currentTime + 0.15)
    } catch (_) { /* 忽略音频失败 */ }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '核销失败')
  }
}

async function initCamera() {
  cameraError.value = ''
  if (!('BarcodeDetector' in window)) {
    cameraError.value = '当前浏览器不支持摄像头扫码（需 Chrome/Edge 最新版 + HTTPS），请使用扫码盒子模式'
    cameraReady.value = false
    return
  }
  try {
    detector = new (window as any).BarcodeDetector({ formats: ['qr_code'] })
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    if (videoRef.value) {
      videoRef.value.srcObject = cameraStream
      cameraReady.value = true
    }
    startScanLoop()
  } catch (e: any) {
    cameraError.value = e?.name === 'NotAllowedError' ? '摄像头权限被拒绝，请在浏览器设置中允许后重试' : '摄像头启动失败，请使用扫码盒子模式'
    cameraReady.value = false
  }
}

async function startScanLoop() {
  if (!detector || !videoRef.value || !cameraReady.value) return
  scanTimer = window.setInterval(async () => {
    try {
      const codes = await detector.detect(videoRef.value)
      if (codes && codes.length > 0 && codes[0].rawValue) {
        stopCamera()
        await doScan(codes[0].rawValue)
      }
    } catch (_) { /* 单帧失败忽略 */ }
  }, 400)
}

function stopCamera() {
  if (scanTimer) { clearInterval(scanTimer); scanTimer = null }
  cameraStream?.getTracks().forEach((t) => t.stop())
  cameraStream = null
  cameraReady.value = false
}

function onScanModeChange(mode: string) {
  if (mode === 'camera') {
    setTimeout(() => initCamera(), 100)
  } else {
    stopCamera()
    setTimeout(() => focusBoxInput(), 100)
  }
}

onBeforeUnmount(() => {
  stopCamera()
})

// ---------- 记录 ----------
const records = ref<any[]>([])
const recordsLoading = ref(false)
const recPage = ref(1)
const recPageSize = ref(10)
const recTotal = ref(0)
const recQuery = reactive({ status: null as number | null, method: '', keyword: '', session_id: null as number | null })

async function loadRecords(page = recPage.value) {
  recPage.value = page
  recordsLoading.value = true
  try {
    const data: any = await request.get(`/checkin/projects/${siteId}/records`, {
      params: {
        page: recPage.value,
        page_size: recPageSize.value,
        status: recQuery.status ?? undefined,
        method: recQuery.method || undefined,
        keyword: recQuery.keyword || undefined,
        session_id: recQuery.session_id ?? undefined,
      },
    })
    records.value = data.items || []
    recTotal.value = data.total || 0
  } finally {
    recordsLoading.value = false
  }
}

async function exportRecords() {
  try {
    const res: any = await request.post(`/checkin/projects/${siteId}/export`, {}, {
      params: { session_id: recQuery.session_id ?? undefined },
      responseType: 'blob',
    })
    const url = URL.createObjectURL(res)
    const a = document.createElement('a')
    a.href = url
    a.download = `签到记录_${siteName.value || siteId}.csv`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (_) {
    ElMessage.error('导出失败')
  }
}

// ---------- 人工补签 ----------
const manualVisible = ref(false)
const manualAccountId = ref<number | null>(null)
const manualSessionId = ref<number | null>(null)
const manualRemark = ref('')
const manualLoading = ref(false)
const accountOptions = ref<any[]>([])
const searchingAccounts = ref(false)

function maskPhone(p: string) {
  if (!p) return '无手机号'
  if (p.length < 7) return p
  return p.slice(0, 3) + '****' + p.slice(-4)
}

async function searchAccounts(kw: string) {
  if (!kw) return
  searchingAccounts.value = true
  try {
    const data: any = await request.get(`/sites/${siteId}/accounts`, { params: { keyword: kw, page_size: 20 } })
    accountOptions.value = data.items || []
  } finally {
    searchingAccounts.value = false
  }
}

function openManual() {
  manualVisible.value = true
  manualAccountId.value = null
  manualSessionId.value = scanSessionId.value || (sessions.value[0]?.id ?? null)
  manualRemark.value = ''
}

async function submitManual() {
  if (!manualSessionId.value) { ElMessage.warning('请选择场次'); return }
  if (!manualAccountId.value) { ElMessage.warning('请先搜索并选择账号'); return }
  if (!manualRemark.value.trim()) { ElMessage.warning('请填写补签原因'); return }
  manualLoading.value = true
  try {
    await request.post(`/checkin/projects/${siteId}/manual`, {
      account_id: manualAccountId.value,
      session_id: manualSessionId.value,
      remark: manualRemark.value.trim(),
    })
    ElMessage.success('补签成功')
    manualVisible.value = false
    loadRecords(1)
  } finally {
    manualLoading.value = false
  }
}

// ---------- 撤销 ----------
const revokeVisible = ref(false)
const revokeRemark = ref('')
const revokeLoading = ref(false)
const revokeTarget = ref<any>(null)

function openRevoke(row: any) {
  revokeTarget.value = row
  revokeRemark.value = ''
  revokeVisible.value = true
}

async function submitRevoke() {
  if (!revokeRemark.value.trim()) { ElMessage.warning('请填写撤销原因'); return }
  revokeLoading.value = true
  try {
    await request.post(`/checkin/records/${revokeTarget.value.id}/revoke`, { remark: revokeRemark.value.trim() })
    ElMessage.success('已撤销，用户可重新签到')
    revokeVisible.value = false
    loadRecords()
  } finally {
    revokeLoading.value = false
  }
}

// ---------- 工具 ----------
function fmtTime(t: string | null): string {
  if (!t) return '-'
  return t.replace('T', ' ').slice(0, 19)
}

const resultClass = computed(() => {
  if (!result.value) return ''
  const r = result.value.result
  if (r === 'SUCCESS') return 'result-success'
  if (r === 'ALREADY_CHECKED_IN') return 'result-warn'
  return 'result-fail'
})

// ---------- 初始化 ----------
async function loadConfig() {
  const data: any = await request.get(`/checkin/projects/${siteId}/config`)
  siteName.value = data.name || ''
}

onMounted(async () => {
  await loadConfig()
  await loadSessions()
  // 默认选中第一个启用场次
  if (sessions.value.length > 0) {
    const firstEnabled = sessions.value.find((s) => s.enabled)
    scanSessionId.value = firstEnabled?.id || sessions.value[0].id
  }
  loadRecords(1)
  setTimeout(() => focusBoxInput(), 300)
})
</script>

<style scoped>
.page-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.head-title {
  font-size: 16px;
  font-weight: 600;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.session-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.session-tip {
  font-size: 14px;
  color: #606266;
}
.text-muted {
  color: #c0c4cc;
}
.scan-session-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}
.bar-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}
.scan-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.scan-card {
  flex: 1;
  max-width: 560px;
}
.scan-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.box-mode {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  border: 2px dashed #dcdfe6;
  border-radius: 10px;
  cursor: pointer;
  transition: border-color .2s;
}
.box-mode:hover {
  border-color: #409eff;
}
.box-icon {
  font-size: 44px;
  color: #409eff;
}
.box-hint {
  margin-top: 12px;
  color: #909399;
  font-size: 13px;
}
.box-input {
  margin-top: 14px;
  width: 100%;
  max-width: 320px;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  outline: none;
  font-size: 14px;
}
.box-input:focus {
  border-color: #409eff;
}
.camera-wrap {
  position: relative;
  width: 100%;
  max-width: 420px;
  margin: 0 auto;
}
.camera-video {
  width: 100%;
  border-radius: 10px;
  background: #000;
  min-height: 240px;
  object-fit: cover;
}
.camera-tip {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
}
.camera-unavailable {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 40px 20px;
  color: #909399;
  text-align: center;
}
.manual-row {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  justify-content: center;
}
.result-card {
  flex: 1;
  min-width: 280px;
}
.result-success { border-color: #b3e8a1; }
.result-warn { border-color: #f3d19e; }
.result-fail { border-color: #f8b5b5; }
.result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}
.result-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.result-item {
  display: flex;
  gap: 10px;
  font-size: 14px;
}
.result-item span {
  color: #909399;
  min-width: 60px;
}
.records-toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.toolbar-right {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
