-- ============================================================
-- 数据库迁移：Embedding 维度 512 → 1024
-- ============================================================
-- 背景：从 bge-small-zh-v1.5 (512维) 迁移到 text-embedding-v4 (1024维)
-- 执行前请先备份数据！
-- ============================================================

-- 开始事务
BEGIN;

-- 0. 先删除旧函数（避免返回类型冲突）
DROP FUNCTION IF EXISTS search_similar_memories CASCADE;

-- 1. 删除旧的索引
DROP INDEX IF EXISTS idx_memories_embedding;

-- 2. 删除旧的 embedding 列（512 维）
ALTER TABLE memories DROP COLUMN IF EXISTS embedding;

-- 3. 添加新的 embedding 列（1024 维）
ALTER TABLE memories ADD COLUMN embedding vector(1024);

-- 4. 创建新的索引（使用 ivfflat 加速向量搜索）
-- 注意：ivfflat 索引需要数据量 >= lists（这里假设 lists = 100）
-- 如果数据量少于 100，可以先不加索引，等数据量增长后再创建
CREATE INDEX idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 5. 删除旧的 search_similar_memories 函数（512 维）
DROP FUNCTION IF EXISTS search_similar_memories(vector(512), uuid, float, int);

-- 6. 创建新的 search_similar_memories 函数（1024 维）
CREATE OR REPLACE FUNCTION search_similar_memories(
    query_embedding vector(1024),
    filter_agent_id uuid DEFAULT NULL,
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id uuid,
    agent_id uuid,
    content text,
    similarity float,
    memory_type text,
    importance float,
    tags text[]
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.agent_id,
        m.content,
        1 - (m.embedding <=> query_embedding) AS similarity,
        m.memory_type::text,
        m.importance,
        m.tags
    FROM memories m
    WHERE 
        (filter_agent_id IS NULL OR m.agent_id = filter_agent_id)
        AND m.embedding IS NOT NULL
        AND 1 - (m.embedding <=> query_embedding) > match_threshold
    ORDER BY m.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 提交事务
COMMIT;

-- ============================================================
-- 迁移后说明
-- ============================================================
-- 1. 旧数据已删除（embedding 为 NULL）
-- 2. 需要重新生成 embedding：
--    - 方式一：通过 API 重新创建记忆（会自动生成 1024 维 embedding）
--    - 方式二：编写脚本批量重新生成（推荐）
-- 3. 新的 API Key 已配置：sk-8060572b6d3c423399d1dabd67dac5d4
-- 4. 新的模型：text-embedding-v4 (1024 维)
-- ============================================================