'use client'

import React, { useState } from 'react'
import FileUpload from './FileUpload'
import DatasetList from './DatasetList'

const ClientOnlyPage: React.FC = () => {
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const handleUploadSuccess = (datasetId: string) => {
    setUploadSuccess(`数据集上传成功！ID: ${datasetId}`)
    setUploadError(null)
    setTimeout(() => setUploadSuccess(null), 3000)
  }

  const handleUploadError = (error: string) => {
    setUploadError(error)
    setUploadSuccess(null)
  }

  const clearMessages = () => {
    setUploadSuccess(null)
    setUploadError(null)
  }

  return (
    <div suppressHydrationWarning>
      {/* 消息提示 */}
      {(uploadSuccess || uploadError) && (
        <div className="mb-6">
          {uploadSuccess && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
              <span className="text-green-700">{uploadSuccess}</span>
              <button onClick={clearMessages} className="text-green-600 hover:text-green-800 font-medium">×</button>
            </div>
          )}
          {uploadError && (
             <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center justify-between">
              <span className="text-red-700">{uploadError}</span>
              <button onClick={clearMessages} className="text-red-600 hover:text-red-800 font-medium">×</button>
            </div>
          )}
        </div>
      )}

      {/* 文件上传 */}
      <FileUpload
        onUploadSuccess={handleUploadSuccess}
        onUploadError={handleUploadError}
      />

      {/* 数据集列表 */}
      <DatasetList />
    </div>
  )
}

export default ClientOnlyPage 