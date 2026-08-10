<template>
  <div class="transport-info-preview">
    <!-- 去程信息 -->
    <div v-if="field.props?.showDeparture !== false" class="transport-section">
      <div class="section-label">
        <el-icon><Position /></el-icon>
        <span>去程信息</span>
      </div>
      <el-select disabled placeholder="选择去程方式" size="small" style="width: 100%; margin-bottom: 8px">
        <el-option v-for="opt in departureOptions" :key="opt" :label="opt" :value="opt" />
      </el-select>
      <el-input disabled placeholder="航班/车次号" size="small" />
    </div>

    <!-- 回程信息 -->
    <div v-if="field.props?.showReturn !== false" class="transport-section">
      <div class="section-label">
        <el-icon><Position /></el-icon>
        <span>回程信息</span>
      </div>
      <el-select disabled placeholder="选择回程方式" size="small" style="width: 100%; margin-bottom: 8px">
        <el-option v-for="opt in returnOptions" :key="opt" :label="opt" :value="opt" />
      </el-select>
      <el-input disabled placeholder="航班/车次号" size="small" />
    </div>

    <!-- 备注 -->
    <div v-if="field.props?.showRemark !== false" class="transport-section">
      <div class="section-label">
        <el-icon><EditPen /></el-icon>
        <span>备注</span>
      </div>
      <el-input disabled type="textarea" :rows="2" placeholder="备注信息" size="small" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Position, EditPen } from '@element-plus/icons-vue'
import type { FormField } from '../types'

const props = defineProps<{
  field: FormField
}>()

const departureOptions = computed(() => {
  return props.field.props?.departureOptions || ['飞机', '火车', '其他']
})

const returnOptions = computed(() => {
  return props.field.props?.returnOptions || ['飞机', '火车', '其他']
})
</script>

<style scoped>
.transport-info-preview {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.transport-section {
  background: #f8f9fb;
  border-radius: 6px;
  padding: 10px;
  border: 1px solid #ebeef5;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.section-label .el-icon {
  font-size: 13px;
  color: #409eff;
}
</style>
