import type { Metadata } from 'next'
import './globals.css'

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
    <html lang="zh-CN">
      <body>
        <div className="min-h-screen p-5">
          <div className="container-main">
            {children}
          </div>
        </div>
      </body>
    </html>
  )
} 