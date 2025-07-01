import type { Metadata } from 'next'
import './globals.css'
import HydrationErrorBoundary from '@/components/HydrationErrorBoundary'

export const metadata: Metadata = {
  title: '数据集管理系统',
  description: '基于Next.js和FastAPI的智能数据集管理平台',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <HydrationErrorBoundary>
          <div className="min-h-screen p-5" suppressHydrationWarning>
            <div className="container-main" suppressHydrationWarning>
              {children}
            </div>
          </div>
        </HydrationErrorBoundary>
      </body>
    </html>
  )
} 