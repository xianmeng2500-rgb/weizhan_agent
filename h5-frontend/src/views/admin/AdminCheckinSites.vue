<template>
  <div class="sites-page">
    <van-nav-bar title="签到管理" fixed placeholder>
      <template #right>
        <span class="nickname" @click="showAction = true">{{ nickname || '我' }}</span>
      </template>
    </van-nav-bar>

    <van-search v-model="keyword" placeholder="搜索微站名称" @search="onSearch" />

    <van-pull-refresh v-model="refreshing" @refresh="loadData(1, true)" class="list-wrap">
      <div v-if="!loading && items.length === 0" class="empty-wrap">
        <van-empty description="暂无开启签到的微站" />
      </div>

      <div
        v-for="item in items"
        :key="item.id"
        class="site-card"
        @click="goDetail(item)"
      >
        <div class="site-info">
          <div class="site-name van-ellipsis">{{ item.name }}</div>
          <div class="site-meta">
            <span>{{ item.session_count }} 个场次</span>
            <van-divider vertical />
            <span>报名 {{ item.registered_count }}</span>
            <van-divider vertical />
            <span class="checked">已签到 {{ item.checked_in_count }}</span>
          </div>
        </div>
        <van-icon name="arrow" color="#c8c9cc" />
      </div>

      <div v-if="items.length > 0 && finished && items.length >= total" class="list-end">
        共 {{ total }} 个微站
      </div>
    </van-pull-refresh>

    <van-action-sheet
      v-model:show="showAction"
      :actions="actions"
      cancel-text="取消"
      @select="onAction"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getCheckinProjects, ADMIN_NICKNAME_KEY, clearAdminAuth, errMsg } from '@/api/admin'

const router = useRouter()
const nickname = ref(localStorage.getItem(ADMIN_NICKNAME_KEY) || '')
const keyword = ref('')
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const finished = ref(false)
const loading = ref(false)
const refreshing = ref(false)
const showAction = ref(false)

const actions = [
  { name: '退出登录', color: '#ee0a24' },
]

async function loadData(p = 1, reset = false) {
  if (loading.value) return
  loading.value = true
  try {
    const data = await getCheckinProjects({
      page: p,
      page_size: 20,
      keyword: keyword.value.trim() || undefined,
    })
    total.value = data.total
    page.value = p
    if (reset || p === 1) {
      items.value = data.items
    } else {
      items.value.push(...data.items)
    }
    finished.value = items.value.length >= data.total
  } catch (e) {
    showToast(errMsg(e))
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function onSearch() {
  loadData(1, true)
}

function goDetail(item: any) {
  if (!item.checkin_enabled) {
    showToast('该微站未开启签到')
    return
  }
  router.push({ path: `/m/checkin/${item.id}`, query: { name: item.name } })
}

function onAction(action: any) {
  showAction.value = false
  if (action.name === '退出登录') {
    clearAdminAuth()
    router.replace('/m/login')
  }
}

onMounted(() => {
  loadData(1, true)
})

// 触底加载下一页
onMounted(() => {
  window.addEventListener('scroll', () => {
    if (finished.value || loading.value) return
    const bottom = document.documentElement.scrollHeight - window.innerHeight - window.scrollY
    if (bottom < 60) loadData(page.value + 1)
  })
})
</script>

<style scoped>
.sites-page {
  min-height: 100vh;
  background: #f5f6fa;
}
.nickname {
  font-size: 14px;
  color: #323233;
  max-width: 90px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}
.list-wrap {
  min-height: 60vh;
}
.site-card {
  margin: 10px 12px;
  padding: 14px 16px;
  background: #fff;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.site-info {
  flex: 1;
  min-width: 0;
}
.site-name {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 6px;
}
.site-meta {
  font-size: 12px;
  color: #969799;
  display: flex;
  align-items: center;
}
.checked {
  color: #07c160;
}
.list-end {
  text-align: center;
  color: #c8c9cc;
  font-size: 12px;
  padding: 12px 0 24px;
}
.empty-wrap {
  padding-top: 15vh;
}
</style>
