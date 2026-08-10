<template>
  <div class="form-designer">
    <!-- 左侧：组件库 -->
    <ComponentLibrary
      @drag-start="handleDragStart"
      @add-field="addField"
    />

    <!-- 中间：画布 -->
    <FormCanvas
      :config="config"
      :mode="mode"
      :selected-id="selectedId"
      v-model:mode="mode"
      @add-field="addField"
      @select-field="selectField"
      @field-drag-start="handleFieldDragStart"
      @field-drop="handleFieldDrop"
      @remove-field="removeField"
      @copy-field="copyField"
      @move-up="moveUp"
      @move-down="moveDown"
    />

    <!-- 右侧：属性面板 -->
    <PropertyPanel
      v-if="mode === 'design'"
      :field="selectedField"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { FormConfig, FormField } from './types'
import { createFieldFromDefinition } from './fieldRegistry'
import ComponentLibrary from './ComponentLibrary.vue'
import FormCanvas from './FormCanvas.vue'
import PropertyPanel from './PropertyPanel.vue'

const props = defineProps<{
  modelValue: FormConfig
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: FormConfig): void
}>()

const config = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const mode = ref<'design' | 'preview'>('design')
const selectedId = ref<string | null>(null)
const dragFieldIndex = ref<number | null>(null)

const selectedField = computed(() => {
  if (!selectedId.value) return null
  return config.value.fields.find(f => f.id === selectedId.value) || null
})

/* -------------------------------------------------------------------------- */
/*  字段操作                                                                    */
/* -------------------------------------------------------------------------- */

function addField(type: string, label?: string) {
  const field = createFieldFromDefinition(type, label)
  config.value.fields.push(field)
  selectedId.value = field.id
}

function removeField(index: number) {
  const field = config.value.fields[index]
  config.value.fields.splice(index, 1)
  if (selectedId.value === field.id) {
    selectedId.value = null
  }
}

function copyField(index: number) {
  const original = config.value.fields[index]
  const copy: FormField = JSON.parse(JSON.stringify(original))
  copy.id = 'field_' + Math.random().toString(36).substr(2, 9)
  copy.title = original.title + '_副本'
  config.value.fields.splice(index + 1, 0, copy)
  selectedId.value = copy.id
}

function moveUp(index: number) {
  if (index === 0) return
  const fields = [...config.value.fields]
  ;[fields[index - 1], fields[index]] = [fields[index], fields[index - 1]]
  config.value.fields = fields
}

function moveDown(index: number) {
  if (index === config.value.fields.length - 1) return
  const fields = [...config.value.fields]
  ;[fields[index], fields[index + 1]] = [fields[index + 1], fields[index]]
  config.value.fields = fields
}

function selectField(field: FormField) {
  if (mode.value === 'design') {
    selectedId.value = field.id
  }
}

/* -------------------------------------------------------------------------- */
/*  拖拽逻辑                                                                    */
/* -------------------------------------------------------------------------- */

function handleDragStart(e: DragEvent, type: string) {
  if (e.dataTransfer) {
    e.dataTransfer.setData('component-type', type)
    e.dataTransfer.effectAllowed = 'copy'
  }
}

function handleFieldDragStart(e: DragEvent, index: number) {
  dragFieldIndex.value = index
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('field-index', String(index))
  }
}

function handleFieldDrop(e: DragEvent, index: number) {
  e.preventDefault()
  e.stopPropagation()
  const fromIndex = Number(e.dataTransfer?.getData('field-index'))
  if (!Number.isNaN(fromIndex) && fromIndex !== index) {
    const fields = [...config.value.fields]
    const [moved] = fields.splice(fromIndex, 1)
    fields.splice(index, 0, moved)
    config.value.fields = fields
    selectedId.value = null
  }
  dragFieldIndex.value = null
}

/* -------------------------------------------------------------------------- */
/*  暴露方法                                                                    */
/* -------------------------------------------------------------------------- */

function getConfig(): FormConfig {
  return config.value
}

function validate(): boolean {
  return config.value.title.trim().length > 0
}

defineExpose({ getConfig, validate })

/* -------------------------------------------------------------------------- */
/*  监听器                                                                      */
/* -------------------------------------------------------------------------- */

watch(() => config.value.fields, () => {
  // 确保选项类字段有 options 数组
  config.value.fields.forEach(f => {
    if (['radio', 'checkbox', 'select'].includes(f.type) && !Array.isArray(f.options)) {
      f.options = []
    }
    // 确保交通信息字段有正确的 props 结构
    if (f.type === 'transport_info' && !f.props) {
      f.props = {
        showDeparture: true,
        showReturn: true,
        showRemark: true,
        departureOptions: ['飞机', '火车', '其他'],
        returnOptions: ['飞机', '火车', '其他'],
      }
    }
  })
}, { deep: true })
</script>

<style scoped>
.form-designer {
  display: flex;
  height: 600px;
  border: 1px solid #e8eaed;
  border-radius: 12px;
  overflow: hidden;
  background: #f5f7fa;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
</style>
