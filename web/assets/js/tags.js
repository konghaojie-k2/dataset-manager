/**
 * 标签管理模块
 */

const Tags = {
    // 标签数据缓存
    allTags: [],
    categories: [],
    
    /**
     * 初始化标签管理
     */
    async init() {
        try {
            await this.loadTags();
            await this.loadCategories();
            Utils.log.info('标签管理模块初始化完成');
        } catch (error) {
            Utils.log.error('标签管理模块初始化失败:', error);
        }
    },

    /**
     * 加载所有标签
     */
    async loadTags() {
        try {
            const response = await API.get('/api/v1/tags/');
            if (response && response.tags) {
                this.allTags = response.tags || [];
                Utils.log.debug('标签数据已加载:', this.allTags.length, '个标签');
            }
        } catch (error) {
            Utils.log.error('加载标签失败:', error);
            this.allTags = [];
        }
    },

    /**
     * 加载标签分类
     */
    async loadCategories() {
        try {
            const response = await API.get('/api/v1/tags/categories');
            if (response) {
                this.categories = response || [];
                Utils.log.debug('标签分类已加载:', this.categories.length, '个分类');
            }
        } catch (error) {
            Utils.log.error('加载标签分类失败:', error);
            this.categories = [];
        }
    },

    /**
     * 搜索标签
     */
    async searchTags(query, limit = 20) {
        try {
            const response = await API.get(`/api/v1/tags/search?q=${encodeURIComponent(query)}&limit=${limit}`);
            if (response && response.tags) {
                return response.tags || [];
            }
            return [];
        } catch (error) {
            Utils.log.error('搜索标签失败:', error);
            return [];
        }
    },

    /**
     * 获取热门标签
     */
    async getPopularTags(limit = 10) {
        try {
            const response = await API.get(`/api/v1/tags/popular?limit=${limit}`);
            if (response && response.tags) {
                return response.tags || [];
            }
            return [];
        } catch (error) {
            Utils.log.error('获取热门标签失败:', error);
            return [];
        }
    },

    /**
     * 创建标签
     */
    async createTag(tagData) {
        try {
            const response = await API.post('/api/v1/tags/', tagData);
            if (response) {
                // 重新加载标签列表
                await this.loadTags();
                UI.showMessage('标签创建成功', CONFIG.MESSAGE.TYPES.SUCCESS);
                return response;
            }
            throw new Error('创建标签失败');
        } catch (error) {
            Utils.log.error('创建标签失败:', error);
            UI.showMessage(error.message || '创建标签失败', CONFIG.MESSAGE.TYPES.ERROR);
            throw error;
        }
    },

    /**
     * 更新标签
     */
    async updateTag(tagId, tagData) {
        try {
            const response = await API.put(`/api/v1/tags/${tagId}`, tagData);
            if (response) {
                // 重新加载标签列表
                await this.loadTags();
                UI.showMessage('标签更新成功', CONFIG.MESSAGE.TYPES.SUCCESS);
                return response;
            }
            throw new Error('更新标签失败');
        } catch (error) {
            Utils.log.error('更新标签失败:', error);
            UI.showMessage(error.message || '更新标签失败', CONFIG.MESSAGE.TYPES.ERROR);
            throw error;
        }
    },

    /**
     * 删除标签
     */
    async deleteTag(tagId) {
        try {
            const response = await API.delete(`/api/v1/tags/${tagId}`);
            if (response && response.success) {
                // 重新加载标签列表
                await this.loadTags();
                UI.showMessage('标签删除成功', CONFIG.MESSAGE.TYPES.SUCCESS);
                return true;
            }
            throw new Error((response && response.message) || '删除标签失败');
        } catch (error) {
            Utils.log.error('删除标签失败:', error);
            UI.showMessage(error.message || '删除标签失败', CONFIG.MESSAGE.TYPES.ERROR);
            return false;
        }
    },

    /**
     * 更新数据集标签
     */
    async updateDatasetTags(datasetId, tagNames) {
        try {
            const response = await API.put(`/api/v1/tags/datasets/${datasetId}`, {
                dataset_id: datasetId,
                tag_names: tagNames
            });
            if (response && response.success) {
                UI.showMessage('数据集标签更新成功', CONFIG.MESSAGE.TYPES.SUCCESS);
                return response.tags || tagNames;
            }
            throw new Error((response && response.message) || '更新数据集标签失败');
        } catch (error) {
            Utils.log.error('更新数据集标签失败:', error);
            UI.showMessage(error.message || '更新数据集标签失败', CONFIG.MESSAGE.TYPES.ERROR);
            throw error;
        }
    },

    /**
     * 获取数据集标签
     */
    async getDatasetTags(datasetId) {
        try {
            const response = await API.get(`/api/v1/tags/datasets/${datasetId}`);
            if (response && response.tags) {
                return response.tags || [];
            }
            return [];
        } catch (error) {
            Utils.log.error('获取数据集标签失败:', error);
            return [];
        }
    },

    /**
     * 渲染标签选择器
     */
    renderTagSelector(containerId, selectedTags = [], options = {}) {
        const container = Utils.dom.find(containerId);
        if (!container) return;

        const {
            allowCreate = true,
            placeholder = '选择或输入标签...',
            maxTags = null,
            showCategories = false
        } = options;

        // 按使用次数排序标签
        const sortedTags = [...(this.allTags || [])].sort((a, b) => (b.usage_count || 0) - (a.usage_count || 0));
        const popularTags = sortedTags.slice(0, 8); // 显示前8个热门标签

        const selectorHtml = `
            <div class="tag-selector">
                <div class="tag-input-container">
                    <input type="text" 
                           class="tag-input" 
                           placeholder="${placeholder}"
                           autocomplete="off">
                    <div class="tag-suggestions" style="display: none;"></div>
                </div>
                <div class="selected-tags">
                    ${selectedTags.map(tag => this.generateSelectedTagHtml(tag)).join('')}
                </div>
                ${popularTags.length > 0 ? this.generatePopularTagsHtml(popularTags, selectedTags) : ''}
                ${allowCreate ? '<div class="tag-create-hint">💡 输入新标签名称后按回车创建，点击下方标签快速选择</div>' : ''}
            </div>
        `;

        container.innerHTML = selectorHtml;
        this.initTagSelectorEvents(container, selectedTags, options);
    },

    /**
     * 生成已选标签HTML
     */
    generateSelectedTagHtml(tagName) {
        const tag = (this.allTags || []).find(t => t.name === tagName);
        const color = (tag && tag.color) ? tag.color : '#007bff';
        
        return `
            <span class="selected-tag" data-tag="${Utils.escapeHtml(tagName)}" style="background-color: ${color}">
                ${Utils.escapeHtml(tagName)}
                <button type="button" class="tag-remove" onclick="Tags.removeSelectedTag(this)">×</button>
            </span>
        `;
    },

    /**
     * 生成热门标签HTML
     */
    generatePopularTagsHtml(popularTags, selectedTags) {
        const availableTags = popularTags.filter(tag => !selectedTags.includes(tag.name));
        
        if (availableTags.length === 0) return '';

        return `
            <div class="popular-tags">
                <div class="popular-tags-title">🔥 热门标签：</div>
                <div class="popular-tags-list">
                    ${availableTags.map(tag => `
                        <button type="button" 
                                class="popular-tag-btn" 
                                data-tag="${Utils.escapeHtml(tag.name)}"
                                style="border-left: 3px solid ${tag.color}"
                                title="${Utils.escapeHtml(tag.description || tag.name)} (使用${tag.usage_count}次)">
                            ${Utils.escapeHtml(tag.name)}
                            <span class="tag-usage-count">${tag.usage_count}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    },

    /**
     * 初始化标签选择器事件
     */
    initTagSelectorEvents(container, selectedTags, options) {
        const input = container.querySelector('.tag-input');
        const suggestions = container.querySelector('.tag-suggestions');
        
        let currentSelectedTags = [...selectedTags];

        // 输入事件
        input.addEventListener('input', async (e) => {
            const query = e.target.value.trim();
            if (query.length > 0) {
                // 获取最新的选中标签
                currentSelectedTags = self.getSelectedTags(container);
                const matchedTags = await self.searchTags(query);
                self.showSuggestions(suggestions, matchedTags, currentSelectedTags, options);
            } else {
                self.hideSuggestions(suggestions);
            }
        });

        // 回车创建标签
        const self = this;
        input.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const tagName = e.target.value.trim();
                // 获取最新的选中标签
                currentSelectedTags = self.getSelectedTags(container);
                if (tagName && !currentSelectedTags.includes(tagName)) {
                    if (options.allowCreate) {
                        await self.addTagToSelection(container, tagName, currentSelectedTags, options);
                        // 更新当前选中标签列表
                        currentSelectedTags = self.getSelectedTags(container);
                        e.target.value = '';
                        self.hideSuggestions(suggestions);
                        // 更新热门标签显示
                        self.updatePopularTagsDisplay(container, currentSelectedTags);
                    }
                }
            }
        });

        // 点击外部隐藏建议
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target)) {
                self.hideSuggestions(suggestions);
            }
        });

        // 热门标签点击事件
        container.addEventListener('click', async (e) => {
            if (e.target.classList.contains('popular-tag-btn') || e.target.closest('.popular-tag-btn')) {
                const button = e.target.classList.contains('popular-tag-btn') ? e.target : e.target.closest('.popular-tag-btn');
                const tagName = button.dataset.tag;
                // 获取最新的选中标签
                currentSelectedTags = self.getSelectedTags(container);
                if (tagName && !currentSelectedTags.includes(tagName)) {
                    await self.addTagToSelection(container, tagName, currentSelectedTags, options);
                    // 更新当前选中标签列表
                    currentSelectedTags = self.getSelectedTags(container);
                    self.updatePopularTagsDisplay(container, currentSelectedTags);
                }
            }
        });
    },

    /**
     * 显示标签建议
     */
    showSuggestions(suggestionsContainer, tags, selectedTags, options = {}) {
        const availableTags = tags.filter(tag => !selectedTags.includes(tag.name));
        
        if (availableTags.length === 0) {
            this.hideSuggestions(suggestionsContainer);
            return;
        }

        const suggestionsHtml = availableTags.map(tag => `
            <div class="tag-suggestion" data-tag="${Utils.escapeHtml(tag.name)}" style="border-left: 3px solid ${tag.color}">
                <span class="tag-name">${Utils.escapeHtml(tag.name)}</span>
                ${tag.description ? `<span class="tag-description">${Utils.escapeHtml(tag.description)}</span>` : ''}
                <span class="tag-usage">${tag.usage_count} 次使用</span>
            </div>
        `).join('');

        suggestionsContainer.innerHTML = suggestionsHtml;
        suggestionsContainer.style.display = 'block';

        // 为每个建议添加点击事件（避免重复绑定）
        const self = this;
        suggestionsContainer.querySelectorAll('.tag-suggestion').forEach(suggestion => {
            suggestion.addEventListener('click', async (e) => {
                const tagName = suggestion.dataset.tag;
                const container = suggestionsContainer.closest('.tag-selector');
                let currentSelectedTags = self.getSelectedTags(container);
                await self.addTagToSelection(container, tagName, currentSelectedTags, options);
                // 更新选中标签列表
                currentSelectedTags = self.getSelectedTags(container);
                container.querySelector('.tag-input').value = '';
                self.hideSuggestions(suggestionsContainer);
                // 更新热门标签显示
                self.updatePopularTagsDisplay(container, currentSelectedTags);
            });
        });
    },

    /**
     * 隐藏标签建议
     */
    hideSuggestions(suggestionsContainer) {
        suggestionsContainer.style.display = 'none';
        // 清理事件监听器
        suggestionsContainer.querySelectorAll('.tag-suggestion').forEach(suggestion => {
            suggestion.replaceWith(suggestion.cloneNode(true));
        });
        suggestionsContainer.innerHTML = '';
    },

    /**
     * 添加标签到选择列表
     */
    async addTagToSelection(container, tagName, currentSelectedTags, options = {}) {
        if (currentSelectedTags.includes(tagName)) return;

        // 检查最大标签数限制
        if (options.maxTags && currentSelectedTags.length >= options.maxTags) {
            UI.showMessage(`最多只能选择 ${options.maxTags} 个标签`, CONFIG.MESSAGE.TYPES.WARNING);
            return;
        }

        // 如果标签不存在且允许创建，则创建新标签
        let tag = (this.allTags || []).find(t => t.name === tagName);
        if (!tag && options.allowCreate) {
            try {
                const response = await API.post('/api/v1/tags/', {
                    name: tagName,
                    description: `自动创建的标签: ${tagName}`,
                    color: this.generateRandomColor()
                });
                            if (response) {
                tag = response; // 创建标签API直接返回Tag对象
                // 将新创建的标签添加到本地缓存
                if (!this.allTags) {
                    this.allTags = [];
                }
                this.allTags.push(tag);
                Utils.log.debug('标签创建成功:', tag);
            } else {
                throw new Error('创建标签失败');
            }
            } catch (error) {
                Utils.log.error('创建标签失败:', error);
                UI.showMessage(error.message || '创建标签失败', CONFIG.MESSAGE.TYPES.ERROR);
                return; // 创建失败，不添加到选择列表
            }
        }

        if (!tag) return;

        // 添加到选择列表
        const selectedTagsContainer = container.querySelector('.selected-tags');
        if (!selectedTagsContainer) {
            Utils.log.error('未找到选中标签容器');
            return;
        }
        const tagHtml = this.generateSelectedTagHtml(tagName);
        selectedTagsContainer.insertAdjacentHTML('beforeend', tagHtml);

        // 触发变更事件
        this.triggerTagChangeEvent(container);
    },

    /**
     * 移除选中的标签
     */
    removeSelectedTag(button) {
        const tagElement = button.closest('.selected-tag');
        const container = button.closest('.tag-selector');
        
        if (tagElement) {
            tagElement.remove();
        }
        
        if (container) {
            this.triggerTagChangeEvent(container);
            
            // 更新热门标签显示
            const currentSelectedTags = this.getSelectedTags(container);
            this.updatePopularTagsDisplay(container, currentSelectedTags);
        }
    },

    /**
     * 更新热门标签显示
     */
    updatePopularTagsDisplay(container, selectedTags) {
        const popularTagsContainer = container.querySelector('.popular-tags-list');
        if (!popularTagsContainer) return;

        const sortedTags = [...(this.allTags || [])].sort((a, b) => (b.usage_count || 0) - (a.usage_count || 0));
        const popularTags = sortedTags.slice(0, 8);
        const availableTags = popularTags.filter(tag => !selectedTags.includes(tag.name));

        if (availableTags.length === 0) {
            const popularTagsElement = container.querySelector('.popular-tags');
            if (popularTagsElement) {
                popularTagsElement.style.display = 'none';
            }
            return;
        }

        const popularTagsElement = container.querySelector('.popular-tags');
        if (popularTagsElement) {
            popularTagsElement.style.display = 'block';
        }
        popularTagsContainer.innerHTML = availableTags.map(tag => `
            <button type="button" 
                    class="popular-tag-btn" 
                    data-tag="${Utils.escapeHtml(tag.name)}"
                    style="border-left: 3px solid ${tag.color}"
                    title="${Utils.escapeHtml(tag.description || tag.name)} (使用${tag.usage_count}次)">
                ${Utils.escapeHtml(tag.name)}
                <span class="tag-usage-count">${tag.usage_count}</span>
            </button>
        `).join('');
    },

    /**
     * 获取选中的标签
     */
    getSelectedTags(container) {
        const tagElements = container.querySelectorAll('.selected-tag');
        return Array.from(tagElements).map(el => el.dataset.tag);
    },

    /**
     * 触发标签变更事件
     */
    triggerTagChangeEvent(container) {
        const selectedTags = this.getSelectedTags(container);
        const event = new CustomEvent('tagsChanged', {
            detail: { tags: selectedTags }
        });
        container.dispatchEvent(event);
    },

    /**
     * 生成随机颜色
     */
    generateRandomColor() {
        const colors = [
            '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8',
            '#6f42c1', '#e83e8c', '#fd7e14', '#20c997', '#6c757d'
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    },

    /**
     * 打开标签管理对话框 - 已废弃，功能集成到标签选择器中
     */
    openTagManagementDialog() {
        UI.showMessage('标签管理功能已集成到标签选择器中', CONFIG.MESSAGE.TYPES.INFO);
        return;
        // 以下代码已废弃
        const dialogHtml = `
            <div class="modal-overlay" id="tagManagementModal">
                <div class="modal-content tag-management-modal">
                    <div class="popup-header">
                        <div class="popup-title">
                            <span class="popup-icon">🏷️</span>
                            <span>标签管理</span>
                        </div>
                        <button type="button" class="popup-close" onclick="Tags.closeTagManagementDialog()">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="tag-management-tabs">
                            <button type="button" class="tab-btn active" data-tab="list">标签列表</button>
                            <button type="button" class="tab-btn" data-tab="create">创建标签</button>
                            <button type="button" class="tab-btn" data-tab="categories">分类管理</button>
                        </div>
                        <div class="tab-content">
                            <div class="tab-pane active" id="tagListTab">
                                <div class="tag-list-container">
                                    <div class="tag-search">
                                        <input type="text" placeholder="搜索标签..." class="tag-search-input">
                                    </div>
                                    <div class="tag-list" id="tagList"></div>
                                </div>
                            </div>
                            <div class="tab-pane" id="tagCreateTab">
                                <form class="tag-create-form" id="tagCreateForm">
                                    <div class="form-group">
                                        <label>标签名称</label>
                                        <input type="text" name="name" required>
                                    </div>
                                    <div class="form-group">
                                        <label>描述</label>
                                        <textarea name="description"></textarea>
                                    </div>
                                    <div class="form-group">
                                        <label>颜色</label>
                                        <input type="color" name="color" value="#007bff">
                                    </div>
                                    <div class="form-group">
                                        <label>分类</label>
                                        <input type="text" name="category" placeholder="可选">
                                    </div>
                                    <button type="submit" class="btn btn-primary">创建标签</button>
                                </form>
                            </div>
                            <div class="tab-pane" id="tagCategoriesTab">
                                <div class="categories-list" id="categoriesList"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', dialogHtml);
        this.initTagManagementEvents();
        this.renderTagList();
        this.renderCategoriesList();
    },

    /**
     * 关闭标签管理对话框
     */
    closeTagManagementDialog() {
        const modal = Utils.dom.find('#tagManagementModal');
        if (modal) {
            modal.remove();
        }
    },

    /**
     * 初始化标签管理事件
     */
    initTagManagementEvents() {
        const modal = Utils.dom.find('#tagManagementModal');
        
        // 标签页切换
        modal.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-btn')) {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            }
        });

        // 创建标签表单
        const createForm = modal.querySelector('#tagCreateForm');
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const tagData = {
                name: formData.get('name'),
                description: formData.get('description'),
                color: formData.get('color'),
                category: formData.get('category') || null
            };

            try {
                await this.createTag(tagData);
                e.target.reset();
                this.renderTagList();
                this.renderCategoriesList();
            } catch (error) {
                // 错误已在createTag中处理
            }
        });

        // 搜索标签
        const searchInput = modal.querySelector('.tag-search-input');
        searchInput.addEventListener('input', (e) => {
            this.filterTagList(e.target.value);
        });
    },

    /**
     * 切换标签页
     */
    switchTab(tabName) {
        const modal = Utils.dom.find('#tagManagementModal');
        
        // 更新标签页按钮状态
        modal.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // 更新内容面板状态
        modal.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === `tag${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Tab`);
        });
    },

    /**
     * 渲染标签列表
     */
    renderTagList() {
        const container = Utils.dom.find('#tagList');
        if (!container) return;

        const tagsHtml = this.allTags.map(tag => `
            <div class="tag-item" data-tag-id="${tag.id}">
                <div class="tag-info">
                    <span class="tag-name" style="color: ${tag.color}">${Utils.escapeHtml(tag.name)}</span>
                    ${tag.description ? `<span class="tag-description">${Utils.escapeHtml(tag.description)}</span>` : ''}
                    <div class="tag-meta">
                        ${tag.category ? `<span class="tag-category">${Utils.escapeHtml(tag.category)}</span>` : ''}
                        <span class="tag-usage">${tag.usage_count} 次使用</span>
                    </div>
                </div>
                <div class="tag-actions">
                    <button type="button" class="btn btn-sm btn-secondary" onclick="Tags.editTag(${tag.id})">编辑</button>
                    <button type="button" class="btn btn-sm btn-danger" onclick="Tags.confirmDeleteTag(${tag.id})">删除</button>
                </div>
            </div>
        `).join('');

        container.innerHTML = tagsHtml || '<p class="no-tags">暂无标签</p>';
    },

    /**
     * 渲染分类列表
     */
    renderCategoriesList() {
        const container = Utils.dom.find('#categoriesList');
        if (!container) return;

        const categoriesHtml = this.categories.map(category => `
            <div class="category-item">
                <div class="category-info">
                    <span class="category-name">${Utils.escapeHtml(category.name)}</span>
                    <span class="category-count">${category.tag_count} 个标签</span>
                </div>
            </div>
        `).join('');

        container.innerHTML = categoriesHtml || '<p class="no-categories">暂无分类</p>';
    },

    /**
     * 过滤标签列表
     */
    filterTagList(query) {
        const container = Utils.dom.find('#tagList');
        if (!container) return;

        const tagItems = container.querySelectorAll('.tag-item');
        tagItems.forEach(item => {
            const tagName = item.querySelector('.tag-name').textContent.toLowerCase();
            const tagDescription = item.querySelector('.tag-description')?.textContent.toLowerCase() || '';
            const matches = tagName.includes(query.toLowerCase()) || tagDescription.includes(query.toLowerCase());
            item.style.display = matches ? 'flex' : 'none';
        });
    },

    /**
     * 编辑标签
     */
    editTag(tagId) {
        // TODO: 实现标签编辑功能
        UI.showMessage('标签编辑功能开发中...', CONFIG.MESSAGE.TYPES.INFO);
    },

    /**
     * 确认删除标签
     */
    confirmDeleteTag(tagId) {
        const tag = this.allTags.find(t => t.id === tagId);
        if (!tag) return;

        if (confirm(`确定要删除标签 "${tag.name}" 吗？此操作不可撤销。`)) {
            this.deleteTag(tagId).then(success => {
                if (success) {
                    this.renderTagList();
                    this.renderCategoriesList();
                }
            });
        }
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    Tags.init();
}); 