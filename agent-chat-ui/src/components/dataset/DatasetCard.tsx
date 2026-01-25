/**
 * Dataset Card Component
 * E-commerce style card for displaying datasets in the marketplace
 */

import React, { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { type Dataset } from '@/lib/api-extension';

interface DatasetCardProps {
  dataset: Dataset;
  onClick?: () => void;
  onDelete?: (datasetId: string) => void;
  analyzing?: boolean;
}

export function DatasetCard({ dataset, onClick, onDelete, analyzing }: DatasetCardProps) {
  const [deleting, setDeleting] = useState(false);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getStatusInfo = (status: string) => {
    if (status === 'uploaded' || status.includes('completed')) {
      return { text: '可用', bgColor: 'bg-[#7c9885]/10', textColor: 'text-[#7c9885]' };
    }
    if (status === 'analyzing') {
      return { text: '分析中', bgColor: 'bg-[#c75b39]/10', textColor: 'text-[#c75b39]' };
    }
    return { text: status, bgColor: 'bg-gray-100', textColor: 'text-gray-600' };
  };

  const status = getStatusInfo(dataset.processing_status);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();

    if (deleting || analyzing) return;

    const confirmed = window.confirm(
      `确定要删除数据集 "${dataset.name}" 吗？\n\n此操作将：\n• 删除数据集文件\n• 删除所有分析结果\n• 删除相关的血缘关系\n\n此操作无法撤销！`
    );

    if (!confirmed) return;

    setDeleting(true);
    try {
      await onDelete?.(dataset.id);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div
      onClick={onClick}
      className="group bg-white rounded-lg border border-[#e8e4df] hover:border-[#c75b39] hover:shadow-lg transition-all duration-300 cursor-pointer overflow-hidden"
    >
      {/* Card Header - Color strip */}
      <div className="h-2 bg-gradient-to-r from-[#c75b39] to-[#7c9885]" />

      {/* Card Content */}
      <div className="p-5">
        {/* Title and Status */}
        <div className="flex items-start justify-between mb-3">
          <h3
            className="font-semibold text-lg text-[#1a1a1a] leading-tight group-hover:text-[#c75b39] transition-colors line-clamp-2"
            style={{ fontFamily: 'var(--font-playfair)' }}
          >
            {dataset.name}
          </h3>
          <span className={`px-2 py-1 rounded text-xs font-medium ${status.bgColor} ${status.textColor} flex-shrink-0 ml-2`}>
            {status.text}
          </span>
        </div>

        {/* Description */}
        {dataset.description && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-2 font-light">
            {dataset.description}
          </p>
        )}

        {/* Tags */}
        {dataset.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {dataset.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 bg-[#faf8f5] text-gray-600 text-xs rounded border border-[#e8e4df]"
              >
                {tag}
              </span>
            ))}
            {dataset.tags.length > 3 && (
              <span className="px-2 py-0.5 text-gray-400 text-xs">
                +{dataset.tags.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-500 mb-3">
          {dataset.row_count && (
            <div className="flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7c0-2-1-3-3-3H7C5 4 4 5 4 7z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h8M8 8h8M8 16h4" />
              </svg>
              <span>{dataset.row_count.toLocaleString()} 行</span>
            </div>
          )}
          {dataset.column_count && (
            <div className="flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
              </svg>
              <span>{dataset.column_count} 列</span>
            </div>
          )}
          <div className="flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
            </svg>
            <span>{formatFileSize(dataset.file_size)}</span>
          </div>
          {dataset.industry && (
            <div className="flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <span className="truncate">{dataset.industry}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-[#e8e4df] flex items-center justify-between">
          <div className="text-xs text-gray-400">
            {dataset.upload_time && (
              <span>{formatDistanceToNow(new Date(dataset.upload_time), { addSuffix: true })}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* 删除按钮 */}
            {onDelete && (
              <button
                onClick={handleDelete}
                disabled={deleting || analyzing}
                className="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                title="删除数据集"
              >
                {deleting ? (
                  <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                )}
              </button>
            )}
            {/* 查看按钮 */}
            <div className="flex items-center gap-1 text-[#c75b39] text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
              <span>查看</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
