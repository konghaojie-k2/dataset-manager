'use client'

import React from 'react'
import { FiEye, FiDownload, FiTrash2, FiTag, FiCalendar, FiFileText, FiTrendingUp, FiMoreVertical } from 'react-icons/fi'
import { useRouter } from 'next/navigation'
import { DatasetMetadata } from '@/types/dataset'

interface DatasetCardCompactProps {
  dataset: DatasetMetadata
  onDelete?: (id: string) => void
  onStartAnalysis?: (id: string, type: 'business' | 'quality') => void
}

const DatasetCardCompact: React.FC<DatasetCardCompactProps> = ({
  dataset,
  onDelete,
  onStartAnalysis
}) => {
  const router = useRouter()

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return '今天'
    if (diffDays === 1) return '昨天'
    if (diffDays < 7) return `${diffDays} 天前`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} 周前`
    return date.toLocaleDateString('zh-CN')
  }

  const getQualityColor = (score?: number): string => {
    if (!score) return 'bg-gray-300'
    if (score >= 80) return 'bg-green-600'
    if (score >= 60) return 'bg-yellow-600'
    return 'bg-red-600'
  }

  // 安全地获取质量分数
  const qualityScore = dataset.quality_analysis_results?.overall_score ||
                       dataset.quality_analysis_results?.quality_score

  // 获取行数和列数
  const rows = dataset.columns?.length || 0
  const columns = dataset.columns?.length || 0

  const handlePreview = () => {
    router.push(`/datasets/${dataset.id}/preview`)
  }

  const handleDownload = () => {
    window.open(`/api/v1/datasets/${dataset.id}/download`, '_blank')
  }

  return (
    <div className="group bg-white rounded-lg border border-gray-200 hover:border-blue-500 hover:shadow-md transition-all duration-150 cursor-pointer overflow-hidden">
      {/* 卡片主体 */}
      <div className="p-4">
        {/* 头部：名称和快速操作 */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1 min-w-0 pr-2">
            <h3 className="text-base font-medium text-gray-800 truncate group-hover:text-blue-700 transition-colors">
              {dataset.name}
            </h3>
            {dataset.description && (
              <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{dataset.description}</p>
            )}
          </div>
          <button
            className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
            title="更多操作"
          >
            <FiMoreVertical className="w-4 h-4" />
          </button>
        </div>

        {/* 标签 - 只渲染字符串数组 */}
        {dataset.tags && Array.isArray(dataset.tags) && dataset.tags.length > 0 && dataset.tags[0] && typeof dataset.tags[0] === 'string' && (
          <div className="flex items-center flex-wrap gap-1.5 mb-3">
            {dataset.tags.slice(0, 2).map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded"
              >
                {tag}
              </span>
            ))}
            {dataset.tags.length > 2 && (
              <span className="text-xs text-gray-500">+{dataset.tags.length - 2}</span>
            )}
          </div>
        )}

        {/* 数据统计 - Material Design风格 */}
        <div className="grid grid-cols-3 gap-3 mb-3">
          {/* 文件大小 */}
          <div className="flex flex-col">
            <div className="flex items-center text-gray-500 mb-1">
              <FiFileText className="w-3.5 h-3.5 mr-1" />
              <span className="text-xs">大小</span>
            </div>
            <span className="text-sm font-medium text-gray-800">{formatFileSize(dataset.file_size)}</span>
          </div>

          {/* 列数 */}
          <div className="flex flex-col">
            <div className="flex items-center text-gray-500 mb-1">
              <FiTrendingUp className="w-3.5 h-3.5 mr-1" />
              <span className="text-xs">列数</span>
            </div>
            <span className="text-sm font-medium text-gray-800">{columns}</span>
          </div>

          {/* 质量评分 */}
          <div className="flex flex-col">
            <div className="flex items-center text-gray-500 mb-1">
              <span className="text-xs">质量</span>
            </div>
            {qualityScore !== undefined ? (
              <span className="text-sm font-medium text-gray-800">{qualityScore}%</span>
            ) : (
              <span className="text-sm text-gray-400">-</span>
            )}
          </div>
        </div>

        {/* 底部：操作和时间 */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-100">
          {/* 左侧操作按钮 */}
          <div className="flex items-center space-x-1">
            <button
              onClick={handlePreview}
              className="px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-50 rounded transition-colors"
            >
              预览
            </button>
            <button
              onClick={handleDownload}
              className="px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-50 rounded transition-colors"
            >
              下载
            </button>
            {onDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  if (confirm('确定要删除这个数据集吗？')) {
                    onDelete(dataset.id)
                  }
                }}
                className="px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 rounded transition-colors"
              >
                删除
              </button>
            )}
          </div>

          {/* 上传时间 */}
          <div className="flex items-center text-xs text-gray-500">
            <FiCalendar className="w-3 h-3 mr-1" />
            {formatDate(dataset.upload_time)}
          </div>
        </div>

        {/* 处理状态指示器 */}
        {(dataset.processing_status === 'business_analyzing' ||
          dataset.processing_status === 'quality_analyzing' ||
          dataset.processing_status === 'extracting') && (
          <div className="mt-2 pt-2 border-t border-gray-100">
            <div className="flex items-center text-blue-700 text-xs">
              <div className="animate-spin rounded-full h-3 w-3 border-2 border-blue-700 border-t-transparent mr-2"></div>
              {dataset.processing_status === 'extracting' && '提取中...'}
              {dataset.processing_status === 'business_analyzing' && '业务分析中...'}
              {dataset.processing_status === 'quality_analyzing' && '质量分析中...'}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DatasetCardCompact
