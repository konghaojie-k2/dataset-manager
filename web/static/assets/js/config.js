/**
 * 应用配置文件
 * 包含API端点、全局常量等配置项
 */

// API配置
const CONFIG = {
    // API基础URL
    API_BASE: '/api/v1',
    
    // 文件上传配置
    UPLOAD: {
        // 允许的文件类型
        ALLOWED_TYPES: ['.csv', '.zip'],
        // 最大文件大小 (50MB)
        MAX_SIZE: 50 * 1024 * 1024,
        // 文件类型描述
        TYPE_DESCRIPTIONS: {
            '.csv': 'CSV数据文件',
            '.zip': 'ZIP压缩包'
        }
    },
    
    // 分页配置
    PAGINATION: {
        // 默认每页显示数量
        DEFAULT_PAGE_SIZE: 10,
        // 可选的每页显示数量
        PAGE_SIZE_OPTIONS: [5, 10, 20, 50]
    },
    
    // 消息提示配置
    MESSAGE: {
        // 显示时长 (毫秒)
        DURATION: 3000,
        // 消息类型
        TYPES: {
            SUCCESS: 'success',
            ERROR: 'error',
            INFO: 'info',
            WARNING: 'warning'
        }
    },
    
    // LangGraph流程步骤配置
    WORKFLOW: {
        STEPS: [
            { id: 'upload', name: '数据上传', icon: '📤', description: '文件上传与基础信息提取' },
            { id: 'business', name: '业务分析', icon: '💡', description: '业务语义分析、控制逻辑推理' },
            { id: 'quality', name: '数据质量分析', icon: '✅', description: '数据质量评估与分析' }
        ]
    },
    
    // 数据集状态配置 - 更新为支持新的分析阶段
    DATASET_STATUS: {
        UPLOADED: 'uploaded',                    // 已上传，未开始分析
        BUSINESS_ANALYZING: 'business_analyzing', // 业务分析中
        BUSINESS_COMPLETED: 'business_completed', // 业务分析完成
        QUALITY_ANALYZING: 'quality_analyzing',   // 质量分析中
        QUALITY_COMPLETED: 'quality_completed',   // 质量分析完成
        ANALYSIS_FAILED: 'analysis_failed'        // 分析失败
    },
    
    // 状态文本映射
    STATUS_TEXT: {
        'uploaded': '已上传',
        'business_analyzing': '业务分析中',
        'business_completed': '业务分析完成',
        'quality_analyzing': '质量分析中', 
        'quality_completed': '质量分析完成',
        'analysis_failed': '分析失败'
    },
    
    // 状态样式类映射
    STATUS_CLASS: {
        'uploaded': 'uploaded',
        'business_analyzing': 'analyzing',
        'business_completed': 'completed',
        'quality_analyzing': 'analyzing',
        'quality_completed': 'completed',
        'analysis_failed': 'failed'
    },
    
    // 数据质量评分配置
    QUALITY: {
        // 评分等级
        GRADES: {
            EXCELLENT: { min: 90, color: '#28a745', label: '优秀' },
            GOOD: { min: 70, color: '#ffc107', label: '良好' },
            FAIR: { min: 50, color: '#fd7e14', label: '一般' },
            POOR: { min: 0, color: '#dc3545', label: '较差' }
        }
    },
    
    // 动画配置
    ANIMATION: {
        // 默认动画时长
        DURATION: 300,
        // 缓动函数
        EASING: 'ease-in-out'
    },
    
    // 调试模式
    DEBUG: false
};

// 冻结配置对象，防止意外修改
Object.freeze(CONFIG);

// 导出配置 (如果支持模块化)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} 