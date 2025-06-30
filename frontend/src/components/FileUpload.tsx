'use client'

import React, { useState, useRef, DragEvent, ChangeEvent } from 'react'
import { useFileUpload } from '@/hooks/useFileUpload'

interface FileUploadProps {
  onUploadSuccess?: (datasetId: string) => void
  onUploadError?: (error: string) => void
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess, onUploadError }) => {
  const [isDragOver, setIsDragOver] = useState(false)
  const [userInput, setUserInput] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const { uploading, progress, error, uploadFile, resetUpload } = useFileUpload()

  // 处理文件选择
  const handleFileSelect = async (file: File) => {
    if (!file) return

    try {
      const datasetId = await uploadFile(file, userInput)
      if (datasetId) {
        onUploadSuccess?.(datasetId)
        setUserInput('')
        // 清空文件输入
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '上传失败'
      onUploadError?.(errorMessage)
    }
  }

  // 拖拽处理
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  // 文件输入变化处理
  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  // 点击选择文件
  const handleSelectClick = () => {
    fileInputRef.current?.click()
  }

  // 重置错误状态
  const handleReset = () => {
    resetUpload()
    setUserInput('')
  }

  return (
    <section className="bg-gray-50 rounded-xl p-8 mb-8 border-2 border-dashed border-gray-300 transition-all duration-300 hover:border-primary-500 hover:bg-primary-50">
      <div
        className={`text-center transition-all duration-300 ${
          isDragOver ? 'scale-105 bg-primary-100 rounded-lg p-4' : ''
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* 上传图标 */}
        <div className="text-6xl text-primary-500 mb-4">
          {uploading ? '⏳' : '📁'}
        </div>

        <h3 className="text-2xl font-semibold text-gray-800 mb-2">上传数据文件</h3>
        <p className="text-gray-600 mb-6">
          支持CSV、ZIP格式文件，拖拽文件到此处或点击选择文件
        </p>

        {/* 文件输入 */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.zip"
          onChange={handleInputChange}
          className="hidden"
          disabled={uploading}
        />

        {/* 上传按钮和进度 */}
        {!uploading ? (
          <button
            onClick={handleSelectClick}
            className="btn btn-primary text-lg px-8 py-3 mb-4"
            disabled={uploading}
          >
            选择文件
          </button>
        ) : (
          <div className="mb-4">
            <div className="flex items-center justify-center mb-2">
              <div className="loading-spinner mr-2"></div>
              <span className="text-primary-600 font-medium">正在上传... {progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* 用户输入框 */}
        <div className="max-w-md mx-auto mb-4">
          <textarea
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="可选：添加对数据集的描述或分析要求..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            rows={3}
            disabled={uploading}
          />
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <span className="text-red-600 mr-2">❌</span>
                <span className="text-red-700">{error}</span>
              </div>
              <button
                onClick={handleReset}
                className="text-red-600 hover:text-red-800 font-medium"
              >
                重试
              </button>
            </div>
          </div>
        )}

        {/* 提示信息 */}
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
          <div className="flex items-center">
            <span className="text-blue-600 mr-2">💡</span>
            <p className="text-blue-700 text-sm">
              提示：请上传包含时间序列数据的文件，系统将自动进行智能分析
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default FileUpload 