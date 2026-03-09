-- ============================================================
-- Memory Hub - 双表隔离架构迁移
-- ============================================================
-- 功能：将 memories 表拆分为 private_memories 和 shared_memories
-- 作者：小码
-- 日期：2026-03-09
-- ============================================================

BEGIN;

-- 1. 创建私人记忆表
CREATE TABLE IF NOT EXISTS private_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    
    -- 记忆内容
    content TEXT NOT NULL,
    memory_type VARCHAR(50) DEFAULT 'fact',
    importance FLOAT DEFAULT 0.5,
    
    -- 向量嵌入（用于语义搜索）
    embedding vector(1024),
    
    -- 元数据
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- 时间信息
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- 访问统计
    access_count INTEGER DEFAULT 0
);

-- 2. 创建共同记忆表
CREATE TABLE IF NOT EXISTS shared_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by UUID REFERENCES agents(id) ON DELETE SET NULL,
    team_id UUID,  -- 团队 ID（预留多团队）
    
    -- 记忆内容
    content TEXT NOT NULL,
    memory_type VARCHAR(50) DEFAULT 'experience',
    importance FLOAT DEFAULT 0.7,
    
    -- 向量嵌入
    embedding vector(1024),
    
    -- 访问控制
    visible_to UUID[] DEFAULT '{}',  -- 哪些智能体可见（空=全部可见）
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- 时间信息
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 统计信息
    access_count INTEGER DEFAULT 0,
    used_by UUID[] DEFAULT '{}'  -- 哪些智能体用过
);

-- 3. 创建索引

-- 私人记忆表索引
CREATE INDEX IF NOT EXISTS idx_private_memories_agent_id ON private_memories(agent_id);
CREATE INDEX IF NOT EXISTS idx_private_memories_memory_type ON private_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_private_memories_importance ON private_memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_private_memories_created_at ON private_memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_private_memories_tags ON private_memories USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_private_memories_embedding ON private_memories 
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- 共同记忆表索引
CREATE INDEX IF NOT EXISTS idx_shared_memories_team_id ON shared_memories(team_id);
CREATE INDEX IF NOT EXISTS idx_shared_memories_created_by ON shared_memories(created_by);
CREATE INDEX IF NOT EXISTS idx_shared_memories_memory_type ON shared_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_shared_memories_importance ON shared_memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_shared_memories_visible_to ON shared_memories USING GIN(visible_to);
CREATE INDEX IF NOT EXISTS idx_shared_memories_tags ON shared_memories USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_shared_memories_embedding ON shared_memories 
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- 4. 迁移现有数据（从 memories 表到新表）

-- 迁移私人记忆
INSERT INTO private_memories (
    id, agent_id, content, memory_type, importance, 
    embedding, tags, metadata, created_at, access_count
)
SELECT 
    id, agent_id, content, memory_type, importance,
    embedding, tags, metadata, created_at, access_count
FROM memories
WHERE 
    visibility = 'private' 
    OR metadata->>'visibility' = 'private'
    OR (metadata IS NULL AND agent_id IS NOT NULL);

-- 迁移共同记忆
INSERT INTO shared_memories (
    id, created_by, content, memory_type, importance,
    embedding, tags, metadata, created_at, access_count
)
SELECT 
    id, agent_id as created_by, content, memory_type, importance,
    embedding, tags, metadata, created_at, access_count
FROM memories
WHERE 
    visibility = 'shared' 
    OR metadata->>'visibility' = 'shared';

-- 5. 重命名旧表（备份）
ALTER TABLE memories RENAME TO memories_backup_20260309;

-- 6. 创建视图（向后兼容，可选）
CREATE OR REPLACE VIEW memories AS
SELECT 
    p.id, p.agent_id as created_by, p.content, p.memory_type, 
    p.importance, p.embedding, p.tags, p.metadata, 
    p.created_at, p.access_count,
    'private' as visibility
FROM private_memories p
UNION ALL
SELECT 
    s.id, s.created_by as agent_id, s.content, s.memory_type,
    s.importance, s.embedding, s.tags, s.metadata,
    s.created_at, s.access_count,
    'shared' as visibility
FROM shared_memories s;

-- 7. 输出完成信息
DO $$
DECLARE
    private_count INTEGER;
    shared_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO private_count FROM private_memories;
    SELECT COUNT(*) INTO shared_count FROM shared_memories;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE '数据库迁移完成！';
    RAISE NOTICE '已创建表：private_memories, shared_memories';
    RAISE NOTICE '迁移数据：私人记忆 {} 条，共同记忆 {} 条', private_count, shared_count;
    RAISE NOTICE '旧表已备份：memories_backup_20260309';
    RAISE NOTICE '========================================';
END $$;

COMMIT;