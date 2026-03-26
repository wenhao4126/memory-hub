# ============================================================
# Memory Hub - 小码任务 API 路由
# ============================================================
# 功能：提供小码任务的查询和创建 API 接口
# 作者：小码 1 号 🟡
# 日期：2026-03-24
# 版本：v1.0
# ============================================================

from fastapi import APIRouter, HTTPException, status, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import uuid

from ..services.coder_task_service import coder_task_service
from ..database import db
from ..auth import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])
logger = logging.getLogger(__name__)


# ============================================================
# 请求/响应模型
# ============================================================

class CoderTaskCreateRequest(BaseModel):
    """创建小码任务请求"""
    coder_id: str = Field(..., description="小码智能体 ID")
    coder_name: str = Field(..., description="小码名称（小码 1 号/小码 2 号/小码 3 号）")
    task_id: Optional[str] = Field(None, description="飞书任务 ID")
    task_type: Optional[str] = Field(None, description="任务类型（search/write/code/review/analyze）")
    title: str = Field(..., description="任务标题")
    project_path: Optional[str] = Field(None, description="项目路径")
    status: str = Field(default="completed", description="任务状态（pending/running/completed/failed）")
    result: Optional[str] = Field(None, description="任务完成结果")
    duration_seconds: Optional[int] = Field(None, description="任务耗时（秒）")
    description: Optional[str] = Field(None, description="任务描述")
    priority: str = Field(default="中", description="优先级（高/中/低）")


class CoderTaskResponse(BaseModel):
    """小码任务响应"""
    id: str
    task_id: Optional[str]
    coder_id: Optional[str]
    coder_name: str
    task_type: Optional[str]
    title: str
    description: Optional[str]
    project_path: Optional[str]
    status: str
    priority: str
    progress: int
    progress_message: Optional[str]
    result: Optional[str]
    error_message: Optional[str]
    start_time: Optional[str]
    complete_time: Optional[str]
    duration_seconds: Optional[int]
    memory_id: Optional[str]
    created_at: str
    updated_at: str


class CoderTaskListResponse(BaseModel):
    """小码任务列表响应"""
    total: int
    tasks: List[Dict[str, Any]]


class CoderTaskCreateResponse(BaseModel):
    """创建小码任务响应"""
    id: str
    status: str
    message: str


class CoderTaskUpdateRequest(BaseModel):
    """更新小码任务请求"""
    status: Optional[str] = Field(None, description="任务状态（pending/running/completed/failed）")
    result: Optional[str] = Field(None, description="任务完成结果")
    complete_time: Optional[str] = Field(None, description="完成时间")
    duration_seconds: Optional[int] = Field(None, description="任务耗时（秒）")
    progress: Optional[int] = Field(None, description="进度（0-100）")
    progress_message: Optional[str] = Field(None, description="进度消息")
    error_message: Optional[str] = Field(None, description="错误消息")


# ============================================================
# API 路由
# ============================================================

