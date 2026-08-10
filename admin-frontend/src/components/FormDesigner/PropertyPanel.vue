<template>
  <div class="property-panel">
    <div class="panel-header">
      <el-icon :size="16" color="#409eff"><Setting /></el-icon>
      <span>属性设置</span>
    </div>

    <div class="panel-body">
      <!-- 选中字段时的属性编辑 -->
      <div v-if="field" class="property-content">
        <!-- 基础属性 -->
        <div class="property-section">
          <div class="section-title">基础属性</div>
          <el-form label-position="top" size="small">
            <el-form-item label="字段标题">
              <el-input v-model="field.title" placeholder="字段标题" />
            </el-form-item>
            <el-form-item label="是否必填">
              <el-switch v-model="field.required" active-text="必填" inactive-text="选填" />
            </el-form-item>
            <el-form-item v-if="supportsPlaceholder" label="占位提示">
              <el-input v-model="field.placeholder" type="textarea" :rows="2" placeholder="占位提示文字" />
            </el-form-item>
          </el-form>
        </div>

        <!-- 类型特定属性 -->
        <div v-if="field.type === 'textarea'" class="property-section">
          <div class="section-title">文本配置</div>
          <el-form label-position="top" size="small">
            <el-form-item label="行数">
              <el-input-number v-model="field.props.rows" :min="2" :max="10" style="width: 100%" />
            </el-form-item>
          </el-form>
        </div>

        <div v-if="field.type === 'text'" class="property-section">
          <div class="section-title">文本配置</div>
          <el-form label-position="top" size="small">
            <el-form-item label="最大输入长度">
              <el-input-number v-model="field.props.maxLength" :min="1" :max="1000" style="width: 100%" />
            </el-form-item>
          </el-form>
        </div>

        <!-- 选项编辑 -->
        <div v-if="supportsOptions" class="property-section">
          <div class="section-title">选项配置</div>
          <div class="options-editor">
            <div v-for="(opt, idx) in field.options" :key="idx" class="option-row">
              <el-input v-model="field.options[idx]" size="small" placeholder="选项内容" />
              <el-button link type="danger" size="small" @click="removeOption(idx)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <el-button type="primary" link size="small" @click="addOption">
              <el-icon><Plus /></el-icon> 添加选项
            </el-button>
          </div>
        </div>

        <!-- 默认值 -->
        <div v-if="supportsDefaultValue" class="property-section">
          <div class="section-title">默认值</div>
          <el-form label-position="top" size="small">
            <el-form-item>
              <el-input v-if="['text', 'textarea', 'phone', 'idcard', 'email'].includes(field.type)" v-model="field.defaultValue" placeholder="默认值" />
              <el-input-number v-else-if="field.type === 'number'" v-model="field.defaultValue" style="width: 100%" />
              <el-switch v-else-if="field.type === 'agreement'" v-model="field.defaultValue" />
              <el-select v-else-if="field.type === 'select'" v-model="field.defaultValue" style="width: 100%" placeholder="选择默认值" clearable>
                <el-option v-for="opt in (field.options || [])" :key="opt" :label="opt" :value="opt" />
              </el-select>
              <el-radio-group v-else-if="field.type === 'radio'" v-model="field.defaultValue">
                <el-radio v-for="opt in (field.options || [])" :key="opt" :value="opt" size="small">{{ opt }}</el-radio>
              </el-radio-group>
              <el-checkbox-group v-else-if="field.type === 'checkbox'" v-model="field.defaultValue">
                <el-checkbox v-for="opt in (field.options || [])" :key="opt" :value="opt" size="small">{{ opt }}</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </div>

        <!-- 中划线配置 -->
        <div v-if="field.type === 'divider'" class="property-section">
          <div class="section-title">分割线配置</div>
          <el-form label-position="top" size="small">
            <el-form-item label="分割线文字（选填）">
              <el-input v-model="field.props.text" placeholder="例如：以下为出行信息" />
            </el-form-item>
          </el-form>
        </div>

        <!-- 提示文字配置 -->
        <div v-if="field.type === 'tip_text'" class="property-section">
          <div class="section-title">提示文字配置</div>
          <el-form label-position="top" size="small">
            <el-form-item label="提示内容">
              <el-input v-model="field.props.content" type="textarea" :rows="4" placeholder="请输入提示内容" />
            </el-form-item>
            <el-form-item label="提示样式">
              <el-select v-model="field.props.tone" style="width: 100%">
                <el-option label="信息提示（蓝色）" value="info" />
                <el-option label="成功提示（绿色）" value="success" />
                <el-option label="注意提示（橙色）" value="warning" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 同意协议配置 -->
        <div v-if="field.type === 'agreement'" class="property-section">
          <div class="section-title">协议内容</div>
          <el-form label-position="top" size="small">
            <el-form-item label="协议正文（选填）">
              <el-input
                v-model="field.props.agreementContent"
                type="textarea"
                :rows="6"
                placeholder="请输入需要展示给填写者阅读的协议内容"
              />
            </el-form-item>
            <p class="property-hint">协议正文将在 H5 表单内展示，填写者可勾选确认同意。</p>
          </el-form>
        </div>

        <!-- 交通信息自定义属性 -->
        <div v-if="field.type === 'transport_info'" class="property-section">
          <div class="section-title">交通信息配置</div>
          <el-form label-position="top" size="small">
            <el-form-item label="显示模块">
              <div class="checkbox-group-vertical">
                <el-checkbox v-model="field.props.showDeparture">去程信息</el-checkbox>
                <el-checkbox v-model="field.props.showReturn">回程信息</el-checkbox>
                <el-checkbox v-model="field.props.showRemark">备注</el-checkbox>
              </div>
            </el-form-item>
            <el-form-item v-if="field.props.showDeparture" label="去程方式选项">
              <div class="options-editor">
                <div v-for="(opt, idx) in field.props.departureOptions" :key="'dep-' + idx" class="option-row">
                  <el-input v-model="field.props.departureOptions[idx]" size="small" placeholder="去程方式" />
                  <el-button link type="danger" size="small" @click="removeTransportOption('departure', idx)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
                <el-button type="primary" link size="small" @click="addTransportOption('departure')">
                  <el-icon><Plus /></el-icon> 添加选项
                </el-button>
              </div>
            </el-form-item>
            <el-form-item v-if="field.props.showReturn" label="回程方式选项">
              <div class="options-editor">
                <div v-for="(opt, idx) in field.props.returnOptions" :key="'ret-' + idx" class="option-row">
                  <el-input v-model="field.props.returnOptions[idx]" size="small" placeholder="回程方式" />
                  <el-button link type="danger" size="small" @click="removeTransportOption('return', idx)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
                <el-button type="primary" link size="small" @click="addTransportOption('return')">
                  <el-icon><Plus /></el-icon> 添加选项
                </el-button>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </div>

      <!-- 未选中字段时的空状态 -->
      <div v-else class="empty-state">
        <el-icon :size="40" color="#dcdfe6"><Setting /></el-icon>
        <p class="empty-title">属性设置</p>
        <p class="empty-desc">点击画布中的字段进行编辑</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Setting, Plus, Delete } from '@element-plus/icons-vue'
