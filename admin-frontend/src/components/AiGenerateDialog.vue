<template>
  <el-dialog
    :model-value="visible"
    :title="dialogTitle"
    width="620px"
    append-to-body
    :close-on-click-modal="false"
    @update:model-value="(v) => emit('update:visible', v)"
  >
    <!-- 未配置 -->
    <el-alert
      v-if="aiConfig && !aiConfig.configured"
      title="AI 生图尚未配置 API Key，无法生成图片。请联系超级管理员在「管理员配置 → AI 生图」中填写通义万相（DashScope）API Key。"
      type="warning"
      show-icon
      :closable="false"
      class="config-alert"
    />

    <template v-else>
      <!-- 用途说明 -->
      <div class="use-info">
        <span class="use-label">{{ useInfo?.label || '图片' }}</span>
        <el-tag size="small" effect="plain">{{ useInfo ? useInfo.size.replace('*', '×') : '' }}</el-tag>
        <span class="use-desc">{{ useInfo?.desc }}</span>
      </div>

      <!-- 提示词 + 参考图并排（参考图走图生图：wan2.5-i2i-preview） -->
      <div class="prompt-row">
        <el-input
          v-model="prompt"
          type="textarea"
          :rows="5"
          :placeholder="promptPlaceholder"
          maxlength="2000"
          show-word-limit
          class="prompt-input"
        />
        <div class="ref-side" :class="{ 'ref-side--filled': !!refFile }">
          <div class="ref-label">参考图</div>
          <el-upload
            v-model:file-list="refFileList"
            :auto-upload="false"
            :limit="1"
            accept=".jpg,.jpeg,.png,.gif,.webp"
            list-type="picture-card"
            :on-change="onRefChange"
            :on-exceed="onRefExceed"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </div>
      </div>

      <div class="ref-foot">
        <el-tag size="small" :type="refFile ? 'warning' : 'success'" effect="plain">
          {{ refFile ? '图生图' : '文生图' }}
        </el-tag>
        <span class="ref-hint">
          <template v-if="refFile">按参考图的构图与风格，配合提示词生成 1 张</template>
          <template v-else>可选：上传参考图，按其构图与风格配合提示词生成</template>
        </span>
      </div>

      <div class="fee-bar">
        <template v-if="aiConfig?.is_free">
          <el-icon><CircleCheck /></el-icon>
          <span>超级管理员免扣费</span>
        </template>
        <template v-else>
          <span>当前余额 <b>¥{{ aiConfig?.balance_yuan }}</b></span>
          <el-divider direction="vertical" />
          <span>本次费用 <b>¥{{ aiConfig?.price_per_image_yuan }}</b>（1 张）</span>
        </template>
      </div>

      <div v-if="insufficientBalance" class="fee-warn">
        余额不足，无法生成。请联系管理员充值后使用（按张扣费 ¥{{ aiConfig?.price_per_image_yuan }}/张）。
      </div>

      <div class="btn-row">
        <el-button
          type="primary"
          :loading="generating"
          :disabled="!prompt.trim() || !aiConfig?.configured || insufficientBalance"
          @click="generate"
        >
          <template v-if="generating">
            生成中，已用时 <span class="elapsed-num">{{ elapsedSeconds }}</span> 秒…
          </template>
          <template v-else>立即生成</template>
        </el-button>
        <span v-if="generating" class="gen-hint">约需 10-60 秒，请勿关闭窗口</span>
      </div>

      <!-- 生成结果 -->
      <div v-if="results.length" class="result-section">
        <div class="result-title">
          生成结果
          <span class="result-time">· 用时 {{ elapsedSeconds }}s</span>
        </div>
        <div class="result-grid">
          <div v-for="(item, index) in results" :key="index" class="result-item">
            <el-image
              :src="item.result_url"
              fit="contain"
              class="result-img"
              :preview-src-list="results.map((r) => r.result_url)"
              :initial-index="index"
              preview-teleported
            />
            <el-button type="primary" size="small" class="use-btn" @click="useImage(item.result_url)">
              使用此图
            </el-button>
          </div>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck, Plus } from '@element-plus/icons-vue'
import api from '@/api'

interface AiUseInfo {
  key: string
  label: string
  size: string
  desc: string
}

