/**
 * 范围字段组件
 *
 * @module components/a2ui/fields/RangeField
 */

'use client'

import React from 'react'
import { A2UIField } from '@/types/a2ui'

interface RangeFieldProps {
  field: A2UIField
  value: any
  error?: string
  onChange: (value: any) => void
}

export default function RangeField({ field, value, error, onChange }: RangeFieldProps) {
  // 获取范围值
  const rangeValue = value || field.default || { min: '', max: '' }

  const handleMinChange = (min: string) => {
    onChange({ ...rangeValue, min })
  }

  const handleMaxChange = (max: string) => {
    onChange({ ...rangeValue, max })
  }

  // 获取验证规则
  const min = field.validation?.min
  const max = field.validation?.max

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {field.label}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </label>

      <div className="flex items-center gap-2">
        <div className="flex-1">
          <input
            type="number"
            value={rangeValue.min || ''}
            onChange={(e) => handleMinChange(e.target.value)}
            placeholder="最小值"
            min={min}
            max={max}
            className={`
              w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2
              ${error ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}
            `}
          />
        </div>

        <span className="text-gray-500">-</span>

        <div className="flex-1">
          <input
            type="number"
            value={rangeValue.max || ''}
            onChange={(e) => handleMaxChange(e.target.value)}
            placeholder="最大值"
            min={min}
            max={max}
            className={`
              w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2
              ${error ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}
            `}
          />
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-500 mt-1">{error}</p>
      )}
    </div>
  )
}
