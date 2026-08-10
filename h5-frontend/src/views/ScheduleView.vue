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

    <!-- 日历主体 -->
    <div v-else class="calendar-container">
      <!-- 月切换 -->
      <div class="month-nav">
        <div class="month-nav-btn" @click="prevMonth">
          <van-icon name="arrow-left" size="18" />
        </div>
        <div class="month-label">{{ currentYear }}年 {{ currentMonth }}月</div>
        <div class="month-nav-btn" @click="nextMonth">
          <van-icon name="arrow" size="18" />
        </div>
      </div>

      <!-- 星期头 -->
      <div class="weekday-row">
        <span v-for="w in weekNames" :key="w" class="weekday-cell" :class="{ weekend: w === '六' || w === '日' }">{{ w }}</span>
      </div>

      <!-- 日期网格 -->
      <div class="date-grid">
        <div
          v-for="(cell, idx) in calendarCells"
          :key="idx"
          class="date-cell"
          :class="{
            'is-other-month': !cell.isCurrentMonth,
            'is-today': cell.isToday,
            'is-selected': cell.date === selectedDate,
            'has-schedule': cell.hasSchedule,
          }"
          @click="onDateClick(cell)"
        >
          <span class="date-num">{{ cell.day }}</span>
          <span v-if="cell.hasSchedule" class="date-dot"></span>
        </div>
      </div>

      <!-- 选中日期分隔线 -->
      <div v-if="selectedDate" class="section-divider">
        <span class="divider-label">{{ formatSelectedLabel() }}</span>
      </div>

      <!-- 下方卡片列表 -->
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const moduleId = route.params.moduleId as string
const code = route.params.code as string

const loading = ref(true)
const moduleTitle = ref('')
const siteTheme = ref('classic')
const rawItems = ref<any[]>([])

const weekNames = ['日', '一', '二', '三', '四', '五', '六']

// 当前显示的月份
const now = new Date()
const currentYear = ref(now.getFullYear())
const currentMonth = ref(now.getMonth() + 1)

// 选中的日期 YYYY-MM-DD
const selectedDate = ref('')

interface CalendarCell {
  date: string         // YYYY-MM-DD
  day: number
  isCurrentMonth: boolean
  isToday: boolean
  hasSchedule: boolean
}

// 快速查询某天是否有日程
const scheduleDateSet = computed(() => {
  const s = new Set<string>()
  for (const item of rawItems.value) {
    if (item.date) s.add(item.date)
  }
  return s
})

const todayStr = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

const calendarCells = computed<CalendarCell[]>(() => {
  const y = currentYear.value
  const m = currentMonth.value

  const firstDay = new Date(y, m - 1, 1)
  const lastDay = new Date(y, m, 0)
  const daysInMonth = lastDay.getDate()
  const startDow = firstDay.getDay() // 0=日

  const cells: CalendarCell[] = []

  // 上月填充
  const prevLastDay = new Date(y, m - 1, 0).getDate()
  for (let i = startDow - 1; i >= 0; i--) {
    const d = prevLastDay - i
    const ds = formatDate(y, m - 1, d)
    cells.push({ date: ds, day: d, isCurrentMonth: false, isToday: ds === todayStr.value, hasSchedule: scheduleDateSet.value.has(ds) })
  }

  // 本月
  for (let d = 1; d <= daysInMonth; d++) {
    const ds = formatDate(y, m, d)
    cells.push({ date: ds, day: d, isCurrentMonth: true, isToday: ds === todayStr.value, hasSchedule: scheduleDateSet.value.has(ds) })
  }

  // 下月填充（补满 6 行 × 7 列 = 42）
  const remaining = 42 - cells.length
  for (let d = 1; d <= remaining; d++) {
    const mon = m === 12 ? 1 : m + 1
    const yr = m === 12 ? y + 1 : y
    const ds = formatDate(yr, mon, d)
    cells.push({ date: ds, day: d, isCurrentMonth: false, isToday: ds === todayStr.value, hasSchedule: scheduleDateSet.value.has(ds) })
  }

  return cells
})

const selectedSchedules = computed(() => {
  if (!selectedDate.value) return []
  return rawItems.value
    .filter((i: any) => i.date === selectedDate.value)
    .sort((a: any, b: any) => (a.time || '').localeCompare(b.time || ''))
})

