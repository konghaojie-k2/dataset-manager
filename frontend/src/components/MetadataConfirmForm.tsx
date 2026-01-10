'use client'

import React, { useState, useEffect } from 'react'
import {
  DatasetMetadata,
  IndustrialDomain,
  BusinessDataType,
  ImportantColumnsAnalysis,
  EnhancedDatasetColumn,
  TransformationType,
} from '@/types/dataset'
import { api } from '@/lib/api'

interface MetadataConfirmFormProps {
  dataset: DatasetMetadata
  onConfirm: (updatedData: Partial<DatasetMetadata>) => void
  onCancel: () => void
  loading?: boolean
}

// 工业领域选项
const INDUSTRIAL_DOMAINS = [
  '半导体制造',
  '化工/石化',
  '能源/电力',
  '汽车制造',
  '食品饮料',
  '医药制药',
  '钢铁冶金',
  '纺织印染',
  '3C电子制造',
  '通用制造',
]

// 业务数据类型选项
const BUSINESS_DATA_TYPES = [
  '设备运行数据',
  '生产数据',
  '质量检测数据',
  '设备日志数据',
  '维护记录数据',
  '工艺参数数据',
  '能源消耗数据',
  '环境监测数据',
]

// 转换类型选项
const TRANSFORMATION_TYPES: { value: TransformationType; label: string }[] = [
  { value: 'filter', label: '过滤' },
  { value: 'aggregate', label: '聚合' },
  { value: 'join', label: '连接' },
  { value: 'derive', label: '派生' },
  { value: 'feature_engineering', label: '特征工程' },
]

