<template>
  <div class="component-library">
    <div class="library-header">
      <el-icon :size="16" color="#409eff"><Grid /></el-icon>
      <span>组件库</span>
    </div>
    <div class="library-body">
      <div v-for="cat in categories" :key="cat.key" class="component-group">
        <div class="group-title">
          <el-icon :size="12"><component :is="cat.icon" /></el-icon>
          <span>{{ cat.label }}</span>
        </div>
        <div class="component-grid">
          <el-tooltip
            v-for="c in getFieldsByCategory(cat.key)"
            :key="c.type + c.label"
            :content="c.label"
            placement="top"
            :show-after="500"
          >
            <div
              class="component-item"
              draggable="true"
              @dragstart="$emit('drag-start', $event, c.type)"
              @click="$emit('add-field', c.type, c.label)"
            >
              <el-icon :size="18"><component :is="c.icon" /></el-icon>
              <span class="component-label">{{ c.label }}</span>
            </div>
          </el-tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  getCategories,
  getFieldsByCategory,
} from './fieldRegistry'

const categories = getCategories()

defineEmits<{
  (e: 'drag-start', event: DragEvent, type: string): void
  (e: 'add-field', type: string, label?: string): void
}>()
</script>

<style scoped>
.component-library {
  width: 200px;
  background: #fff;
  border-right: 1px solid #e8eaed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.library-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 14px 16px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
}

.library-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 10px;
}

.component-group {
  margin-bottom: 16px;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #909399;
  margin-bottom: 8px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 0 4px;
}

.component-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.component-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 10px 4px;
  border: 1px solid #e8eaed;
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s ease;
  font-size: 11px;
  color: #606266;
  background: #fafbfc;
  user-select: none;
}

.component-item:hover {
  border-color: #409eff;
  color: #409eff;
  background: #ecf5ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.component-item:active {
  cursor: grabbing;
  transform: translateY(0);
}

.component-label {
  text-align: center;
  line-height: 1.2;
}
</style>
