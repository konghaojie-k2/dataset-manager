-- ====================================
-- Supabase 数据库初始化脚本
-- ====================================
-- 用途：创建 dataset-manager 所需的数据库表和索引
-- 环境：Supabase PostgreSQL
-- 版本：1.0
-- ====================================

-- 1. 创建数据集表
CREATE TABLE IF NOT EXISTS datasets (
    -- 主键和基本信息
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,

    -- 文件信息
    file_path TEXT NOT NULL,
    file_size BIGINT,
    file_hash TEXT,
    content_hash TEXT,

    -- 数据结构信息
    row_count INTEGER,
    column_count INTEGER,
    column_names JSONB,
    column_types JSONB,

    -- 分类和标签
    industry TEXT,
    tags TEXT[] DEFAULT '{}',

    -- 处理状态
    processing_status TEXT DEFAULT 'pending',
    data_source TEXT,
    data_quality_score FLOAT,

    -- 版本控制
    is_duplicate BOOLEAN DEFAULT FALSE,
    parent_dataset_id TEXT,
    version_number INTEGER DEFAULT 1,
    storage_strategy TEXT DEFAULT 'full',
    compression_info JSONB,

    -- 时间戳
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 元数据
    preview_data JSONB,
    metadata_version TEXT DEFAULT '1.0',

    -- 业务分析结果（JSONB格式，支持灵活查询）
    device_time_identification JSONB,
    business_meaning_analysis JSONB,
    control_relationships_analysis JSONB,
    basic_analysis JSONB,
    detailed_analysis JSONB,
    insights JSONB,
    recommendations JSONB,
    quality_analysis_results JSONB,
    business_analysis_results JSONB
);

