/**
 * Dataset Filters Sidebar
 * Search and filter controls for the dataset marketplace
 */

import React from 'react';

interface DatasetFiltersProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  industries: string[];
  selectedIndustry: string;
  onIndustryChange: (industry: string) => void;
  tags: string[];
  selectedTags: string[];
  onTagsChange: (tags: string[]) => void;
  resultCount: number;
}

export function DatasetFilters({
  searchQuery,
  onSearchChange,
  industries,
  selectedIndustry,
  onIndustryChange,
  tags,
  selectedTags,
  resultCount,
}: DatasetFiltersProps) {
  const toggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      onTagsChange(selectedTags.filter((t) => t !== tag));
    } else {
      onTagsChange([...selectedTags, tag]);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-[#e8e4df] p-5 sticky top-24">
      {/* Search */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-[#1a1a1a] mb-2" style={{ fontFamily: 'var(--font-playfair)' }}>
          搜索
        </label>
        <div className="relative">
          <input
            type="text"
            placeholder="搜索数据集..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full px-4 py-2.5 pl-10 bg-[#faf8f5] border border-[#e8e4df] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#c75b39]/20 focus:border-[#c75b39] transition-all text-sm"
          />
          <svg
            className="absolute left-3 top-3 w-4 h-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      {/* Industry Filter */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-[#1a1a1a] mb-2" style={{ fontFamily: 'var(--font-playfair)' }}>
          行业领域
        </label>
        <select
          value={selectedIndustry}
          onChange={(e) => onIndustryChange(e.target.value)}
          className="w-full px-4 py-2.5 bg-[#faf8f5] border border-[#e8e4df] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#c75b39]/20 focus:border-[#c75b39] transition-all text-sm"
        >
          {industries.map((industry) => (
            <option key={industry} value={industry}>
              {industry === 'all' ? '全部行业' : industry}
            </option>
          ))}
        </select>
      </div>

      {/* Tags Filter */}
      {tags.length > 0 && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-[#1a1a1a] mb-2" style={{ fontFamily: 'var(--font-playfair)' }}>
            标签
          </label>
          <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
            {tags.slice(0, 10).map((tag) => (
              <button
                key={tag}
                onClick={() => toggleTag(tag)}
                className={`
                  px-3 py-1.5 text-xs rounded-full border transition-all
                  ${selectedTags.includes(tag)
                    ? 'bg-[#c75b39] text-white border-[#c75b39]'
                    : 'bg-[#faf8f5] text-gray-600 border-[#e8e4df] hover:border-[#c75b39] hover:text-[#c75b39]'
                  }
                `}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Clear Filters */}
      {(searchQuery || selectedIndustry !== 'all' || selectedTags.length > 0) && (
        <button
          onClick={() => {
            onSearchChange('');
            onIndustryChange('all');
            onTagsChange([]);
          }}
          className="w-full py-2 text-sm text-[#c75b39] border border-[#c75b39] rounded-lg hover:bg-[#c75b39] hover:text-white transition-all"
        >
          清除筛选
        </button>
      )}

      {/* Result Count */}
      <div className="mt-6 pt-4 border-t border-[#e8e4df]">
        <p className="text-sm text-gray-500">
          找到 <span className="font-semibold text-[#1a1a1a]">{resultCount}</span> 个数据集
        </p>
      </div>
    </div>
  );
}
