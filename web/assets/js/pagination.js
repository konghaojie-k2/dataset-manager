/**
 * 分页功能模块
 */

const Pagination = {
    /**
     * 初始化分页功能
     */
    init() {
        this.setupEventListeners();
        Utils.log.debug('分页模块初始化完成');
    },

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 页面大小变化事件已在HTML中直接绑定
        Utils.log.debug('分页事件监听器设置完成');
    },

    /**
     * 更新分页显示
     */
    update() {
        const totalDatasets = AppState.pagination.totalDatasets;
        const pageSize = AppState.pagination.pageSize;
        const currentPage = AppState.pagination.currentPage;
        const totalPages = Math.ceil(totalDatasets / pageSize);

        this.updatePaginationControls(currentPage, totalPages, totalDatasets);
        this.updatePageNumbers(currentPage, totalPages);
    },

    /**
     * 更新分页控件状态
     */
    updatePaginationControls(currentPage, totalPages, totalDatasets) {
        const paginationEl = Utils.dom.find('#pagination');
        const prevBtn = Utils.dom.find('#prevBtn');
        const nextBtn = Utils.dom.find('#nextBtn');
        const paginationInfo = Utils.dom.find('#paginationInfo');

        if (totalPages <= 1) {
            if (paginationEl) paginationEl.style.display = 'none';
            return;
        }

        if (paginationEl) paginationEl.style.display = 'flex';

        // 更新按钮状态
        if (prevBtn) {
            prevBtn.disabled = currentPage <= 1;
        }
        if (nextBtn) {
            nextBtn.disabled = currentPage >= totalPages;
        }

        // 更新分页信息
        if (paginationInfo) {
            const startItem = (currentPage - 1) * AppState.pagination.pageSize + 1;
            const endItem = Math.min(currentPage * AppState.pagination.pageSize, totalDatasets);
            paginationInfo.textContent = `第 ${startItem}-${endItem} 项，共 ${totalDatasets} 项`;
        }
    },

    /**
     * 更新页码按钮
     */
    updatePageNumbers(currentPage, totalPages) {
        const pageNumbersEl = Utils.dom.find('#pageNumbers');
        if (!pageNumbersEl) return;

        pageNumbersEl.innerHTML = '';

        // 计算显示的页码范围
        const range = this.calculatePageRange(currentPage, totalPages);

        // 添加页码按钮
        for (let i = range.start; i <= range.end; i++) {
            const pageBtn = Utils.dom.create('button', {
                class: `pagination-btn ${i === currentPage ? 'active' : ''}`,
                onclick: `changePage(${i})`
            }, i.toString());

            pageNumbersEl.appendChild(pageBtn);
        }

        // 添加省略号和跳转
        if (range.start > 1) {
            pageNumbersEl.insertAdjacentHTML('afterbegin', 
                '<button class="pagination-btn" onclick="changePage(1)">1</button>' +
                (range.start > 2 ? '<span style="margin: 0 5px;">...</span>' : '')
            );
        }

        if (range.end < totalPages) {
            pageNumbersEl.insertAdjacentHTML('beforeend',
                (range.end < totalPages - 1 ? '<span style="margin: 0 5px;">...</span>' : '') +
                `<button class="pagination-btn" onclick="changePage(${totalPages})">${totalPages}</button>`
            );
        }
    },

    /**
     * 计算页码显示范围
     */
    calculatePageRange(currentPage, totalPages) {
        const maxVisible = 5; // 最多显示5个页码
        const half = Math.floor(maxVisible / 2);

        let start = Math.max(1, currentPage - half);
        let end = Math.min(totalPages, currentPage + half);

        // 调整范围以确保显示足够的页码
        if (end - start + 1 < maxVisible) {
            if (start === 1) {
                end = Math.min(totalPages, start + maxVisible - 1);
            } else if (end === totalPages) {
                start = Math.max(1, end - maxVisible + 1);
            }
        }

        return { start, end };
    },

    /**
     * 跳转到指定页面
     */
    goToPage(page) {
        const totalPages = Math.ceil(AppState.pagination.totalDatasets / AppState.pagination.pageSize);
        
        if (page < 1 || page > totalPages) {
            Utils.log.warn('无效的页码:', page);
            return;
        }

        if (page === AppState.pagination.currentPage) {
            return; // 相同页面，无需处理
        }

        AppState.pagination.currentPage = page;
        Datasets.render();
        
        Utils.log.debug('跳转到页面:', page);
    }
};

// 全局函数，供HTML中的onclick使用
function changePage(page) {
    if (typeof page === 'string') {
        if (page === 'prev') {
            page = AppState.pagination.currentPage - 1;
        } else if (page === 'next') {
            page = AppState.pagination.currentPage + 1;
        }
    }
    Pagination.goToPage(page);
}

function changePageSize() {
    const pageSizeSelect = Utils.dom.find('#pageSizeSelect');
    if (!pageSizeSelect) return;

    const newPageSize = parseInt(pageSizeSelect.value);
    if (newPageSize === AppState.pagination.pageSize) return;

    // 保存设置到本地存储
    Utils.storage.set('pageSize', newPageSize);

    // 更新状态
    AppState.pagination.pageSize = newPageSize;
    AppState.pagination.currentPage = 1; // 重置到第一页

    // 重新渲染
    Datasets.render();

    Utils.log.debug('页面大小已更改:', newPageSize);
} 