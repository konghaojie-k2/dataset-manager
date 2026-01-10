'use client'

import React, { useState } from 'react'
import ChatMarketplaceLayout from '@/components/chat/ChatMarketplaceLayout'
import DataManagerLayout from '@/components/DataManagerLayout'
import EnhancedDatasetList from '@/components/EnhancedDatasetList'

const HomePage: React.FC = () => {
  const [viewMode, setViewMode] = useState<'chat' | 'traditional'>('chat')

  return (
    <div className="h-screen flex flex-col">
      {/* 视图切换按钮 */}
      <div className="bg-white border-b px-4 py-2 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">数据超市</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('chat')}
            className={`px-4 py-2 rounded-lg transition ${
              viewMode === 'chat'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            聊天模式
          </button>
          <button
            onClick={() => setViewMode('traditional')}
            className={`px-4 py-2 rounded-lg transition ${
              viewMode === 'traditional'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            传统视图
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'chat' ? <ChatMarketplaceLayout /> : (
          <DataManagerLayout>
            <EnhancedDatasetList />
          </DataManagerLayout>
        )}
      </div>
    </div>
  )
}

export default HomePage
