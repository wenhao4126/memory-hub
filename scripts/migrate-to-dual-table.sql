-- ============================================================
-- Memory Hub 双表隔离架构迁移脚本
-- ============================================================
-- 功能：将单一 memories 表拆分为 private_memories 和 shared_memories
-- 作者：小码
-- 日期：2026-03-09
-- ============================================================

BEGIN;

-- ============================================================
-- 步骤 1: 备份现有数据
-- ============================================================

-- 创建备份表
CREATE TABLE IF NOT EXISTS memories_backup_20260309 AS 
SELECT * FROM memories;

COMMENT ON TABLE memories_backup_20260309 IS '双表迁移前的备份 - 2026-03-09';

-- ============================================================
-- 步骤 2: 创建 private_memories 表（私人记忆）
-- ============================================================

CREATE TABLE IF NOT EXISTS private_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    
    -- 记忆内容
    content TEXT NOT NULL,
    
    -- 向量嵌入（用于语义搜索）
    embedding vector(1024),
    
    -- 元数据
    memory_type VARCHAR(50) DEFAULT 'fact',
    importance FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    
    -- 时间信息
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- 标签和分类
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

COMMENT ON TABLE private_memories IS '私人记忆表：存储智能体的私有记忆，仅自己可访问';
COMMENT ON COLUMN private_memories.embedding IS '记忆内容的向量嵌入，用于语义相似性搜索';
COMMENT ON COLUMN private_memories.importance IS '重要性分数，用于遗忘机制';
COMMENT ON COLUMN private_memories.access_count IS '访问次数，用于判断记忆活跃度';

-- ============================================================
-- 步骤 3: 创建 shared_memories 表（共同记忆）
-- ============================================================

CREATE TABLE IF NOT EXISTS shared_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    
    -- 记忆内容
    content TEXT NOT NULL,
    
    -- 向量嵌入（用于语义搜索）
    embedding vector(1024),
    
    -- 元数据
    memory_type VARCHAR(50) DEFAULT 'fact',
    importance FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    
    -- 时间信息
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- 标签和分类
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- 共享相关字段
    visibility VARCHAR(50) DEFAULT 'team',  -- team: 团队可见，public: 公开
    allowed_agents UUID[] DEFAULT '{}'      -- 允许访问的智能体列表（为空表示团队全部）
);

COMMENT ON TABLE shared_memories IS '共同记忆表：存储团队共享记忆，所有智能体可访问';
COMMENT ON COLUMN shared_memories.visibility IS '可见性：team(团队可见) 或 public(公开)';
COMMENT ON COLUMN shared_memories.allowed_agents IS '允许访问的智能体列表，为空表示团队全部可见';

-- ============================================================
-- 步骤 4: 创建索引
-- ============================================================

-- private_memories 索引
CREATE INDEX IF NOT EXISTS idx_private_memories_agent_id ON private_memories(agent_id);
CREATE INDEX IF NOT EXISTS idx_private_memories_type ON private_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_private_memories_importance ON private_memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_private_memories_created_at ON private_memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_private_memories_tags ON private_memories USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_private_memories_embedding ON private_memories 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- shared_memories 索引
CREATE INDEX IF NOT EXISTS idx_shared_memories_agent_id ON shared_memories(agent_id);
CREATE INDEX IF NOT EXISTS idx_shared_memories_type ON shared_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_shared_memories_importance ON shared_memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_shared_memories_created_at ON shared_memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_shared_memories_tags ON shared_memories USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_shared_memories_visibility ON shared_memories(visibility);
CREATE INDEX IF NOT EXISTS idx_shared_memories_embedding ON shared_memories 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================
-- 步骤 5: 数据迁移（基于内容自动分类）
-- ============================================================

-- 迁移规则：
-- 1. 包含个人偏好、习惯、密码等 → private_memories
-- 2. 包含项目、经验、知识、规范等 → shared_memories
-- 3. 其他默认 → private_memories（保护隐私）