@router.get(
    "/coder-tasks",
    response_model=CoderTaskListResponse,
    tags=["小码任务"],
    summary="查询小码任务列表",
    description="""
    查询小码任务列表，支持多种过滤条件
    
    **查询参数**:
    - **coder_id**: 按小码 ID 过滤（可选）
    - **coder_name**: 按小码名称过滤（可选）
    - **status**: 按状态过滤（可选）
    - **limit**: 返回数量限制（默认 50）
    - **offset**: 偏移量（默认 0）
    
    **返回**:
    - **total**: 总记录数
    - **tasks**: 任务列表
    """,
    responses={
        200: {"description": "成功返回任务列表"},
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_coder_tasks(
    coder_id: Optional[str] = Query(None, description="小码 ID"),
    coder_name: Optional[str] = Query(None, description="小码名称"),
    status: Optional[str] = Query(None, description="任务状态"),
    limit: int = Query(50, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """
    查询小码任务列表
    
    支持按小码 ID、小码名称、状态等条件过滤
    """
    try:
        # 构建查询条件
        conditions = []
        values = []
        param_index = 0
        
        if coder_id:
            param_index += 1
            conditions.append(f"coder_id = ${param_index}")
            values.append(coder_id)
        
        if coder_name:
            param_index += 1
            conditions.append(f"coder_name = ${param_index}")
            values.append(coder_name)
        
        if status:
            param_index += 1
            conditions.append(f"status = ${param_index}")
            values.append(status)
        
        # 构建 WHERE 子句
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # 查询总数
        count_query = f"SELECT COUNT(*) FROM coder_tasks {where_clause}"
        total_row = await db.fetchrow(count_query, *values)
        total = total_row['count'] if total_row else 0
        
        # 查询数据（带分页）
        param_index += 1
        limit_param_index = param_index
        param_index += 1
        offset_param_index = param_index
        
        query = f"""
            SELECT * FROM coder_tasks
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${limit_param_index} OFFSET ${offset_param_index}
        """
        
        query_values = values + [limit, offset]
        rows = await db.fetch(query, *query_values)
        
        # 转换为字典列表
        tasks = []
        for row in rows:
            task = {
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
            tasks.append(task)
        
        logger.info(f"✅ 查询小码任务列表：{len(tasks)} 条记录 (total: {total}, limit: {limit}, offset: {offset})")
        
        return CoderTaskListResponse(total=total, tasks=tasks)
    
    except Exception as e:
        logger.error(f"❌ 查询小码任务列表失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询任务列表失败：{str(e)}"
        )


@router.post(
    "/coder-tasks",
    response_model=CoderTaskCreateResponse,
    tags=["小码任务"],
    summary="创建小码任务记录",
    description="""
    创建或完成小码任务记录
    
    **请求体**:
    - **coder_id**: 小码智能体 ID（必填）
    - **coder_name**: 小码名称（必填）
    - **task_id**: 飞书任务 ID（可选）
    - **task_type**: 任务类型（可选）
    - **title**: 任务标题（必填）
    - **project_path**: 项目路径（可选）
    - **status**: 任务状态（默认 completed）
    - **result**: 任务完成结果（可选）
    - **duration_seconds**: 任务耗时（可选）
    - **description**: 任务描述（可选）
    - **priority**: 优先级（默认 中）
    
    **返回**:
    - **id**: 生成的任务 UUID
    - **status**: 创建状态
    - **message**: 提示信息
    """,
    responses={
        200: {"description": "成功创建任务"},
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)
async def create_coder_task(request: CoderTaskCreateRequest):
    """
    创建小码任务记录
    
    支持创建新任务或直接记录已完成的任务
    """
    try:
        # 使用 Service 层创建任务
        task_data = await coder_task_service.create_coder_task(
            title=request.title,
            coder_id=uuid.UUID(request.coder_id) if request.coder_id else None,
            coder_name=request.coder_name,
            task_id=request.task_id,
            task_type=request.task_type,
            description=request.description,
            project_path=request.project_path,
            priority=request.priority,
        )
        
        task_uuid = task_data['id']
        
        # 如果状态不是 pending，需要更新状态
        if request.status != 'pending':
            # 如果提供了耗时，直接完成
            if request.status in ['completed', 'failed']:
                await coder_task_service.complete_coder_task(
                    task_id=uuid.UUID(task_uuid),
                    result=request.result or '',
                    error_message=request.result if request.status == 'failed' else None,
                )
                logger.info(f"✅ 创建并完成任务：{request.title} (ID: {task_uuid})")
            else:
                # 其他状态（如 running）
                from datetime import datetime
                await coder_task_service.update_coder_task(
                    task_id=uuid.UUID(task_uuid),
                    status=request.status,
                )
                logger.info(f"✅ 创建并更新任务状态：{request.title} (ID: {task_uuid}, status: {request.status})")
        else:
            logger.info(f"✅ 创建小码任务：{request.title} (ID: {task_uuid})")
        
        return CoderTaskCreateResponse(
            id=task_uuid,
            status="created",
            message="任务记录已创建"
        )
    
    except ValueError as e:
        logger.error(f"❌ 请求参数错误：{e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"请求参数错误：{str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ 创建小码任务失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败：{str(e)}"
        )


@router.get(
    "/coder-tasks/{task_id}",
    response_model=Dict[str, Any],
    tags=["小码任务"],
    summary="获取单个任务详情",
    description="根据任务 ID 获取详细信息",
    responses={
        200: {"description": "成功返回任务详情"},
        404: {"description": "任务不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_coder_task(task_id: str):
    """获取单个任务详情"""
    try:
        task = await coder_task_service.get_task_by_id(uuid.UUID(task_id))
        
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在：{task_id}"
            )
        
        logger.info(f"✅ 获取任务详情：{task['title']} (ID: {task_id})")
        return task
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取任务详情失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务失败：{str(e)}"
        )


@router.put(
    "/coder-tasks/{task_id}",
    response_model=Dict[str, Any],
    tags=["小码任务"],
    summary="更新小码任务",
    description="""
    更新小码任务状态和结果
    
    **请求体**:
    - **status**: 任务状态（可选）
    - **result**: 任务完成结果（可选）
    - **complete_time**: 完成时间（可选，ISO 8601 格式字符串）
    - **duration_seconds**: 任务耗时（可选）
    - **progress**: 进度 0-100（可选）
    - **progress_message**: 进度消息（可选）
    - **error_message**: 错误消息（可选）
    
    **返回**:
    - **success**: 是否成功
    - **message**: 提示信息
    """,
    responses={
        200: {"description": "成功更新任务"},
        404: {"description": "任务不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def update_coder_task(task_id: str, request: CoderTaskUpdateRequest):
    """更新小码任务"""
    try:
        # 检查任务是否存在
        task = await coder_task_service.get_task_by_id(uuid.UUID(task_id))
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在：{task_id}"
            )
        
        # 构建更新数据
        update_data = {}
        if request.status is not None:
            update_data['status'] = request.status
        if request.result is not None:
            update_data['result'] = request.result
        if request.complete_time is not None:
            # 将 ISO 8601 字符串转换为 datetime
            from datetime import datetime, timezone
            try:
                update_data['complete_time'] = datetime.fromisoformat(request.complete_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的日期格式：{request.complete_time}，请使用 ISO 8601 格式"
                )
        if request.duration_seconds is not None:
            update_data['duration_seconds'] = request.duration_seconds
        if request.progress is not None:
            update_data['progress'] = request.progress
        if request.progress_message is not None:
            update_data['progress_message'] = request.progress_message
        if request.error_message is not None:
            update_data['error_message'] = request.error_message
        
        # 使用 Service 层更新任务
        await coder_task_service.update_coder_task(
            task_id=uuid.UUID(task_id),
            **update_data
        )
        
        logger.info(f"✅ 更新任务：{task['title']} (ID: {task_id})")
        
        return {
            "success": True,
            "message": f"任务已更新：{task['title']}",
            "task_id": task_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 更新任务失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新任务失败：{str(e)}"
        )
