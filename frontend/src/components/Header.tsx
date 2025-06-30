'use client'

import React from 'react'

const Header: React.FC = () => {
  return (
    <header className="bg-gradient-primary text-white">
      <div className="max-w-6xl mx-auto px-8 py-8">
        <div className="flex justify-between items-center">
          <div className="text-left">
            <h1 className="text-4xl font-bold mb-2">数据管理系统</h1>
            <p className="text-xl opacity-90">智能数据分析与管理平台</p>
          </div>
          <div className="flex gap-3">
            {/* 预留扩展按钮位置 */}
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header 