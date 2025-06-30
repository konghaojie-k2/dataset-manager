import {
  DatasetMetadata,
  DatasetPreview,
  ApiResponse,
  Tag,
  UploadRequest,
  MetadataExtractionRequest,
  TagUpdateRequest,
} from '@/types/dataset'

// API基础配置
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

// HTTP客户端类
class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  // 通用请求方法
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // GET请求
  private async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  // POST请求
  private async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  // PUT请求
  private async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  // DELETE请求
  private async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }

  // 文件上传
  private async uploadFile<T>(endpoint: string, formData: FormData): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('File upload failed:', error)
      throw error
    }
  }

  // 数据集相关API
  datasets = {
    // 获取数据集列表
    list: (): Promise<DatasetMetadata[]> => {
      return this.get<DatasetMetadata[]>('/datasets')
    },

    // 获取数据集详情
    get: (id: string): Promise<DatasetMetadata> => {
      return this.get<DatasetMetadata>(`/datasets/${id}`)
    },

    // 上传数据集
    upload: (file: File, userInput?: string): Promise<ApiResponse> => {
      const formData = new FormData()
      formData.append('file', file)
      if (userInput) {
        formData.append('user_input', userInput)
      }
      return this.uploadFile<ApiResponse>('/datasets/upload', formData)
    },

    // 获取数据预览
    preview: (id: string, rows: number = 10): Promise<DatasetPreview> => {
      return this.get<DatasetPreview>(`/datasets/${id}/preview?rows=${rows}`)
    },

    // 提取元数据
    extractMetadata: (request: MetadataExtractionRequest): Promise<ApiResponse> => {
      return this.post<ApiResponse>(`/datasets/${request.dataset_id}/extract-metadata`, request)
    },

    // 更新标签
    updateTags: (request: TagUpdateRequest): Promise<DatasetMetadata> => {
      return this.put<DatasetMetadata>(`/datasets/${request.dataset_id}/tags`, request)
    },

    // 删除数据集
    delete: (id: string): Promise<ApiResponse> => {
      return this.delete<ApiResponse>(`/datasets/${id}`)
    },

    // 启动业务分析
    startBusinessAnalysis: (id: string): Promise<ApiResponse> => {
      return this.post<ApiResponse>(`/datasets/${id}/start-business-analysis`)
    },

    // 启动质量分析
    startQualityAnalysis: (id: string): Promise<ApiResponse> => {
      return this.post<ApiResponse>(`/datasets/${id}/start-quality-analysis`)
    },

    // 获取业务分析结果
    getBusinessAnalysisResults: (id: string): Promise<any> => {
      return this.get<any>(`/datasets/${id}/business-analysis-results`)
    },

    // 获取质量分析结果
    getQualityAnalysisResults: (id: string): Promise<any> => {
      return this.get<any>(`/datasets/${id}/quality-analysis-results`)
    },

    // 下载数据集
    download: (id: string): Promise<Blob> => {
      return fetch(`${this.baseUrl}/datasets/${id}/download`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }
          return response.blob()
        })
    },
  }

  // 标签相关API
  tags = {
    // 获取所有标签
    list: (): Promise<Tag[]> => {
      return this.get<Tag[]>('/tags')
    },

    // 创建标签
    create: (tag: Omit<Tag, 'id' | 'created_at' | 'updated_at' | 'usage_count'>): Promise<Tag> => {
      return this.post<Tag>('/tags', tag)
    },

    // 更新标签
    update: (id: number, tag: Partial<Tag>): Promise<Tag> => {
      return this.put<Tag>(`/tags/${id}`, tag)
    },

    // 删除标签
    delete: (id: number): Promise<ApiResponse> => {
      return this.delete<ApiResponse>(`/tags/${id}`)
    },

    // 获取数据集标签
    getDatasetTags: (datasetId: string): Promise<string[]> => {
      return this.get<string[]>(`/tags/dataset/${datasetId}`)
    },

    // 更新数据集标签
    updateDatasetTags: (datasetId: string, tags: string[]): Promise<ApiResponse> => {
      return this.put<ApiResponse>(`/tags/dataset/${datasetId}`, { tags })
    },
  }

  // 健康检查
  health = {
    check: (): Promise<{ status: string; timestamp: string }> => {
      return this.get<{ status: string; timestamp: string }>('/health')
    },
  }
}

// 导出API客户端实例
export const api = new ApiClient()

// 导出工具函数
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

export const escapeHtml = (text: string): string => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
} 