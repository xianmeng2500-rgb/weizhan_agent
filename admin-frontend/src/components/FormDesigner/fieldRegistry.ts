/**
 * 字段注册表 —— 可扩展性的核心
 *
 * 新增字段类型步骤：
 * 1. 在下方 registry 中添加一条 FieldDefinition
 * 2. 如果是复合字段（hasCustomPreview），在 fields/ 目录下创建对应的预览组件
 * 3. 如需在 H5 端支持，在 h5-frontend 的 FormView.vue 中添加对应渲染逻辑
 */

import type { FieldDefinition, CategoryDefinition } from './types'

/* -------------------------------------------------------------------------- */
/*  分类定义                                                                    */
/* -------------------------------------------------------------------------- */

export const categories: CategoryDefinition[] = [
  { key: 'info', label: '填写者信息', icon: 'User' },
  { key: 'basic', label: '基础组件', icon: 'EditPen' },
  { key: 'business', label: '业务组件', icon: 'Briefcase' },
  { key: 'media', label: '多媒体', icon: 'Picture' },
]

/* -------------------------------------------------------------------------- */
/*  字段注册表                                                                  */
/* -------------------------------------------------------------------------- */

const registry: Record<string, FieldDefinition> = {
  /* ---------------------------- 填写者信息 ---------------------------- */
  text: {
    type: 'text',
    label: '单行文本',
    icon: 'EditPen',
    category: 'basic',
    defaultTitle: '单行文本',
    defaultPlaceholder: '请输入',
    defaultProps: { maxLength: 200 },
    supportsPlaceholder: true,
    supportsDefaultValue: true,
  },
  phone: {
    type: 'phone',
    label: '手机号',
    icon: 'Iphone',
    category: 'info',
    defaultTitle: '手机号',
    defaultPlaceholder: '请输入手机号',
    supportsPlaceholder: true,
    supportsDefaultValue: true,
  },
  idcard: {
    type: 'idcard',
    label: '身份证号',
    icon: 'Postcard',
    category: 'info',
    defaultTitle: '身份证号',
    defaultPlaceholder: '请输入身份证号',
    supportsPlaceholder: true,
    supportsDefaultValue: true,
  },
  email: {
    type: 'email',
    label: '邮箱',
    icon: 'Message',
    category: 'info',
    defaultTitle: '邮箱',
    defaultPlaceholder: '请输入邮箱',
    supportsPlaceholder: true,
    supportsDefaultValue: true,
  },
  name: {
    type: 'text',
    label: '姓名',
    icon: 'User',
    category: 'info',
    defaultTitle: '姓名',
    defaultPlaceholder: '请输入姓名',
    supportsPlaceholder: true,
    supportsDefaultValue: true,
  },
  employee_id: {
    type: 'text',
    label: '工号',
    icon: 'Document',
    category: 'info',
    defaultTitle: '工号',
    defaultPlaceholder: '请输入工号',
    supportsPlaceholder: true,
    supportsDefaultValue: true,
  },
  gender: {
    type: 'radio',
    label: '性别',
    icon: 'DataLine',
    category: 'info',
    defaultTitle: '性别',
    defaultOptions: ['男', '女'],
    supportsOptions: true,
    supportsDefaultValue: true,
  },

  /* ----------------------------- 基础组件 ----------------------------- */
  textarea: {
    type: 'textarea',
    label: '多行文本',
    icon: 'Notebook',
    category: 'basic',
    defaultTitle: '多行文本',
    defaultPlaceholder: '请输入',
    defaultProps: { rows: 3 },
    supportsPlaceholder: true,
    supportsDefaultValue: true,
  },
  number: {
    type: 'number',
    label: '数字',
    icon: 'DataLine',
    category: 'basic',
    defaultTitle: '数字',
    defaultPlaceholder: '请输入数字',
    supportsPlaceholder: true,
    supportsDefaultValue: true,
  },
  radio: {
    type: 'radio',
    label: '单选项',
    icon: 'Checked',
    category: 'basic',
    defaultTitle: '单选项',
    defaultOptions: ['选项1', '选项2'],
    supportsOptions: true,
    supportsDefaultValue: true,
  },
  checkbox: {
    type: 'checkbox',
    label: '多选项',
    icon: 'Collection',
    category: 'basic',
    defaultTitle: '多选项',
    defaultOptions: ['选项1', '选项2'],
    supportsOptions: true,
    supportsDefaultValue: true,
  },
  select: {
    type: 'select',
    label: '下拉选择',
    icon: 'List',
    category: 'basic',
    defaultTitle: '下拉选择',
    defaultOptions: ['选项1', '选项2'],
    supportsPlaceholder: true,
    supportsOptions: true,
    supportsDefaultValue: true,
  },
  date: {
    type: 'date',
    label: '日期',
    icon: 'Calendar',
    category: 'basic',
    defaultTitle: '日期',
    defaultPlaceholder: '选择日期',
    supportsPlaceholder: true,
  },
  time: {
    type: 'time',
    label: '时间',
    icon: 'Clock',
    category: 'basic',
    defaultTitle: '时间',
    defaultPlaceholder: '选择时间',
    supportsPlaceholder: true,
  },
  region: {
    type: 'region',
    label: '地区',
    icon: 'Location',
    category: 'basic',
    defaultTitle: '地区',
    defaultPlaceholder: '请选择地区',
    supportsPlaceholder: true,
  },
  divider: {
    type: 'divider',
    label: '中划线',
    icon: 'Minus',
    category: 'basic',
    defaultTitle: '分割线',
    defaultProps: { text: '' },
    hasCustomProperties: true,
  },
  tip_text: {
    type: 'tip_text',
    label: '提示文字',
    icon: 'InfoFilled',
    category: 'basic',
    defaultTitle: '提示文字',
    defaultProps: { content: '请根据实际情况填写以下信息。', tone: 'info' },
    hasCustomProperties: true,
  },
  agreement: {
    type: 'agreement',
    label: '同意协议',
    icon: 'Checked',
    category: 'basic',
    defaultTitle: '同意协议',
    defaultPlaceholder: '我已阅读并同意相关协议',
    defaultProps: { agreementContent: '' },
    supportsPlaceholder: true,
    supportsDefaultValue: true,
    hasCustomProperties: true,
  },

  /* ----------------------------- 业务组件 ----------------------------- */
  transport_info: {
    type: 'transport_info',
    label: '交通信息',
    icon: 'Van',
    category: 'business',
    defaultTitle: '交通信息',
    defaultPlaceholder: '请填写交通信息',
    supportsPlaceholder: true,
    hasCustomPreview: true,
    hasCustomProperties: true,
    defaultProps: {
      showDeparture: true,
      showReturn: true,
      showRemark: true,
      departureOptions: ['飞机', '火车', '其他'],
      returnOptions: ['飞机', '火车', '其他'],
    },
  },

  /* ------------------------------ 多媒体 ------------------------------ */
  image: {
    type: 'image',
    label: '图片',
    icon: 'Picture',
    category: 'media',
    defaultTitle: '图片',
    defaultPlaceholder: '请上传图片',
    supportsPlaceholder: true,
  },
}

