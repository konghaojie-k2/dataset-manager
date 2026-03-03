#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Card Component
* E-commerce style card for displaying datasets in marketplace
* Updated: Added action menu for convert and compress operations
"""

import React, { useState } from 'react'
import { formatDistanceToNow } from 'date-fns';
import { type Dataset } from '@/lib/api-extension';
import { ConvertDialog } from './ConvertDialog';
import { CompressDialog } from './CompressDialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuLabel, DropdownMenuSeparator } from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

interface DatasetCardProps {
  dataset: Dataset;
  onClick?: () => void;
  onDelete?: (datasetId: string) => void;
  analyzing?: boolean;
}

export function DatasetCard({ dataset, onClick, onDelete, analyzing }: DatasetCardProps) {
  const [deleting, setDeleting] = useState(false);
  const [showConvertDialog, setShowConvertDialog] = useState(false);
  const [showCompressDialog, setShowCompressDialog] = useState(false);
  
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
          <div className="flex-1">
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
          
          {/* Action Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="h-8 w-8 p-0"
                disabled={deleting || analyzing}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="2" />
                  <path d="M12 6a2 2 0 006 6 0 012a2 2 0 006z M12 4a2 2 0 006-6a2 2 0 008 0z" />
                </svg>
              </Button>
            </DropdownMenuTrigger>
            
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setShowConvertDialog(true)}>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a2 2 0 00-2.83a2 2 0 002 83a2.2 0 002 83a2 2 0 002 83a2 2 0 002 83a2.2 0 006 6a2 2 0 012a2 2 0 006z M4 12v8a4 4 0 008 0 012a4 4 0 008z" />
                </svg>
                转换为 Parquet
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setShowCompressDialog(true)}>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 8v21a1 1 0 011-21.8.2 0 009 1.1.1.1.8 2 0 11.8a1 1.1 1.1.1.8 2 0 009 1.1.1 1.1.1.8 2 0 009 1.1.1.1.1.1.8 2 0 009 2 0 009 1.1.1.1.1.8 2 0 0 009 1.1 1.1.1.1.8 2 0 0 009 2 0 0 009 2z" />
                </svg>
                压缩文件
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => window.open(`/datasets/${dataset.id}/view`, '_blank')}>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7 7 7-7 7" />
                </svg>
                查看数据
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.1 3 3h10c2 1 3 3 5 0 11.9.9M9 17v4.5 0 11 9.9M5 13h19c2 1 3 3 5 0 11 9.9M9 19l3 3m0 0l3 3m3 3v12" />
                </svg>
                <span>{dataset.row_count.toLocaleString()} 行</span>
            </div>
          )}
          {dataset.column_count && (
            <div className="flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 00-2v16a2 2 0 00-2 2 2 0 002 2 2 0 011 1.9 9M9 19l3 3m0 0l3 3m0 3v12" />
              </svg>
                <span>{dataset.column_count} 列</span>
            </div>
          )}
          <div className="flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5.5 0 1115.9M6 21l-1 1 4h1m1 4h1m4 4h1m1 4h1m-4 4h1m1 4h1m1 4h1m-4 4h1m1 4h1m1 4h1m-4 4h1m1 4h1m4 4h1m1 4h1 3M4 7v10c0 2 1 3 3h10c2 1 3 3 5 0 11 9.9M9 19l3 3m0 0l3 3m3 3v12" />
              </svg>
              <span>{formatFileSize(dataset.file_size)}</span>
            </div>
          {dataset.industry && (
            <div className="flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2.82H7a2 2 0 00-2.82zm0 10a5 5 0 000 2 2 0 002 2H2a2 2 0 00-2v10a2 2 0 011 1v3a2 2 0 0 11.9 9.9M19 21V5a2 2 0 00-2.82H7a2 2 0 00-2 82zM9 19l3 3m0 0l3 3m0 3v12" />
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
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6 3a9 9 011-18 0z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 01-1.995 1.858L5 7m5 4v6m1 10V4a1 1 0 00 1 1h4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                )}
              </button>
            )}
            {/* 查看按钮 */}
            <div className="flex items-center gap-1 text-[#c75b39] text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
              <span>查看</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7 7" />
              </svg>
            </div>
          </div>
        </div>
      </div>
      
      {/* Convert Dialog */}
      <ConvertDialog
        dataset={dataset}
        open={showConvertDialog}
        onOpenChange={setShowConvertDialog}
        onConvertSuccess={() => {
          // 转换成功后刷新数据集列表
          window.location.reload()
        }}
      />
      
      {/* Compress Dialog */}
      <CompressDialog
        dataset={dataset}
        open={showCompressDialog}
        onOpenChange={setShowCompressDialog}
        onCompressSuccess={() => {
          // 压缩成功后刷新数据集列表
          window.location.reload()
        }}
      />
    </div>
  );
}