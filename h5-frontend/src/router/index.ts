import { createRouter, createWebHistory } from 'vue-router'
import { getAdminToken } from '@/api/admin'

const routes = [
  {
    path: '/s/:code',
    name: 'Site',
    component: () => import('@/views/SiteView.vue'),
  },
  {
    path: '/s/:code/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
  },
  {
    path: '/s/:code/module/:moduleId',
    name: 'Content',
    component: () => import('@/views/ContentView.vue'),
  },
  {
    path: '/s/:code/form/:moduleId',
    name: 'Form',
    component: () => import('@/views/FormView.vue'),
  },
  {
    path: '/s/:code/schedule/:moduleId',
    name: 'Schedule',
    component: () => import('@/views/ScheduleView.vue'),
  },
  {
    path: '/s/:code/qrcode/:moduleId',
    name: 'QRCode',
    component: () => import('@/views/QRCodeView.vue'),
  },
  {
    path: '/s/:code/files/:moduleId',
    name: 'FileAttachment',
    component: () => import('@/views/FileAttachmentView.vue'),
  },
  {
    path: '/m/login',
    name: 'AdminLogin',
    component: () => import('@/views/admin/AdminLogin.vue'),
  },
  {
    path: '/m/checkin',
    name: 'AdminCheckinSites',
    component: () => import('@/views/admin/AdminCheckinSites.vue'),
    meta: { requiresAdmin: true },
  },
  {
    path: '/m/checkin/:siteId',
    name: 'AdminCheckinScan',
    component: () => import('@/views/admin/AdminCheckinScan.vue'),
    meta: { requiresAdmin: true },
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.requiresAdmin && !getAdminToken()) {
    return { path: '/m/login', replace: true }
  }
  return true
})

export default router
