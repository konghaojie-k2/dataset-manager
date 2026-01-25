/**
 * 血缘关系可视化组件
 * 显示数据集的上下游血缘关系图
 */

import React, { useEffect, useState, useRef } from 'react';
import { lineageAPI, type Dataset } from '@/lib/api-extension';

interface LineageNode {
  id: string;
  label: string;
  type: 'current' | 'source' | 'derived';
  is_derived?: boolean;
  depth?: number;
}

interface LineageEdge {
  from: string;
  to: string;
  label?: string;
  type: string;
}

interface LineageData {
  nodes: LineageNode[];
  edges: LineageEdge[];
  metadata?: {
    total_nodes: number;
    total_edges: number;
    generated_at: string;
  };
}

interface LineageGraphProps {
  datasetId: string;
  datasetName?: string;
}

export function LineageGraph({ datasetId, datasetName }: LineageGraphProps) {
  const [lineageData, setLineageData] = useState<LineageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadLineageData = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await lineageAPI.getVisualization(datasetId);
        setLineageData(data);
      } catch (err: any) {
        console.error('Failed to load lineage data:', err);
        setError(err.message || '加载血缘关系失败');
      } finally {
        setLoading(false);
      }
    };

    loadLineageData();
  }, [datasetId]);

  // 计算节点位置
  const calculateLayout = (nodes: LineageNode[], edges: LineageEdge[]) => {
    const positions = new Map<string, { x: number; y: number }>();
    const width = 800;
    const height = 500;
    const nodeRadius = 40;

    // 简单的三层布局：上游（左）- 当前（中）- 下游（右）
    const sourceNodes = nodes.filter(n => n.type === 'source');
    const currentNode = nodes.find(n => n.type === 'current');
    const derivedNodes = nodes.filter(n => n.type === 'derived');

    // 上游节点 - 左侧
    sourceNodes.forEach((node, i) => {
      const count = sourceNodes.length;
      const x = 100;
      const y = (height / (count + 1)) * (i + 1);
      positions.set(node.id, { x, y });
    });

    // 当前节点 - 中间
    if (currentNode) {
      positions.set(currentNode.id, { x: width / 2 - nodeRadius, y: height / 2 - nodeRadius });
    }

    // 下游节点 - 右侧
    derivedNodes.forEach((node, i) => {
      const count = derivedNodes.length;
      const x = width - 100 - nodeRadius * 2;
      const y = (height / (count + 1)) * (i + 1);
      positions.set(node.id, { x, y });
    });

    return { positions, width, height, nodeRadius };
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'current':
        return '#3b82f6'; // blue-500
      case 'source':
        return '#10b981'; // green-500
      case 'derived':
        return '#8b5cf6'; // purple-500
      default:
        return '#6b7280'; // gray-500
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 border rounded-lg bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">加载血缘关系中...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 border rounded-lg bg-red-50">
        <h3 className="text-lg font-semibold text-red-800 mb-2">加载失败</h3>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (!lineageData || lineageData.nodes.length === 0) {
    return (
      <div className="p-6 border rounded-lg bg-gray-50 text-center">
        <p className="text-gray-500">暂无血缘关系数据</p>
        <p className="text-sm text-gray-400 mt-1">该数据集没有上下游关系</p>
      </div>
    );
  }

  const { positions, width, height, nodeRadius } = calculateLayout(lineageData.nodes, lineageData.edges);

  return (
    <div className="space-y-4">
      {/* 图例 */}
      <div className="flex gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-blue-500"></div>
          <span>当前数据集</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-green-500"></div>
          <span>上游数据源</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-purple-500"></div>
          <span>下游派生数据</span>
        </div>
      </div>

      {/* 可视化画布 */}
      <div
        ref={canvasRef}
        className="border rounded-lg bg-white overflow-auto"
        style={{ maxHeight: '600px' }}
      >
        <svg width={width} height={height} style={{ minWidth: '100%', minHeight: '400px' }}>
          {/* 边（连接线） */}
          {lineageData.edges.map((edge, i) => {
            const from = positions.get(edge.from);
            const to = positions.get(edge.to);
            if (!from || !to) return null;

            // 计算箭头路径
            const angle = Math.atan2(to.y - from.y, to.x - from.x);
            const arrowLength = 10;
            const arrowAngle = Math.PI / 6;

            const endX = to.x + nodeRadius;
            const endY = to.y + nodeRadius;
            const startX = from.x + nodeRadius;
            const startY = from.y + nodeRadius;

            const arrowX1 = endX - arrowLength * Math.cos(angle - arrowAngle);
            const arrowY1 = endY - arrowLength * Math.sin(angle - arrowAngle);
            const arrowX2 = endX - arrowLength * Math.cos(angle + arrowAngle);
            const arrowY2 = endY - arrowLength * Math.sin(angle + arrowAngle);

            return (
              <g key={i}>
                {/* 连接线 */}
                <line
                  x1={startX}
                  y1={startY}
                  x2={endX}
                  y2={endY}
                  stroke="#94a3b8"
                  strokeWidth={2}
                />
                {/* 箭头 */}
                <polygon
                  points={`${endX},${endY} ${arrowX1},${arrowY1} ${arrowX2},${arrowY2}`}
                  fill="#94a3b8"
                />
                {/* 标签 */}
                {edge.label && (
                  <text
                    x={(startX + endX) / 2}
                    y={(startY + endY) / 2 - 5}
                    textAnchor="middle"
                    className="text-xs fill-gray-500"
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* 节点 */}
          {lineageData.nodes.map((node) => {
            const pos = positions.get(node.id);
            if (!pos) return null;

            return (
              <g key={node.id}>
                {/* 节点圆形 */}
                <circle
                  cx={pos.x + nodeRadius}
                  cy={pos.y + nodeRadius}
                  r={nodeRadius}
                  fill={getNodeColor(node.type)}
                  opacity={0.9}
                  className="cursor-pointer hover:opacity-100 transition-opacity"
                />
                {/* 节点标签 */}
                <text
                  x={pos.x + nodeRadius}
                  y={pos.y + nodeRadius + 5}
                  textAnchor="middle"
                  className="text-xs font-medium fill-white pointer-events-none"
                  style={{ maxWidth: nodeRadius * 2, overflow: 'hidden', textOverflow: 'ellipsis' }}
                >
                  {node.label.length > 10 ? node.label.substring(0, 10) + '...' : node.label}
                </text>
                {/* 完整标签（悬停提示） */}
                <title>{node.label}</title>
              </g>
            );
          })}
        </svg>
      </div>

      {/* 统计信息 */}
      {lineageData.metadata && (
        <div className="flex gap-4 text-sm text-gray-600">
          <span>总节点数: {lineageData.metadata.total_nodes}</span>
          <span>总关系数: {lineageData.metadata.total_edges}</span>
        </div>
      )}
    </div>
  );
}

// 简化的血缘关系列表视图（用于数据集详情）
interface LineageListProps {
  datasetId: string;
}

export function LineageList({ datasetId }: LineageListProps) {
  const [upstream, setUpstream] = useState<any[]>([]);
  const [downstream, setDownstream] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadLineageData = async () => {
      try {
        setLoading(true);
        setError(null);
        const [upData, downData] = await Promise.all([
          lineageAPI.getUpstream(datasetId),
          lineageAPI.getDownstream(datasetId),
        ]);
        setUpstream(upData.upstream_datasets || []);
        setDownstream(downData.downstream_datasets || []);
      } catch (err: any) {
        console.error('Failed to load lineage data:', err);
        setError(err.message || '加载血缘关系失败');
      } finally {
        setLoading(false);
      }
    };

    loadLineageData();
  }, [datasetId]);

  if (loading) {
    return <div className="text-center text-gray-500 py-4">加载中...</div>;
  }

  if (error) {
    return <div className="text-center text-red-500 py-4">{error}</div>;
  }

  if (upstream.length === 0 && downstream.length === 0) {
    return (
      <div className="text-center text-gray-500 py-4">
        <p>该数据集暂无血缘关系</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 上游数据源 */}
      {upstream.length > 0 && (
        <div>
          <h4 className="font-semibold text-green-600 mb-3">上游数据源</h4>
          <div className="space-y-2">
            {upstream.map((item, i) => (
              <div key={i} className="flex items-center justify-between p-3 border rounded-lg bg-green-50">
                <div>
                  <p className="font-medium text-gray-900">{item.name}</p>
                  <p className="text-sm text-gray-500">ID: {item.id}</p>
                </div>
                {item.transformation && (
                  <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded">
                    {item.transformation}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 下游派生数据 */}
      {downstream.length > 0 && (
        <div>
          <h4 className="font-semibold text-purple-600 mb-3">下游派生数据</h4>
          <div className="space-y-2">
            {downstream.map((item, i) => (
              <div key={i} className="flex items-center justify-between p-3 border rounded-lg bg-purple-50">
                <div>
                  <p className="font-medium text-gray-900">{item.name}</p>
                  <p className="text-sm text-gray-500">ID: {item.id}</p>
                </div>
                {item.transformation && (
                  <span className="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded">
                    {item.transformation}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