-- 迁移私人记忆
INSERT INTO private_memories (
    id, agent_id, content, embedding, memory_type, importance, 
    access_count, created_at, last_accessed, expires_at, tags, metadata
)
SELECT 
    id, agent_id, content, embedding, memory_type, importance,
    access_count, created_at, last_accessed, expires_at, tags, metadata
FROM memories
WHERE 
    content ILIKE '%密码%' OR
    content ILIKE '%习惯%' OR
    content ILIKE '%喜欢%' OR
    content ILIKE '%不喜欢%' OR
    content ILIKE '%偏好%' OR
    content ILIKE '%私人%' OR
    content ILIKE '%个人%' OR
    content ILIKE '%账号%' OR
    content ILIKE '%微信%' OR
    content ILIKE '%电话%' OR
    content ILIKE '%邮箱%' OR
    memory_type = 'preference';

-- 迁移共同记忆
INSERT INTO shared_memories (
    id, agent_id, content, embedding, memory_type, importance,
    access_count, created_at, last_accessed, expires_at, tags, metadata,
    visibility, allowed_agents
)
SELECT 
    id, agent_id, content, embedding, memory_type, importance,
    access_count, created_at, last_accessed, expires_at, tags, metadata,
    'team', '{}'
FROM memories
WHERE 
    content ILIKE '%经验%' OR
    content ILIKE '%知识%' OR
    content ILIKE '%规范%' OR
    content ILIKE '%文档%' OR
    content ILIKE '%项目%' OR
    content ILIKE '%架构%' OR
    content ILIKE '%设计%' OR
    content ILIKE '%最佳实践%' OR
    content ILIKE '%方法论%' OR
    content ILIKE '%模板%' OR
    content ILIKE '%代码%' OR
    content ILIKE '%测试%' OR
    memory_type IN ('skill', 'experience');

-- 迁移剩余记忆（默认私人）
INSERT INTO private_memories (
    id, agent_id, content, embedding, memory_type, importance,
    access_count, created_at, last_accessed, expires_at, tags, metadata
)
SELECT 
    id, agent_id, content, embedding, memory_type, importance,
    access_count, created_at, last_accessed, expires_at, tags, metadata
FROM memories
WHERE id NOT IN (SELECT id FROM private_memories)
  AND id NOT IN (SELECT id FROM shared_memories);

-- ============================================================
-- 步骤 6: 创建视图（向后兼容）
-- ============================================================

-- 创建统一视图，兼容旧代码
CREATE OR REPLACE VIEW memories_view AS
SELECT 
    id, agent_id, content, embedding, memory_type, importance,
    access_count, created_at, last_accessed, expires_at, tags, metadata,
    'private'::VARCHAR AS visibility
FROM private_memories
UNION ALL
SELECT 
    id, agent_id, content, embedding, memory_type, importance,
    access_count, created_at, last_accessed, expires_at, tags, metadata,
    'shared'::VARCHAR AS visibility
FROM shared_memories;

COMMENT ON VIEW memories_view IS '记忆统一视图（向后兼容）';

-- ============================================================
-- 步骤 7: 创建搜索函数
-- ============================================================

