/**
 * 主应用入口文件
 * 负责应用初始化和全局状态管理
 */

// 全局应用状态
const AppState = {
    // 当前数据集ID
    currentDatasetId: null,
    
    // 分页状态
    pagination: {
        currentPage: 1,
        pageSize: CONFIG.PAGINATION.DEFAULT_PAGE_SIZE,
        totalDatasets: 0
    },
    
    // 数据集列表
    datasets: [],
    
    // 加载状态
    loading: {
        datasets: false,
        upload: false,
        analysis: false
    },
    
    // UI状态
    ui: {
        showAnalysisFlow: false,
        activeAnalysisStep: null
    }
};

// 全局应用对象
const App = {
    /**
     * 应用初始化
     */
    async init() {
        try {
            Utils.log.info('应用初始化开始');
            
            // 设置事件监听器
            this.setupEventListeners();
            
            // 加载数据集列表
            await this.loadDatasets();
            
            // 恢复上次的分页设置
            this.restorePageSize();
            
            Utils.log.info('应用初始化完成');
            
        } catch (error) {
            Utils.log.error('应用初始化失败:', error);
            UI.showMessage('应用初始化失败', CONFIG.MESSAGE.TYPES.ERROR);
        }
    },

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 文件上传相关事件
        Upload.init();
        
        // 分页相关事件
        Pagination.init();
        
        // 窗口大小变化事件
        window.addEventListener('resize', Utils.debounce(() => {
            this.handleWindowResize();
        }, 250));
        
        // 页面可见性变化事件
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // 页面重新可见时刷新数据
                this.refreshDataIfNeeded();
            }
        });
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    },

    /**
     * 加载数据集列表
     */
    async loadDatasets() {
        try {
            AppState.loading.datasets = true;
            UI.showLoading(true);
            
            Utils.log.debug('开始加载数据集列表');
            
            const datasets = await API.datasets.list();
            
            AppState.datasets = datasets;
            AppState.pagination.totalDatasets = datasets.length;
            
            // 渲染数据集列表
            Datasets.render();
            
            Utils.log.debug('数据集列表加载完成:', datasets.length, '个数据集');
            
        } catch (error) {
            Utils.log.error('加载数据集列表失败:', error);
            UI.showMessage('加载数据集列表失败', CONFIG.MESSAGE.TYPES.ERROR);
        } finally {
            AppState.loading.datasets = false;
            UI.showLoading(false);
        }
    },

    /**
     * 刷新数据集列表
     */
    async refreshDatasets() {
        Utils.log.debug('刷新数据集列表');
        await this.loadDatasets();
    },

    /**
     * 根据需要刷新数据
     */
    async refreshDataIfNeeded() {
        // 如果有数据集正在处理中，则自动刷新
        const hasProcessingDatasets = AppState.datasets.some(
            dataset => dataset.processing_status === CONFIG.DATASET_STATUS.EXTRACTING
        );
        
        if (hasProcessingDatasets) {
            Utils.log.debug('检测到处理中的数据集，自动刷新');
            await this.refreshDatasets();
        }
    },

    /**
     * 恢复页面大小设置
     */
    restorePageSize() {
        const savedPageSize = Utils.storage.get('pageSize', CONFIG.PAGINATION.DEFAULT_PAGE_SIZE);
        const pageSizeSelect = Utils.dom.find('#pageSizeSelect');
        
        if (pageSizeSelect && CONFIG.PAGINATION.PAGE_SIZE_OPTIONS.includes(savedPageSize)) {
            AppState.pagination.pageSize = savedPageSize;
            pageSizeSelect.value = savedPageSize;
            Utils.log.debug('恢复页面大小设置:', savedPageSize);
        }
    },

    /**
     * 处理窗口大小变化
     */
    handleWindowResize() {
        // 响应式布局调整
        const isMobile = window.innerWidth <= 768;
        document.body.classList.toggle('mobile-layout', isMobile);
        
        Utils.log.debug('窗口大小变化:', window.innerWidth, 'x', window.innerHeight);
    },

    /**
     * 处理键盘快捷键
     */
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + R: 刷新数据
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            this.refreshDatasets();
            return;
        }
        
        // F5: 刷新数据
        if (e.key === 'F5') {
            e.preventDefault();
            this.refreshDatasets();
            return;
        }
        
        // Escape: 关闭加载状态
        if (e.key === 'Escape') {
            UI.showLoading(false);
            return;
        }
    },

    /**
     * 设置当前数据集ID
     */
    setCurrentDataset(datasetId) {
        AppState.currentDatasetId = datasetId;
        Utils.log.debug('设置当前数据集:', datasetId);
    },

    /**
     * 获取当前数据集
     */
    getCurrentDataset() {
        if (!AppState.currentDatasetId) return null;
        return AppState.datasets.find(d => d.id === AppState.currentDatasetId);
    },

    /**
     * 获取应用状态
     */
    getState() {
        return Utils.deepClone(AppState);
    },

    /**
     * 更新应用状态
     */
    updateState(updates) {
        Object.assign(AppState, updates);
        Utils.log.debug('应用状态更新:', updates);
    }
};

// UI相关的全局方法
const UI = {
    /**
     * 显示消息提示
     */
    showMessage(text, type = CONFIG.MESSAGE.TYPES.INFO) {
        const messageEl = Utils.dom.find('#message');
        if (!messageEl) return;
        
        messageEl.textContent = text;
        messageEl.className = `message ${type}`;
        Utils.dom.addClass(messageEl, 'show');
        
        Utils.log.info(`消息[${type}]:`, text);
        
        // 自动隐藏
        setTimeout(() => {
            Utils.dom.removeClass(messageEl, 'show');
        }, CONFIG.MESSAGE.DURATION);
    },

    /**
     * 显示/隐藏加载动画
     */
    showLoading(show) {
        const loadingEl = Utils.dom.find('#loading');
        if (loadingEl) {
            Utils.dom.toggle(loadingEl, show);
        }
    },

    /**
     * 显示确认对话框
     */
    confirm(message, title = '确认') {
        return new Promise((resolve) => {
            const result = window.confirm(`${title}\n\n${message}`);
            resolve(result);
        });
    },

    /**
     * 显示输入对话框
     */
    prompt(message, defaultValue = '', title = '输入') {
        return new Promise((resolve) => {
            const result = window.prompt(`${title}\n\n${message}`, defaultValue);
            resolve(result);
        });
    }
};

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    Utils.log.info('DOM加载完成，开始初始化应用');
    App.init();
});

// 错误处理
window.addEventListener('error', (e) => {
    Utils.log.error('全局错误:', e.error);
    UI.showMessage('系统发生错误，请刷新页面重试', CONFIG.MESSAGE.TYPES.ERROR);
});

window.addEventListener('unhandledrejection', (e) => {
    Utils.log.error('未处理的Promise错误:', e.reason);
    UI.showMessage('操作失败，请重试', CONFIG.MESSAGE.TYPES.ERROR);
}); 