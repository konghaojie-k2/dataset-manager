/**
 * 工具函数库
 */

// 显示消息提示
function showMessage(text, type = 'info') {
    const messageEl = document.getElementById('message');
    if (!messageEl) return;

    messageEl.textContent = text;
    messageEl.className = `message ${type}`;
    messageEl.style.display = 'block';

    // 自动隐藏
    setTimeout(() => {
        messageEl.style.display = 'none';
    }, 3000);
}

// 显示/隐藏加载动画
function showLoading(show) {
    const loadingEl = document.getElementById('loading');
    if (!loadingEl) return;

    loadingEl.style.display = show ? 'flex' : 'none';
}

// 工具函数对象
const Utils = {
    // 日志工具
    log: {
        debug: console.log.bind(console),
        info: console.info.bind(console),
        warn: console.warn.bind(console),
        error: console.error.bind(console)
    },

    // DOM工具
    dom: {
        find: (selector) => document.querySelector(selector),
        findAll: (selector) => document.querySelectorAll(selector)
    },

    // 存储工具
    storage: {
        get: (key, defaultValue = null) => {
            try {
                const value = localStorage.getItem(key);
                return value ? JSON.parse(value) : defaultValue;
            } catch {
                return defaultValue;
            }
        },
        set: (key, value) => {
            try {
                localStorage.setItem(key, JSON.stringify(value));
            } catch (e) {
                console.warn('存储失败:', e);
            }
        }
    },

    // 防抖函数
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // HTML转义
    escapeHtml: (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // 格式化日期时间
    formatDateTime: (date) => {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleString('zh-CN');
    },

    formatFullDateTime: (date) => {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
}; 