# ============================================================
# Memory Hub - 记忆版本控制服务
# ============================================================
# 功能：管理记忆的历史版本
# 作者：小码 1 号
# 日期：2026-03-23
# ============================================================

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid
import json

from ..database import db
from ..models.version_schemas import (
    MemoryVersion,
    VersionHistoryResponse,
    VersionDetailResponse,
    RollbackRequest,
    RollbackResponse,
    VersionCompareResponse,
    VersionDiff
)

logger = logging.getLogger(__name__)


class VersionService:
    """记忆版本控制服务"""
    
    async def get_version_history(
        self,
        memory_id: str,
        table_name: str = 'private_memories',
        limit: int = 20,
        offset: int = 0
    ) -> VersionHistoryResponse:
        """
        获取记忆的版本历史
        
        Args:
            memory_id: 记忆 ID
            table_name: 表名（private_memories 或 shared_memories）
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            VersionHistoryResponse: 版本历史响应
        """
        # 获取当前记忆信息
        current_memory = await self._get_memory(memory_id, table_name)
        if not current_memory:
            raise ValueError(f"记忆不存在：{memory_id}")
        
        current_version = current_memory.get('current_version', 1)
        
        # 调用数据库函数获取版本历史
        versions_data = await db.fetch(
            "SELECT * FROM get_memory_versions($1, $2, $3, $4)",
            uuid.UUID(memory_id),
            table_name,
            limit,
            offset
        )
        
        # 构建版本列表
        versions = []
        for v in versions_data:
            versions.append(MemoryVersion(
                id=uuid.uuid4(),  # 临时 ID
                memory_id=uuid.UUID(memory_id),
                version_number=v['version_number'],
                content=v['content'],
                memory_type=v['memory_type'],
                importance=v['importance'],
                tags=v['tags'] or [],
                metadata={},
                changed_by=v['changed_by'],
                change_reason=v['change_reason'],
                created_at=v['created_at']
            ))
        
        return VersionHistoryResponse(
            memory_id=uuid.UUID(memory_id),
            current_version=current_version,
            total_versions=current_version,  # 当前版本号 = 总版本数
            versions=versions
        )
    
    async def get_version(
        self,
        memory_id: str,
        version_number: int,
        table_name: str = 'private_memories'
    ) -> VersionDetailResponse:
        """
        获取指定版本的详情
        
        Args:
            memory_id: 记忆 ID
            version_number: 版本号
            table_name: 表名
        
        Returns:
            VersionDetailResponse: 版本详情
        """
        version_table = f"{table_name.replace('memories', 'memory_versions')}"
        
        query = f"""
            SELECT 
                memory_id, version_number, content, memory_type,
                importance, tags, metadata, changed_by, change_reason, created_at
            FROM {version_table}
            WHERE memory_id = $1 AND version_number = $2
        """
        
        row = await db.fetchrow(query, uuid.UUID(memory_id), version_number)
        
        if not row:
            raise ValueError(f"版本不存在：记忆 {memory_id}，版本 {version_number}")
        
        return VersionDetailResponse(
            memory_id=row['memory_id'],
            version_number=row['version_number'],
            content=row['content'],
            memory_type=row['memory_type'],
            importance=row['importance'],
            tags=row['tags'] or [],
            metadata=row['metadata'] or {},
            changed_by=row['changed_by'],
            change_reason=row['change_reason'],
            created_at=row['created_at']
        )
    
    async def rollback_version(
        self,
        memory_id: str,
        version_number: int,
        reason: Optional[str] = None,
        table_name: str = 'private_memories'
    ) -> RollbackResponse:
        """
        回滚记忆到指定版本
        
        Args:
            memory_id: 记忆 ID
            version_number: 目标版本号
            reason: 回滚原因
            table_name: 表名
        
        Returns:
            RollbackResponse: 回滚结果
        """
        # 获取当前版本号
        current_memory = await self._get_memory(memory_id, table_name)
        if not current_memory:
            raise ValueError(f"记忆不存在：{memory_id}")
        
        current_version = current_memory.get('current_version', 1)
        
        # 检查目标版本是否存在
        target_version = await self.get_version(memory_id, version_number, table_name)
        
        # 调用数据库函数执行回滚
        success = await db.fetchval(
            "SELECT rollback_memory_version($1, $2, $3, $4)",
            uuid.UUID(memory_id),
            version_number,
            table_name,
            reason
        )
        
        if not success:
            raise RuntimeError(f"回滚失败：记忆 {memory_id}")
        
        logger.info(f"记忆回滚成功：{memory_id}，从版本 {current_version} 回滚到 {version_number}")
        
        return RollbackResponse(
            success=True,
            memory_id=uuid.UUID(memory_id),
            rolled_back_from=current_version,
            rolled_back_to=version_number,
            message=f"成功从版本 {current_version} 回滚到版本 {version_number}"
        )
    
    async def compare_versions(
        self,
        memory_id: str,
        version1: int,
        version2: int,
        table_name: str = 'private_memories'
    ) -> VersionCompareResponse:
        """
        比较两个版本的差异
        
        Args:
            memory_id: 记忆 ID
            version1: 版本号 1
            version2: 版本号 2
            table_name: 表名
        
        Returns:
            VersionCompareResponse: 版本比较结果
        """
        # 获取两个版本
        v1 = await self.get_version(memory_id, version1, table_name)
        v2 = await self.get_version(memory_id, version2, table_name)
        
        # 计算差异
        diffs = []
        
        # 比较内容
        if v1.content != v2.content:
            diffs.append(VersionDiff(
                field='content',
                old_value=v1.content,
                new_value=v2.content,
                change_type='modified'
            ))
        
        # 比较类型
        if v1.memory_type != v2.memory_type:
            diffs.append(VersionDiff(
                field='memory_type',
                old_value=v1.memory_type,
                new_value=v2.memory_type,
                change_type='modified'
            ))
        
        # 比较重要性
        if v1.importance != v2.importance:
            diffs.append(VersionDiff(
                field='importance',
                old_value=v1.importance,
                new_value=v2.importance,
                change_type='modified'
            ))
        
        # 比较标签
        tags1 = set(v1.tags)
        tags2 = set(v2.tags)
        if tags1 != tags2:
            added_tags = list(tags2 - tags1)
            removed_tags = list(tags1 - tags2)
            
            if added_tags:
                diffs.append(VersionDiff(
                    field='tags_added',
                    old_value=None,
                    new_value=added_tags,
                    change_type='added'
                ))
            if removed_tags:
                diffs.append(VersionDiff(
                    field='tags_removed',
                    old_value=removed_tags,
                    new_value=None,
                    change_type='removed'
                ))
        
        # 计算内容相似度（简单实现：基于字符重叠）
        similarity = self._calculate_similarity(v1.content, v2.content)
        
        return VersionCompareResponse(
            memory_id=uuid.UUID(memory_id),
            version1=v1,
            version2=v2,
            diffs=diffs,
            similarity_score=similarity
        )
    
    async def update_memory_with_version(
        self,
        memory_id: str,
        updates: Dict[str, Any],
        change_reason: Optional[str] = None,
        changed_by: Optional[str] = None,
        table_name: str = 'private_memories'
    ) -> Dict[str, Any]:
        """
        更新记忆（自动保存历史版本）
        
        Args:
            memory_id: 记忆 ID
            updates: 更新字段
            change_reason: 修改原因
            changed_by: 修改者 ID
            table_name: 表名
        
        Returns:
            更新后的记忆
        """
        # 添加版本控制字段
        if changed_by:
            updates['changed_by_agent'] = uuid.UUID(changed_by)
        
        # 构建更新 SQL
        set_clauses = []
        params = []
        param_idx = 1
        
        for key, value in updates.items():
            if key in ['content', 'memory_type', 'importance', 'tags', 'metadata', 'embedding', 'changed_by_agent']:
                if key == 'embedding' and value:
                    set_clauses.append(f"{key} = ${param_idx}::vector")
                    params.append(f"[{','.join(map(str, value))}]")
                elif key == 'tags':
                    set_clauses.append(f"{key} = ${param_idx}")
                    params.append(value)
                elif key == 'metadata':
                    set_clauses.append(f"{key} = ${param_idx}::jsonb")
                    params.append(json.dumps(value))
                else:
                    set_clauses.append(f"{key} = ${param_idx}")
                    params.append(value)
                param_idx += 1
        
        if not set_clauses:
            raise ValueError("没有有效的更新字段")
        
        # 添加 change_reason 到版本表（需要在触发器之后单独处理）
        # 这里暂时简化处理，后续可以通过应用层逻辑优化
        
        query = f"""
            UPDATE {table_name}
            SET {', '.join(set_clauses)},
                last_accessed = CURRENT_TIMESTAMP
            WHERE id = ${param_idx}
            RETURNING *
        """
        params.append(uuid.UUID(memory_id))
        
        row = await db.fetchrow(query, *params)
        
        if not row:
            raise ValueError(f"记忆不存在：{memory_id}")
        
        logger.info(f"记忆更新成功（版本控制）：{memory_id}")
        
        return dict(row)
    
    async def _get_memory(self, memory_id: str, table_name: str) -> Optional[Dict]:
        """获取记忆详情"""
        query = f"SELECT * FROM {table_name} WHERE id = $1"
        row = await db.fetchrow(query, uuid.UUID(memory_id))
        return dict(row) if row else None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度（简单实现）
        
        使用字符级 Jaccard 相似度
        """
        if not text1 or not text2:
            return 0.0
        
        set1 = set(text1)
        set2 = set(text2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0


# 单例实例
version_service = VersionService()