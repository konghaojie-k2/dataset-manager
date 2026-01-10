// 数据集状态枚举
export enum DatasetStatus {
  UPLOADED = 'uploaded',
  EXTRACTING = 'extracting',
  BUSINESS_ANALYZING = 'business_analyzing',
  BUSINESS_COMPLETED = 'business_completed',
  QUALITY_ANALYZING = 'quality_analyzing',
  QUALITY_COMPLETED = 'quality_completed',
  ANALYSIS_FAILED = 'analysis_failed',
  ENHANCED_COMPLETED = 'enhanced_completed',
}

// 数据集元数据接口
export interface DatasetMetadata {
  id: string
  name: string
  description?: string
  file_path: string
  file_size: number
  upload_time: string
  tags?: string[]
  industry?: string
  processing_status: DatasetStatus
  created_at: string
  updated_at: string
  columns?: EnhancedDatasetColumn[]
  quality_analysis_results?: QualityAnalysisResults
  business_analysis_results?: BusinessAnalysisResults
  version_type?: string
  original_dataset_id?: string
  version_number?: number

  // 增强分析相关字段
  industrial_domain?: IndustrialDomain
  business_data_types?: BusinessDataType[]
  domain_specific_insights?: DomainSpecificInsights
  important_columns_analysis?: ImportantColumnsAnalysis

  // 数据血缘关系字段
  source_dataset_ids?: string[]
  transformation_type?: TransformationType
  transformation_description?: string
  is_derived_data?: boolean
}

// 增强的数据集列信息
export interface EnhancedDatasetColumn {
  name: string
  type: string
  null_count: number
  unique_count: number
  description?: string
  business_meaning?: string
  is_device_id?: boolean
  is_timestamp?: boolean
  is_key_measurement?: boolean
  is_control_variable?: boolean
  importance_score?: number
  sample_values?: any[]
}

// 工业领域识别结果
export interface IndustrialDomain {
  primary: string
  primary_en: string
  secondary: string[]
  confidence: number
  reasoning: string
}

// 业务数据类型
export interface BusinessDataType {
  type: string
  type_en: string
  confidence: number
  evidence: string[]
}

// 领域特定洞察
export interface DomainSpecificInsights {
  process_type: string
  key_equipment: string[]
  critical_parameters: string[]
  typical_use_cases: string[]
}

// 重要列分析结果
export interface ImportantColumnsAnalysis {
  key_measurement_variables: KeyVariable[]
  control_variables: ControlVariable[]
  other_important_columns?: OtherImportantColumns
  control_loop_insights?: ControlLoopInsight[]
  recommendations?: ColumnRecommendations
}

// 关键变量
export interface KeyVariable {
  column_name: string
  importance_score: number
  category: string
  reasoning: string
  statistics_summary?: {
    mean: number
    std: number
    min: number
    max: number
    variance: number
  }
  business_impact: string
}

// 控制变量
export interface ControlVariable {
  column_name: string
  control_type: string
  importance_score: number
  reasoning: string
  possible_target_variables: string[]
  control_range: string
}

// 其他重要列
export interface OtherImportantColumns {
  device_id_columns: string[]
  timestamp_columns: string[]
  status_columns: string[]
  metadata_columns: string[]
}

// 控制回路洞察
export interface ControlLoopInsight {
  control_loop_id: string
  control_variable: string
  target_variable: string
  relationship_description: string
  correlation: number
}

// 列建议
export interface ColumnRecommendations {
  high_priority_monitoring: string[]
  control_optimization: string[]
  data_quality_improvement: string[]
}

// 数据转换类型
export type TransformationType =
  | 'filter'
  | 'aggregate'
  | 'join'
  | 'derive'
  | 'feature_engineering'

// 数据血缘关系链
export interface LineageChain {
  current_dataset: {
    id: string
    name: string
    is_derived: boolean
    transformation_type?: TransformationType
    transformation_description?: string
  }
  upstream: LineageNode[]
  downstream: LineageNode[]
  generated_at: string
}

// 血缘节点
export interface LineageNode {
  id: string
  name: string
  depth: number
  transformation?: TransformationType
  transformation_description?: string
}

// 血缘可视化数据
export interface LineageVisualizationData {
  nodes: LineageVisNode[]
  edges: LineageVisEdge[]
  metadata: {
    total_nodes: number
    total_edges: number
    generated_at: string
  }
}

// 可视化节点
export interface LineageVisNode {
  id: string
  label: string
  type: 'current' | 'source' | 'derived'
  is_derived?: boolean
  depth?: number
}

// 可视化边
export interface LineageVisEdge {
  from: string
  to: string
  label?: string
  type: string
}

// 质量分析结果
export interface QualityAnalysisResults {
  overall_score: number
  quality_score: number
  completeness: number
  accuracy: number
  consistency: number
  timeliness: number
  recommendations: string[]
}

// 业务分析结果
export interface BusinessAnalysisResults {
  device_time_identification?: string
  business_meaning_analysis?: string
  control_relationships_analysis?: string
  basic_analysis?: string
  detailed_analysis?: string
  insights?: string[]
  recommendations?: string
  columns_metadata?: Array<{
    name: string
    dtype: string
    business_meaning: string
    is_device_id: boolean
    is_timestamp: boolean
    null_count: number
    unique_count: number
    sample_values: any[]
  }>
}

// 数据预览接口
export interface DatasetPreview {
  columns: string[]
  data: any[]
  shape?: [number, number]
  dtypes?: { [key: string]: string }
  total_rows?: number
  preview_rows?: number
}

// API响应接口
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  error?: string
}

// 标签接口
export interface Tag {
  id: number
  name: string
  description?: string
  color?: string
  category?: string
  usage_count: number
  created_at: string
  updated_at: string
}

// 上传请求接口
export interface UploadRequest {
  file: File
  user_input?: string
}

// 元数据提取请求
export interface MetadataExtractionRequest {
  dataset_id: string
  user_input?: string
}

// 标签更新请求
export interface TagUpdateRequest {
  dataset_id: string
  tags: string[]
} 