-- 2. 创建索引 - 提升查询性能
CREATE INDEX IF NOT EXISTS idx_datasets_uploaded_at ON datasets(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_datasets_last_modified ON datasets(last_modified DESC);
CREATE INDEX IF NOT EXISTS idx_datasets_industry ON datasets(industry);
CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets(processing_status);
CREATE INDEX IF NOT EXISTS idx_datasets_tags ON datasets USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_datasets_file_hash ON datasets(file_hash);
CREATE INDEX IF NOT EXISTS idx_datasets_content_hash ON datasets(content_hash);
CREATE INDEX IF NOT EXISTS idx_datasets_parent ON datasets(parent_dataset_id);
CREATE INDEX IF NOT EXISTS idx_datasets_duplicate ON datasets(is_duplicate);

-- 3. 创建JSONB字段的GIN索引（用于分析结果查询）
CREATE INDEX IF NOT EXISTS idx_datasets_business_analysis ON datasets USING GIN(business_meaning_analysis);
CREATE INDEX IF NOT EXISTS idx_datasets_quality_analysis ON datasets USING GIN(quality_analysis_results);

-- 4. 启用行级安全策略（RLS）
ALTER TABLE datasets ENABLE ROW LEVEL SECURITY;

-- ====================================
-- 安全策略配置
-- ====================================

-- 开发环境策略：允许所有操作
CREATE POLICY "Allow all access on datasets" ON datasets
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- 生产环境策略（可选，根据实际需求配置）：
-- 如果需要用户级别的权限控制，可以取消注释以下代码并删除上面的开发策略

-- CREATE POLICY "Users can view their own datasets" ON datasets
--     FOR SELECT
--     USING (
--         uploaded_by = auth.uid()::text OR
--         is_public = true
--     );

-- CREATE POLICY "Users can insert their own datasets" ON datasets
--     FOR INSERT
--     WITH CHECK (uploaded_by = auth.uid()::text);

-- CREATE POLICY "Users can update their own datasets" ON datasets
--     FOR UPDATE
--     USING (uploaded_by = auth.uid()::text);

-- CREATE POLICY "Users can delete their own datasets" ON datasets
--     FOR DELETE
--     USING (uploaded_by = auth.uid()::text);

-- ====================================
-- 触发器：自动更新 last_modified
-- ====================================
CREATE OR REPLACE FUNCTION update_last_modified()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_modified = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_last_modified
    BEFORE UPDATE ON datasets
    FOR EACH ROW
    EXECUTE FUNCTION update_last_modified();

-- ====================================
-- 辅助函数
-- ====================================

-- 获取数据集统计信息
CREATE OR REPLACE FUNCTION get_dataset_stats()
RETURNS TABLE (
    total_datasets BIGINT,
    total_size_mb NUMERIC,
    status_counts JSONB,
    industry_counts JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_datasets,
        ROUND(COALESCE(SUM(file_size), 0) / 1024.0 / 1024.0, 2) as total_size_mb,
        jsonb_object_agg(
            COALESCE(processing_status, 'unknown'),
            COUNT(*)
        ) as status_counts,
        jsonb_object_agg(
            COALESCE(industry, 'unknown'),
            COUNT(*)
        ) as industry_counts
    FROM datasets;
END;
$$ LANGUAGE plpgsql;

-- 搜索数据集（全文搜索）
CREATE OR REPLACE FUNCTION search_datasets(
    search_term TEXT DEFAULT NULL,
    industry_filter TEXT DEFAULT NULL,
    status_filter TEXT DEFAULT NULL,
    tag_filters TEXT[] DEFAULT NULL,
    limit_count INTEGER DEFAULT 100,
    offset_count INTEGER DEFAULT 0
)
RETURNS TABLE (
    id TEXT,
    name TEXT,
    description TEXT,
    industry TEXT,
    tags TEXT[],
    processing_status TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.name,
        d.description,
        d.industry,
        d.tags,
        d.processing_status,
        d.uploaded_at
    FROM datasets d
    WHERE
        -- 搜索条件
        (search_term IS NULL OR
         d.name ILIKE '%' || search_term || '%' OR
         d.description ILIKE '%' || search_term || '%')
        -- 行业过滤
        AND (industry_filter IS NULL OR d.industry = industry_filter)
        -- 状态过滤
        AND (status_filter IS NULL OR d.processing_status = status_filter)
        -- 标签过滤（数组重叠）
        AND (tag_filters IS NULL OR d.tags && tag_filters)
    ORDER BY d.uploaded_at DESC
    LIMIT limit_count
    OFFSET offset_count;
END;
$$ LANGUAGE plpgsql;

-- ====================================
-- 数据清理任务（可选）
-- ====================================

-- 清理超过30天的软删除数据（如果实现了软删除）
-- CREATE OR REPLACE FUNCTION cleanup_old_datasets()
-- RETURNS INTEGER AS $$
-- DECLARE
--     deleted_count INTEGER;
-- BEGIN
--     DELETE FROM datasets
--     WHERE processing_status = 'deleted'
--     AND uploaded_at < NOW() - INTERVAL '30 days';
--
--     GET DIAGNOSTICS deleted_count = ROW_COUNT;
--     RETURN deleted_count;
-- END;
-- $$ LANGUAGE plpgsql;

-- ====================================
-- 视图：数据集摘要
-- ====================================
CREATE OR REPLACE VIEW dataset_summary AS
SELECT
    id,
    name,
    industry,
    processing_status,
    row_count,
    column_count,
    file_size,
    uploaded_at,
    last_modified,
    tags,
    data_quality_score
FROM datasets
ORDER BY uploaded_at DESC;

-- ====================================
-- 完成提示
-- ====================================
DO $$
BEGIN
    RAISE NOTICE '====================================';
    RAISE NOTICE 'Supabase 数据库初始化完成！';
    RAISE NOTICE '====================================';
    RAISE NOTICE '已创建的表：datasets';
    RAISE NOTICE '已创建的索引：10个';
    RAISE NOTICE '已创建的视图：dataset_summary';
    RAISE NOTICE '已创建的函数：get_dataset_stats(), search_datasets()';
    RAISE NOTICE '已创建的触发器：自动更新 last_modified';
    RAISE NOTICE '====================================';
    RAISE NOTICE '下一步：配置 .env 文件并启动应用';
    RAISE NOTICE '====================================';
END $$;
