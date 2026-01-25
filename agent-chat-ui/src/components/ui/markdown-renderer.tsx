/**
 * Markdown Renderer Component
 * Uses the same implementation as agent chat for consistency
 */

import React, { FC, memo, useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import remarkMath from 'remark-math';
import { PrismAsyncLight as SyntaxHighlighterPrism } from 'react-syntax-highlighter';
import tsx from 'react-syntax-highlighter/dist/esm/languages/prism/tsx';
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python';
import { coldarkDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { CheckIcon, CopyIcon, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';
import 'katex/dist/katex.min.css';
import mermaid from 'mermaid';

// Register languages
SyntaxHighlighterPrism.registerLanguage('js', tsx);
SyntaxHighlighterPrism.registerLanguage('jsx', tsx);
SyntaxHighlighterPrism.registerLanguage('ts', tsx);
SyntaxHighlighterPrism.registerLanguage('tsx', tsx);
SyntaxHighlighterPrism.registerLanguage('python', python);

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'base',
  securityLevel: 'loose',
  themeVariables: {
    // 背景
    background: '#ffffff',
    tertiaryColor: '#ffffff',

    // 主色调 - 参考 Mermaid Chart 的柔和配色方案
    primaryColor: '#e3f2fd', // 浅蓝色 - 参考 #e3f2fd
    primaryTextColor: '#1565c0', // 深蓝色文字
    primaryBorderColor: '#64b5f6', // 蓝色边框

    // 辅助色 - 柔和的粉色系
    secondaryColor: '#f9d5e5', // 浅粉色 - 参考 #f9d5e5
    secondaryTextColor: '#c2185b', // 深粉色文字
    secondaryBorderColor: '#f48fb1', // 粉色边框

    // 线条颜色 - 柔和的灰色
    lineColor: '#90a4ae',
    tertiaryBorderColor: '#cfd8dc',

    // 文字颜色
    fontSize: '16px',
    fontFamily: 'system-ui, -apple-system, sans-serif',

    // 优化的节点配色方案 - 参考 Mermaid Chart 的配色
    // 粉色系 - 输入/起始节点
    fillType0: '#f9d5e5', // 浅粉色 - 参考示例中的 A1
    fillType1: '#ffcdd2', // 浅桃色 - 参考示例中的 C
    
    // 蓝色系 - 控制/管理节点
    fillType2: '#e3f2fd', // 浅蓝色 - 参考示例中的 A2
    fillType3: '#bbdefb', // 稍深蓝色
    
    // 绿色系 - 过程/执行节点
    fillType4: '#dcedc8', // 浅绿色 - 参考示例中的 A3
    fillType5: '#c5e1a5', // 稍深绿色
    
    // 紫色系 - 数据/信息节点
    fillType6: '#e1bee7', // 浅紫色
    fillType7: '#ce93d8', // 稍深紫色
    
    // 扩展颜色
    noteBkgColor: '#fff9c4', // 浅黄色 - 注释/说明
    noteTextColor: '#f57f17', // 深黄色文字
    noteBorderColor: '#fdd835', // 黄色边框
    
    // 激活/高亮颜色
    activationBorderColor: '#64b5f6', // 蓝色边框
    activationBkgColor: '#e3f2fd', // 浅蓝色背景
    
    // 标签颜色
    labelTextColor: '#37474f', // 深灰色文字
    labelBackground: '#f5f5f5', // 浅灰色背景
    
    // 错误/警告颜色
    errorBkgColor: '#ffcdd2', // 浅红色
    errorTextColor: '#c62828', // 深红色文字
    
    // 成功/完成颜色
    successBkgColor: '#dcedc8', // 浅绿色
    successTextColor: '#2e7d32', // 深绿色文字
  },
});

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

// Mermaid Diagram Component
const MermaidDiagram: FC<{ chart: string }> = ({ chart }) => {
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState<number>(1);
  const [position, setPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const renderDiagram = async () => {
      try {
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
        const { svg } = await mermaid.render(id, chart);
        setSvg(svg);
        setError(null);
        setZoom(1); // 重置缩放
        setPosition({ x: 0, y: 0 }); // 重置位置
      } catch (err) {
        console.error('Mermaid render error:', err);
        setError(err instanceof Error ? err.message : 'Failed to render diagram');
      }
    };

    renderDiagram();
  }, [chart]);

  // 鼠标滚轮缩放
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        setZoom((prev) => Math.max(0.5, Math.min(3, prev + delta)));
      }
    };

    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, []);

  // 拖拽功能
  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      const deltaX = e.clientX - dragStart.x;
      const deltaY = e.clientY - dragStart.y;
      setPosition((prev) => ({
        x: prev.x + deltaX,
        y: prev.y + deltaY,
      }));
      setDragStart({ x: e.clientX, y: e.clientY });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = 'grabbing';
    document.body.style.userSelect = 'none';

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDragging, dragStart]);

  const handleMouseDown = (e: React.MouseEvent) => {
    // 只在按住鼠标左键且放大时才开始拖拽
    if (e.button === 0 && zoom > 1) {
      e.preventDefault();
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
    }
  };

  const handleZoomIn = () => {
    setZoom((prev) => Math.min(3, prev + 0.2));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(0.5, prev - 0.2));
  };

  const handleReset = () => {
    setZoom(1);
    setPosition({ x: 0, y: 0 });
  };

  if (error) {
    return (
      <div className="my-6 p-4 bg-red-50 border border-red-200 rounded-xl">
        <p className="text-red-600 text-sm font-medium">图表渲染失败</p>
        <p className="text-red-500 text-xs mt-1">{error}</p>
        <pre className="mt-3 text-xs text-red-400 bg-red-100 p-3 rounded overflow-auto max-h-40">{chart}</pre>
      </div>
    );
  }

  if (!svg) {
    return (
      <div className="my-6 flex items-center justify-center p-12 bg-gradient-to-br from-gray-50 to-white rounded-xl border border-gray-200">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-gray-200 border-t-blue-600 mx-auto mb-3"></div>
          <span className="text-gray-600 text-sm font-medium">正在渲染图表...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="my-6 bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-gray-50 to-white px-4 py-2 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">流程图</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">{Math.round(zoom * 100)}%</span>
            <button
              onClick={handleZoomOut}
              disabled={zoom <= 0.5}
              className="p-1.5 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="缩小 (Ctrl + 滚轮)"
            >
              <ZoomOut className="w-4 h-4 text-gray-600" />
            </button>
            <button
              onClick={handleReset}
              className="p-1.5 rounded hover:bg-gray-200 transition-colors"
              title="重置缩放和位置"
            >
              <RotateCcw className="w-4 h-4 text-gray-600" />
            </button>
            <button
              onClick={handleZoomIn}
              disabled={zoom >= 3}
              className="p-1.5 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="放大 (Ctrl + 滚轮)"
            >
              <ZoomIn className="w-4 h-4 text-gray-600" />
            </button>
          </div>
        </div>
      </div>
      <div 
        ref={containerRef}
        className="p-4 flex justify-center items-center bg-white overflow-hidden relative"
        style={{ maxHeight: '600px' }}
      >
        <div 
          ref={svgRef}
          onMouseDown={handleMouseDown}
          style={{ 
            transform: `translate(${position.x}px, ${position.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
            transition: isDragging ? 'none' : 'transform 0.2s ease-out',
            cursor: isDragging ? 'grabbing' : zoom > 1 ? 'grab' : 'default',
            userSelect: 'none',
            touchAction: 'none'
          }}
          dangerouslySetInnerHTML={{ __html: svg }} 
        />
      </div>
    </div>
  );
};

const useCopyToClipboard = ({
  copiedDuration = 3000,
}: {
  copiedDuration?: number;
} = {}) => {
  const [isCopied, setIsCopied] = useState<boolean>(false);

  const copyToClipboard = (value: string) => {
    if (!value) return;

    navigator.clipboard.writeText(value).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), copiedDuration);
    });
  };

  return { isCopied, copyToClipboard };
};

interface CodeHeaderProps {
  language?: string;
  code: string;
}

const CodeHeader: FC<CodeHeaderProps> = ({ language, code }) => {
  const { isCopied, copyToClipboard } = useCopyToClipboard();
  const onCopy = () => {
    if (!code || isCopied) return;
    copyToClipboard(code);
  };

  return (
    <div className="flex items-center justify-between gap-4 rounded-t-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white">
      <span className="lowercase [&>span]:text-xs">{language}</span>
      <button
        onClick={onCopy}
        className="text-gray-300 hover:text-white transition-colors"
        title={isCopied ? '已复制' : '复制'}
      >
        {!isCopied && <CopyIcon className="w-4 h-4" />}
        {isCopied && <CheckIcon className="w-4 h-4" />}
      </button>
    </div>
  );
};

interface SyntaxHighlighterProps {
  children: string;
  language: string;
  className?: string;
}

const SyntaxHighlighter: FC<SyntaxHighlighterProps> = ({
  children,
  language,
  className,
}) => {
  return (
    <SyntaxHighlighterPrism
      language={language}
      style={coldarkDark}
      customStyle={{
        margin: 0,
        width: '100%',
        background: 'transparent',
        padding: '1.5rem 1rem',
      }}
      className={className}
    >
      {children}
    </SyntaxHighlighterPrism>
  );
};

const defaultComponents: any = {
  h1: ({ className, ...props }: { className?: string }) => (
    <h1
      className={cn(
        'mb-4 scroll-m-20 text-3xl font-extrabold tracking-tight last:mb-0',
        className,
      )}
      {...props}
    />
  ),
  h2: ({ className, ...props }: { className?: string }) => (
    <h2
      className={cn(
        'mt-6 mb-4 scroll-m-20 text-2xl font-semibold tracking-tight first:mt-0 last:mb-0',
        className,
      )}
      {...props}
    />
  ),
  h3: ({ className, ...props }: { className?: string }) => (
    <h3
      className={cn(
        'mt-5 mb-3 scroll-m-20 text-xl font-semibold tracking-tight first:mt-0 last:mb-0',
        className,
      )}
      {...props}
    />
  ),
  h4: ({ className, ...props }: { className?: string }) => (
    <h4
      className={cn(
        'mt-4 mb-2 scroll-m-20 text-lg font-semibold tracking-tight first:mt-0 last:mb-0',
        className,
      )}
      {...props}
    />
  ),
  p: ({ className, ...props }: { className?: string }) => (
    <p
      className={cn('mt-4 mb-4 leading-7 first:mt-0 last:mb-0', className)}
      {...props}
    />
  ),
  a: ({ className, ...props }: { className?: string }) => (
    <a
      className={cn(
        'text-blue-600 font-medium underline underline-offset-4 hover:no-underline',
        className,
      )}
      {...props}
    />
  ),
  blockquote: ({ className, ...props }: { className?: string }) => (
    <blockquote
      className={cn('border-l-4 border-gray-300 pl-4 italic text-gray-700', className)}
      {...props}
    />
  ),
  ul: ({ className, ...props }: { className?: string }) => (
    <ul
      className={cn('my-3 ml-6 list-disc [&>li]:mt-2', className)}
      {...props}
    />
  ),
  ol: ({ className, ...props }: { className?: string }) => (
    <ol
      className={cn('my-3 ml-6 list-decimal [&>li]:mt-2', className)}
      {...props}
    />
  ),
  hr: ({ className, ...props }: { className?: string }) => (
    <hr
      className={cn('my-4 border-t border-gray-300', className)}
      {...props}
    />
  ),
  table: ({ className, ...props }: { className?: string }) => (
    <div className="my-4 overflow-x-auto">
      <table
        className={cn(
          'min-w-full border-collapse border border-gray-300',
          className,
        )}
        {...props}
      />
    </div>
  ),
  th: ({ className, ...props }: { className?: string }) => (
    <th
      className={cn(
        'border border-gray-300 bg-gray-100 px-4 py-2 text-left font-bold text-sm',
        className,
      )}
      {...props}
    />
  ),
  td: ({ className, ...props }: { className?: string }) => (
    <td
      className={cn(
        'border border-gray-300 px-4 py-2 text-sm',
        className,
      )}
      {...props}
    />
  ),
  tr: ({ className, ...props }: { className?: string }) => (
    <tr
      className={cn(
        'even:bg-gray-50',
        className,
      )}
      {...props}
    />
  ),
  pre: ({ className, ...props }: { className?: string }) => (
    <pre
      className={cn(
        'my-4 max-w-4xl overflow-x-auto',
        className,
      )}
      {...props}
    />
  ),
  code: ({
    className,
    children,
    ...props
  }: {
    className?: string;
    children: React.ReactNode;
  }) => {
    const match = /language-(\w+)/.exec(className || '');
    const code = String(children).replace(/\n$/, '');

    // Handle mermaid diagrams
    if (match && match[1] === 'mermaid') {
      return <MermaidDiagram chart={code} />;
    }

    // Handle regular code blocks
    if (match) {
      const language = match[1];

      return (
        <>
          <CodeHeader
            language={language}
            code={code}
          />
          <SyntaxHighlighter
            language={language}
            className={className}
          >
            {code}
          </SyntaxHighlighter>
        </>
      );
    }

    return (
      <code
        className={cn(
          'rounded bg-gray-100 px-1.5 py-0.5 font-mono text-sm font-semibold text-red-600',
          className,
        )}
        {...props}
      >
        {children}
      </code>
    );
  },
};

export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  if (!content) {
    return null;
  }

  return (
    <div className={cn('markdown-content', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={defaultComponents}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
