<template>
  <div class="system-config" v-loading="loading">
    <el-alert
      title="系统配置仅对超级管理员开放"
      type="warning"
      :closable="false"
      show-icon
      class="page-alert"
    />

    <el-form label-position="top" class="config-form">
      <el-card shadow="never" class="config-card">
        <template #header><div class="card-title">移动端 H5 域名</div></template>
        <el-form-item label="H5 对外访问域名">
          <el-input v-model="form.h5_domain" placeholder="例如：https://m.example.com" />
          <div class="form-hint">用于生成后台“预览”链接及微信分享链接，请填写协议和域名，不要填写末尾斜杠。</div>
        </el-form-item>
      </el-card>

      <el-card shadow="never" class="config-card">
        <template #header><div class="card-title">微信分享</div></template>
        <el-form-item label="启用微信分享">
          <el-switch v-model="form.wechat_share_enabled" active-text="已启用" inactive-text="未启用" />
        </el-form-item>
        <div v-if="form.wechat_share_enabled" class="config-grid">
          <el-form-item label="微信 AppID">
            <el-input v-model="form.wechat_app_id" placeholder="请输入公众号 AppID" />
          </el-form-item>
          <el-form-item :label="`微信 AppSecret${form.wechat_app_secret_configured ? '（已配置，留空不修改）' : ''}`">
            <el-input v-model="form.wechat_app_secret" type="password" show-password placeholder="请输入或更新 AppSecret" />
          </el-form-item>
        </div>
        <div class="form-hint">单个微站的分享图标、标题和副标题请在“微站编辑”中配置；此处仅配置全局微信接入参数。</div>
      </el-card>

      <el-card shadow="never" class="config-card">
        <template #header><div class="card-title">阿里云 OSS</div></template>
        <div class="config-grid">
          <el-form-item label="AccessKey ID">
            <el-input v-model="form.oss_access_key_id" placeholder="请输入 AccessKey ID" />
          </el-form-item>
          <el-form-item :label="`AccessKey Secret${form.oss_access_key_secret_configured ? '（已配置，留空不修改）' : ''}`">
            <el-input v-model="form.oss_access_key_secret" type="password" show-password placeholder="请输入或更新 AccessKey Secret" />
          </el-form-item>
          <el-form-item label="Bucket 名称">
            <el-input v-model="form.oss_bucket_name" placeholder="例如：weizhan-assets" />
          </el-form-item>
          <el-form-item label="Endpoint">
            <el-input v-model="form.oss_endpoint" placeholder="例如：oss-cn-shanghai.aliyuncs.com" />
          </el-form-item>
          <el-form-item label="自定义访问域名">
            <el-input v-model="form.oss_custom_domain" placeholder="可选，例如：https://cdn.example.com" />
          </el-form-item>
        </div>
        <div class="form-hint">完整配置后，新上传的图片将优先存入 OSS；未完整配置时自动使用本地存储。密钥不会回显。</div>
      </el-card>

      <el-card shadow="never" class="config-card">
        <template #header>
          <div class="card-header"><span class="card-title">本地图标库</span><el-button type="primary" size="small" @click="addIcon">添加图标</el-button></div>
        </template>
        <div v-if="form.local_icon_library.length" class="icon-list">
          <div v-for="(icon, index) in form.local_icon_library" :key="index" class="icon-row">
            <el-image :src="icon.url" fit="cover" class="icon-preview"><template #error><span>图标</span></template></el-image>
            <el-input v-model="icon.name" placeholder="图标名称" />
            <el-input v-model="icon.url" placeholder="图标 URL" />
            <el-button link type="danger" @click="removeIcon(index)">删除</el-button>
          </div>
        </div>
        <el-empty v-else description="暂无本地图标，可添加图标名称和图片地址" :image-size="72" />
        <div class="form-hint">图标库用于集中维护可复用图标资源；保存后后续可在按钮图标选择器中扩展调用。</div>
      </el-card>

      <el-card shadow="never" class="config-card">
        <template #header><div class="card-title">AI 生图</div></template>
        <div class="config-grid">
          <el-form-item label="服务商">
            <el-select v-model="form.ai_provider" style="width: 100%">
              <el-option label="通义万相（阿里云百炼 DashScope）" value="dashscope" />
            </el-select>
          </el-form-item>
          <el-form-item label="生图模型">
            <el-select v-model="form.ai_image_model" style="width: 100%" allow-create filterable>
              <el-option label="wan2.2-t2i-flash（文生图·极速，推荐）" value="wan2.2-t2i-flash" />
              <el-option label="wan2.2-t2i-plus（文生图·专业）" value="wan2.2-t2i-plus" />
              <el-option label="wan2.6-t2i（文生图·最新，尺寸有限制）" value="wan2.6-t2i" />
              <el-option label="wanx2.1-t2i-turbo（文生图·快速）" value="wanx2.1-t2i-turbo" />
              <el-option label="wanx2.1-t2i-plus（文生图·增强）" value="wanx2.1-t2i-plus" />
            </el-select>
          </el-form-item>
          <el-form-item :label="`DashScope API Key${form.ai_api_key_configured ? '（已配置，留空不修改）' : ''}`" class="span-2">
            <el-input v-model="form.ai_api_key" type="password" show-password placeholder="请输入或更新 API Key（sk- 开头）" />
          </el-form-item>
        </div>
        <div class="form-hint">
          在阿里云百炼控制台（bailian.console.aliyun.com）创建 API Key。配置后「AI 生图」模块即可输入提示词生成微站图片与图标。密钥不会回显。若生成报「Model not exist」，请在控制台开通所选模型，并确认 API Key 地域与模型地域一致。
        </div>
      </el-card>

      <div class="actions"><el-button type="primary" :loading="saving" @click="save">保存配置</el-button></div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

