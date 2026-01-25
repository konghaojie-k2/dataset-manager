"use client";

import React, { useState, useCallback, useEffect } from 'react';
import { Thread } from '@/components/thread';
import { StreamProvider } from '@/providers/Stream';
import { ThreadProvider } from '@/providers/Thread';
import { ArtifactProvider } from '@/components/thread/artifact';
import { Toaster } from '@/components/ui/sonner';
import { DatasetBrowseTab } from '@/components/dataset/DatasetBrowseTab';
import { DatasetUploadTab } from '@/components/dataset/DatasetUploadTab';
import { DatasetMarketplaceHeader } from '@/components/dataset/DatasetMarketplaceHeader';
import { datasetAPI, type Dataset, type AnalysisResult } from '@/lib/api-extension';
import { AnalysisProgressPanel } from '@/components/analysis/AnalysisProgressPanel';
import { DynamicResultView } from '@/components/analysis/DynamicResultView';

type TabType = 'chat' | 'browse' | 'upload';

export default function HomePage(): React.ReactNode {
  // Tab state - default to chat (智能查询)
  const [activeTab, setActiveTab] = useState<TabType>('chat');

  // Dataset states
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetForView, setSelectedDatasetForView] = useState<Dataset | null>(null);
  const [viewingAnalysisResult, setViewingAnalysisResult] = useState<AnalysisResult | null>(null);
  const [analyzingDatasetId, setAnalyzingDatasetId] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Load datasets
  useEffect(() => {
    const loadDatasets = async () => {
      try {
        const data = await datasetAPI.list();
        setDatasets(data);
      } catch (error) {
        console.error('Failed to load datasets:', error);
      }
    };
    loadDatasets();
  }, [refreshTrigger]);

  // Upload complete callback
  const handleUploadComplete = useCallback((datasetId: string) => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  // Analysis start callback
  const handleAnalysisStart = useCallback((datasetId: string) => {
    setAnalyzingDatasetId(datasetId);
    setAnalysisResult(null);
  }, []);

  // Analysis complete callback
  const handleAnalysisComplete = useCallback(async (result: AnalysisResult) => {
    setAnalyzingDatasetId(null);
    setAnalysisResult(result);
    setRefreshTrigger(prev => prev + 1);

    // Fetch dataset details
    try {
      if (result.dataset_id) {
        const dataset = await datasetAPI.getById(result.dataset_id);
        // After analysis, show the result in view mode
        setSelectedDatasetForView(dataset);
        setViewingAnalysisResult(result);
      }
    } catch (error) {
      console.error('Failed to fetch dataset details:', error);
    }
  }, []);

  // Select dataset - view analysis results in browse tab
  const handleSelectDataset = useCallback(async (dataset: Dataset) => {
    setSelectedDatasetForView(dataset);

    // Fetch analysis results for this dataset
    try {
      const result = await datasetAPI.getAnalysisResults(dataset.id);
      setViewingAnalysisResult(result);
    } catch (error) {
      console.error('Failed to fetch analysis results:', error);
      setViewingAnalysisResult(null);
    }
  }, []);

  // Close analysis result view
  const handleCloseAnalysisView = useCallback(() => {
    setSelectedDatasetForView(null);
    setViewingAnalysisResult(null);
  }, []);

  // Cancel analysis result view
  const handleBackToChat = useCallback(() => {
    setAnalysisResult(null);
  }, []);

  return (
    <React.Suspense fallback={<div className="flex items-center justify-center h-screen">加载中...</div>}>
      <Toaster />
      <ThreadProvider>
        <StreamProvider>
          <ArtifactProvider>
            <div className="min-h-screen bg-[#faf8f5]">
              {/* Header */}
              <DatasetMarketplaceHeader />

              {/* Tab Navigation */}
              <div className="border-b border-[#e8e4df] bg-white/80 backdrop-blur-sm sticky top-0 z-40">
                <div className="max-w-7xl mx-auto px-6">
                  <nav className="flex gap-8">
                    <button
                      onClick={() => setActiveTab('chat')}
                      className={`
                        relative py-4 px-1 font-medium transition-all duration-300
                        ${activeTab === 'chat'
                          ? 'text-[#1a1a1a]'
                          : 'text-gray-400 hover:text-gray-600'
                        }
                      `}
                      style={{ fontFamily: 'var(--font-playfair)' }}
                    >
                      <span className="text-lg">智能查询</span>
                      {activeTab === 'chat' && (
                        <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#c75b39] transform scale-x-100 transition-transform duration-300" />
                      )}
                    </button>
                    <button
                      onClick={() => setActiveTab('browse')}
                      className={`
                        relative py-4 px-1 font-medium transition-all duration-300
                        ${activeTab === 'browse'
                          ? 'text-[#1a1a1a]'
                          : 'text-gray-400 hover:text-gray-600'
                        }
                      `}
                      style={{ fontFamily: 'var(--font-playfair)' }}
                    >
                      <span className="text-lg">浏览数据集</span>
                      {activeTab === 'browse' && (
                        <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#c75b39] transform scale-x-100 transition-transform duration-300" />
                      )}
                    </button>
                    <button
                      onClick={() => setActiveTab('upload')}
                      className={`
                        relative py-4 px-1 font-medium transition-all duration-300
                        ${activeTab === 'upload'
                          ? 'text-[#1a1a1a]'
                          : 'text-gray-400 hover:text-gray-600'
                        }
                      `}
                      style={{ fontFamily: 'var(--font-playfair)' }}
                    >
                      <span className="text-lg">上传与分析</span>
                      {activeTab === 'upload' && (
                        <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#c75b39] transform scale-x-100 transition-transform duration-300" />
                      )}
                    </button>
                  </nav>
                </div>
              </div>

              {/* Content */}
              <main className="max-w-7xl mx-auto">
                {activeTab === 'browse' && (
                  <div className="relative px-6 py-8">
                    <DatasetBrowseTab
                      datasets={datasets}
                      onDatasetSelect={handleSelectDataset}
                      refreshTrigger={refreshTrigger}
                    />

                    {/* Backdrop */}
                    {selectedDatasetForView && viewingAnalysisResult && (
                      <div
                        className="fixed inset-0 bg-black/30 z-40 backdrop-blur-sm"
                        onClick={handleCloseAnalysisView}
                      />
                    )}

                    {/* Analysis Result Side Panel */}
                    {selectedDatasetForView && viewingAnalysisResult && (
                      <div className="fixed inset-x-0 top-[180px] bottom-0 mx-auto max-w-5xl bg-white border border-[#e8e4df] shadow-2xl overflow-hidden flex flex-col z-50 animate-in slide-in-from-top duration-300 rounded-2xl">
                        {/* Header */}
                        <div className="bg-gradient-to-r from-[#faf8f5] to-white border-b border-[#e8e4df] px-8 py-6 flex items-center justify-between shrink-0">
                          <div className="flex-1 min-w-0">
                            <h2
                              className="text-2xl font-bold text-[#1a1a1a] truncate"
                              style={{ fontFamily: 'var(--font-playfair)' }}
                            >
                              {selectedDatasetForView.name}
                            </h2>
                            <p className="text-sm text-gray-500 mt-1 truncate">
                              {selectedDatasetForView.description || '数据分析报告'}
                            </p>
                          </div>
                          <button
                            onClick={handleCloseAnalysisView}
                            className="ml-4 flex-shrink-0 p-2 hover:bg-gray-100 rounded-full transition-colors group"
                            aria-label="关闭"
                          >
                            <svg className="w-7 h-7 text-gray-400 group-hover:text-gray-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>

                        {/* Analysis results */}
                        <div className="flex-1 overflow-y-auto p-8 bg-white">
                          <DynamicResultView
                            datasetId={selectedDatasetForView.id}
                            analysisResult={viewingAnalysisResult}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'upload' && (
                  <div className="px-6 py-8">
                    <DatasetUploadTab
                      onUploadComplete={handleUploadComplete}
                      onAnalysisStart={handleAnalysisStart}
                      analyzingDatasetId={analyzingDatasetId}
                      analysisResult={analysisResult}
                      onAnalysisComplete={handleAnalysisComplete}
                    />
                  </div>
                )}

                {activeTab === 'chat' && (
                  <div className="h-[calc(100vh-180px)]">
                    {analysisResult ? (
                      // Show analysis results (for upload tab)
                      <div className="h-full overflow-y-auto p-6 bg-white">
                        <div className="max-w-4xl mx-auto">
                          {/* Header with back button */}
                          <div className="mb-6">
                            <button
                              onClick={handleBackToChat}
                              className="text-[#c75b39] hover:text-[#a64a2f] flex items-center gap-1 text-sm mb-3 transition-colors"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                              </svg>
                              返回对话
                            </button>
                            <h2
                              className="text-3xl font-bold text-[#1a1a1a]"
                              style={{ fontFamily: 'var(--font-playfair)' }}
                            >
                              分析报告
                            </h2>
                            <p className="text-gray-600 mt-1">
                              智能分析已完成
                            </p>
                          </div>

                          {/* Analysis results */}
                          {selectedDatasetForView && (
                            <DynamicResultView
                              datasetId={selectedDatasetForView.id}
                              analysisResult={analysisResult}
                            />
                          )}
                        </div>
                      </div>
                    ) : (
                      // Show chat interface (independent query)
                      <div className="bg-white border-l border-r border-[#e8e4df] h-full">
                        <Thread
                          datasets={datasets}
                          onDatasetSelect={handleSelectDataset}
                        />
                      </div>
                    )}
                  </div>
                )}
              </main>

              {/* Footer - only show on browse/upload tabs */}
              {activeTab !== 'chat' && (
                <footer className="border-t border-[#e8e4df] mt-16 py-8">
                  <div className="max-w-7xl mx-auto px-6 text-center text-sm text-gray-500">
                    <p>数据集超市 Dataset Supermarket · 智能数据管理平台</p>
                  </div>
                </footer>
              )}
            </div>
          </ArtifactProvider>
        </StreamProvider>
      </ThreadProvider>
    </React.Suspense>
  );
}
