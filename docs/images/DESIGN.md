# Memory Hub 视觉设计说明

## 🎨 设计概述

**设计理念**：科技感、简洁、专业
**主色调**：深蓝 (#1e3a5f) → 青色 (#06b6d4) → 紫色 (#8b5cf6)
**辅助色**：白色、深灰

---

## 📁 输出文件结构

```
memory-hub/
├── logo/
│   ├── memory-hub-logo.png    # Logo PNG 版本 (512x512)
│   └── memory-hub-logo.svg    # Logo SVG 矢量版本
│
└── docs/images/
    ├── hero-banner.png           # README 头图 (16:9)
    ├── architecture-diagram.png  # 系统架构图 (16:9)
    ├── memory-hub-concept.png    # 记忆中枢概念图 (16:9)
    ├── masmp-flowchart.png       # MASMP 协议流程图 (16:9)
    └── feature-icons.png         # 功能特性图标集 (16:9)
```

---

## 🧠 Logo 设计

### 设计元素

1. **中心大脑图标**
   - 象征智能体记忆中枢
   - 左右半球结构，中间分隔线

2. **网络节点**
   - 6 个外围节点代表分布式智能体
   - 圆形节点 + 发光效果

3. **连接线条**
   - 表示记忆共享和数据流转
   - 渐变色：蓝 → 青

4. **电路纹理**
   - 内部电路图案
   - 象征 AI 神经网络

### 配色方案

| 元素 | 颜色 | 说明 |
|------|------|------|
| 主渐变 | #1e3a5f → #2563eb → #06b6d4 | 深蓝到青色 |
| 发光色 | #8b5cf6 → #06b6d4 | 紫到青 |
| 节点 | #06b6d4, #2563eb | 青色、蓝色 |
| 背景 | #0f172a | 深蓝黑 |

### 使用场景

| 场景 | 推荐格式 | 说明 |
|------|----------|------|
| GitHub Avatar | PNG 512x512 | 项目头像 |
| 网站头部 | SVG | 矢量无损缩放 |
| 文档引用 | PNG 256x256 | 缩小版本 |

---

## 🖼️ 配图设计

### 1. Hero Banner (hero-banner.png)

**用途**：GitHub README 顶部头图
**尺寸**：16:9 宽屏 (推荐 1920x1080)
**元素**：
- 中心发光核心（记忆中枢）
- 神经网络连接扩展
- 大脑电路图案
- 数据流动粒子

**风格**：科技感、电影感、现代

---

### 2. 架构图 (architecture-diagram.png)

**用途**：技术文档、README 系统架构
**尺寸**：16:9 宽屏
**展示内容**：
- Memory Hub 核心层
- 周围连接的 AI Agent 节点
- PostgreSQL 数据库层
- 向量搜索可视化

---

### 3. 概念图 (memory-hub-concept.png)

**用途**：产品介绍、概念说明
**尺寸**：16:9 宽屏
**展示内容**：
- 中心发光球体（集体记忆）
- 四种记忆类型图标：
  - 文档 → 事实 (Fact)
  - 心形 → 偏好 (Preference)
  - 齿轮 → 技能 (Skill)
  - 闪电 → 经验 (Experience)
- 神经网络脉冲

---

### 4. MASMP 流程图 (masmp-flowchart.png)

**用途**：协议说明、技术文档
**尺寸**：16:9 宽屏
**展示流程**：
```
Register Agent → Store Memory → Vector Embed → Search Query → Retrieve Results
```

---

### 5. 功能图标集 (feature-icons.png)

**用途**：README 功能特性展示
**尺寸**：16:9 宽屏（包含 6 个图标）
**图标内容**：
1. 多智能体管理 (Brain + Network)
2. 统一存储 (Database)
3. 向量搜索 (Magnifying Glass + Vectors)
4. 智能遗忘 (Recycling Arrows)
5. RESTful API (Code Brackets)
6. 安全保障 (Shield Check)

---

## 📐 设计规范

### 色彩规范

```css
/* 主色系 */
--primary-dark: #0f172a;    /* 深蓝黑背景 */
--primary-blue: #1e3a5f;    /* 深蓝 */
--primary-cyan: #06b6d4;    /* 青色 */
--primary-purple: #8b5cf6;  /* 紫色 */

/* 辅助色 */
--accent-glow: rgba(6, 182, 212, 0.5);  /* 青色发光 */
--text-primary: #ffffff;    /* 白色文字 */
--text-secondary: #94a3b8;  /* 灰色文字 */
```

### 排版规范

| 元素 | 字体 | 说明 |
|------|------|------|
| 标题 | Inter / SF Pro | 粗体、大写 |
| 正文 | Inter / SF Pro | 常规、易读 |
| 代码 | JetBrains Mono | 等宽字体 |

### 间距规范

```css
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 32px;
--spacing-2xl: 48px;
```

---

## 🔧 使用指南

### Logo 使用

```markdown
<!-- README.md 引用 -->
![Memory Hub Logo](./logo/memory-hub-logo.png)

<!-- HTML 网页使用 -->
<img src="./logo/memory-hub-logo.svg" alt="Memory Hub" width="128">
```

### 配图使用

```markdown
<!-- Hero Banner -->
![Memory Hub](./docs/images/hero-banner.png)

<!-- 架构图 -->
## 系统架构
![Architecture](./docs/images/architecture-diagram.png)

<!-- 功能特性 -->
## 核心功能
![Features](./docs/images/feature-icons.png)
```

---

## 📝 设计原则

1. **简洁至上**：避免复杂装饰，保持视觉清晰
2. **色彩克制**：主色不超过 3 种，辅助色适度点缀
3. **风格统一**：所有视觉元素保持一致的设计语言
4. **可扩展性**：SVG 格式支持任意缩放不失真
5. **无障碍**：足够的对比度，确保可读性

---

## 📅 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-03-09 | 初始版本，完成全部视觉设计 |

---

*设计：小图 🎨 | Memory Hub 视觉包装*