<template>
  <div class="module-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>模块管理</span>
          <el-button type="primary" @click="openCreate">添加模块</el-button>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" border>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="图标" width="80">
          <template #default="{ row }">
            <img v-if="row.icon" :src="row.icon" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="150" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.content_type === 'rich_text' ? '富文本' : '外部链接' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间控制" width="200">
          <template #default="{ row }">
            <div v-if="row.start_time || row.end_time" style="font-size: 12px; color: #666">
              <div v-if="row.start_time">开始: {{ formatTime(row.start_time) }}</div>
              <div v-if="row.end_time">结束: {{ formatTime(row.end_time) }}</div>
            </div>
            <span v-else>始终可用</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm title="确认删除？" @confirm="deleteModule(row)">
              <template #reference><el-button size="small" type="danger">删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 模块编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing.id ? '编辑模块' : '添加模块'" width="800px" :close-on-click-modal="false">
      <el-form :model="editing" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="editing.title" placeholder="模块标题" />
        </el-form-item>
        <el-form-item label="图标">
          <el-upload action="/api/v1/upload/image" :headers="uploadHeaders" :show-file-list="false" :on-success="onIconSuccess" accept="image/*">
            <img v-if="editing.icon" :src="editing.icon" style="width:60px; height:60px; object-fit:cover; border-radius:8px" />
            <el-button v-else size="small">上传图标</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="editing.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="内容类型">
          <el-radio-group v-model="editing.content_type">
            <el-radio value="rich_text">富文本内容</el-radio>
            <el-radio value="external_link">外部链接</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="editing.content_type === 'external_link'" label="外部链接">
          <el-input v-model="editing.external_url" placeholder="https://" />
        </el-form-item>
        <el-form-item v-if="editing.content_type === 'rich_text'" label="富文本内容">
          <div style="border: 1px solid #ccc; z-index: 100">
            <Toolbar :editor="editorRef" :defaultConfig="toolbarConfig" style="border-bottom: 1px solid #ccc" />
            <Editor v-model="editing.rich_content" :defaultConfig="editorConfig" style="height: 300px; overflow-y: hidden" @onCreated="handleEditorCreated" />
          </div>
        </el-form-item>
        <el-form-item label="开启时间">
          <el-date-picker v-model="editing.start_time" type="datetime" placeholder="不选则始终可用" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item label="关闭时间">
          <el-date-picker v-model="editing.end_time" type="datetime" placeholder="不选则始终可用" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="editing.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveModule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, shallowRef, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import api from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const auth = useAuthStore()
const siteId = route.params.id as string

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)

const uploadHeaders = computed(() => ({ Authorization: `Bearer ${auth.token}` }))

// wangEditor
const editorRef = shallowRef()
const toolbarConfig = {}
const editorConfig = {
  MENU_CONF: {
    uploadImage: {
      server: '/api/v1/upload/image',
      fieldName: 'file',
      headers: { Authorization: `Bearer ${auth.token}` },
      customInsert(res: any, insertFn: any) {
        if (res.url) insertFn(res.url)
      },
    },
  },
}

function handleEditorCreated(editor: any) {
  editorRef.value = editor
}

onBeforeUnmount(() => {
  editorRef.value?.destroy()
})

const editing = reactive({
  id: null as number | null,
  title: '',
  icon: '',
  sort_order: 0,
  content_type: 'rich_text',
  external_url: '',
  rich_content: '',
  start_time: '',
  end_time: '',
  is_active: true,
})

function formatTime(t: string) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm') : ''
}

async function loadData() {
  loading.value = true
  try {
    const res: any = await api.get(`/sites/${siteId}/modules`)
    list.value = res
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(editing, {
    id: null, title: '', icon: '', sort_order: list.value.length,
    content_type: 'rich_text', external_url: '', rich_content: '',
    start_time: '', end_time: '', is_active: true,
  })
  dialogVisible.value = true
}

function openEdit(row: any) {
  Object.assign(editing, row)
  dialogVisible.value = true
}

function onIconSuccess(res: any) {
  if (res.url) editing.icon = res.url
}

async function saveModule() {
  if (!editing.title) { ElMessage.warning('请输入标题'); return }
  saving.value = true
  try {
    const data = { ...editing }
    if (editing.id) {
      await api.put(`/sites/${siteId}/modules/${editing.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post(`/sites/${siteId}/modules`, data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

async function deleteModule(row: any) {
  await api.delete(`/sites/${siteId}/modules/${row.id}`)
  ElMessage.success('已删除')
  loadData()
}

loadData()
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
