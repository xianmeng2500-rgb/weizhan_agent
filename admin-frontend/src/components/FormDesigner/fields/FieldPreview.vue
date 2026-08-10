<template>
  <div class="field-preview">
    <!-- 交通信息复合组件 -->
    <TransportInfoPreview
      v-if="field.type === 'transport_info'"
      :field="field"
    />

    <!-- 中划线 -->
    <template v-else-if="field.type === 'divider'">
      <div class="divider-preview">
        <span v-if="field.props?.text" class="divider-preview__text">{{ field.props.text }}</span>
      </div>
    </template>

    <!-- 提示文字 -->
    <template v-else-if="field.type === 'tip_text'">
      <div class="tip-preview" :class="`tip-preview--${field.props?.tone || 'info'}`">
        {{ field.props?.content || field.title }}
      </div>
    </template>

    <!-- 文本类 -->
    <template v-else-if="['text', 'phone', 'idcard', 'email'].includes(field.type)">
      <el-input :placeholder="field.placeholder || '请输入'" disabled />
    </template>

    <!-- 多行文本 -->
    <template v-else-if="field.type === 'textarea'">
      <el-input type="textarea" :rows="field.props?.rows || 3" :placeholder="field.placeholder || '请输入'" disabled />
    </template>

    <!-- 数字 -->
    <template v-else-if="field.type === 'number'">
      <el-input-number disabled style="width: 100%" />
    </template>

    <!-- 单选 -->
    <template v-else-if="field.type === 'radio'">
      <el-radio-group disabled>
        <el-radio v-for="opt in (field.options || [])" :key="opt" :value="opt">{{ opt }}</el-radio>
      </el-radio-group>
    </template>

    <!-- 多选 -->
    <template v-else-if="field.type === 'checkbox'">
      <el-checkbox-group disabled>
        <el-checkbox v-for="opt in (field.options || [])" :key="opt" :value="opt">{{ opt }}</el-checkbox>
      </el-checkbox-group>
    </template>

    <!-- 下拉选择 -->
    <template v-else-if="field.type === 'select'">
      <el-select disabled :placeholder="field.placeholder || '请选择'" style="width: 100%">
        <el-option v-for="opt in (field.options || [])" :key="opt" :label="opt" :value="opt" />
      </el-select>
    </template>

    <!-- 日期 -->
    <template v-else-if="field.type === 'date'">
      <el-date-picker disabled type="date" :placeholder="field.placeholder || '选择日期'" style="width: 100%" />
    </template>

    <!-- 时间 -->
    <template v-else-if="field.type === 'time'">
      <el-time-picker disabled :placeholder="field.placeholder || '选择时间'" style="width: 100%" />
    </template>

    <!-- 地区 -->
    <template v-else-if="field.type === 'region'">
      <el-cascader disabled :placeholder="field.placeholder || '请选择地区'" style="width: 100%" />
    </template>

    <!-- 同意协议 -->
    <template v-else-if="field.type === 'agreement'">
      <div class="agreement-preview">
        <el-checkbox disabled>{{ field.placeholder || '我已阅读并同意' }}</el-checkbox>
        <p v-if="field.props?.agreementContent" class="agreement-preview__content">
          {{ field.props.agreementContent }}
        </p>
      </div>
    </template>

    <!-- 图片上传 -->
    <template v-else-if="field.type === 'image'">
      <el-upload disabled :show-file-list="false">
        <el-button disabled>点击上传图片</el-button>
      </el-upload>
    </template>

    <!-- 未知类型兜底 -->
    <template v-else>
      <div class="unknown-type">未知字段类型: {{ field.type }}</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { FormField } from '../types'
import TransportInfoPreview from './TransportInfoPreview.vue'

defineProps<{
  field: FormField
}>()
</script>

<style scoped>
.field-preview {
  width: 100%;
}

.divider-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #909399;
  font-size: 12px;
}
.divider-preview::before,
.divider-preview::after {
  height: 1px;
  flex: 1;
  content: '';
  background: #dcdfe6;
}
.divider-preview__text { white-space: nowrap; }

.tip-preview {
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
}
.tip-preview--info { color: #337ecc; background: #ecf5ff; }
.tip-preview--success { color: #529b2e; background: #f0f9eb; }
.tip-preview--warning { color: #b88230; background: #fdf6ec; }

.agreement-preview { display: flex; flex-direction: column; gap: 6px; }
.agreement-preview__content { margin: 0; color: #909399; font-size: 12px; line-height: 1.6; white-space: pre-wrap; }

.unknown-type {
  color: #f56c6c;
  font-size: 12px;
  padding: 8px;
  background: #fef0f0;
  border-radius: 4px;
}
</style>
