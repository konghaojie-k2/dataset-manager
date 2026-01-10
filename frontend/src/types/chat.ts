/**
 * 聊天相关的类型定义
 */

import { A2UISchema } from './a2ui'

/**
 * 消息角色
 */
export type MessageRole = 'user' | 'assistant' | 'system'

/**
 * 响应类型
 */
export type ResponseType =
  | 'search_results'
  | 'clarification_needed'
  | 'error'
  | 'info'

/**
 * 数据集搜索结果
 */
export interface DatasetSearchResult {
  id: string
  name: string
  description: string
  tags: string[]
  industry?: string
  file_size: number
  upload_time: string
  processing_status: string
  relevance_score: number
}

/**
 * 聊天消息
 */
export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: string
  session_id: string
  datasets?: DatasetSearchResult[]
  a2ui_form?: A2UISchema
  metadata?: Record<string, any>
}

/**
 * 搜索意图
 */
export interface SearchIntent {
  search_query: string
  entities: Record<string, any>
  filters: Record<string, any>
  needs_clarification: boolean
  clarification_reason?: string
  confidence: number
}

/**
 * 聊天响应
 */
export interface ChatResponse {
  type: ResponseType
  message: string
  datasets: DatasetSearchResult[]
  a2ui_form?: A2UISchema
  session_id: string
  timestamp: string
  total_results?: number
  search_query?: string
  relevance_scores?: number[]
}

/**
 * 聊天请求
 */
export interface ChatRequest {
  session_id: string
  content: string
  timestamp?: string
}

/**
 * 聊天会话
 */
export interface ChatSession {
  session_id: string
  messages: ChatMessage[]
  created_at: string
  updated_at: string
  search_history: SearchHistoryEntry[]
  current_context: Record<string, any>
  user_preferences: Record<string, any>
}

/**
 * 搜索历史条目
 */
export interface SearchHistoryEntry {
  query: string
  count: number
  dataset_ids: string[]
  timestamp: string
}

/**
 * 推荐提示词
 */
export interface SuggestedPrompt {
  id: string
  label: string
  query: string
  icon?: string
}
