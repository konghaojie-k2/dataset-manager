import {
  DatasetMetadata,
  DatasetPreview,
  ApiResponse,
  Tag,
  UploadRequest,
  MetadataExtractionRequest,
  TagUpdateRequest,
} from '@/types/dataset'

// API基础配置 - 使用相对路径通过Next.js代理
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
      // 添加超时和重试机制
      signal: AbortSignal.timeout(30000), // 30秒超时
      ...options,
    }

    try {
      const response = await fetch(url, config)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.detail || `HTTP error! status: ${response.status}`

        // 根据状态码提供更友好的错误信息
        if (response.status === 500) {
          throw new Error('服务器内部错误，请稍后重试')
        } else if (response.status === 404) {
          throw new Error('请求的资源不存在')
        } else if (response.status >= 400 && response.status < 500) {
          throw new Error(errorMessage)
        } else {
          throw new Error('网络错误，请检查连接')
        }
      }

      return await response.json()
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('请求超时，请稍后重试')
        }
        console.error('API request failed:', error.message)
        throw error
      } else {
        console.error('API request failed:', error)
        throw new Error('未知错误')
      }
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

    // 根据ID获取数据集详情
    getById: (id: string): Promise<DatasetMetadata> => {
      return this.get<DatasetMetadata>(`/datasets/${id}`)
    },

    // 获取数据集详情
    get: (id: string): Promise<DatasetMetadata> => {
      return this.get<DatasetMetadata>(`/datasets/${id}`)
    },

    // 获取数据集详情（别名）
    getById: (id: string): Promise<DatasetMetadata> => {
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
    getDatasetTags: async (datasetId: string): Promise<string[]> => {
      const response = await this.get<{dataset_id: string, tags: string[]}>(`/tags/datasets/${datasetId}`)
      return response.tags || []
    },

    // 更新数据集标签
    updateDatasetTags: (datasetId: string, tags: string[]): Promise<ApiResponse> => {
      return this.put<ApiResponse>(`/tags/datasets/${datasetId}`, {
        dataset_id: datasetId,
        tag_names: tags
      })
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
  // 使用固定格式避免服务端和客户端不一致
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

export const escapeHtml = (text: string): string => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
} 