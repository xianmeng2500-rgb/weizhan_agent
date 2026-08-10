<template>
  <div class="qrcode-editor">
    <el-form label-width="100px" size="default" class="qrcode-form">
      <el-form-item label="提示信息">
        <el-input
          v-model="config.hint"
          placeholder="如：请向工作人员出示此二维码签到"
          maxlength="50"
          show-word-limit
          @input="syncToParent"
        />
        <div class="form-hint">二维码上方的提示文案，最多50字</div>
      </el-form-item>

      <el-form-item label="显示字段">
        <el-checkbox-group v-model="config.display_fields" @change="syncToParent">
          <el-checkbox label="username">姓名/账号</el-checkbox>
          <el-checkbox label="phone">手机号</el-checkbox>
          <el-checkbox label="nickname">昵称</el-checkbox>
        </el-checkbox-group>
        <div class="form-hint">勾选后将在二维码下方显示对应的报名信息</div>
      </el-form-item>
    </el-form>

    <!-- 预览区 -->
    <div class="qrcode-preview">
      <div class="preview-title">移动端预览效果</div>
      <div class="preview-phone">
        <div class="preview-qr-area">
          <div class="preview-qrcode">
            <svg viewBox="0 0 100 100" class="qr-placeholder">
              <rect width="100" height="100" fill="#fff" rx="8"/>
              <rect x="10" y="10" width="80" height="80" fill="none" stroke="#667eea" stroke-width="2" rx="4" stroke-dasharray="4,3"/>
              <text x="50" y="48" text-anchor="middle" fill="#667eea" font-size="10" font-weight="600">QR</text>
              <text x="50" y="62" text-anchor="middle" fill="#999" font-size="7">签到二维码</text>
            </svg>
          </div>
          <div v-if="config.hint" class="preview-hint">{{ config.hint }}</div>
          <div class="preview-fields">
            <div v-if="config.display_fields.includes('username')" class="preview-field">
              <span class="field-label">姓名/账号</span>
              <span class="field-value">张三</span>
            </div>
            <div v-if="config.display_fields.includes('phone')" class="preview-field">
              <span class="field-label">手机号</span>
              <span class="field-value">138****1234</span>
            </div>
            <div v-if="config.display_fields.includes('nickname')" class="preview-field">
              <span class="field-label">昵称</span>
              <span class="field-value">小明</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

interface QRCodeConfig {
  hint: string
  display_fields: string[]
}

const props = defineProps<{
  modelValue: QRCodeConfig | null
  siteId: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: QRCodeConfig): void
}>()

const config = reactive<QRCodeConfig>({
  hint: '',
  display_fields: [],
})

// 单向：仅首次从 props 初始化
watch(() => props.modelValue, (val) => {
  if (val) {
    config.hint = val.hint || ''
    config.display_fields = val.display_fields || []
  }
}, { immediate: true })

function syncToParent() {
  emit('update:modelValue', {
    hint: config.hint,
    display_fields: [...config.display_fields],
  })
}

function getConfig(): QRCodeConfig {
  return {
    hint: config.hint,
    display_fields: [...config.display_fields],
  }
}

defineExpose({ getConfig })
</script>

<style scoped>
.qrcode-editor {
  display: flex;
  gap: 40px;
  height: 100%;
  min-height: 400px;
}

.qrcode-form {
  flex: 1;
  max-width: 500px;
}

.form-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.qrcode-preview {
  flex: 0 0 340px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.preview-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 16px;
  font-weight: 500;
}

.preview-phone {
  width: 280px;
  background: #f5f5f5;
  border-radius: 24px;
  padding: 30px 20px;
  border: 8px solid #1a1a1a;
  border-top-width: 32px;
  border-bottom-width: 32px;
  position: relative;
}

.preview-qr-area {
  background: #fff;
  border-radius: 16px;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.preview-qrcode {
  width: 160px;
  height: 160px;
}

.qr-placeholder {
  width: 100%;
  height: 100%;
}

.preview-hint {
  font-size: 13px;
  color: #666;
  text-align: center;
  line-height: 1.4;
}

.preview-fields {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #eee;
}

.preview-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.field-label {
  font-size: 13px;
  color: #999;
}

.field-value {
  font-size: 13px;
  color: #333;
  font-weight: 500;
}
</style>
