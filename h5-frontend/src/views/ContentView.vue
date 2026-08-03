<template>
  <div class="content-page">
    <van-nav-bar :title="content.title" left-arrow @click-left="goBack" />
    <div class="rich-content" v-if="content.rich_content" v-html="content.rich_content"></div>
    <van-empty v-else description="暂无内容" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const moduleId = route.params.moduleId as string

const content = ref<any>({})

async function loadContent() {
  try {
    content.value = await api.get(`/p/modules/${moduleId}`)
  } catch {
    // 错误已在拦截器处理
  }
}

function goBack() {
  const code = route.params.code as string
  router.push(`/s/${code}`)
}

onMounted(loadContent)
</script>

<style scoped>
.content-page { min-height: 100vh; background: #fff; }
.rich-content { padding: 16px; overflow-x: hidden; }
.rich-content :deep(img) { max-width: 100% !important; height: auto !important; }
.rich-content :deep(p) { margin: 8px 0; line-height: 1.6; }
.rich-content :deep(h1), .rich-content :deep(h2), .rich-content :deep(h3) { margin: 16px 0 8px; }
.rich-content :deep(table) { width: 100% !important; }
.rich-content :deep(video) { max-width: 100%; }
</style>
