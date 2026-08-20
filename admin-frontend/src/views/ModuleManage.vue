<template>
  <div class="module-manage">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Grid /></el-icon>
            模块管理
          </span>
          <el-button type="primary" :icon="Plus" @click="openCreate">添加模块</el-button>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" stripe>
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
            <el-tag size="small">{{ typeText(row.content_type) }}</el-tag>
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
            <el-button v-if="row.content_type === 'registration_form'" size="small" type="success" @click="goSubmissions(row)">数据</el-button>
            <el-popconfirm title="确认删除？" @confirm="deleteModule(row)">
              <template #reference><el-button size="small" type="danger">删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 模块编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editing.id ? '编辑模块' : '添加模块'"
      width="92vw"
      top="4vh"
      class="fullscreen-dialog"
      :close-on-click-modal="false"
    >
      <div class="dialog-body">
      <el-form :model="editing" label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="editing.title" placeholder="模块标题" />
        </el-form-item>
        <el-form-item label="图标">
          <IconPicker :model-value="editing.icon" @update:model-value="(v: string) => (editing.icon = v)" />
          <div class="form-tip">可从图标库选择或上传自定义图标，建议 128×128 正方形</div>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="editing.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="内容类型">
          <el-radio-group v-model="editing.content_type" @change="handleContentTypeChange">
            <el-radio value="rich_text">富文本内容</el-radio>
            <el-radio value="external_link">外部链接</el-radio>
            <el-radio value="registration_form">报名表单</el-radio>
            <el-radio value="schedule">日程安排</el-radio>
            <el-radio v-if="needCheckin" value="qrcode">我的二维码</el-radio>
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
        <el-form-item v-if="editing.content_type === 'registration_form'" label="报名表单">
          <div class="form-designer-entry">
            <div class="form-designer-entry__icon">
              <el-icon><EditPen /></el-icon>
            </div>
            <div class="form-designer-entry__content">
              <strong>{{ editing.form_config.title || '未命名报名表单' }}</strong>
              <span>已配置 {{ editing.form_config.fields?.length || 0 }} 个表单字段</span>
            </div>
            <el-button type="primary" @click="formDesignerVisible = true">
              {{ editing.form_config.fields?.length ? '编辑表单' : '开始设计' }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item v-if="editing.content_type === 'schedule'" label="日程安排">
          <div class="form-designer-entry">
            <div class="form-designer-entry__icon">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="form-designer-entry__content">
              <strong>日程安排</strong>
              <span>已配置 {{ editing.schedule_config?.items?.length || 0 }} 条日程</span>
            </div>
            <el-button type="primary" @click="scheduleEditorVisible = true">
              {{ editing.schedule_config?.items?.length ? '编辑日程' : '开始编辑' }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item v-if="editing.content_type === 'qrcode'" label="二维码配置">
          <div class="form-designer-entry">
            <div class="form-designer-entry__icon">
              <el-icon><PictureFilled /></el-icon>
            </div>
            <div class="form-designer-entry__content">
              <strong>我的二维码</strong>
              <span>{{ editing.qrcode_config?.hint || '未配置提示信息' }}</span>
            </div>
            <el-button type="primary" @click="qrcodeEditorVisible = true">
              编辑配置
            </el-button>
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
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveModule">保存</el-button>
      </template>
    </el-dialog>

    <!-- 报名表单设计器：独立最大化工作区 -->
    <el-dialog
      v-model="formDesignerVisible"
      class="form-designer-dialog"
      title="报名表单设计"
      fullscreen
      append-to-body
      :close-on-click-modal="false"
    >
      <div class="form-designer-dialog__body">
        <FormDesigner v-model="editing.form_config" />
      </div>
      <template #footer>
        <el-button @click="formDesignerVisible = false">返回模块编辑</el-button>
        <el-button type="primary" @click="confirmFormDesign">完成设计</el-button>
      </template>
    </el-dialog>

    <!-- 日程安排编辑器：独立全屏工作区 -->
    <el-dialog
      v-model="scheduleEditorVisible"
      class="form-designer-dialog"
      title="日程安排编辑"
      fullscreen
      append-to-body
      :close-on-click-modal="false"
    >
      <div class="form-designer-dialog__body">
        <ScheduleEditor
          ref="scheduleEditorRef"
          v-model="editing.schedule_config"
          :site-id="Number(siteId)"
          :module-id="editing.id || 0"
        />
      </div>
      <template #footer>
        <el-button @click="scheduleEditorVisible = false">返回模块编辑</el-button>
        <el-button type="primary" @click="confirmScheduleDesign">完成编辑</el-button>
      </template>
    </el-dialog>

    <!-- 二维码配置编辑器：独立全屏工作区 -->
    <el-dialog
      v-model="qrcodeEditorVisible"
      class="form-designer-dialog"
      title="我的二维码配置"
      fullscreen
      append-to-body
      :close-on-click-modal="false"
    >
      <div class="form-designer-dialog__body">
        <QRCodeEditor
          ref="qrcodeEditorRef"
          v-model="editing.qrcode_config"
          :site-id="Number(siteId)"
        />
      </div>
      <template #footer>
        <el-button @click="qrcodeEditorVisible = false">返回模块编辑</el-button>
        <el-button type="primary" @click="confirmQRCodeDesign">完成配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, shallowRef, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { EditPen, Grid, Plus, Calendar, PictureFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import FormDesigner from '@/components/FormDesigner'
import ScheduleEditor from '@/components/ScheduleEditor'
import QRCodeEditor from '@/components/QRCodeEditor'
import IconPicker from '@/components/IconPicker.vue'
import api from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const siteId = route.params.id as string

const list = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const formDesignerVisible = ref(false)
const scheduleEditorVisible = ref(false)
const qrcodeEditorVisible = ref(false)
const scheduleEditorRef = ref()
const qrcodeEditorRef = ref()
const needCheckin = ref(false)

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
  form_config: {
    title: '',
    description: '',
    buttonText: '提交',
    allowEditAfterSubmit: false,
    fields: [],
  },
  schedule_config: { items: [] } as { items: any[] },
  qrcode_config: { hint: '', display_fields: [] as string[] },
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
    const [res, siteInfo]: any[] = await Promise.all([
      api.get(`/sites/${siteId}/modules`),
      api.get(`/sites/${siteId}`),
    ])
    list.value = res
    needCheckin.value = siteInfo.need_checkin || false
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(editing, {
    id: null, title: '', icon: '', sort_order: list.value.length,
    content_type: 'rich_text', external_url: '', rich_content: '',
    form_config: { title: '', description: '', buttonText: '提交', allowEditAfterSubmit: false, fields: [] },
    schedule_config: { items: [] },
    qrcode_config: { hint: '', display_fields: [] },
    start_time: '', end_time: '', is_active: true,
  })
  dialogVisible.value = true
}

function openEdit(row: any) {
  Object.assign(editing, {
    ...row,
    form_config: row.form_config || { title: '', description: '', buttonText: '提交', allowEditAfterSubmit: false, fields: [] },
    schedule_config: row.schedule_config || { items: [] },
    qrcode_config: row.qrcode_config || { hint: '', display_fields: [] },
  })
  dialogVisible.value = true
}

function handleContentTypeChange(contentType: string | number | boolean | undefined) {
  if (contentType === 'registration_form') {
    formDesignerVisible.value = true
  } else if (contentType === 'schedule') {
    scheduleEditorVisible.value = true
  } else if (contentType === 'qrcode') {
    qrcodeEditorVisible.value = true
  }
}

function confirmFormDesign() {
  if (!editing.form_config.title?.trim()) {
    ElMessage.warning('请先填写表单标题')
    return
  }
  formDesignerVisible.value = false
  ElMessage.success('表单设计已保存到当前模块')
}

function confirmScheduleDesign() {
  // 确保子组件最新数据已同步回 editing
  const cfg = scheduleEditorRef.value?.getConfig?.()
  if (cfg) editing.schedule_config = cfg
  scheduleEditorVisible.value = false
  ElMessage.success('日程安排已保存到当前模块')
}

function confirmQRCodeDesign() {
  const cfg = qrcodeEditorRef.value?.getConfig?.()
  if (cfg) editing.qrcode_config = cfg
  qrcodeEditorVisible.value = false
  ElMessage.success('二维码配置已保存到当前模块')
}

async function saveModule() {
  if (!editing.title) { ElMessage.warning('请输入标题'); return }
  if (editing.content_type === 'registration_form') {
    if (!editing.form_config?.title?.trim()) {
      ElMessage.warning('请输入表单标题')
      return
    }
  }
  saving.value = true
  try {
    // 清理空字符串和空值，避免后端 Pydantic 校验失败
    const data: Record<string, any> = {}
    for (const [key, value] of Object.entries(editing)) {
      if (value === '' || value === null || value === undefined) continue
      data[key] = value
    }
    // 报名表单时清理不相关字段
    if (editing.content_type === 'registration_form') {
      delete data.rich_content
      delete data.external_url
    }
    // 富文本时清理表单配置（可选，保留也无妨）
    if (editing.content_type === 'rich_text') {
      delete data.form_config
      delete data.external_url
    }
    if (editing.content_type === 'external_link') {
      delete data.rich_content
      delete data.form_config
      delete data.schedule_config
    }
    if (editing.content_type === 'schedule') {
      delete data.rich_content
      delete data.external_url
      delete data.form_config
      delete data.qrcode_config
    }
    if (editing.content_type === 'qrcode') {
      delete data.rich_content
      delete data.external_url
      delete data.form_config
      delete data.schedule_config
    }
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

function typeText(contentType: string) {
  const map: Record<string, string> = {
    rich_text: '富文本',
    external_link: '外部链接',
    registration_form: '报名表单',
    schedule: '日程安排',
    qrcode: '我的二维码',
  }
  return map[contentType] || contentType
}

function goSubmissions(row: any) {
  router.push(`/sites/${siteId}/modules/${row.id}/submissions`)
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
.form-tip { font-size: 12px; color: #909399; line-height: 1.5; width: 100%; }
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
.dialog-body { padding-right: 8px; }
.form-designer-entry {
  width: min(720px, 100%);
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid #d9e8ff;
  border-radius: 10px;
  background: linear-gradient(135deg, #f4f8ff 0%, #fbfdff 100%);
}
.form-designer-entry__icon {
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  place-items: center;
  color: #409eff;
  font-size: 20px;
  border-radius: 10px;
  background: #e8f3ff;
}
.form-designer-entry__content { display: flex; flex: 1; min-width: 0; flex-direction: column; gap: 4px; }
.form-designer-entry__content strong { overflow: hidden; color: #303133; text-overflow: ellipsis; white-space: nowrap; }
.form-designer-entry__content span { color: #909399; font-size: 13px; }
:deep(.fullscreen-dialog) { display: flex; flex-direction: column; max-height: 90vh; margin-bottom: 0; }
:deep(.fullscreen-dialog .el-dialog__body) { flex: 1; overflow-y: auto; padding: 20px; }
:deep(.fullscreen-dialog .el-dialog__header) { padding-bottom: 12px; margin-right: 0; flex-shrink: 0; }
:deep(.fullscreen-dialog .el-dialog__footer) { flex-shrink: 0; }
:deep(.form-designer-dialog) { display: flex; flex-direction: column; margin: 0; }
:deep(.form-designer-dialog .el-dialog__header) { padding: 16px 24px; margin-right: 0; border-bottom: 1px solid #ebeef5; }
:deep(.form-designer-dialog .el-dialog__body) { display: flex; flex: 1; min-height: 0; padding: 0; overflow: hidden; }
:deep(.form-designer-dialog .el-dialog__footer) { padding: 12px 24px; border-top: 1px solid #ebeef5; }
.form-designer-dialog__body { width: 100%; height: 100%; padding: 20px 24px; box-sizing: border-box; background: #f5f7fa; }
:deep(.form-designer-dialog .form-designer) { height: 100%; min-height: 620px; }
</style>
