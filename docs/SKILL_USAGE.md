# 傻妞手下技能使用指南

> 让每个需求都能找到对的手下

---

## 📦 技能分配总览

| 手下 | 职责 | 技能数量 | 核心技能 |
|------|------|---------|---------|
| 小搜 🟢 (team-researcher) | 信息采集 | 2 | agent-reach, find-skills |
| 小写 🟢 (team-writer) | 文案撰写 | 3 | brainstorming, marketing-psychology, self-improving-agent |
| 小码 🟡 (team-coder) | 代码开发 | 5 | frontend-design, mcp-builder, skill-creator, test-driven-development, self-improving-agent |
| 小审 🔴 (team-reviewer) | 质量审核 | 1 | self-improving-agent |
| 小图 🎨 (team-designer) | 图片设计 | 8 | baoyu-image-gen, baoyu-cover-image, baoyu-comic, baoyu-infographic, baoyu-slide-deck, baoyu-xhs-images, baoyu-article-illustrator, frontend-design |
| 小排 📐 (team-layout) | 排版布局 | 2 | baoyu-infographic, baoyu-slide-deck |
| 小析 📊 (team-analyst) | 数据分析 | 1 | agent-reach |
| 小网 🌐 (team-browser) | 网页浏览 | 1 | agent-reach |

---

## 🎯 场景 → 手下映射

### 🔍 需要搜索信息
→ **小搜 🟢** (team-researcher)
- `agent-reach` - 多平台搜索（Twitter/X, Reddit, YouTube, GitHub, 小红书, 抖音, 微信公众号等）
- `find-skills` - 发现和安装新技能

### ✍️ 需要写文案
→ **小写 🟢** (team-writer)
- `brainstorming` - 创意头脑风暴
- `marketing-psychology` - 营销心理学应用
- `self-improving-agent` - 持续改进

### 💻 需要写代码
→ **小码 🟡** (team-coder)
- `frontend-design` - 前端界面设计
- `mcp-builder` - MCP 服务器开发
- `skill-creator` - 创建新技能
- `test-driven-development` - 测试驱动开发
- `self-improving-agent` - 持续改进

### 🔴 需要审核质量
→ **小审 🔴** (team-reviewer)
- `self-improving-agent` - 代码审查和质量改进

### 🎨 需要生成图片
→ **小图 🎨** (team-designer)
- `baoyu-image-gen` - AI 图像生成（OpenAI/Google/Replicate）
- `baoyu-cover-image` - 文章封面图
- `baoyu-comic` - 知识漫画
- `baoyu-infographic` - 信息图
- `baoyu-slide-deck` - 幻灯片
- `baoyu-xhs-images` - 小红书图片
- `baoyu-article-illustrator` - 文章配图
- `frontend-design` - 前端设计

### 📐 需要排版布局
→ **小排 📐** (team-layout)
- `baoyu-infographic` - 信息图布局
- `baoyu-slide-deck` - 幻灯片布局

### 📊 需要数据分析
→ **小析 📊** (team-analyst)
- `agent-reach` - 数据采集

### 🌐 需要浏览网页
→ **小网 🌐** (team-browser)
- `agent-reach` - 网页浏览和交互

---

## 📋 技能详细说明

### agent-reach
**用途**: 多平台信息采集和网页交互
**支持平台**: Twitter/X, Reddit, YouTube, GitHub, 小红书, 抖音, 微信公众号, LinkedIn, Boss直聘, RSS
**触发词**: "搜推特", "搜小红书", "看视频", "搜一下", "上网搜"

### baoyu-image-gen
**用途**: AI 图像生成
**支持后端**: OpenAI DALL-E, Google Imagen, DashScope, Replicate
**特点**: 支持文本生图、参考图、多种宽高比

### brainstorming
**用途**: 创意头脑风暴和需求分析
**触发**: 创建功能、构建组件前必须使用
**流程**: 探索用户意图 → 理解需求 → 设计方案

### frontend-design
**用途**: 创建高质量前端界面
**场景**: 网页、落地页、仪表盘、React 组件
**特点**: 避免 AI 味道，追求独特设计

### mcp-builder
**用途**: 构建 MCP 服务器
**支持**: Python (FastMCP) 和 Node/TypeScript (MCP SDK)
**场景**: 集成外部 API 和服务

### self-improving-agent
**用途**: 持续改进和质量审核
**功能**: 捕获错误、记录学习、优化流程
**触发**: 命令失败、用户纠正、发现更好方法时

### skill-creator
**用途**: 创建和优化技能
**功能**: 创建新技能、修改现有技能、性能评估

### test-driven-development
**用途**: 测试驱动开发
**触发**: 实现功能或修复 Bug 前
**流程**: 先写测试 → 再写实现

---

## 🧹 清理流程

每月执行一次技能清理，保持系统整洁：

```bash
# 1. 先预览（不执行删除）
cd /home/wen/.openclaw/workspace
./scripts/skill-cleanup.sh --dry-run

# 2. 查看报告
cat ~/memory/skill-cleanup-report.md

# 3. 执行清理（带确认）
./scripts/skill-cleanup.sh

# 4. 强制清理（无确认，慎用）
./scripts/skill-cleanup.sh --force
```

### 清理标准
- **阈值**: 90 天（3 个月）未更新
- **排除**: 符号链接（共享技能）
- **日志**: `~/memory/skill-cleanup.log`

---

## 📝 添加新技能流程

### 1. 评估需求
- 确定哪个手下需要这个技能
- 考虑技能是否适合团队职责

### 2. 搜索技能
```bash
clawhub search <关键词>
```

### 3. 安装到对应手下
```bash
# 安装到小码
clawhub install <skill> --dir ~/.openclaw/workspace-team-coder/skills/

# 安装到小图
clawhub install <skill> --dir ~/.openclaw/workspace-team-designer/skills/
```

### 4. 更新文档
- 修改 `docs/SKILL_USAGE.md`（本文档）
- 更新对应团队的 `TOOLS.md`

### 5. 记录到记忆
```bash
echo "$(date '+%Y-%m-%d'): 安装 <skill> 到 <team>" >> ~/memory/skill-changelog.md
```

---

## 🔄 技能共享机制

部分技能通过符号链接共享给多个团队：

```
find-skills → team-researcher（来自 ~/.agents/skills/）
```

**优点**:
- 单点维护
- 自动同步更新
- 节省存储空间

**创建符号链接**:
```bash
ln -s ~/.agents/skills/find-skills ~/.openclaw/workspace-team-xxx/skills/
```

---

## ⚠️ 注意事项

1. **不要删除符号链接目标**: 符号链接指向的源文件是共享的
2. **清理前先备份**: 重要技能建议先备份
3. **测试新技能**: 安装后先测试功能是否正常
4. **定期清理**: 避免技能堆积，影响性能

---

## 📞 问题排查

### 技能不生效
```bash
# 检查技能目录权限
ls -la ~/.openclaw/workspace-team-*/skills/

# 检查 SKILL.md 是否存在
find ~/.openclaw/workspace-team-*/skills/ -name "SKILL.md"
```

### 清理脚本报错
```bash
# 检查脚本权限
chmod +x ~/workspace/scripts/skill-cleanup.sh

# 检查目录是否存在
mkdir -p ~/workspace/memory
```

---

*最后更新：2026-03-07*
*维护者：小码 🟡*