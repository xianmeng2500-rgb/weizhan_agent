/**
 * FormDesigner 共享类型定义
 */

export interface FormField {
  id: string
  type: string
  title: string
  required: boolean
  placeholder?: string
  options?: string[]
  defaultValue?: any
  props?: Record<string, any>
}

export interface FormConfig {
  title: string
  description: string
  buttonText: string
  fields: FormField[]
}

export type FieldCategory = 'info' | 'basic' | 'media' | 'business'

/**
 * 字段定义 —— 注册表中的一条记录
 * 后续新增字段类型只需在 fieldRegistry 中注册一条 FieldDefinition 即可
 */
export interface FieldDefinition {
  /** 字段类型标识（唯一） */
  type: string
  /** 组件库中显示的名称 */
  label: string
  /** Element Plus 图标组件名 */
  icon: string
  /** 所属分类 */
  category: FieldCategory
  /** 默认标题 */
  defaultTitle?: string
  /** 默认占位提示 */
  defaultPlaceholder?: string
  /** 默认 props */
  defaultProps?: Record<string, any>
  /** 默认选项（用于 radio/checkbox/select） */
  defaultOptions?: string[]
  /** 是否支持占位提示 */
  supportsPlaceholder?: boolean
  /** 是否支持选项编辑 */
  supportsOptions?: boolean
  /** 是否支持默认值 */
  supportsDefaultValue?: boolean
  /** 是否有自定义预览组件（用于复合字段如交通信息） */
  hasCustomPreview?: boolean
  /** 是否有自定义属性编辑器 */
  hasCustomProperties?: boolean
}

/** 组件库分类定义 */
export interface CategoryDefinition {
  key: FieldCategory
  label: string
  icon: string
}
