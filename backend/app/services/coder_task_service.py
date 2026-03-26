# ============================================================
# Memory Hub - 小码任务服务
# ============================================================
# 功能：管理小码任务的创建、更新、完成等操作
# 作者：小码 1 号 🟡
# 日期：2026-03-24
# 版本：v1.0
# ============================================================

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID, uuid4

from ..database import db

logger = logging.getLogger(__name__)


class CoderTaskService:
    """小码任务服务类"""
    
    async def create_coder_task(
        self,
        title: str,
        coder_id: Optional[UUID] = None,
        coder_name: Optional[str] = None,
        task_id: Optional[str] = None,
        task_type: Optional[str] = None,
        description: Optional[str] = None,
        project_path: Optional[str] = None,
        priority: str = '中',
        memory_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        创建小码任务
        
        Args:
            title: 任务标题
            coder_id: 小码智能体 ID
            coder_name: 小码名称（小码 1 号/小码 2 号/小码 3 号）
            task_id: 飞书任务 ID
            task_type: 任务类型（search/write/code/review/analyze）
            description: 任务描述
            project_path: 项目路径
            priority: 优先级（高/中/低）
            memory_id: 关联的记忆 ID
            
        Returns:
            创建的任务信息
        """
        try:
            task_uuid = uuid4()
            now = datetime.now(timezone.utc)
            
            query = """
                INSERT INTO coder_tasks (
                    id, task_id, coder_id, coder_name, task_type, title,
                    description, project_path, status, priority, progress,
                    memory_id, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                )
                RETURNING *
            """
            
            row = await db.fetchrow(
                query,
                task_uuid,
                task_id,
                coder_id,
                coder_name,
                task_type,
                title,
                description,
                project_path,
                'pending',
                priority,
                0,
                memory_id,
                now,
                now
            )
            
            logger.info(f"✅ 创建小码任务：{title} (ID: {task_uuid})")
            
            return self._row_to_dict(row)
        except Exception as e:
            logger.error(f"❌ 创建小码任务失败：{e}")
            raise
    
    async def update_coder_task(
        self,
        task_id: UUID,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        progress_message: Optional[str] = None,
        start_time: Optional[datetime] = None,
        result: Optional[str] = None,
        complete_time: Optional[datetime] = None,
        duration_seconds: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        更新小码任务
        
        Args:
            task_id: 任务 ID
            status: 状态（pending/running/completed/failed）
            progress: 进度（0-100）
            progress_message: 进度描述
            start_time: 开始时间
            result: 任务结果
            complete_time: 完成时间
            duration_seconds: 耗时（秒）
            error_message: 错误信息
            
        Returns:
            更新后的任务信息
        """
        try:
            # 构建动态更新语句
            updates = []
            values = [task_id]
            param_index = 1
            
            if status is not None:
                param_index += 1
                updates.append(f"status = ${param_index}")
                values.append(status)
            
            if progress is not None:
                param_index += 1
                updates.append(f"progress = ${param_index}")
                values.append(progress)
            
            if progress_message is not None:
                param_index += 1
                updates.append(f"progress_message = ${param_index}")
                values.append(progress_message)
            
            if start_time is not None:
                param_index += 1
                updates.append(f"start_time = ${param_index}")
                values.append(start_time)
            
            if result is not None:
                param_index += 1
                updates.append(f"result = ${param_index}")
                values.append(result)
            
            if complete_time is not None:
                param_index += 1
                updates.append(f"complete_time = ${param_index}")
                values.append(complete_time)
            
            if duration_seconds is not None:
                param_index += 1
                updates.append(f"duration_seconds = ${param_index}")
                values.append(duration_seconds)
            
            if error_message is not None:
                param_index += 1
                updates.append(f"error_message = ${param_index}")
                values.append(error_message)
            
            # 添加 updated_at
            param_index += 1
            updates.append(f"updated_at = ${param_index}")
            values.append(datetime.now(timezone.utc))
            
            if not updates:
                raise ValueError("至少需要一个更新字段")
            
            query = f"""
                UPDATE coder_tasks
                SET {', '.join(updates)}
                WHERE id = $1
                RETURNING *
            """
            
            row = await db.fetchrow(query, *values)
            
            if row is None:
                raise ValueError(f"任务不存在：{task_id}")
            
            logger.info(f"✅ 更新小码任务：{row['title']} (ID: {task_id})")
            
            return self._row_to_dict(row)
        except Exception as e:
            logger.error(f"❌ 更新小码任务失败：{e}")
            raise
    
    async def complete_coder_task(
        self,
        task_id: UUID,
        result: str,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        完成小码任务
        
        Args:
            task_id: 任务 ID
            result: 任务结果
            error_message: 错误信息（如果有）
            
        Returns:
            完成后的任务信息
        """
        try:
            now = datetime.now(timezone.utc)
            
            # 计算耗时
            query_get_start = "SELECT start_time, created_at FROM coder_tasks WHERE id = $1"
            start_row = await db.fetchrow(query_get_start, task_id)
            
            duration_seconds = None
            if start_row and start_row['start_time']:
                duration_seconds = int((now - start_row['start_time']).total_seconds())
            elif start_row and start_row['created_at']:
                duration_seconds = int((now - start_row['created_at']).total_seconds())
            
            status = 'completed' if error_message is None else 'failed'
            
            query = """
                UPDATE coder_tasks
                SET 
                    status = $2,
                    result = $3,
                    error_message = $4,
                    complete_time = $5,
                    duration_seconds = $6,
                    updated_at = $7
                WHERE id = $1
                RETURNING *
            """
            
            row = await db.fetchrow(
                query,
                task_id,
                status,
                result,
                error_message,
                now,
                duration_seconds,
                now
            )
            
            if row is None:
                raise ValueError(f"任务不存在：{task_id}")
            
            logger.info(f"✅ 完成小码任务：{row['title']} (ID: {task_id}, 状态：{status})")
            
            return self._row_to_dict(row)
        except Exception as e:
            logger.error(f"❌ 完成小码任务失败：{e}")
            raise
    
    async def get_task_by_id(self, task_id: UUID) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务信息，不存在则返回 None
        """
        try:
            query = "SELECT * FROM coder_tasks WHERE id = $1"
            row = await db.fetchrow(query, task_id)
            
            if row is None:
                return None
            
            return self._row_to_dict(row)
        except Exception as e:
            logger.error(f"❌ 获取任务失败：{e}")
            raise
    
    async def get_tasks_by_coder_name(
        self,
        coder_name: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        根据小码名称获取任务列表
        
        Args:
            coder_name: 小码名称
            status: 状态过滤（可选）
            limit: 返回数量限制
            
        Returns:
            任务列表
        """
        try:
            if status:
                query = """
                    SELECT * FROM coder_tasks
                    WHERE coder_name = $1 AND status = $2
                    ORDER BY created_at DESC
                    LIMIT $3
                """
                rows = await db.fetch(query, coder_name, status, limit)
            else:
                query = """
                    SELECT * FROM coder_tasks
                    WHERE coder_name = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """
                rows = await db.fetch(query, coder_name, limit)
            
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ 获取任务列表失败：{e}")
            raise
    
    async def get_tasks_by_status(
        self,
        status: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        根据状态获取任务列表
        
        Args:
            status: 状态
            limit: 返回数量限制
            
        Returns:
            任务列表
        """
        try:
            query = """
                SELECT * FROM coder_tasks
                WHERE status = $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            rows = await db.fetch(query, status, limit)
            
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ 获取任务列表失败：{e}")
            raise
    
    async def get_pending_tasks(
        self,
        coder_name: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取待执行的任务
        
        Args:
            coder_name: 小码名称（可选）
            limit: 返回数量限制
            
        Returns:
            待执行任务列表
        """
        try:
            if coder_name:
                query = """
                    SELECT * FROM coder_tasks
                    WHERE status = 'pending' AND coder_name = $1
                    ORDER BY 
                        CASE priority
                            WHEN '高' THEN 1
                            WHEN '中' THEN 2
                            WHEN '低' THEN 3
                            ELSE 4
                        END,
                        created_at ASC
                    LIMIT $2
                """
                rows = await db.fetch(query, coder_name, limit)
            else:
                query = """
                    SELECT * FROM coder_tasks
                    WHERE status = 'pending'
                    ORDER BY 
                        CASE priority
                            WHEN '高' THEN 1
                            WHEN '中' THEN 2
                            WHEN '低' THEN 3
                            ELSE 4
                        END,
                        created_at ASC
                    LIMIT $1
                """
                rows = await db.fetch(query, limit)
            
            return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ 获取待执行任务失败：{e}")
            raise
    
    async def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 按状态统计
            query_status = """
                SELECT status, COUNT(*) as count
                FROM coder_tasks
                GROUP BY status
            """
            status_rows = await db.fetch(query_status)
            
            # 按小码统计
            query_coder = """
                SELECT coder_name, COUNT(*) as count
                FROM coder_tasks
                WHERE coder_name IS NOT NULL
                GROUP BY coder_name
            """
            coder_rows = await db.fetch(query_coder)
            
            # 平均耗时
            query_avg_duration = """
                SELECT AVG(duration_seconds) as avg_duration
                FROM coder_tasks
                WHERE status = 'completed' AND duration_seconds IS NOT NULL
            """
            avg_row = await db.fetchrow(query_avg_duration)
            
            # 最近创建的任务数（24 小时内）
            query_recent = """
                SELECT COUNT(*) as count
                FROM coder_tasks
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """
            recent_row = await db.fetchrow(query_recent)
            
            return {
                'by_status': {row['status']: row['count'] for row in status_rows},
                'by_coder': {row['coder_name']: row['count'] for row in coder_rows},
                'avg_duration_seconds': float(avg_row['avg_duration']) if avg_row['avg_duration'] else None,
                'recent_24h_count': recent_row['count'],
            }
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败：{e}")
            raise
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        if row is None:
            return {}
        
        return {
            'id': str(row['id']),
            'task_id': row['task_id'],
            'coder_id': str(row['coder_id']) if row['coder_id'] else None,
            'coder_name': row['coder_name'],
            'task_type': row['task_type'],
            'title': row['title'],
            'description': row['description'],
            'project_path': row['project_path'],
            'status': row['status'],
            'priority': row['priority'],
            'progress': row['progress'],
            'progress_message': row['progress_message'],
            'result': row['result'],
            'error_message': row['error_message'],
            'start_time': row['start_time'],
            'complete_time': row['complete_time'],
            'duration_seconds': row['duration_seconds'],
            'memory_id': str(row['memory_id']) if row['memory_id'] else None,
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
        }


# 全局服务实例
coder_task_service = CoderTaskService()
