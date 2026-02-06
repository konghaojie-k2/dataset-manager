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
import { useQueryState } from 'nuqs';

type TabType = 'chat' | 'browse' | 'upload';

export default function HomePage(): React.ReactNode {
  // Tab state - default to chat (智能查询)
  const [activeTab, setActiveTab] = useState<TabType>('chat');
  // Check if there's an active thread (chat in progress)
  const [threadId] = useQueryState("threadId");

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

  // Dataset deleted callback
  const handleDatasetDeleted = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
    // Clear selected dataset if it was deleted
    setSelectedDatasetForView(null);
    setViewingAnalysisResult(null);
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
            <div className="flex flex-col h-screen bg-[#faf8f5] overflow-hidden">
              {/* Combined Header and Tab Navigation - Only show header content on homepage when no active chat */}
              <div className="flex-shrink-0 border-b border-[#e8e4df] bg-white z-40">
                <div className="max-w-7xl mx-auto px-6">
                  {/* Header content - only show when no active chat */}
                  {!threadId && (
                    <div className="pt-6 pb-4 relative">
                      <div className="flex items-center gap-8">
                        {/* Left: Title and description */}
                        <div className="flex-1 min-w-0">
                          <h1
                            className="text-2xl font-bold text-[#1a1a1a] mb-0.5 tracking-tight"
                            style={{ fontFamily: 'var(--font-playfair)' }}
                          >
                            数据集超市
                          </h1>
                          <p className="text-xs text-gray-600 font-light" style={{ fontFamily: 'var(--font-outfit)' }}>
                            发现、探索和分析高质量数据集
                          </p>
                        </div>
                        {/* Center: Tab Navigation - absolutely centered */}
                        <nav className="absolute left-1/2 transform -translate-x-1/2 flex gap-6 flex-shrink-0 items-end justify-center">
                          <button
                            onClick={() => setActiveTab('chat')}
                            className={`
                              relative py-3 px-1 font-medium transition-all duration-300
                              ${activeTab === 'chat'
                                ? 'text-[#1a1a1a]'
                                : 'text-gray-400 hover:text-gray-600'
                              }
                            `}
                            style={{ fontFamily: 'var(--font-playfair)' }}
                          >
                            <span className="text-base">智能查询</span>
                            {activeTab === 'chat' && (
                              <span className="absolute -bottom-4 left-0 right-0 h-0.5 bg-[#c75b39] transform scale-x-100 transition-transform duration-300" />
                            )}
                          </button>
                          <button
                            onClick={() => setActiveTab('browse')}
                            className={`
                              relative py-3 px-1 font-medium transition-all duration-300
                              ${activeTab === 'browse'
                                ? 'text-[#1a1a1a]'
                                : 'text-gray-400 hover:text-gray-600'
                              }
                            `}
                            style={{ fontFamily: 'var(--font-playfair)' }}
                          >
                            <span className="text-base">浏览数据集</span>
                            {activeTab === 'browse' && (
                              <span className="absolute -bottom-4 left-0 right-0 h-0.5 bg-[#c75b39] transform scale-x-100 transition-transform duration-300" />
                            )}
                          </button>
                          <button
                            onClick={() => setActiveTab('upload')}
                            className={`
                              relative py-3 px-1 font-medium transition-all duration-300
                              ${activeTab === 'upload'
                                ? 'text-[#1a1a1a]'
                                : 'text-gray-400 hover:text-gray-600'
                              }
                            `}
                            style={{ fontFamily: 'var(--font-playfair)' }}
                          >
                            <span className="text-base">上传与分析</span>
                            {activeTab === 'upload' && (
                              <span className="absolute -bottom-4 left-0 right-0 h-0.5 bg-[#c75b39] transform scale-x-100 transition-transform duration-300" />
                            )}
                          </button>
                        </nav>
                        {/* Right: Stats */}
                        <div className="hidden md:flex gap-6 text-center flex-1 justify-end">
                          <div>
                            <div className="text-lg font-bold text-[#c75b39]" style={{ fontFamily: 'var(--font-playfair)' }}>
                              1000+
                            </div>
                            <div className="text-xs text-gray-500 uppercase tracking-wide mt-0.5">数据集</div>
                          </div>
                          <div>
                            <div className="text-lg font-bold text-[#7c9885]" style={{ fontFamily: 'var(--font-playfair)' }}>
                              50+
                            </div>
                            <div className="text-xs text-gray-500 uppercase tracking-wide mt-0.5">行业领域</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Tab Navigation - show when threadId exists */}
                  {threadId && (
                    <nav className="flex gap-8 pt-4 pb-4">
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
                  )}
                </div>
              </div>

              {/* Content */}
              {activeTab === 'chat' ? (
                // Chat tab: full width to maintain consistent background
                <main className="flex-1 w-full overflow-hidden">
                  <div className="h-full">
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
                      <div className="h-full">
                        <Thread
                          datasets={datasets}
                          onDatasetSelect={handleSelectDataset}
                        />
                      </div>
                    )}
                  </div>
                </main>
              ) : (
                // Browse and Upload tabs: centered content
                <main className="max-w-7xl mx-auto">
                  {activeTab === 'browse' && (
                    <div className="relative px-6 py-8">
                      <DatasetBrowseTab
                        datasets={datasets}
                        onDatasetSelect={handleSelectDataset}
                        refreshTrigger={refreshTrigger}
                        onDatasetDeleted={handleDatasetDeleted}
                        analyzingId={analyzingDatasetId}
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
                </main>
              )}

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
