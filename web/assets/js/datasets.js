/**
 * 数据集管理模块
 */

const Datasets = {
    /**
     * 渲染数据集列表
     */
    render() {
        const startIndex = (AppState.pagination.currentPage - 1) * AppState.pagination.pageSize;
        const endIndex = startIndex + AppState.pagination.pageSize;
        const currentPageDatasets = AppState.datasets.slice(startIndex, endIndex);
        
        this.renderDatasetCards(currentPageDatasets);
        Pagination.update();
        

        
        Utils.log.debug('数据集列表渲染完成:', currentPageDatasets.length, '个数据集');
    },

    /**
     * 渲染数据集卡片
     */
    renderDatasetCards(datasets) {
        const container = Utils.dom.find('#datasetsList');
        if (!container) return;

        if (datasets.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">暂无数据集，请上传第一个数据集</p>';
            return;
        }

        // 添加列表头部
        const headerHtml = this.generateHeaderHtml();
        
        // 生成数据集卡片HTML
        const datasetsHtml = datasets.map(dataset => this.generateDatasetCardHtml(dataset)).join('');

        container.innerHTML = headerHtml + datasetsHtml;
    },

    /**
     * 生成列表头部HTML
     */
    generateHeaderHtml() {
        return `
            <div class="datasets-header">
                <div class="header-main-info">
                    <div class="header-name-section">数据集名称</div>
                    <div class="header-stats">
                        <div class="header-stat-item">文件大小</div>
                        <div class="header-stat-item">列数</div>
                        <div class="header-stat-item">质量评估</div>
                        <div class="header-stat-item">业务理解</div>
                    </div>
                </div>
                <div class="header-actions">操作</div>
            </div>
        `;
    },

    /**
     * 生成数据集卡片HTML
     */
    generateDatasetCardHtml(dataset) {
        const isDuplicate = dataset.version_type === 'duplicate';
        const cardClass = isDuplicate ? 'dataset-card duplicate-dataset' : 'dataset-card';
        
        return `
            <div class="${cardClass}">
                <div class="dataset-main-info">
                    <div class="dataset-name-section">
                        <div class="dataset-name">
                            ${Utils.escapeHtml(dataset.name)}
                            ${isDuplicate ? '<span class="duplicate-badge" title="重复数据">🔗 重复</span>' : ''}
                        </div>
                        <div class="dataset-upload-time">${Utils.formatDate(dataset.upload_time)}</div>
                        ${dataset.description ? `<div class="dataset-description" title="${Utils.escapeHtml(dataset.description)}">${Utils.escapeHtml(dataset.description)}</div>` : ''}
                        ${this.generateTagsHtml(dataset.tags, dataset.id)}
                    </div>
                    <div class="dataset-stats">
                        <div class="stat-item">
                            <div class="stat-value">${Utils.formatFileSize(dataset.file_size)}</div>
                            <div class="stat-label">文件大小</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${dataset.columns ? dataset.columns.length : '未分析'}</div>
                            <div class="stat-label">列数</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value version-info" onclick="Datasets.showVersionInfo('${dataset.id}')" title="点击查看版本详情">
                                ${this.getVersionDisplay(dataset)}
                            </div>
                            <div class="stat-label">版本</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-status">${this.getQualityStatus(dataset)}</div>
                            <div class="stat-label">质量评估</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-status">${this.getBusinessStatus(dataset)}</div>
                            <div class="stat-label">业务理解</div>
                        </div>
                    </div>
                </div>
                <div class="dataset-actions">
                    ${this.generateActionButtonsHtml(dataset)}
                </div>
            </div>
        `;
    },

    /**
     * 生成标签HTML
     */
    generateTagsHtml(tags, datasetId) {
        const tagsHtml = tags && tags.length > 0 
            ? tags.map(tag => `<span class="tag">${Utils.escapeHtml(tag)}</span>`).join('')
            : '';
        
        return `
            <div class="dataset-tags" data-dataset-id="${datasetId}">
                ${tagsHtml}
                <span class="tag-edit-trigger" onclick="Datasets.editDatasetTags('${datasetId}')" title="编辑标签">
                    ${tags && tags.length > 0 ? '🏷️' : '+ 添加标签'}
                </span>
            </div>
        `;
    },

    /**
     * 生成操作按钮HTML
     */
    generateActionButtonsHtml(dataset) {
        const functionButtons = [];
        const manageButtons = [];

        // 数据预览按钮 - 始终显示
        functionButtons.push(`<button class="action-btn btn-primary" onclick="Datasets.previewDataset('${dataset.id}')">数据预览</button>`);

        // 根据状态显示不同的分析按钮
        const status = dataset.processing_status || CONFIG.DATASET_STATUS.UPLOADED;

        if (status === CONFIG.DATASET_STATUS.UPLOADED) {
            // 已上传，可以启动业务分析
            functionButtons.push(`<button class="action-btn btn-success" onclick="Datasets.startBusinessAnalysis('${dataset.id}')">启动业务分析</button>`);
        } else if (status === CONFIG.DATASET_STATUS.BUSINESS_ANALYZING) {
            // 业务分析中
            functionButtons.push(`<button class="action-btn btn-secondary" disabled>业务分析中...</button>`);
        } else if (status === CONFIG.DATASET_STATUS.BUSINESS_COMPLETED) {
            // 业务分析完成，可以查看结果和启动质量分析
            functionButtons.push(`<button class="action-btn btn-info" onclick="Datasets.viewBusinessAnalysisResults('${dataset.id}')">查看业务分析</button>`);
            functionButtons.push(`<button class="action-btn btn-success" onclick="Datasets.startQualityAnalysis('${dataset.id}')">启动质量分析</button>`);
        } else if (status === CONFIG.DATASET_STATUS.QUALITY_ANALYZING) {
            // 质量分析中
            functionButtons.push(`<button class="action-btn btn-info" onclick="Datasets.viewBusinessAnalysisResults('${dataset.id}')">查看业务分析</button>`);
            functionButtons.push(`<button class="action-btn btn-secondary" disabled>质量分析中...</button>`);
        } else if (status === CONFIG.DATASET_STATUS.QUALITY_COMPLETED) {
            // 质量分析完成，可以查看所有结果
            functionButtons.push(`<button class="action-btn btn-info" onclick="Datasets.viewBusinessAnalysisResults('${dataset.id}')">查看业务分析</button>`);
            functionButtons.push(`<button class="action-btn btn-info" onclick="Datasets.viewQualityAnalysisResults('${dataset.id}')">查看质量分析</button>`);
        } else if (status === CONFIG.DATASET_STATUS.ANALYSIS_FAILED) {
            // 分析失败，可以重新启动
            functionButtons.push(`<button class="action-btn btn-warning" onclick="Datasets.startBusinessAnalysis('${dataset.id}')">重新分析</button>`);
        }

        // 管理按钮
        manageButtons.push(`<button class="action-btn btn-success" onclick="Datasets.downloadDataset('${dataset.id}')">下载</button>`);
        manageButtons.push(`<button class="action-btn btn-danger" onclick="Datasets.deleteDataset('${dataset.id}')">删除</button>`);

        return `
            <div class="action-group function-group">
                ${functionButtons.join('')}
            </div>
            <div class="action-group manage-group">
                ${manageButtons.join('')}
            </div>
        `;
    },

    /**
     * 获取数据质量状态
     */
    getQualityStatus(dataset) {
        const status = dataset.processing_status || CONFIG.DATASET_STATUS.UPLOADED;
        
        if (status === CONFIG.DATASET_STATUS.QUALITY_COMPLETED) {
            // 检查质量分析结果
            const qualityResults = dataset.quality_analysis_results || dataset.quality_metrics;
            if (qualityResults) {
                const score = Math.round(qualityResults.overall_score || qualityResults.quality_score) || 100;
                return `<span class="quality-score">${score}分</span>`;
            } else {
                return '<span class="status-completed">已完成</span>';
            }
        } else if (status === CONFIG.DATASET_STATUS.QUALITY_ANALYZING) {
            return '<span class="status-analyzing">分析中</span>';
        } else {
            return '<span class="status-not-started">未开始</span>';
        }
    },

    /**
     * 获取业务理解状态
     */
    getBusinessStatus(dataset) {
        const status = dataset.processing_status || CONFIG.DATASET_STATUS.UPLOADED;
        
        if (status === CONFIG.DATASET_STATUS.BUSINESS_COMPLETED || status === CONFIG.DATASET_STATUS.QUALITY_ANALYZING || status === CONFIG.DATASET_STATUS.QUALITY_COMPLETED) {
            return '<span class="status-completed">已完成</span>';
        } else if (status === CONFIG.DATASET_STATUS.BUSINESS_ANALYZING) {
            return '<span class="status-analyzing">分析中</span>';
        } else {
            return '<span class="status-not-started">未开始</span>';
        }
    },

    /**
     * 获取版本显示信息
     */
    getVersionDisplay(dataset) {
        const version = dataset.version || '1.0';
        const versionType = dataset.version_type || 'original';
        
        let versionIcon = '';
        let versionClass = '';
        
        switch (versionType) {
            case 'original':
                versionIcon = '🆕';
                versionClass = 'version-original';
                break;
            case 'updated':
                versionIcon = '🔄';
                versionClass = 'version-updated';
                break;
            case 'duplicate':
                versionIcon = '🔗';
                versionClass = 'version-duplicate';
                break;
            default:
                versionIcon = '📄';
                versionClass = 'version-default';
        }
        
        return `<span class="${versionClass}">${versionIcon} ${version}</span>`;
    },

    /**
     * 显示版本信息弹窗
     */
    async showVersionInfo(datasetId) {
        try {
            UI.showLoading(true);
            
            // 获取版本历史和重复数据
            const versionData = await API.versionControl.getVersionHistory(datasetId);
            
            this.openVersionInfoModal(datasetId, versionData);
            
        } catch (error) {
            Utils.log.error('获取版本信息失败:', error);
            UI.showMessage('获取版本信息失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            UI.showLoading(false);
        }
    },

    /**
     * 打开版本信息弹窗
     */
    openVersionInfoModal(datasetId, versionData) {
        const currentDataset = AppState.datasets.find(d => d.id === datasetId);
        const currentDatasetName = currentDataset ? currentDataset.name : datasetId;
        
        const versionHistoryHtml = versionData.version_history.map(version => `
            <div class="version-item">
                <div class="version-header">
                    <span class="version-number">${this.getVersionDisplay({version: version.version, version_type: version.version_type})}</span>
                    <span class="version-date">${Utils.formatDate(version.upload_time)}</span>
                </div>
                <div class="version-details">
                    <div class="version-name">${Utils.escapeHtml(version.name)}</div>
                    ${version.version_notes ? `<div class="version-notes">${Utils.escapeHtml(version.version_notes)}</div>` : ''}
                    <div class="version-size">${Utils.formatFileSize(version.file_size)}</div>
                </div>
            </div>
        `).join('');
        
        const duplicatesHtml = versionData.duplicates.map(duplicate => `
            <div class="duplicate-item">
                <div class="duplicate-header">
                    <span class="duplicate-name">${Utils.escapeHtml(duplicate.name)}</span>
                    <span class="duplicate-type">${duplicate.duplicate_type === 'file' ? '完全相同' : '内容相同'}</span>
                </div>
                <div class="duplicate-details">
                    <span class="duplicate-version">${this.getVersionDisplay({version: duplicate.version, version_type: duplicate.version_type})}</span>
                    <span class="duplicate-date">${Utils.formatDate(duplicate.upload_time)}</span>
                    <span class="duplicate-size">${Utils.formatFileSize(duplicate.file_size)}</span>
                </div>
            </div>
        `).join('');
        
        const modalHtml = `
            <div class="modal-overlay" id="versionInfoModal">
                <div class="modal-content version-info-modal">
                    <div class="modal-header">
                        <h3>📋 版本信息 - ${Utils.escapeHtml(currentDatasetName)}</h3>
                        <button type="button" class="modal-close" onclick="Datasets.closeVersionInfoModal()">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="version-section">
                            <h4>📚 版本历史 (${versionData.total_versions})</h4>
                            <div class="version-list">
                                ${versionHistoryHtml || '<div class="empty-state">暂无版本历史</div>'}
                            </div>
                        </div>
                        
                        ${versionData.total_duplicates > 0 ? `
                        <div class="duplicate-section">
                            <h4>🔗 重复数据 (${versionData.total_duplicates})</h4>
                            <div class="duplicate-list">
                                ${duplicatesHtml}
                            </div>
                        </div>
                        ` : ''}
                        
                        <div class="version-actions">
                            <button type="button" class="btn btn-secondary" onclick="Datasets.closeVersionInfoModal()">关闭</button>
                            ${versionData.total_versions > 5 ? `
                            <button type="button" class="btn btn-warning" onclick="Datasets.cleanupVersions('${datasetId}')">清理旧版本</button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 添加到页面
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    },

    /**
     * 关闭版本信息弹窗
     */
    closeVersionInfoModal() {
        const modal = document.getElementById('versionInfoModal');
        if (modal) {
            modal.remove();
        }
    },

    /**
     * 清理旧版本
     */
    async cleanupVersions(datasetId) {
        const confirmed = await UI.confirm('确定要清理旧版本吗？将保留最新的5个版本，其他版本将被删除。', '清理版本');
        if (!confirmed) return;
        
        try {
            UI.showLoading(true);
            
            const result = await API.versionControl.cleanupVersions(datasetId, 5);
            
            UI.showMessage(result.message, CONFIG.MESSAGE.TYPES.SUCCESS);
            
            // 关闭弹窗并刷新版本信息
            this.closeVersionInfoModal();
            setTimeout(() => {
                this.showVersionInfo(datasetId);
            }, 1000);
            
        } catch (error) {
            Utils.log.error('清理版本失败:', error);
            UI.showMessage('清理版本失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            UI.showLoading(false);
        }
    },

    /**
     * 预览数据集
     */
    async previewDataset(datasetId) {
        try {
            UI.showLoading(true);
            Utils.log.debug('预览数据集:', datasetId);

            const preview = await API.datasets.preview(datasetId);
            
            if (preview && preview.data) {
                this.openPreviewWindow(preview);
            } else {
                UI.showMessage('预览数据为空', CONFIG.MESSAGE.TYPES.WARNING);
            }

        } catch (error) {
            Utils.log.error('预览数据集失败:', error);
            UI.showMessage('预览失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            UI.showLoading(false);
        }
    },

    /**
     * 打开预览窗口
     */
    openPreviewWindow(preview) {
        const previewWindow = window.open('', '_blank', 'width=1000,height=700');
        previewWindow.document.write(`
            <html>
            <head>
                <title>数据预览</title>
                <style>
                    body { font-family: 'Microsoft YaHei', Arial, sans-serif; padding: 20px; background: #f8f9fa; }
                    .container { max-width: 100%; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
                    .header { border-bottom: 3px solid #667eea; padding-bottom: 15px; margin-bottom: 20px; }
                    .title { font-size: 1.5em; color: #333; margin-bottom: 5px; }
                    .subtitle { color: #666; }
                    table { border-collapse: collapse; width: 100%; margin-top: 15px; font-size: 0.9em; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
                    th { background-color: #667eea; color: white; font-weight: bold; }
                    tr:nth-child(even) { background-color: #f8f9fa; }
                    tr:hover { background-color: #e3f2fd; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="title">📊 数据预览</div>
                        <div class="subtitle">显示前 ${preview.data.length} 行数据 (共 ${preview.shape ? preview.shape[0] : 0} 行 × ${preview.shape ? preview.shape[1] : 0} 列)</div>
                    </div>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead>
                                <tr>${preview.columns ? preview.columns.map(col => `<th title="${col}">${col}</th>`).join('') : ''}</tr>
                            </thead>
                            <tbody>
                                ${preview.data ? preview.data.map(row => 
                                    `<tr>${preview.columns.map(col => `<td title="${row[col] || ''}">${row[col] || ''}</td>`).join('')}</tr>`
                                ).join('') : ''}
                            </tbody>
                        </table>
                    </div>
                </div>
            </body>
            </html>
        `);
    },

    /**
     * 启动业务分析
     */
    async startBusinessAnalysis(datasetId) {
        const confirmed = await UI.confirm('确定要启动业务分析吗？这将分析数据集的设备列、时间列、业务语义和控制逻辑。', '启动业务分析');
        if (!confirmed) return;

        try {
            await Analysis.startBusinessAnalysis(datasetId);
        } catch (error) {
            Utils.log.error('启动业务分析失败:', error);
            UI.showMessage('启动业务分析失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        }
    },

    /**
     * 启动质量分析
     */
    async startQualityAnalysis(datasetId) {
        const confirmed = await UI.confirm('确定要启动数据质量分析吗？这将评估数据的完整性、准确性和一致性。', '启动质量分析');
        if (!confirmed) return;

        try {
            await Analysis.startQualityAnalysis(datasetId);
        } catch (error) {
            Utils.log.error('启动质量分析失败:', error);
            UI.showMessage('启动质量分析失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        }
    },

    /**
     * 查看业务分析结果
     */
    async viewBusinessAnalysisResults(datasetId) {
        try {
            await Analysis.viewBusinessAnalysisResults(datasetId);
        } catch (error) {
            Utils.log.error('查看业务分析结果失败:', error);
            UI.showMessage('查看业务分析结果失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        }
    },

    /**
     * 查看质量分析结果
     */
    async viewQualityAnalysisResults(datasetId) {
        try {
            await Analysis.viewQualityAnalysisResults(datasetId);
        } catch (error) {
            Utils.log.error('查看质量分析结果失败:', error);
            UI.showMessage('查看质量分析结果失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        }
    },

    /**
     * 提取元数据 - 保持向后兼容
     */
    async extractMetadata(datasetId) {
        try {
            UI.showLoading(true);
            UI.showMessage('开始提取元数据...', CONFIG.MESSAGE.TYPES.INFO);

            await API.datasets.extractMetadata(datasetId);
            
            UI.showMessage('元数据提取已开始，请稍候...', CONFIG.MESSAGE.TYPES.SUCCESS);

            // 刷新数据集列表
            setTimeout(() => {
                App.refreshDatasets();
            }, 2000);

        } catch (error) {
            Utils.log.error('提取元数据失败:', error);
            UI.showMessage('提取失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            UI.showLoading(false);
        }
    },

    /**
     * 下载数据集
     */
    async downloadDataset(datasetId) {
        try {
            UI.showLoading(true);
            UI.showMessage('正在准备下载...', CONFIG.MESSAGE.TYPES.INFO);

            const filename = await API.download.dataset(datasetId);
            UI.showMessage(`下载成功: ${filename}`, CONFIG.MESSAGE.TYPES.SUCCESS);

        } catch (error) {
            Utils.log.error('下载数据集失败:', error);
            UI.showMessage('下载失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            UI.showLoading(false);
        }
    },

    /**
     * 编辑数据集标签
     */
    async editDatasetTags(datasetId) {
        try {
            // 获取数据集信息
            const dataset = AppState.datasets.find(d => d.id === datasetId);
            if (!dataset) {
                UI.showMessage('数据集不存在', CONFIG.MESSAGE.TYPES.ERROR);
                return;
            }

            // 获取当前标签
            const currentTags = dataset.tags || [];

            // 创建标签编辑弹出框
            const dialogHtml = `
                <div class="modal-overlay" id="tagEditModal">
                    <div class="modal-content tag-edit-popup">
                        <div class="popup-header">
                            <div class="popup-title">
                                <span class="popup-icon">🏷️</span>
                                <span>编辑标签</span>
                            </div>
                            <button type="button" class="popup-close" onclick="Datasets.closeTagEditModal()">×</button>
                        </div>
                        <div class="popup-body">
                            <div class="dataset-info-compact">
                                <span class="dataset-name">${Utils.escapeHtml(dataset.name)}</span>
                            </div>
                            <div class="tag-selector-container" id="tagSelectorContainer">
                                <!-- 标签选择器将在这里渲染 -->
                            </div>
                        </div>
                        <div class="popup-footer">
                            <button type="button" class="btn btn-sm btn-secondary" onclick="Datasets.closeTagEditModal()">取消</button>
                            <button type="button" class="btn btn-sm btn-primary" onclick="Datasets.saveDatasetTags('${datasetId}')">保存</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', dialogHtml);

            // 确保标签数据已加载，然后渲染标签选择器
            await Tags.loadTags();
            Tags.renderTagSelector('#tagSelectorContainer', currentTags, {
                allowCreate: true,
                placeholder: '选择或输入标签...',
                showCategories: true
            });

            Utils.log.debug('标签编辑对话框已打开:', datasetId);

        } catch (error) {
            Utils.log.error('打开标签编辑对话框失败:', error);
            UI.showMessage('打开标签编辑失败', CONFIG.MESSAGE.TYPES.ERROR);
        }
    },

    /**
     * 关闭标签编辑对话框
     */
    closeTagEditModal() {
        const modal = Utils.dom.find('#tagEditModal');
        if (modal) {
            modal.remove();
        }
    },

    /**
     * 保存数据集标签
     */
    async saveDatasetTags(datasetId) {
        try {
            const tagSelector = Utils.dom.find('#tagSelectorContainer .tag-selector');
            if (!tagSelector) {
                UI.showMessage('标签选择器未找到', CONFIG.MESSAGE.TYPES.ERROR);
                return;
            }

            const selectedTags = Tags.getSelectedTags(tagSelector);
            
            Utils.log.debug('保存数据集标签:', datasetId, selectedTags);

            // 调用API更新标签
            const updatedTags = await Tags.updateDatasetTags(datasetId, selectedTags);

            // 关闭对话框
            this.closeTagEditModal();

            // 刷新数据集列表以确保数据同步
            await App.refreshDatasets();

            UI.showMessage('标签保存成功', CONFIG.MESSAGE.TYPES.SUCCESS);

        } catch (error) {
            Utils.log.error('保存数据集标签失败:', error);
            UI.showMessage('保存标签失败', CONFIG.MESSAGE.TYPES.ERROR);
        }
    },

    /**
     * 删除数据集
     */
    async deleteDataset(datasetId) {
        const confirmed = await UI.confirm('确定要删除这个数据集吗？此操作不可恢复。', '确认删除');
        if (!confirmed) return;

        try {
            UI.showLoading(true);

            await API.datasets.delete(datasetId);
            
            UI.showMessage('数据集删除成功', CONFIG.MESSAGE.TYPES.SUCCESS);
            App.refreshDatasets();

        } catch (error) {
            Utils.log.error('删除数据集失败:', error);
            UI.showMessage('删除失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            UI.showLoading(false);
        }
    }
}; 