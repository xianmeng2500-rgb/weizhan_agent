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
          <el-menu-item index="/checkin">
            <el-icon><Checked /></el-icon>
            <template #title>签到管理</template>
          </el-menu-item>
          <el-menu-item index="/sites">
            <el-icon><Monitor /></el-icon>
            <template #title>微站管理</template>
          </el-menu-item>
          <el-menu-item v-if="auth.canManageAccounts" index="/admin/accounts">
            <el-icon><UserFilled /></el-icon>
            <template #title>账号管理</template>
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
            <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
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
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { ElMessage } from 'element-plus'
import { ArrowRight, Fold, Expand, SwitchButton, UserFilled, Checked } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const isCollapse = ref(false)

const activeMenu = computed(() => {
  if (route.path.startsWith('/checkin')) return '/checkin'
  if (route.path.startsWith('/sites')) return '/sites'
  if (route.path.startsWith('/admin/accounts')) return '/admin/accounts'
  if (route.path.startsWith('/admin/system-config')) return '/admin/system-config'
  return route.path
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
</style>
