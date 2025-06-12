/**
 * 分析功能模块
 */

const Analysis = {


    /**
     * 启动业务分析
     */
    async startBusinessAnalysis(datasetId) {
        try {
            UI.showLoading(true);
            UI.showMessage('开始业务分析...', CONFIG.MESSAGE.TYPES.INFO);

            // 调用后端API开始业务分析
            await API.analysis.startBusinessAnalysis(datasetId);
            
            UI.showMessage('业务分析已开始，请稍候...', CONFIG.MESSAGE.TYPES.SUCCESS);

            // 刷新数据集列表
            setTimeout(() => {
                App.refreshDatasets();
            }, 2000);

        } catch (error) {
            Utils.log.error('启动业务分析失败:', error);
            UI.showMessage('启动业务分析失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            UI.showLoading(false);
        }
    },

    /**
     * 启动质量分析
     */
    async startQualityAnalysis(datasetId) {
        try {
            UI.showLoading(true);
            UI.showMessage('开始质量分析...', CONFIG.MESSAGE.TYPES.INFO);

            // 调用后端API开始质量分析
            await API.analysis.startQualityAnalysis(datasetId);
            
            UI.showMessage('质量分析已开始，请稍候...', CONFIG.MESSAGE.TYPES.SUCCESS);

            // 刷新数据集列表
            setTimeout(() => {
                App.refreshDatasets();
            }, 2000);

        } catch (error) {
            Utils.log.error('启动质量分析失败:', error);
            UI.showMessage('启动质量分析失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            UI.showLoading(false);
        }
    },

    /**
     * 查看业务分析结果
     */
    async viewBusinessAnalysisResults(datasetId) {
        try {
            UI.showLoading(true);
            Utils.log.debug('查看业务分析结果:', datasetId);

            const results = await API.analysis.getBusinessAnalysisResults(datasetId);
            
            // 添加详细的调试日志
            console.log('🔍 业务分析结果数据:', results);
            console.log('🔍 数据类型:', typeof results);
            console.log('🔍 数据键:', results ? Object.keys(results) : 'null');
            
            if (results) {
                console.log('🔍 dataset_name:', results.dataset_name);
                console.log('🔍 business_meaning 长度:', results.business_meaning ? results.business_meaning.length : 0);
                console.log('🔍 control_logic 长度:', results.control_logic ? results.control_logic.length : 0);
                console.log('🔍 columns 数量:', (results.columns || []).length);
                
                this.openBusinessAnalysisWindow(results);
            } else {
                console.log('❌ 业务分析结果为空');
                UI.showMessage('业务分析结果为空', CONFIG.MESSAGE.TYPES.WARNING);
            }

        } catch (error) {
            console.error('❌ 获取业务分析结果失败:', error);
            Utils.log.error('获取业务分析结果失败:', error);
            UI.showMessage('获取业务分析结果失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            UI.showLoading(false);
        }
    },

    /**
     * 查看质量分析结果
     */
    async viewQualityAnalysisResults(datasetId) {
        try {
            UI.showLoading(true);
            Utils.log.debug('查看质量分析结果:', datasetId);

            const results = await API.analysis.getQualityAnalysisResults(datasetId);
            
            // 添加调试日志
            console.log('🔍 质量分析结果数据:', results);
            console.log('🔍 数据类型:', typeof results);
            console.log('🔍 数据键:', results ? Object.keys(results) : 'null');
            
            if (results) {
                console.log('🔍 overall_score:', results.overall_score);
                console.log('🔍 quality_level:', results.quality_level);
                console.log('🔍 time_columns 长度:', (results.time_columns || []).length);
                console.log('🔍 parameter_columns 长度:', (results.parameter_columns || []).length);
                console.log('🔍 key_issues 长度:', (results.key_issues || []).length);
                console.log('🔍 recommendations 长度:', (results.recommendations || []).length);
                
                this.openQualityAnalysisWindow(results);
            } else {
                console.log('❌ 质量分析结果为空');
                UI.showMessage('质量分析结果为空', CONFIG.MESSAGE.TYPES.WARNING);
            }

        } catch (error) {
            console.error('❌ 获取质量分析结果失败:', error);
            Utils.log.error('获取质量分析结果失败:', error);
            UI.showMessage('获取质量分析结果失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            UI.showLoading(false);
        }
    },

    /**
     * 打开业务分析结果窗口
     */
    openBusinessAnalysisWindow(results) {
        console.log('🚀 开始生成业务分析HTML，数据:', results);
        
        const analysisWindow = window.open('', '_blank', 'width=1400,height=900');
        
        if (!analysisWindow) {
            console.error('❌ 无法打开新窗口，可能被浏览器阻止');
            UI.showMessage('无法打开新窗口，请检查浏览器弹窗设置', CONFIG.MESSAGE.TYPES.ERROR);
            return;
        }
        
        console.log('✅ 新窗口已创建');
        
        const htmlContent = this.generateBusinessAnalysisHTML(results);
        console.log('📄 生成的HTML长度:', htmlContent.length);
        console.log('📄 HTML前500字符:', htmlContent.substring(0, 500));
        
        analysisWindow.document.write(htmlContent);
        analysisWindow.document.close();
        
        console.log('✅ 业务分析窗口已打开');
    },

    /**
     * 打开质量分析结果窗口
     */
    openQualityAnalysisWindow(results) {
        console.log('🚀 开始生成质量分析HTML，数据:', results);
        
        const analysisWindow = window.open('', '_blank', 'width=1400,height=900');
        
        const htmlContent = this.generateQualityAnalysisHTML(results);
        console.log('📄 生成的HTML长度:', htmlContent.length);
        
        analysisWindow.document.write(htmlContent);
        analysisWindow.document.close();
        
        console.log('✅ 质量分析窗口已打开');
    },

    /**
     * 生成业务分析结果HTML
     */
    generateBusinessAnalysisHTML(results) {
        console.log('开始生成业务分析HTML，数据:', results);
        
        try {
            const html = `
                <!DOCTYPE html>
                <html lang="zh-CN">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>业务分析结果</title>
                    <style>
                        ${this.getAnalysisStyles()}
                        ${MarkdownRenderer.getStyles()}
                    </style>
                </head>
                <body>
                    <div class="analysis-container">
                        <div class="analysis-header">
                            <h1>💡 业务分析结果</h1>
                            <div class="analysis-meta">
                                <span>数据集: ${Utils.escapeHtml(results.dataset_name || '未知')}</span>
                                <span>分析时间: ${Utils.formatFullDateTime(results.analysis_time || new Date())}</span>
                            </div>
                        </div>

                        <div class="analysis-content">
                            <!-- 业务含义分析 -->
                            <section class="business-meaning">
                                <h2>💼 业务含义分析</h2>
                                <div class="meaning-content markdown-content">
                                    ${MarkdownRenderer.render(results.business_meaning || '暂无业务含义分析结果')}
                                </div>
                            </section>

                            <!-- 控制逻辑分析 -->
                            <section class="control-logic">
                                <h2>⚙️ 控制逻辑分析</h2>
                                <div class="logic-content markdown-content">
                                    ${MarkdownRenderer.render(results.control_logic || '暂无控制逻辑分析结果')}
                                </div>
                            </section>
                        </div>
                    </div>

                    ${this.getMermaidScript()}
                </body>
                </html>
            `;
            
            console.log('业务分析HTML生成成功');
            return html;
        } catch (error) {
            console.error('生成业务分析HTML失败:', error);
            return this.generateErrorHTML('生成业务分析结果页面失败: ' + error.message);
        }
    },

    /**
     * 生成质量分析结果HTML
     */
    generateQualityAnalysisHTML(results) {
        return `
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>数据质量分析结果</title>
                <style>
                    ${this.getAnalysisStyles()}
                </style>
            </head>
            <body>
                <div class="analysis-container">
                    <div class="analysis-header">
                        <h1>✅ 数据质量分析结果</h1>
                        <div class="analysis-meta">
                            <span>数据集: ${Utils.escapeHtml(results.dataset_name || '未知')}</span>
                            <span>分析时间: ${Utils.formatFullDateTime(results.analysis_time || new Date())}</span>
                        </div>
                    </div>

                    <div class="analysis-content">
                        <!-- 质量总览 -->
                        <section class="quality-overview">
                            <h2>📊 质量评分概览</h2>
                            <div class="score-display">
                                <div class="score-circle">
                                    <div class="score-value">${(results.overall_score || 0).toFixed(1)}</div>
                                    <div class="score-label">总体评分</div>
                                </div>
                                <div class="quality-level">
                                    <div class="level-badge level-${results.quality_level || 'unknown'}">
                                        ${this.getQualityLevelText(results.quality_level)}
                                    </div>
                                </div>
                            </div>
                        </section>

                        <!-- 列类型分布 -->
                        <section class="column-distribution">
                            <h2>📋 列类型分布</h2>
                            <div class="distribution-grid">
                                <div class="distribution-item">
                                    <div class="distribution-count">${(results.time_columns || []).length}</div>
                                    <div class="distribution-label">时间列</div>
                                </div>
                                <div class="distribution-item">
                                    <div class="distribution-count">${(results.parameter_columns || []).length}</div>
                                    <div class="distribution-label">参数列</div>
                                </div>
                                <div class="distribution-item">
                                    <div class="distribution-count">${(results.category_columns || []).length}</div>
                                    <div class="distribution-label">类目列</div>
                                </div>
                            </div>
                        </section>

                        <!-- 时间列分析 -->
                        ${(results.time_columns || []).length > 0 ? `
                        <section class="time-columns">
                            <h2>⏰ 时间列分析</h2>
                            <div class="columns-grid">
                                ${(results.time_columns || []).map(col => `
                                    <div class="column-card">
                                        <div class="column-name">${Utils.escapeHtml(col.column_name || '')}</div>
                                        <div class="column-score">评分: ${(col.overall_score || 0).toFixed(1)}</div>
                                        <div class="column-issues">
                                            ${(col.issues || []).length > 0 ? 
                                                `问题: ${(col.issues || []).slice(0, 2).map(issue => Utils.escapeHtml(String(issue))).join(', ')}` : 
                                                '无问题'
                                            }
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </section>
                        ` : ''}

                        <!-- 参数列分析 -->
                        ${(results.parameter_columns || []).length > 0 ? `
                        <section class="parameter-columns">
                            <h2>📊 参数列分析</h2>
                            <div class="columns-grid">
                                ${(results.parameter_columns || []).slice(0, 10).map(col => `
                                    <div class="column-card">
                                        <div class="column-name">${Utils.escapeHtml(col.column_name || '')}</div>
                                        <div class="column-score">评分: ${(col.overall_score || 0).toFixed(1)}</div>
                                        <div class="column-issues">
                                            ${(col.issues || []).length > 0 ? 
                                                `问题: ${(col.issues || []).slice(0, 2).map(issue => Utils.escapeHtml(String(issue))).join(', ')}` : 
                                                '无问题'
                                            }
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                            ${(results.parameter_columns || []).length > 10 ? 
                                `<div class="more-columns">还有 ${(results.parameter_columns || []).length - 10} 个参数列...</div>` : 
                                ''
                            }
                        </section>
                        ` : ''}

                        <!-- 关键问题 -->
                        <section class="key-issues">
                            <h2>⚠️ 关键问题</h2>
                            <div class="issues-list">
                                ${(results.key_issues || []).map(issue => `
                                    <div class="issue-item">
                                        <div class="issue-icon">⚠️</div>
                                        <div class="issue-content">${Utils.escapeHtml(String(issue))}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </section>

                        <!-- 改进建议 -->
                        <section class="recommendations">
                            <h2>💡 改进建议</h2>
                            <div class="recommendations-list">
                                ${(results.recommendations || []).map(rec => `
                                    <div class="recommendation-item">
                                        <div class="recommendation-icon">💡</div>
                                        <div class="recommendation-content">${Utils.escapeHtml(String(rec))}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </section>
                    </div>
                </div>
                ${this.getMermaidScript()}
            </body>
            </html>
        `;
    },

    /**
     * 获取质量等级文本
     */
    getQualityLevelText(level) {
        const levelMap = {
            'excellent': '优秀',
            'good': '良好',
            'fair': '一般',
            'poor': '较差',
            'critical': '严重'
        };
        return levelMap[level] || '未知';
    },

    /**
     * 获取分析结果页面样式
     */
    getAnalysisStyles() {
        return `
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f8f9fa;
                color: #333;
                line-height: 1.6;
            }
            
            .analysis-container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .analysis-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .analysis-header h1 {
                margin: 0 0 15px 0;
                font-size: 2.2em;
            }
            
            .analysis-meta {
                opacity: 0.9;
                font-size: 0.95em;
            }
            
            .analysis-meta span {
                margin: 0 15px;
            }
            
            .analysis-content {
                padding: 40px;
            }
            
            section {
                margin-bottom: 40px;
            }
            
            section h2 {
                color: #333;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            

            
            /* 内容样式 */
            .meaning-content, .logic-content, .details-content {
                background: #f8f9fa;
                padding: 25px;
                border-radius: 10px;
                border-left: 4px solid #667eea;
                white-space: pre-line;
            }
            
            /* 表格样式 */
            .mapping-table {
                overflow-x: auto;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            
            th {
                background-color: #667eea;
                color: white;
                font-weight: bold;
            }
            
            tr:nth-child(even) {
                background-color: #f8f9fa;
            }
            
            tr:hover {
                background-color: #e3f2fd;
            }
            
            /* 质量评分样式 */
            .score-display {
                display: flex;
                align-items: center;
                gap: 40px;
                margin-bottom: 30px;
            }
            
            .score-circle {
                width: 150px;
                height: 150px;
                border-radius: 50%;
                background: conic-gradient(#28a745 0deg, #28a745 ${(85 * 360) / 100}deg, #e9ecef ${(85 * 360) / 100}deg);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                position: relative;
                flex-shrink: 0;
            }
            
            .score-circle::before {
                content: '';
                width: 110px;
                height: 110px;
                background: white;
                border-radius: 50%;
                position: absolute;
            }
            
            .score-value {
                font-size: 2em;
                font-weight: bold;
                color: #333;
                z-index: 1;
            }
            
            .score-label {
                font-size: 0.9em;
                color: #666;
                z-index: 1;
            }
            
            .quality-metrics {
                flex: 1;
            }
            
            .metric-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid #eee;
            }
            
            .metric-name {
                font-weight: bold;
            }
            
            .metric-score {
                color: #667eea;
                font-weight: bold;
            }
            
            /* 推荐样式 */
            .recommendations-list {
                space-y: 15px;
            }
            
            .recommendation-item {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #17a2b8;
                margin-bottom: 15px;
            }
            
            .recommendation-type {
                font-weight: bold;
                color: #333;
                margin-bottom: 8px;
            }
            
            .recommendation-content {
                color: #555;
                line-height: 1.6;
            }
            
            /* 新增样式 - 质量等级 */
            .quality-level {
                flex: 1;
            }
            
            .level-badge {
                display: inline-block;
                padding: 10px 20px;
                border-radius: 25px;
                font-weight: bold;
                font-size: 1.1em;
            }
            
            .level-excellent {
                background: #d4edda;
                color: #155724;
            }
            
            .level-good {
                background: #d1ecf1;
                color: #0c5460;
            }
            
            .level-fair {
                background: #fff3cd;
                color: #856404;
            }
            
            .level-poor {
                background: #f8d7da;
                color: #721c24;
            }
            
            .level-critical {
                background: #f5c6cb;
                color: #721c24;
            }
            
            .level-unknown {
                background: #e2e3e5;
                color: #383d41;
            }
            
            /* 分布网格 */
            .distribution-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .distribution-item {
                text-align: center;
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border: 2px solid #e9ecef;
            }
            
            .distribution-count {
                font-size: 2.5em;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 5px;
            }
            
            .distribution-label {
                color: #666;
                font-weight: 500;
            }
            
            /* 列网格 */
            .columns-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .column-score {
                color: #667eea;
                font-weight: bold;
                margin-bottom: 8px;
            }
            
            .column-issues {
                color: #666;
                font-size: 0.9em;
                line-height: 1.4;
            }
            
            .more-columns {
                text-align: center;
                color: #666;
                font-style: italic;
                margin-top: 15px;
            }
            
            /* 问题列表 */
            .issues-list {
                space-y: 12px;
            }
            
            .issue-item {
                display: flex;
                align-items: flex-start;
                background: #fff3cd;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #ffc107;
                margin-bottom: 12px;
            }
            
            .issue-icon {
                margin-right: 12px;
                font-size: 1.2em;
                flex-shrink: 0;
            }
            
            .issue-content {
                color: #856404;
                line-height: 1.5;
            }
            
            /* 建议列表 */
            .recommendation-item {
                display: flex;
                align-items: flex-start;
                background: #d1ecf1;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #17a2b8;
                margin-bottom: 12px;
            }
            
            .recommendation-icon {
                margin-right: 12px;
                font-size: 1.2em;
                flex-shrink: 0;
            }
            
            @media print {
                body { background: white; padding: 0; }
                .analysis-container { box-shadow: none; }
                .analysis-header { background: #333 !important; }
            }
        `;
    },

    getMermaidScript() {
        return `
            <script>
                // 动态加载Mermaid脚本，避免document.write警告
                function loadMermaidScript() {
                    return new Promise((resolve, reject) => {
                        // 检查是否已经加载
                        if (window.mermaid) {
                            resolve();
                            return;
                        }
                        
                        // 创建script标签
                        const script = document.createElement('script');
                        script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js';
                        script.crossOrigin = 'anonymous';
                        script.onload = () => {
                            console.log('✅ Mermaid脚本加载成功');
                            resolve();
                        };
                        script.onerror = (error) => {
                            console.error('❌ Mermaid CDN加载失败，尝试使用备用CDN');
                            // 尝试备用CDN
                            const fallbackScript = document.createElement('script');
                            fallbackScript.src = 'https://unpkg.com/mermaid@10.6.1/dist/mermaid.min.js';
                            fallbackScript.crossOrigin = 'anonymous';
                            fallbackScript.onload = () => {
                                console.log('✅ Mermaid备用脚本加载成功');
                                resolve();
                            };
                            fallbackScript.onerror = () => {
                                console.error('❌ 备用CDN加载失败，尝试本地文件');
                                // 尝试本地文件
                                const localScript = document.createElement('script');
                                localScript.src = 'assets/js/libs/mermaid.min.js';
                                localScript.onload = () => {
                                    console.log('✅ Mermaid本地脚本加载成功');
                                    resolve();
                                };
                                localScript.onerror = () => {
                                    console.error('❌ 所有Mermaid加载方式都失败');
                                    reject(new Error('Mermaid脚本加载失败'));
                                };
                                document.head.appendChild(localScript);
                            };
                            document.head.appendChild(fallbackScript);
                        };
                        document.head.appendChild(script);
                    });
                }
                
                // 初始化Mermaid
                function initializeMermaid() {
                    if (window.mermaid) {
                        mermaid.initialize({
                            startOnLoad: false, // 手动控制渲染
                            theme: 'default',
                            flowchart: {
                                useMaxWidth: true,
                                htmlLabels: true
                            },
                            securityLevel: 'loose',
                            fontFamily: 'Microsoft YaHei, Arial, sans-serif'
                        });
                        return true;
                    }
                    return false;
                }
                
                // 渲染所有Mermaid图表
                async function renderMermaidDiagrams() {
                    try {
                        // 确保Mermaid已加载
                        await loadMermaidScript();
                        
                        // 初始化Mermaid
                        if (!initializeMermaid()) {
                            throw new Error('Mermaid初始化失败');
                        }
                        
                        const mermaidElements = document.querySelectorAll('.mermaid');
                        console.log(\`🎨 找到 \${mermaidElements.length} 个Mermaid图表待渲染\`);
                        
                        for (let i = 0; i < mermaidElements.length; i++) {
                            const element = mermaidElements[i];
                            if (!element.getAttribute('data-processed')) {
                                try {
                                    const graphId = 'mermaid-graph-' + i + '-' + Date.now();
                                    const graphDefinition = element.textContent.trim();
                                    
                                    console.log(\`🎨 渲染第 \${i + 1} 个图表，ID: \${graphId}\`);
                                    console.log(\`📋 图表定义: \${graphDefinition.substring(0, 100)}...\`);
                                    
                                    // 使用新的mermaid API
                                    const { svg } = await mermaid.render(graphId, graphDefinition);
                                    element.innerHTML = svg;
                                    element.setAttribute('data-processed', 'true');
                                    console.log(\`✅ 图表 \${i + 1} 渲染成功\`);
                                } catch (error) {
                                    console.error(\`❌ 图表 \${i + 1} 渲染失败:\`, error);
                                    element.innerHTML = \`
                                        <div style="color: #d63384; background: #f8d7da; border: 1px solid #f5c2c7; border-radius: 4px; padding: 15px; margin: 10px 0; font-family: monospace;">
                                            <strong>🚫 Mermaid图表渲染失败</strong><br/>
                                            <details style="margin-top: 8px;">
                                                <summary style="cursor: pointer; color: #842029;">查看错误详情</summary>
                                                <pre style="margin-top: 8px; font-size: 12px; white-space: pre-wrap;">\${error.message}</pre>
                                            </details>
                                        </div>
                                    \`;
                                    element.setAttribute('data-processed', 'error');
                                }
                            }
                        }
                        
                        console.log('🎉 所有Mermaid图表渲染完成');
                    } catch (error) {
                        console.error('❌ Mermaid图表渲染过程失败:', error);
                        // 显示全局错误信息
                        const mermaidElements = document.querySelectorAll('.mermaid:not([data-processed])');
                        mermaidElements.forEach(element => {
                            element.innerHTML = \`
                                <div style="color: #d63384; background: #f8d7da; border: 1px solid #f5c2c7; border-radius: 4px; padding: 15px; margin: 10px 0; text-align: center;">
                                    <strong>🚫 Mermaid服务不可用</strong><br/>
                                    <small style="color: #842029;">网络连接问题或CDN服务异常，请稍后重试</small>
                                </div>
                            \`;
                            element.setAttribute('data-processed', 'failed');
                        });
                    }
                }
                
                // 页面加载完成后延迟渲染，确保DOM完全加载
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', function() {
                        setTimeout(renderMermaidDiagrams, 200);
                    });
                } else {
                    setTimeout(renderMermaidDiagrams, 200);
                }
                
                // 导出重新渲染函数，供外部调用
                window.rerenderMermaid = renderMermaidDiagrams;
            </script>
        `;
    },

    generateErrorHTML(message) {
        return `
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>错误</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
                        padding: 50px;
                        background: #f5f5f5;
                    }
                    .error-container {
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        text-align: center;
                    }
                    .error-icon {
                        font-size: 48px;
                        margin-bottom: 20px;
                    }
                    .error-message {
                        color: #dc3545;
                        font-size: 18px;
                        margin-bottom: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="error-container">
                    <div class="error-icon">❌</div>
                    <div class="error-message">${Utils.escapeHtml(message)}</div>
                    <button onclick="window.close()">关闭窗口</button>
                </div>
            </body>
            </html>
        `;
    }
}; 