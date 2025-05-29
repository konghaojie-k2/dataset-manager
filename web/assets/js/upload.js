/**
 * 文件上传功能模块
 */

const Upload = {
    /**
     * 初始化上传功能
     */
    init() {
        this.setupEventListeners();
        Utils.log.debug('文件上传模块初始化完成');
    },

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        const uploadSection = Utils.dom.find('#uploadSection');
        const fileInput = Utils.dom.find('#fileInput');

        if (!uploadSection || !fileInput) {
            Utils.log.warn('上传区域或文件输入框未找到');
            return;
        }

        // 拖拽上传事件
        uploadSection.addEventListener('dragover', (e) => {
            e.preventDefault();
            Utils.dom.addClass(uploadSection, 'dragover');
        });

        uploadSection.addEventListener('dragleave', (e) => {
            e.preventDefault();
            Utils.dom.removeClass(uploadSection, 'dragover');
        });

        uploadSection.addEventListener('drop', (e) => {
            e.preventDefault();
            Utils.dom.removeClass(uploadSection, 'dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });

        // 文件选择事件
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });
    },

    /**
     * 处理文件上传
     */
    async handleFileUpload(file) {
        try {
            // 验证文件
            if (!this.validateFile(file)) {
                return;
            }

            // 显示简化的工作流程
            Analysis.showWorkflow();
            Analysis.resetSteps();

            // 开始上传
            await this.uploadFile(file);

        } catch (error) {
            Utils.log.error('文件上传处理失败:', error);
            UI.showMessage('文件上传失败', CONFIG.MESSAGE.TYPES.ERROR);
            Analysis.updateStep('upload', 'failed');
        }
    },

    /**
     * 验证文件
     */
    validateFile(file) {
        // 检查文件类型
        if (!Utils.validateFileType(file)) {
            const allowedTypes = CONFIG.UPLOAD.ALLOWED_TYPES.join(', ');
            UI.showMessage(`不支持的文件类型，请上传 ${allowedTypes} 格式的文件`, CONFIG.MESSAGE.TYPES.ERROR);
            return false;
        }

        // 检查文件大小
        if (!Utils.validateFileSize(file)) {
            const maxSize = Utils.formatFileSize(CONFIG.UPLOAD.MAX_SIZE);
            UI.showMessage(`文件大小超出限制，最大支持 ${maxSize}`, CONFIG.MESSAGE.TYPES.ERROR);
            return false;
        }

        return true;
    },

    /**
     * 上传文件到服务器
     */
    async uploadFile(file) {
        AppState.loading.upload = true;
        Analysis.updateStep('upload', 'active');
        UI.showLoading(true);

        try {
            const formData = new FormData();
            formData.append('file', file);

            Utils.log.debug('开始上传文件:', file.name, Utils.formatFileSize(file.size));

            const result = await API.datasets.upload(formData);

            Analysis.updateStep('upload', 'completed');
            App.setCurrentDataset(result.dataset_id);
            
            UI.showMessage(`文件上传成功！数据集ID: ${result.dataset_id}`, CONFIG.MESSAGE.TYPES.SUCCESS);

            // 清空文件输入
            const fileInput = Utils.dom.find('#fileInput');
            if (fileInput) {
                fileInput.value = '';
            }

            // 隐藏工作流程，刷新数据集列表以显示新的分析按钮
            setTimeout(() => {
                Analysis.hideWorkflow();
                App.refreshDatasets();
            }, 2000);

        } catch (error) {
            Analysis.updateStep('upload', 'failed');
            throw error;
        } finally {
            AppState.loading.upload = false;
            UI.showLoading(false);
        }
    }
}; 