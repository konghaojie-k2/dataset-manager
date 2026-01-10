/**
 * 多选字段组件
 *
 * @module components/a2ui/fields/MultiSelectField
 */

'use client'

import React, { useState } from 'react'
import { A2UIField } from '@/types/a2ui'

interface MultiSelectFieldProps {
  field: A2UIField
  value: any
  error?: string
  onChange: (value: any) => void
}

export default function MultiSelectField({ field, value, error, onChange }: MultiSelectFieldProps) {
  const [isOpen, setIsOpen] = useState(false)

  // 获取当前选中的值列表
  const selectedValues = value || field.default || []

  // 处理选项点击
  const handleOptionClick = (optionValue: string) => {
    const newValues = selectedValues.includes(optionValue)
      ? selectedValues.filter((v: string) => v !== optionValue)
      : [...selectedValues, optionValue]

    onChange(newValues)
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {field.label}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </label>

      <div className="relative">
        {/* 选择框 */}
        <div
          onClick={() => setIsOpen(!isOpen)}
          className={`
            w-full px-3 py-2 border rounded-lg cursor-pointer min-h-[42px]
            ${error ? 'border-red-500' : 'border-gray-300'}
          `}
        >
          {selectedValues.length === 0 ? (
            <span className="text-gray-400">{field.placeholder || '请选择'}</span>
          ) : (
            <div className="flex flex-wrap gap-1">
              {selectedValues.map((val: string) => (
                <span
                  key={val}
                  className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                >
                  {val}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 下拉选项 */}
        {isOpen && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
            {field.options?.map((option) => (
              <div
                key={option.value}
                onClick={() => {
                  handleOptionClick(option.value)
                }}
                className={`
                  px-3 py-2 cursor-pointer hover:bg-blue-50
                  ${selectedValues.includes(option.value) ? 'bg-blue-100' : ''}
                `}
              >
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedValues.includes(option.value)}
                    onChange={() => {}}
                    className="mr-2"
                  />
                  <span>{option.label}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-500 mt-1">{error}</p>
      )}
    </div>
  )
}
