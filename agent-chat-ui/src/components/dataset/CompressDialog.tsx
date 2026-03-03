#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CompressDialog - 文件压缩对话框
* 选择压缩方法，显示压缩进度
"""

import React, { useState, useCallback } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter }
  from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { datasetAPI, type Dataset } from '@/lib/api-extension'

interface CompressDialogProps {
  dataset: Dataset
  open: boolean
  onOpenChange: (open: boolean) => void
  onCompressSuccess: (datasetId: string) => void
}

type CompressionMethod = 'gzip' | 'bzip2' | 'xz'

export function CompressDialog({ dataset, open, onOpenChange, onCompressSuccess }: CompressDialogProps) {
  const [compressing, setCompressing] = useState(false)
  const [method, setMethod] = useState<CompressionMethod>('gzip')
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<{
    success: boolean
    message: string
    original_size_mb: number
    compressed_size_mb: number
    compression_ratio: number
  } | null>(null)

  const compressionMethods = [
    { value: 'gzip' as CompressionMethod, label: 'Gzip', description: '速度快，兼容性最好' },
    { value: 'bzip2' as CompressionMethod, label: 'Bzip2', description: '压缩率中等' },
    { value: 'xz' as CompressionMethod, label: 'XZ', description: '压缩率最高' },
  ]

  const handleCompress = useCallback(async () => {
    setCompressing(true)
    setProgress(0)
    setResult(null)

    try {
      // 注意：这里目前还没有后端 API，先使用模拟数据
      // TODO: 等待后端实现 /api/v1/datasets/{id}/compress 端点
      
      // 模拟压缩过程
      const simulateProgress = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 95) {
            clearInterval(simulateProgress)
            return 95
          }
          return prev + 5
        })
      }, 100)

      // 模拟 2 秒后完成
      setTimeout(() => {
        clearInterval(simulateProgress)
        
        const originalSize = dataset.file_size / 1024 / 1024
        
        const compressionRatios = {
          gzip: 0.45,
          bzip2: 0.6,
          xz: 0.3,
        }
        const ratio = compressionRatios[method] || 0.45
        const compressedSize = originalSize * ratio
        
        setResult({
          success: true,
          message: '文件压缩成功',
          original_size_mb: Number(originalSize.toFixed(2)),
          compressed_size_mb: Number(compressedSize.toFixed(2)),
          compression_ratio: Number(((1 - ratio) * 100).toFixed(1)),
        })

        setProgress(100)

        // 通知父组件
        setTimeout(() => {
          if (result.success) {
            // TODO: 实际调用 API 后刷新数据集卡片
            onCompressSuccess?.(dataset.id)
          }
          setCompressing(false)
          setTimeout(() => {
            onOpenChange(false)
          }, 1500)
        }, 500)
      }, 2000)
    } catch (error: any) {
      console.error('Compress failed:', error)
      setResult({
        success: false,
        message: `压缩失败: ${error.message || '未知错误'}`,
        original_size_mb: 0,
        compressed_size_mb: 0,
        compression_ratio: 0
      })
      setCompressing(false)
    }
  }, [dataset.id, method, onCompressSuccess])

  const handleClose = useCallback(() => {
    if (!compressing) {
      onOpenChange(false)
    }
  }, [compressing, onOpenChange])

  // 估算压缩后文件大小（基于压缩率）
  const estimateSize = (originalSizeMb: number, compressionMethod: CompressionMethod): string => {
    const ratios = {
      gzip: 0.45,
      bzip2: 0.6,
      xz: 0.3,
    }
    const ratio = ratios[compressionMethod] || 0.45
    const estimatedSize = (originalSizeMb * ratio).toFixed(2)
    return `${estimatedSize} MB`
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>压缩数据集</DialogTitle>
          <DialogDescription>
            选择压缩方法并开始压缩
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* 压缩方法选择 */}
          <div>
            <label className="text-sm font-medium mb-3">选择压缩方法</label>
            <div className="space-y-2">
              {compressionMethods.map((option) => (
                <div
                  key={option.value}
                  className={`
                    flex items-center space-x-3 p-3 rounded-lg border
                    ${method === option.value
                      ? 'border-[#1a1a1a] bg-[#f0f9ff] ring-2 ring-offset-2 ring-[#1a1a1a]/20'
                      : 'border-[#e8e4df] hover:border-[#d1d5db] cursor-pointer transition-colors'
                    }
                  `}
                  onClick={() => !compressing && setMethod(option.value)}
                >
                  <RadioGroupItem
                    value={option.value}
                    disabled={compressing}
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
                <span className="text-gray-600">预估压缩后大小</span>
                <span className="font-medium text-[#1a1a1a]">
                  {estimateSize(
                    dataset.file_size ? dataset.file_size / 1024 / 1024 : 0,
                    method
                  )}
                </span>
              </div>
              <div className="text-xs text-gray-500">
                * 压缩后的文件将占用更少的存储空间
              </div>
            </div>
          </div>

          {/* 进度显示 */}
          {compressing && (
            <div className="space-y-4">
              <div className="text-center">
                <div className="inline-flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-[#c75b39] border-t-transparent border-r-transparent">
                    <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12v8a4 4 0 008 0 012a4 4 0 008 0zm0 6a4 4 0 004 4 4 0 008zm0 0a4 4 0 012 4 4 0 008zm0 12a4 4 0 012 4 4 0 008zm0 12a4 4 0 012 4 4 0 008zm0 0a4 4 0 012 4 4 0 008z"
                      />
                    </svg>
                  </div>
                  <span className="text-sm font-medium text-[#1a1a1a]">
                    压缩中... {progress}%
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
          {result && !compressing && (
            <div className={`space-y-4 ${result.success ? 'text-center' : 'text-center'}`}>
              <div
                className={`text-2xl font-semibold mb-2 ${
                  result.success ? 'text-[#10b981]' : 'text-red-600'
                }`}
                style={{ fontFamily: 'var(--font-playfair)' }}
              >
                {result.success ? '✓ 压缩成功！' : '✗ 压缩失败'}
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
                    文件已压缩完成
                  </div>
                  <div className="text-sm text-gray-600">
                    原文件大小: <span className="font-medium">{result.original_size_mb} MB</span>
                  </div>
                  <div className="text-sm text-gray-600">
                    压缩后大小: <span className="font-medium">{result.compressed_size_mb} MB</span>
                  </div>
                  <div className="text-sm text-gray-600">
                    节省空间: <span className="font-medium text-green-600">{result.compression_ratio}%</span>
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
            disabled={compressing}
          >
            {compressing ? '压缩中...' : '取消'}
          </Button>
          <Button
            onClick={handleCompress}
            disabled={compressing}
            className="bg-[#1a1a1a] hover:bg-[#c75b39] text-white"
          >
            {compressing ? '压缩中...' : '开始压缩'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}