import { createRouter, createWebHistory } from 'vue-router'

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
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
