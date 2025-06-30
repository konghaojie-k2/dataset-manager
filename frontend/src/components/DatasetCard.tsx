'use client'

import React, { useState } from 'react'
import { DatasetMetadata, DatasetStatus } from '@/types/dataset'
import { formatFileSize, formatDate } from '@/lib/api'
import { api } from '@/lib/api'

interface DatasetCardProps {
  dataset: DatasetMetadata
  onDelete?: (id: string) => void
  onStartBusinessAnalysis?: (id: string) => void
  onStartQualityAnalysis?: (id: string) => void
}

const DatasetCard: React.FC<DatasetCardProps> = ({
  dataset,
  onDelete,
  onStartBusinessAnalysis,
  onStartQualityAnalysis,
}) => {
  const [showPreview, setShowPreview] = useState(false)
  const [previewData, setPreviewData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  // 获取状态显示
  const getStatusBadge = (status: DatasetStatus) => {
    switch (status) {
      case DatasetStatus.UPLOADED:
        return <span className="status-badge status-not-started">未开始</span>
      case DatasetStatus.BUSINESS_ANALYZING:
        return <span className="status-badge status-analyzing">业务分析中</span>
      case DatasetStatus.BUSINESS_COMPLETED:
        return <span className="status-badge status-completed">业务分析完成</span>
      case DatasetStatus.QUALITY_ANALYZING:
        return <span className="status-badge status-analyzing">质量分析中</span>
      case DatasetStatus.QUALITY_COMPLETED:
        return <span className="status-badge status-completed">全部完成</span>
      case DatasetStatus.ANALYSIS_FAILED:
        return <span className="status-badge bg-red-100 text-red-800">分析失败</span>
      default:
        return <span className="status-badge status-not-started">未知状态</span>
    }
  }

  // 获取质量评分显示
  const getQualityScore = () => {
    if (dataset.quality_analysis_results) {
      const score = Math.round(
        dataset.quality_analysis_results.overall_score || 
        dataset.quality_analysis_results.quality_score || 
        0
      )
      return <span className="quality-score">{score}分</span>
    }
    return <span className="text-gray-500">未评估</span>
  }

  // 处理预览
  const handlePreview = async () => {
    try {
      setLoading(true)
      const preview = await api.datasets.preview(dataset.id)
      setPreviewData(preview)
      setShowPreview(true)
    } catch (error) {
      console.error('Failed to load preview:', error)
      alert('加载预览失败')
    } finally {
      setLoading(false)
    }
  }

  // 处理删除
  const handleDelete = () => {
    if (confirm(`确定要删除数据集 "${dataset.name}" 吗？此操作不可撤销。`)) {
      onDelete?.(dataset.id)
    }
  }

  // 处理下载
  const handleDownload = async () => {
    try {
      const blob = await api.datasets.download(dataset.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = dataset.name
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to download dataset:', error)
      alert('下载失败')
    }
  }

  const isDuplicate = dataset.version_type === 'duplicate'

  return (
    <>
      <div className={`card p-6 mb-4 ${isDuplicate ? 'border-l-4 border-yellow-400' : ''}`}>
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-lg font-semibold text-gray-800">{dataset.name}</h3>
              {isDuplicate && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  🔗 重复
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500 mb-2">{formatDate(dataset.upload_time)}</p>
            {dataset.description && (
              <p className="text-sm text-gray-600 mb-2">{dataset.description}</p>
            )}
            
            {/* 标签 */}
            {dataset.tags && dataset.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-3">
                {dataset.tags.map((tag, index) => (
                  <span key={index} className="tag">
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 统计信息 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 p-4 bg-gray-50 rounded-lg">
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-800">{formatFileSize(dataset.file_size)}</div>
            <div className="text-xs text-gray-500">文件大小</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-800">
              {dataset.columns ? dataset.columns.length : '未分析'}
            </div>
            <div className="text-xs text-gray-500">列数</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold">{getQualityScore()}</div>
            <div className="text-xs text-gray-500">质量评估</div>
          </div>
          <div className="text-center">
            <div>{getStatusBadge(dataset.processing_status)}</div>
            <div className="text-xs text-gray-500">处理状态</div>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex flex-wrap gap-2 justify-between">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handlePreview}
              className="btn btn-info text-sm px-3 py-1"
              disabled={loading}
            >
              {loading ? '加载中...' : '数据预览'}
            </button>
            
            {dataset.processing_status === DatasetStatus.UPLOADED && (
              <button
                onClick={() => onStartBusinessAnalysis?.(dataset.id)}
                className="btn btn-success text-sm px-3 py-1"
              >
                启动业务分析
              </button>
            )}
            
            {dataset.processing_status === DatasetStatus.BUSINESS_COMPLETED && (
              <button
                onClick={() => onStartQualityAnalysis?.(dataset.id)}
                className="btn btn-success text-sm px-3 py-1"
              >
                启动质量分析
              </button>
            )}
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={handleDownload}
              className="btn btn-success text-sm px-3 py-1"
            >
              下载
            </button>
            <button
              onClick={handleDelete}
              className="btn btn-danger text-sm px-3 py-1"
            >
              删除
            </button>
          </div>
        </div>
      </div>

      {/* 预览模态框 */}
      {showPreview && previewData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl max-h-[80vh] overflow-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">数据预览 - {dataset.name}</h3>
                <button
                  onClick={() => setShowPreview(false)}
                  className="text-gray-500 hover:text-gray-700 text-xl"
                >
                  ×
                </button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse border border-gray-300">
                  <thead>
                    <tr className="bg-gray-50">
                      {previewData.columns.map((col: string, index: number) => (
                        <th key={index} className="border border-gray-300 px-4 py-2 text-left text-sm font-medium text-gray-700">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.data.map((row: any[], rowIndex: number) => (
                      <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        {row.map((cell: any, cellIndex: number) => (
                          <td key={cellIndex} className="border border-gray-300 px-4 py-2 text-sm text-gray-900">
                            {cell !== null ? String(cell) : ''}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="mt-4 text-sm text-gray-600">
                显示 {previewData.preview_rows} / {previewData.total_rows} 行数据
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default DatasetCard 