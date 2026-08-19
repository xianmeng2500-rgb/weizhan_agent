<template>
  <el-container class="layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo-wrap">
        <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23409eff'%3E%3Cpath d='M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5'/%3E%3C/svg%3E" class="logo-icon" />
        <span v-show="!isCollapse" class="logo-text">微站管理</span>
      </div>
      <el-scrollbar class="menu-scroll">
        <el-menu
          :default-active="activeMenu"
          :default-openeds="defaultOpeneds"
          :collapse="isCollapse"
          :collapse-transition="false"
          router
          background-color="transparent"
          text-color="#bfcbd9"
          active-text-color="#fff"
          class="side-menu"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <template #title>工作台</template>
          </el-menu-item>
          <el-sub-menu index="/sites-group">
            <template #title>
              <el-icon><Monitor /></el-icon>
              <span>微站管理</span>
            </template>
            <el-sub-menu index="/sites-list">
              <template #title>
                <el-icon><List /></el-icon>
                <span>微站列表</span>
              </template>
              <el-menu-item index="/sites">
                <el-icon><Grid /></el-icon>
                <template #title>查看全部</template>
              </el-menu-item>
              <el-menu-item
                v-for="site in sites"
                :key="site.id"
                :index="`/sites/${site.id}/edit`"
                class="site-nav-item"
              >
                <template #title>
                  <span class="site-nav-name" :title="site.name">{{ site.name }}</span>
                </template>
              </el-menu-item>
              <div v-if="sites.length > 0" class="sidebar-pagination" @click.stop>
                <el-button text size="small" :disabled="sitesPage <= 1" @click="loadSites(sitesPage - 1)">
                  <el-icon><CaretLeft /></el-icon>
                </el-button>
                <span class="page-info">{{ sitesPage }}/{{ sitesTotalPages }}</span>
                <el-button text size="small" :disabled="sitesPage >= sitesTotalPages" @click="loadSites(sitesPage + 1)">
                  <el-icon><CaretRight /></el-icon>
                </el-button>
              </div>
            </el-sub-menu>
          </el-sub-menu>
          <el-menu-item index="/ai-generate">
            <el-icon><MagicStick /></el-icon>
            <template #title>AI 生图</template>
          </el-menu-item>
          <el-sub-menu index="/checkin-group">
            <template #title>
              <el-icon><Checked /></el-icon>
              <span>签到管理</span>
            </template>
            <el-sub-menu index="/checkin-list">
              <template #title>
                <el-icon><List /></el-icon>
                <span>签到项目列表</span>
              </template>
              <el-menu-item index="/checkin">
                <el-icon><Grid /></el-icon>
                <template #title>查看全部</template>
              </el-menu-item>
              <el-menu-item
                v-for="project in checkinProjects"
                :key="project.id"
                :index="`/checkin/${project.id}`"
                class="site-nav-item"
              >
                <template #title>
                  <span class="site-nav-name" :title="project.name">{{ project.name }}</span>
                </template>
              </el-menu-item>
              <div v-if="checkinProjects.length > 0" class="sidebar-pagination" @click.stop>
                <el-button text size="small" :disabled="checkinPage <= 1" @click="loadCheckinProjects(checkinPage - 1)">
                  <el-icon><CaretLeft /></el-icon>
                </el-button>
                <span class="page-info">{{ checkinPage }}/{{ checkinTotalPages }}</span>
                <el-button text size="small" :disabled="checkinPage >= checkinTotalPages" @click="loadCheckinProjects(checkinPage + 1)">
                  <el-icon><CaretRight /></el-icon>
                </el-button>
              </div>
            </el-sub-menu>
          </el-sub-menu>
          <el-menu-item index="/billing">
            <el-icon><Wallet /></el-icon>
            <template #title>会员中心</template>
          </el-menu-item>
          <el-menu-item v-if="auth.canManageAccounts" index="/admin/accounts">
            <el-icon><UserFilled /></el-icon>
            <template #title>账号管理</template>
          </el-menu-item>
          <el-menu-item v-if="auth.isSuperAdmin" index="/admin/members">
            <el-icon><CreditCard /></el-icon>
            <template #title>会员管理</template>
          </el-menu-item>
          <el-menu-item v-if="auth.isSuperAdmin" index="/admin/system-config">
            <el-icon><Setting /></el-icon>
            <template #title>管理员配置</template>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container class="main-container">
      <!-- 顶栏 -->
      <el-header class="header" height="50px">
        <div class="header-left">
          <div class="collapse-btn" @click="isCollapse = !isCollapse">
            <el-icon :size="18"><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
          </div>
          <!-- 面包屑 -->
          <el-breadcrumb :separator-icon="ArrowRight" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <template v-if="siteId">
              <el-breadcrumb-item :to="{ path: '/sites' }">微站列表</el-breadcrumb-item>
              <el-breadcrumb-item :to="{ path: `/sites/${siteId}/edit` }">
                {{ siteStore.currentSiteName || `#${siteId}` }}
              </el-breadcrumb-item>
              <el-breadcrumb-item v-if="route.meta.title && !isSiteEditPage">{{ route.meta.title }}</el-breadcrumb-item>
            </template>
            <template v-else>
              <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
            </template>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tag
            v-if="auth.role"
            size="small"
            :type="auth.role === 'super_admin' ? 'danger' : auth.role === 'admin' ? 'warning' : 'info'"
            effect="plain"
            class="role-tag"
          >
            {{ roleText }}
          </el-tag>
          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="30" class="user-avatar">
                {{ (auth.nickname || 'U').charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="user-name">{{ auth.nickname }}</span>
              <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="app-main">
        <!-- 会员到期提醒横幅 -->
        <el-alert
          v-if="membershipRemindText"
          :title="membershipRemindText"
          type="warning"
          show-icon
          closable
          class="membership-alert"
        >
          <template #default>
            <span>{{ membershipRemindText }}</span>
            <el-button type="primary" link @click="router.push('/billing')">去续费</el-button>
          </template>
        </el-alert>
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { useSiteStore } from '@/store/site'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { ArrowRight, Fold, Expand, SwitchButton, UserFilled, Checked, List, Grid, CaretLeft, CaretRight, Wallet, CreditCard, MagicStick } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const siteStore = useSiteStore()
const isCollapse = ref(false)

// 会员到期提醒（7/3/1天）
const membershipRemindText = ref('')
async function loadMembershipRemind() {
  if (auth.isSuperAdmin) return
  try {
    const res: any = await api.get('/billing/me')
    const m = res?.membership
    if (m?.status === 'active' && m?.days_remaining != null) {
      const d = m.days_remaining
      if (d <= 1) membershipRemindText.value = `您的会员将于明天到期，请及时续费`
      else if (d <= 3 || d <= 7) membershipRemindText.value = `您的会员将于${d}天后到期，请及时续费`
    } else if (m?.status === 'expired') {
      membershipRemindText.value = '您的会员已过期，微站已变为只读，续费后可恢复编辑'
    }
  } catch {
    // ignore
  }
}

const sites = ref<any[]>([])
const sitesPage = ref(1)
const sitesPageSize = 10
const sitesTotal = ref(0)

const sitesTotalPages = computed(() => Math.ceil(sitesTotal.value / sitesPageSize) || 1)

async function loadSites(page = 1) {
  try {
    const res: any = await api.get('/sites', {
      params: { page, page_size: sitesPageSize }
    })
    sites.value = res.items || []
    sitesTotal.value = res.total || 0
    sitesPage.value = page
  } catch {
    // ignore
  }
}

const checkinProjects = ref<any[]>([])
const checkinPage = ref(1)
const checkinPageSize = 10
const checkinTotal = ref(0)

const checkinTotalPages = computed(() => Math.ceil(checkinTotal.value / checkinPageSize) || 1)

async function loadCheckinProjects(page = 1) {
  try {
    const res: any = await api.get('/checkin/projects', {
      params: { page, page_size: checkinPageSize }
    })
    checkinProjects.value = res.items || []
    checkinTotal.value = res.total || 0
    checkinPage.value = page
  } catch {
    // ignore
  }
}

const siteId = computed(() => {
  const id = route.params.id
  if (!id) return null
  const num = Number(id)
  return isNaN(num) ? null : num
})

const isSiteEditPage = computed(() => {
  return route.name === 'SiteEditPage'
})

watch(siteId, (id) => {
  if (id) {
    siteStore.loadSite(id)
  } else {
    siteStore.clear()
  }
}, { immediate: true })

const activeMenu = computed(() => {
  if (route.path.startsWith('/checkin')) {
    const m = route.path.match(/^\/checkin\/(\d+)/)
    if (m) return `/checkin/${m[1]}`
    return '/checkin'
  }
  if (route.path.startsWith('/sites')) {
    if (siteId.value) return `/sites/${siteId.value}/edit`
    return '/sites'
  }
  if (route.path.startsWith('/admin/accounts')) return '/admin/accounts'
  if (route.path.startsWith('/admin/system-config')) return '/admin/system-config'
  if (route.path.startsWith('/ai-generate')) return '/ai-generate'
  return route.path
})

const defaultOpeneds = computed(() => {
  if (route.path.startsWith('/sites')) return ['/sites-group', '/sites-list']
  if (route.path.startsWith('/checkin')) return ['/checkin-group', '/checkin-list']
  return []
})

const roleText = computed(() => {
  const map: Record<string, string> = {
    super_admin: '超级管理员',
    admin: '管理员',
    sub_admin: '子账号',
  }
  return map[auth.role] || auth.role
})

function handleCommand(cmd: string) {
  if (cmd === 'logout') {
    auth.clear()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}

onMounted(() => {
  loadSites(1)
  loadCheckinProjects(1)
  loadMembershipRemind()
})
</script>

<style scoped>
.layout {
  height: 100vh;
}

/* ===== 侧边栏 ===== */
.sidebar {
  background: var(--left-menu-bg-color);
  transition: width var(--transition-time-02);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.logo-wrap {
  height: var(--logo-height);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}
.logo-icon {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
}
.logo-text {
  color: var(--logo-title-text-color);
  font-size: 17px;
  font-weight: 600;
  white-space: nowrap;
  letter-spacing: 1px;
}
.menu-scroll {
  flex: 1;
}
/* 菜单样式覆盖 */
.side-menu {
  border: none !important;
}
.side-menu:not(.el-menu--collapse) {
  width: 220px;
}
.side-menu .el-menu-item {
  height: 50px;
  line-height: 50px;
}
.side-menu .el-menu-item:hover {
  background-color: var(--left-menu-bg-light-color) !important;
}
.side-menu .el-menu-item.is-active {
  background-color: var(--left-menu-bg-active-color) !important;
  color: var(--left-menu-text-active-color) !important;
}

/* 站点列表项 */
.site-nav-item {
  height: 38px !important;
  line-height: 38px !important;
}
.site-nav-item .site-nav-name {
  display: inline-block;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

/* 侧边栏分页 */
.sidebar-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 0;
  cursor: default;
}
.sidebar-pagination .page-info {
  font-size: 12px;
  color: #bfcbd9;
  min-width: 32px;
  text-align: center;
}
.sidebar-pagination .el-button {
  color: #bfcbd9;
  padding: 4px 6px;
  height: auto;
}
.sidebar-pagination .el-button.is-disabled {
  color: #5a5e66;
}
.sidebar-pagination .el-button:not(.is-disabled):hover {
  color: #fff;
}

/* ===== 主容器 ===== */
.main-container {
  height: 100vh;
  overflow: hidden;
}

/* ===== 顶栏 ===== */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--top-header-bg-color);
  border-bottom: 1px solid #f0f0f0;
  padding: 0 16px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.05);
  z-index: 10;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.collapse-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  cursor: pointer;
  color: #5a5e66;
  transition: all var(--transition-time-02);
}
.collapse-btn:hover {
  background: var(--top-header-hover-color);
  color: var(--el-color-primary);
}
.breadcrumb {
  font-size: 14px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.role-tag {
  border-radius: 4px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 0 8px;
  height: 50px;
  transition: all var(--transition-time-02);
}
.user-info:hover {
  background: var(--top-header-hover-color);
}
.user-avatar {
  background: var(--el-color-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}
.user-name {
  font-size: 14px;
  color: #303133;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dropdown-arrow {
  color: #909399;
  font-size: 12px;
}

/* ===== 内容区 ===== */
.app-main {
  background: var(--app-content-bg-color);
  padding: var(--app-content-padding);
  overflow-y: auto;
  overflow-x: hidden;
}
.membership-alert {
  margin-bottom: 12px;
}
</style>
