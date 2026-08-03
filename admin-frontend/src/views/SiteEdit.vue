<template>
  <div class="site-edit">
    <el-card>
      <template #header>{{ isEdit ? '编辑微站' : '创建微站' }}</template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" style="max-width: 700px">
        <el-form-item label="微站名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入微站名称" />
        </el-form-item>
        <el-form-item label="访问码" prop="code">
          <el-input v-model="form.code" placeholder="英文+数字, 用于生成访问链接" :disabled="isEdit">
            <template #append>
              <el-button @click="generateCode">随机生成</el-button>
            </template>
          </el-input>
          <div class="hint">访问链接: /s/{{ form.code || 'xxx' }}</div>
        </el-form-item>
        <el-form-item label="模板" prop="template">
          <el-radio-group v-model="form.template">
            <el-radio value="classic">经典(蓝紫渐变)</el-radio>
            <el-radio value="dark">暗黑(深色系)</el-radio>
            <el-radio value="festive">节日(红色系)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="布局" prop="layout">
          <el-radio-group v-model="form.layout">
            <el-radio value="grid">九宫格</el-radio>
            <el-radio value="button">按钮</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="KV图">
          <el-upload
            action="/api/v1/upload/image"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="onKvSuccess"
            accept="image/*"
          >
            <img v-if="form.kv_image" :src="form.kv_image" class="kv-preview" />
            <el-button v-else>上传KV图</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="背景色">
          <el-color-picker v-model="form.background_color" />
          <span class="hint" style="margin-left:10px">留空则使用模板默认背景</span>
        </el-form-item>
        <el-form-item label="是否需要登录">
          <el-switch v-model="form.need_login" />
          <span class="hint" style="margin-left:10px">开启后用户需要输入账号密码才能访问</span>
        </el-form-item>
        <el-form-item label="开启时间">
          <el-date-picker v-model="form.start_time" type="datetime" placeholder="选择开启时间" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item label="关闭时间">
          <el-date-picker v-model="form.end_time" type="datetime" placeholder="选择关闭时间" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item label="关闭提示文案">
          <el-input v-model="form.close_message" type="textarea" :rows="2" placeholder="微站关闭后展示的提示文案" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
          <el-button @click="$router.back()">返回</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const formRef = ref<FormInstance>()
const saving = ref(false)

const isEdit = computed(() => !!route.params.id)

const uploadHeaders = computed(() => ({ Authorization: `Bearer ${auth.token}` }))

const form = reactive({
  name: '',
  code: '',
  template: 'classic',
  layout: 'grid',
  kv_image: '',
  background_color: '',
  need_login: false,
  start_time: '',
  end_time: '',
  close_message: '',
})

const rules = {
  name: [{ required: true, message: '请输入微站名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入访问码', trigger: 'blur' }],
}

function generateCode() {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
  let code = ''
  for (let i = 0; i < 8; i++) code += chars[Math.floor(Math.random() * chars.length)]
  form.code = code
}

function onKvSuccess(res: any) {
  if (res.url) form.kv_image = res.url
  else ElMessage.error('上传失败')
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const data = { ...form }
    if (isEdit.value) {
      await api.put(`/sites/${route.params.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/sites', data)
      ElMessage.success('创建成功')
    }
    router.push('/sites')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  if (isEdit.value) {
    const res: any = await api.get(`/sites/${route.params.id}`)
    Object.assign(form, res)
  }
})
</script>

<style scoped>
.kv-preview { max-width: 300px; max-height: 150px; border-radius: 4px; }
.hint { color: #999; font-size: 12px; }
</style>
