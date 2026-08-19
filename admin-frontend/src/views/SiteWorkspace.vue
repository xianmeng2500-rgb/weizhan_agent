<template>
  <div class="site-workspace">
    <!-- 顶部站点信息栏 -->
    <div class="workspace-header">
      <div class="header-left">
        <el-button text :icon="ArrowLeft" @click="router.push('/sites')">返回列表</el-button>
        <el-divider direction="vertical" />
        <span class="site-name">{{ siteName || '加载中...' }}</span>
        <el-tag :type="statusTagType" size="small" effect="light">{{ statusText }}</el-tag>
      </div>
      <div class="header-right">
        <el-button size="small" :href="previewUrl" target="_blank" tag="a">预览</el-button>
        <el-button
          size="small"
          :type="siteStatus === 'online' ? 'danger' : 'success'"
          plain
          @click="toggleStatus"
        >{{ siteStatus === 'online' ? '下线' : '上线' }}</el-button>
        <el-popconfirm title="确认删除此微站？删除后不可恢复" @confirm="deleteSite">
          <template #reference>
            <el-button size="small" type="danger" plain>删除</el-button>
          </template>
        </el-popconfirm>
      </div>
    </div>

    <!-- Tab 导航栏 -->
    <div class="workspace-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="workspace-tab"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        <el-icon v-if="tab.icon"><component :is="tab.icon" /></el-icon>
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <!-- 内容区域 -->
    <div class="workspace-content">
      <SiteEdit v-show="activeTab === 'editor'" ref="editorRef" :key="siteId" />
      <ModuleManage v-if="mountedTabs.has('modules')" v-show="activeTab === 'modules'" :key="'modules-' + siteId" />
      <AccountManage v-if="mountedTabs.has('accounts')" v-show="activeTab === 'accounts'" :key="'accounts-' + siteId" />
      <Stats v-if="mountedTabs.has('stats')" v-show="activeTab === 'stats'" :key="'stats-' + siteId" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, provide, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Monitor, Grid, UserFilled, TrendCharts } from '@element-plus/icons-vue'
import api from '@/api'
import SiteEdit from './SiteEdit.vue'
import ModuleManage from './ModuleManage.vue'
import AccountManage from './AccountManage.vue'
import Stats from './Stats.vue'

const route = useRoute()
const router = useRouter()
const siteId = computed(() => route.params.id as string)

const siteName = ref('')
const siteStatus = ref('draft')
const h5Domain = ref('')
const siteCode = ref('')
const needLogin = ref(false)
const editorRef = ref()

const activeTab = ref('editor')
const mountedTabs = ref(new Set<string>(['editor']))

const tabs = computed(() => {
  const list = [
    { key: 'editor', label: '可视化编辑', icon: Monitor },
    { key: 'modules', label: '模块管理', icon: Grid },
  ]
  if (needLogin.value) {
    list.push({ key: 'accounts', label: '账号管理', icon: UserFilled })
  }
  list.push({ key: 'stats', label: '数据统计', icon: TrendCharts })
  return list
})

const statusText = computed(() => {
  const map: Record<string, string> = { draft: '草稿', online: '在线', offline: '已下线' }
  return map[siteStatus.value] || siteStatus.value
})

const statusTagType = computed(() => {
  const map: Record<string, string> = { draft: 'info', online: 'success', offline: 'danger' }
  return map[siteStatus.value] || 'info'
})

const previewUrl = computed(() => {
  const base = (h5Domain.value || '').replace(/\/$/, '')
  return siteCode.value ? `${base}/s/${siteCode.value}` : '#'
})

// 提供给 SiteEdit 调用的切 Tab 方法
provide('switchWorkspaceTab', (tab: string) => {
  switchTab(tab)
})

// 也提供 siteStatus 给 SiteEdit 读取
provide('workspaceSiteStatus', siteStatus)

function switchTab(tab: string) {
  activeTab.value = tab
  if (!mountedTabs.value.has(tab)) {
    mountedTabs.value.add(tab)
  }
}

async function loadSiteInfo() {
  if (!siteId.value) return
  try {
    const [res, systemConfig]: any[] = await Promise.all([
      api.get(`/sites/${siteId.value}`),
      api.get('/system-config/runtime').catch(() => ({ h5_domain: '' })),
    ])
    siteName.value = res.name
    siteStatus.value = res.status || 'draft'
    siteCode.value = res.code || ''
    h5Domain.value = systemConfig.h5_domain || ''
    needLogin.value = res.need_login || false
  } catch {
    ElMessage.error('加载站点信息失败')
  }
}

async function toggleStatus() {
  const newStatus = siteStatus.value === 'online' ? 'offline' : 'online'
  try {
    await api.put(`/sites/${siteId.value}/status`, { status: newStatus })
    siteStatus.value = newStatus
    ElMessage.success(newStatus === 'online' ? '已上线' : '已下线')
    // 同步给 SiteEdit
    if (editorRef.value) {
      editorRef.value.updateSiteStatus?.(newStatus)
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

async function deleteSite() {
  try {
    await api.delete(`/sites/${siteId.value}`)
    ElMessage.success('已删除')
    router.replace('/sites')
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  // 支持通过 ?tab=modules 直接定位到对应 Tab
  const queryTab = route.query.tab as string
  if (queryTab && tabs.value.some(t => t.key === queryTab)) {
    switchTab(queryTab)
  }
  loadSiteInfo()
})

// 监听路由参数变化
watch(siteId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    activeTab.value = 'editor'
    mountedTabs.value = new Set(['editor'])
    loadSiteInfo()
  }
})

// 监听 query.tab 变化
watch(() => route.query.tab, (newTab) => {
  if (newTab && typeof newTab === 'string' && tabs.value.some(t => t.key === newTab)) {
    switchTab(newTab)
  }
})
</script>

<style scoped>
.site-workspace {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 50px - 32px);
  margin: -16px;
  background: var(--app-content-bg-color);
}

.workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.site-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.workspace-tabs {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 0 20px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
  margin-bottom: 16px;
}

.workspace-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.workspace-tab:hover {
  color: #409eff;
}

.workspace-tab.active {
  color: #409eff;
  border-bottom-color: #409eff;
  font-weight: 500;
}

.workspace-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 嵌入 SiteEdit 时覆盖其高度计算 */
.workspace-content :deep(.visual-editor) {
  height: 100%;
  margin: 0;
}
</style>
