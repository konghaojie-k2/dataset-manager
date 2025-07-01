'use client'

import React, { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import rehypeRaw from 'rehype-raw'
import mermaid from 'mermaid'

// 导入代码高亮样式
import 'highlight.js/styles/github.css'

interface MarkdownRendererProps {
  content: string
  className?: string
}

// Mermaid组件
const MermaidDiagram: React.FC<{ chart: string }> = ({ chart }) => {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ref.current) {
      // 初始化mermaid
      mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'loose',
        fontFamily: 'Arial, sans-serif'
      })

      // 生成唯一ID
      const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`
      
      // 渲染图表
      mermaid.render(id, chart).then(({ svg }) => {
        if (ref.current) {
          ref.current.innerHTML = svg
        }
      }).catch((error) => {
        console.error('Mermaid渲染失败:', error)
        if (ref.current) {
          ref.current.innerHTML = `<div class="error">图表渲染失败: ${error.message}</div>`
        }
      })
    }
  }, [chart])

  return (
    <div 
      ref={ref} 
      className="mermaid-diagram my-4 p-4 bg-gray-50 rounded-lg border overflow-x-auto"
    />
  )
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ 
  content, 
  className = '' 
}) => {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeRaw]}
        components={{
          // 自定义代码块渲染
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            const language = match ? match[1] : ''
            
            if (!inline && language === 'mermaid') {
              return <MermaidDiagram chart={String(children).replace(/\n$/, '')} />
            }
            
            return (
              <code className={className} {...props}>
                {children}
              </code>
            )
          },
          // 自定义表格样式
          table({ children }) {
            return (
              <div className="overflow-x-auto my-4">
                <table className="min-w-full divide-y divide-gray-200 border border-gray-300">
                  {children}
                </table>
              </div>
            )
          },
          thead({ children }) {
            return (
              <thead className="bg-gray-50">
                {children}
              </thead>
            )
          },
          th({ children }) {
            return (
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                {children}
              </th>
            )
          },
          td({ children }) {
            return (
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 border-b border-gray-200">
                {children}
              </td>
            )
          },
          // 自定义标题样式
          h1({ children }) {
            return <h1 className="text-3xl font-bold text-gray-900 mb-4 mt-8">{children}</h1>
          },
          h2({ children }) {
            return <h2 className="text-2xl font-semibold text-gray-800 mb-3 mt-6">{children}</h2>
          },
          h3({ children }) {
            return <h3 className="text-xl font-semibold text-gray-800 mb-2 mt-4">{children}</h3>
          },
          h4({ children }) {
            return <h4 className="text-lg font-semibold text-gray-700 mb-2 mt-3">{children}</h4>
          },
          // 自定义段落样式
          p({ children }) {
            return <p className="text-gray-700 leading-relaxed mb-4">{children}</p>
          },
          // 自定义列表样式
          ul({ children }) {
            return <ul className="list-disc list-inside mb-4 space-y-1 text-gray-700">{children}</ul>
          },
          ol({ children }) {
            return <ol className="list-decimal list-inside mb-4 space-y-1 text-gray-700">{children}</ol>
          },
          // 自定义引用样式
          blockquote({ children }) {
            return (
              <blockquote className="border-l-4 border-blue-400 pl-4 py-2 my-4 bg-blue-50 text-gray-700 italic">
                {children}
              </blockquote>
            )
          },
          // 自定义代码样式
          pre({ children }) {
            return (
              <pre className="bg-gray-100 rounded-lg p-4 overflow-x-auto my-4 text-sm">
                {children}
              </pre>
            )
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownRenderer
