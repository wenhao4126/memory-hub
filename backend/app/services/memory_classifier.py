# ============================================================
# Memory Hub - 记忆分类服务
# ============================================================
# 功能：自动判断记忆应该存私人表还是共同记忆表
# 作者：小码
# 日期：2026-03-09
# ============================================================

import re
from typing import Tuple, Optional
from enum import Enum

class MemoryVisibility(Enum):
    PRIVATE = "private"      # 私人记忆
    SHARED = "shared"        # 共同记忆
    TEAM = "team"           # 团队记忆

class MemoryClassifier:
    """记忆分类器：自动判断记忆可见性"""
    
    # 共同记忆关键词（出现这些词 → 共享）
    SHARED_KEYWORDS = [
        # 项目相关
        "项目", "架构", "设计", "规范", "标准", "流程",
        # 技术相关
        "技术", "代码", "开发", "测试", "部署", "API", "数据库",
        # 协作相关
        "协作", "团队", "共享", "经验", "最佳实践", "方法论",
        # 文档相关
        "文档", "教程", "指南", "手册", "说明",
    ]
    
    # 私人记忆关键词（出现这些词 → 不共享）
    PRIVATE_KEYWORDS = [
        # 个人偏好
        "喜欢", "不喜欢", "偏好", "习惯", "爱好",
        # 个人隐私
        "密码", "账号", "token", "密钥", "私钥",
        # 个人信息
        "电话", "地址", "身份证", "邮箱", "微信",
        # 情感相关
        "心情", "感受", "想法", "秘密", "隐私",
    ]
    
    # 智能体角色映射（某些角色的记忆默认共享）
    ROLE_DEFAULT_VISIBILITY = {
        "小码": MemoryVisibility.TEAM,    # 技术经验共享
        "小写": MemoryVisibility.TEAM,    # 文案模板共享
        "小测": MemoryVisibility.TEAM,    # 测试经验共享
        "傻妞": MemoryVisibility.PRIVATE, # 管家记忆偏私人
    }
    
    def classify(
        self,
        content: str,
        agent_name: Optional[str] = None,
        memory_type: Optional[str] = None
    ) -> Tuple[MemoryVisibility, float, str]:
        """
        分类记忆
        
        Args:
            content: 记忆内容
            agent_name: 智能体名称
            memory_type: 记忆类型（fact/experience/skill）
        
        Returns:
            (可见性，置信度，理由)
        """
        reasons = []
        shared_score = 0
        private_score = 0
        
        # 1. 关键词匹配
        for keyword in self.SHARED_KEYWORDS:
            if keyword in content:
                shared_score += 1
                reasons.append(f"包含共享关键词：{keyword}")
        
        for keyword in self.PRIVATE_KEYWORDS:
            if keyword in content:
                private_score += 2  # 私人关键词权重更高
                reasons.append(f"包含私人关键词：{keyword}")
        
        # 2. 智能体角色判断
        if agent_name and agent_name in self.ROLE_DEFAULT_VISIBILITY:
            default_visibility = self.ROLE_DEFAULT_VISIBILITY[agent_name]
            if default_visibility == MemoryVisibility.TEAM:
                shared_score += 1
                reasons.append(f"{agent_name} 的经验默认共享")
        
        # 3. 记忆类型判断
        if memory_type == "experience":
            shared_score += 1
            reasons.append("经验类记忆倾向于共享")
        elif memory_type in ["fact", "preference"]:
            private_score += 1
            reasons.append("事实/偏好类记忆倾向于私人")
        
        # 4. 特殊规则
        # 包含"憨货"的记忆 → 私人（用户隐私）
        if "憨货" in content:
            private_score += 3
            reasons.append("包含用户信息，保护隐私")
        
        # 包含代码/技术细节 → 共享（技术价值）
        if re.search(r'```|import |def |class |function', content):
            shared_score += 2
            reasons.append("包含代码，技术价值高")
        
        # 5. 最终判断
        if private_score > shared_score:
            confidence = min(private_score / (shared_score + private_score), 0.95)
            return MemoryVisibility.PRIVATE, confidence, "；".join(reasons)
        elif shared_score > 0:
            confidence = min(shared_score / (shared_score + private_score), 0.95)
            return MemoryVisibility.SHARED, confidence, "；".join(reasons)
        else:
            # 默认私人
            return MemoryVisibility.PRIVATE, 0.5, "无明确特征，默认私人"


# 全局实例
memory_classifier = MemoryClassifier()