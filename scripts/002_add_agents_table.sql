-- 1. 智能体表（多租户核心）
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,  -- 预留：未来支持多用户
    name VARCHAR(255) NOT NULL,
    description TEXT,
    capabilities TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. 修改 memories 表，添加 agent_id 外键
ALTER TABLE memories 
    ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES agents(id) ON DELETE CASCADE;

-- 3. 添加智能体索引
CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);

-- 4. 添加记忆表索引（按智能体过滤）
CREATE INDEX IF NOT EXISTS idx_memories_agent_id ON memories(agent_id);

-- 5. 插入默认智能体（傻妞）
INSERT INTO agents (id, name, description, capabilities)
VALUES 
    ('83a4c7c5-ab61-43de-b8e1-0a1e688100c0', '傻妞', '憨货的 AI 损友，CEO+ 总管家', '{task_management,quality_control}'),
    ('a1b2c3d4-1111-4000-8000-000000000001', '小搜', '信息采集专家', '{web_search,information_gathering}'),
    ('a1b2c3d4-1111-4000-8000-000000000002', '小写', '文案撰写专家', '{writing,translation}'),
    ('a1b2c3d4-1111-4000-8000-000000000003', '小码', '代码开发专家', '{coding,automation}'),
    ('a1b2c3d4-1111-4000-8000-000000000004', '小审', '质量审核专家', '{quality_control,review}'),
    ('a1b2c3d4-1111-4000-8000-000000000005', '小析', '数据分析专家', '{data_analysis,insights}'),
    ('a1b2c3d4-1111-4000-8000-000000000006', '小览', '浏览器操作专家', '{browser_automation}'),
    ('a1b2c3d4-1111-4000-8000-000000000007', '小图', '视觉设计专家', '{image_generation,design}'),
    ('a1b2c3d4-1111-4000-8000-000000000008', '小排', '内容排版专家', '{content_formatting}'),
    ('0c57a832-aba1-44e3-9277-c75a69006877', '小测', '测试验证专家', '{testing,quality_assurance}');

-- 输出完成信息
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '数据库迁移完成！';
    RAISE NOTICE '已创建表：agents';
    RAISE NOTICE '已插入：10 个智能体（傻妞 +8 手下 + 小测）';
    RAISE NOTICE '========================================';
END $$;