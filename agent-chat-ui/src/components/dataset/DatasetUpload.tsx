/**
 * 文件上传组件
 * 支持拖拽上传，上传后自动触发 Agent 分析
 * Redesigned with marketplace aesthetic
 */

import React, { useState, useCallback } from 'react';
import { datasetAPI } from '@/lib/api-extension';

interface DatasetUploadProps {
  onUploadComplete?: (datasetId: string) => void;
  onAnalysisStart?: (datasetId: string) => void;
}

export function DatasetUpload({ onUploadComplete, onAnalysisStart }: DatasetUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [userInput, setUserInput] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleFileChange = (selectedFile: File | null) => {
    if (selectedFile) {
      const validExtensions = ['.csv', '.zip'];
      const extension = '.' + selectedFile.name.split('.').pop()?.toLowerCase();

      if (!validExtensions.includes(extension)) {
        alert('只支持 CSV 和 ZIP 文件');
        return;
      }

      setFile(selectedFile);
    }
  };

  const handleUpload = useCallback(async () => {
    if (!file) return;

    setUploading(true);
    setProgress(0);

    try {
      // 模拟上传进度
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // 上传并自动触发分析
      const result = await datasetAPI.uploadAndAnalyze(file, userInput);

      clearInterval(progressInterval);
      setProgress(100);

      // 通知父组件
      onAnalysisStart?.(result.dataset_id);

      // 延迟一下再调用 onUploadComplete，让用户看到进度完成
      setTimeout(() => {
        onUploadComplete?.(result.dataset_id);
      }, 500);

      // 重置表单
      setFile(null);
      setUserInput('');
      setProgress(0);
    } catch (error) {
      console.error('Upload failed:', error);
      alert(`上传失败: ${error}`);
    } finally {
      setUploading(false);
    }
  }, [file, userInput, onUploadComplete, onAnalysisStart]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      handleFileChange(droppedFile);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  return (
    <div className="bg-white rounded-lg border border-[#e8e4df] p-8">
      {/* 拖拽上传区域 */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center transition-all duration-300
          ${dragOver
            ? 'border-[#c75b39] bg-[#c75b39]/5'
            : 'border-[#e8e4df] hover:border-[#c75b39]/50'
          }
        `}
      >
        <input
          type="file"
          accept=".csv,.zip"
          onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
          className="hidden"
          id="file-upload"
          disabled={uploading}
        />
        <label
          htmlFor="file-upload"
          className="cursor-pointer flex flex-col items-center gap-4"
        >
          <div
            className={`
              w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300
              ${dragOver ? 'bg-[#c75b39]/10' : 'bg-[#faf8f5]'}
            `}
          >
            <svg
              className={`w-8 h-8 transition-colors ${dragOver ? 'text-[#c75b39]' : 'text-gray-400'}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
          <div className="space-y-1">
            <span className="text-[#1a1a1a] font-medium" style={{ fontFamily: 'var(--font-playfair)' }}>
              {file ? file.name : '拖拽文件到此处或点击选择'}
            </span>
            <p className="text-sm text-gray-500">支持 CSV、ZIP 文件，最大 100MB</p>
          </div>
        </label>
      </div>

      {/* 用户输入 */}
      <div className="mt-6">
        <label className="block text-sm font-medium text-[#1a1a1a] mb-2" style={{ fontFamily: 'var(--font-playfair)' }}>
          数据集描述（可选）
        </label>
        <textarea
          placeholder="添加关于数据集的额外信息，帮助 AI 更好地理解数据..."
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          className="w-full px-4 py-3 bg-[#faf8f5] border border-[#e8e4df] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#c75b39]/20 focus:border-[#c75b39] transition-all text-sm resize-none"
          rows={3}
          disabled={uploading}
        />
      </div>

      {/* 上传进度 */}
      {uploading && (
        <div className="mt-6 p-4 bg-[#faf8f5] rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-[#1a1a1a]">上传中...</span>
            <span className="text-sm text-[#c75b39] font-semibold">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-[#c75b39] to-[#7c9885] h-2 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">
            {progress < 100 ? '正在上传数据集...' : '上传完成，正在启动智能分析...'}
          </p>
        </div>
      )}

      {/* 上传按钮 */}
      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className={`
          w-full mt-6 px-6 py-3 rounded-lg font-medium transition-all duration-300
          ${file && !uploading
            ? 'bg-[#c75b39] text-white hover:bg-[#a64a2f] shadow-md hover:shadow-lg'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }
        `}
        style={{ fontFamily: 'var(--font-outfit)' }}
      >
        {uploading ? '处理中...' : '上传并开始智能分析'}
      </button>

      {/* 提示信息 */}
      <p className="text-xs text-gray-500 text-center mt-4">
        <span className="inline-block w-1 h-1 bg-[#7c9885] rounded-full mr-1" />
        上传后 AI Agent 将自动分析数据特征并生成报告
      </p>
    </div>
  );
}
