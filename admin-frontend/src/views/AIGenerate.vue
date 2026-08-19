<template>
  <div class="ai-generate" v-loading="loading">
    <!-- 未配置提示 -->
    <el-alert
      v-if="aiConfig && !aiConfig.configured"
      title="AI 生图尚未配置 API Key，无法生成图片。请联系超级管理员在「管理员配置 → AI 生图」中填写通义万相（DashScope）API Key。"
      type="warning"
      show-icon
      :closable="false"
      class="config-alert"
    />

    <div class="ai-layout">
      <!-- 左侧：参数表单 -->
      <el-card shadow="never" class="panel form-panel">
        <template #header><div class="panel-title">生成参数</div></template>
        <el-form label-position="top" @submit.prevent>
          <el-form-item label="提示词（描述你想生成的画面）">
            <el-input
              v-model="form.prompt"
              type="textarea"
              :rows="4"
              placeholder="例如：极简风格的科技感背景，蓝紫色渐变光效，适合活动宣传海报"
              maxlength="2000"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="负面提示词（不希望出现的内容，可选）">
            <el-input
              v-model="form.negative_prompt"
              type="textarea"
              :rows="2"
              placeholder="例如：文字，水印，低质量，模糊"
              maxlength="2000"
            />
          </el-form-item>

          <div class="form-grid">
            <el-form-item label="尺寸">
              <el-select v-model="form.size" style="width: 100%">
                <el-option label="图标 128×128" value="128*128" />
                <el-option label="KV 750×300" value="750*300" />
                <el-option label="竖版 720×1280" value="720*1280" />
              </el-select>
            </el-form-item>
            <el-form-item label="生成数量">
              <el-radio-group v-model="form.n" :disabled="!!refFile">
                <el-radio-button :value="1">1</el-radio-button>
                <el-radio-button :value="2">2</el-radio-button>
              </el-radio-group>
              <div v-if="refFile" class="field-hint">图生图一次生成 1 张</div>
            </el-form-item>
          </div>

          <el-form-item label="参考图（可选，上传后走图生图）">
            <el-upload
              :auto-upload="false"
              :limit="1"
              accept="image/*"
              :on-change="onRefChange"
              :on-remove="() => (refFile = null)"
              :on-exceed="() => ElMessage.warning('最多上传 1 张参考图')"
              list-type="picture-card"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
            <div class="field-hint">参考图用于保持参考图的构图/角色/风格，配合提示词生成新图。</div>
          </el-form-item>

          <div v-if="aiConfig?.configured" class="fee-bar">
            <template v-if="aiConfig.is_free">
              <span>超级管理员免扣费</span>
            </template>
            <template v-else>
              <span>当前余额 <b>¥{{ aiConfig.balance_yuan }}</b></span>
              <el-divider direction="vertical" />
              <span>本次费用 <b>¥{{ costYuan }}</b>（{{ refFile ? 1 : form.n }} 张 × ¥{{ aiConfig.price_per_image_yuan }}）</span>
            </template>
          </div>
          <el-button
            type="primary"
            class="generate-btn"
            :loading="generating"
            :disabled="!form.prompt.trim() || !aiConfig?.configured || insufficientBalance"
            @click="generate"
          >
            {{ generating ? '生成中（约需 10-60 秒）' : '立即生成' }}
          </el-button>
          <div v-if="insufficientBalance" class="fee-warn">
            余额不足，无法生成。请联系管理员充值后使用（按张扣费 ¥{{ aiConfig?.price_per_image_yuan }}/张）。
          </div>
        </el-form>
      </el-card>

      <!-- 右侧：生成结果 -->
      <el-card shadow="never" class="panel result-panel">
        <template #header>
          <div class="panel-title result-title">
            生成结果
            <span v-if="generatedCount" class="result-count">
              本次 {{ generatedCount }} 张<template v-if="elapsedSeconds"> · 用时 {{ elapsedSeconds }}s</template>
            </span>
          </div>
        </template>

        <div v-if="results.length" class="result-grid">
          <div v-for="(item, index) in results" :key="index" class="result-item">
            <el-image
              :src="item.result_url"
              fit="contain"
              class="result-img"
              :preview-src-list="results.map((r) => r.result_url)"
              :initial-index="index"
              preview-teleported
            />
            <div class="result-actions">
              <el-button size="small" link @click="copyUrl(item.result_url)">复制链接</el-button>
              <el-button size="small" link type="primary" @click="download(item.result_url, index)">下载</el-button>
            </div>
          </div>
        </div>
        <el-empty v-else-if="!generating" description="输入提示词后点击「立即生成」" :image-size="80" />
        <div v-else class="generating-tip">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>AI 正在生成，已用时 <span class="elapsed-num">{{ elapsedSeconds }}</span> 秒…</span>
        </div>
      </el-card>
    </div>

    <!-- 生成历史 -->
    <el-card shadow="never" class="panel history-panel">
      <template #header>
        <div class="panel-title history-title">
          生成历史
          <span class="result-count" v-if="historyTotal">共 {{ historyTotal }} 条</span>
        </div>
      </template>

      <el-table :data="history" v-loading="historyLoading" stripe>
        <el-table-column label="结果图" width="90">
          <template #default="{ row }">
            <el-image :src="row.result_url" fit="cover" class="history-thumb" :preview-src-list="[row.result_url]" preview-teleported />
          </template>
        </el-table-column>
        <el-table-column prop="prompt" label="提示词" min-width="220" show-overflow-tooltip />
        <el-table-column label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.reference_image ? 'warning' : 'success'" effect="plain">
              {{ row.reference_image ? '图生图' : '文生图' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="尺寸" width="110" align="center" />
        <el-table-column label="生成时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button size="small" link @click="copyUrl(row.result_url)">复制链接</el-button>
            <el-button size="small" link type="primary" @click="download(row.result_url, row.id)">下载</el-button>
            <el-button size="small" link type="danger" @click="removeHistory(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="historyPage"
          :page-size="pageSize"
          :total="historyTotal"
          layout="prev, pager, next"
          background
          @current-change="loadHistory"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Loading } from '@element-plus/icons-vue'
import api from '@/api'

interface GenerationRecord {
  id: number
  prompt: string
  negative_prompt?: string | null
  reference_image?: string | null
  result_url: string
  provider: string
  model_name: string
  size: string
  created_at: string
}

interface AiConfigInfo {
  configured: boolean
  provider: string
  image_model: string
  i2i_model: string
  price_per_image_cents: number
  price_per_image_yuan: string
  balance: number
  balance_yuan: string
  is_free: boolean
}

const loading = ref(false)
const generating = ref(false)
const aiConfig = ref<AiConfigInfo | null>(null)

// 生成计时动画
const elapsedSeconds = ref(0)
let timer: ReturnType<typeof setInterval> | null = null
function startTimer() {
  elapsedSeconds.value = 0
  timer = setInterval(() => {
    elapsedSeconds.value += 1
  }, 1000)
}
function stopTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

const form = reactive({
  prompt: '',
  negative_prompt: '',
  size: '750*300',
  n: 1,
})
const refFile = ref<File | null>(null)

// 本次费用（元）与余额是否足够：图生图固定 1 张
const costYuan = computed(() => {
  if (!aiConfig.value) return '0.00'
  const count = refFile.value ? 1 : form.n
  return ((aiConfig.value.price_per_image_cents * count) / 100).toFixed(2)
})
const insufficientBalance = computed(() => {
  if (!aiConfig.value?.configured || aiConfig.value.is_free) return false
  const count = refFile.value ? 1 : form.n
  return aiConfig.value.balance < aiConfig.value.price_per_image_cents * count
})

const results = ref<GenerationRecord[]>([])
const generatedCount = computed(() => results.value.length)

const history = ref<GenerationRecord[]>([])
const historyTotal = ref(0)
const historyPage = ref(1)
const pageSize = 12
const historyLoading = ref(false)

async function loadAiConfig() {
  try {
    aiConfig.value = await api.get('/ai/config')
  } catch {
    aiConfig.value = {
      configured: false,
      provider: 'dashscope',
      image_model: '',
      i2i_model: '',
      price_per_image_cents: 10,
      price_per_image_yuan: '0.10',
      balance: 0,
      balance_yuan: '0.00',
      is_free: false,
    }
  }
}

function onRefChange(file: any) {
  refFile.value = file.raw || null
}

async function generate() {
  if (!form.prompt.trim()) {
    ElMessage.warning('请输入提示词')
    return
  }
  generating.value = true
  results.value = []
  startTimer()
  try {
    const fd = new FormData()
    fd.append('prompt', form.prompt.trim())
    fd.append('negative_prompt', form.negative_prompt.trim())
    fd.append('size', form.size)
    fd.append('n', String(form.n))
    if (refFile.value) fd.append('reference_image', refFile.value)

    const res: any = await api.post('/ai/generate', fd, { timeout: 180000 })
    results.value = res.items || []
    if (results.value.length) {
      ElMessage.success(`生成成功，共 ${results.value.length} 张，用时 ${elapsedSeconds}s`)
    }
    historyPage.value = 1
    await loadHistory()
    await loadAiConfig() // 刷新余额
  } catch {
    await loadAiConfig() // 失败也刷新一次，保持余额展示准确
    // 错误提示由 axios 拦截器统一处理
  } finally {
    stopTimer()
    generating.value = false
  }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const res: any = await api.get('/ai/generations', {
      params: { page: historyPage.value, page_size: pageSize },
    })
    history.value = res.items || []
    historyTotal.value = res.total || 0
  } catch {
    // ignore
  } finally {
    historyLoading.value = false
  }
}

