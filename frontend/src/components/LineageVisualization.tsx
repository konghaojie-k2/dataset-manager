'use client'

import React, { useEffect, useState } from 'react'
import { LineageChain, LineageVisualizationData, DatasetMetadata } from '@/types/dataset'
import { api } from '@/lib/api'

interface LineageVisualizationProps {
  datasetId: string
  height?: string
  onDatasetClick?: (datasetId: string) => void
}

export default function LineageVisualization({
  datasetId,
  height = '400px',
  onDatasetClick,
}: LineageVisualizationProps) {
  const [lineageData, setLineageData] = useState<LineageChain | null>(null)
  const [vizData, setVizData] = useState<LineageVisualizationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 加载血缘数据
  useEffect(() => {
    const loadLineageData = async () => {
      try {
        setLoading(true)
        setError(null)

        // 获取血缘链和可视化数据
        const [chainData, visualizationData] = await Promise.all([
          api.lineage.getChain(datasetId),
          api.lineage.getVisualization(datasetId),
        ])

        setLineageData(chainData)
        setVizData(visualizationData)
      } catch (err: any) {
        console.error('加载血缘数据失败:', err)
        setError(err.message || '加载失败')
      } finally {
        setLoading(false)
      }
    }

    loadLineageData()
  }, [datasetId])

  if (loading) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg"
        style={{ height }}
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600">加载血缘关系中...</p>
        </div>
      </div>
    )
  }

  if (error || !vizData || vizData.nodes.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg"
        style={{ height }}
      >
        <div className="text-center text-gray-500">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          <p className="mt-2 text-sm">暂无血缘关系数据</p>
          {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
        </div>
      </div>
    )
  }

  // 简单的层次化布局算法
  const layoutNodes = () => {
    const levels: { [key: number]: string[] } = {}
    const nodeLevels: { [key: string]: number } = {}

    // 计算每个节点的层级
    vizData.nodes.forEach((node) => {
      const level = node.depth || 0
      if (!levels[level]) levels[level] = []
      levels[level].push(node.id)
      nodeLevels[node.id] = level
    })

    // 计算节点位置
    const positions: { [key: string]: { x: number; y: number } } = {}
    const levelHeight = 100
    const nodeWidth = 180
    const horizontalGap = 40

    Object.keys(levels).forEach((level) => {
      const levelNum = parseInt(level)
      const nodesInLevel = levels[levelNum]
      const totalWidth = nodesInLevel.length * nodeWidth + (nodesInLevel.length - 1) * horizontalGap
      const startX = (800 - totalWidth) / 2 // 假设画布宽度800

      nodesInLevel.forEach((nodeId, idx) => {
        positions[nodeId] = {
          x: startX + idx * (nodeWidth + horizontalGap),
          y: 50 + levelNum * levelHeight,
        }
      })
    })

    return { positions, nodeLevels }
  }

  const { positions, nodeLevels } = layoutNodes()

  // 计算边的路径
  const getEdgePath = (edge: any) => {
    const from = positions[edge.from]
    const to = positions[edge.to]

    if (!from || !to) return ''

    // 简单的贝塞尔曲线
    const midY = (from.y + to.y) / 2
    return `M ${from.x + 90} ${from.y + 30} C ${from.x + 90} ${midY}, ${
      to.x + 90
    } ${midY}, ${to.x + 90} ${to.y}`
  }

  // 获取节点样式
  const getNodeStyle = (node: any) => {
    const baseStyle = 'absolute rounded-lg shadow-md transition-all duration-200 cursor-pointer hover:shadow-lg '
    if (node.type === 'current') {
      return baseStyle + 'bg-blue-500 text-white border-2 border-blue-600'
    } else if (node.type === 'source') {
      return baseStyle + 'bg-green-100 text-green-800 border border-green-300'
    } else {
      return baseStyle + 'bg-purple-100 text-purple-800 border border-purple-300'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow" style={{ height }}>
      {/* 工具栏 */}
      <div className="p-3 border-b flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">数据血缘关系图</h3>
        {lineageData && (
          <div className="text-xs text-gray-500">
            上游: {lineageData.upstream.length} | 下游: {lineageData.downstream.length}
          </div>
        )}
      </div>

      {/* 可视化画布 */}
      <div className="relative overflow-auto" style={{ height: `calc(${height} - 50px)` }}>
        <div className="relative" style={{ width: '100%', height: '600px' }}>
          {/* SVG边 */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            {vizData.edges.map((edge, idx) => (
              <g key={idx}>
                <path
                  d={getEdgePath(edge)}
                  stroke="#94a3b8"
                  strokeWidth={2}
                  fill="none"
                  markerEnd="url(#arrowhead)"
                />
                {edge.label && (
                  <text
                    x={
                      (positions[edge.from]?.x || 0) +
                      (positions[edge.to]?.x || 0)
                    ) / 2 + 90}
                    y={
                      (positions[edge.from]?.y || 0) +
                      (positions[edge.to]?.y || 0)
                    ) / 2
                    }
                    className="text-xs fill-gray-600"
                    textAnchor="middle"
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            ))}
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
              </marker>
            </defs>
          </svg>

          {/* 节点 */}
          {vizData.nodes.map((node) => {
            const pos = positions[node.id]
            if (!pos) return null

            return (
              <div
                key={node.id}
                className={getNodeStyle(node)}
                style={{
                  left: pos.x,
                  top: pos.y,
                  width: '180px',
                  minHeight: '60px',
                  padding: '8px',
                }}
                onClick={() => onDatasetClick?.(node.id)}
              >
                <div className="text-xs font-semibold mb-1 truncate" title={node.label}>
                  {node.label}
                </div>
                <div className="text-xs opacity-75">
                  {node.type === 'current' && '当前数据集'}
                  {node.type === 'source' && '源数据集'}
                  {node.type === 'derived' && '派生数据集'}
                </div>
                {node.is_derived && (
                  <div className="text-xs opacity-75 mt-1">
                    派生: {lineageData?.current_dataset.transformation_type}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* 图例 */}
      <div className="p-3 border-t bg-gray-50">
        <div className="flex items-center space-x-6 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span className="text-gray-700">当前数据集</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-100 border border-green-300 rounded"></div>
            <span className="text-gray-700">源数据集</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-purple-100 border border-purple-300 rounded"></div>
            <span className="text-gray-700">派生数据集</span>
          </div>
        </div>
      </div>
    </div>
  )
}
