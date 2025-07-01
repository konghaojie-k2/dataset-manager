import React from 'react'

const LoadingSpinner: React.FC = () => {
  return (
    <div className="flex items-center justify-center py-8">
      <div className="loading-spinner"></div>
      <span className="ml-2 text-gray-600">加载中...</span>
    </div>
  )
}

export default LoadingSpinner 