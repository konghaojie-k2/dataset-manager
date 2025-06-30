/**
 * API接口封装
 * 统一管理所有的HTTP请求
 */

const API = {
    /**
     * 通用HTTP请求方法
     * @param {string} url - 请求URL
     * @param {Object} options - 请求选项
     * @returns {Promise} Promise对象
     */
    async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };

        // 如果是FormData，不设置Content-Type，让浏览器自动设置
        if (options.body instanceof FormData) {
            delete defaultOptions.headers['Content-Type'];
        }

        try {
            Utils.log.debug('API请求:', url, defaultOptions);
            
            const response = await fetch(url, defaultOptions);
            
            // 检查响应状态
            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || errorMessage;
                } catch (e) {
                    // 无法解析错误信息，使用默认错误信息
                }
                throw new Error(errorMessage);
            }

            // 尝试解析JSON响应
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                Utils.log.debug('API响应:', data);
                return data;
            }

            // 返回blob数据 (用于文件下载)
            return response;

        } catch (error) {
            Utils.log.error('API请求失败:', error);
            throw error;
        }
    },

    /**
     * GET请求
     * @param {string} url - 请求URL
     * @param {Object} params - 查询参数
     * @returns {Promise} Promise对象
     */
    async get(url, params = {}) {
        const queryString = Utils.buildQueryString(params);
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        return this.request(fullUrl, { method: 'GET' });
    },

    /**
     * POST请求
     * @param {string} url - 请求URL
     * @param {any} data - 请求数据
     * @returns {Promise} Promise对象
     */
    async post(url, data) {
        const options = {
            method: 'POST',
            body: data instanceof FormData ? data : JSON.stringify(data)
        };
        return this.request(url, options);
    },

    /**
     * PUT请求
     * @param {string} url - 请求URL
     * @param {any} data - 请求数据
     * @returns {Promise} Promise对象
     */
    async put(url, data) {
        const options = {
            method: 'PUT',
            body: JSON.stringify(data)
        };
        return this.request(url, options);
    },

    /**
     * DELETE请求
     * @param {string} url - 请求URL
     * @returns {Promise} Promise对象
     */
    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    },

    // 数据集相关API
    datasets: {
        /**
         * 获取数据集列表
         * @param {Object} params - 查询参数
         * @returns {Promise} 数据集列表
         */
        async list(params = {}) {
            return API.get(`${CONFIG.API_BASE}/datasets`, params);
        },

        /**
         * 获取数据集详情
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 数据集详情
         */
        async get(datasetId) {
            return API.get(`${CONFIG.API_BASE}/datasets/${datasetId}`);
        },

        /**
         * 上传数据集
         * @param {FormData} formData - 表单数据
         * @returns {Promise} 上传结果
         */
        async upload(formData) {
            return API.post(`${CONFIG.API_BASE}/datasets/upload`, formData);
        },

        /**
         * 删除数据集
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 删除结果
         */
        async delete(datasetId) {
            return API.delete(`${CONFIG.API_BASE}/datasets/${datasetId}`);
        },

        /**
         * 预览数据集
         * @param {string} datasetId - 数据集ID
         * @param {number} rows - 预览行数
         * @returns {Promise} 预览数据
         */
        async preview(datasetId, rows = 10) {
            return API.get(`${CONFIG.API_BASE}/datasets/${datasetId}/preview`, { rows });
        },

        /**
         * 提取元数据
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 提取结果
         */
        async extractMetadata(datasetId) {
            return API.post(`${CONFIG.API_BASE}/datasets/${datasetId}/extract-metadata`);
        },

        /**
         * 下载数据集
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 文件blob
         */
        async download(datasetId) {
            const response = await API.request(`${CONFIG.API_BASE}/datasets/${datasetId}/download`, {
                method: 'GET'
            });
            
            if (response instanceof Response) {
                return {
                    blob: await response.blob(),
                    filename: this._extractFilename(response)
                };
            }
            
            throw new Error('下载响应格式错误');
        },

        /**
         * 从响应头中提取文件名
         * @param {Response} response - HTTP响应对象
         * @returns {string} 文件名
         */
        _extractFilename(response) {
            const contentDisposition = response.headers.get('Content-Disposition');
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch && filenameMatch[1]) {
                    return filenameMatch[1].replace(/['"]/g, '');
                }
            }
            return 'dataset.csv';
        }
    },

    // 版本控制相关API
    versionControl: {
        /**
         * 获取数据集版本历史
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 版本历史
         */
        async getVersionHistory(datasetId) {
            return API.get(`${CONFIG.API_BASE}/version-control/datasets/${datasetId}/versions`);
        },

        /**
         * 获取重复数据集
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 重复数据集列表
         */
        async getDuplicates(datasetId) {
            return API.get(`${CONFIG.API_BASE}/version-control/datasets/${datasetId}/duplicates`);
        },

        /**
         * 清理旧版本
         * @param {string} datasetId - 数据集ID
         * @param {number} keepVersions - 保留版本数量
         * @returns {Promise} 清理结果
         */
        async cleanupVersions(datasetId, keepVersions = 5) {
            return API.delete(`${CONFIG.API_BASE}/version-control/datasets/${datasetId}/versions/cleanup?keep_versions=${keepVersions}`);
        }
    },

    // 分析相关API
    analysis: {
        /**
         * 启动业务分析
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 启动结果
         */
        async startBusinessAnalysis(datasetId) {
            return API.post(`${CONFIG.API_BASE}/datasets/${datasetId}/start-business-analysis`);
        },

        /**
         * 启动质量分析
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 启动结果
         */
        async startQualityAnalysis(datasetId) {
            return API.post(`${CONFIG.API_BASE}/datasets/${datasetId}/start-quality-analysis`);
        },

        /**
         * 获取业务分析结果
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 业务分析结果
         */
        async getBusinessAnalysisResults(datasetId) {
            return API.get(`${CONFIG.API_BASE}/datasets/${datasetId}/business-analysis-results`);
        },

        /**
         * 获取质量分析结果
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 质量分析结果
         */
        async getQualityAnalysisResults(datasetId) {
            return API.get(`${CONFIG.API_BASE}/datasets/${datasetId}/quality-analysis-results`);
        },

        /**
         * 获取分析结果 - 保持向后兼容
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 分析结果
         */
        async getResult(datasetId) {
            return API.get(`${CONFIG.API_BASE}/datasets/${datasetId}/analysis`);
        },

        /**
         * 获取质量报告 - 保持向后兼容
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 质量报告
         */
        async getQualityReport(datasetId) {
            return API.get(`${CONFIG.API_BASE}/datasets/${datasetId}/quality-report`);
        },

        /**
         * 获取业务分析报告 - 保持向后兼容
         * @param {string} datasetId - 数据集ID
         * @returns {Promise} 业务分析报告
         */
        async getBusinessReport(datasetId) {
            return API.get(`${CONFIG.API_BASE}/datasets/${datasetId}/business-report`);
        }
    },

    // 系统相关API
    system: {
        /**
         * 获取系统状态
         * @returns {Promise} 系统状态
         */
        async status() {
            return API.get(`${CONFIG.API_BASE}/system/status`);
        },

        /**
         * 获取系统信息
         * @returns {Promise} 系统信息
         */
        async info() {
            return API.get(`${CONFIG.API_BASE}/system/info`);
        }
    },

    // 文件下载助手
    download: {
        /**
         * 下载文件
         * @param {Blob} blob - 文件blob
         * @param {string} filename - 文件名
         */
        file(blob, filename) {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        },

        /**
         * 下载数据集文件
         * @param {string} datasetId - 数据集ID
         */
        async dataset(datasetId) {
            try {
                const { blob, filename } = await API.datasets.download(datasetId);
                this.file(blob, filename);
                return filename;
            } catch (error) {
                Utils.log.error('下载失败:', error);
                throw error;
            }
        }
    }
};

// 冻结API对象
Object.freeze(API); 