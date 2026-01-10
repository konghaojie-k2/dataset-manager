/**
 * 聊天市场布局组件
 * 提供分屏布局：左侧聊天，右侧数据集详情
 */

'use client'

import React, { useState } from 'react'
import ChatInterface from './ChatInterface'
import { DatasetSearchResult } from '@/types/chat'
import { api } from '@/lib/api'

interface ChatMarketplaceLayoutProps {
  children?: React.ReactNode
}

export default function ChatMarketplaceLayout({ children }: ChatMarketplaceLayoutProps) {
  const [selectedDataset, setSelectedDataset] = useState<DatasetSearchResult | null>(null)
  const [datasetDetails, setDatasetDetails] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  // 处理数据集点击
  const handleDatasetClick = async (dataset: DatasetSearchResult) => {
    setSelectedDataset(dataset)
    setLoading(true)

    try {
      // 获取完整的数据集详情
      const details = await api.datasets.getById(dataset.id)
      setDatasetDetails(details)
    } catch (error) {
      console.error('获取数据集详情失败:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen">
      {/* 左侧：聊天界面 (60%) */}
      <div className="w-3/5 border-r">
        <ChatInterface onDatasetClick={handleDatasetClick} />
      </div>

      {/* 右侧：数据集详情面板 (40%) */}
      <div className="w-2/5 bg-white overflow-y-auto">
        {selectedDataset ? (
          <div className="p-6">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
                  <p className="mt-4 text-gray-600">加载中...</p>
                </div>
              </div>
            ) : datasetDetails ? (
              <div>
                {/* 标题 */}
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  {datasetDetails.name}
                </h2>

                {/* 描述 */}
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-gray-500 mb-2">描述</h3>
                  <p className="text-gray-700">{datasetDetails.description}</p>
                </div>

                {/* 元数据 */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-1">文件大小</h3>
                    <p className="text-gray-900">
                      {(datasetDetails.file_size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-1">上传时间</h3>
                    <p className="text-gray-900">
                      {new Date(datasetDetails.upload_time).toLocaleDateString('zh-CN')}
                    </p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-1">列数</h3>
                    <p className="text-gray-900">{datasetDetails.columns?.length || 0}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-1">状态</h3>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        datasetDetails.processing_status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : datasetDetails.processing_status === 'processing'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {datasetDetails.processing_status}
                    </span>
                  </div>
                </div>

                {/* 标签 */}
                {datasetDetails.tags && datasetDetails.tags.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-gray-500 mb-2">标签</h3>
                    <div className="flex flex-wrap gap-2">
                      {datasetDetails.tags.map((tag: string, index: number) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-50 text-blue-700"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 列信息 */}
                {datasetDetails.columns && datasetDetails.columns.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-gray-500 mb-2">列信息</h3>
                    <div className="bg-gray-50 rounded-lg overflow-hidden">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-100">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                              列名
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                              类型
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                              业务含义
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {datasetDetails.columns.slice(0, 10).map((column: any, index: number) => (
                            <tr key={index}>
                              <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                                {column.name}
                              </td>
                              <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                                {column.data_type}
                              </td>
                              <td className="px-4 py-2 text-sm text-gray-500">
                                {column.business_meaning || '-'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {datasetDetails.columns.length > 10 && (
                        <div className="px-4 py-2 text-sm text-gray-500 text-center">
                          还有 {datasetDetails.columns.length - 10} 列...
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* 操作按钮 */}
                <div className="flex gap-3">
                  <button
                    onClick={() => window.open(`/api/v1/datasets/${selectedDataset.id}/preview`, '_blank')}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                  >
                    预览数据
                  </button>
                  <button
                    onClick={() => api.datasets.download(selectedDataset.id)}
                    className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
                  >
                    下载数据
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 mt-20">
                <p>无法加载数据集详情</p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-400">
              <svg
                className="mx-auto h-24 w-24 mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="text-lg mb-2">选择一个数据集</p>
              <p className="text-sm">点击左侧聊天中的数据集查看详细信息</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
