# ============================================================
# 多智能体并行任务系统 - Worker 模块
# ============================================================
# 作者：小码 🟡
# 日期：2026-03-16
# 更新：2026-03-17 - 添加所有手下的 Worker 类
# ============================================================

from .agent_worker import AgentWorker, WorkerPool, SimpleWorker

# 各手下的 Worker 类
from .researcher_worker import ResearcherWorker, ResearcherPool
from .writer_worker import WriterWorker, WriterPool
from .reviewer_worker import ReviewerWorker, ReviewerPool
from .analyst_worker import AnalystWorker, AnalystPool
from .browser_worker import BrowserWorker, BrowserPool
from .designer_worker import DesignerWorker, DesignerPool
from .layout_worker import LayoutWorker, LayoutPool

__all__ = [
    # 基类
    'AgentWorker',
    'WorkerPool',
    'SimpleWorker',
    
    # 小搜 - 信息采集
    'ResearcherWorker',
    'ResearcherPool',
    
    # 小写 - 文案撰写
    'WriterWorker',
    'WriterPool',
    
    # 小审 - 质量审核
    'ReviewerWorker',
    'ReviewerPool',
    
    # 小析 - 数据分析
    'AnalystWorker',
    'AnalystPool',
    
    # 小览 - 浏览器操作
    'BrowserWorker',
    'BrowserPool',
    
    # 小图 - 视觉设计
    'DesignerWorker',
    'DesignerPool',
    
    # 小排 - 内容排版
    'LayoutWorker',
    'LayoutPool',
]

__version__ = '1.1.0'