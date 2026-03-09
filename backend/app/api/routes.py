from fastapi import APIRouter, HTTPException
import uuid
import logging

from ..services.memory_router import memory_router
from ..services.embedding_service import embedding_service
from ..services.agent_service import get_agent_by_id

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/memories")
async def create_memory(
    agent_id: str,
    content: str,
    memory_type: str = "fact",
    auto_route: bool = True  # 新增参数：是否自动路由
):
    """
    创建记忆（支持自动路由到私人表或共同表）
    
    - **agent_id**: 智能体 ID
    - **content**: 记忆内容
    - **memory_type**: 记忆类型
    - **auto_route**: 是否自动路由（默认 true）
    """
    try:
        agent_uuid = uuid.UUID(agent_id)
        
        # 1. 获取智能体信息
        agent = await get_agent_by_id(agent_uuid)
        
        # 2. 生成向量
        embedding = await embedding_service.get_embedding(content)
        
        # 3. 自动路由
        if auto_route:
            memory_id, table_name, visibility = await memory_router.save(
                db=db,
                content=content,
                agent_id=agent_uuid,
                memory_type=memory_type,
                agent_name=agent.name,
                embedding=embedding
            )
            
            return {
                "memory_id": str(memory_id),
                "table": table_name,
                "visibility": visibility,
                "auto_routed": True
            }
        else:
            # 手动指定表（向后兼容）
            # ... 原有逻辑
            pass
    
    except Exception as e:
        logger.error(f"创建记忆失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))