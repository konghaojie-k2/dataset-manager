'use client'

import React, { useMemo } from 'react'
import { useDatasets } from '@/hooks/useDatasets'
import DatasetCardCompact from './DatasetCardCompact'
import LoadingSpinner from './LoadingSpinner'
import { useDataManager } from './DataManagerLayout'
import { FiFolder, FiSearch } from 'react-icons/fi'

const EnhancedDatasetList: React.FC = () => {
  const { viewMode, searchQuery, filters } = useDataManager()
  const {
    datasets,
    loading,
    error,
    refreshDatasets,
    deleteDataset,
  } = useDatasets()

  // 筛选和搜索逻辑
  const filteredDatasets = useMemo(() => {
    let filtered = [...datasets]

    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(dataset =>
        dataset.name.toLowerCase().includes(query) ||
        dataset.description?.toLowerCase().includes(query) ||
        dataset.tags?.some(tag => tag.toLowerCase().includes(query))
      )
    }

    // 标签过滤
    if (filters.tags && filters.tags.length > 0) {
      filtered = filtered.filter(dataset =>
        dataset.tags?.some(tag => filters.tags!.includes(tag))
      )
    }

    // 质量评分过滤
    if (filters.qualityScore) {
      filtered = filtered.filter(dataset => {
        if (!dataset.quality_score) return false
        if (filters.qualityScore === 'high') return dataset.quality_score >= 80
        if (filters.qualityScore === 'medium') return dataset.quality_score >= 60 && dataset.quality_score < 80
        if (filters.qualityScore === 'low') return dataset.quality_score < 60
        return true
      })
    }

    // 时间过滤
    if (filters.dateRange) {
      const now = new Date()
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())

      filtered = filtered.filter(dataset => {
        const uploadDate = new Date(dataset.upload_time)
        if (filters.dateRange === 'today') {
          return uploadDate >= today
        }
        if (filters.dateRange === 'week') {
          const weekAgo = new Date(today)
          weekAgo.setDate(weekAgo.getDate() - 7)
          return uploadDate >= weekAgo
        }
        if (filters.dateRange === 'month') {
          const monthAgo = new Date(today)
          monthAgo.setMonth(monthAgo.getMonth() - 1)
          return uploadDate >= monthAgo
        }
        return true
      })
    }

    return filtered
  }, [datasets, searchQuery, filters])

  const handleDelete = async (id: string) => {
    try {
      await deleteDataset(id)
    } catch (error) {
      console.error('Delete failed:', error)
    }
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-12 text-center">
        <FiSearch className="w-16 h-16 text-red-400 mx-auto mb-4" />
        <div className="text-red-600 text-lg font-semibold mb-2">加载失败</div>
        <p className="text-red-700 mb-6">{error}</p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={refreshDatasets}
            disabled={loading}
            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '重试中...' : '重新加载'}
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            刷新页面
          </button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <LoadingSpinner />
        <p className="mt-4 text-gray-600">加载数据集中...</p>
      </div>
    )
  }

  if (datasets.length === 0) {
    return (
      <div className="bg-white rounded-xl border-2 border-dashed border-gray-300 p-16 text-center">
        <FiFolder className="w-20 h-20 text-gray-300 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-700 mb-2">暂无数据集</h3>
        <p className="text-gray-500 mb-6">上传您的第一个数据集开始使用</p>
      </div>
    )
  }

  if (filteredDatasets.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-16 text-center">
        <FiSearch className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-700 mb-2">未找到匹配的数据集</h3>
        <p className="text-gray-500 mb-6">尝试调整搜索词或筛选条件</p>
      </div>
    )
  }

  return (
    <div>
      {/* 结果统计 */}
      <div className="mb-6 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          找到 <span className="font-semibold text-gray-900">{filteredDatasets.length}</span> 个数据集
          {searchQuery || filters.tags?.length || filters.qualityScore ? (
            <span className="ml-2 text-gray-500">
              (从 {datasets.length} 个中筛选)
            </span>
          ) : ''}
        </div>
      </div>

      {/* 数据集网格/列表 */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredDatasets.map((dataset) => (
            <DatasetCardCompact
              key={dataset.id}
              dataset={dataset}
              onDelete={handleDelete}
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredDatasets.map((dataset) => (
            <DatasetCardCompact
              key={dataset.id}
              dataset={dataset}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default EnhancedDatasetList
