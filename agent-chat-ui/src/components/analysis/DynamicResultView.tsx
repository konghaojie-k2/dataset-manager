/**
 * 动态结果展示组件
 * 根据不同数据集的分析结果，动态渲染不同的内容
 */

import React, { useState } from 'react';
import { datasetAPI, type AnalysisResult } from '@/lib/api-extension';
import { MarkdownRenderer } from '@/components/ui/markdown-renderer';
import { LineageGraph, LineageList } from '@/components/visualization/LineageGraph';

interface DynamicResultViewProps {
  datasetId: string;
  analysisResult: AnalysisResult;
}

export function DynamicResultView({ datasetId, analysisResult }: DynamicResultViewProps) {
  return (
    <div className="space-y-4">
      {/* === 基础信息（始终显示）=== */}
      <section className="bg-gradient-to-br from-blue-50 to-white border border-blue-100 rounded-xl p-5 shadow-sm">
        <h3 className="text-base font-semibold mb-6 pb-3 text-gray-800 flex items-center gap-2 border-b border-blue-200">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          数据概览
        </h3>
        <DataOverview data={analysisResult.basic_info} />
      </section>

      {/* === 动态内容（根据分析结果）=== */}

      {/* 业务分析结果 */}
      {analysisResult.business_analysis && (
        <section className="bg-white border border-blue-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold mb-6 pb-3 text-blue-700 flex items-center gap-2 border-b border-blue-200">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            业务分析
          </h3>
          <BusinessAnalysisView data={analysisResult.business_analysis} />
        </section>
      )}

      {/* 质量分析结果 */}
      {analysisResult.quality_analysis && (
        <section className="bg-white border border-purple-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold mb-6 pb-3 text-purple-700 flex items-center gap-2 border-b border-purple-200">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            数据质量
          </h3>
          <QualityAnalysisView data={analysisResult.quality_analysis} />
        </section>
      )}

      {/* 增强分析结果 */}
      {analysisResult.enhanced_analysis && (
        <section className="bg-white border border-green-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold mb-6 pb-3 text-green-700 flex items-center gap-2 border-b border-green-200">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            智能洞察
          </h3>
          <EnhancedAnalysisView data={analysisResult.enhanced_analysis} />
        </section>
      )}

      {/* === 操作区（始终显示）=== */}
      <section className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-base font-semibold mb-6 pb-3 text-gray-800 flex items-center gap-2 border-b border-gray-200">
          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
          操作
        </h3>
        <ActionButtons datasetId={datasetId} />
      </section>
    </div>
  );
}

// 子组件：数据概览
function DataOverview({ data }: { data: any }) {
  if (!data) return <p className="text-gray-500">暂无概览数据</p>;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {data.row_count && (
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{data.row_count.toLocaleString()}</div>
          <div className="text-sm text-gray-500">总行数</div>
        </div>
      )}
      {data.column_count && (
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{data.column_count}</div>
          <div className="text-sm text-gray-500">总列数</div>
        </div>
      )}
      {data.file_size && (
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{(data.file_size / 1024).toFixed(1)} KB</div>
          <div className="text-sm text-gray-500">文件大小</div>
        </div>
      )}
      {data.upload_time && (
        <div className="text-center">
          <div className="text-sm font-bold text-gray-900">
            {new Date(data.upload_time).toLocaleDateString()}
          </div>
          <div className="text-sm text-gray-500">上传时间</div>
        </div>
      )}
    </div>
  );
}