interface GenerationRecord {
  id: number
  result_url: string
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
  uses: AiUseInfo[]
}

// 兜底用途列表：config 拉取失败时仍可用
const FALLBACK_USES: AiUseInfo[] = [
  { key: 'icon', label: '模块图标', size: '128*128', desc: '128×128 正方形，用于九宫格/按钮模块图标' },
  { key: 'kv', label: 'KV 横幅', size: '750*340', desc: '750×340 宽幅横幅，用于微站顶部 KV 图' },
  { key: 'share', label: '微信分享图', size: '500*500', desc: '500×500 正方形，用于微信分享卡片' },
  { key: 'background', label: '页面背景', size: '750*1334', desc: '750×1334 竖版，用于微站页面全屏背景' },
]

const TITLE_MAP: Record<string, string> = {
  icon: 'AI 生成图标',
  kv: 'AI 生成 KV 图',
  share: 'AI 生成分享图',
  background: 'AI 生成背景图',
}

const PLACEHOLDER_MAP: Record<string, string> = {
  icon: '例如：蓝色圆角图标，扁平风格，科技感',
  kv: '例如：科技蓝渐变背景，现代感，适合活动横幅',
  share: '例如：喜庆节日主题，红金配色，适合分享卡片',
  background: '例如：淡雅渐变星空背景，安静柔和',
}

const props = defineProps<{
  visible: boolean
  use: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  select: [url: string]
}>()

const aiConfig = ref<AiConfigInfo | null>(null)
const prompt = ref('')
const results = ref<GenerationRecord[]>([])
const generating = ref(false)

// 参考图：用 file-list 双向绑定，移除时状态才能被正确清空
const refFileList = ref<any[]>([])
const refFile = computed<File | null>(() => refFileList.value[0]?.raw || null)
const MAX_REF_MB = 10
// 与后端 settings.ALLOWED_FILE_TYPES / MAX_FILE_SIZE 保持一致
const REF_EXT = ['jpg', 'jpeg', 'png', 'gif', 'webp']

function rejectRef(file: any, msg: string) {
  ElMessage.warning(msg)
  if (typeof file?.url === 'string' && file.url.startsWith('blob:')) {
    URL.revokeObjectURL(file.url)
  }
  refFileList.value = []
}

function onRefChange(file: any) {
  const raw: File | undefined = file?.raw
  if (!raw) return
  const ext = (raw.name.split('.').pop() || '').toLowerCase()
  if (!REF_EXT.includes(ext)) {
    rejectRef(file, `参考图仅支持 ${REF_EXT.join(' / ')} 格式`)
    return
  }
  if (raw.size > MAX_REF_MB * 1024 * 1024) {
    rejectRef(file, `参考图不能超过 ${MAX_REF_MB}MB，当前 ${(raw.size / 1024 / 1024).toFixed(1)}MB`)
  }
}

function onRefExceed() {
  ElMessage.warning('最多上传 1 张参考图，请先移除已选图片')
}

// 生成计时动画
const elapsedSeconds = ref(0)
let timer: ReturnType<typeof setInterval> | null = null
function startTimer() {
  stopTimer() // 防止重复点击/重复打开导致 interval 叠加
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
onUnmounted(stopTimer)

const uses = computed<AiUseInfo[]>(() => (aiConfig.value?.uses?.length ? aiConfig.value.uses : FALLBACK_USES))
const useInfo = computed(() => uses.value.find((u) => u.key === props.use))
const dialogTitle = computed(() => TITLE_MAP[props.use] || 'AI 生成图片')
const promptPlaceholder = computed(() => PLACEHOLDER_MAP[props.use] || '描述你想生成的画面')

const insufficientBalance = computed(() => {
  if (!aiConfig.value?.configured || aiConfig.value.is_free) return false
  return aiConfig.value.balance < aiConfig.value.price_per_image_cents
})

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
      uses: [],
    }
  }
}

