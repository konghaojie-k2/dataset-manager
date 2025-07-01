'use client'

import React, { useState, useEffect, useRef } from 'react'
import { api } from '@/lib/api'

interface Tag {
  id: number
  name: string
  description?: string
  color: string
  category?: string
  usage_count: number
}

interface TagEditorProps {
  datasetId: string
  datasetName: string
  currentTags: string[]
  isOpen: boolean
  onClose: () => void
  onSave: (tags: string[]) => void
}

const TagEditor: React.FC<TagEditorProps> = ({
  datasetId,
  datasetName,
  currentTags,
  isOpen,
  onClose,
  onSave
}) => {
  const [selectedTags, setSelectedTags] = useState<string[]>(currentTags)
  const [availableTags, setAvailableTags] = useState<Tag[]>([])
  const [inputValue, setInputValue] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  // 加载可用标签
  useEffect(() => {
    if (isOpen) {
      loadAvailableTags()
      setSelectedTags(currentTags)
    }
  }, [isOpen, currentTags])

  // 自动隐藏建议列表
  useEffect(() => {
    if (showSuggestions && inputValue.length === 0) {
      setShowSuggestions(false)
    }
  }, [inputValue, showSuggestions])

  const loadAvailableTags = async () => {
    try {
      setLoading(true)
      const response = await api.tags.list()
      setAvailableTags(response.tags || [])
    } catch (error) {
      console.error('Failed to load tags:', error)
    } finally {
      setLoading(false)
    }
  }

  // 过滤建议标签
  const filteredSuggestions = availableTags.filter(tag => 
    tag.name.toLowerCase().includes(inputValue.toLowerCase()) &&
    !selectedTags.includes(tag.name)
  ).slice(0, 8) // 最多显示8个建议

  // 热门标签（按使用次数排序）
  const popularTags = availableTags
    .filter(tag => !selectedTags.includes(tag.name))
    .sort((a, b) => (b.usage_count || 0) - (a.usage_count || 0))
    .slice(0, 6)

  // 添加标签
  const addTag = async (tagName: string) => {
    const trimmedName = tagName.trim()
    if (!trimmedName || selectedTags.includes(trimmedName)) return

    // 检查标签是否存在
    let existingTag = availableTags.find(tag => tag.name === trimmedName)
    
    // 如果标签不存在，创建新标签
    if (!existingTag) {
      try {
        const newTag = await api.tags.create({
          name: trimmedName,
          description: `自动创建的标签: ${trimmedName}`,
          color: generateRandomColor()
        })
        setAvailableTags(prev => [...prev, newTag])
      } catch (error) {
        console.error('Failed to create tag:', error)
        alert('创建标签失败')
        return
      }
    }

    setSelectedTags(prev => [...prev, trimmedName])
    setInputValue('')
    setShowSuggestions(false)
  }

  // 移除标签
  const removeTag = (tagName: string) => {
    setSelectedTags(prev => prev.filter(tag => tag !== tagName))
  }

  // 处理输入
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setInputValue(value)
    setShowSuggestions(value.length > 0)
  }

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (inputValue.trim()) {
        addTag(inputValue)
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false)
      setInputValue('')
    }
  }

  // 保存标签
  const handleSave = async () => {
    try {
      setSaving(true)
      console.log('保存标签:', { datasetId, selectedTags })

      const response = await api.tags.updateDatasetTags(datasetId, selectedTags)
      console.log('保存响应:', response)

      onSave(selectedTags)
      onClose()
    } catch (error) {
      console.error('保存标签失败:', error)

      // 更详细的错误信息
      let errorMessage = '保存标签失败'
      if (error instanceof Error) {
        errorMessage += `: ${error.message}`
      }

      alert(errorMessage)
    } finally {
      setSaving(false)
    }
  }

  // 生成随机颜色
  const generateRandomColor = () => {
    const colors = [
      '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8',
      '#6f42c1', '#e83e8c', '#fd7e14', '#20c997', '#6c757d'
    ]
    return colors[Math.floor(Math.random() * colors.length)]
  }

  // 获取标签颜色
  const getTagColor = (tagName: string) => {
    const tag = availableTags.find(t => t.name === tagName)
    return tag?.color || '#007bff'
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4"
      style={{ zIndex: 9999 }}
      onClick={(e) => {
        // 点击背景关闭，但不影响对话框内部
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <div
        className="tag-editor-modal bg-white rounded-lg max-w-2xl w-full flex flex-col relative shadow-2xl"
        style={{
          maxHeight: 'calc(100vh - 2rem)',
          zIndex: 10000,
          pointerEvents: 'auto'
        }}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-500 to-purple-600 text-white flex-shrink-0 rounded-t-lg">
          <div className="flex items-center">
            <span className="text-2xl mr-3">🏷️</span>
            <div>
              <h2 className="text-xl font-semibold">编辑标签</h2>
              <p className="text-blue-100 text-sm">{datasetName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 text-2xl font-bold transition-colors"
          >
            ×
          </button>
        </div>

        {/* 内容 */}
        <div
          className="p-6 overflow-y-auto flex-1"
          style={{
            minHeight: '200px',
            maxHeight: 'calc(100vh - 16rem)' // 调整高度为按钮留出空间
          }}
        >
          {/* 输入框 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              选择或输入标签...
            </label>
            <div className="relative" style={{ zIndex: 1 }}>
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                onFocus={() => setShowSuggestions(inputValue.length > 0)}
                onBlur={() => {
                  // 延迟隐藏建议，允许点击建议项
                  setTimeout(() => setShowSuggestions(false), 200)
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="输入标签名称后按回车添加，点击下方标签快速选择"
                style={{ position: 'relative', zIndex: 2 }}
              />
              
              {/* 建议列表 */}
              {showSuggestions && filteredSuggestions.length > 0 && (
                <div
                  ref={suggestionsRef}
                  className="suggestions-list absolute top-full left-0 right-0 bg-white border border-gray-300 rounded-lg shadow-lg mt-1 max-h-48 overflow-y-auto"
                  style={{
                    zIndex: 10001,
                    position: 'absolute'
                  }}
                >
                  {filteredSuggestions.map(tag => (
                    <button
                      key={tag.id}
                      onClick={() => addTag(tag.name)}
                      className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center justify-between border-b border-gray-100 last:border-b-0"
                    >
                      <span>{tag.name}</span>
                      <span className="text-xs text-gray-500">使用 {tag.usage_count} 次</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div className="mt-2 text-sm text-blue-600 flex items-center">
              <span className="mr-2">💡</span>
              输入新标签名称后按回车创建，点击下方标签快速选择
            </div>
          </div>

          {/* 已选标签 */}
          {selectedTags.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">已选标签</h3>
              <div className="flex flex-wrap gap-2">
                {selectedTags.map(tagName => (
                  <span
                    key={tagName}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium text-white"
                    style={{ backgroundColor: getTagColor(tagName) }}
                  >
                    {tagName}
                    <button
                      onClick={() => removeTag(tagName)}
                      className="ml-2 text-white hover:text-gray-200"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 热门标签 */}
          {popularTags.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">热门标签</h3>
              <div className="flex flex-wrap gap-2">
                {popularTags.map(tag => (
                  <button
                    key={tag.id}
                    onClick={() => addTag(tag.name)}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm border border-gray-300 hover:bg-gray-50 transition-colors"
                  >
                    <span
                      className="w-2 h-2 rounded-full mr-2"
                      style={{ backgroundColor: tag.color }}
                    />
                    {tag.name}
                    <span className="ml-2 text-xs text-gray-500">({tag.usage_count})</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p className="text-gray-600 mt-2">加载标签中...</p>
            </div>
          )}
        </div>

        {/* 底部按钮 - 固定在底部但可见 */}
        <div
          className="button-area flex justify-end gap-3 p-4 border-t bg-gray-50 flex-shrink-0 rounded-b-lg"
          style={{
            position: 'sticky',
            bottom: 0,
            zIndex: 99999,
            backgroundColor: '#f9fafb',
            borderTop: '1px solid #e5e7eb',
            marginTop: 'auto'
          }}
        >
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm"
            style={{
              zIndex: 100000,
              pointerEvents: 'auto',
              position: 'relative'
            }}
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center shadow-sm"
            style={{
              zIndex: 100000,
              pointerEvents: 'auto',
              position: 'relative'
            }}
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                保存中...
              </>
            ) : (
              '保存'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default TagEditor