interface LocalIcon { name: string; url: string }

const loading = ref(false)
const saving = ref(false)
const form = reactive({
  h5_domain: '',
  wechat_share_enabled: false,
  wechat_app_id: '',
  wechat_app_secret: '',
  wechat_app_secret_configured: false,
  oss_access_key_id: '',
  oss_access_key_secret: '',
  oss_access_key_secret_configured: false,
  oss_bucket_name: '',
  oss_endpoint: '',
  oss_custom_domain: '',
  local_icon_library: [] as LocalIcon[],
  ai_provider: 'dashscope',
  ai_api_key: '',
  ai_api_key_configured: false,
  ai_image_model: 'wan2.2-t2i-flash',
})

async function load() {
  loading.value = true
  try {
    const data: any = await api.get('/system-config')
    Object.assign(form, data, {
      wechat_app_secret: '',
      oss_access_key_secret: '',
      ai_api_key: '',
      local_icon_library: Array.isArray(data.local_icon_library) ? data.local_icon_library : [],
    })
  } finally {
    loading.value = false
  }
}

function addIcon() { form.local_icon_library.push({ name: '', url: '' }) }
function removeIcon(index: number) { form.local_icon_library.splice(index, 1) }

async function save() {
  saving.value = true
  try {
    await api.put('/system-config', {
      h5_domain: form.h5_domain,
      wechat_share_enabled: form.wechat_share_enabled,
      wechat_app_id: form.wechat_app_id,
      wechat_app_secret: form.wechat_app_secret || undefined,
      oss_access_key_id: form.oss_access_key_id,
      oss_access_key_secret: form.oss_access_key_secret || undefined,
      oss_bucket_name: form.oss_bucket_name,
      oss_endpoint: form.oss_endpoint,
      oss_custom_domain: form.oss_custom_domain,
      local_icon_library: form.local_icon_library.filter((icon) => icon.name || icon.url),
      ai_provider: form.ai_provider,
      ai_api_key: form.ai_api_key || undefined,
      ai_image_model: form.ai_image_model,
    })
    ElMessage.success('管理员配置已保存')
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.system-config { max-width: 960px; margin: 0 auto; }
.page-alert { margin-bottom: 16px; }
.config-form { display: flex; flex-direction: column; gap: 16px; }
.config-card { border-radius: 4px; }
.card-title { font-size: 15px; font-weight: 600; color: #303133; display: flex; align-items: center; gap: 6px; }
.card-header { display: flex; align-items: center; justify-content: space-between; }
.config-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 16px; }
.config-grid .span-2 { grid-column: 1 / -1; }
.form-hint { margin-top: -6px; color: #909399; font-size: 12px; line-height: 1.6; }
.icon-list { display: flex; flex-direction: column; gap: 10px; }
.icon-row { display: grid; grid-template-columns: 44px minmax(120px, 0.6fr) minmax(180px, 1.4fr) auto; align-items: center; gap: 10px; }
.icon-preview { width: 40px; height: 40px; border: 1px solid #ebeef5; border-radius: 6px; color: #909399; font-size: 11px; }
.actions { display: flex; justify-content: flex-end; padding: 4px 0 20px; }
@media (max-width: 760px) { .config-grid { grid-template-columns: 1fr; } .icon-row { grid-template-columns: 40px 1fr auto; } .icon-row .el-input:nth-of-type(2) { grid-column: 2 / 4; } }
</style>
