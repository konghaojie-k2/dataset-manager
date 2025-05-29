/**
 * 分析功能模块
 */

const Analysis = {
    /**
     * 显示LangGraph工作流
     */
    showWorkflow() {
        const workflowEl = Utils.dom.find('#langGraphFlow');
        if (workflowEl) {
            workflowEl.style.display = 'block';
            AppState.ui.showAnalysisFlow = true;
            Utils.log.debug('显示分析工作流');
        }
    },

    /**
     * 隐藏工作流
     */
    hideWorkflow() {
        const workflowEl = Utils.dom.find('#langGraphFlow');
        if (workflowEl) {
            workflowEl.style.display = 'none';
            AppState.ui.showAnalysisFlow = false;
        }
    },

    /**
     * 重置所有步骤状态
     */
    resetSteps() {
        CONFIG.WORKFLOW.STEPS.forEach(step => {
            const element = Utils.dom.find(`#step-${step.id}`);
            if (element) {
                element.className = 'flow-step';
            }
        });
        AppState.ui.activeAnalysisStep = null;
        Utils.log.debug('重置工作流步骤状态');
    },

    /**
     * 更新步骤状态
     */
    updateStep(stepId, status) {
        const element = Utils.dom.find(`#step-${stepId}`);
        if (element) {
            element.className = `flow-step ${status}`;
            AppState.ui.activeAnalysisStep = status === 'active' ? stepId : AppState.ui.activeAnalysisStep;
            Utils.log.debug(`更新步骤状态: ${stepId} -> ${status}`);
        }
    },

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
            
            if (results) {
                this.openBusinessAnalysisWindow(results);
            } else {
                UI.showMessage('业务分析结果为空', CONFIG.MESSAGE.TYPES.WARNING);
            }

        } catch (error) {
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
            
            if (results) {
                this.openQualityAnalysisWindow(results);
            } else {
                UI.showMessage('质量分析结果为空', CONFIG.MESSAGE.TYPES.WARNING);
            }

        } catch (error) {
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
        const analysisWindow = window.open('', '_blank', 'width=1400,height=900');
        
        const htmlContent = this.generateBusinessAnalysisHTML(results);
        analysisWindow.document.write(htmlContent);
        analysisWindow.document.close();
    },

    /**
     * 打开质量分析结果窗口
     */
    openQualityAnalysisWindow(results) {
        const analysisWindow = window.open('', '_blank', 'width=1400,height=900');
        
        const htmlContent = this.generateQualityAnalysisHTML(results);
        analysisWindow.document.write(htmlContent);
        analysisWindow.document.close();
    },

    /**
     * 生成业务分析结果HTML
     */
    generateBusinessAnalysisHTML(results) {
        return `
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>业务分析结果</title>
                <style>
                    ${this.getAnalysisStyles()}
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
                        <!-- 列识别结果 -->
                        <section class="column-identification">
                            <h2>📊 列识别与分析结果</h2>
                            <div class="column-grid">
                                ${(results.columns || []).map(column => `
                                    <div class="column-card ${column.type}-column">
                                        <div class="column-name">${Utils.escapeHtml(column.name)}</div>
                                        <div class="column-type type-${column.type}">
                                            ${column.type === 'device' ? '设备列' : column.type === 'time' ? '时间列' : '业务列'}
                                        </div>
                                        <div class="column-description">${Utils.escapeHtml(column.description || '')}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </section>

                        <!-- 业务含义分析 -->
                        <section class="business-meaning">
                            <h2>💼 业务含义分析</h2>
                            <div class="meaning-content">
                                ${Utils.escapeHtml(results.business_meaning || '暂无业务含义分析结果')}
                            </div>
                        </section>

                        <!-- 控制逻辑分析 -->
                        <section class="control-logic">
                            <h2>⚙️ 控制逻辑分析</h2>
                            <div class="logic-content">
                                ${Utils.escapeHtml(results.control_logic || '暂无控制逻辑分析结果')}
                            </div>
                        </section>

                        <!-- 中文Schema映射 -->
                        <section class="schema-mapping">
                            <h2>📋 中文Schema映射</h2>
                            <div class="mapping-table">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>原始列名</th>
                                            <th>中文名称</th>
                                            <th>数据类型</th>
                                            <th>业务描述</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${(results.schema_mapping || []).map(mapping => `
                                            <tr>
                                                <td>${Utils.escapeHtml(mapping.original_name || '')}</td>
                                                <td>${Utils.escapeHtml(mapping.chinese_name || '')}</td>
                                                <td>${Utils.escapeHtml(mapping.data_type || '')}</td>
                                                <td>${Utils.escapeHtml(mapping.description || '')}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </section>
                    </div>
                </div>
            </body>
            </html>
        `;
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
                                    <div class="score-value">${results.overall_score || 0}%</div>
                                    <div class="score-label">总体评分</div>
                                </div>
                                <div class="quality-metrics">
                                    ${(results.quality_metrics || []).map(metric => `
                                        <div class="metric-item">
                                            <span class="metric-name">${Utils.escapeHtml(metric.name || '')}</span>
                                            <span class="metric-score">${metric.score || 0}%</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </section>

                        <!-- 详细分析 -->
                        <section class="quality-details">
                            <h2>📋 详细分析</h2>
                            <div class="details-content">
                                ${Utils.escapeHtml(results.detailed_analysis || '暂无详细分析结果')}
                            </div>
                        </section>

                        <!-- 问题与建议 -->
                        <section class="recommendations">
                            <h2>💡 问题与建议</h2>
                            <div class="recommendations-list">
                                ${(results.recommendations || []).map(rec => `
                                    <div class="recommendation-item">
                                        <div class="recommendation-type">${Utils.escapeHtml(rec.type || '建议')}</div>
                                        <div class="recommendation-content">${Utils.escapeHtml(rec.content || '')}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </section>
                    </div>
                </div>
            </body>
            </html>
        `;
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
            
            /* 列识别样式 */
            .column-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }
            
            .column-card {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                border-left: 5px solid #667eea;
                transition: all 0.3s ease;
            }
            
            .column-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            }
            
            .column-card.device-column {
                border-left-color: #28a745;
                background: #f0fff4;
            }
            
            .column-card.time-column {
                border-left-color: #ffc107;
                background: #fffbf0;
            }
            
            .column-card.business-column {
                border-left-color: #17a2b8;
                background: #f0f9ff;
            }
            
            .column-name {
                font-size: 1.2em;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
            
            .column-type {
                display: inline-block;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 0.8em;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .type-device {
                background: #d4edda;
                color: #155724;
            }
            
            .type-time {
                background: #fff3cd;
                color: #856404;
            }
            
            .type-business {
                background: #d1ecf1;
                color: #0c5460;
            }
            
            .column-description {
                color: #666;
                line-height: 1.5;
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
            
            @media print {
                body { background: white; padding: 0; }
                .analysis-container { box-shadow: none; }
                .analysis-header { background: #333 !important; }
            }
        `;
    }
}; 