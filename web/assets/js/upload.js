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

            // 开始上传
            await this.uploadFile(file);

        } catch (error) {
            Utils.log.error('文件上传处理失败:', error);
            
            // 检查是否是重复数据错误
            if (error.message && error.message.includes('检测到重复数据')) {
                await this.handleDuplicateDataError(error.message, file);
            } else {
                UI.showMessage('文件上传失败: ' + error.message, CONFIG.MESSAGE.TYPES.ERROR);
            }
        }
    },

    /**
     * 处理重复数据错误
     */
    async handleDuplicateDataError(errorMessage, file) {
        // 从错误消息中提取原数据集信息
        const match = errorMessage.match(/已存在相同的数据集：(.+?) \(ID: (.+?)\)/);
        const existingDatasetName = match ? match[1] : '未知数据集';
        const existingDatasetId = match ? match[2] : '';

        const confirmed = await UI.confirm(
            `检测到重复数据！\n\n` +
            `已存在相同的数据集：${existingDatasetName}\n\n` +
            `您希望如何处理？\n` +
            `• 点击"确定"：删除原数据集并上传新文件\n` +
            `• 点击"取消"：取消上传，保留原数据集`,
            '重复数据处理'
        );

        if (confirmed && existingDatasetId) {
            try {
                UI.showLoading(true);
                UI.showMessage('正在删除原数据集...', CONFIG.MESSAGE.TYPES.INFO);

                // 删除原数据集
                await API.datasets.delete(existingDatasetId);
                
                UI.showMessage('原数据集已删除，重新上传中...', CONFIG.MESSAGE.TYPES.INFO);

                // 重新上传文件
                await this.uploadFile(file);

            } catch (deleteError) {
                Utils.log.error('删除原数据集失败:', deleteError);
                UI.showMessage('删除原数据集失败，请手动删除后重试', CONFIG.MESSAGE.TYPES.ERROR);
            } finally {
                UI.showLoading(false);
            }
        } else {
            UI.showMessage('上传已取消，保留原数据集', CONFIG.MESSAGE.TYPES.INFO);
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
        UI.showLoading(true);

        try {
            const formData = new FormData();
            formData.append('file', file);

            Utils.log.debug('开始上传文件:', file.name, Utils.formatFileSize(file.size));

            const result = await API.datasets.upload(formData);

            App.setCurrentDataset(result.dataset_id);
            
            UI.showMessage(`文件上传成功！数据集ID: ${result.dataset_id}`, CONFIG.MESSAGE.TYPES.SUCCESS);

            // 清空文件输入
            const fileInput = Utils.dom.find('#fileInput');
            if (fileInput) {
                fileInput.value = '';
            }

            // 刷新数据集列表以显示新的分析按钮
            setTimeout(() => {
                App.refreshDatasets();
            }, 2000);

        } catch (error) {
            throw error;
        } finally {
            AppState.loading.upload = false;
            UI.showLoading(false);
        }
    }
}; 