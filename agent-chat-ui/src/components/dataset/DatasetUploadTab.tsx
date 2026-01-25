/**
 * Dataset Upload & Analyze Tab
 * Clean, focused interface for uploading and analyzing datasets
 */

import React, { useState, useCallback } from 'react';
import { DatasetUpload } from './DatasetUpload';
import { AnalysisProgressPanel } from '../analysis/AnalysisProgressPanel';
import { DynamicResultView } from '../analysis/DynamicResultView';
import { datasetAPI, type AnalysisResult, type Dataset } from '@/lib/api-extension';

interface DatasetUploadTabProps {
  onUploadComplete?: (datasetId: string) => void;
  onAnalysisStart?: (datasetId: string) => void;
  analyzingDatasetId?: string | null;
  analysisResult?: AnalysisResult | null;
  onAnalysisComplete?: (result: AnalysisResult) => void;
}

export function DatasetUploadTab({
  onUploadComplete,
  onAnalysisStart,
  analyzingDatasetId,
  analysisResult,
  onAnalysisComplete,
}: DatasetUploadTabProps) {
  const [analyzedDataset, setAnalyzedDataset] = useState<Dataset | null>(null);

  // Analysis complete callback
  const handleAnalysisCompleteCallback = useCallback(async (result: AnalysisResult) => {
    // Fetch dataset details
    try {
      if (result.dataset_id) {
        const dataset = await datasetAPI.getDetails(result.dataset_id);
        setAnalyzedDataset(dataset);
      }
    } catch (error) {
      console.error('Failed to fetch dataset details:', error);
    }

    // Call parent callback
    onAnalysisComplete?.(result);
  }, [onAnalysisComplete]);

  // Upload new dataset
  const handleUploadNew = () => {
    setAnalyzedDataset(null);
  };

  return (
    <div className="max-w-4xl mx-auto">
      {!analysisResult ? (
        <>
          {/* Upload Section */}
          <div className="mb-8">
            <div className="text-center mb-8">
              <h2
                className="text-3xl font-bold text-[#1a1a1a] mb-3"
                style={{ fontFamily: 'var(--font-playfair)' }}
              >
                上传数据集
              </h2>
              <p className="text-gray-600 font-light">
                支持 CSV 和 ZIP 格式，上传后自动进行智能分析
              </p>
            </div>

            <DatasetUpload
              onUploadComplete={onUploadComplete}
              onAnalysisStart={onAnalysisStart}
            />
          </div>

          {/* Progress Section */}
          {analyzingDatasetId && (
            <div className="mt-8">
              <h3
                className="text-xl font-semibold text-[#1a1a1a] mb-4"
                style={{ fontFamily: 'var(--font-playfair)' }}
              >
                分析进度
              </h3>
              <AnalysisProgressPanel
                datasetId={analyzingDatasetId}
                onComplete={handleAnalysisCompleteCallback}
              />
            </div>
          )}
        </>
      ) : (
        <>
          {/* Results Section */}
          <div className="mb-6 flex items-center justify-between">
            <div>
              <button
                onClick={handleUploadNew}
                className="text-sm text-gray-500 hover:text-[#c75b39] transition-colors flex items-center gap-1 mb-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                上传新数据集
              </button>
              {analyzedDataset && (
                <>
                  <h2
                    className="text-3xl font-bold text-[#1a1a1a]"
                    style={{ fontFamily: 'var(--font-playfair)' }}
                  >
                    {analyzedDataset.name}
                  </h2>
                  <p className="text-gray-600 mt-1">
                    {analyzedDataset.description || '智能分析报告'}
                  </p>
                </>
              )}
            </div>
          </div>

          <DynamicResultView
            datasetId={analysisResult.dataset_id || ''}
            analysisResult={analysisResult}
          />
        </>
      )}

      {/* Info Cards */}
      {!analysisResult && !analyzingDatasetId && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          <div className="bg-white rounded-lg border border-[#e8e4df] p-6 text-center">
            <div className="w-12 h-12 bg-[#c75b39]/10 rounded-lg flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-[#c75b39]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h3 className="font-semibold text-[#1a1a1a] mb-2">拖拽上传</h3>
            <p className="text-sm text-gray-600">将文件拖到上方区域即可上传</p>
          </div>

          <div className="bg-white rounded-lg border border-[#e8e4df] p-6 text-center">
            <div className="w-12 h-12 bg-[#7c9885]/10 rounded-lg flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-[#7c9885]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="font-semibold text-[#1a1a1a] mb-2">智能分析</h3>
            <p className="text-sm text-gray-600">AI 自动识别数据特征并分析</p>
          </div>

          <div className="bg-white rounded-lg border border-[#e8e4df] p-6 text-center">
            <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="font-semibold text-[#1a1a1a] mb-2">安全可靠</h3>
            <p className="text-sm text-gray-600">数据本地存储，隐私安全</p>
          </div>
        </div>
      )}
    </div>
  );
}