/* -------------------------------------------------------------------------- */
/*  注册表 API                                                                  */
/* -------------------------------------------------------------------------- */

/** 获取字段定义 */
export function getFieldDefinition(type: string): FieldDefinition | undefined {
  return registry[type]
}

/** 获取某分类下的所有组件（用于组件库渲染） */
export function getFieldsByCategory(category: string): FieldDefinition[] {
  return Object.values(registry).filter((f) => f.category === category)
}

/** 注册新字段类型（供后期扩展使用） */
export function registerField(def: FieldDefinition): void {
  registry[def.type] = def
}

/** 获取所有分类 */
export function getCategories(): CategoryDefinition[] {
  return categories
}

/**
 * 根据字段定义创建一个新字段实例
 */
export function createFieldFromDefinition(type: string, label?: string): import('./types').FormField {
  const def = registry[type] || registry['text']
  const field: import('./types').FormField = {
    id: 'field_' + Math.random().toString(36).substr(2, 9),
    type: def.type,
    title: label || def.defaultTitle || '未命名字段',
    required: false,
    props: { ...(def.defaultProps || {}) },
  }

  if (def.defaultPlaceholder) {
    field.placeholder = def.defaultPlaceholder
  }
  if (def.defaultOptions) {
    field.options = [...def.defaultOptions]
  }
  if (def.type === 'checkbox') {
    field.defaultValue = []
  }

  return field
}

/** 判断字段是否支持占位提示 */
export function fieldSupportsPlaceholder(type: string): boolean {
  return registry[type]?.supportsPlaceholder ?? false
}

/** 判断字段是否支持选项编辑 */
export function fieldSupportsOptions(type: string): boolean {
  return registry[type]?.supportsOptions ?? false
}

/** 判断字段是否支持默认值 */
export function fieldSupportsDefaultValue(type: string): boolean {
  return registry[type]?.supportsDefaultValue ?? false
}

/** 判断字段是否有自定义预览 */
export function fieldHasCustomPreview(type: string): boolean {
  return registry[type]?.hasCustomPreview ?? false
}

/** 判断字段是否有自定义属性 */
export function fieldHasCustomProperties(type: string): boolean {
  return registry[type]?.hasCustomProperties ?? false
}