// 子组件：业务分析
function BusinessAnalysisView({ data }: { data: any }) {
  return (
    <div className="space-y-4">
      {/* 设备识别 */}
      {data.device_columns && data.device_columns.length > 0 && (
        <div className="mt-6 pt-4 border-t border-blue-100 first:mt-0 first:pt-0 first:border-t-0">
          <h4 className="font-semibold text-blue-600 mb-3 pb-2 border-b border-blue-200">设备列识别</h4>
          <div className="flex flex-wrap gap-2">
            {data.device_columns.map((col: any, i: number) => (
              <span
                key={i}
                className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
              >
                {col.name} ({col.confidence})
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 时间列 */}
      {data.time_columns && data.time_columns.length > 0 && (
        <div className="mt-6 pt-4 border-t border-blue-100 first:mt-0 first:pt-0 first:border-t-0">
          <h4 className="font-semibold text-blue-600 mb-3 pb-2 border-b border-blue-200">时间列识别</h4>
          <div className="flex flex-wrap gap-2">
            {data.time_columns.map((col: any, i: number) => (
              <span
                key={i}
                className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
              >
                {col.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 业务含义 */}
      {data.business_meaning && (
        <div className="mt-6 pt-4 border-t border-blue-100 first:mt-0 first:pt-0 first:border-t-0">
          <h4 className="font-semibold text-blue-600 mb-3 pb-2 border-b border-blue-200">业务含义</h4>
          <MarkdownRenderer content={data.business_meaning} />
        </div>
      )}

      {/* 控制逻辑 */}
      {data.control_logic && (
        <div className="mt-6 pt-4 border-t border-blue-100 first:mt-0 first:pt-0 first:border-t-0">
          <h4 className="font-semibold text-blue-600 mb-3 pb-2 border-b border-blue-200">控制逻辑</h4>
          <MarkdownRenderer content={data.control_logic} />
        </div>
      )}
    </div>
  );
}

// 子组件：质量分析
function QualityAnalysisView({ data }: { data: any }) {
  return (
    <div className="space-y-4">
      {/* 质量评分 */}
      {data.overall_score !== undefined && (
        <div>
          <div className="flex items-center gap-4 mb-4">
            <div className="text-center">
              <div className="text-4xl font-bold text-gray-900">{data.overall_score}</div>
              <div className="text-sm text-gray-500">质量评分</div>
            </div>
            {data.quality_level && (
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  data.overall_score >= 80
                    ? 'bg-green-100 text-green-800'
                    : data.overall_score >= 60
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {data.quality_level}
              </span>
            )}
          </div>
        </div>
      )}

      {/* 各维度评分 */}
      {(data.completeness !== undefined || data.accuracy !== undefined || data.consistency !== undefined || data.timeliness !== undefined) && (
        <div className="mt-6 pt-4 border-t border-purple-100 first:mt-0 first:pt-0 first:border-t-0">
          <h4 className="font-semibold text-purple-600 mb-3 pb-2 border-b border-purple-200">各维度评分</h4>
          <div className="grid grid-cols-2 gap-4">
            {data.completeness !== undefined && (
              <ScoreBar label="完整性" score={data.completeness} />
            )}
            {data.accuracy !== undefined && (
              <ScoreBar label="准确性" score={data.accuracy} />
            )}
            {data.consistency !== undefined && (
              <ScoreBar label="一致性" score={data.consistency} />
            )}
            {data.timeliness !== undefined && (
              <ScoreBar label="时效性" score={data.timeliness} />
            )}
          </div>
        </div>
      )}

      {/* 关键问题 */}
      {data.key_issues && data.key_issues.length > 0 && (
        <div className="mt-6 pt-4 border-t border-purple-100 first:mt-0 first:pt-0 first:border-t-0">
          <h4 className="font-semibold text-red-600 mb-3 pb-2 border-b border-red-200">关键问题</h4>
          <ul className="space-y-1">
            {data.key_issues.map((issue: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="text-red-500 mt-0.5">•</span>
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 改进建议 */}
      {data.recommendations && data.recommendations.length > 0 && (
        <div className="mt-6 pt-4 border-t border-purple-100 first:mt-0 first:pt-0 first:border-t-0">
          <h4 className="font-semibold text-green-600 mb-3 pb-2 border-b border-green-200">改进建议</h4>
          <ul className="space-y-1">
            {data.recommendations.map((rec: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="text-green-500 mt-0.5">✓</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// 子组件：增强分析
function EnhancedAnalysisView({ data }: { data: any }) {
  return (
    <div className="space-y-4">
      {/* 工业领域 */}
      {data.industrial_domain && (
        <div className="mt-6 pt-4 border-t border-green-100 first:mt-0 first:pt-0 first:border-t-0">
          <h4 className="font-semibold text-green-600 mb-3 pb-2 border-b border-green-200">工业领域</h4>
          <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
            {data.industrial_domain}
          </span>
        </div>
      )}

      {/* 业务数据类型 */}
      {data.business_data_types && data.business_data_types.length > 0 && (
        <div className="mt-6 pt-4 border-t border-green-100 first:mt-0 first:pt-0 first:border-t-0">
          <h4 className="font-semibold text-green-600 mb-3 pb-2 border-b border-green-200">业务数据类型</h4>
          <div className="flex flex-wrap gap-2">
            {data.business_data_types.map((type: string, i: number) => (
              <span
                key={i}
                className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
              >
                {type}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 重要列 */}
      {data.important_columns && (
        <div className="mt-6 pt-4 border-t border-green-100 first:mt-0 first:pt-0 first:border-t-0">
          <h4 className="font-semibold text-green-600 mb-3 pb-2 border-b border-green-200">重要列识别</h4>
          <MarkdownRenderer content={data.important_columns} />
        </div>
      )}
    </div>
  );
}

// 子组件：评分条
function ScoreBar({ label, score }: { label: string; score: number }) {
  const getColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium">{score}/100</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className={`h-2 rounded-full transition-all ${getColor(score)}`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

// 子组件：操作按钮
function ActionButtons({ datasetId }: { datasetId: string }) {
  const [showLineage, setShowLineage] = useState(false);

  const handleDownload = async () => {
    try {
      const blob = await datasetAPI.download(datasetId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dataset-${datasetId}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      alert('下载失败');
    }
  };

  const handleQueryData = () => {
    // 切换到聊天模式询问数据
    // 这可以通过父组件传递的回调来实现
    alert('询问数据功能开发中...');
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <button
          onClick={handleDownload}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all hover:shadow-md font-medium text-sm"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          下载数据
        </button>
        <button
          onClick={() => setShowLineage(!showLineage)}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all hover:shadow-md font-medium text-sm"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          {showLineage ? '隐藏血缘' : '查看血缘'}
        </button>
        <button
          onClick={handleQueryData}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all hover:shadow-md font-medium text-sm"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          询问数据
        </button>
      </div>

      {/* 血缘关系展示 */}
      {showLineage && (
        <div className="mt-4 border border-purple-200 rounded-lg p-4 bg-purple-50/50">
          <h4 className="text-base font-semibold mb-4 text-purple-900">数据血缘关系</h4>
          <LineageGraph datasetId={datasetId} />
        </div>
      )}
    </div>
  );
}
