/**
 * Dataset Marketplace Header
 * Elegant, editorial-style header for the dataset supermarket
 */

import React from 'react';

export function DatasetMarketplaceHeader() {
  return (
    <header className="bg-white border-b border-[#e8e4df]">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Main title area */}
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h1
              className="text-4xl font-bold text-[#1a1a1a] mb-2 tracking-tight"
              style={{ fontFamily: 'var(--font-playfair)' }}
            >
              数据集超市
            </h1>
            <p className="text-lg text-gray-600 font-light" style={{ fontFamily: 'var(--font-outfit)' }}>
              发现、探索和分析高质量数据集
            </p>
          </div>

          {/* Stats */}
          <div className="hidden md:flex gap-8 text-center">
            <div>
              <div className="text-2xl font-bold text-[#c75b39]" style={{ fontFamily: 'var(--font-playfair)' }}>
                1000+
              </div>
              <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">数据集</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-[#7c9885]" style={{ fontFamily: 'var(--font-playfair)' }}>
                50+
              </div>
              <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">行业领域</div>
            </div>
          </div>
        </div>

        {/* Decorative line */}
        <div className="mt-6 flex gap-1">
          <div className="h-0.5 w-16 bg-[#c75b39]" />
          <div className="h-0.5 w-8 bg-[#7c9885]" />
          <div className="h-0.5 w-4 bg-gray-300" />
        </div>
      </div>
    </header>
  );
}
