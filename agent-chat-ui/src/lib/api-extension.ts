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
  steps_completed: string | string[];  // 可以是字符串（逗号分隔）或数组
  steps_remaining: string | string[];
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
      // 尝试从响应体中获取详细错误信息
      let errorMessage = `上传失败: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        }
      } catch (e) {
        // 如果无法解析 JSON，使用默认错误信息
        console.warn('无法解析错误响应:', e);
      }

      throw new Error(errorMessage);
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
   * 支持心跳检测和自动重连
   * 返回 EventSource
   */
  subscribeProgress: (datasetId: string, onMessage: (data: AnalysisProgress) => void, onComplete?: () => void, onError?: (error: any) => void): EventSource => {
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const baseReconnectDelay = 1000;
    let heartbeatTimeout: ReturnType<typeof setTimeout> | null = null;
    let isCompleted = false;

    const createEventSource = () => {
      const eventSource = new EventSource(`${API_BASE}/api/analysis/${datasetId}/progress`);

      // 连接成功
      eventSource.addEventListener('connected', (e: MessageEvent) => {
        console.log('[SSE] Connected:', e.data);
        reconnectAttempts = 0; // 重置重连计数
        isCompleted = false;
      });

      // 心跳事件
      eventSource.addEventListener('heartbeat', (e: MessageEvent) => {
        console.debug('[SSE] Heartbeat:', e.data);
        // 清除之前的心跳超时
        if (heartbeatTimeout) {
          clearTimeout(heartbeatTimeout);
        }
        // 设置新的心跳超时（如果超过10秒没有心跳则重连）
        heartbeatTimeout = setTimeout(() => {
          console.warn('[SSE] No heartbeat for 10s, reconnecting...');
          eventSource.close();
          attemptReconnect();
        }, 10000);
      });

      // 进度事件
      eventSource.addEventListener('progress', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);

          // 转换 steps_completed 和 steps_remaining：如果字符串则分割为数组
          if (typeof data.steps_completed === 'string') {
            data.steps_completed = data.steps_completed
              .split(',')
              .map((s: string) => s.trim())
              .filter((s: string) => s && s !== '无');
          }
          if (typeof data.steps_remaining === 'string') {
            data.steps_remaining = data.steps_remaining
              .split(',')
              .map((s: string) => s.trim())
              .filter((s: string) => s && s !== '无');
          }

          // 解析 intermediate_result（如果是 JSON 字符串）
          if (typeof data.intermediate_result === 'string') {
            try {
              data.intermediate_result = JSON.parse(data.intermediate_result);
            } catch {
              data.intermediate_result = undefined;
            }
          }

          onMessage(data);
        } catch (err) {
          console.error('[SSE] Parse error:', err);
          onError?.(new Error('Failed to parse progress data'));
        }
      });

      // 完成事件
      eventSource.addEventListener('complete', (e: MessageEvent) => {
        console.log('[SSE] Complete:', e.data);
        isCompleted = true;
        if (heartbeatTimeout) {
          clearTimeout(heartbeatTimeout);
        }
        eventSource.close();
        onComplete?.();
      });

      // 自定义 error 事件（后端发送的业务错误）
      eventSource.addEventListener('error', (e: MessageEvent) => {
        if (isCompleted) return; // 已完成时不处理

        try {
          const errorData = JSON.parse(e.data);
          console.error('[SSE] Business Error:', errorData);
          onError?.(new Error(errorData.error || 'Unknown error'));
        } catch {
          console.error('[SSE] Error:', e.data);
          onError?.(new Error('Unknown error'));
        }
        eventSource.close();
      });

      // EventSource 内置错误（网络错误、连接断开等）
      eventSource.onerror = (evt) => {
        if (isCompleted) return; // 已完成时不处理

        console.error('[SSE] Connection Error:', evt);
        eventSource.close();
        attemptReconnect();
      };

      return eventSource;
    };

    // 重连逻辑
    const attemptReconnect = () => {
      if (isCompleted) return;
      if (reconnectAttempts >= maxReconnectAttempts) {
        console.error('[SSE] Max reconnect attempts reached');
        onError?.(new Error('SSE connection failed after max attempts'));
        return;
      }

      reconnectAttempts++;
      const delay = baseReconnectDelay * Math.pow(2, reconnectAttempts - 1); // 指数退避
      console.log(`[SSE] Attempting reconnect ${reconnectAttempts}/${maxReconnectAttempts} in ${delay}ms...`);

      setTimeout(() => {
        if (!isCompleted) {
          createEventSource();
        }
      }, delay);
    };

    // 创建 EventSource
    return createEventSource();
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
