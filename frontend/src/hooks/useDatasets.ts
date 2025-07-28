'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
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
  const pollingInterval = useRef<NodeJS.Timeout | null>(null)
  const lastFetchTime = useRef<number>(0)

  // 检查是否有正在分析的数据集
  const hasAnalyzing = useCallback((datasets: DatasetMetadata[]) => {
    return datasets.some(dataset => 
      dataset.processing_status === 'business_analyzing' || 
      dataset.processing_status === 'quality_analyzing'
    )
  }, [])

  // 获取数据集列表
  const fetchDatasets = useCallback(async (skipLoadingState = false) => {
    try {
      if (!skipLoadingState) {
        setLoading(true)
      }
      setError(null)
      
      // 防止频繁请求
      const now = Date.now()
      if (now - lastFetchTime.current < 1000) {
        return
      }
      lastFetchTime.current = now
      
      const data = await api.datasets.list()
      setDatasets(data)
      
      // 如果有正在分析的任务，启动轮询
      if (hasAnalyzing(data)) {
        startPolling()
      } else {
        stopPolling()
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '获取数据集列表失败'
      setError(errorMessage)
      console.error('Failed to fetch datasets:', err)
    } finally {
      if (!skipLoadingState) {
        setLoading(false)
      }
    }
  }, [hasAnalyzing])

  // 启动轮询
  const startPolling = useCallback(() => {
    if (pollingInterval.current) return // 避免重复启动
    
    console.log('开始轮询数据集状态...')
    pollingInterval.current = setInterval(() => {
      fetchDatasets(true) // 轮询时不显示loading状态
    }, 3000) // 每3秒检查一次
  }, [fetchDatasets])

  // 停止轮询
  const stopPolling = useCallback(() => {
    if (pollingInterval.current) {
      console.log('停止轮询数据集状态')
      clearInterval(pollingInterval.current)
      pollingInterval.current = null
    }
  }, [])

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
      // 立即更新本地状态
      setDatasets(prev => prev.map(dataset => 
        dataset.id === id 
          ? { ...dataset, processing_status: 'business_analyzing' as any }
          : dataset
      ))
      // 启动轮询监控状态变化
      startPolling()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '启动业务分析失败'
      setError(errorMessage)
      throw err
    }
  }, [startPolling])

  // 启动质量分析
  const startQualityAnalysis = useCallback(async (id: string) => {
    try {
      await api.datasets.startQualityAnalysis(id)
      // 立即更新本地状态
      setDatasets(prev => prev.map(dataset => 
        dataset.id === id 
          ? { ...dataset, processing_status: 'quality_analyzing' as any }
          : dataset
      ))
      // 启动轮询监控状态变化
      startPolling()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '启动质量分析失败'
      setError(errorMessage)
      throw err
    }
  }, [startPolling])

  // 初始化数据
  useEffect(() => {
    fetchDatasets()
  }, []) // 移除fetchDatasets依赖，只在组件挂载时执行一次

  // 页面可见性变化监听
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        // 页面重新可见时，重置错误状态并刷新数据
        setError(null)
        fetchDatasets(true)
      } else {
        // 页面隐藏时停止轮询
        stopPolling()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [fetchDatasets, stopPolling])

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      stopPolling()
    }
  }, [stopPolling])

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