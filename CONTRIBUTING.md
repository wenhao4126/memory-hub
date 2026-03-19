# 🤝 贡献指南

感谢你对 Memory Hub 项目的关注！欢迎任何形式的贡献，包括代码、文档、测试、问题报告和功能建议。

## 📖 目录

- [行为准则](#行为准则)
- [开发环境搭建](#开发环境搭建)
- [提交流程](#提交流程)
- [代码规范](#代码规范)
- [测试要求](#测试要求)
- [PR 指南](#pr-指南)

---

## 🎯 行为准则

本项目遵循 [Contributor Covenant](https://www.contributor-covenant.org/) 行为准则：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

---

## 🛠️ 开发环境搭建

### 前置要求

- **Node.js**: >= 18.0.0
- **npm**: >= 9.0.0
- **Git**: 最新版本
- **Docker** (可选): 用于 Docker 开发和测试

### 1. Fork 项目

在 GitHub 上点击 Fork 按钮，将项目 fork 到你的账户。

### 2. 克隆到本地

```bash
git clone git@github.com:YOUR_USERNAME/memory-hub.git
cd memory-hub
```

### 3. 安装依赖

```bash
npm install
```

### 4. 配置开发环境

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑 .env 文件，配置你的开发环境
nano .env
```

### 5. 启动开发服务

```bash
# 方式一：直接启动（需要配置数据库）
npm start

# 方式二：使用 Docker（推荐）
docker-compose up -d

# 验证安装
curl http://localhost:8000/api/v1/health
```

### 6. 运行测试

```bash
# 运行所有测试
npm test

# 运行特定测试文件
npm test -- tests/unit/test-commands.js

# 查看测试覆盖率
npm test -- --coverage
```

---

## 📝 提交流程

### 1. 创建分支

```bash
# 确保主分支是最新的
git checkout master
git pull upstream master

# 创建功能分支
git checkout -b feature/your-feature-name

# 分支命名规范：
# - feature/add-new-api        # 新功能
# - bugfix/fix-memory-leak     # Bug 修复
# - docs/update-readme         # 文档更新
# - refactor/cleanup-code      # 代码重构
# - test/add-unit-tests        # 测试添加
```

### 2. 进行修改

进行你的代码修改、文档更新或测试添加。

### 3. 提交更改

```bash
# 添加更改的文件
git add .

# 提交（遵循提交规范）
git commit -m "feat: add new search API endpoint"
```

### 4. 推送到 GitHub

```bash
git push origin feature/your-feature-name
```

---

## 📏 代码规范

### JavaScript/Node.js 规范

- 使用 ES6+ 语法
- 使用 `const` 和 `let`，避免 `var`
- 使用有意义的变量和函数名
- 保持函数简洁（建议不超过 50 行）
- 添加必要的注释和 JSDoc

### 提交信息规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Type 类型**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 代码重构（既不是新功能也不是 Bug 修复）
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具变动

**示例**:
```
feat(api): add vector search endpoint
fix(cli): resolve memory leak in long-running processes
docs(readme): update installation instructions
```

---

## ✅ 测试要求

### 单元测试

- 新功能必须包含单元测试
- Bug 修复需要添加回归测试
- 保持测试覆盖率在 80% 以上

```bash
# 运行测试
npm test

# 查看覆盖率报告
npm test -- --coverage
```

### 集成测试

对于 API 改动，需要添加集成测试：

```bash
# 启动测试数据库
docker-compose -f docker-compose.test.yml up -d

# 运行集成测试
npm run test:integration
```

### 手动测试

在提交 PR 前，确保在本地环境中手动测试过：

- [ ] 新功能按预期工作
- [ ] 没有破坏现有功能
- [ ] 文档已更新
- [ ] 代码已通过 lint 检查

---

## 🚀 PR 指南

### 1. 创建 Pull Request

1. 访问你的 fork 页面
2. 点击 "Compare & pull request"
3. 填写 PR 模板

### 2. PR 模板

```markdown
## 📋 变更类型

- [ ] 新功能 (feat)
- [ ] Bug 修复 (fix)
- [ ] 文档更新 (docs)
- [ ] 代码重构 (refactor)
- [ ] 测试添加 (test)
- [ ] 其他 (chore)

## 🎯 变更描述

清晰简洁地描述这个 PR 做了什么。

## 🐛 关联的 Issue

Fixes #123

## ✅ 测试清单

- [ ] 代码已通过本地测试
- [ ] 已添加或更新测试用例
- [ ] 文档已相应更新
- [ ] 遵循了代码规范
- [ ] 没有引入新的警告或错误

## 📸 截图（如果适用）

添加功能演示或 UI 变更的截图。

## 📝 其他信息

任何需要 reviewer 知道的额外信息。
```

### 3. Code Review

- 所有 PR 需要至少一个 maintainer 审核
- 积极回应 review 意见
- 保持专业和友好的态度
- 必要时进行讨论，解释你的设计决策

### 4. 合并

- PR 通过审核后会合并到 master 分支
- 合并后删除功能分支
- 在 release note 中记录变更

---

## 📚 资源

- [项目文档](docs/)
- [API 参考](docs/API.md)
- [架构设计](docs/ARCHITECTURE.md)
- [示例代码](examples/)

---

## 🙏 致谢

感谢所有为 Memory Hub 项目做出贡献的开发者！

你的每一次贡献都让这个项目变得更好！❤️
