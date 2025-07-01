'use client'

import { useState, useEffect, useCallback } from 'react'
import { DatasetMetadata } from '@/types/dataset'
import { api } from '@/lib/api'

export interface UseDatasets {
  datasets: DatasetMetadata[]
  loading: boolean
  error: string | null
  refreshDatasets: () => Promise<void>
  deleteDataset: (id: string) => Promise<void>
  startBusinessAnalysis: (id: string) => Promise<void>
  startQualityAnalysis: (id: string) => Promise<void>
}

export const useDatasets = (): UseDatasets => {
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 获取数据集列表
  const fetchDatasets = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.datasets.list()
      setDatasets(data)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '获取数据集列表失败'
      setError(errorMessage)
      console.error('Failed to fetch datasets:', err)
    } finally {
      setLoading(false)
    }
  }, []) // 移除依赖，避免无限循环

  // 刷新数据集列表
  const refreshDatasets = useCallback(async () => {
    await fetchDatasets()
  }, [fetchDatasets])

  // 删除数据集
  const deleteDataset = useCallback(async (id: string) => {
    try {
      await api.datasets.delete(id)
      // 从本地状态中移除已删除的数据集
      setDatasets(prev => prev.filter(dataset => dataset.id !== id))
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '删除数据集失败'
      setError(errorMessage)
      throw err
    }
  }, [])

  // 启动业务分析
  const startBusinessAnalysis = useCallback(async (id: string) => {
    try {
      await api.datasets.startBusinessAnalysis(id)
      // 更新本地状态
      setDatasets(prev => prev.map(dataset => 
        dataset.id === id 
          ? { ...dataset, processing_status: 'business_analyzing' as any }
          : dataset
      ))
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '启动业务分析失败'
      setError(errorMessage)
      throw err
    }
  }, [])

  // 启动质量分析
  const startQualityAnalysis = useCallback(async (id: string) => {
    try {
      await api.datasets.startQualityAnalysis(id)
      // 更新本地状态
      setDatasets(prev => prev.map(dataset => 
        dataset.id === id 
          ? { ...dataset, processing_status: 'quality_analyzing' as any }
          : dataset
      ))
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '启动质量分析失败'
      setError(errorMessage)
      throw err
    }
  }, [])

  // 初始化数据
  useEffect(() => {
    fetchDatasets()
  }, []) // 移除fetchDatasets依赖，只在组件挂载时执行一次

  // 添加页面可见性变化监听，处理重新加载情况
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        // 页面重新可见时，重置错误状态
        setError(null)
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  return {
    datasets,
    loading,
    error,
    refreshDatasets,
    deleteDataset,
    startBusinessAnalysis,
    startQualityAnalysis,
  }
} 