function formatDate(y: number, m: number, d: number) {
  return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

const navBarStyle = computed(() => {
  if (siteTheme.value === 'dark') {
    return { '--van-nav-bar-background': '#1a1a2e', '--van-nav-bar-text-color': '#e0e0e0', '--van-nav-bar-icon-color': '#e0e0e0' }
  }
  return {}
})

function prevMonth() {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

function nextMonth() {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

function onDateClick(cell: CalendarCell) {
  if (cell.date === selectedDate.value) {
    selectedDate.value = '' // 取消选中
  } else {
    selectedDate.value = cell.date
    // 如果点击的日期不在当前月，跳过去
    if (!cell.isCurrentMonth) {
      const parts = cell.date.split('-')
      currentYear.value = parseInt(parts[0])
      currentMonth.value = parseInt(parts[1])
    }
  }
}

function formatSelectedLabel() {
  if (!selectedDate.value) return ''
  const d = new Date(selectedDate.value.replace(/-/g, '/'))
  const m = d.getMonth() + 1
  const day = d.getDate()
  const w = weekNames[d.getDay()]
  return `${m}月${day}日 ${w}`
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

    // 默认选中今天
    selectedDate.value = todayStr.value
  } catch {
    // 错误已在拦截器处理
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
}

/* ===== 主题变量 ===== */
.tpl-classic { --schedule-accent: #667eea; --schedule-accent-light: #eef0fd; --schedule-accent-soft: #f0f2ff; }
.tpl-dark {
  --schedule-accent: #5dcaa5;
  --schedule-accent-light: rgba(93, 202, 165, 0.15);
  --schedule-accent-soft: rgba(93, 202, 165, 0.06);
  background: #0f0f1a;
  color: #e0e0e0;
}
.tpl-festive {
  --schedule-accent: #e74c3c;
  --schedule-accent-light: rgba(231, 76, 60, 0.1);
  --schedule-accent-soft: rgba(231, 76, 60, 0.05);
}

.page-loading {
  display: flex;
  justify-content: center;
  padding-top: 120px;
}

/* ========== 日历容器 ========== */
.calendar-container {
  padding: 0 12px;
}

/* ===== 月切换 ===== */
.month-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 4px 12px;
}

.month-label {
  font-size: 17px;
  font-weight: 700;
  color: #1a1a1a;
  letter-spacing: 0.5px;
}
.tpl-dark .month-label { color: #e8e8e8; }

.month-nav-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: #666;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: all 0.2s;
}
.month-nav-btn:active {
  background: var(--schedule-accent);
  color: #fff;
}
.tpl-dark .month-nav-btn {
  background: #1a1a2e;
  color: #aaa;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}

/* ===== 星期头 ===== */
.weekday-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  margin-bottom: 4px;
}

.weekday-cell {
  text-align: center;
  font-size: 12px;
  color: #999;
  font-weight: 500;
  padding: 6px 0;
}
.weekday-cell.weekend { color: #e74c3c; }
.tpl-dark .weekday-cell { color: #666; }
.tpl-dark .weekday-cell.weekend { color: #f56c6c; }

/* ===== 日期网格 ===== */
.date-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.date-cell {
  aspect-ratio: 1 / 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  border-radius: 12px;
  cursor: pointer;
  position: relative;
  transition: background 0.15s;
  -webkit-tap-highlight-color: transparent;
}

.date-num {
  font-size: 15px;
  color: #333;
  font-weight: 500;
  line-height: 1;
}
.is-other-month .date-num {
  color: #ccc;
}
.tpl-dark .date-num { color: #ddd; }
.tpl-dark .is-other-month .date-num { color: #444; }

.date-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--schedule-accent);
  flex-shrink: 0;
}

/* 今天 */
.is-today {
  background: var(--schedule-accent-soft);
}
.is-today .date-num {
  color: var(--schedule-accent);
  font-weight: 700;
}

/* 选中 */
.is-selected {
  background: var(--schedule-accent) !important;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.35);
}
.is-selected .date-num {
  color: #fff !important;
  font-weight: 700;
}
.is-selected .date-dot {
  background: #fff;
}
.tpl-festive .is-selected { box-shadow: 0 2px 8px rgba(231, 76, 60, 0.35); }
.tpl-dark .is-selected { box-shadow: 0 2px 8px rgba(93, 202, 165, 0.35); }

/* 有日程的普通日期 hover */
.has-schedule:not(.is-selected):not(.is-other-month):active {
  background: var(--schedule-accent-light);
}

/* ===== 分隔线 ===== */
.section-divider {
  display: flex;
  align-items: center;
  padding: 16px 4px 12px;
}

.section-divider::before,
.section-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e8e8e8;
}
.tpl-dark .section-divider::before,
.tpl-dark .section-divider::after {
  background: #2a2a3e;
}

.divider-label {
  padding: 0 14px;
  font-size: 13px;
  color: #999;
  font-weight: 500;
  white-space: nowrap;
}
.tpl-dark .divider-label { color: #777; }

/* ===== 卡片列表 ===== */
.card-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 4px 12px;
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
