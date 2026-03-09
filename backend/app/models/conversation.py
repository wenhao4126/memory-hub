# ============================================================
# 多智能体记忆中枢 - 对话数据模型
# ============================================================
# 功能：定义对话相关的数据结构
# 作者：小码
# 日期：2026-03-06
# ============================================================

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, UUID4, ConfigDict


# ============================================================
# 对话相关模型
# ============================================================

class ConversationBase(BaseModel):
    """对话基础模型"""
    user_message: str = Field(..., min_length=1, description="用户消息")
    ai_response: str = Field(..., min_length=1, description="AI回复")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class ConversationCreate(ConversationBase):
    """创建对话请求模型"""
    agent_id: UUID4 = Field(..., description="所属智能体 ID")
    session_id: str = Field(..., min_length=1, max_length=255, description="会话标识")


class Conversation(ConversationBase):
    """对话完整模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4
    agent_id: UUID4
    session_id: str
    created_at: datetime


class ConversationList(BaseModel):
    """对话列表响应模型"""
    conversations: list[Conversation]
    total: int
    limit: int
    offset: int


# ============================================================
# 记忆提取相关模型
# ============================================================

class ExtractedMemory(BaseModel):
    """提取的记忆项"""
    content: str = Field(..., description="记忆内容")
    memory_type: str = Field(..., description="记忆类型：fact/relationship/event/emotion")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="置信度")


class MemoryExtractionResult(BaseModel):
    """记忆提取结果"""
    facts: list[str] = Field(default_factory=list, description="提取的事实")
    relationships: list[str] = Field(default_factory=list, description="提取的关系")
    events: list[str] = Field(default_factory=list, description="提取的事件")
    emotions: list[str] = Field(default_factory=list, description="提取的情感")
    
    def to_memories(self) -> list[ExtractedMemory]:
        """转换为记忆列表"""
        memories = []
        for fact in self.facts:
            memories.append(ExtractedMemory(content=fact, memory_type="fact"))
        for relationship in self.relationships:
            memories.append(ExtractedMemory(content=relationship, memory_type="relationship"))
        for event in self.events:
            memories.append(ExtractedMemory(content=event, memory_type="event"))
        for emotion in self.emotions:
            memories.append(ExtractedMemory(content=emotion, memory_type="emotion"))
        return memories


class AutoExtractRequest(BaseModel):
    """自动提取请求"""
    agent_id: UUID4 = Field(..., description="智能体 ID")
    session_id: str = Field(..., description="会话标识")
    conversation_text: str = Field(..., min_length=1, description="对话内容")
    
    # 可选参数
    auto_store: bool = Field(default=True, description="是否自动存储到数据库")


class AutoExtractResponse(BaseModel):
    """自动提取响应"""
    extracted_memories: list[ExtractedMemory] = Field(default_factory=list, description="提取的记忆列表")
    stored_count: int = Field(default=0, description="已存储的记忆数量")
    message: str = Field(default="", description="处理消息")


# ============================================================
# 对话增强相关模型
# ============================================================

class MemorySource(BaseModel):
    """记忆来源信息"""
    id: str = Field(..., description="记忆 ID")
    content: str = Field(..., description="记忆内容")
    type: str = Field(..., description="记忆类型")
    similarity: float = Field(default=0.0, ge=0.0, le=1.0, description="相似度")


class EnhancedChatRequest(BaseModel):
    """增强对话请求"""
    agent_id: UUID4 = Field(..., description="智能体 ID")
    session_id: str = Field(..., min_length=1, max_length=255, description="会话标识")
    user_message: str = Field(..., min_length=1, description="用户消息")
    
    # 可选参数
    use_memory: bool = Field(default=True, description="是否使用记忆增强")
    use_history: bool = Field(default=True, description="是否使用对话历史")
    auto_extract: bool = Field(default=True, description="是否自动提取记忆")
    memory_count: int = Field(default=5, ge=1, le=20, description="检索记忆数量")
    history_count: int = Field(default=6, ge=1, le=20, description="历史对话数量")


class EnhancedReply(BaseModel):
    """增强对话响应"""
    reply: str = Field(..., description="AI 增强回复")
    conversation_id: Optional[str] = Field(default=None, description="对话记录 ID")
    memories_used: int = Field(default=0, description="使用的记忆数量")
    history_used: int = Field(default=0, description="使用的历史对话数量")
    memory_sources: list[MemorySource] = Field(default_factory=list, description="记忆来源详情")
    extracted_memories: Optional[list[ExtractedMemory]] = Field(default=None, description="提取的新记忆")
    stored_count: Optional[int] = Field(default=None, description="存储的新记忆数量")