async function generate() {
  if (!prompt.value.trim()) {
    ElMessage.warning('请输入提示词')
    return
  }
  generating.value = true
  results.value = []
  startTimer()
  try {
    const fd = new FormData()
    fd.append('prompt', prompt.value.trim())
    fd.append('use', props.use)
    fd.append('n', '1')
    // 有参考图则走后端图生图（wan2.5-i2i-preview），输出仍按用途预设尺寸
    if (refFile.value) fd.append('reference_image', refFile.value)

    const res: any = await api.post('/ai/generate', fd, { timeout: 180000 })
    results.value = res.items || []
    stopTimer() // 先停表，保证提示与结果区展示的用时一致
    if (results.value.length) {
      ElMessage.success({ message: `生成成功，用时 ${elapsedSeconds.value}s`, zIndex: 3000 })
    }
    await loadAiConfig() // 刷新余额
  } catch {
    await loadAiConfig() // 失败也刷新一次，保持余额展示准确
    // 错误提示由 axios 拦截器统一处理
  } finally {
    stopTimer()
    generating.value = false
  }
}

function useImage(url: string) {
  emit('select', url)
  emit('update:visible', false)
}

// 每次打开弹窗重新加载配置，并清空上次内容
watch(
  () => props.visible,
  (v) => {
    if (v) {
      prompt.value = ''
      results.value = []
      refFileList.value = []
      elapsedSeconds.value = 0
      loadAiConfig()
    }
  },
)
</script>

<style scoped>
.config-alert { margin-bottom: 12px; }
.use-info { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.use-label { font-size: 14px; font-weight: 600; color: #303133; }
.use-desc { font-size: 12px; color: #909399; line-height: 1.5; }
/* 提示词 + 参考图并排 */
.prompt-row { display: flex; align-items: flex-start; gap: 12px; }
.prompt-input { flex: 1; min-width: 0; }
.ref-side { width: 84px; flex-shrink: 0; }
.ref-label { font-size: 12px; color: #909399; line-height: 1; text-align: center; margin-bottom: 6px; }
.ref-side :deep(.el-upload-list--picture-card) { display: flex; flex-wrap: wrap; }
.ref-side :deep(.el-upload--picture-card),
.ref-side :deep(.el-upload-list--picture-card .el-upload-list__item) {
  width: 84px;
  height: 84px;
  margin: 0;
  border-radius: 8px;
}
.ref-side :deep(.el-upload--picture-card) { line-height: 88px; }
.ref-side :deep(.el-upload-list--picture-card .el-upload-list__item-thumbnail) {
  object-fit: cover;
}
/* 已有参考图时隐藏上传触发块，右侧始终只占一个方块 */
.ref-side--filled :deep(.el-upload--picture-card) { display: none; }
.ref-foot { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.ref-hint { font-size: 12px; color: #909399; line-height: 1.5; }
.fee-bar {
  display: flex; align-items: center; justify-content: center;
  padding: 8px 0; margin-top: 12px;
  font-size: 13px; color: #606266;
  background: #f5f7fa; border-radius: 4px;
}
.fee-bar b { color: #f56c6c; font-weight: 600; }
.fee-warn {
  margin-top: 8px; font-size: 12px; line-height: 1.6;
  color: #f56c6c; background: #fef0f0; border: 1px solid #fde2e2;
  border-radius: 4px; padding: 6px 10px;
}
.btn-row { display: flex; align-items: center; gap: 12px; margin-top: 12px; }
.gen-hint { font-size: 12px; color: #909399; }
.elapsed-num {
  font-variant-numeric: tabular-nums; min-width: 2.2em; display: inline-block;
  text-align: right; font-weight: 600; color: #409eff;
  animation: elapsed-pulse 1s ease-in-out infinite;
}
/* 按钮内（primary 蓝底）的秒数：白字加粗，对比明显 */
.btn-row .elapsed-num { color: #fff; }
@keyframes elapsed-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.15); }
}
.result-section { margin-top: 14px; border-top: 1px solid #ebeef5; padding-top: 10px; }
.result-title { font-size: 13px; font-weight: 600; color: #303133; margin-bottom: 8px; }
.result-time { font-size: 12px; font-weight: 400; color: #909399; }
/* 结果用小缩略图横排，避免纵向撑高弹窗 */
.result-grid { display: flex; flex-wrap: wrap; gap: 10px; max-height: 220px; overflow-y: auto; }
.result-item { width: 136px; padding: 6px; border: 1px solid #ebeef5; border-radius: 8px; }
.result-img { display: block; width: 100%; height: 88px; border-radius: 4px; background: #f5f7fa; }
.use-btn { width: 100%; margin-top: 6px; }
</style>
