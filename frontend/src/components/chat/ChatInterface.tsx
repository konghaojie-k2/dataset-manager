/**
 * 聊天界面组件
 * 提供用户与LLM对话的界面（支持A2UI表单）
 */

'use client'

import React, { useState, useRef, useEffect } from 'react'
import { api } from '@/lib/api'
import { ChatMessage, DatasetSearchResult } from '@/types/chat'
import { A2UISchema, A2UIFormData } from '@/types/a2ui'
import DynamicFormRenderer from '@/components/a2ui/DynamicFormRenderer'

interface ChatInterfaceProps {
  onDatasetClick?: (dataset: DatasetSearchResult) => void
}

export default function ChatInterface({ onDatasetClick }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState('new')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 发送消息
  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setIsLoading(true)

    // 添加用户消息到界面
    const tempUserMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
      session_id: sessionId,
    }
    setMessages((prev) => [...prev, tempUserMessage])

    try {
      // 调用后端API
      const response = await api.chat.send({
        session_id: sessionId,
        content: userMessage,
      })

      // 更新会话ID
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id)
      }

      // 添加助手消息到界面
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.message,
        timestamp: response.timestamp,
        session_id: response.session_id,
        datasets: response.datasets || [],
        a2ui_form: response.a2ui_form,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('发送消息失败:', error)
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: `错误: ${error instanceof Error ? error.message : '未知错误'}`,
        timestamp: new Date().toISOString(),
        session_id: sessionId,
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // 处理A2UI表单提交
  const handleFormSubmit = async (formData: A2UIFormData) => {
    setIsLoading(true)

    // 构建用户消息（基于表单数据）
    const formMessage = `根据表单数据搜索: ${JSON.stringify(formData)}`

    // 添加用户消息到界面
    const tempUserMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: formMessage,
      timestamp: new Date().toISOString(),
      session_id: sessionId,
    }
    setMessages((prev) => [...prev, tempUserMessage])

    try {
      // 调用后端API（将表单数据作为content传递）
      const response = await api.chat.send({
        session_id: sessionId,
        content: formMessage,
      })

      // 更新会话ID
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id)
      }

      // 添加助手消息到界面
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.message,
        timestamp: response.timestamp,
        session_id: response.session_id,
        datasets: response.datasets || [],
        a2ui_form: response.a2ui_form,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('提交表单失败:', error)
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: `错误: ${error instanceof Error ? error.message : '未知错误'}`,
        timestamp: new Date().toISOString(),
        session_id: sessionId,
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  // 处理A2UI表单取消
  const handleFormCancel = () => {
    // 可以在这里添加取消逻辑，比如关闭表单或显示取消消息
    console.log('用户取消了表单填写')
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <p className="text-lg mb-2">欢迎使用数据超市</p>
            <p className="text-sm">输入您想要搜索的数据集类型，例如：</p>
            <div className="mt-4 space-y-2">
              <button
                className="block w-full text-left px-4 py-2 bg-white rounded-lg hover:bg-gray-100 transition"
                onClick={() => setInput('显示所有半导体传感器数据')}
              >
                显示所有半导体传感器数据
              </button>
              <button
                className="block w-full text-left px-4 py-2 bg-white rounded-lg hover:bg-gray-100 transition"
                onClick={() => setInput('找化工领域的生产数据')}
              >
                找化工领域的生产数据
              </button>
              <button
                className="block w-full text-left px-4 py-2 bg-white rounded-lg hover:bg-gray-100 transition"
                onClick={() => setInput('温度和压力相关的质量检测数据')}
              >
                温度和压力相关的质量检测数据
              </button>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.role === 'system'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-white text-gray-800 shadow'
              }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>

              {/* 显示A2UI表单 */}
              {message.a2ui_form && (
                <div className="mt-3">
                  <DynamicFormRenderer
                    schema={message.a2ui_form as A2UISchema}
                    onSubmit={handleFormSubmit}
                    onCancel={handleFormCancel}
                  />
                </div>
              )}

              {/* 显示数据集结果 */}
              {message.datasets && message.datasets.length > 0 && (
                <div className="mt-3 space-y-2">
                  {message.datasets.map((dataset) => (
                    <div
                      key={dataset.id}
                      className="bg-gray-50 rounded p-3 hover:bg-gray-100 cursor-pointer transition"
                      onClick={() => onDatasetClick?.(dataset)}
                    >
                      <div className="font-medium text-gray-900">{dataset.name}</div>
                      <div className="text-sm text-gray-600 mt-1 line-clamp-2">
                        {dataset.description}
                      </div>
                      <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                        <span>相关度: {dataset.relevance_score ? (dataset.relevance_score * 100).toFixed(0) : 'N/A'}%</span>
                        {dataset.tags && dataset.tags.length > 0 && (
                          <span>• {dataset.tags.slice(0, 2).join(', ')}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* 显示时间戳 */}
              <div className="text-xs opacity-70 mt-1">
                {new Date(message.timestamp).toLocaleTimeString('zh-CN', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-lg px-4 py-2 shadow">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <div className="border-t bg-white p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入您想要搜索的数据集类型..."
            className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  )
}
