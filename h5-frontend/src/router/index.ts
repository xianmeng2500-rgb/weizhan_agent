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
