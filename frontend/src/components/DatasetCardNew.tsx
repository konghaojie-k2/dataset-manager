'use client'

import React, { useState, useEffect } from 'react'
import { DatasetMetadata, DatasetStatus } from '@/types/dataset'
import { formatFileSize, formatDate } from '@/lib/api'
import { api } from '@/lib/api'
import TagEditor from './TagEditor'

interface DatasetCardProps {
  dataset: DatasetMetadata
  onDelete?: (id: string) => void
  onStartBusinessAnalysis?: (id: string) => void
  onStartQualityAnalysis?: (id: string) => void
  onTagsUpdate?: (id: string, tags: string[]) => void
}

// 获取质量状态显示
const getQualityStatus = (dataset: DatasetMetadata): JSX.Element => {
  const status = dataset.processing_status || DatasetStatus.UPLOADED
  
  if (status === DatasetStatus.QUALITY_COMPLETED) {
    // 检查质量分析结果
    const qualityResults = dataset.quality_analysis_results
    if (qualityResults) {
      const score = Math.round(qualityResults.overall_score) || 100
      return <span className="quality-score">{score}分</span>
    } else {
      return <span className="status-completed">已完成</span>
    }
  } else if (status === DatasetStatus.QUALITY_ANALYZING) {
    return <span className="status-analyzing">分析中</span>
  } else {
    return <span className="status-not-started">未开始</span>
  }
}

// 获取业务理解状态显示
const getBusinessStatus = (dataset: DatasetMetadata): JSX.Element => {
  const status = dataset.processing_status || DatasetStatus.UPLOADED
  
  if (status === DatasetStatus.BUSINESS_COMPLETED || 
      status === DatasetStatus.QUALITY_ANALYZING || 
      status === DatasetStatus.QUALITY_COMPLETED) {
    return <span className="status-completed">已完成</span>
  } else if (status === DatasetStatus.BUSINESS_ANALYZING) {
    return <span className="status-analyzing">分析中</span>
  } else {
    return <span className="status-not-started">未开始</span>
  }
}

