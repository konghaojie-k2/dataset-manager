'use client'

import { useState, useCallback } from 'react'
import { api } from '@/lib/api'

export interface UseFileUpload {
  uploading: boolean
  progress: number
  error: string | null
  uploadFile: (file: File, userInput?: string) => Promise<string | null>
  resetUpload: () => void
}

export const useFileUpload = (): UseFileUpload => {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  // 上传文件
  const uploadFile = useCallback(async (file: File, userInput?: string): Promise<string | null> => {
    try {
      setUploading(true)
      setProgress(0)
      setError(null)

      // 验证文件类型
      const allowedTypes = ['.csv', '.zip']
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
      
      if (!allowedTypes.includes(fileExtension)) {
        throw new Error('只支持CSV和ZIP格式的文件')
      }

      // 验证文件大小 (100MB)
      const maxSize = 100 * 1024 * 1024
      if (file.size > maxSize) {
        throw new Error('文件大小不能超过100MB')
      }

      // 模拟上传进度
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      // 调用API上传文件
      const response = await api.datasets.upload(file, userInput)
      
      clearInterval(progressInterval)
      setProgress(100)

      if (response.success) {
        return (response as any).dataset_id || null
      } else {
        throw new Error(response.message || '上传失败')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '文件上传失败'
      setError(errorMessage)
      console.error('File upload failed:', err)
      return null
    } finally {
      setUploading(false)
    }
  }, [])

  // 重置上传状态
  const resetUpload = useCallback(() => {
    setUploading(false)
    setProgress(0)
    setError(null)
  }, [])

  return {
    uploading,
    progress,
    error,
    uploadFile,
    resetUpload,
  }
} 