/**
 * A2UI 相关的类型定义
 */

/**
 * A2UI 字段类型
 */
export type A2UIFieldType =
  | 'text'
  | 'select'
  | 'multiselect'
  | 'range'
  | 'date_range'
  | 'toggle'

/**
 * A2UI 字段定义
 */
export interface A2UIField {
  name: string
  type: A2UIFieldType
  label: string
  placeholder?: string
  options?: Array<{ value: string; label: string }>
  required: boolean
  validation?: {
    pattern?: string
    min?: number
    max?: number
    minLength?: number
    maxLength?: number
  }
  default?: any
}

/**
 * A2UI 操作定义
 */
export interface A2UIAction {
  id: string
  type: 'submit' | 'button' | 'cancel'
  label: string
  primary: boolean
}

/**
 * A2UI 表单类型
 */
export type A2UIFormType =
  | 'search_refinement'
  | 'filter_builder'
  | 'preference_setting'

/**
 * A2UI 表单 Schema
 */
export interface A2UISchema {
  version: string
  form_type: A2UIFormType
  title: string
  description: string
  fields: A2UIField[]
  actions: A2UIAction[]
}

/**
 * A2UI 表单数据
 */
export interface A2UIFormData {
  [fieldName: string]: any
}

/**
 * 表单验证错误
 */
export interface A2UIValidationError {
  fieldName: string
  message: string
}

/**
 * 表单验证状态
 */
export interface A2UIValidationState {
  isValid: boolean
  errors: Record<string, string>
}
