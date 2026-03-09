-- ============================================================
-- 多智能体记忆中枢 - 自动记忆模块数据库迁移
-- ============================================================
-- 功能：创建 conversations 表，支持对话记录
-- 作者：小码
-- 日期：2026-03-06
-- ============================================================

-- 创建 conversations 表
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_conversations_agent_id ON conversations(agent_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);

-- 添加注释
COMMENT ON TABLE conversations IS '对话记录表：存储用户和AI的对话历史';
COMMENT ON COLUMN conversations.id IS '对话记录唯一标识';
COMMENT ON COLUMN conversations.agent_id IS '关联的智能体ID';
COMMENT ON COLUMN conversations.session_id IS '会话标识，用于关联同一会话的多轮对话';
COMMENT ON COLUMN conversations.user_message IS '用户输入的消息';
COMMENT ON COLUMN conversations.ai_response IS 'AI回复的消息';
COMMENT ON COLUMN conversations.created_at IS '对话创建时间';
COMMENT ON COLUMN conversations.metadata IS '额外元数据（JSON格式）';

-- 验证创建成功
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'conversations') THEN
        RAISE NOTICE '✅ conversations 表创建成功';
    ELSE
        RAISE EXCEPTION '❌ conversations 表创建失败';
    END IF;
END $$;