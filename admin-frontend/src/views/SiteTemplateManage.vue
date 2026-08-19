<template>
  <div class="template-manage">
    <!-- 工具栏 -->
    <el-card shadow="never" class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="模板名称">
          <el-input v-model="searchForm.keyword" placeholder="请输入模板名称" clearable style="width: 220px" @keyup.enter="loadData" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 140px" @change="loadData">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 模板卡片列表 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Files /></el-icon>
            微站模板
          </span>
          <el-button type="primary" :icon="Plus" @click="router.push('/templates/create')">新建模板</el-button>
        </div>
      </template>

      <div v-loading="loading" class="template-grid">
        <div v-for="tpl in list" :key="tpl.id" class="template-card" :class="{ inactive: tpl.status !== 'active' }">
          <!-- 预览区 -->
          <div class="card-preview" :class="'tpl-' + tpl.template_key">
            <img v-if="tpl.preview_image" :src="tpl.preview_image" class="preview-img" />
            <div v-else class="preview-placeholder">
              <span class="style-name">{{ templateKeyMap[tpl.template_key] || tpl.template_key }}</span>
            </div>
            <div class="preview-overlay">
              <el-tag v-if="tpl.is_system" type="warning" size="small" effect="dark">系统</el-tag>
              <el-tag :type="tpl.status === 'active' ? 'success' : 'info'" size="small" effect="dark">
                {{ tpl.status === 'active' ? '启用' : '停用' }}
              </el-tag>
            </div>
          </div>
          <!-- 信息区 -->
          <div class="card-info">
            <div class="info-title">{{ tpl.name }}</div>
            <div class="info-desc">{{ tpl.description || '暂无描述' }}</div>
            <div class="info-tags">
              <el-tag size="small" type="info">{{ templateKeyMap[tpl.template_key] || tpl.template_key }}</el-tag>
              <el-tag size="small" type="info">{{ layoutMap[tpl.layout] || tpl.layout }}</el-tag>
              <el-tag v-if="tpl.title_config?.enabled" size="small" type="warning">标题装饰</el-tag>
              <el-tag v-if="moduleCount(tpl) > 0" size="small" type="info">预置模块 {{ moduleCount(tpl) }} 个</el-tag>
            </div>
            <div class="card-actions">
              <el-button link type="primary" size="small" @click="router.push(`/templates/edit/${tpl.id}`)">编辑</el-button>
              <el-button link size="small" :type="tpl.status === 'active' ? 'info' : 'success'" @click="toggleStatus(tpl)">
                {{ tpl.status === 'active' ? '停用' : '启用' }}
              </el-button>
              <el-button v-if="!tpl.is_system" link type="danger" size="small" @click="deleteTemplate(tpl)">删除</el-button>
            </div>
          </div>
        </div>
        <el-empty v-if="!loading && list.length === 0" description="暂无模板，点击右上角新建" class="grid-empty" />
      </div>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[12, 24, 48]"
        layout="total, prev, pager, next"
        style="margin-top: 16px"
        @current-change="loadData"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Files } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()

const list = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const searchForm = reactive({ keyword: '', status: '' })

const templateKeyMap: Record<string, string> = { default: '默认', classic: '经典蓝紫', dark: '暗夜科技', festive: '节日红金' }
const layoutMap: Record<string, string> = { grid: '九宫格', button: '按钮列表', free: '自由拖拽' }

function moduleCount(tpl: any): number {
  return Array.isArray(tpl.modules_config) ? tpl.modules_config.length : 0
}

async function loadData() {
  loading.value = true
  try {
    const res: any = await api.get('/templates', {
      params: {
        page: page.value,
        page_size: pageSize.value,
        keyword: searchForm.keyword || undefined,
        status: searchForm.status || undefined,
      },
    })
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function resetSearch() {
  searchForm.keyword = ''
  searchForm.status = ''
  page.value = 1
  loadData()
}

async function toggleStatus(tpl: any) {
  const newStatus = tpl.status === 'active' ? 'inactive' : 'active'
  await api.put(`/templates/${tpl.id}`, { status: newStatus })
  ElMessage.success(newStatus === 'active' ? '已启用' : '已停用')
  loadData()
}

async function deleteTemplate(tpl: any) {
  await ElMessageBox.confirm(`确认删除模板「${tpl.name}」？已创建的微站不受影响。`, '删除模板', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
  await api.delete(`/templates/${tpl.id}`)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.search-card {
  margin-bottom: 16px;
}
.search-card :deep(.el-card__body) {
  padding: 18px 20px 0;
}
.search-form {
  display: flex;
  flex-wrap: wrap;
}
.table-card :deep(.el-card__body) {
  padding: 16px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.card-title .el-icon {
  color: var(--el-color-primary);
}

/* 模板卡片网格 */
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  min-height: 200px;
}
.grid-empty {
  grid-column: 1 / -1;
}
.template-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.2s;
  background: #fff;
}
.template-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.template-card.inactive {
  opacity: 0.65;
}
.card-preview {
  position: relative;
  height: 140px;
  overflow: hidden;
}
.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
/* 风格占位背景（与 H5 模板样式一致） */
.preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tpl-default .preview-placeholder {
  background: #ffffff;
}
.tpl-classic .preview-placeholder {
  background: linear-gradient(135deg, #c5cef5 0%, #c8bde0 100%);
}
.tpl-dark .preview-placeholder {
  background: linear-gradient(135deg, #4a4a68 0%, #3e3e5a 100%);
}
.tpl-festive .preview-placeholder {
  background: linear-gradient(135deg, #e8c5c5 0%, #e0b8b8 100%);
}
.style-name {
  font-size: 15px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.45);
}
.tpl-dark .style-name {
  color: rgba(255, 255, 255, 0.75);
}
.preview-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 6px;
}
.card-info {
  padding: 12px;
}
.info-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.info-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  height: 32px;
  line-height: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.info-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.card-actions {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
}
</style>
