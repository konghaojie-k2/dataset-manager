/**
 * 分析进度实时展示组件
 * 显示 Agent 分析的实时进度、步骤列表和中间结果
 */

import React, { useEffect, useState } from 'react';
import { CheckIcon, ClockIcon } from 'lucide-react';
import { agentAPI, datasetAPI, type AnalysisProgress, type AnalysisResult } from '@/lib/api-extension';

interface AnalysisProgressPanelProps {
  datasetId: string;
  onComplete?: (result: AnalysisResult) => void;
}

export function AnalysisProgressPanel({ datasetId, onComplete }: AnalysisProgressPanelProps) {
  const [progress, setProgress] = useState<AnalysisProgress>({
    type: 'analysis_progress',
    dataset_id: datasetId,
    current_step: '初始化中...',
    progress: 0,
    steps_completed: [],
    steps_remaining: ['数据扫描', '特征分析', '执行分析', '生成报告'],
  });

  useEffect(() => {
    let eventSource: EventSource | null = null;

    // 订阅 SSE 进度流
    eventSource = agentAPI.subscribeProgress(
      datasetId,
      (data) => {
        setProgress(data);
      },
      async () => {
        console.log('[ProgressPanel] Analysis complete');
        try {
          // 获取最终分析结果
          const result = await datasetAPI.getAnalysisResults(datasetId);
          onComplete?.(result);
        } catch (error) {
          console.error('[ProgressPanel] Failed to fetch analysis results:', error);
          // 即使获取结果失败，也返回基础结果
          onComplete?.({ dataset_id: datasetId } as any);
        }
      },
      (error) => {
        console.error('[ProgressPanel] Error:', error);
      }
    );

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [datasetId, onComplete]);

  return (
    <div className="space-y-4 p-6 border rounded-lg bg-blue-50">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">分析进度</h3>
        <span className="text-sm text-gray-600">数据集: {datasetId.slice(0, 8)}...</span>
      </div>

      {/* 进度条 */}
      <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
        <div
          className="bg-blue-600 h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progress.progress}%` }}
        />
      </div>

      {/* 进度百分比 */}
      <div className="text-center text-sm font-medium text-gray-700">
        {progress.progress}%
      </div>

      {/* 当前步骤 */}
      <div className="flex items-center gap-2">
        {progress.progress < 100 ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
            <span className="font-medium text-gray-800">{progress.current_step}</span>
          </>
        ) : (
          <span className="font-medium text-green-600">✓ 分析完成！</span>
        )}
      </div>

      {/* 步骤列表 */}
      <div className="grid grid-cols-2 gap-4">
        {/* 已完成 */}
        <div>
          <h4 className="font-semibold text-green-600 mb-2 flex items-center gap-1">
            <CheckIcon className="w-4 h-4" />
            已完成
          </h4>
          {progress.steps_completed.length > 0 ? (
            <ul className="space-y-1">
              {progress.steps_completed.map((step, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-gray-700">
                  <CheckIcon className="w-3 h-3 text-green-600" />
                  {step}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-gray-500">等待开始...</p>
          )}
        </div>

        {/* 待完成 */}
        <div>
          <h4 className="font-semibold text-gray-600 mb-2 flex items-center gap-1">
            <ClockIcon className="w-4 h-4" />
            待完成
          </h4>
          {progress.steps_remaining.length > 0 ? (
            <ul className="space-y-1">
              {progress.steps_remaining.map((step, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-gray-500">
                  <ClockIcon className="w-3 h-3" />
                  {step}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-gray-500">全部完成</p>
          )}
        </div>
      </div>

      {/* 中间结果 */}
      {progress.intermediate_result && (
        <div className="mt-4 p-4 bg-white rounded border">
          <h4 className="font-semibold mb-3">扫描结果</h4>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-gray-500">列数：</span>
              <span className="font-medium ml-2">{progress.intermediate_result.columns_detected}</span>
            </div>
            <div>
              <span className="text-gray-500">行数：</span>
              <span className="font-medium ml-2">{progress.intermediate_result.row_count.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-500">数据类型：</span>
              <span className="font-medium ml-2">
                数值: {progress.intermediate_result.data_types.numeric}
                {', '}分类: {progress.intermediate_result.data_types.categorical}
                {', '}时间: {progress.intermediate_result.data_types.datetime}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 提示信息 */}
      <p className="text-xs text-gray-500 text-center">
        Agent 正在自主分析数据特征，请稍候...
      </p>
    </div>
  );
}