const DatasetCard: React.FC<DatasetCardProps> = ({
  dataset,
  onDelete,
  onStartBusinessAnalysis,
  onStartQualityAnalysis,
  onTagsUpdate,
}) => {
  const [loading, setLoading] = useState(false)
  const [isClient, setIsClient] = useState(false)
  const [showTagEditor, setShowTagEditor] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  // 处理标签更新
  const handleTagsUpdate = (newTags: string[]) => {
    onTagsUpdate?.(dataset.id, newTags)
  }

  // 处理数据预览
  const handlePreview = async () => {
    try {
      setLoading(true)
      const preview = await api.datasets.preview(dataset.id)
      
      if (preview && preview.data) {
        openPreviewWindow(preview)
      } else {
        alert('预览数据为空')
      }
    } catch (error) {
      console.error('预览数据集失败:', error)
      alert('预览失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  // 打开预览窗口
  const openPreviewWindow = (preview: any) => {
    const previewWindow = window.open('', '_blank', 'width=1000,height=700')
    if (previewWindow) {
      previewWindow.document.write(`
        <html>
        <head>
          <title>数据预览</title>
          <style>
            body { font-family: 'Microsoft YaHei', Arial, sans-serif; padding: 20px; background: #f8f9fa; }
            .container { max-width: 100%; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
            .header { border-bottom: 3px solid #667eea; padding-bottom: 15px; margin-bottom: 20px; }
            .title { font-size: 1.5em; color: #333; margin-bottom: 5px; }
            .subtitle { color: #666; }
            table { border-collapse: collapse; width: 100%; margin-top: 15px; font-size: 0.9em; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
            th { background-color: #667eea; color: white; font-weight: bold; }
            tr:nth-child(even) { background-color: #f8f9fa; }
            tr:hover { background-color: #e3f2fd; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="title">📊 数据预览</div>
              <div class="subtitle">显示前 ${preview.data.length} 行数据 (共 ${preview.shape ? preview.shape[0] : 0} 行 × ${preview.shape ? preview.shape[1] : 0} 列)</div>
            </div>
            <div style="overflow-x: auto;">
              <table>
                <thead>
                  <tr>${preview.columns ? preview.columns.map((col: string) => `<th title="${col}">${col}</th>`).join('') : ''}</tr>
                </thead>
                <tbody>
                  ${preview.data ? preview.data.map((row: any) => 
                    `<tr>${preview.columns.map((col: string) => `<td title="${row[col] || ''}">${row[col] || ''}</td>`).join('')}</tr>`
                  ).join('') : ''}
                </tbody>
              </table>
            </div>
          </div>
        </body>
        </html>
      `)
    }
  }

  // 处理下载
  const handleDownload = async () => {
    if (typeof window === 'undefined') return
    
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

  // 处理查看业务分析报告
  const handleViewBusinessReport = () => {
    if (typeof window === 'undefined') return
    const reportUrl = `/reports/business/${dataset.id}`
    window.open(reportUrl, '_blank')
  }

  // 处理查看质量分析报告
  const handleViewQualityReport = () => {
    if (typeof window === 'undefined') return
    const reportUrl = `/reports/quality/${dataset.id}`
    window.open(reportUrl, '_blank')
  }

  // 处理删除
  const handleDelete = async () => {
    if (!confirm('确定要删除这个数据集吗？此操作不可恢复。')) return
    
    try {
      await api.datasets.delete(dataset.id)
      onDelete?.(dataset.id)
      alert('数据集删除成功')
    } catch (error) {
      console.error('删除数据集失败:', error)
      alert('删除失败，请重试')
    }
  }

  // 生成操作按钮
  const generateActionButtons = () => {
    const status = dataset.processing_status || DatasetStatus.UPLOADED
    const buttons = []

    // 数据预览按钮 - 始终显示
    buttons.push(
      <button 
        key="preview"
        className="action-btn btn-primary" 
        onClick={handlePreview}
        disabled={loading}
      >
        {loading ? '加载中...' : '数据预览'}
      </button>
    )

    // 根据状态显示不同的分析按钮
    if (status === DatasetStatus.UPLOADED) {
      buttons.push(
        <button 
          key="business"
          className="action-btn btn-success" 
          onClick={() => onStartBusinessAnalysis?.(dataset.id)}
        >
          启动业务分析
        </button>
      )
    } else if (status === DatasetStatus.BUSINESS_ANALYZING) {
      buttons.push(
        <button key="business-analyzing" className="action-btn btn-secondary" disabled>
          业务分析中...
        </button>
      )
    } else if (status === DatasetStatus.BUSINESS_COMPLETED) {
      buttons.push(
        <button
          key="view-business"
          className="action-btn btn-info"
          onClick={handleViewBusinessReport}
        >
          查看业务分析
        </button>
      )
      buttons.push(
        <button
          key="quality"
          className="action-btn btn-success"
          onClick={() => onStartQualityAnalysis?.(dataset.id)}
        >
          启动质量分析
        </button>
      )
    } else if (status === DatasetStatus.QUALITY_ANALYZING) {
      buttons.push(
        <button
          key="view-business-2"
          className="action-btn btn-info"
          onClick={handleViewBusinessReport}
        >
          查看业务分析
        </button>
      )
      buttons.push(
        <button key="quality-analyzing" className="action-btn btn-secondary" disabled>
          质量分析中...
        </button>
      )
    } else if (status === DatasetStatus.QUALITY_COMPLETED) {
      buttons.push(
        <button
          key="view-business-3"
          className="action-btn btn-info"
          onClick={handleViewBusinessReport}
        >
          查看业务分析
        </button>
      )
      buttons.push(
        <button
          key="view-quality"
          className="action-btn btn-info"
          onClick={handleViewQualityReport}
        >
          查看质量分析
        </button>
      )
    }

    // 管理按钮
    buttons.push(
      <button key="download" className="action-btn btn-success" onClick={handleDownload}>
        下载
      </button>
    )
    buttons.push(
      <button key="delete" className="action-btn btn-danger" onClick={handleDelete}>
        删除
      </button>
    )

    return buttons
  }

  const isDuplicate = dataset.version_type === 'duplicate'

  return (
    <div className={`dataset-card ${isDuplicate ? 'duplicate-dataset' : ''}`}>
      <div className="dataset-main-info">
        {/* 数据集名称区域 */}
        <div className="dataset-name-section">
          <div className="dataset-name">
            {dataset.name}
            {isDuplicate && <span className="duplicate-badge" title="重复数据">🔗 重复</span>}
          </div>
          <div className="dataset-upload-time">
            {isClient ? formatDate(dataset.upload_time) : '加载中...'}
          </div>
          {dataset.description && (
            <div className="dataset-description" title={dataset.description}>
              {dataset.description}
            </div>
          )}
          {/* 标签区域 */}
          <div className="dataset-tags">
            <div className="tags-container">
              {dataset.tags && dataset.tags.length > 0 ? (
                dataset.tags.map((tag, index) => (
                  <span key={index} className="tag">{tag}</span>
                ))
              ) : (
                <span className="no-tags">暂无标签</span>
              )}
            </div>
            <button
              onClick={() => setShowTagEditor(true)}
              className="tag-edit-btn"
              title="编辑标签"
            >
              🏷️
            </button>
          </div>
        </div>

        {/* 统计信息区域 */}
        <div className="dataset-stats">
          {/* 文件大小 */}
          <div className="stat-item">
            <div className="stat-value">{formatFileSize(dataset.file_size)}</div>
            <div className="stat-label">文件大小</div>
          </div>

          {/* 列数 */}
          <div className="stat-item">
            <div className="stat-value">{dataset.columns?.length || '未分析'}</div>
            <div className="stat-label">列数</div>
          </div>

          {/* 质量评估 */}
          <div className="stat-item">
            <div className="stat-status">{getQualityStatus(dataset)}</div>
            <div className="stat-label">质量评估</div>
          </div>

          {/* 业务理解 */}
          <div className="stat-item">
            <div className="stat-status">{getBusinessStatus(dataset)}</div>
            <div className="stat-label">业务理解</div>
          </div>
        </div>
      </div>

      {/* 操作按钮区域 */}
      <div className="dataset-actions">
        <div className="action-group function-group">
          {generateActionButtons().slice(0, -2)}
        </div>
        <div className="action-group manage-group">
          {generateActionButtons().slice(-2)}
        </div>
      </div>

      {/* 标签编辑器 */}
      <TagEditor
        datasetId={dataset.id}
        datasetName={dataset.name}
        currentTags={dataset.tags || []}
        isOpen={showTagEditor}
        onClose={() => setShowTagEditor(false)}
        onSave={handleTagsUpdate}
      />
    </div>
  )
}

export default DatasetCard