async function removeHistory(id: number) {
  try {
    await api.delete(`/ai/generations/${id}`)
    ElMessage.success('已删除')
    if (history.value.length === 1 && historyPage.value > 1) historyPage.value--
    await loadHistory()
  } catch {
    // ignore
  }
}

async function copyUrl(url: string) {
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  }
}

function download(url: string, name: string | number) {
  const a = document.createElement('a')
  a.href = url
  a.download = `ai_image_${name}.png`
  a.target = '_blank'
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

function formatTime(t: string) {
  const d = new Date(t)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(() => {
  loadAiConfig()
  loadHistory()
})
</script>

<style scoped>
.ai-generate { max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }
.config-alert { margin-bottom: 0; }
.ai-layout { display: grid; grid-template-columns: 360px minmax(0, 1fr); gap: 16px; align-items: start; }
.panel { border-radius: 4px; }
.panel-title { font-size: 15px; font-weight: 600; color: #303133; display: flex; align-items: center; gap: 8px; }
.form-panel :deep(.el-form-item__label) { font-size: 13px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px; }
.field-hint { font-size: 12px; color: #909399; line-height: 1.5; margin-top: 4px; }
.generate-btn { width: 100%; margin-top: 4px; }
.fee-bar { display: flex; align-items: center; justify-content: center; padding: 8px 0 4px; font-size: 13px; color: #606266; background: #f5f7fa; border-radius: 4px; }
.fee-bar b { color: #f56c6c; font-weight: 600; }
.fee-warn { margin-top: 8px; font-size: 12px; line-height: 1.6; color: #f56c6c; background: #fef0f0; border: 1px solid #fde2e2; border-radius: 4px; padding: 6px 10px; }

.result-title, .history-title { justify-content: space-between; }
.result-count { font-size: 12px; font-weight: 400; color: #909399; }
.result-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; align-items: start; }
.result-item { border: 1px solid #ebeef5; border-radius: 8px; overflow: hidden; }
.result-img { width: 100%; height: auto; display: block; }
.result-actions { display: flex; justify-content: center; gap: 4px; padding: 6px 0; }
.generating-tip { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 60px 0; color: #909399; }
.elapsed-num { font-variant-numeric: tabular-nums; min-width: 2.2em; display: inline-block; text-align: right; font-weight: 600; color: #409eff; animation: elapsed-pulse 1s ease-in-out infinite; }
@keyframes elapsed-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.15); }
}

.history-thumb { width: 56px; height: 56px; border-radius: 4px; border: 1px solid #ebeef5; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 12px; }

@media (max-width: 900px) {
  .ai-layout { grid-template-columns: 1fr; }
  .form-grid { grid-template-columns: 1fr; }
}
</style>