-- 私人记忆搜索函数
CREATE OR REPLACE FUNCTION search_private_memories(
    query_embedding vector(1024),
    target_agent_id UUID,
    match_threshold FLOAT DEFAULT 0.5,
    match_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    agent_id UUID,
    content TEXT,
    similarity FLOAT,
    memory_type VARCHAR(50),
    importance FLOAT,
    tags TEXT[],
    visibility VARCHAR(50)
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
        m.memory_type,
        m.importance,
        m.tags,
        'private'::VARCHAR AS visibility
    FROM private_memories m
    WHERE 
        m.agent_id = target_agent_id
        AND 1 - (m.embedding <=> query_embedding) > match_threshold
    ORDER BY m.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 共同记忆搜索函数
CREATE OR REPLACE FUNCTION search_shared_memories(
    query_embedding vector(1024),
    target_agent_id UUID,
    match_threshold FLOAT DEFAULT 0.5,
    match_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    agent_id UUID,
    content TEXT,
    similarity FLOAT,
    memory_type VARCHAR(50),
    importance FLOAT,
    tags TEXT[],
    visibility VARCHAR(50)
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
        m.memory_type,
        m.importance,
        m.tags,
        'shared'::VARCHAR AS visibility
    FROM shared_memories m
    WHERE 
        (m.visibility = 'public' OR 
         m.allowed_agents = '{}' OR 
         target_agent_id = ANY(m.allowed_agents))
        AND 1 - (m.embedding <=> query_embedding) > match_threshold
    ORDER BY m.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 统一搜索函数（兼容旧代码）
CREATE OR REPLACE FUNCTION search_similar_memories(
    query_embedding vector(1024),
    target_agent_id UUID DEFAULT NULL,
    match_threshold FLOAT DEFAULT 0.5,
    match_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    agent_id UUID,
    content TEXT,
    similarity FLOAT,
    memory_type VARCHAR(50),
    importance FLOAT,
    tags TEXT[],
    visibility VARCHAR(50)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM search_private_memories(
        query_embedding, target_agent_id, match_threshold, match_count
    )
    UNION ALL
    SELECT * FROM search_shared_memories(
        query_embedding, target_agent_id, match_threshold, match_count
    )
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- ============================================================
-- 步骤 8: 创建记忆路由函数（自动分类）
-- ============================================================

CREATE OR REPLACE FUNCTION route_memory(content TEXT)
RETURNS VARCHAR(50)
LANGUAGE plpgsql
AS $$
BEGIN
    -- 私人记忆关键词
    IF content ILIKE '%密码%' OR
       content ILIKE '%习惯%' OR
       content ILIKE '%喜欢%' OR
       content ILIKE '%不喜欢%' OR
       content ILIKE '%偏好%' OR
       content ILIKE '%私人%' OR
       content ILIKE '%个人%' OR
       content ILIKE '%账号%' OR
       content ILIKE '%微信%' OR
       content ILIKE '%电话%' OR
       content ILIKE '%邮箱%' THEN
        RETURN 'private';
    END IF;
    
    -- 共同记忆关键词
    IF content ILIKE '%经验%' OR
       content ILIKE '%知识%' OR
       content ILIKE '%规范%' OR
       content ILIKE '%文档%' OR
       content ILIKE '%项目%' OR
       content ILIKE '%架构%' OR
       content ILIKE '%设计%' OR
       content ILIKE '%最佳实践%' OR
       content ILIKE '%方法论%' OR
       content ILIKE '%模板%' OR
       content ILIKE '%代码%' OR
       content ILIKE '%测试%' THEN
        RETURN 'shared';
    END IF;
    
    -- 默认私人（保护隐私）
    RETURN 'private';
END;
$$;

COMMENT ON FUNCTION route_memory IS '根据内容自动路由记忆到合适的表';

-- ============================================================
-- 输出迁移信息
-- ============================================================

DO $$
DECLARE
    private_count INTEGER;
    shared_count INTEGER;
    total_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO private_count FROM private_memories;
    SELECT COUNT(*) INTO shared_count FROM shared_memories;
    SELECT COUNT(*) INTO total_count FROM memories_backup_20260309;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE '双表迁移完成！';
    RAISE NOTICE '';
    RAISE NOTICE '迁移统计:';
    RAISE NOTICE '  - 原始记忆总数：%', total_count;
    RAISE NOTICE '  - 私人记忆数：%', private_count;
    RAISE NOTICE '  - 共同记忆数：%', shared_count;
    RAISE NOTICE '  - 备份表：memories_backup_20260309';
    RAISE NOTICE '';
    RAISE NOTICE '新建表:';
    RAISE NOTICE '  - private_memories (私人记忆表)';
    RAISE NOTICE '  - shared_memories (共同记忆表)';
    RAISE NOTICE '';
    RAISE NOTICE '新建函数:';
    RAISE NOTICE '  - route_memory(content) - 自动路由函数';
    RAISE NOTICE '  - search_private_memories() - 私人记忆搜索';
    RAISE NOTICE '  - search_shared_memories() - 共同记忆搜索';
    RAISE NOTICE '========================================';
END $$;

COMMIT;
