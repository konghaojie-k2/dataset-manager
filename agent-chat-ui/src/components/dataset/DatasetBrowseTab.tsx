/**
 * Dataset Browse Tab
 * Marketplace-style grid layout for browsing datasets
 */

import React, { useEffect, useState, useCallback } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { type Dataset } from '@/lib/api-extension';
import { datasetAPI } from '@/lib/api-extension';
import { DatasetCard } from './DatasetCard';
import { DatasetFilters } from './DatasetFilters';

interface DatasetBrowseTabProps {
  datasets: Dataset[];
  onDatasetSelect: (dataset: Dataset) => void;
  refreshTrigger: number;
  onDatasetDeleted?: () => void;
  analyzingId?: string | null;
}

export function DatasetBrowseTab({ datasets, onDatasetSelect, refreshTrigger, onDatasetDeleted, analyzingId }: DatasetBrowseTabProps) {
  const [filteredDatasets, setFilteredDatasets] = useState<Dataset[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState<string>('all');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  // Initialize filtered datasets
  useEffect(() => {
    setFilteredDatasets(datasets);
  }, [datasets]);

  // Filter datasets
  useEffect(() => {
    let filtered = datasets;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (d) =>
          d.name.toLowerCase().includes(query) ||
          (d.description && d.description.toLowerCase().includes(query))
      );
    }

    // Industry filter
    if (selectedIndustry !== 'all') {
      filtered = filtered.filter((d) => d.industry === selectedIndustry);
    }

    // Tags filter
    if (selectedTags.length > 0) {
      filtered = filtered.filter((d) =>
        selectedTags.some((tag) => d.tags.includes(tag))
      );
    }

    setFilteredDatasets(filtered);
  }, [searchQuery, selectedIndustry, selectedTags, datasets, refreshTrigger]);

  // Get all unique industries and tags
  const industries = ['all', ...Array.from(new Set(datasets.map((d) => d.industry).filter(Boolean)))];
  const allTags = Array.from(new Set(datasets.flatMap((d) => d.tags)));

  // Handle dataset card click - pass to parent to switch to chat
  const handleDatasetClick = useCallback((dataset: Dataset) => {
    onDatasetSelect(dataset);
  }, [onDatasetSelect]);

  // Handle dataset delete
  const handleDelete = useCallback(async (datasetId: string) => {
    try {
      await datasetAPI.delete(datasetId);
      onDatasetDeleted?.();
      // eslint-disable-next-line no-alert
      alert('数据集删除成功');
    } catch (error: any) {
      console.error('删除失败:', error);
      // eslint-disable-next-line no-alert
      alert(`删除失败: ${error.message || error}`);
    }
  }, [onDatasetDeleted]);

  return (
    <div className="flex gap-8">
      {/* Filters Sidebar */}
      <aside className="w-64 flex-shrink-0">
        <DatasetFilters
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          industries={industries}
          selectedIndustry={selectedIndustry}
          onIndustryChange={setSelectedIndustry}
          tags={allTags}
          selectedTags={selectedTags}
          onTagsChange={setSelectedTags}
          resultCount={filteredDatasets.length}
        />
      </aside>

      {/* Dataset Grid */}
      <div className="flex-1">
        {filteredDatasets.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-lg border border-[#e8e4df]">
            <div className="text-gray-400 mb-4">
              <svg
                className="w-16 h-16 mx-auto"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <p className="text-gray-500 text-lg mb-2">没有找到数据集</p>
            <p className="text-sm text-gray-400">
              {searchQuery || selectedIndustry !== 'all' || selectedTags.length > 0
                ? '尝试调整筛选条件'
                : '前往"上传与分析"标签页上传您的第一个数据集'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredDatasets.map((dataset) => (
              <DatasetCard
                key={dataset.id}
                dataset={dataset}
                onClick={() => handleDatasetClick(dataset)}
                onDelete={handleDelete}
                analyzing={analyzingId === dataset.id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
