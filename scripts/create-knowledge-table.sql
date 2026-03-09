-- ============================================================
-- 知识库表创建脚本
-- ============================================================
-- 功能：创建 knowledge 表和相关索引
-- 作者：小码
-- 日期：2026-03-07
-- ============================================================

-- 启用 pgvector 扩展（如果还没启用）
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建 knowledge 表
CREATE TABLE IF NOT EXISTS knowledge (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  title TEXT NOT NULL,                    -- 知识标题
  content TEXT NOT NULL,                  -- 知识内容
  category TEXT,                          -- 分类（如"编程"、"设计"）
  tags TEXT[],                            -- 标签数组
  source TEXT,                            -- 来源（如"Obsidian/xxx.md"）
  embedding vector(1024),                 -- 向量（1024 维）
  importance FLOAT DEFAULT 0.5,           -- 重要性
  metadata JSONB DEFAULT '{}',            -- 元数据
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建向量索引（HNSW 算法，更快）
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding 
ON knowledge USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 创建普通索引
CREATE INDEX IF NOT EXISTS idx_knowledge_agent_id ON knowledge (agent_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge (category);
CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_knowledge_created_at ON knowledge (created_at);

-- 创建更新时间触发器（如果不存在）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 删除旧触发器（如果存在）
DROP TRIGGER IF EXISTS update_knowledge_updated_at ON knowledge;

-- 创建新触发器
CREATE TRIGGER update_knowledge_updated_at
  BEFORE UPDATE ON knowledge
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- 创建知识 agent（如果不存在）
INSERT INTO agents (name, description, capabilities, metadata, is_public)
VALUES (
  '知识',
  '知识库 agent，存储所有知识文件',
  '["knowledge_management", "question_answering"]',
  '{"role": "knowledge_base", "source": "obsidian"}',
  false
)
ON CONFLICT DO NOTHING;