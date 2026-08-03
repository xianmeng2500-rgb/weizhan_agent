<template>
  <el-container class="layout">
    <el-aside width="200px" class="sidebar">
      <div class="logo">微站管理</div>
      <el-menu :default-active="activeMenu" router class="menu">
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/sites">
          <el-icon><Monitor /></el-icon>
          <span>微站管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="page-title">{{ route.meta.title || '微站管理后台' }}</span>
        <div class="user-info">
          <el-dropdown @command="handleCommand">
            <span class="user-name">
              {{ auth.nickname }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeMenu = computed(() => {
  if (route.path.startsWith('/sites')) return '/sites'
  return route.path
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
.layout { height: 100vh; }
.sidebar {
  background: #001529; color: #fff; overflow: hidden;
}
.logo {
  height: 60px; line-height: 60px; text-align: center;
  font-size: 18px; font-weight: bold; color: #fff;
  border-bottom: 1px solid #333;
}
.menu { border: none; background: transparent; }
.menu .el-menu-item { color: #bbb; }
.menu .el-menu-item:hover, .menu .el-menu-item.is-active { color: #fff; background: #1890ff; }
.header {
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid #e8e8e8; background: #fff;
}
.page-title { font-size: 16px; font-weight: 500; }
.user-name { cursor: pointer; display: flex; align-items: center; gap: 4px; color: #333; }
.main { background: #f0f2f5; overflow-y: auto; }
</style>
