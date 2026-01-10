'use client'

import React, { useState, createContext, useContext } from 'react'
import { FiSearch, FiUpload, FiGrid, FiList, FiFilter } from 'react-icons/fi'

interface DataManagerContextType {
  viewMode: 'grid' | 'list'
  setViewMode: (mode: 'grid' | 'list') => void
  searchQuery: string
  setSearchQuery: (query: string) => void
  showFilters: boolean
  setShowFilters: (show: boolean) => void
  showUpload: boolean
  setShowUpload: (show: boolean) => void
  filters: {
    tags: string[]
    dateRange: string
    fileType: string
    qualityScore: string
  }
  setFilters: (filters: any) => void
}

const DataManagerContext = createContext<DataManagerContextType | undefined>(undefined)

export const useDataManager = () => {
  const context = useContext(DataManagerContext)
  if (!context) {
    throw new Error('useDataManager must be used within DataManagerLayout')
  }
  return context
}

interface DataManagerLayoutProps {
  children: React.ReactNode
}

const DataManagerLayout: React.FC<DataManagerLayoutProps> = ({ children }) => {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const [filters, setFilters] = useState({
    tags: [] as string[],
    dateRange: '',
    fileType: '',
    qualityScore: ''
  })

  // 动态导入 FileUpload 以避免编译时错误
  const FileUploadComponent = React.useMemo(
    () => React.lazy(() => import('./FileUpload')),
    []
  )

  return (
    <DataManagerContext.Provider value={{
      viewMode,
      setViewMode,
      searchQuery,
      setSearchQuery,
      showFilters,
      setShowFilters,
      showUpload,
      setShowUpload,
      filters,
      setFilters
    }}>
      {/* 谷歌 Material Design 风格背景 */}
      <div className="min-h-screen bg-gray-100">
        {/* 顶部导航栏 - Material Design AppBar 风格 */}
        <header className="bg-white border-b border-gray-300 sticky top-0 z-50 shadow-sm">
          <div className="px-6 py-3">
            <div className="flex items-center justify-between">
              {/* 左侧：Logo 和标题 */}
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 bg-blue-600 rounded flex items-center justify-center shadow-sm">
                  <span className="text-white text-lg font-medium">DM</span>
                </div>
                <div>
                  <h1 className="text-base font-medium text-gray-800">数据管理中心</h1>
                </div>
              </div>

              {/* 右侧：操作按钮 */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowUpload(!showUpload)}
                  className={`flex items-center px-4 py-2 text-sm font-medium rounded transition-all duration-150 ${
                    showUpload
                      ? 'bg-gray-200 text-gray-700'
                      : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm'
                  }`}
                >
                  <FiUpload className="mr-2 w-4 h-4" />
                  上传数据
                </button>
              </div>
            </div>
          </div>

          {/* 搜索和筛选栏 */}
          <div className="px-6 pb-3">
            <div className="flex items-center space-x-3">
              {/* 搜索框 - Material Design 风格 */}
              <div className="flex-1 relative">
                <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="搜索数据集名称、标签、描述..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                />
              </div>

              {/* 视图切换 - Material Design Toggle Button */}
              <div className="flex items-center bg-gray-200 rounded-md p-0.5">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-1.5 rounded transition-all ${
                    viewMode === 'grid' ? 'bg-white shadow-sm text-blue-700' : 'text-gray-600 hover:bg-gray-300'
                  }`}
                  title="网格视图"
                >
                  <FiGrid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-1.5 rounded transition-all ${
                    viewMode === 'list' ? 'bg-white shadow-sm text-blue-700' : 'text-gray-600 hover:bg-gray-300'
                  }`}
                  title="列表视图"
                >
                  <FiList className="w-4 h-4" />
                </button>
              </div>

              {/* 筛选按钮 */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`flex items-center px-4 py-2 text-sm font-medium rounded-md transition-all ${
                  showFilters
                    ? 'bg-blue-50 text-blue-700 border border-blue-500'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                <FiFilter className="mr-2 w-4 h-4" />
                筛选
                {(filters.tags.length > 0 || filters.dateRange || filters.qualityScore) && (
                  <span className="ml-2 w-2 h-2 bg-blue-600 rounded-full" />
                )}
              </button>
            </div>
          </div>
        </header>

        {/* 上传面板（可折叠） */}
        {showUpload && (
          <div className="bg-white border-b border-gray-300 px-6 py-4 shadow-sm">
            <React.Suspense fallback={<div className="text-sm text-gray-500">加载上传组件...</div>}>
              <FileUploadComponent
                onUploadSuccess={(id) => {
                  console.log('Upload success:', id)
                  setShowUpload(false)
                }}
                onUploadError={(error) => console.error('Upload error:', error)}
              />
            </React.Suspense>
          </div>
        )}

        {/* 筛选面板（可折叠） */}
        {showFilters && (
          <div className="bg-white border-b border-gray-300 px-6 py-4 shadow-sm">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">
                  标签
                </label>
                <select
                  value={filters.tags[0] || ''}
                  onChange={(e) => setFilters({ ...filters, tags: e.target.value ? [e.target.value] : [] })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">所有标签</option>
                  <option value="生产数据">生产数据</option>
                  <option value="测试数据">测试数据</option>
                  <option value="历史数据">历史数据</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">
                  时间范围
                </label>
                <select
                  value={filters.dateRange}
                  onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">所有时间</option>
                  <option value="today">今天</option>
                  <option value="week">最近一周</option>
                  <option value="month">最近一月</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">
                  文件类型
                </label>
                <select
                  value={filters.fileType}
                  onChange={(e) => setFilters({ ...filters, fileType: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">所有类型</option>
                  <option value="csv">CSV 文件</option>
                  <option value="excel">Excel 文件</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">
                  质量评分
                </label>
                <select
                  value={filters.qualityScore}
                  onChange={(e) => setFilters({ ...filters, qualityScore: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">所有评分</option>
                  <option value="high">高评分 (≥80)</option>
                  <option value="medium">中等评分 (60-79)</option>
                  <option value="low">低评分 (&lt;60)</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* 主内容区 */}
        <main className="px-6 py-4">
          {children}
        </main>
      </div>
    </DataManagerContext.Provider>
  )
}

export default DataManagerLayout
