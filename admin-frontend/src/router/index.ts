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
      { path: 'sites', name: 'SiteList', component: () => import('@/views/SiteList.vue'), meta: { title: '微站管理' } },
      { path: 'sites/create', name: 'SiteCreate', component: () => import('@/views/SiteEdit.vue'), meta: { title: '创建微站' } },
      { path: 'sites/:id/edit', name: 'SiteEditPage', component: () => import('@/views/SiteEdit.vue'), meta: { title: '编辑微站' } },
      { path: 'sites/:id/modules', name: 'ModuleManage', component: () => import('@/views/ModuleManage.vue'), meta: { title: '模块管理' } },
      { path: 'sites/:id/accounts', name: 'AccountManage', component: () => import('@/views/AccountManage.vue'), meta: { title: '账号管理' } },
      { path: 'sites/:id/stats', name: 'Stats', component: () => import('@/views/Stats.vue'), meta: { title: '数据统计' } },
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
  } else {
    next()
  }
})

export default router
