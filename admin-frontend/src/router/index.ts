import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
  },
  {
    path: '/',
    component: () => import('@/layout/Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '工作台' } },
      { path: 'checkin', name: 'CheckinList', component: () => import('@/views/CheckinList.vue'), meta: { title: '签到管理' } },
      { path: 'checkin/:id', name: 'CheckinDetail', component: () => import('@/views/CheckinDetail.vue'), meta: { title: '签到管理' } },
      { path: 'sites', name: 'SiteList', component: () => import('@/views/SiteList.vue'), meta: { title: '微站管理' } },
      { path: 'sites/create', name: 'SiteCreate', component: () => import('@/views/SiteEdit.vue'), meta: { title: '创建微站' } },
      { path: 'sites/:id/edit', name: 'SiteEditPage', component: () => import('@/views/SiteEdit.vue'), meta: { title: '编辑微站' } },
      { path: 'sites/:id/modules', name: 'ModuleManage', component: () => import('@/views/ModuleManage.vue'), meta: { title: '模块管理' } },
      { path: 'sites/:id/modules/:moduleId/submissions', name: 'FormSubmissions', component: () => import('@/views/FormSubmissions.vue'), meta: { title: '报名数据' } },
      { path: 'sites/:id/accounts', name: 'AccountManage', component: () => import('@/views/AccountManage.vue'), meta: { title: '账号管理' } },
      { path: 'sites/:id/stats', name: 'Stats', component: () => import('@/views/Stats.vue'), meta: { title: '数据统计' } },
      { path: 'admin/accounts', name: 'AdminAccounts', component: () => import('@/views/AdminAccounts.vue'), meta: { title: '账号管理' } },
      { path: 'admin/system-config', name: 'SystemConfig', component: () => import('@/views/SystemConfig.vue'), meta: { title: '管理员配置', requiresSuperAdmin: true } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory('/admin/'),
  routes,
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  const token = auth.token
  if (to.name !== 'Login' && !token) {
    next({ name: 'Login' })
  } else if (to.meta.requiresSuperAdmin && auth.role && !auth.isSuperAdmin) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
