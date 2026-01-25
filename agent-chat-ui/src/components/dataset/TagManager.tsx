/**
 * 标签管理组件
 * 用于管理数据集的标签
 */

import React, { useState, useEffect } from 'react';
import { datasetAPI, type Dataset } from '@/lib/api-extension';

interface TagManagerProps {
  dataset: Dataset;
  onUpdated?: (dataset: Dataset) => void;
}

export function TagManager({ dataset, onUpdated }: TagManagerProps) {
  const [tags, setTags] = useState<string[]>(dataset.tags || []);
  const [newTag, setNewTag] = useState('');
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleAddTag = async () => {
    const trimmedTag = newTag.trim();
    if (!trimmedTag) return;
    if (tags.includes(trimmedTag)) {
      alert('标签已存在');
      return;
    }

    const updatedTags = [...tags, trimmedTag];
    setTags(updatedTags);
    setNewTag('');
    await saveTags(updatedTags);
  };

  const handleRemoveTag = async (tagToRemove: string) => {
    const updatedTags = tags.filter(t => t !== tagToRemove);
    setTags(updatedTags);
    await saveTags(updatedTags);
  };

  const saveTags = async (updatedTags: string[]) => {
    try {
      setLoading(true);
      await datasetAPI.updateTags(dataset.id, updatedTags);
      // 通知父组件刷新
      onUpdated?.({ ...dataset, tags: updatedTags });
    } catch (error) {
      console.error('Failed to update tags:', error);
      alert('更新标签失败');
      // 恢复原状态
      setTags(dataset.tags || []);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddTag();
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-gray-800">标签管理</h4>
        <button
          onClick={() => setEditing(!editing)}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          {editing ? '完成' : '编辑'}
        </button>
      </div>

      {/* 标签列表 */}
      <div className="flex flex-wrap gap-2">
        {tags.length === 0 ? (
          <span className="text-sm text-gray-400">暂无标签</span>
        ) : (
          tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
            >
              {tag}
              {editing && (
                <button
                  onClick={() => handleRemoveTag(tag)}
                  className="ml-1 text-blue-600 hover:text-blue-800"
                  disabled={loading}
                >
                  ×
                </button>
              )}
            </span>
          ))
        )}
      </div>

      {/* 添加标签 */}
      {editing && (
        <div className="flex gap-2">
          <input
            type="text"
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入新标签"
            className="flex-1 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            onClick={handleAddTag}
            disabled={loading || !newTag.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            添加
          </button>
        </div>
      )}
    </div>
  );
}

// 预设标签组件
const PRESET_TAGS = [
  '工业数据',
  '设备监控',
  '生产数据',
  '质量检测',
  '传感器数据',
  '时序数据',
  'CSV',
  '已分析',
  '待处理',
];

interface TagInputProps {
  selectedTags: string[];
  onTagsChange: (tags: string[]) => void;
  placeholder?: string;
}

export function TagInput({ selectedTags, onTagsChange, placeholder = '选择标签...' }: TagInputProps) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      onTagsChange(selectedTags.filter(t => t !== tag));
    } else {
      onTagsChange([...selectedTags, tag]);
    }
  };

  return (
    <div className="relative">
      {/* 选中的标签 */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="min-h-[42px] px-3 py-2 border rounded cursor-pointer flex flex-wrap gap-2"
      >
        {selectedTags.length === 0 ? (
          <span className="text-gray-400">{placeholder}</span>
        ) : (
          selectedTags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
              onClick={(e) => {
                e.stopPropagation();
                toggleTag(tag);
              }}
            >
              {tag}
              <span className="cursor-pointer hover:text-blue-600">×</span>
            </span>
          ))
        )}
      </div>

      {/* 下拉标签列表 */}
      {isOpen && (
        <div className="absolute z-10 w-full mt-1 border rounded-lg bg-white shadow-lg max-h-60 overflow-y-auto">
          <div className="p-2 space-y-1">
            {PRESET_TAGS.map((tag) => (
              <button
                key={tag}
                onClick={() => toggleTag(tag)}
                className={`w-full text-left px-3 py-2 rounded transition-colors ${
                  selectedTags.includes(tag)
                    ? 'bg-blue-100 text-blue-800'
                    : 'hover:bg-gray-100 text-gray-700'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
