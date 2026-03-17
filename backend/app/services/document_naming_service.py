# ============================================================
# 多智能体记忆中枢 - 文档命名服务
# ============================================================
# 功能：根据文档内容生成有意义的中文名字
# 作者：小码 🟡
# 日期：2026-03-16
#
# ⚠️ 设计理念（憨货决策）：
#   - 小搜/小写生成的 .md 文档，根据内容起有意义的中文名
#   - 原则：有意义、简洁、中文优先、保留技术名词
#   - 示例：Python 快速入门教程.md、Vue.js 组件开发指南.md
#
# 命名规则：
#   1. 从标题提取关键词
#   2. 从内容提取关键信息
#   3. 组合成有意义的中文名字
#   4. 清理非法字符
#   5. 不超过 30 个字
# ============================================================

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentNamingService:
    """
    文档命名服务 - 根据文档内容生成有意义的中文名字
    
    功能：
        - generate_chinese_name(): 根据标题、内容生成中文名字
        - sanitize_filename(): 清理文件名中的非法字符
    
    使用场景：
        小搜搜索完成 → 生成中文名字 → 保存为 .md 文件
    
    命名原则：
        1. 有意义 - 能看出文档内容
        2. 简洁 - 不超过 30 个字
        3. 中文优先 - 优先使用中文
        4. 保留关键英文 - 技术名词保留英文（Python、Vue.js、React 等）
    """
    
    # 技术名词列表（保留英文）
    TECH_KEYWORDS = [
        # 编程语言
        'Python', 'JavaScript', 'TypeScript', 'Java', 'C\\+\\+', 'C#', 'Go', 'Rust',
        'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'Perl',
        # 前端框架
        'React', 'Vue\\.js', 'Vue', 'Angular', 'Svelte', 'Next\\.js', 'Nuxt\\.js',
        'Express', 'Koa', 'FastAPI', 'Django', 'Flask', 'Spring', 'SpringBoot',
        # 运行时和工具
        'Node\\.js', 'Node', 'Deno', 'Bun', 'npm', 'yarn', 'pnpm', 'webpack', 'vite',
        'Docker', 'Kubernetes', 'K8s', 'Git', 'GitHub', 'GitLab', 'Jenkins',
        # 数据库
        'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 'SQL Server',
        # AI/ML
        'AI', 'ML', 'GPT', 'LLM', 'OpenAI', 'Claude', 'Gemini', 'ChatGPT',
        'TensorFlow', 'PyTorch', 'Keras', 'Transformers',
        # 云服务
        'AWS', 'Azure', 'GCP', 'Alibaba Cloud', '腾讯云', '阿里云', '华为云',
        # 其他技术名词
        'API', 'REST', 'GraphQL', 'gRPC', 'HTTP', 'HTTPS', 'TCP', 'UDP', 'IP',
        'Linux', 'Windows', 'macOS', 'Ubuntu', 'CentOS', 'Debian',
        'Nginx', 'Apache', 'Redis', 'Kafka', 'RabbitMQ', 'Elasticsearch',
        # 开发概念
        'CI/CD', 'DevOps', 'Agile', 'Scrum', 'TDD', 'BDD',
    ]
    
    # 中英文对照表（用于翻译常见词汇）
    EN_CN_MAPPING = {
        # 教程类型
        'Tutorial': '教程',
        'Guide': '指南',
        'Introduction': '入门',
        'Quick Start': '快速入门',
        'Getting Started': '快速上手',
        'Documentation': '文档',
        'Docs': '文档',
        'API Reference': 'API 参考',
        'Reference': '参考',
        'Manual': '手册',
        'Handbook': '手册',
        
        # 学习类型
        'Course': '课程',
        'Lesson': '课程',
        'Training': '培训',
        'Learning': '学习',
        'Basics': '基础',
        'Fundamentals': '基础',
        'Advanced': '进阶',
        'Advanced Topics': '进阶',
        'Best Practices': '最佳实践',
        
        # 内容类型
        'Example': '示例',
        'Examples': '示例',
        'Demo': '演示',
        'Sample': '示例',
        'Case Study': '案例分析',
        'Cookbook': '实战',
        'Recipes': '实战技巧',
        
        # 主题类型
        'Setup': '配置',
        'Installation': '安装',
        'Configuration': '配置',
        'Deployment': '部署',
        'Development': '开发',
        'Testing': '测试',
        'Debugging': '调试',
        'Performance': '性能',
        'Security': '安全',
        'Optimization': '优化',
        
        # 标题后缀
        '- 菜鸟教程': '',
        '- 廖雪峰': '',
        '- 官方文档': '官方文档',
        '| 菜鸟教程': '',
        '| 廖雪峰': '',
    }
    
    # 中文停用词（不作为关键词）
    STOP_WORDS = {
        '的', '了', '是', '在', '有', '和', '与', '或', '但', '而',
        '这', '那', '这个', '那个', '这些', '那些',
        '一个', '一些', '一种', '一篇', '一段',
        '可以', '能够', '应该', '需要', '必须',
        '我们', '你们', '他们', '它', '她', '他',
        '什么', '怎么', '如何', '为什么', '哪里', '哪个',
        '非常', '很', '太', '更', '最', '特别',
        '已经', '正在', '将要', '曾经',
        '就是', '不是', '只是', '还是',
        '以及', '或者', '并且', '而且', '但是',
    }
    
    async def generate_chinese_name(
        self,
        title: str,
        content: str = None,
        source: str = None,
        url: str = None
    ) -> str:
        """
        根据文档内容生成有意义的中文名字
        
        Args:
            title: 原始标题
            content: 文档内容（可选，用于提取更多信息）
            source: 来源（小搜/小写等，可选）
            url: 文档 URL（可选，用于提取域名信息）
        
        Returns:
            chinese_name: 中文文件名（不含 .md 后缀）
        
        示例：
            generate_chinese_name(
                title="Python 基础教程 | 菜鸟教程",
                content="...",
                source="小搜",
                url="https://www.runoob.com/python/python-tutorial.html"
            )
            → "Python 基础教程"
            
            generate_chinese_name(
                title="快速上手 - Vue.js",
                content="...",
                source="小搜",
                url="https://vuejs.org/guide/introduction.html"
            )
            → "Vue.js 快速上手指南"
        """
        logger.info(f"生成中文名字：title={title[:50] if title else 'None'}")
        
        # ============================================================
        # 步骤 1：预处理标题
        # ============================================================
        processed_title = self._preprocess_title(title)
        
        # ============================================================
        # 步骤 2：提取关键词
        # ============================================================
        keywords = self._extract_keywords(processed_title, content)
        
        # ============================================================
        # 步骤 3：组合成有意义的中文名字
        # ============================================================
        chinese_name = self._compose_name(keywords, processed_title, url)
        
        # ============================================================
        # 步骤 4：清理和优化
        # ============================================================
        chinese_name = self.sanitize_filename(chinese_name)
        
        # ============================================================
        # 步骤 5：限制长度（不超过 30 个字）
        # ============================================================
        if len(chinese_name) > 30:
            chinese_name = chinese_name[:30]
            logger.info(f"文件名过长，截取为：{chinese_name}")
        
        logger.info(f"生成的中文名字：{chinese_name}")
        
        return chinese_name
    
    def _preprocess_title(self, title: str) -> str:
        """
        预处理标题 - 清理常见的网站后缀和前缀
        
        Args:
            title: 原始标题
        
        Returns:
            processed_title: 处理后的标题
        """
        if not title:
            return ""
        
        processed = title.strip()
        
        # 移除常见的网站名称（后缀）
        suffixes_to_remove = [
            r'\s*[-_|]\s*菜鸟教程$',
            r'\s*[-_|]\s*廖雪峰的官方网站$',
            r'\s*[-_|]\s*廖雪峰$',
            r'\s*[-_|]\s*官方文档$',
            r'\s*[-_|]\s*官方中文网$',
            r'\s*[-_|]\s*中文网$',
            r'\s*-\s*GitHub$',
            r'\s*-\s*CSDN$',
            r'\s*-\s*掘金$',
            r'\s*-\s*知乎$',
            r'\s*-\s*博客园$',
            r'\s*-\s*SegmentFault$',
        ]
        
        for pattern in suffixes_to_remove:
            processed = re.sub(pattern, '', processed, flags=re.IGNORECASE)
        
        # 移除多余的分隔符
        processed = re.sub(r'\s*[-_|]+\s*$', '', processed)
        processed = re.sub(r'^\s*[-_|]+\s*', '', processed)
        
        return processed.strip()
    
    def _extract_keywords(self, title: str, content: str = None) -> list:
        """
        从标题和内容中提取关键词
        
        Args:
            title: 标题
            content: 内容（可选）
        
        Returns:
            keywords: 关键词列表
        """
        keywords = []
        
        # 1. 提取技术名词（保留英文）
        for tech in self.TECH_KEYWORDS:
            # 在标题中查找
            if re.search(rf'\b{tech}\b', title, re.IGNORECASE):
                # 规范化技术名词（如 vue -> Vue.js）
                normalized = self._normalize_tech_keyword(tech)
                if normalized and normalized not in keywords:
                    keywords.append(normalized)
        
        # 2. 提取中文关键词（简单分词）
        # 使用正则提取中文词组（2-4个字）
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', title)
        for word in chinese_words:
            if word not in self.STOP_WORDS and word not in keywords:
                keywords.append(word)
        
        # 3. 如果内容不为空，提取前 200 字符中的关键词
        if content:
            content_preview = content[:200]
            for tech in self.TECH_KEYWORDS[:20]:  # 只检查前 20 个
                if re.search(rf'\b{tech}\b', content_preview, re.IGNORECASE):
                    normalized = self._normalize_tech_keyword(tech)
                    if normalized and normalized not in keywords:
                        keywords.append(normalized)
        
        return keywords
    
    def _normalize_tech_keyword(self, keyword: str) -> str:
        """
        规范化技术名词
        
        Args:
            keyword: 原始关键词（可能是正则表达式）
        
        Returns:
            normalized: 规范化后的关键词
        """
        # 移除正则表达式的转义字符
        normalized = keyword.replace('\\', '')
        
        # 特殊处理
        special_cases = {
            'Vue': 'Vue.js',
            'Node': 'Node.js',
            'Next.js': 'Next.js',
            'Nuxt.js': 'Nuxt.js',
            'C++': 'C++',
            'C#': 'C#',
        }
        
        return special_cases.get(normalized, normalized)
    
    def _compose_name(self, keywords: list, title: str, url: str = None) -> str:
        """
        组合成有意义的中文名字
        
        Args:
            keywords: 关键词列表
            title: 处理后的标题
            url: 原始 URL（可选）
        
        Returns:
            composed_name: 组合后的名字
        """
        # 如果标题已经很好，直接使用
        if self._is_good_chinese_title(title):
            return title
        
        # 否则，使用关键词组合
        if not keywords:
            # 没有提取到关键词，使用原始标题
            return title
        
        # 尝试组合关键词
        # 优先保留技术名词 + 中文关键词
        tech_keywords = []
        cn_keywords = []
        
        for kw in keywords:
            if re.match(r'^[A-Za-z0-9._+#-]+$', kw):
                tech_keywords.append(kw)
            else:
                cn_keywords.append(kw)
        
        # 组合策略：
        # 1. 技术名词在前（如 Python、Vue.js）
        # 2. 中文关键词在后（如 基础教程、快速入门）
        
        parts = []
        
        # 添加技术名词
        if tech_keywords:
            parts.extend(tech_keywords[:2])  # 最多 2 个技术名词
        
        # 添加中文关键词
        if cn_keywords:
            parts.extend(cn_keywords[:3])  # 最多 3 个中文关键词
        
        # 如果还是没有内容，返回标题
        if not parts:
            return title
        
        # 用空格连接
        composed = ' '.join(parts)
        
        # 添加后缀（如果标题暗示了文档类型）
        suffix = self._detect_doc_type_suffix(title, url)
        if suffix and suffix not in composed:
            composed = f"{composed} {suffix}"
        
        return composed
    
    def _is_good_chinese_title(self, title: str) -> bool:
        """
        判断标题是否已经是好的中文名字
        
        Args:
            title: 标题
        
        Returns:
            is_good: 是否是好的标题
        """
        if not title:
            return False
        
        # 好的标题特征：
        # 1. 包含中文
        # 2. 长度适中（5-25 个字）
        # 3. 不包含网站名称
        # 4. 不包含特殊符号
        
        has_chinese = bool(re.search(r'[\u4e00-\u9fa5]', title))
        proper_length = 5 <= len(title) <= 25
        no_website_name = not re.search(r'(菜鸟教程|廖雪峰|CSDN|掘金|知乎)', title)
        no_special_chars = not re.search(r'[|/\\]', title)
        
        return has_chinese and proper_length and no_website_name and no_special_chars
    
    def _detect_doc_type_suffix(self, title: str, url: str = None) -> str:
        """
        检测文档类型并返回后缀
        
        Args:
            title: 标题
            url: URL（可选）
        
        Returns:
            suffix: 文档类型后缀
        """
        title_lower = title.lower()
        
        # 根据标题关键词判断
        if any(word in title_lower for word in ['tutorial', '教程', '入门', '学习']):
            return '教程'
        elif any(word in title_lower for word in ['guide', '指南', '手册']):
            return '指南'
        elif any(word in title_lower for word in ['reference', '参考', '文档']):
            return '文档'
        elif any(word in title_lower for word in ['api', '接口']):
            return 'API 参考'
        elif any(word in title_lower for word in ['example', '示例', 'demo']):
            return '示例'
        elif any(word in title_lower for word in ['quick start', '快速上手', '快速入门']):
            return '快速入门'
        elif any(word in title_lower for word in ['installation', '安装', '配置']):
            return '配置指南'
        elif any(word in title_lower for word in ['best practices', '最佳实践']):
            return '最佳实践'
        
        # 根据 URL 判断
        if url:
            url_lower = url.lower()
            if '/docs/' in url_lower or '/documentation/' in url_lower:
                return '文档'
            elif '/guide/' in url_lower or '/tutorial/' in url_lower:
                return '教程'
            elif '/api/' in url_lower:
                return 'API 参考'
        
        return ''
    
    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名中的非法字符
        
        Args:
            filename: 原始文件名
        
        Returns:
            safe_filename: 清理后的文件名
        
        清理规则：
            1. 移除 Windows/Linux 不允许的字符：< > : " / \\ | ? *
            2. 保留空格（不替换为下划线，保持可读性）
            3. 移除连续空格
            4. 移除首尾空格
        """
        if not filename:
            return "未命名文档"
        
        # 定义非法字符（Windows/Linux）
        invalid_chars = '<>:"/\\|？*'
        
        safe_name = filename
        for char in invalid_chars:
            safe_name = safe_name.replace(char, ' ')
        
        # 移除连续空格
        safe_name = re.sub(r'\s+', ' ', safe_name)
        
        # 移除首尾空格
        safe_name = safe_name.strip()
        
        # 如果清理后为空，返回默认名称
        if not safe_name:
            return "未命名文档"
        
        return safe_name


# 全局服务实例
document_naming_service = DocumentNamingService()