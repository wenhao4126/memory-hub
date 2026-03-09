from fastapi import APIRouter, HTTPException
import uuid
from backend.app.services.memory_classifier import memory_classifier, MemoryVisibility

router = APIRouter()

# 模拟的数据结构和函数，实际实现可能不同
class MemoryCreate:
    def __init__(self):
        self.agent_id = None
        self.content = None
        self.memory_type = None
        self.visibility = None
        self.classification_reason = None
        self.classification_confidence = None

class MessageResponse:
    def __init__(self, message, data):
        self.message = message
        self.data = data

async def get_agent_by_id(agent_id):
    # 模拟获取智能体信息
    class Agent:
        def __init__(self, name):
            self.name = name
    return Agent("小码")

async def memory_service_create_memory(memory):
    # 模拟创建记忆
    return str(uuid.uuid4())

async def memory_service_list_memories_by_agent(agent_id, visibility, limit, offset):
    # 模拟查询记忆
    return []

logger = type('Logger', (), {'info': lambda s, msg: print(msg), 'error': lambda s, msg: print(msg)})()

@router.post("/memories")
async def create_memory(memory: MemoryCreate, auto_classify: bool = True):
    """
    创建记忆（支持自动分类）
    
    - **agent_id**: 智能体 ID
    - **content**: 记忆内容
    - **memory_type**: 记忆类型
    - **auto_classify**: 是否自动分类（默认 true）
    - **visibility**: 可见性（如果 auto_classify=false，需要手动指定）
    """
    try:
        # 1. 自动分类（如果启用）
        if auto_classify and not memory.visibility:
            # 获取智能体信息
            agent = await get_agent_by_id(memory.agent_id)
            
            # 调用分类器
            visibility, confidence, reason = memory_classifier.classify(
                content=memory.content,
                agent_name=agent.name,
                memory_type=memory.memory_type
            )
            
            memory.visibility = visibility.value
            memory.classification_reason = reason
            memory.classification_confidence = confidence
            
            logger.info(f"自动分类结果：{visibility.value} (置信度：{confidence:.2f}, 理由：{reason})")
        
        # 2. 验证可见性
        if not memory.visibility:
            memory.visibility = "private"  # 默认私人
        
        # 3. 保存到数据库
        memory_id = await memory_service_create_memory(memory)
        
        return MessageResponse(
            message=f"记忆创建成功",
            data={
                "memory_id": memory_id,
                "visibility": memory.visibility,
                "auto_classified": auto_classify
            }
        )
    
    except Exception as e:
        logger.error(f"创建记忆失败：{e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@router.get("/agents/{agent_id}/memories")
async def list_agent_memories(
    agent_id: str,
    visibility: str = "all",  # all/private/shared
    limit: int = 50,
    offset: int = 0
):
    """
    列出智能体的记忆（支持按可见性过滤）
    
    - **agent_id**: 智能体 ID
    - **visibility**: 可见性过滤（all/private/shared）
    - **limit**: 返回数量
    - **offset**: 偏移量
    """
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的智能体 ID")
    
    # 查询记忆
    memories = await memory_service_list_memories_by_agent(
        agent_id=agent_uuid,
        visibility=visibility,
        limit=limit,
        offset=offset
    )
    
    return {
        "total": len(memories),
        "limit": limit,
        "offset": offset,
        "memories": memories
    }