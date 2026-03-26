# ============================================================
# Memory Hub - 记忆版本控制数据模型
# ============================================================
# 功能：定义版本控制相关的数据结构
# 作者：小码 1 号
# 日期：2026-03-23
# ============================================================

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from enum import Enum


# ============================================================
# 版本历史模型
# ============================================================

class MemoryVersion(BaseModel):
    """记忆版本快照"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    memory_id: UUID
    version_number: int
    content: str
    memory_type: Optional[str] = None
    importance: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    changed_by: Optional[UUID] = None
    change_reason: Optional[str] = None
    created_at: datetime


class VersionHistoryResponse(BaseModel):
    """版本历史响应"""
    memory_id: UUID
    current_version: int
    total_versions: int
    versions: List[MemoryVersion]


class VersionDetailResponse(BaseModel):
    """单个版本详情响应"""
    memory_id: UUID
    version_number: int
    content: str
    memory_type: Optional[str] = None
    importance: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    changed_by: Optional[UUID] = None
    change_reason: Optional[str] = None
    created_at: datetime


# ============================================================
# 版本操作请求模型
# ============================================================

class RollbackRequest(BaseModel):
    """回滚请求"""
    reason: Optional[str] = Field(None, description="回滚原因")


class RollbackResponse(BaseModel):
    """回滚响应"""
    success: bool
    memory_id: UUID
    rolled_back_from: int
    rolled_back_to: int
    message: str


class VersionDiff(BaseModel):
    """版本差异"""
    field: str
    old_value: Any
    new_value: Any
    change_type: str  # 'added', 'removed', 'modified'


class VersionCompareResponse(BaseModel):
    """版本比较响应"""
    memory_id: UUID
    version1: VersionDetailResponse
    version2: VersionDetailResponse
    diffs: List[VersionDiff]
    similarity_score: Optional[float] = None  # 内容相似度（0-1）


# ============================================================
# 更新记忆请求（带版本控制）
# ============================================================

class MemoryUpdateWithVersion(BaseModel):
    """更新记忆请求（带版本控制）"""
    content: Optional[str] = Field(None, description="记忆内容")
    memory_type: Optional[str] = Field(None, description="记忆类型")
    importance: Optional[float] = Field(None, ge=0.0, le=1.0, description="重要性")
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    change_reason: Optional[str] = Field(None, description="修改原因")
    changed_by: Optional[UUID] = Field(None, description="修改者（智能体 ID）")