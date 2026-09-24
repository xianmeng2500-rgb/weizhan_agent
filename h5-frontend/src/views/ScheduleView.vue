<template>
  <div class="schedule-page" :class="'tpl-' + siteTheme">
    <van-nav-bar
      :title="moduleTitle || '日程安排'"
      left-arrow
      @click-left="goBack"
      :style="navBarStyle"
    />

    <!-- 加载中 -->
    <van-loading v-if="loading" class="page-loading" size="32" color="var(--schedule-accent, #667eea)" />

    <!-- 空状态 -->
    <van-empty v-else-if="!rawItems.length" description="暂无日程安排" />

    <div v-else class="schedule-container">
      <!-- 日期按钮条（横向滚动，仅展示有日程的日期） -->
      <div ref="tabStrip" class="date-strip">
        <div
          v-for="tab in dateTabs"
          :key="tab.date"
          class="date-btn"
          :class="{
            'is-active': tab.date === selectedDate,
            'is-today': tab.isToday,
            'is-past': tab.isPast,
          }"
          @click="selectDate(tab.date)"
        >
          <span class="db-day">{{ tab.dayLabel }}</span>
          <span class="db-week">{{ tab.weekLabel }}</span>
        </div>
      </div>

      <!-- 选中日期标题 -->
      <div v-if="selectedDate" class="section-title">
        <span class="section-title-text">{{ selectedLabel }}</span>
        <span class="section-count">共 {{ selectedSchedules.length }} 项</span>
      </div>

      <!-- 日程卡片列表 -->
      <div v-if="selectedSchedules.length" class="card-list">
        <div
          v-for="(item, idx) in selectedSchedules"
          :key="item.id"
          class="schedule-card"
          :style="{ animationDelay: idx * 0.06 + 's' }"
        >
          <div class="card-left-bar" :class="'bar-' + (idx % 4)"></div>
          <div class="card-content">
            <div class="card-header-row">
              <div class="card-time-badge">
                <van-icon name="clock-o" size="13" />
                <span>{{ item.time || '待定' }}</span>
              </div>
              <van-tag
                v-if="item.personnel"
                size="medium"
                type="primary"
                plain
                class="personnel-tag"
              >
                {{ item.personnel }}
              </van-tag>
            </div>
            <div class="card-topic">
              {{ item.topic || '未命名日程' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 选中日期无日程 -->
      <div v-else-if="selectedDate" class="no-schedule-hint">
        <van-icon name="info-o" size="16" />
        <span>当天暂无日程安排</span>
      </div>
    </div>

    <!-- 底部填充 -->
    <div class="bottom-safe"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const moduleId = route.params.moduleId as string
const code = route.params.code as string

const loading = ref(true)
const moduleTitle = ref('')
const siteTheme = ref('classic')
const rawItems = ref<any[]>([])

const weekNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

// 选中的日期 YYYY-MM-DD
const selectedDate = ref('')
const tabStrip = ref<HTMLElement | null>(null)

const todayStr = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

interface DateTab {
  date: string      // YYYY-MM-DD
  dayLabel: string  // 9月23日
  weekLabel: string // 周三 / 今天
  isToday: boolean
  isPast: boolean
  count: number
}

// 只取有日程的日期，按升序排列
const dateTabs = computed<DateTab[]>(() => {
  const map = new Map<string, number>()
  for (const item of rawItems.value) {
    if (!item.date) continue
    map.set(item.date, (map.get(item.date) || 0) + 1)
  }

  const today = todayStr.value
  return Array.from(map.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([date, count]) => {
      const d = new Date(date.replace(/-/g, '/'))
      const isToday = date === today
      return {
        date,
        dayLabel: `${d.getMonth() + 1}月${d.getDate()}日`,
        weekLabel: isToday ? '今天' : weekNames[d.getDay()],
        isToday,
        isPast: date < today,
        count,
      }
    })
})

const selectedTab = computed(() => dateTabs.value.find((t) => t.date === selectedDate.value) || null)

const selectedLabel = computed(() => {
  const tab = selectedTab.value
  if (!tab) return ''
  return `${tab.dayLabel} ${weekNames[new Date(tab.date.replace(/-/g, '/')).getDay()]}`
})

const selectedSchedules = computed(() => {
  if (!selectedDate.value) return []
  return rawItems.value
    .filter((i: any) => i.date === selectedDate.value)
    .sort((a: any, b: any) => (a.time || '').localeCompare(b.time || ''))
})

const navBarStyle = computed(() => {
  if (siteTheme.value === 'dark') {
    return { '--van-nav-bar-background': '#1a1a2e', '--van-nav-bar-text-color': '#e0e0e0', '--van-nav-bar-icon-color': '#e0e0e0' }
  }
  return {}
})

// 默认高亮：距离当前时间最近的日期（优先今天及之后最近的一天；若全部已过，则取最靠近今天的那天）
function pickNearestDate() {
  const tabs = dateTabs.value
  if (!tabs.length) return ''
  const today = todayStr.value
  const upcoming = tabs.find((t) => t.date >= today)
  return upcoming ? upcoming.date : tabs[tabs.length - 1].date
}

function selectDate(date: string) {
  if (selectedDate.value === date) return
  selectedDate.value = date
  scrollActiveIntoView()
}

// 让高亮按钮自动居中
function scrollActiveIntoView() {
  nextTick(() => {
    const strip = tabStrip.value
    if (!strip) return
    const el = strip.querySelector('.is-active') as HTMLElement | null
    if (!el) return
    const target = el.offsetLeft - strip.clientWidth / 2 + el.offsetWidth / 2
    strip.scrollTo({ left: Math.max(target, 0), behavior: 'smooth' })
  })
}

async function loadData() {
  loading.value = true
  try {
    const [mod, siteInfo]: any[] = await Promise.all([
      api.get(`/p/modules/${moduleId}`),
      api.get(`/p/sites/${code}`),
    ])

    moduleTitle.value = mod.title || '日程安排'
    siteTheme.value = siteInfo.template || 'classic'

    const config = mod.schedule_config
    if (config && Array.isArray(config.items)) {
      rawItems.value = config.items
    }

    selectedDate.value = pickNearestDate()
    scrollActiveIntoView()
  } catch (err: any) {
    showToast(err.response?.data?.detail || '加载失败')
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
.schedule-page {
  min-height: 100vh;
  background: #f5f7fa;
  /* ===== 主题变量（基类兜底 = classic 配色，未知模板 key 也能正常显示） ===== */
  /* --schedule-active-text: 选中态按钮文字色（深色主题强调色偏亮，需用深色文字保证对比度） */
  --schedule-accent: #667eea;
  --schedule-accent-light: #eef0fd;
  --schedule-accent-soft: #f0f2ff;
  --schedule-active-text: #fff;
}

/* ===== 主题覆盖 ===== */
.tpl-dark {
  --schedule-accent: #5dcaa5;
  --schedule-accent-light: rgba(93, 202, 165, 0.15);
  --schedule-accent-soft: rgba(93, 202, 165, 0.06);
  --schedule-active-text: #0d2b23;
  background: #0f0f1a;
  color: #e0e0e0;
}
.tpl-festive {
  --schedule-accent: #e74c3c;
  --schedule-accent-light: rgba(231, 76, 60, 0.1);
  --schedule-accent-soft: rgba(231, 76, 60, 0.05);
  --schedule-active-text: #fff;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding-top: 120px;
}

/* ========== 容器 ========== */
.schedule-container {
  padding: 12px 0 0;
}

/* ===== 日期按钮条 ===== */
.date-strip {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding: 4px 14px 12px;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}
.date-strip::-webkit-scrollbar {
  display: none;
}

.date-btn {
  flex-shrink: 0;
  min-width: 72px;
  padding: 9px 14px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #eee;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  cursor: pointer;
  transition: all 0.2s;
  -webkit-tap-highlight-color: transparent;
}
.date-btn:active {
  transform: scale(0.96);
}

.db-day {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  line-height: 1.2;
  white-space: nowrap;
}

.db-week {
  font-size: 11px;
  color: #999;
  line-height: 1.2;
  white-space: nowrap;
}

/* 已过日期 */
.is-past .db-day {
  color: #b5b5b5;
}
.is-past .db-week {
  color: #c4c4c4;
}

/* 今天（未选中） */
.is-today:not(.is-active) {
  border-color: var(--schedule-accent);
}
.is-today:not(.is-active) .db-day {
  color: var(--schedule-accent);
}

/* 选中 */
.date-btn.is-active {
  background: var(--schedule-accent);
  border-color: var(--schedule-accent);
  box-shadow: 0 3px 10px rgba(102, 126, 234, 0.28);
}
.tpl-festive .date-btn.is-active { box-shadow: 0 3px 10px rgba(231, 76, 60, 0.28); }
.tpl-dark .date-btn.is-active { box-shadow: 0 3px 10px rgba(93, 202, 165, 0.28); }

/* 暗色主题 */
.tpl-dark .date-btn {
  background: #1a1a2e;
  border-color: #2a2a3e;
}
.tpl-dark .db-day { color: #e0e0e0; }
.tpl-dark .db-week { color: #888; }
.tpl-dark .is-past .db-day { color: #5a5a6e; }
.tpl-dark .is-past .db-week { color: #4a4a5e; }

/* ===== 选中态文字（放最后，覆盖上面各主题/过期态的颜色） ===== */
.schedule-page .date-btn.is-active .db-day,
.schedule-page .date-btn.is-active .db-week {
  color: var(--schedule-active-text, #fff);
}

/* ===== 选中日期标题 ===== */
.section-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 4px 18px 10px;
}

.section-title-text {
  font-size: 15px;
  font-weight: 700;
  color: #1a1a1a;
}
.tpl-dark .section-title-text { color: #e8e8e8; }

.section-count {
  font-size: 12px;
  color: #999;
}
.tpl-dark .section-count { color: #777; }

/* ===== 卡片列表 ===== */
.card-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 14px 12px;
}

.schedule-card {
  display: flex;
  border-radius: 14px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 6px rgba(0,0,0,0.05);
  animation: cardIn 0.35s ease both;
  transition: transform 0.15s, box-shadow 0.15s;
}
.schedule-card:active {
  transform: scale(0.985);
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.tpl-dark .schedule-card {
  background: #1a1a2e;
  box-shadow: 0 1px 6px rgba(0,0,0,0.25);
}

@keyframes cardIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.card-left-bar {
  width: 4px;
  flex-shrink: 0;
}
.bar-0 { background: #667eea; }
.bar-1 { background: #67c23a; }
.bar-2 { background: #e6a23c; }
.bar-3 { background: #f56c6c; }

.card-content {
  flex: 1;
  min-width: 0;
  padding: 14px 16px;
}

.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.card-time-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: var(--schedule-accent);
  font-weight: 500;
  background: var(--schedule-accent-light);
  padding: 3px 10px;
  border-radius: 20px;
}
.tpl-dark .card-time-badge { color: #5dcaa5; }

.personnel-tag {
  font-size: 11px;
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 负责人标签跟随主题色（Vant 默认 primary 蓝，与 dark/festive 主题不一致） */
.schedule-page .schedule-card .van-tag.van-tag--plain {
  color: var(--schedule-accent);
  border-color: var(--schedule-accent);
  background: transparent;
}

.card-topic {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.5;
  word-break: break-word;
  padding-left: 2px;
}
.tpl-dark .card-topic { color: #e8e8e8; }

/* ===== 无日程提示 ===== */
.no-schedule-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 24px 0;
  color: #bbb;
  font-size: 14px;
}
.tpl-dark .no-schedule-hint { color: #555; }

/* ===== 底部安全区 ===== */
.bottom-safe {
  height: calc(24px + env(safe-area-inset-bottom));
}
</style>