import type { FormField } from './types'
import {
  fieldSupportsPlaceholder,
  fieldSupportsOptions,
  fieldSupportsDefaultValue,
} from './fieldRegistry'

const props = defineProps<{
  field: FormField | null
}>()

const supportsPlaceholder = computed(() => {
  if (!props.field) return false
  return fieldSupportsPlaceholder(props.field.type)
})

const supportsOptions = computed(() => {
  if (!props.field) return false
  return fieldSupportsOptions(props.field.type)
})

const supportsDefaultValue = computed(() => {
  if (!props.field) return false
  return fieldSupportsDefaultValue(props.field.type)
})

function addOption() {
  if (props.field) {
    if (!props.field.options) props.field.options = []
    props.field.options.push(`选项${props.field.options.length + 1}`)
  }
}

function removeOption(index: number) {
  if (props.field && props.field.options) {
    props.field.options.splice(index, 1)
  }
}

function addTransportOption(direction: 'departure' | 'return') {
  if (!props.field || !props.field.props) return
  const key = direction === 'departure' ? 'departureOptions' : 'returnOptions'
  if (!Array.isArray(props.field.props[key])) {
    props.field.props[key] = ['飞机', '火车', '其他']
  }
  props.field.props[key].push('新选项')
}

function removeTransportOption(direction: 'departure' | 'return', index: number) {
  if (!props.field || !props.field.props) return
  const key = direction === 'departure' ? 'departureOptions' : 'returnOptions'
  if (Array.isArray(props.field.props[key])) {
    props.field.props[key].splice(index, 1)
  }
}
</script>

<style scoped>
.property-panel {
  width: 280px;
  background: #fff;
  border-left: 1px solid #e8eaed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 14px 16px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  flex-shrink: 0;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.property-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f5f5f5;
}

.property-section:last-child {
  border-bottom: none;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: #909399;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.options-editor {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.checkbox-group-vertical {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 0;
}

.property-hint {
  margin: -4px 0 0;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-title {
  font-size: 14px;
  color: #606266;
  font-weight: 600;
  margin: 12px 0 4px;
}

.empty-desc {
  font-size: 12px;
  color: #c0c4cc;
  margin: 0;
}
</style>
