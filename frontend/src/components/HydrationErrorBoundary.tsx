'use client'

import React, { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

/**
 * Hydration错误边界组件
 * 捕获并处理Hydration相关的错误
 */
class HydrationErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    // 检查是否是Hydration错误
    const isHydrationError = 
      error.message?.includes('Hydration') ||
      error.message?.includes('hydration') ||
      error.message?.includes('server rendered HTML') ||
      error.stack?.includes('hydration')

    if (isHydrationError) {
      console.warn('Hydration error caught by boundary:', error)
      return { hasError: true, error }
    }

    // 对于非Hydration错误，重新抛出
    throw error
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.warn('HydrationErrorBoundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-yellow-800">
              页面正在重新加载以修复显示问题...
            </p>
          </div>
        )
      )
    }

    return this.props.children
  }
}

export default HydrationErrorBoundary
