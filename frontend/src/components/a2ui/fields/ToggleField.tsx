/**
 * 开关字段组件
 *
 * @module components/a2ui/fields/ToggleField
 */

'use client'

import React from 'react'
import { A2UIField } from '@/types/a2ui'

interface ToggleFieldProps {
  field: A2UIField
  value: any
  error?: string
  onChange: (value: any) => void
}

export default function ToggleField({ field, value, error, onChange }: ToggleFieldProps) {
  // 获取当前值
  const currentValue = value ?? field.default ?? false

  const handleChange = () => {
    onChange(!currentValue)
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {field.label}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </label>

      <button
        type="button"
        onClick={handleChange}
        className={`
          relative inline-flex h-6 w-11 items-center rounded-full transition-colors
          ${currentValue ? 'bg-blue-600' : 'bg-gray-300'}
        `}
      >
        <span
          className={`
            inline-block h-4 w-4 transform rounded-full bg-white transition-transform
            ${currentValue ? 'translate-x-6' : 'translate-x-1'}
          `}
        />
      </button>

      <span className="ml-2 text-sm text-gray-600">
        {currentValue ? '是' : '否'}
      </span>

      {error && (
        <p className="text-sm text-red-500 mt-1">{error}</p>
      )}
    </div>
  )
}
