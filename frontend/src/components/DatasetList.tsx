'use client'

import React, { useState, useEffect } from 'react'
import { useDatasets } from '@/hooks/useDatasets'
import DatasetCard from './DatasetCardNew'
import LoadingSpinner from './LoadingSpinner'
import '../styles/dataset-card.css'

const DatasetList: React.FC = () => {
  const {
    datasets,
    loading,
    error,
    refreshDatasets,
    deleteDataset,
    startBusinessAnalysis,
    startQualityAnalysis,
  } = useDatasets()

  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  // 处理页面重新加载时的状态重置
  useEffect(() => {
    // 如果有错误且不在加载中，尝试重新获取数据
    if (error && !loading) {
      const timer = setTimeout(() => {
        console.log('检测到错误，尝试重新获取数据...')
        refreshDatasets()
      }, 1000) // 延迟1秒重试

      return () => clearTimeout(timer)
    }
  }, [error, loading, refreshDatasets])

  // 分页计算
  const totalPages = Math.ceil(datasets.length / pageSize)
  const startIndex = (currentPage - 1) * pageSize
  const endIndex = startIndex + pageSize
  const currentDatasets = datasets.slice(startIndex, endIndex)

  // 处理页面变化
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  // 处理页面大小变化
  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize)
    setCurrentPage(1) // 重置到第一页
  }

  // 处理删除
  const handleDelete = async (id: string) => {
    try {
      await deleteDataset(id)
      // 如果当前页没有数据了，回到上一页
      if (currentDatasets.length === 1 && currentPage > 1) {
        setCurrentPage(currentPage - 1)
      }
    } catch (error) {
      console.error('Delete failed:', error)
    }
  }

  // 处理业务分析
  const handleStartBusinessAnalysis = async (id: string) => {
    try {
      await startBusinessAnalysis(id)
    } catch (error) {
      console.error('Start business analysis failed:', error)
    }
  }

  // 处理质量分析
  const handleStartQualityAnalysis = async (id: string) => {
    try {
      await startQualityAnalysis(id)
    } catch (error) {
      console.error('Start quality analysis failed:', error)
    }
  }

  // 处理标签更新
  const handleTagsUpdate = async (id: string, tags: string[]) => {
    try {
      // 刷新数据集列表以获取最新的标签信息
      await refreshDatasets()
    } catch (error) {
      console.error('Refresh datasets after tag update failed:', error)
    }
  }

  // 计算正在分析的任务数量
  const analyzingCount = datasets.filter(dataset => 
    dataset.processing_status === 'business_analyzing' || 
    dataset.processing_status === 'quality_analyzing'
  ).length

  // 检查是否有错误并提供详细信息
  const hasAnalyzeError = datasets.some(dataset => 
    dataset.processing_status === 'analysis_failed'
  )

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <div className="text-red-600 mb-4">❌ 加载失败</div>
        <p className="text-red-700 mb-4">{error}</p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={refreshDatasets}
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '重新加载中...' : '重新加载'}
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
          >
            刷新页面
          </button>
        </div>
      </div>
    )
  }

  return (
    <section className="py-8" suppressHydrationWarning>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center">
          <span className="mr-2">📚</span>
          数据集管理
        </h2>
        
        {/* 只有在加载完成后才显示分页大小选择器 */}
        {!loading && datasets.length > 0 && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600">每页显示：</span>
            <select
              value={pageSize}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value={5}>5条</option>
              <option value={10}>10条</option>
              <option value={20}>20条</option>
              <option value={50}>50条</option>
            </select>
          </div>
        )}
      </div>

      {/* 状态指示器 */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <span className="text-gray-600">数据集总数:</span>
              <span className="ml-2 font-semibold text-gray-800">{datasets.length}</span>
            </div>
            
            {analyzingCount > 0 && (
              <div className="flex items-center">
                <div className="flex items-center text-blue-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-2"></div>
                  <span>正在分析:</span>
                  <span className="ml-1 font-semibold">{analyzingCount}</span>
                  <span className="ml-1">个任务</span>
                </div>
              </div>
            )}

            {hasAnalyzeError && (
              <div className="flex items-center text-red-600">
                <span className="mr-1">⚠️</span>
                <span>有分析任务失败</span>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-3">
            {analyzingCount > 0 && (
              <div className="text-xs text-blue-500 bg-blue-50 px-2 py-1 rounded-full">
                自动刷新中...
              </div>
            )}
            
            <button
              onClick={refreshDatasets}
              disabled={loading}
              className="flex items-center px-3 py-1 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-2"></div>
                  刷新中...
                </>
              ) : (
                <>
                  <span className="mr-1">🔄</span>
                  刷新
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 数据集列表 */}
      {loading ? (
        <LoadingSpinner />
      ) : datasets.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl text-gray-400 mb-4">📁</div>
          <p className="text-gray-500 text-lg">暂无数据集，请上传第一个数据集</p>
        </div>
      ) : (
        <>
          {/* 数据集列表 */}
          <div className="datasets-container">
            {/* 列表头部 */}
            <div className="datasets-header">
              <div className="header-main-info">
                <div className="header-name-section">数据集名称</div>
                <div className="header-stats">
                  <div className="header-stat-item">文件大小</div>
                  <div className="header-stat-item">列数</div>
                  <div className="header-stat-item">质量评估</div>
                  <div className="header-stat-item">业务理解</div>
                </div>
              </div>
              <div className="header-actions">操作</div>
            </div>

            {/* 数据集卡片列表 */}
            <div className="datasets-list">
              {currentDatasets.map((dataset) => (
                <DatasetCard
                  key={dataset.id}
                  dataset={dataset}
                  onDelete={handleDelete}
                  onStartBusinessAnalysis={handleStartBusinessAnalysis}
                  onStartQualityAnalysis={handleStartQualityAnalysis}
                  onTagsUpdate={handleTagsUpdate}
                />
              ))}
            </div>
          </div>

          {/* 分页控件 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-8 p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600">
                显示 {startIndex + 1} - {Math.min(endIndex, datasets.length)} 条，共 {datasets.length} 条数据集
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="btn btn-secondary text-sm px-3 py-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  上一页
                </button>
                
                {/* 页码 */}
                <div className="flex gap-1">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                    // 只显示当前页附近的页码
                    if (
                      page === 1 ||
                      page === totalPages ||
                      (page >= currentPage - 2 && page <= currentPage + 2)
                    ) {
                      return (
                        <button
                          key={page}
                          onClick={() => handlePageChange(page)}
                          className={`px-3 py-1 text-sm rounded ${
                            page === currentPage
                              ? 'bg-primary-500 text-white'
                              : 'bg-white text-gray-700 hover:bg-gray-100'
                          }`}
                        >
                          {page}
                        </button>
                      )
                    } else if (
                      page === currentPage - 3 ||
                      page === currentPage + 3
                    ) {
                      return (
                        <span key={page} className="px-2 py-1 text-sm text-gray-400">
                          ...
                        </span>
                      )
                    }
                    return null
                  })}
                </div>
                
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="btn btn-secondary text-sm px-3 py-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </section>
  )
}

export default DatasetList 