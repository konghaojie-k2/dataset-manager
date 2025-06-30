'use client'

import React, { useState } from 'react'
import { useDatasets } from '@/hooks/useDatasets'
import DatasetCard from './DatasetCard'

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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="loading-spinner mr-3"></div>
        <span className="text-gray-600">正在加载数据集...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <div className="text-red-600 mb-4">❌ 加载失败</div>
        <p className="text-red-700 mb-4">{error}</p>
        <button
          onClick={refreshDatasets}
          className="btn btn-primary"
        >
          重新加载
        </button>
      </div>
    )
  }

  return (
    <section className="py-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center">
          <span className="mr-2">📚</span>
          数据集管理
        </h2>
        
        {/* 页面大小选择器 */}
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
      </div>

      {/* 数据集列表 */}
      {datasets.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl text-gray-400 mb-4">📁</div>
          <p className="text-gray-500 text-lg">暂无数据集，请上传第一个数据集</p>
        </div>
      ) : (
        <>
          {/* 数据集卡片 */}
          <div className="space-y-4">
            {currentDatasets.map((dataset) => (
              <DatasetCard
                key={dataset.id}
                dataset={dataset}
                onDelete={handleDelete}
                onStartBusinessAnalysis={handleStartBusinessAnalysis}
                onStartQualityAnalysis={handleStartQualityAnalysis}
              />
            ))}
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