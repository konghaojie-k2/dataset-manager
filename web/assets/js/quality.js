/**
 * 数据质量分析功能
 */

class DataQualityAnalyzer {
    constructor() {
        this.apiBase = '/api/v1';
        this.currentDatasets = [];
        this.init();
    }

    init() {
        this.loadDatasets();
    }

    async loadDatasets() {
        try {
            // 调用API获取数据集列表
            const response = await fetch(`${this.apiBase}/datasets`);
            const datasets = await response.json();

            if (response.ok) {
                this.currentDatasets = datasets;
                this.updateDatasetSelect();
            } else {
                throw new Error('获取数据集列表失败');
            }
        } catch (error) {
            console.error('加载数据集失败:', error);
            showMessage('加载数据集失败', 'error');
        }
    }

    updateDatasetSelect() {
        const select = document.getElementById('datasetSelect');
        if (!select) return;

        // 清空现有选项
        select.innerHTML = '<option value="">请选择数据集...</option>';

        // 添加数据集选项
        this.currentDatasets.forEach(dataset => {
            const option = document.createElement('option');
            option.value = dataset.id;
            option.textContent = dataset.name;
            select.appendChild(option);
        });
    }

    async detectColumnTypes() {
        const datasetId = document.getElementById('datasetSelect').value;
        if (!datasetId) {
            showMessage('请先选择数据集', 'warning');
            return;
        }

        try {
            showLoading(true);
            const response = await fetch(`${this.apiBase}/data-quality/column-types/${datasetId}`);
            const data = await response.json();

            if (response.ok) {
                this.displayColumnTypes(data);
                showMessage('列类型检测完成', 'success');
            } else {
                throw new Error(data.detail || '检测失败');
            }
        } catch (error) {
            console.error('列类型检测失败:', error);
            showMessage('列类型检测失败: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    }

    displayColumnTypes(data) {
        const container = document.getElementById('columnTypesContent');
        const resultDiv = document.getElementById('columnTypesResult');

        if (!container || !resultDiv) return;

        let html = `
            <div class="column-types-summary">
                <div class="summary-metrics">
                    <div class="summary-item">
                        <div class="summary-value">${data.basic_info.total_columns}</div>
                        <div class="summary-label">总列数</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">${data.basic_info.total_rows}</div>
                        <div class="summary-label">总行数</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">${Object.keys(data.column_types).length}</div>
                        <div class="summary-label">已识别列数</div>
                    </div>
                </div>
            </div>
            <div class="column-types-table">
                <table>
                    <thead>
                        <tr>
                            <th>列名</th>
                            <th>类型</th>
                            <th>标签</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        for (const [column, type] of Object.entries(data.column_types)) {
            const typeLabel = this.getTypeLabel(type);
            const typeBadge = this.getTypeBadge(type);
            html += `
                <tr>
                    <td>${column}</td>
                    <td>${typeLabel}</td>
                    <td>${typeBadge}</td>
                </tr>
            `;
        }

        html += '</tbody></table></div>';
        container.innerHTML = html;
        resultDiv.style.display = 'block';
    }

    async startQualityAnalysis() {
        const datasetId = document.getElementById('datasetSelect').value;
        const userRequirements = document.getElementById('userRequirements').value;

        if (!datasetId) {
            showMessage('请先选择数据集', 'warning');
            return;
        }

        // 显示分析状态
        document.getElementById('analysisStatus').style.display = 'block';
        document.getElementById('qualityResults').style.display = 'none';
        document.getElementById('analyzeBtn').disabled = true;

        try {
            const request = {
                dataset_id: datasetId,
                user_requirements: userRequirements || null,
                analysis_config: {}
            };

            const response = await fetch(`${this.apiBase}/datasets/${datasetId}/start-quality-analysis`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // 分析已启动，等待完成后获取结果
                showMessage('质量分析已启动，正在处理...', 'success');
                
                // 轮询检查分析状态
                await this.pollAnalysisStatus(datasetId);
            } else {
                throw new Error(data.message || '启动分析失败');
            }
        } catch (error) {
            console.error('数据质量分析失败:', error);
            showMessage('数据质量分析失败: ' + error.message, 'error');
        } finally {
            document.getElementById('analysisStatus').style.display = 'none';
            document.getElementById('analyzeBtn').disabled = false;
        }
    }

    async pollAnalysisStatus(datasetId) {
        const maxAttempts = 30; // 最多等待5分钟 (30 * 10秒)
        let attempts = 0;

        const checkStatus = async () => {
            try {
                attempts++;
                
                // 获取数据集状态
                const response = await fetch(`${this.apiBase}/datasets/${datasetId}`);
                const dataset = await response.json();

                if (response.ok) {
                    if (dataset.processing_status === 'quality_completed') {
                        // 分析完成，获取结果
                        await this.loadAnalysisResults(datasetId);
                        return;
                    } else if (dataset.processing_status === 'quality_failed') {
                        throw new Error('质量分析失败');
                    } else if (attempts >= maxAttempts) {
                        throw new Error('分析超时，请稍后查看结果');
                    } else {
                        // 继续等待
                        setTimeout(checkStatus, 10000); // 10秒后再次检查
                    }
                } else {
                    throw new Error('获取分析状态失败');
                }
            } catch (error) {
                console.error('检查分析状态失败:', error);
                showMessage('检查分析状态失败: ' + error.message, 'error');
                document.getElementById('analysisStatus').style.display = 'none';
                document.getElementById('analyzeBtn').disabled = false;
            }
        };

        // 开始检查
        setTimeout(checkStatus, 5000); // 5秒后开始第一次检查
    }

    async loadAnalysisResults(datasetId) {
        try {
            const response = await fetch(`${this.apiBase}/datasets/${datasetId}/quality-analysis-results`);
            const results = await response.json();

            if (response.ok) {
                this.displayQualityResults(results);
                showMessage('数据质量分析完成', 'success');
            } else {
                throw new Error('获取分析结果失败');
            }
        } catch (error) {
            console.error('获取分析结果失败:', error);
            showMessage('获取分析结果失败: ' + error.message, 'error');
        } finally {
            document.getElementById('analysisStatus').style.display = 'none';
            document.getElementById('analyzeBtn').disabled = false;
        }
    }

    displayQualityResults(report) {
        // 显示整体概览
        this.displayOverview(report);
        
        // 显示列类型分布
        if (report.summary && report.summary.column_breakdown) {
            this.displayColumnTypeDistribution(report.summary.column_breakdown);
        }

        // 显示详细分析结果
        this.displayTimeColumns(report.time_columns || []);
        this.displayParameterColumns(report.parameter_columns || []);
        this.displayCategoryColumns(report.category_columns || []);

        // 显示问题和建议
        this.displayKeyIssues(report.key_issues || []);
        this.displayRecommendations(report.recommendations || []);

        document.getElementById('qualityResults').style.display = 'block';
    }

    displayOverview(report) {
        const overallScore = document.getElementById('overallScore');
        const qualityLevel = document.getElementById('qualityLevel');
        const analyzedColumns = document.getElementById('analyzedColumns');
        const highQualityColumns = document.getElementById('highQualityColumns');

        if (overallScore) {
            const score = report.overall_score || 0;
            overallScore.textContent = score.toFixed(1);
            overallScore.className = `metric-value ${this.getQualityClass(report.quality_level)}`;
        }

        if (qualityLevel) {
            qualityLevel.textContent = this.getQualityLevelText(report.quality_level);
        }

        if (analyzedColumns) {
            const analyzed = report.analyzed_columns || 0;
            const total = report.total_columns || 0;
            analyzedColumns.textContent = `${analyzed}/${total}`;
        }

        if (highQualityColumns) {
            highQualityColumns.textContent = report.high_quality_columns || 0;
        }
    }

    displayColumnTypeDistribution(breakdown) {
        const container = document.getElementById('columnTypeDistribution');
        if (!container) return;

        container.innerHTML = `
            <div class="distribution-item">
                <div class="distribution-value time">${breakdown.time_columns}</div>
                <div class="distribution-label">时间列</div>
            </div>
            <div class="distribution-item">
                <div class="distribution-value parameter">${breakdown.parameter_columns}</div>
                <div class="distribution-label">参数列</div>
            </div>
            <div class="distribution-item">
                <div class="distribution-value category">${breakdown.category_columns}</div>
                <div class="distribution-label">类目列</div>
            </div>
        `;
    }

    displayTimeColumns(columns) {
        const container = document.getElementById('timeColumnsContent');
        if (!container) return;

        if (columns.length === 0) {
            container.innerHTML = '<p class="no-data">暂无时间列数据</p>';
            return;
        }

        let html = '';
        columns.forEach(column => {
            html += this.createColumnCard(column, 'time');
        });
        container.innerHTML = html;
    }

    displayParameterColumns(columns) {
        const container = document.getElementById('parameterColumnsContent');
        if (!container) return;

        if (columns.length === 0) {
            container.innerHTML = '<p class="no-data">暂无参数列数据</p>';
            return;
        }

        let html = '';
        columns.forEach(column => {
            html += this.createColumnCard(column, 'parameter');
        });
        container.innerHTML = html;
    }

    displayCategoryColumns(columns) {
        const container = document.getElementById('categoryColumnsContent');
        if (!container) return;

        if (columns.length === 0) {
            container.innerHTML = '<p class="no-data">暂无类目列数据</p>';
            return;
        }

        let html = '';
        columns.forEach(column => {
            html += this.createColumnCard(column, 'category');
        });
        container.innerHTML = html;
    }

    createColumnCard(column, type) {
        const qualityClass = this.getQualityClass(column.quality_level);
        const issueCount = column.issues ? column.issues.length : 0;
        
        return `
            <div class="column-card">
                <div class="column-card-header">
                    <div class="column-name">${column.column_name}</div>
                    <div class="quality-badge ${column.quality_level}">${column.overall_score.toFixed(1)}</div>
                </div>
                <div class="column-info">
                    质量等级: ${this.getQualityLevelText(column.quality_level)}
                </div>
                ${issueCount > 0 ? `
                    <div class="column-issues">
                        <span class="issue-badge">${issueCount} 个问题</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    displayKeyIssues(issues) {
        const container = document.getElementById('keyIssuesContent');
        if (!container) return;

        if (issues.length === 0) {
            container.innerHTML = '<p class="no-data">暂无关键问题</p>';
            return;
        }

        let html = '';
        issues.forEach(issue => {
            html += `
                <div class="issue-item">
                    <div class="issue-icon">⚠️</div>
                    <div class="issue-text">${issue}</div>
                </div>
            `;
        });
        container.innerHTML = html;
    }

    displayRecommendations(recommendations) {
        const container = document.getElementById('recommendationsContent');
        if (!container) return;

        if (recommendations.length === 0) {
            container.innerHTML = '<p class="no-data">暂无改进建议</p>';
            return;
        }

        let html = '';
        recommendations.forEach(rec => {
            html += `
                <div class="recommendation-item">
                    <div class="recommendation-icon">💡</div>
                    <div class="recommendation-text">${rec}</div>
                </div>
            `;
        });
        container.innerHTML = html;
    }

    getTypeLabel(type) {
        const labels = {
            'time': '时间列',
            'parameter': '参数列',
            'category': '类目列'
        };
        return labels[type] || type;
    }

    getTypeBadge(type) {
        const badges = {
            'time': '<span class="type-badge time">时间</span>',
            'parameter': '<span class="type-badge parameter">参数</span>',
            'category': '<span class="type-badge category">类目</span>'
        };
        return badges[type] || `<span class="type-badge">${type}</span>`;
    }

    getQualityClass(level) {
        const classes = {
            'excellent': 'quality-excellent',
            'good': 'quality-good',
            'fair': 'quality-fair',
            'poor': 'quality-poor'
        };
        return classes[level] || 'quality-poor';
    }

    getQualityLevelText(level) {
        const texts = {
            'excellent': '优秀',
            'good': '良好',
            'fair': '一般',
            'poor': '较差'
        };
        return texts[level] || level;
    }
}

// 全局函数
function switchTab(tabName) {
    // 隐藏所有标签页内容
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });

    // 移除所有导航标签的激活状态
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
        tab.classList.remove('active');
    });

    // 显示选中的标签页内容
    const targetTab = document.getElementById(tabName + 'Tab');
    if (targetTab) {
        targetTab.classList.add('active');
    }

    // 激活对应的导航标签
    const activeNavTab = document.querySelector(`[onclick="switchTab('${tabName}')"]`);
    if (activeNavTab) {
        activeNavTab.classList.add('active');
    }

    // 如果切换到质量分析标签页，初始化数据质量分析器
    if (tabName === 'quality' && !window.qualityAnalyzer) {
        window.qualityAnalyzer = new DataQualityAnalyzer();
    }
}

function detectColumnTypes() {
    if (window.qualityAnalyzer) {
        window.qualityAnalyzer.detectColumnTypes();
    }
}

function startQualityAnalysis() {
    if (window.qualityAnalyzer) {
        window.qualityAnalyzer.startQualityAnalysis();
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 默认显示数据集管理标签页
    switchTab('datasets');
}); 