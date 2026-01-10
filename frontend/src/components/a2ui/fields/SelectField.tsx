/**
 * 选择字段组件
 *
 * @module components/a2ui/fields/SelectField
 */

'use client'

import React from 'react'
import { A2UIField } from '@/types/a2ui'

interface SelectFieldProps {
  field: A2UIField
  value: any
  error?: string
  onChange: (value: any) => void
}

export default function SelectField({ field, value, error, onChange }: SelectFieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {field.label}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </label>

      <select
        value={value ?? field.default ?? ''}
        onChange={(e) => onChange(e.target.value)}
        className={`
          w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2
          ${error ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}
        `}
      >
        {field.placeholder && (
          <option value="" disabled>
            {field.placeholder}
          </option>
        )}

        {field.options?.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {error && (
        <p className="text-sm text-red-500 mt-1">{error}</p>
      )}
    </div>
  )
}
