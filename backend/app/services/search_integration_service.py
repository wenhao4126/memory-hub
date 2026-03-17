# ============================================================
# 多智能体记忆中枢 - 搜索集成服务
# ============================================================
# 功能：集成搜索结果到知识库（保存 .md 文件 + 存入 knowledge 表）
# 作者：小码 🟡
# 日期：2026-03-16
#
# ⚠️ 架构说明（憨货决策）：
#   小搜搜索到的文档处理流程：
#   1. 抓取文档内容
#   2. 保存为 .md 文件
#   3. 读取 .md 文件内容
#   4. 存入 knowledge 表（内容 + 文件路径）
#   5. 创建 shared_memory（引用 knowledge_id）
#
# 优势：
#   - 有文件备份，方便查看
#   - 防止链接失效后内容丢失
#   - knowledge 表记录文件路径，可追溯
# ============================================================

import logging
import uuid
from typing import List, Dict, Any, Optional

from .document_storage_service import document_storage_service
from .knowledge_service import knowledge_service
from .memory_service import memory_service
from ..models.schemas import MemoryCreate, MemoryType

logger = logging.getLogger(__name__)


class SearchIntegrationService:
    """
    搜索集成服务 - 将搜索结果保存到知识库
    
    功能：
        - process_search_results(): 处理搜索结果，保存到 .md 文件和 knowledge 表
        - fetch_document_content(): 抓取文档内容（从 URL）
    
    使用场景：
        小搜搜索完成 → 调用 process_search_results() → 结果保存到知识库
    """
    
    async def process_search_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
        source: str = "小搜",
        agent_id: uuid.UUID = None
    ) -> List[Dict[str, Any]]:
        """
        处理搜索结果
        
        将搜索结果保存为 .md 文件，然后存入 knowledge 表。
        
        Args:
            results: 搜索结果列表，每个结果包含 title, url, snippet
            query: 搜索查询词
            source: 来源标识（默认"小搜"）
            agent_id: 智能体 ID（可选，用于 shared_memory）
        
        Returns:
            processed: 处理后的结果列表，包含 knowledge_id 和 file_path
        
        示例：
            results = [
                {"title": "Python教程", "url": "https://...", "snippet": "..."},
                ...
            ]
            
            processed = await search_integration.process_search_results(
                results=results,
                query="Python教程",
                source="小搜"
            )
            
            # processed[0] 包含：
            # {
            #   "title": "Python教程",
            #   "url": "...",
            #   "knowledge_id": "uuid",
            #   "file_path": "/home/wen/.../documents/xxx.md"
            # }
        """
        logger.info(f"处理搜索结果：{len(results)} 条，查询词：{query}")
        
        processed_results = []
        
        for idx, result in enumerate(results):
            try:
                logger.info(f"处理第 {idx + 1} 条：{result.get('title', 'unknown')[:50]}")
                
                # ============================================================
                # 步骤 1：抓取文档内容
                # ============================================================
                content = await self.fetch_document_content(result.get('url'))
                
                if not content:
                    # 如果抓取失败，使用 snippet 作为内容
                    content = result.get('snippet', '无法获取内容')
                    logger.warning(f"抓取内容失败，使用 snippet：{result.get('url')}")
                
                # ============================================================
                # 步骤 2：保存为 .md 文件
                # ============================================================
                file_path = await document_storage_service.save_document(
                    title=result.get('title', '未知标题'),
                    content=content,
                    source=source,
                    url=result.get('url'),
                    metadata={
                        'search_query': query,
                        'snippet': result.get('snippet', '')[:500]  # 保存 snippet 摘要
                    }
                )
                
                logger.info(f"文档已保存：{file_path}")
                
                # ============================================================
                # 步骤 3：读取 .md 文件内容
                # ============================================================
                file_content = document_storage_service.read_document(file_path)
                
                # ============================================================
                # 步骤 4：存入 knowledge 表
                # ============================================================
                knowledge_id = await knowledge_service.create(
                    title=result.get('title', '未知标题'),
                    content=file_content,  # 读取文件内容
                    source=source,
                    url=result.get('url'),
                    category="search_result",  # 分类为搜索结果
                    tags=[query],  # 搜索词作为标签
                    file_path=file_path,  # ← 保存文件路径到专门字段
                    metadata={
                        'file_path': file_path,  # 同时保存到 metadata
                        'search_query': query,
                        'original_snippet': result.get('snippet', '')[:500]
                    }
                )
                
                logger.info(f"知识记录已创建：{knowledge_id}")
                
                # ============================================================
                # 步骤 5：创建 shared_memory（引用）
                # 可选：如果有 agent_id，创建记忆引用
                # ============================================================
                memory_id = None
                if agent_id:
                    try:
                        # 创建 MemoryCreate 对象
                        memory_create = MemoryCreate(
                            agent_id=agent_id,
                            content=f"找到文档：{result.get('title', '未知标题')}",
                            memory_type=MemoryType.FACT,
                            importance=0.7,  # 文档引用重要性较高
                            metadata={
                                'memory_category': 'document',  # ← 关键！用于文档记忆 API 查询
                                'knowledge_id': str(knowledge_id),
                                'file_path': file_path,
                                'source': source,
                                'doc_url': result.get('url'),
                                'doc_title': result.get('title'),
                                'search_query': query
                            },
                            auto_route=False,
                            visibility='shared'  # 文档引用作为共享记忆
                        )
                        
                        memory_id, table_name, visibility, auto_routed = await memory_service.create_memory(memory_create)
                        logger.info(f"记忆引用已创建：{memory_id}，表：{table_name}")
                    except Exception as e:
                        logger.warning(f"创建记忆引用失败：{e}")
                
                # ============================================================
                # 记录处理结果
                # ============================================================
                processed_results.append({
                    'title': result.get('title'),
                    'url': result.get('url'),
                    'snippet': result.get('snippet'),
                    'knowledge_id': str(knowledge_id),
                    'file_path': file_path,
                    'memory_id': str(memory_id) if memory_id else None,
                    'status': 'success'
                })
            
            except Exception as e:
                logger.error(f"处理搜索结果失败：{result.get('title')}, 错误={e}", exc_info=True)
                
                processed_results.append({
                    'title': result.get('title'),
                    'url': result.get('url'),
                    'snippet': result.get('snippet'),
                    'knowledge_id': None,
                    'file_path': None,
                    'memory_id': None,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # ============================================================
        # 统计处理结果
        # ============================================================
        success_count = sum(1 for r in processed_results if r['status'] == 'success')
        failed_count = len(processed_results) - success_count
        
        logger.info(f"搜索结果处理完成：成功 {success_count} 条，失败 {failed_count} 条")
        
        return processed_results
    
    async def fetch_document_content(self, url: str) -> Optional[str]:
        """
        抓取文档内容
        
        从 URL 抓取网页内容，提取正文文本。
        
        Args:
            url: 文档 URL
        
        Returns:
            content: 文档内容（提取后的正文）
            如果抓取失败返回 None
        
        注意：
            此方法目前使用简单的 requests + 正则提取，
            后续可以集成更强大的抓取工具（如 agent-reach）
        """
        if not url:
            return None
        
        logger.info(f"抓取文档内容：{url}")
        
        try:
            # 使用 httpx 或 requests 抓取
            import httpx
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
            
            html = response.text
            
            # 简单提取正文（移除 HTML 标签）
            import re
            
            # 移除 script 和 style 标签
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            
            # 移除所有 HTML 标签
            text = re.sub(r'<[^>]+>', ' ', html)
            
            # 清理空白字符
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            # 截取前 10000 字符（避免过长）
            if len(text) > 10000:
                text = text[:10000] + "\n\n... (内容已截断)"
            
            logger.info(f"抓取成功，内容长度：{len(text)}")
            
            return text
        
        except Exception as e:
            logger.warning(f"抓取文档内容失败：{url}, 错误={e}")
            return None


# 全局服务实例
search_integration_service = SearchIntegrationService()