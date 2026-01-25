/**
 * API 扩展客户端 - 集成 FastAPI Extension 和 LangGraph Agents
 */

// API 基础地址
const API_BASE = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

// Agent ID
const DATA_PROCESSING_AGENT = process.env.NEXT_PUBLIC_DATA_PROCESSING_AGENT || 'data_processing_agent';
const QUERY_AGENT = process.env.NEXT_PUBLIC_QUERY_AGENT || 'query_agent';

// ===== 类型定义 =====

export interface Dataset {
  id: string;
  name: string;
  description: string | null;
  tags: string[];
  industry: string | null;
  file_size: number;
  upload_time: string | null;
  processing_status: string;
  row_count?: number;
  column_count?: number;
}

export interface UploadResult {
  dataset_id: string;
  status: string;
  message: string;
}

export interface AnalysisProgress {
  type: string;
  dataset_id: string;
  current_step: string;
  progress: number;
  steps_completed: string[];
  steps_remaining: string[];
  intermediate_result?: {
    columns_detected: number;
    row_count: number;
    data_types: {
      numeric: number;
      categorical: number;
      datetime: number;
    };
  };
}

export interface AnalysisResult {
  dataset_id: string;
  basic_info: any;
  business_analysis?: any;
  quality_analysis?: any;
  enhanced_analysis?: any;
}

// ===== 数据集 API =====

