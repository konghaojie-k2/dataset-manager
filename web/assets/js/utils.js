/**
 * 工具函数集合
 * 包含常用的格式化、验证、DOM操作等辅助函数
 */

const Utils = {
    /**
     * 格式化文件大小
     * @param {number} bytes - 字节数
     * @returns {string} 格式化后的文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * 格式化日期时间
     * @param {string} dateString - 日期字符串
     * @returns {string} 格式化后的日期
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) {
            return '今天';
        } else if (diffDays === 2) {
            return '昨天';
        } else if (diffDays <= 7) {
            return `${diffDays-1}天前`;
        } else {
            return date.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
        }
    },

    /**
     * 格式化完整日期时间
     * @param {string} dateString - 日期字符串
     * @returns {string} 完整的日期时间字符串
     */
    formatFullDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    },

    /**
     * 获取文件扩展名
     * @param {string} filename - 文件名
     * @returns {string} 文件扩展名
     */
    getFileExtension(filename) {
        return '.' + filename.split('.').pop().toLowerCase();
    },

    /**
     * 验证文件类型
     * @param {File} file - 文件对象
     * @returns {boolean} 是否为允许的文件类型
     */
    validateFileType(file) {
        const extension = this.getFileExtension(file.name);
        return CONFIG.UPLOAD.ALLOWED_TYPES.includes(extension);
    },

    /**
     * 验证文件大小
     * @param {File} file - 文件对象
     * @returns {boolean} 是否在允许的大小范围内
     */
    validateFileSize(file) {
        return file.size <= CONFIG.UPLOAD.MAX_SIZE;
    },

    /**
     * 生成随机ID
     * @param {number} length - ID长度
     * @returns {string} 随机ID字符串
     */
    generateId(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    },

    /**
     * 防抖函数
     * @param {Function} func - 要防抖的函数
     * @param {number} wait - 等待时间 (毫秒)
     * @returns {Function} 防抖后的函数
     */
    debounce(func, wait) {
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

    /**
     * 节流函数
     * @param {Function} func - 要节流的函数
     * @param {number} limit - 时间间隔 (毫秒)
     * @returns {Function} 节流后的函数
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * 深度复制对象
     * @param {any} obj - 要复制的对象
     * @returns {any} 复制后的对象
     */
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (obj instanceof Object) {
            const clonedObj = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    },

    /**
     * 转义HTML特殊字符
     * @param {string} text - 要转义的文本
     * @returns {string} 转义后的文本
     */
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, (m) => map[m]);
    },

    /**
     * 解析查询字符串
     * @param {string} queryString - 查询字符串
     * @returns {Object} 解析后的参数对象
     */
    parseQueryString(queryString) {
        const params = {};
        const pairs = (queryString || '').split('&');
        for (let pair of pairs) {
            const [key, value] = pair.split('=');
            if (key) {
                params[decodeURIComponent(key)] = decodeURIComponent(value || '');
            }
        }
        return params;
    },

    /**
     * 构建查询字符串
     * @param {Object} params - 参数对象
     * @returns {string} 查询字符串
     */
    buildQueryString(params) {
        const pairs = [];
        for (const [key, value] of Object.entries(params)) {
            if (value !== null && value !== undefined && value !== '') {
                pairs.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
            }
        }
        return pairs.join('&');
    },

    /**
     * 本地存储操作
     */
    storage: {
        /**
         * 设置本地存储
         * @param {string} key - 键名
         * @param {any} value - 值
         */
        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
            } catch (e) {
                console.warn('localStorage设置失败:', e);
            }
        },

        /**
         * 获取本地存储
         * @param {string} key - 键名
         * @param {any} defaultValue - 默认值
         * @returns {any} 存储的值或默认值
         */
        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                console.warn('localStorage获取失败:', e);
                return defaultValue;
            }
        },

        /**
         * 删除本地存储
         * @param {string} key - 键名
         */
        remove(key) {
            try {
                localStorage.removeItem(key);
            } catch (e) {
                console.warn('localStorage删除失败:', e);
            }
        },

        /**
         * 清空本地存储
         */
        clear() {
            try {
                localStorage.clear();
            } catch (e) {
                console.warn('localStorage清空失败:', e);
            }
        }
    },

    /**
     * DOM操作辅助函数
     */
    dom: {
        /**
         * 查找元素
         * @param {string} selector - CSS选择器
         * @param {Element} parent - 父元素 (可选)
         * @returns {Element|null} 找到的元素
         */
        find(selector, parent = document) {
            return parent.querySelector(selector);
        },

        /**
         * 查找所有匹配的元素
         * @param {string} selector - CSS选择器
         * @param {Element} parent - 父元素 (可选)
         * @returns {NodeList} 找到的元素列表
         */
        findAll(selector, parent = document) {
            return parent.querySelectorAll(selector);
        },

        /**
         * 添加CSS类
         * @param {Element} element - 目标元素
         * @param {...string} classes - 要添加的类名
         */
        addClass(element, ...classes) {
            if (element) {
                element.classList.add(...classes);
            }
        },

        /**
         * 移除CSS类
         * @param {Element} element - 目标元素
         * @param {...string} classes - 要移除的类名
         */
        removeClass(element, ...classes) {
            if (element) {
                element.classList.remove(...classes);
            }
        },

        /**
         * 切换CSS类
         * @param {Element} element - 目标元素
         * @param {string} className - 要切换的类名
         * @returns {boolean} 是否包含该类
         */
        toggleClass(element, className) {
            return element ? element.classList.toggle(className) : false;
        },

        /**
         * 检查是否包含CSS类
         * @param {Element} element - 目标元素
         * @param {string} className - 要检查的类名
         * @returns {boolean} 是否包含该类
         */
        hasClass(element, className) {
            return element ? element.classList.contains(className) : false;
        },

        /**
         * 设置元素显示/隐藏
         * @param {Element} element - 目标元素
         * @param {boolean} show - 是否显示
         */
        toggle(element, show) {
            if (element) {
                element.style.display = show ? 'block' : 'none';
            }
        },

        /**
         * 创建元素
         * @param {string} tagName - 标签名
         * @param {Object} attributes - 属性对象
         * @param {string} textContent - 文本内容
         * @returns {Element} 创建的元素
         */
        create(tagName, attributes = {}, textContent = '') {
            const element = document.createElement(tagName);
            Object.entries(attributes).forEach(([key, value]) => {
                element.setAttribute(key, value);
            });
            if (textContent) {
                element.textContent = textContent;
            }
            return element;
        }
    },

    /**
     * 日志输出 (仅在调试模式下输出)
     */
    log: {
        debug(...args) {
            if (CONFIG.DEBUG) {
                console.log('[DEBUG]', ...args);
            }
        },
        info(...args) {
            console.info('[INFO]', ...args);
        },
        warn(...args) {
            console.warn('[WARN]', ...args);
        },
        error(...args) {
            console.error('[ERROR]', ...args);
        }
    }
};

// 冻结工具对象，防止意外修改
Object.freeze(Utils); 