/**
 * 报告管理模块
 */

const Reports = {
    /**
     * 查看质量报告
     */
    async viewQualityReport(datasetId) {
        try {
            UI.showLoading(true);
            Utils.log.debug('查看质量报告:', datasetId);

            // 获取质量报告数据
            const report = await API.analysis.getQualityReport(datasetId);
            
            if (report) {
                this.openQualityReportWindow(report);
            } else {
                UI.showMessage('质量报告数据为空', CONFIG.MESSAGE.TYPES.WARNING);
            }

        } catch (error) {
            Utils.log.error('查看质量报告失败:', error);
            UI.showMessage('获取质量报告失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            UI.showLoading(false);
        }
    },

    /**
     * 查看业务分析报告
     */
    async viewBusinessAnalysis(datasetId) {
        try {
            UI.showLoading(true);
            Utils.log.debug('查看业务分析报告:', datasetId);

            // 获取业务分析报告数据
            const report = await API.analysis.getBusinessReport(datasetId);
            
            if (report) {
                this.openBusinessReportWindow(report);
            } else {
                UI.showMessage('业务分析报告数据为空', CONFIG.MESSAGE.TYPES.WARNING);
            }

        } catch (error) {
            Utils.log.error('查看业务分析报告失败:', error);
            UI.showMessage('获取业务分析报告失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            UI.showLoading(false);
        }
    },

    /**
     * 打开质量报告窗口
     */
    openQualityReportWindow(report) {
        const reportWindow = window.open('', '_blank', 'width=1200,height=800');
        
        const htmlContent = this.generateQualityReportHTML(report);
        reportWindow.document.write(htmlContent);
        reportWindow.document.close();
    },

    /**
     * 打开业务分析报告窗口
     */
    openBusinessReportWindow(report) {
        const reportWindow = window.open('', '_blank', 'width=1200,height=800');
        
        const htmlContent = this.generateBusinessReportHTML(report);
        reportWindow.document.write(htmlContent);
        reportWindow.document.close();
    },

    /**
     * 生成质量报告HTML
     */
    generateQualityReportHTML(report) {
        return `
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>数据质量报告</title>
                <style>
                    ${this.getReportStyles()}
                </style>
            </head>
            <body>
                <div class="report-container">
                    <div class="report-header">
                        <h1>🎯 数据质量评估报告</h1>
                        <div class="report-meta">
                            <span>生成时间: ${Utils.formatFullDateTime(new Date())}</span>
                            <span>数据集: ${Utils.escapeHtml(report.dataset_name || '未知')}</span>
                        </div>
                    </div>

                    <div class="report-content">
                        <!-- 质量评分概览 -->
                        <section class="quality-overview">
                            <h2>📊 质量评分概览</h2>
                            <div class="score-display">
                                <div class="score-circle">
                                    <div class="score-value">${report.overall_score || 0}%</div>
                                    <div class="score-label">总体评分</div>
                                </div>
                                <div class="score-details">
                                    <div class="score-item">
                                        <span class="score-metric">完整性</span>
                                        <span class="score-bar">
                                            <span class="score-fill" style="width: ${report.completeness_score || 0}%"></span>
                                        </span>
                                        <span class="score-number">${report.completeness_score || 0}%</span>
                                    </div>
                                    <div class="score-item">
                                        <span class="score-metric">准确性</span>
                                        <span class="score-bar">
                                            <span class="score-fill" style="width: ${report.accuracy_score || 0}%"></span>
                                        </span>
                                        <span class="score-number">${report.accuracy_score || 0}%</span>
                                    </div>
                                    <div class="score-item">
                                        <span class="score-metric">一致性</span>
                                        <span class="score-bar">
                                            <span class="score-fill" style="width: ${report.consistency_score || 0}%"></span>
                                        </span>
                                        <span class="score-number">${report.consistency_score || 0}%</span>
                                    </div>
                                    <div class="score-item">
                                        <span class="score-metric">有效性</span>
                                        <span class="score-bar">
                                            <span class="score-fill" style="width: ${report.validity_score || 0}%"></span>
                                        </span>
                                        <span class="score-number">${report.validity_score || 0}%</span>
                                    </div>
                                </div>
                            </div>
                        </section>

                        <!-- 详细分析 -->
                        <section class="quality-details">
                            <h2>📋 详细分析</h2>
                            <div class="analysis-text">
                                ${Utils.escapeHtml(report.detailed_analysis || '暂无详细分析内容')}
                            </div>
                        </section>

                        <!-- 问题与建议 -->
                        <section class="quality-recommendations">
                            <h2>💡 问题与建议</h2>
                            <div class="recommendations-list">
                                ${(report.recommendations || []).map(rec => 
                                    `<div class="recommendation-item">
                                        <div class="recommendation-type">${rec.type || '建议'}</div>
                                        <div class="recommendation-text">${Utils.escapeHtml(rec.description || '')}</div>
                                    </div>`
                                ).join('')}
                            </div>
                        </section>
                    </div>
                </div>
            </body>
            </html>
        `;
    },

    /**
     * 生成业务分析报告HTML
     */
    generateBusinessReportHTML(report) {
        return `
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>业务分析报告</title>
                <style>
                    ${this.getReportStyles()}
                </style>
            </head>
            <body>
                <div class="report-container">
                    <div class="report-header">
                        <h1>💼 业务分析报告</h1>
                        <div class="report-meta">
                            <span>生成时间: ${Utils.formatFullDateTime(new Date())}</span>
                            <span>数据集: ${Utils.escapeHtml(report.dataset_name || '未知')}</span>
                        </div>
                    </div>

                    <div class="report-content">
                        <!-- 业务概述 -->
                        <section class="business-overview">
                            <h2>📈 业务概述</h2>
                            <div class="overview-text">
                                ${Utils.escapeHtml(report.business_overview || '暂无业务概述')}
                            </div>
                        </section>

                        <!-- 关键指标 -->
                        <section class="key-metrics">
                            <h2>📊 关键指标</h2>
                            <div class="metrics-grid">
                                ${(report.key_metrics || []).map(metric => 
                                    `<div class="metric-card">
                                        <div class="metric-value">${metric.value || '0'}</div>
                                        <div class="metric-label">${Utils.escapeHtml(metric.label || '')}</div>
                                        <div class="metric-description">${Utils.escapeHtml(metric.description || '')}</div>
                                    </div>`
                                ).join('')}
                            </div>
                        </section>

                        <!-- 业务洞察 -->
                        <section class="business-insights">
                            <h2>💡 业务洞察</h2>
                            <div class="insights-list">
                                ${(report.insights || []).map(insight => 
                                    `<div class="insight-item">
                                        <div class="insight-title">${Utils.escapeHtml(insight.title || '')}</div>
                                        <div class="insight-content">${Utils.escapeHtml(insight.content || '')}</div>
                                    </div>`
                                ).join('')}
                            </div>
                        </section>

                        <!-- 控制原理 -->
                        <section class="control-principles">
                            <h2>⚙️ 控制原理分析</h2>
                            <div class="principles-text">
                                ${Utils.escapeHtml(report.control_principles || '暂无控制原理分析')}
                            </div>
                        </section>

                        <!-- 操作建议 -->
                        <section class="operation-recommendations">
                            <h2>🎯 操作建议</h2>
                            <div class="recommendations-list">
                                ${(report.operation_recommendations || []).map(rec => 
                                    `<div class="recommendation-item">
                                        <div class="recommendation-priority">${rec.priority || '一般'}</div>
                                        <div class="recommendation-text">${Utils.escapeHtml(rec.description || '')}</div>
                                    </div>`
                                ).join('')}
                            </div>
                        </section>
                    </div>
                </div>
            </body>
            </html>
        `;
    },

    /**
     * 获取报告样式
     */
    getReportStyles() {
        return `
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f8f9fa;
                color: #333;
                line-height: 1.6;
            }
            
            .report-container {
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .report-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .report-header h1 {
                margin: 0 0 15px 0;
                font-size: 2.2em;
            }
            
            .report-meta {
                opacity: 0.9;
                font-size: 0.95em;
            }
            
            .report-meta span {
                margin: 0 15px;
            }
            
            .report-content {
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
            
            /* 质量评分样式 */
            .quality-overview {
                background: #f8f9fa;
                padding: 25px;
                border-radius: 10px;
            }
            
            .score-display {
                display: flex;
                align-items: center;
                gap: 40px;
            }
            
            .score-circle {
                width: 150px;
                height: 150px;
                border-radius: 50%;
                background: conic-gradient(#28a745 0deg, #28a745 ${(80 * 360) / 100}deg, #e9ecef ${(80 * 360) / 100}deg);
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
            
            .score-details {
                flex: 1;
            }
            
            .score-item {
                display: flex;
                align-items: center;
                margin-bottom: 15px;
                gap: 15px;
            }
            
            .score-metric {
                width: 80px;
                font-weight: bold;
                flex-shrink: 0;
            }
            
            .score-bar {
                flex: 1;
                height: 20px;
                background: #e9ecef;
                border-radius: 10px;
                overflow: hidden;
                position: relative;
            }
            
            .score-fill {
                height: 100%;
                background: linear-gradient(90deg, #28a745, #20c997);
                transition: width 0.3s ease;
            }
            
            .score-number {
                width: 50px;
                text-align: right;
                font-weight: bold;
                flex-shrink: 0;
            }
            
            /* 通用样式 */
            .analysis-text, .overview-text, .principles-text {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                white-space: pre-line;
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }
            
            .metric-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                border: 2px solid #e9ecef;
                transition: all 0.3s ease;
            }
            
            .metric-card:hover {
                border-color: #667eea;
                transform: translateY(-3px);
            }
            
            .metric-value {
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 5px;
            }
            
            .metric-label {
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .metric-description {
                font-size: 0.9em;
                color: #666;
            }
            
            .insights-list, .recommendations-list {
                space-y: 15px;
            }
            
            .insight-item, .recommendation-item {
                background: #f8f9fa;
                padding: 15px 20px;
                border-radius: 8px;
                border-left: 4px solid #17a2b8;
                margin-bottom: 15px;
            }
            
            .insight-title, .recommendation-type, .recommendation-priority {
                font-weight: bold;
                color: #333;
                margin-bottom: 8px;
            }
            
            .insight-content, .recommendation-text {
                color: #555;
                line-height: 1.6;
            }
            
            @media print {
                body { background: white; padding: 0; }
                .report-container { box-shadow: none; }
                .report-header { background: #333 !important; }
            }
        `;
    }
}; 