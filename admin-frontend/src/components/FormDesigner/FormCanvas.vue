<template>
  <div class="form-canvas-wrapper">
    <!-- 顶部工具栏 -->
    <div class="canvas-toolbar">
      <el-radio-group v-model="modeValue" size="small">
        <el-radio-button value="design">
          <el-icon style="margin-right: 4px"><EditPen /></el-icon>设计
        </el-radio-button>
        <el-radio-button value="preview">
          <el-icon style="margin-right: 4px"><View /></el-icon>预览
        </el-radio-button>
      </el-radio-group>
      <div v-if="mode === 'design' && config.fields.length > 0" class="canvas-info">
        <el-icon color="#909399" :size="12"><InfoFilled /></el-icon>
        <span>{{ config.fields.length }} 个字段</span>
      </div>
    </div>

    <!-- 画布区域 -->
    <div class="canvas-scroll" @dragover.prevent @drop="handleDrop">
      <div class="form-canvas">
        <!-- 表单标题区 -->
        <div class="form-header">
          <el-input
            v-if="mode === 'design'"
            v-model="config.title"
            placeholder="请输入表单标题"
            class="form-title-input"
          >
            <template #prefix><el-icon color="#c0c4cc"><EditPen /></el-icon></template>
          </el-input>
          <h3 v-else class="form-title">{{ config.title || '未命名表单' }}</h3>

          <el-input
            v-if="mode === 'design'"
            v-model="config.description"
            type="textarea"
            :rows="2"
            placeholder="表单描述/说明（选填）"
            class="form-desc-input"
            resize="none"
          />
          <p v-else-if="config.description" class="form-desc">{{ config.description }}</p>
        </div>

        <!-- 空状态 -->
        <div v-if="config.fields.length === 0" class="empty-state" @dragover.prevent @drop="handleDrop">
          <div class="empty-icon">
            <el-icon :size="48" color="#c0c4cc"><Plus /></el-icon>
          </div>
          <p class="empty-title">开始设计你的表单</p>
          <p class="empty-desc">从左侧组件库拖拽或点击组件添加到此处</p>
        </div>

        <!-- 字段列表 -->
        <div v-else class="field-list" @dragover.prevent @drop="handleListDrop">
          <div
            v-for="(field, index) in config.fields"
            :key="field.id"
            class="field-card"
            :class="{
              active: selectedId === field.id,
              preview: mode === 'preview',
              'drag-over': dragOverIndex === index,
            }"
            draggable="true"
            @click="$emit('select-field', field)"
            @dragstart="$emit('field-drag-start', $event, index)"
            @dragover.prevent="dragOverIndex = index"
            @dragleave="dragOverIndex = null"
            @drop.stop="$emit('field-drop', $event, index); dragOverIndex = null"
            @dragend="dragOverIndex = null"
          >
            <!-- 拖拽手柄 -->
            <div v-if="mode === 'design'" class="drag-handle">
              <el-icon color="#c0c4cc" :size="14"><Rank /></el-icon>
            </div>

            <!-- 字段内容 -->
            <div class="field-body">
              <div v-if="!['divider', 'tip_text'].includes(field.type)" class="field-label-row">
                <span class="field-label-text">{{ field.title }}</span>
                <span v-if="field.required" class="required-mark">*</span>
                <el-tag v-if="mode === 'design'" size="small" type="info" effect="plain" class="field-type-tag">
                  {{ getTypeLabel(field.type) }}
                </el-tag>
              </div>
              <el-tag v-else-if="mode === 'design'" size="small" type="info" effect="plain" class="display-field-tag">
                {{ getTypeLabel(field.type) }}
              </el-tag>
              <div class="field-preview-area">
                <FieldPreview :field="field" />
              </div>
            </div>

            <!-- 操作按钮 -->
            <div v-if="mode === 'design'" class="field-toolbar">
              <el-tooltip content="复制" placement="top">
                <el-button link size="small" @click.stop="$emit('copy-field', index)">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="上移" placement="top">
                <el-button link size="small" :disabled="index === 0" @click.stop="$emit('move-up', index)">
                  <el-icon><Top /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="下移" placement="top">
                <el-button link size="small" :disabled="index === config.fields.length - 1" @click.stop="$emit('move-down', index)">
                  <el-icon><Bottom /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button link type="danger" size="small" @click.stop="$emit('remove-field', index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </div>
        </div>

        <!-- 底部按钮区 -->
        <div v-if="mode === 'design'" class="form-footer-design">
          <el-input v-model="config.buttonText" placeholder="提交按钮文字" style="width: 200px">
            <template #prefix><el-icon color="#c0c4cc"><Pointer /></el-icon></template>
          </el-input>
        </div>
        <div v-else class="form-footer-preview">
          <el-button type="primary" size="large" style="width: 100%">{{ config.buttonText || '提交' }}</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Plus, Delete, Rank, EditPen, View, InfoFilled,
  CopyDocument, Top, Bottom, Pointer,
} from '@element-plus/icons-vue'
import type { FormConfig, FormField } from './types'
import { getFieldDefinition } from './fieldRegistry'
import FieldPreview from './fields/FieldPreview.vue'

