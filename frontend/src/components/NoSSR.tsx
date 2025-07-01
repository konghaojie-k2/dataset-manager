'use client'

import React, { useState, useEffect, ReactNode } from 'react'

interface NoSSRProps {
  children: ReactNode
  fallback?: ReactNode
  suppressHydrationWarning?: boolean
}

/**
 * NoSSR组件 - 防止服务端渲染，避免hydration不匹配
 * 只在客户端渲染子组件
 */
const NoSSR: React.FC<NoSSRProps> = ({
  children,
  fallback = null,
  suppressHydrationWarning = true
}) => {
  const [isClient, setIsClient] = useState(false)
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsClient(true)
    // 添加额外的挂载检查
    const timer = setTimeout(() => {
      setIsMounted(true)
    }, 0)

    return () => clearTimeout(timer)
  }, [])

  // 在服务端或客户端未完全挂载时显示fallback
  if (!isClient || !isMounted) {
    return (
      <div suppressHydrationWarning={suppressHydrationWarning}>
        {fallback}
      </div>
    )
  }

  return (
    <div suppressHydrationWarning={suppressHydrationWarning}>
      {children}
    </div>
  )
}

export default NoSSR
