'use client'

import React, { useState } from 'react'
import Header from '@/components/Header'
import FileUpload from '@/components/FileUpload'
import DatasetList from '@/components/DatasetList'

const HomePage: React.FC = () => {
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  // 处理上传成功
  const handleUploadSuccess = (datasetId: string) => {
    setUploadSuccess(`数据集上传成功！ID: ${datasetId}`)
    setUploadError(null)
    
    // 3秒后清除成功消息
    setTimeout(() => {
      setUploadSuccess(null)
    }, 3000)
  }

  // 处理上传错误
  const handleUploadError = (error: string) => {
    setUploadError(error)
    setUploadSuccess(null)
  }

  // 清除消息
  const clearMessages = () => {
    setUploadSuccess(null)
    setUploadError(null)
  }

  return (
    <div>
      {/* 页面头部 */}
      <Header />

      {/* 主要内容区域 */}
      <main className="p-8">
        {/* 消息提示 */}
        {(uploadSuccess || uploadError) && (
          <div className="mb-6">
            {uploadSuccess && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center">
                  <span className="text-green-600 mr-2">✅</span>
                  <span className="text-green-700">{uploadSuccess}</span>
                </div>
                <button
                  onClick={clearMessages}
                  className="text-green-600 hover:text-green-800 font-medium"
                >
                  ×
                </button>
              </div>
            )}
            
            {uploadError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center">
                  <span className="text-red-600 mr-2">❌</span>
                  <span className="text-red-700">{uploadError}</span>
                </div>
                <button
                  onClick={clearMessages}
                  className="text-red-600 hover:text-red-800 font-medium"
                >
                  ×
                </button>
              </div>
            )}
          </div>
        )}

        {/* 文件上传区域 */}
        <FileUpload
          onUploadSuccess={handleUploadSuccess}
          onUploadError={handleUploadError}
        />

        {/* 数据集管理区域 */}
        <DatasetList />
      </main>
    </div>
  )
}

export default HomePage 