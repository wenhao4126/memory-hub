# ============================================================
# 多智能体记忆中枢 - 数据模型
# ============================================================
# 功能：定义数据结构和验证
# 作者：小码
# 日期：2026-03-05
# ============================================================

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID
from enum import Enum
import uuid


class MemoryType(str, Enum):
    """记忆类型枚举"""
    FACT = "fact"           # 事实：客观信息
    PREFERENCE = "preference"  # 偏好：用户喜好
    SKILL = "skill"         # 技能：能力标签
    EXPERIENCE = "experience"  # 经验：历史事件


class RelationType(str, Enum):
    """记忆关系类型"""
    SIMILAR = "similar"         # 相似
    CONTRADICTS = "contradicts"  # 矛盾
    DERIVES_FROM = "derives_from"  # 衍生
    SUPERSEDES = "supersedes"   # 取代


# ============================================================
# 智能体相关模型
# ============================================================

class AgentBase(BaseModel):
    """智能体基础模型"""
    name: str = Field(..., min_length=1, max_length=255, description="智能体名称")
    description: Optional[str] = Field(None, description="智能体描述")
    capabilities: List[str] = Field(default_factory=list, description="能力标签")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class AgentCreate(AgentBase):
    """创建智能体请求模型"""
    pass


class AgentUpdate(BaseModel):
    """更新智能体请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="智能体名称")
    description: Optional[str] = Field(None, description="智能体描述")
    capabilities: Optional[List[str]] = Field(None, description="能力标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class Agent(AgentBase):
    """智能体完整模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime


# ============================================================
# 记忆相关模型
# ============================================================

class MemoryBase(BaseModel):
    """记忆基础模型"""
    content: str = Field(..., min_length=1, description="记忆内容")
    memory_type: MemoryType = Field(default=MemoryType.FACT, description="记忆类型")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="重要性分数")
    tags: List[str] = Field(default_factory=list, description="标签")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class MemoryCreate(MemoryBase):
    """创建记忆请求模型"""
    agent_id: UUID = Field(..., description="所属智能体 ID")
    embedding: Optional[List[float]] = Field(None, description="向量嵌入")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    
    # 双表架构相关字段
    auto_route: bool = Field(default=True, description="是否自动路由到合适的表")
    visibility: Optional[str] = Field(default=None, description="可见性：private/shared（auto_route=false 时使用）")
    
    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v):
        """验证 embedding 维度（text-embedding-v4: 1024维）"""
        if v is not None and len(v) != 1024:
            raise ValueError('embedding 维度必须为 1024（text-embedding-v4 模型）')
        return v


class MemoryUpdate(BaseModel):
    """更新记忆请求模型"""
    content: Optional[str] = Field(None, min_length=1, description="记忆内容")
    memory_type: Optional[MemoryType] = Field(None, description="记忆类型")
    importance: Optional[float] = Field(None, ge=0.0, le=1.0, description="重要性分数")
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")
    embedding: Optional[List[float]] = Field(None, description="向量嵌入")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    
    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v):
        """验证 embedding 维度（text-embedding-v4: 1024维）"""
        if v is not None and len(v) != 1024:
            raise ValueError('embedding 维度必须为 1024（text-embedding-v4 模型）')
        return v


class Memory(MemoryBase):
    """记忆完整模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    agent_id: UUID
    embedding: Optional[List[float]] = None
    access_count: int = 0
    created_at: datetime
    last_accessed: datetime
    expires_at: Optional[datetime] = None


class MemorySearchRequest(BaseModel):
    """记忆搜索请求（旧版：需要 query_embedding）"""
    query_embedding: List[float] = Field(..., description="查询向量")
    agent_id: Optional[UUID] = Field(None, description="限定智能体")
    match_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="相似度阈值")
    match_count: int = Field(default=10, ge=1, le=100, description="返回数量")
    
    @field_validator('query_embedding')
    @classmethod
    def validate_query_embedding(cls, v):
        """验证查询向量维度（text-embedding-v4: 1024维）"""
        if len(v) != 1024:
            raise ValueError('query_embedding 维度必须为 1024（text-embedding-v4 模型）')
        return v


class MemoryTextSearchRequest(BaseModel):
    """记忆文本搜索请求（新版：接受 query 文本）"""
    query: str = Field(..., min_length=1, description="查询文本")
    agent_id: Optional[UUID] = Field(None, description="限定智能体")
    match_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="相似度阈值")
    match_count: int = Field(default=10, ge=1, le=100, description="返回数量")


class MemorySearchResult(BaseModel):
    """记忆搜索结果"""
    id: UUID
    agent_id: UUID
    content: str
    similarity: float
    memory_type: MemoryType
    importance: float
    tags: List[str]


# ============================================================
# 会话相关模型
# ============================================================

class SessionBase(BaseModel):
    """会话基础模型"""
    session_key: str = Field(..., description="会话标识")
    context: Dict[str, Any] = Field(default_factory=dict, description="会话上下文")


class SessionCreate(SessionBase):
    """创建会话请求"""
    agent_id: UUID
    expires_at: Optional[datetime] = None


class Session(SessionBase):
    """会话完整模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    agent_id: UUID
    created_at: datetime
    expires_at: Optional[datetime] = None


# ============================================================
# 响应模型
# ============================================================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "ok"
    database: str = "connected"
    version: str = "0.1.0"


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: str
    status_code: int


# ============================================================
# 知识库相关模型
# ============================================================

class KnowledgeCreate(BaseModel):
    """创建知识请求模型"""
    agent_id: UUID = Field(..., description="所属智能体 ID")
    title: str = Field(..., min_length=1, max_length=500, description="知识标题")
    content: str = Field(..., min_length=1, max_length=50000, description="知识内容")
    category: Optional[str] = Field(None, max_length=100, description="分类")
    tags: List[str] = Field(default_factory=list, description="标签")
    source: Optional[str] = Field(None, max_length=500, description="来源")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="重要性")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class KnowledgeUpdate(BaseModel):
    """更新知识请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="知识标题")
    content: Optional[str] = Field(None, min_length=1, max_length=50000, description="知识内容")
    category: Optional[str] = Field(None, max_length=100, description="分类")
    tags: Optional[List[str]] = Field(None, description="标签")
    importance: Optional[float] = Field(None, ge=0.0, le=1.0, description="重要性")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class KnowledgeResponse(BaseModel):
    """知识完整模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    agent_id: UUID
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    importance: float
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class KnowledgeSearchRequest(BaseModel):
    """知识搜索请求"""
    query: str = Field(..., min_length=1, description="查询文本")
    agent_id: Optional[UUID] = Field(None, description="限定智能体")
    category: Optional[str] = Field(None, description="限定分类")
    match_threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="相似度阈值")
    match_count: int = Field(default=5, ge=1, le=50, description="返回数量")


class KnowledgeSearchResponse(BaseModel):
    """知识搜索结果"""
    id: UUID
    agent_id: UUID
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    similarity: float