export default function MetadataConfirmForm({
  dataset,
  onConfirm,
  onCancel,
  loading = false,
}: MetadataConfirmFormProps) {
  // 本地状态
  const [industrialDomain, setIndustrialDomain] = useState<string>(
    dataset.industrial_domain?.primary || dataset.industry || ''
  )
  const [selectedBusinessTypes, setSelectedBusinessTypes] = useState<string[]>(
    dataset.business_data_types?.map((t) => t.type) || []
  )
  const [columns, setColumns] = useState<EnhancedDatasetColumn[]>(
    dataset.columns || []
  )
  const [availableDatasets, setAvailableDatasets] = useState<DatasetMetadata[]>([])

  // 血缘关系状态
  const [isDerivedData, setIsDerivedData] = useState<boolean>(
    dataset.is_derived_data || false
  )
  const [sourceDatasetIds, setSourceDatasetIds] = useState<string[]>(
    dataset.source_dataset_ids || []
  )
  const [transformationType, setTransformationType] = useState<TransformationType>(
    dataset.transformation_type || 'derive'
  )
  const [transformationDescription, setTransformationDescription] = useState(
    dataset.transformation_description || ''
  )

  // 加载可用数据集列表
  useEffect(() => {
    const loadDatasets = async () => {
      try {
        const datasets = await api.datasets.list()
        // 排除当前数据集
        const filtered = datasets.filter((d) => d.id !== dataset.id)
        setAvailableDatasets(filtered)
      } catch (error) {
        console.error('加载数据集列表失败:', error)
      }
    }
    loadDatasets()
  }, [dataset.id])

  // 切换业务类型
  const toggleBusinessType = (type: string) => {
    setSelectedBusinessTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }

  // 更新列属性
  const updateColumn = (columnName: string, updates: Partial<EnhancedDatasetColumn>) => {
    setColumns((prev) =>
      prev.map((col) =>
        col.name === columnName ? { ...col, ...updates } : col
      )
    )
  }

  // 切换源数据集
  const toggleSourceDataset = (datasetId: string) => {
    setSourceDatasetIds((prev) =>
      prev.includes(datasetId)
        ? prev.filter((id) => id !== datasetId)
        : [...prev, datasetId]
    )
  }

  // 提交表单
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // 构建更新后的数据
    const updatedData: Partial<DatasetMetadata> = {
      ...dataset,
      industrial_domain: {
        primary: industrialDomain,
        primary_en: '', // 可以映射或留空
        secondary: [],
        confidence: 1.0,
        reasoning: '用户确认',
      },
      business_data_types: selectedBusinessTypes.map((type) => ({
        type,
        type_en: '',
        confidence: 1.0,
        evidence: [],
      })),
      columns,
      is_derived_data: isDerivedData,
      source_dataset_ids: isDerivedData ? sourceDatasetIds : [],
      transformation_type: isDerivedData ? transformationType : undefined,
      transformation_description: isDerivedData ? transformationDescription : undefined,
    }

    onConfirm(updatedData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 p-6 bg-white rounded-lg shadow">
      {/* 标题 */}
      <div className="border-b pb-4">
        <h2 className="text-xl font-semibold text-gray-900">
          确认元数据信息
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          请检查并修正自动识别的元数据信息
        </p>
      </div>

      {/* 工业领域 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          工业领域
        </label>
        <select
          value={industrialDomain}
          onChange={(e) => setIndustrialDomain(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">请选择工业领域</option>
          {INDUSTRIAL_DOMAINS.map((domain) => (
            <option key={domain} value={domain}>
              {domain}
            </option>
          ))}
        </select>
        {dataset.industrial_domain?.reasoning && (
          <p className="mt-1 text-xs text-gray-500">
            AI判断依据: {dataset.industrial_domain.reasoning}
          </p>
        )}
      </div>

      {/* 业务数据类型 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          业务数据类型（可多选）
        </label>
        <div className="grid grid-cols-2 gap-2">
          {BUSINESS_DATA_TYPES.map((type) => (
            <label key={type} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedBusinessTypes.includes(type)}
                onChange={() => toggleBusinessType(type)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">{type}</span>
            </label>
          ))}
        </div>
      </div>

      {/* 重要列信息 */}
      {dataset.important_columns_analysis && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            重要列识别结果
          </h3>

          {/* 关键观测量 */}
          <div className="mb-4">
            <h4 className="text-xs font-medium text-gray-600 mb-2">
              关键观测量 ({dataset.important_columns_analysis.key_measurement_variables?.length || 0})
            </h4>
            <div className="space-y-2 max-h-40 overflow-y-auto border rounded p-2">
              {dataset.important_columns_analysis.key_measurement_variables?.map((kv) => (
                <div key={kv.column_name} className="flex items-center justify-between text-sm">
                  <span className="font-medium">{kv.column_name}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-500">
                      重要性: {(kv.importance_score * 100).toFixed(0)}%
                    </span>
                    <input
                      type="checkbox"
                      checked={columns.find((c) => c.name === kv.column_name)?.is_key_measurement || false}
                      onChange={(e) =>
                        updateColumn(kv.column_name, {
                          is_key_measurement: e.target.checked,
                          importance_score: kv.importance_score,
                        })
                      }
                      className="rounded border-gray-300 text-blue-600"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 控制量 */}
          <div className="mb-4">
            <h4 className="text-xs font-medium text-gray-600 mb-2">
              控制量 ({dataset.important_columns_analysis.control_variables?.length || 0})
            </h4>
            <div className="space-y-2 max-h-40 overflow-y-auto border rounded p-2">
              {dataset.important_columns_analysis.control_variables?.map((cv) => (
                <div key={cv.column_name} className="flex items-center justify-between text-sm">
                  <span className="font-medium">{cv.column_name}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">{cv.control_type}</span>
                    <input
                      type="checkbox"
                      checked={columns.find((c) => c.name === cv.column_name)?.is_control_variable || false}
                      onChange={(e) =>
                        updateColumn(cv.column_name, {
                          is_control_variable: e.target.checked,
                          importance_score: cv.importance_score,
                        })
                      }
                      className="rounded border-gray-300 text-green-600"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 控制回路洞察 */}
          {dataset.important_columns_analysis.control_loop_insights &&
            dataset.important_columns_analysis.control_loop_insights.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-gray-600 mb-2">
                  控制回路关系 ({dataset.important_columns_analysis.control_loop_insights.length})
                </h4>
                <div className="space-y-1 max-h-32 overflow-y-auto border rounded p-2 bg-blue-50">
                  {dataset.important_columns_analysis.control_loop_insights.map((loop, idx) => (
                    <div key={idx} className="text-xs text-gray-700">
                      <span className="font-medium">{loop.control_variable}</span>
                      {' → '}
                      <span className="font-medium">{loop.target_variable}</span>
                      <span className="text-gray-500 ml-2">
                        (相关: {loop.correlation.toFixed(2)})
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
        </div>
      )}

      {/* 血缘关系 */}
      <div className="border-t pt-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-700">数据血缘关系</h3>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={isDerivedData}
              onChange={(e) => setIsDerivedData(e.target.checked)}
              className="rounded border-gray-300 text-blue-600"
            />
            <span className="text-xs text-gray-600">这是派生数据</span>
          </label>
        </div>

        {isDerivedData && (
          <div className="space-y-3 pl-4 border-l-2 border-blue-200">
            {/* 源数据集选择 */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                源数据集（可多选）
              </label>
              <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto border rounded p-2">
                {availableDatasets.map((ds) => (
                  <label key={ds.id} className="flex items-center space-x-2 text-sm">
                    <input
                      type="checkbox"
                      checked={sourceDatasetIds.includes(ds.id)}
                      onChange={() => toggleSourceDataset(ds.id)}
                      className="rounded border-gray-300 text-blue-600"
                    />
                    <span className="truncate" title={ds.name}>
                      {ds.name}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* 转换类型 */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                转换类型
              </label>
              <select
                value={transformationType}
                onChange={(e) => setTransformationType(e.target.value as TransformationType)}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {TRANSFORMATION_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 转换描述 */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                转换描述
              </label>
              <textarea
                value={transformationDescription}
                onChange={(e) => setTransformationDescription(e.target.value)}
                placeholder="描述如何从源数据生成此数据集"
                rows={2}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* 按钮 */}
      <div className="flex justify-end space-x-3 border-t pt-4">
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50"
        >
          取消
        </button>
        <button
          type="submit"
          disabled={loading || !industrialDomain}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {loading ? '保存中...' : '确认并保存'}
        </button>
      </div>
    </form>
  )
}