export const datasetAPI = {
  /**
   * 上传文件
   */
  upload: async (file: File, userInput: string): Promise<UploadResult> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_input', userInput);

    const response = await fetch(`${API_BASE}/api/v1/datasets/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`上传失败: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 上传并触发自动分析
   */
  uploadAndAnalyze: async (file: File, userInput: string): Promise<UploadResult> => {
    // 1. 上传文件
    const uploadResult = await datasetAPI.upload(file, userInput);

    // 2. 触发 Agent 自动分析
    await agentAPI.startAnalysis(uploadResult.dataset_id);

    return uploadResult;
  },

  /**
   * 获取数据集列表
   */
  list: async (): Promise<Dataset[]> => {
    const response = await fetch(`${API_BASE}/api/v1/datasets`);
    if (!response.ok) {
      throw new Error(`获取列表失败: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * 获取数据集详情
   */
  getById: async (datasetId: string): Promise<Dataset> => {
    const response = await fetch(`${API_BASE}/api/v1/datasets/${datasetId}`);
    if (!response.ok) {
      throw new Error(`获取详情失败: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * 删除数据集
   */
  delete: async (datasetId: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/api/v1/datasets/${datasetId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`删除失败: ${response.statusText}`);
    }
  },

  /**
   * 下载文件
   */
  download: async (datasetId: string): Promise<Blob> => {
    const response = await fetch(`${API_BASE}/api/v1/datasets/${datasetId}/download`);
    if (!response.ok) {
      throw new Error(`下载失败: ${response.statusText}`);
    }
    return response.blob();
  },

  /**
   * 获取数据预览
   */
  getPreview: async (datasetId: string, rows: number = 10) => {
    const response = await fetch(`${API_BASE}/api/v1/datasets/${datasetId}/preview?rows=${rows}`);
    if (!response.ok) {
      throw new Error(`获取预览失败: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * 更新标签
   */
  updateTags: async (datasetId: string, tags: string[]) => {
    const response = await fetch(`${API_BASE}/api/v1/datasets/${datasetId}/tags`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tags }),
    });
    if (!response.ok) {
      throw new Error(`更新标签失败: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * 获取业务分析结果
   */
  getBusinessAnalysis: async (datasetId: string) => {
    const response = await fetch(`${API_BASE}/api/v1/datasets/${datasetId}/business-analysis-results`);
    if (!response.ok) {
      throw new Error(`获取业务分析失败: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * 获取质量分析结果
   */
  getQualityAnalysis: async (datasetId: string) => {
    const response = await fetch(`${API_BASE}/api/v1/datasets/${datasetId}/quality-analysis-results`);
    if (!response.ok) {
      throw new Error(`获取质量分析失败: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * 获取增强分析结果
   */
  getEnhancedAnalysis: async (datasetId: string) => {
    const response = await fetch(`${API_BASE}/api/v1/datasets/${datasetId}/enhanced-analysis-results`);
    if (!response.ok) {
      throw new Error(`获取增强分析失败: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * 获取所有分析结果（包括基础信息、业务分析、质量分析、增强分析）
   */
  getAnalysisResults: async (datasetId: string): Promise<AnalysisResult> => {
    const response = await fetch(`${API_BASE}/api/v1/datasets/${datasetId}/analysis-results`);
    if (!response.ok) {
      throw new Error(`获取分析结果失败: ${response.statusText}`);
    }
    return response.json();
  },
};

// ===== Agent API =====

export const agentAPI = {
  /**
   * 启动 Data Processing Agent 分析
   */
  startAnalysis: async (datasetId: string): Promise<any> => {
    const response = await fetch(`${API_BASE}/api/agents/${DATA_PROCESSING_AGENT}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset_id: datasetId }),
    });
    if (!response.ok) {
      throw new Error(`启动分析失败: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Query Agent 查询
   */
  query: async (query: string): Promise<any> => {
    const response = await fetch(`${API_BASE}/api/agents/${QUERY_AGENT}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    if (!response.ok) {
      throw new Error(`查询失败: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * 订阅分析进度流 (SSE)
   * 返回 EventSource
   */
  subscribeProgress: (datasetId: string, onMessage: (data: AnalysisProgress) => void, onComplete?: () => void, onError?: (error: any) => void): EventSource => {
    const eventSource = new EventSource(`${API_BASE}/api/analysis/${datasetId}/progress`);

    eventSource.addEventListener('connected', (e: MessageEvent) => {
      console.log('[SSE] Connected:', e.data);
    });

    eventSource.addEventListener('progress', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        onMessage(data);
      } catch (err) {
        console.error('[SSE] Parse error:', err);
      }
    });

    eventSource.addEventListener('complete', (e: MessageEvent) => {
      console.log('[SSE] Complete:', e.data);
      eventSource.close();
      onComplete?.();
    });

    eventSource.addEventListener('error', (e: MessageEvent) => {
      console.error('[SSE] Error:', e);
      onError?.(e);
      eventSource.close();
    });

    return eventSource;
  },
};

// ===== 其他 API =====

export const tagsAPI = {
  /**
   * 获取所有标签
   */
  list: async () => {
    const response = await fetch(`${API_BASE}/api/v1/tags`);
    if (!response.ok) {
      throw new Error(`获取标签失败: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * 创建标签
   */
  create: async (name: string, color?: string, category?: string) => {
    const response = await fetch(`${API_BASE}/api/v1/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, color, category }),
    });
    if (!response.ok) {
      throw new Error(`创建标签失败: ${response.statusText}`);
    }
    return response.json();
  },
};

export const lineageAPI = {
  /**
   * 获取血缘关系可视化数据
   */
  getVisualization: async (datasetId: string) => {
    const response = await fetch(`${API_BASE}/api/v1/lineage/${datasetId}/graph`);
    if (!response.ok) {
      throw new Error(`获取血缘关系失败: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * 获取上游数据集
   */
  getUpstream: async (datasetId: string) => {
    const response = await fetch(`${API_BASE}/api/v1/lineage/${datasetId}/upstream`);
    if (!response.ok) {
      throw new Error(`获取上游失败: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * 获取下游数据集
   */
  getDownstream: async (datasetId: string) => {
    const response = await fetch(`${API_BASE}/api/v1/lineage/${datasetId}/downstream`);
    if (!response.ok) {
      throw new Error(`获取下游失败: ${response.statusText}`);
    }
    return response.json();
  },
};