const props = defineProps<{
  config: FormConfig
  mode: 'design' | 'preview'
  selectedId: string | null
}>()

const emit = defineEmits<{
  (e: 'update:mode', value: 'design' | 'preview'): void
  (e: 'drag-start', event: DragEvent, type: string): void
  (e: 'add-field', type: string): void
  (e: 'select-field', field: FormField): void
  (e: 'field-drag-start', event: DragEvent, index: number): void
  (e: 'field-drop', event: DragEvent, index: number): void
  (e: 'remove-field', index: number): void
  (e: 'copy-field', index: number): void
  (e: 'move-up', index: number): void
  (e: 'move-down', index: number): void
}>()

const modeValue = computed({
  get: () => props.mode,
  set: (val) => emit('update:mode', val),
})

const dragOverIndex = ref<number | null>(null)

function getTypeLabel(type: string): string {
  return getFieldDefinition(type)?.label || type
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  const type = e.dataTransfer?.getData('component-type')
  if (type) {
    emit('add-field', type)
  }
}

function handleListDrop(e: DragEvent) {
  e.preventDefault()
  const type = e.dataTransfer?.getData('component-type')
  if (type) {
    emit('add-field', type)
  }
}
</script>

<style scoped>
.form-canvas-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f0f2f5;
}

.canvas-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid #e8eaed;
  flex-shrink: 0;
}

.canvas-info {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.canvas-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.form-canvas {
  max-width: 520px;
  margin: 0 auto;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 24px 20px;
  min-height: calc(100% - 0px);
}

.form-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #ebeef5;
}

.form-title-input :deep(.el-input__wrapper) {
  border: none;
  box-shadow: none;
  background: transparent;
}

.form-title-input :deep(.el-input__inner) {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
}

.form-desc-input :deep(.el-textarea__inner) {
  border: none;
  padding: 4px 0 0 24px;
  background: transparent;
  font-size: 13px;
  color: #909399;
  resize: none;
  box-shadow: none;
}

.form-title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
  color: #303133;
}

.form-desc {
  margin: 0;
  color: #909399;
  font-size: 13px;
  line-height: 1.5;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  border: 2px dashed #d9d9d9;
  border-radius: 10px;
  background: #fafbfc;
  transition: all 0.2s;
}

.empty-state:hover {
  border-color: #409eff;
  background: #f0f7ff;
}

.empty-icon {
  margin-bottom: 12px;
}

.empty-title {
  font-size: 15px;
  color: #606266;
  font-weight: 600;
  margin: 0 0 4px;
}

.empty-desc {
  font-size: 12px;
  color: #c0c4cc;
  margin: 0;
}

/* 字段列表 */
.field-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.field-card {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 14px 12px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.field-card:hover {
  border-color: #c6e2ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.field-card.active {
  border-color: #409eff;
  background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%);
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.12);
}

.field-card.drag-over {
  border-color: #67c23a;
  border-style: dashed;
}

.field-card.preview {
  cursor: default;
  background: #fff;
}

.drag-handle {
  padding-top: 2px;
  cursor: move;
  opacity: 0.4;
  transition: opacity 0.2s;
}

.field-card:hover .drag-handle {
  opacity: 1;
}

.field-body {
  flex: 1;
  min-width: 0;
}

.field-label-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
}

.field-label-text {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.required-mark {
  color: #f56c6c;
  font-size: 14px;
}

.field-type-tag {
  margin-left: auto;
  font-size: 10px;
}

.field-preview-area {
  width: 100%;
}

.display-field-tag {
  margin: 0 0 8px;
  font-size: 10px;
}

.field-toolbar {
  display: flex;
  flex-direction: column;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}

.field-card:hover .field-toolbar {
  opacity: 1;
}

.field-toolbar .el-button {
  padding: 2px;
  margin: 0;
}

.form-footer-design {
  margin-top: 24px;
  text-align: center;
}

.form-footer-preview {
  margin-top: 24px;
}
</style>
