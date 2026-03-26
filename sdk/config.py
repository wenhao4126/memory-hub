# ============================================================
# 多智能体并行任务系统 - 配置管理
# ============================================================
# 功能：从环境变量读取配置
# 作者：小码 🟡
# 日期：2026-03-16
# ============================================================

import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

# 自动加载 .env 文件
from dotenv import load_dotenv

# 尝试从项目根目录加载 .env
_project_root = Path(__file__).parent.parent
_env_file = _project_root / ".env"
if _env_file.exists():
    load_dotenv(_env_file)


@dataclass
class Settings:
    """
    配置类 - 从环境变量读取配置
    
    环境变量：
        DATABASE_URL: 数据库连接字符串
                     格式：postgresql://user:pass@host:port/dbname
        DB_HOST: 数据库主机（默认：localhost）
        DB_PORT: 数据库端口（默认：5432）
        DB_NAME: 数据库名称（默认：memory_hub）
        DB_USER: 数据库用户（默认：memory_user）
        DB_PASSWORD: 数据库密码（默认：memory_pass_2026）
        
        MEMORY_API_URL: 记忆系统 API 地址（默认：http://localhost:8000/api/v1）
    """
    
    # 数据库配置
    DATABASE_URL: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "memory_hub"
    DB_USER: str = "memory_user"
    DB_PASSWORD: str = "memory_pass_2026"
    
    # 记忆系统配置（Phase 3 新增）
    MEMORY_API_URL: str = "http://localhost:8000/api/v1"
    
    # 连接池配置
    DB_POOL_MIN: int = 5
    DB_POOL_MAX: int = 20
    
    # 任务默认配置
    DEFAULT_LOCK_DURATION: int = 30  # 分钟
    DEFAULT_TIMEOUT: int = 30  # 分钟
    DEFAULT_MAX_RETRIES: int = 3
    
    def __post_init__(self):
        """从环境变量加载配置"""
        # 优先使用 DATABASE_URL
        self.DATABASE_URL = os.getenv("DATABASE_URL", "")
        
        # 如果没有 DATABASE_URL，从各个组件构建
        if not self.DATABASE_URL:
            self.DB_HOST = os.getenv("DB_HOST", self.DB_HOST)
            self.DB_PORT = int(os.getenv("DB_PORT", self.DB_PORT))
            self.DB_NAME = os.getenv("DB_NAME", self.DB_NAME)
            self.DB_USER = os.getenv("DB_USER", self.DB_USER)
            self.DB_PASSWORD = os.getenv("DB_PASSWORD", self.DB_PASSWORD)
            
            self.DATABASE_URL = (
                f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        
        # 加载记忆系统配置
        self.MEMORY_API_URL = os.getenv("MEMORY_API_URL", self.MEMORY_API_URL)
        
        # 加载其他配置
        self.DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", self.DB_POOL_MIN))
        self.DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", self.DB_POOL_MAX))
        self.DEFAULT_LOCK_DURATION = int(os.getenv("DEFAULT_LOCK_DURATION", self.DEFAULT_LOCK_DURATION))
        self.DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", self.DEFAULT_TIMEOUT))
        self.DEFAULT_MAX_RETRIES = int(os.getenv("DEFAULT_MAX_RETRIES", self.DEFAULT_MAX_RETRIES))


# 全局配置实例
settings = Settings()


# ============================================================
# 智能体类型配置（2026-03-16 新增）
# ============================================================
# 设计决策：只持久化小码（team-coder）的任务
# 原因：其他智能体（小搜、小写、小审等）都是一次性任务，不需要保存到数据库
# ============================================================

# 智能体名称 -> 智能体类型映射
AGENT_TYPES = {
    'team-coder': 'coder',         # 小码 - 代码开发
    'team-researcher': 'researcher', # 小搜 - 信息采集
    'team-writer': 'writer',       # 小写 - 文案撰写
    'team-reviewer': 'reviewer',   # 小审 - 质量审核
    'team-analyst': 'analyst',     # 小析 - 数据分析
    'team-browser': 'browser',     # 小览 - 浏览器操作
    'team-designer': 'designer',   # 小图 - 视觉设计
    'team-layout': 'layout',       # 小排 - 内容排版
}

# 任务持久化开关
# True: 任务保存到数据库（小码专用）
# False: 任务直接执行，不保存（其他智能体）
PERSISTENCE_ENABLED = {
    'coder': True,       # ✅ 小码 - 需要持久化（跟踪代码任务进度）
    'researcher': False, # ❌ 小搜 - 一次性搜索任务
    'writer': False,     # ❌ 小写 - 一次性写作任务
    'reviewer': False,   # ❌ 小审 - 一次性审核任务
    'analyst': False,    # ❌ 小析 - 一次性分析任务
    'browser': False,    # ❌ 小览 - 一次性浏览器操作
    'designer': False,   # ❌ 小图 - 一次性设计任务
    'layout': False,     # ❌ 小排 - 一次性排版任务
}


def get_database_url() -> str:
    """
    获取数据库连接 URL
    
    Returns:
        数据库连接字符串
    """
    return settings.DATABASE_URL


def get_agent_type(agent_name: str) -> str:
    """
    获取智能体类型
    
    Args:
        agent_name: 智能体名称（如 'team-coder'）
    
    Returns:
        智能体类型（如 'coder'），如果未找到返回 'custom'
    """
    return AGENT_TYPES.get(agent_name, 'custom')


def is_persistence_enabled(agent_type: str) -> bool:
    """
    检查智能体类型是否启用任务持久化
    
    Args:
        agent_type: 智能体类型（如 'coder'）
    
    Returns:
        True: 需要持久化
        False: 不需要持久化
    """
    return PERSISTENCE_ENABLED.get(agent_type, False)