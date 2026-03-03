#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ConvertDialog - Parquet 转换对话框
* 选择压缩算法，显示转换进度
"""

import React, { useState, useCallback } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter }
  from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { datasetAPI, type Dataset } from '@/lib/api-extension'

interface ConvertDialogProps {
  dataset: Dataset
  open: boolean
  onOpenChange: (open: boolean) => void
  onConvertSuccess: (datasetId: string) => void
}

type CompressionType = 'snappy' | 'gzip' | 'brotli' | 'lz4'

export function ConvertDialog({ dataset, open, onOpenChange, onConvertSuccess }: ConvertDialogProps) {
  const [converting, setConverting] = useState(false)
  const [compression, setCompression] = useState<CompressionType>('snappy')
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<{
    success: boolean
    message: string
    original_size_mb: number
    compressed_size_mb: number
    compression_ratio: number
  } | null>(null)

  const compressionOptions = [
    { value: 'snappy' as CompressionType, label: 'Snappy', description: '压缩速度最快，适合实时处理' },
    { value: 'gzip' as CompressionType, label: 'Gzip', description: '压缩率中等，兼容性最好' },
    { value: 'brotli' as CompressionType, label: 'Brotli', description: '压缩率较高，但速度较慢' },
    { value: 'lz4' as CompressionType, label: 'LZ4', description: '压缩率最高，但压缩时间较长' },
  ]

  const handleConvert = useCallback(async () => {
    setConverting(true)
    setProgress(0)
    setResult(null)

    try {
      const response = await datasetAPI.convertToParquet(dataset.id, compression)
      setResult(response)
      setProgress(100)

      // 通知父组件
      setTimeout(() => {
        if (response.success && response.dataset_id) {
          onConvertSuccess?.(response.dataset_id)
        }
        setConverting(false)
        // 延迟关闭对话框
        setTimeout(() => {
          onOpenChange(false)
        }, 1500)
      }, 500)
    } catch (error: any) {
      console.error('Convert failed:', error)
      setResult({
        success: false,
        message: `转换失败: ${error.message || '未知错误'}`,
        original_size_mb: 0,
        compressed_size_mb: 0,
        compression_ratio: 0
      })
      setConverting(false)
    }
  }, [dataset.id, compression, onConvertSuccess])

  const handleClose = useCallback(() => {
    if (!converting) {
      onOpenChange(false)
    }
    }, [converting, onOpenChange])

  // 估算转换后文件大小（基于压缩率）
  const estimateSize = (originalSizeMb: number, compressionType: CompressionType): string => {
    const ratios = {
      snappy: 0.6,
      gzip: 0.5,
      brotli: 0.45,
      lz4: 0.4,
    }
    const ratio = ratios[compressionType] || 0.6
    const estimatedSize = (originalSizeMb * ratio).toFixed(2)
    return `${estimatedSize} MB`
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>转换为 Parquet 格式</DialogTitle>
          <DialogDescription>
            选择压缩算法并开始转换
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* 压缩算法选择 */}
          <div>
            <label className="text-sm font-medium mb-3">选择压缩算法</label>
            <div className="space-y-2">
              {compressionOptions.map((option) => (
                <div
                  key={option.value}
                  className={`
                    flex items-center space-x-3 p-3 rounded-lg border
                    ${compression === option.value
                      ? 'border-[#1a1a1a] bg-[#f0f9ff] ring-2 ring-offset-2 ring-[#1a1a1a]/20'
                      : 'border-[#e8e4df] hover:border-[#d1d5db] cursor-pointer transition-colors'
                    }
                  `}
                  onClick={() => !converting && setCompression(option.value)}
                >
                  <RadioGroupItem
                    value={option.value}
                    disabled={converting}
                    className="cursor-pointer"
                  >
                    {option.label}
                  </RadioGroupItem>
                  <div className="ml-4 flex-1">
                    <div className="text-sm font-medium text-[#1a1a1a]">{option.label}</div>
                    <div className="text-xs text-gray-500">{option.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 压缩信息显示 */}
          <div className="bg-[#f8fafc] rounded-lg p-4 border border-[#e8e4df]">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">原文件大小</span>
                <span className="font-medium text-[#1a1a1a]">
                  {dataset.file_size
                    ? `${(dataset.file_size / 1024 / 1024).toFixed(2)} MB`
                    : '-'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">预估转换后大小</span>
                <span className="font-medium text-[#1a1a1a]">
                  {estimateSize(
                    dataset.file_size ? dataset.file_size / 1024 / 1024 : 0,
                    compression
                  )}
                </span>
              </div>
              <div className="text-xs text-gray-500">
                * 压缩后的文件将用于更快速的数据加载和分析
              </div>
            </div>
          </div>

          {/* 进度显示 */}
          {converting && (
            <div className="space-y-4">
              <div className="text-center">
                <div className="inline-flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-[#c75b39] border-t-transparent border-r-transparent">
                    <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12v8a4 4 0 008 0 012a4 4 0 008 0 0zm0 6a4 4 0 004 4 4 0 008zm0 0a4 4 0 012 4 4 0 012zm0-12a4 4 0 012 4 0 008 0zm4 4 4 0 004-4 4 4zm0 0a4 4 0 012 4 4 0 012zm-12 0a4 4 0 012 4 4 0 008zm0 12a4 4 0 012 4 4 0 008zm0 12a4 4 0 012 4 4 0 008z"
                      />
                    </svg>
                  </div>
                  <span className="text-sm font-medium text-[#1a1a1a]">
                    转换中... {progress}%
                  </span>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-[#1a1a1a] to-[#c75b39] h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* 结果显示 */}
          {result && !converting && (
            <div className={`space-y-4 ${result.success ? 'text-center' : 'text-center'}`}>
              <div
                className={`text-2xl font-semibold mb-2 ${
                  result.success ? 'text-[#10b981]' : 'text-red-600'
                }`}
                style={{ fontFamily: 'var(--font-playfair)' }}
              >
                {result.success ? '✓ 转换成功！' : '✗ 转换失败'}
              </div>
              <div
                className={`text-sm ${
                  result.success ? 'text-gray-700' : 'text-gray-600'
                }`}
              >
                {result.message}
              </div>
              {result.success && (
                <div className="space-y-2 bg-[#f0fdf4] rounded-lg p-4 text-left">
                  <div className="text-sm text-gray-600">
                    Parquet 文件已生成
                  </div>
                  <div className="text-sm text-gray-600">
                    原文件大小: <span className="font-medium">{result.original_size_mb} MB</span>
                  </div>
                  <div className="text-sm text-gray-600">
                    转换后大小: <span className="font-medium">{result.compressed_size_mb} MB</span>
                  </div>
                  <div className="text-sm text-gray-600">
                    压缩率: <span className="font-medium text-green-600">{result.compression_ratio}%</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={converting}
          >
            {converting ? '转换中...' : '取消'}
          </Button>
          <Button
            onClick={handleConvert}
            disabled={converting}
            className="bg-[#1a1a1a] hover:bg-[#c75b39] text-white"
          >
            {converting ? '转换中...' : '开始转换'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}