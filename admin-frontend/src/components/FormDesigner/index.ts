/**
 * FormDesigner 组件导出入口
 *
 * 使用方式：
 *   import FormDesigner from '@/components/FormDesigner'
 *   <FormDesigner v-model="formConfig" />
 *
 * 扩展新字段类型：
 *   import { registerField } from '@/components/FormDesigner'
 *   registerField({ type: 'my_field', label: '自定义字段', icon: 'EditPen', category: 'basic', ... })
 */

import FormDesigner from './FormDesigner.vue'

export default FormDesigner

// 导出类型
export type { FormField, FormConfig, FieldDefinition, FieldCategory } from './types'

// 导出注册表 API（供后期扩展）
export {
  registerField,
  getFieldDefinition,
  getFieldsByCategory,
  getCategories,
  createFieldFromDefinition,
  fieldSupportsPlaceholder,
  fieldSupportsOptions,
  fieldSupportsDefaultValue,
  fieldHasCustomPreview,
  fieldHasCustomProperties,
} from './fieldRegistry'
