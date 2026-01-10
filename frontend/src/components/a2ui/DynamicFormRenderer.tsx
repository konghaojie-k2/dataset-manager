/**
 * 动态A2UI表单渲染器
 * 根据A2UISchema动态渲染表单
 *
 * @module components/a2ui/DynamicFormRenderer
 */

'use client'

import React, { useState, useEffect } from 'react'
import { A2UISchema, A2UIFormData } from '@/types/a2ui'

// 动态导入字段组件
const fieldRenderers: Record<string, React.FC<any>> = {
  text: require('./fields/TextField').default,
  select: require('./fields/SelectField').default,
  multiselect: require('./fields/MultiSelectField').default,
  range: require('./fields/RangeField').default,
  toggle: require('./fields/ToggleField').default,
}

interface DynamicFormRendererProps {
  schema: A2UISchema
  onSubmit: (data: A2UIFormData) => Promise<void>
  onCancel?: () => void
  initialData?: A2UIFormData
}

export default function DynamicFormRenderer({
  schema,
  onSubmit,
  onCancel,
  initialData = {}
}: DynamicFormRendererProps) {
  const [formData, setFormData] = useState<A2UIFormData>(initialData)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)

  // 初始化表单数据（应用默认值）
  useEffect(() => {
    const defaultData: A2UIFormData = {}
    for (const field of schema.fields) {
      if (field.default !== undefined) {
        defaultData[field.name] = field.default
      }
    }
    setFormData({ ...defaultData, ...initialData })
  }, [schema, initialData])

  // 验证表单
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    for (const field of schema.fields) {
      const value = formData[field.name]

      // 必填验证
      if (field.required) {
        if (value === undefined || value === null || value === '') {
          newErrors[field.name] = `${field.label}是必填项`
          continue
        }
        // 对于数组和对象，检查是否为空
        if (Array.isArray(value) && value.length === 0) {
          newErrors[field.name] = `${field.label}是必填项`
          continue
        }
      }

      // 类型验证
      if (field.validation && value !== undefined && value !== null && value !== '') {
        // 范围字段特殊处理
        if (field.type === 'range' && typeof value === 'object') {
          const { min, max } = value
          if (field.validation.min !== undefined && min !== '' && Number(min) < field.validation.min) {
            newErrors[field.name] = `${field.label}最小值不能小于${field.validation.min}`
          }
          if (field.validation.max !== undefined && max !== '' && Number(max) > field.validation.max) {
            newErrors[field.name] = `${field.label}最大值不能大于${field.validation.max}`
          }
        } else {
          // 数值验证
          if (field.validation.min !== undefined && Number(value) < field.validation.min) {
            newErrors[field.name] = `${field.label}不能小于${field.validation.min}`
          }
          if (field.validation.max !== undefined && Number(value) > field.validation.max) {
            newErrors[field.name] = `${field.label}不能大于${field.validation.max}`
          }
        }

        // 正则验证
        if (field.validation.pattern && typeof value === 'string') {
          const regex = new RegExp(field.validation.pattern)
          if (!regex.test(value)) {
            newErrors[field.name] = `${field.label}格式不正确`
          }
        }
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // 提交表单
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)
    try {
      await onSubmit(formData)
    } catch (error) {
      console.error('表单提交失败:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-semibold mb-2">{schema.title}</h3>
      <p className="text-gray-600 mb-6">{schema.description}</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        {schema.fields.map((field) => {
          const FieldRenderer = fieldRenderers[field.type]
          if (!FieldRenderer) {
            console.warn(`未找到字段类型 ${field.type} 的渲染器`)
            return null
          }

          return (
            <FieldRenderer
              key={field.name}
              field={field}
              value={formData[field.name]}
              error={errors[field.name]}
              onChange={(value: any) => setFormData({ ...formData, [field.name]: value })}
            />
          )
        })}

        <div className="flex gap-3 pt-4">
          {schema.actions.map((action) => (
            <button
              key={action.id}
              type={action.type === 'submit' ? 'submit' : 'button'}
              onClick={action.type === 'cancel' ? onCancel : undefined}
              disabled={isSubmitting}
              className={`
                px-6 py-2 rounded-lg font-medium transition
                ${action.primary
                  ? 'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300 disabled:bg-gray-100'
                }
                ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              {isSubmitting && action.type === 'submit' ? '提交中...' : action.label}
            </button>
          ))}
        </div>
      </form>
    </div>
  )
}
