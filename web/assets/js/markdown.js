/**
 * 简单的Markdown渲染器
 * 支持常用的Markdown语法
 */
class MarkdownRenderer {
    /**
     * 渲染Markdown文本为HTML
     * @param {string} markdown - Markdown文本
     * @returns {string} - 渲染后的HTML
     */
    static render(markdown) {
        if (!markdown || typeof markdown !== 'string') {
            return '';
        }

        let html = markdown;

        // 转义HTML特殊字符（但保留我们要处理的Markdown语法）
        html = html.replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;');

        // 处理Mermaid图表并修复常见语法错误
        html = html.replace(/```mermaid\s*\n([\s\S]*?)```/g, (match, code) => {
            const mermaidId = 'mermaid-' + Math.random().toString(36).substr(2, 9);
            // 清理和修复Mermaid代码
            const cleanCode = this.fixMermaidSyntax(code.trim());
            return `<div class="mermaid-container">
                <div id="${mermaidId}" class="mermaid">${cleanCode}</div>
            </div>`;
        });

        // 处理代码块（三个反引号）
        html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang || 'text'}">${code.trim()}</code></pre>`;
        });

        // 处理行内代码（单个反引号）
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        // 处理标题（从h6到h1，避免冲突）
        html = html.replace(/^###### (.*$)/gm, '<h6>$1</h6>');
        html = html.replace(/^##### (.*$)/gm, '<h5>$1</h5>');
        html = html.replace(/^#### (.*$)/gm, '<h4>$1</h4>');
        html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');

        // 处理粗体
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');

        // 处理斜体
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        html = html.replace(/_(.*?)_/g, '<em>$1</em>');

        // 处理链接
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

        // 处理表格
        html = this.renderTables(html);

        // 处理列表
        html = this.renderLists(html);

        // 处理段落和换行
        html = this.renderParagraphs(html);

        return html;
    }

    /**
     * 修复Mermaid语法错误
     * @param {string} mermaidCode - 原始Mermaid代码
     * @returns {string} - 修复后的Mermaid代码
     */
    static fixMermaidSyntax(mermaidCode) {
        if (!mermaidCode || typeof mermaidCode !== 'string') {
            return mermaidCode;
        }

        let fixedCode = mermaidCode.trim();
        
        try {
            // 1. 修复graph声明语法错误
            // 将 "graph TDA[...]" 修复为 "graph TD"
            fixedCode = fixedCode.replace(/^graph\s+TD([A-Z])\[(.*?)\]/gm, (match, letter, content) => {
                // 如果是 graph TDA[...] 这种错误格式，修复为正确格式
                return `graph TD\n    A[${content}]`;
            });
            
            // 2. 修复节点定义中的连续节点问题
            // 将 "A --> B[...]B --> C[...]" 修复为换行格式
            fixedCode = fixedCode.replace(/(\]\s*)(([A-Z][A-Z0-9]*)\s*-->\s*([A-Z][A-Z0-9]*)\[)/g, (match, p1, p2, p3, p4) => {
                return p1 + '\n    ' + p2;
            });
            
            // 3. 修复连续的节点连接，确保换行
            fixedCode = fixedCode.replace(/(\]\s*)([A-Z][A-Z0-9]*\s*-->)/g, '$1\n    $2');
            
            // 4. 修复箭头连接语法
            fixedCode = fixedCode.replace(/-->\s*([A-Z][A-Z0-9]*)\s*([A-Z][A-Z0-9]*)\s*-->/g, '--> $1\n    $2 -->');
            
            // 5. 确保每个节点定义都在新行
            const lines = fixedCode.split('\n');
            const fixedLines = [];
            
            for (let i = 0; i < lines.length; i++) {
                let line = lines[i].trim();
                
                if (i === 0 && line.startsWith('graph')) {
                    // 图表类型声明行
                    fixedLines.push(line);
                } else if (line && !line.startsWith('graph')) {
                    // 节点定义行，确保适当缩进
                    if (!line.startsWith('    ') && !line.startsWith('subgraph') && !line.startsWith('end')) {
                        line = '    ' + line;
                    }
                    fixedLines.push(line);
                } else if (line) {
                    fixedLines.push(line);
                }
            }
            
            fixedCode = fixedLines.join('\n');
            
            // 6. 确保subgraph语法正确
            fixedCode = fixedCode.replace(/subgraph\s+"([^"]+)"/g, 'subgraph "$1"');
            
            // 7. 最终清理：移除多余的空行
            fixedCode = fixedCode.replace(/\n\s*\n\s*\n/g, '\n\n');
            
            console.log('🔧 Mermaid语法修复完成');
            console.log('原始代码:', mermaidCode.substring(0, 100) + '...');
            console.log('修复后代码:', fixedCode.substring(0, 100) + '...');
            
            return fixedCode;
            
        } catch (error) {
            console.error('❌ Mermaid语法修复失败:', error);
            // 如果修复失败，返回原始代码
            return mermaidCode;
        }
    }

    /**
     * 渲染表格
     * @param {string} html - HTML文本
     * @returns {string} - 处理后的HTML
     */
    static renderTables(html) {
        // 匹配表格模式
        const tableRegex = /(\|.*\|[\r\n]+\|[-\s|:]+\|[\r\n]+((\|.*\|[\r\n]*)+))/gm;
        
        return html.replace(tableRegex, (match) => {
            const lines = match.trim().split(/[\r\n]+/);
            if (lines.length < 3) return match;

            const headerLine = lines[0];
            const separatorLine = lines[1];
            const dataLines = lines.slice(2);

            // 解析表头
            const headers = headerLine.split('|').map(h => h.trim()).filter(h => h);
            
            // 解析数据行
            const rows = dataLines.map(line => 
                line.split('|').map(cell => cell.trim()).filter(cell => cell !== '')
            ).filter(row => row.length > 0);

            // 生成HTML表格
            let tableHtml = '<table class="markdown-table">\n';
            
            // 表头
            tableHtml += '<thead>\n<tr>\n';
            headers.forEach(header => {
                tableHtml += `<th>${header}</th>\n`;
            });
            tableHtml += '</tr>\n</thead>\n';

            // 表体
            tableHtml += '<tbody>\n';
            rows.forEach(row => {
                tableHtml += '<tr>\n';
                row.forEach((cell, index) => {
                    if (index < headers.length) {
                        tableHtml += `<td>${cell}</td>\n`;
                    }
                });
                tableHtml += '</tr>\n';
            });
            tableHtml += '</tbody>\n</table>\n';

            return tableHtml;
        });
    }

    /**
     * 渲染列表
     * @param {string} html - HTML文本
     * @returns {string} - 处理后的HTML
     */
    static renderLists(html) {
        // 处理无序列表
        html = html.replace(/^[\s]*[-*+] (.+)$/gm, '<li>$1</li>');
        
        // 处理有序列表
        html = html.replace(/^[\s]*\d+\. (.+)$/gm, '<li>$1</li>');

        // 包装连续的列表项
        html = html.replace(/(<li>.*<\/li>[\r\n]*)+/g, (match) => {
            return `<ul>\n${match}</ul>\n`;
        });

        return html;
    }

    /**
     * 渲染段落和换行
     * @param {string} html - HTML文本
     * @returns {string} - 处理后的HTML
     */
    static renderParagraphs(html) {
        // 分割成段落（双换行分隔）
        const paragraphs = html.split(/\n\s*\n/);
        
        return paragraphs.map(paragraph => {
            paragraph = paragraph.trim();
            if (!paragraph) return '';
            
            // 如果已经是HTML标签，不要包装在<p>中
            if (paragraph.match(/^<(h[1-6]|table|ul|ol|pre|div|section)/)) {
                return paragraph;
            }
            
            // 处理单个换行为<br>
            paragraph = paragraph.replace(/\n/g, '<br>');
            
            return `<p>${paragraph}</p>`;
        }).join('\n\n');
    }

    /**
     * 获取Markdown样式
     * @returns {string} - CSS样式
     */
    static getStyles() {
        return `
            /* Markdown渲染样式 */
            .markdown-content {
                line-height: 1.6;
                color: #24292e !important;
            }
            
            .markdown-content *:not(a):not(h6) {
                color: inherit !important;
            }
            
            .markdown-content h1,
            .markdown-content h2,
            .markdown-content h3,
            .markdown-content h4,
            .markdown-content h5,
            .markdown-content h6 {
                margin-top: 24px;
                margin-bottom: 16px;
                font-weight: 600;
                line-height: 1.25;
                color: #24292e !important;
            }
            
            .markdown-content h1 {
                font-size: 2em;
                border-bottom: 1px solid #eaecef;
                padding-bottom: 10px;
            }
            
            .markdown-content h2 {
                font-size: 1.5em;
                border-bottom: 1px solid #eaecef;
                padding-bottom: 8px;
            }
            
            .markdown-content h3 {
                font-size: 1.25em;
            }
            
            .markdown-content h4 {
                font-size: 1.1em;
            }
            
            .markdown-content h5 {
                font-size: 1em;
            }
            
            .markdown-content h6 {
                font-size: 0.9em;
                color: #6a737d !important;
            }
            
            .markdown-content p {
                margin-bottom: 16px;
            }
            
            .markdown-content code {
                background-color: rgba(27,31,35,0.05);
                border-radius: 3px;
                font-size: 85%;
                margin: 0;
                padding: 0.2em 0.4em;
                font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            }
            
            .markdown-content pre {
                background-color: #f6f8fa;
                border-radius: 6px;
                font-size: 85%;
                line-height: 1.45;
                overflow: auto;
                padding: 16px;
                margin-bottom: 16px;
            }
            
            .markdown-content pre code {
                background-color: transparent;
                border: 0;
                display: inline;
                line-height: inherit;
                margin: 0;
                max-width: auto;
                overflow: visible;
                padding: 0;
                word-wrap: normal;
            }
            
            .markdown-content .markdown-table {
                border-collapse: collapse;
                border-spacing: 0;
                width: 100%;
                margin-bottom: 16px;
            }
            
            .markdown-content .markdown-table th,
            .markdown-content .markdown-table td {
                border: 1px solid #dfe2e5;
                padding: 6px 13px;
                text-align: left;
                color: #24292e !important;
            }
            
            .markdown-content .markdown-table th {
                background-color: #f6f8fa;
                font-weight: 600;
                color: #24292e !important;
            }
            
            .markdown-content .markdown-table tr:nth-child(2n) {
                background-color: #f6f8fa;
            }
            
            .markdown-content ul,
            .markdown-content ol {
                margin-bottom: 16px;
                padding-left: 2em;
            }
            
            .markdown-content li {
                margin-bottom: 4px;
            }
            
            .markdown-content strong {
                font-weight: 600;
            }
            
            .markdown-content em {
                font-style: italic;
            }
            
            .markdown-content a {
                color: #0366d6;
                text-decoration: none;
            }
            
            .markdown-content a:hover {
                text-decoration: underline;
            }
            
            /* Mermaid图表样式 */
            .mermaid-container {
                margin: 16px 0;
                text-align: center;
                background-color: #ffffff;
                border: 1px solid #e1e4e8;
                border-radius: 6px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .mermaid {
                max-width: 100%;
                overflow: auto;
                min-height: 100px;
                display: inline-block;
            }
            
            /* Mermaid SVG样式优化 */
            .mermaid svg {
                max-width: 100%;
                height: auto;
            }
            
            /* Mermaid错误显示样式 */
            .mermaid-error {
                color: #d63384;
                background: #f8d7da;
                border: 1px solid #f5c2c7;
                border-radius: 4px;
                padding: 12px;
                margin: 8px 0;
                font-family: monospace;
                font-size: 14px;
            }
        `;
    }
} 