# ============================================================
# 多智能体记忆中枢 - 文档存储服务
# ============================================================
# 功能：将搜索到的文档保存为 .md 文件
# 作者：小码 🟡
# 日期：2026-03-16
#
# ⚠️ 架构说明（憨货决策）：
#   - 小搜搜索到的文档先保存为 .md 文件
#   - 然后读取 .md 文件内容存入 knowledge 表
#   - 优势：有文件备份、方便查看、防止链接失效
#
# 文件存储位置：/home/wen/tools/obsidian/
# 文件命名格式：{中文名字}_{时间戳}.md（2026-03-16 憨货决策）
# ============================================================

import os
import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from .document_naming_service import document_naming_service

logger = logging.getLogger(__name__)


class DocumentStorageService:
    """
    文档存储服务 - 将搜索到的文档保存为 .md 文件
    
    功能：
        - save_document(): 保存文档为 .md 文件，返回文件路径
        - read_document(): 读取 .md 文件内容
        - delete_document(): 删除 .md 文件
    
    使用场景：
        小搜搜索到文档 → 保存为 .md 文件 → 读取内容存 knowledge 表
    """
    
    def __init__(self, storage_dir: str = "/home/wen/tools/obsidian/"):
        """
        初始化文档存储服务
        
        Args:
            storage_dir: 文档存储目录（默认：/home/wen/tools/obsidian/）
        """
        self.storage_dir = storage_dir
        # 确保目录存在
        os.makedirs(storage_dir, exist_ok=True)
        logger.info(f"文档存储服务初始化完成，存储目录：{storage_dir}")
    
    async def save_document(
        self,
        title: str,
        content: str,
        source: str,
        url: str = None,
        metadata: dict = None
    ) -> str:
        """
        保存文档为 .md 文件
        
        将搜索到的文档保存为 Markdown 格式的文件，包含元数据和正文。
        
        文件命名格式（2026-03-16 憨货决策）：
            {中文名字}_{时间戳}.md
            
            示例：
            - Python 快速入门教程_20260316_194800.md
            - Vue.js 组件开发指南_20260316_194801.md
            - Deno 运行时官方文档_20260316_194802.md
        
        Args:
            title: 文档标题（用于生成文件名）
            content: 文档正文内容
            source: 来源（如"小搜"、"小码"）
            url: 原始 URL（可选）
            metadata: 额外元数据（可选）
        
        Returns:
            filepath: 保存的文件路径
        
        Raises:
            ValueError: 参数验证失败
            IOError: 文件写入失败
        
        文件格式：
            # 标题
            
            **来源**: 小搜
            **URL**: https://...
            **时间**: 2026-03-16T14:40:00
            
            ---
            
            正文内容...
        """
        # ============================================================
        # 参数验证
        # ============================================================
        if not title or not title.strip():
            raise ValueError("标题不能为空")
        
        if not content or not content.strip():
            raise ValueError("内容不能为空")
        
        if not source or not source.strip():
            raise ValueError("来源不能为空")
        
        logger.info(f"保存文档：{title[:50]}...")
        
        try:
            # ============================================================
            # 步骤 1：生成中文名字（调用命名服务）
            # 根据文档内容生成有意义的中文名字
            # ============================================================
            chinese_name = await document_naming_service.generate_chinese_name(
                title=title,
                content=content,
                source=source,
                url=url
            )
            
            logger.info(f"生成的中文名字：{chinese_name}")
            
            # ============================================================
            # 步骤 2：生成文件名（中文名字 + 时间戳）
            # 时间戳避免文件名重复
            # ============================================================
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{chinese_name}_{timestamp}.md"
            
            # 二次清理文件名（确保合法）
            safe_filename = self._sanitize_filename(filename)
            filepath = os.path.join(self.storage_dir, safe_filename)
            
            # ============================================================
            # 步骤 3：构建 Markdown 内容
            # 包含：标题、来源、URL、时间、分隔线、正文
            # ============================================================
            markdown_content = self._build_markdown(
                title=title,
                content=content,
                source=source,
                url=url,
                metadata=metadata
            )
            
            # ============================================================
            # 步骤 4：写入文件（同步操作，确保文件写入完成）
            # ============================================================
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"文档保存成功：{filepath}")
            
            return filepath
        
        except Exception as e:
            logger.error(f"保存文档失败：{e}", exc_info=True)
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名中的非法字符（二次保障）
        
        移除或替换文件名中不允许的字符，确保文件名合法。
        注意：命名服务已经做过清理，这里是最后的保障。
        
        Args:
            filename: 文件名（已包含时间戳）
        
        Returns:
            safe_filename: 清理后的文件名
        
        非法字符：
            Windows/Linux 不允许：< > : " / \\ | ? *
            额外处理：保留空格（保持可读性）
        """
        # 定义非法字符（Windows/Linux）
        invalid_chars = '<>:"/\\|？*'
        
        safe_name = filename
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')
        
        # 移除连续空格/下划线
        safe_name = re.sub(r'[\s_]+', ' ', safe_name)
        
        # 截取前 100 字符（避免文件名过长，留时间戳空间）
        if len(safe_name) > 100:
            safe_name = safe_name[:100]
        
        # 移除首尾空格
        safe_name = safe_name.strip()
        
        return safe_name
    
    def _build_markdown(
        self,
        title: str,
        content: str,
        source: str,
        url: str = None,
        metadata: dict = None
    ) -> str:
        """
        构建 Markdown 格式的文档内容
        
        Args:
            title: 文档标题
            content: 正文内容
            source: 来源
            url: 原始 URL
            metadata: 额外元数据
        
        Returns:
            markdown_content: Markdown 格式的完整内容
        """
        lines = []
        
        # 标题
        lines.append(f"# {title}\n")
        
        # 元数据区域
        lines.append(f"**来源**: {source}")
        
        if url:
            lines.append(f"**URL**: {url}")
        
        lines.append(f"**时间**: {datetime.now().isoformat()}")
        
        # 额外元数据
        if metadata:
            for key, value in metadata.items():
                # 跳过已处理的字段
                if key in ['source', 'url', 'time']:
                    continue
                lines.append(f"**{key}**: {value}")
        
        # 分隔线
        lines.append("\n---\n")
        
        # 正文
        lines.append(content)
        
        return '\n'.join(lines)
    
    def read_document(self, filepath: str) -> str:
        """
        读取 .md 文件内容
        
        Args:
            filepath: 文件路径
        
        Returns:
            content: 文件内容
        
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 文件读取失败
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在：{filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"读取文档成功：{filepath}")
            return content
        
        except Exception as e:
            logger.error(f"读取文档失败：{filepath}, 错误={e}")
            raise
    
    def delete_document(self, filepath: str) -> bool:
        """
        删除 .md 文件
        
        Args:
            filepath: 文件路径
        
        Returns:
            success: 是否删除成功
        """
        if not os.path.exists(filepath):
            logger.warning(f"文件不存在，无法删除：{filepath}")
            return False
        
        try:
            os.remove(filepath)
            logger.info(f"文档已删除：{filepath}")
            return True
        
        except Exception as e:
            logger.error(f"删除文档失败：{filepath}, 错误={e}")
            return False
    
    def list_documents(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """
        列出存储目录中的所有文档
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            documents: 文档列表，包含文件名、路径、大小、修改时间
        """
        try:
            files = []
            
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.md'):
                    filepath = os.path.join(self.storage_dir, filename)
                    stat = os.stat(filepath)
                    
                    files.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': stat.st_size,
                        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # 按修改时间倒序排序
            files.sort(key=lambda x: x['modified_at'], reverse=True)
            
            # 分页
            return files[offset:offset + limit]
        
        except Exception as e:
            logger.error(f"列出文档失败：{e}")
            return []
    
    def get_document_path(self, filename: str) -> str:
        """
        获取文档完整路径
        
        Args:
            filename: 文件名
        
        Returns:
            filepath: 完整路径
        """
        return os.path.join(self.storage_dir, filename)


# 全局服务实例
document_storage_service = DocumentStorageService()