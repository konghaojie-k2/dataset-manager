// 数据集状态枚举
export enum DatasetStatus {
  UPLOADED = 'uploaded',
  EXTRACTING = 'extracting',
  BUSINESS_ANALYZING = 'business_analyzing',
  BUSINESS_COMPLETED = 'business_completed',
  QUALITY_ANALYZING = 'quality_analyzing',
  QUALITY_COMPLETED = 'quality_completed',
  ANALYSIS_FAILED = 'analysis_failed',
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
  columns?: DatasetColumn[]
  quality_analysis_results?: QualityAnalysisResults
  business_analysis_results?: BusinessAnalysisResults
  version_type?: string
  original_dataset_id?: string
  version_number?: number
}

// 数据集列信息
export interface DatasetColumn {
  name: string
  type: string
  null_count: number
  unique_count: number
  description?: string
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
  device_id_column?: string
  time_column?: string
  business_meaning: string
  control_relationships: string[]
  insights: string[]
}

// 数据预览接口
export interface DatasetPreview {
  columns: string[]
  data: any[][]
  total_rows: number
  preview_rows: number
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