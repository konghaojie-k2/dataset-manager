/**
 * 数据集列表组件
 * 显示所有数据集，支持搜索、筛选
 */

import React, { useEffect, useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { datasetAPI, type Dataset } from '@/lib/api-extension';
import { Badge } from '@/components/ui/badge';

interface DatasetListProps {
  datasets: Dataset[];
  selectedId: string | null;
  analyzingId: string | null;
  onSelect: (dataset: Dataset) => void;
  refreshTrigger?: number;
}

export function DatasetList({ datasets, selectedId, analyzingId, onSelect, refreshTrigger }: DatasetListProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredDatasets, setFilteredDatasets] = useState(datasets);

  // 搜索过滤
  useEffect(() => {
    if (!searchQuery) {
      setFilteredDatasets(datasets);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredDatasets(
        datasets.filter(
          (d) =>
            d.name.toLowerCase().includes(query) ||
            (d.description && d.description.toLowerCase().includes(query)) ||
            d.tags.some((tag) => tag.toLowerCase().includes(query))
        )
      );
    }
  }, [searchQuery, datasets, refreshTrigger]);

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // 获取状态颜色
  const getStatusColor = (status: string): string => {
    if (status === 'uploaded') return 'bg-gray-100 text-gray-800';
    if (status === 'analyzing') return 'bg-blue-100 text-blue-800';
    if (status.includes('completed')) return 'bg-green-100 text-green-800';
    return 'bg-yellow-100 text-yellow-800';
  };

  return (
    <div className="space-y-4">
      {/* 搜索框 */}
      <div className="relative">
        <input
          type="text"
          placeholder="搜索数据集..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <svg
          className="absolute right-3 top-2.5 w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>

      {/* 数据集列表 */}
      <div className="space-y-2 max-h-[600px] overflow-y-auto">
        {filteredDatasets.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            {searchQuery ? '未找到匹配的数据集' : '暂无数据集'}
          </div>
        ) : (
          filteredDatasets.map((dataset) => (
            <div
              key={dataset.id}
              onClick={() => onSelect(dataset)}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                selectedId === dataset.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              } ${analyzingId === dataset.id ? 'ring-2 ring-blue-300' : ''}`}
            >
              {/* 头部：名称和状态 */}
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-gray-900 flex-1">{dataset.name}</h3>
                <span className={`px-2 py-1 rounded text-xs ${getStatusColor(dataset.processing_status)}`}>
                  {dataset.processing_status}
                </span>
              </div>

              {/* 描述 */}
              {dataset.description && (
                <p className="text-sm text-gray-600 mb-2 line-clamp-2">{dataset.description}</p>
              )}

              {/* 标签 */}
              {dataset.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {dataset.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}

              {/* 元数据 */}
              <div className="flex items-center gap-4 text-xs text-gray-500">
                {dataset.row_count && (
                  <span>{dataset.row_count.toLocaleString()} 行</span>
                )}
                {dataset.column_count && (
                  <span>{dataset.column_count} 列</span>
                )}
                <span>{formatFileSize(dataset.file_size)}</span>
                {dataset.upload_time && (
                  <span>{formatDistanceToNow(new Date(dataset.upload_time), { addSuffix: true })}</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
