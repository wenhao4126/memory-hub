# Memory Hub 使用场景示例 🎯

> 真实场景演示：个人开发者、团队、企业如何使用 Memory Hub

---

## 📋 目录

1. [个人开发者场景](#个人开发者场景)
2. [小团队场景](#小团队场景)
3. [企业级场景](#企业级场景)
4. [特殊场景](#特殊场景)

---

## 个人开发者场景

### 场景 1: 个人 AI 助手

**用户画像**: 自由开发者，使用多个 AI 工具辅助工作

**痛点**:
- 每次都要重新解释自己的技术栈
- AI 记不住项目背景
- 在不同 AI 工具间重复说明需求

**解决方案**:

```bash
# 1. 创建个人智能体
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的 AI 助手",
    "description": "个人开发助手",
    "capabilities": ["代码审查", "架构设计", "技术选型"]
  }'

# 2. 添加个人偏好记忆
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_xxx",
    "content": "用户主要使用 TypeScript + Node.js 技术栈",
    "memory_type": "fact",
    "importance": 0.9,
    "tags": ["技术栈", "偏好"]
  }'

# 3. 添加项目背景
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_xxx",
    "content": "用户正在开发 Memory Hub - 一个 AI 记忆管理系统",
    "memory_type": "fact",
    "importance": 0.8,
    "tags": ["项目", "工作"]
  }'

# 4. 添加沟通偏好
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_xxx",
    "content": "用户喜欢简洁直接的回答，讨厌废话",
    "memory_type": "preference",
    "importance": 0.95,
    "tags": ["沟通风格"]
  }'
```

**使用效果**:

```
第一次对话：
用户：帮我 review 一下这段代码
AI：好的，你是用 TypeScript 写的对吧？我按照你的简洁风格直接说重点...

第 N 次对话：
用户：这个架构怎么优化？
AI：根据你的技术栈偏好，我建议用...（自动记得你是 TS 开发者）
```

**价值**:
- ✅ 不再重复解释技术栈
- ✅ AI 越用越懂你
- ✅ 提升沟通效率

---

### 场景 2: 多智能体协作

**用户画像**: 开发者使用多个专用 AI 助手（写作、代码、设计）

**痛点**:
- 每个 AI 都是独立记忆
- 在写作 AI 说的需求，代码 AI 不知道
- 信息孤岛

**解决方案**:

```bash
# 创建多个智能体，共享同一个记忆库

# 1. 写作助手
curl -X POST http://localhost:8000/api/v1/agents \
  -d '{"name": "小写", "capabilities": ["写作", "翻译"]}'

# 2. 代码助手
curl -X POST http://localhost:8000/api/v1/agents \
  -d '{"name": "小码", "capabilities": ["开发", "调试"]}'

# 3. 设计助手
curl -X POST http://localhost:8000/api/v1/agents \
  -d '{"name": "小图", "capabilities": ["设计", "配图"]}'

# 4. 添加共享记忆（所有智能体都能访问）
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "shared",  # 共享记忆
    "content": "用户正在开发一个 AI 记忆管理系统，项目名叫 Memory Hub",
    "memory_type": "fact",
    "importance": 0.9,
    "tags": ["项目背景", "共享"]
  }'
```

**使用流程**:

```
1. 告诉小写："我在做 Memory Hub 项目，需要写文档"
   ↓ 记忆存储到共享库

2. 问小码："Memory Hub 的 API 怎么设计？"
   ↓ 自动检索到项目背景，给出针对性建议

3. 让小图："给 Memory Hub 设计个 logo"
   ↓ 知道项目定位，设计风格匹配
```

**价值**:
- ✅ 信息在智能体间流通
- ✅ 避免重复说明
- ✅ 多智能体协作更顺畅

---

## 小团队场景

### 场景 3: 客服机器人团队

**用户画像**: 10 人电商团队，需要处理客户咨询

**痛点**:
- 客户每次咨询都要重新说明情况
- 不同客服机器人信息不互通
- 客户体验差

**解决方案**:

```bash
# 1. 为每个客户创建独立智能体
curl -X POST http://localhost:8000/api/v1/agents \
  -d '{
    "name": "客户_张三",
    "description": "VIP 客户 - 张三",
    "metadata": {
      "customer_id": "C001",
      "level": "VIP",
      "tags": ["电子产品", "高频购买"]
    }
  }'

# 2. 记录客户偏好
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_customer_zhang",
    "content": "客户偏好顺丰快递，不喜欢放快递柜",
    "memory_type": "preference",
    "importance": 0.9,
    "tags": ["配送偏好"]
  }'

# 3. 记录购买历史
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_customer_zhang",
    "content": "客户上次购买了 iPhone 15 Pro，2026-02-15 发货",
    "memory_type": "experience",
    "importance": 0.7,
    "tags": ["购买历史"]
  }'

# 4. 记录投诉记录
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_customer_zhang",
    "content": "客户曾因包装破损投诉，要求加强包装",
    "memory_type": "experience",
    "importance": 0.95,
    "tags": ["投诉记录", "重要"]
  }'
```

**使用效果**:

```
客户：我买的东西什么时候到？

传统客服：
"亲，请提供订单号，我帮您查询"

Memory Hub 客服：
"张先生您好，您的 iPhone 15 Pro 订单已发货，
预计明天到达。已备注顺丰配送，不放快递柜。"
```

**价值**:
- ✅ 客户体验提升
- ✅ 减少重复沟通
- ✅ 提高客户满意度

---

### 场景 4: 内部知识助手

**用户画像**: 20 人技术团队，新人培训成本高

**痛点**:
- 新人反复问相同问题
- 老员工重复解答
- 知识沉淀困难

**解决方案**:

```bash
# 1. 创建团队知识助手
curl -X POST http://localhost:8000/api/v1/agents \
  -d '{
    "name": "团队知识库",
    "description": "技术团队内部助手",
    "capabilities": ["新人指引", "技术问答", "流程咨询"]
  }'

# 2. 导入团队规范
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_team_knowledge",
    "content": "团队使用 Git Flow 工作流，main 分支保护，feature 分支开发",
    "memory_type": "fact",
    "importance": 0.9,
    "tags": ["开发规范", "Git"]
  }'

# 3. 导入技术栈信息
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_team_knowledge",
    "content": "团队技术栈：React + TypeScript + Node.js + PostgreSQL",
    "memory_type": "fact",
    "importance": 0.85,
    "tags": ["技术栈"]
  }'

# 4. 导入部署流程
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_team_knowledge",
    "content": "部署流程：开发 → 测试环境 → 预发布 → 生产，需 Code Review",
    "memory_type": "fact",
    "importance": 0.9,
    "tags": ["部署", "流程"]
  }'

# 5. 导入常见问题
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_team_knowledge",
    "content": "开发环境配置：Node 18+，npm 9+，PostgreSQL 15+",
    "memory_type": "fact",
    "importance": 0.8,
    "tags": ["环境配置", "新人指引"]
  }'
```

**使用效果**:

```
新人：我们用什么工作流？

AI：团队使用 Git Flow：
1. main 分支保护，直接发布
2. develop 分支集成分支
3. feature 分支开发新功能
4. 提交 PR 需 Code Review

详细文档：/docs/git-flow.md
```

**价值**:
- ✅ 减少重复解答
- ✅ 知识沉淀自动化
- ✅ 新人培训效率提升

---

## 企业级场景

### 场景 5: 企业智能客服平台

**用户画像**: 大型企业，多产品线，海量客户

**需求**:
- 百万级客户记忆管理
- 高并发访问
- 数据安全隔离
- 跨部门记忆共享

**架构设计**:

```
┌─────────────────────────────────────────────────┐
│              Memory Hub Cluster                 │
├─────────────────────────────────────────────────┤
│  API Gateway (负载均衡)                          │
├──────────┬──────────┬──────────┬───────────────┤
│ 产品 A   │ 产品 B   │ 产品 C   │ 公共知识      │
│ 记忆库   │ 记忆库   │ 记忆库   │ 记忆库        │
├──────────┴──────────┴──────────┴───────────────┤
│         PostgreSQL Cluster + pgvector           │
└─────────────────────────────────────────────────┘
```

**部署配置**:

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  api:
    image: memory-hub:latest
    deploy:
      replicas: 5  # 5 个 API 实例
    environment:
      - DB_POOL_MIN=20
      - DB_POOL_MAX=100
      - LOG_LEVEL=WARN
  
  db:
    image: pgvector/pgvector:pg15
    deploy:
      replicas: 3  # 主从复制
    volumes:
      - pgdata:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    # 缓存热点记忆

volumes:
  pgdata:
```

**数据隔离策略**:

```bash
# 按部门创建独立命名空间
curl -X POST http://localhost:8000/api/v1/namespaces \
  -d '{"name": "sales_dept", "description": "销售部"}'

curl -X POST http://localhost:8000/api/v1/namespaces \
  -d '{"name": "support_dept", "description": "客服部"}'

# 跨部门共享记忆
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "shared_product_info",
    "namespace": "public",
    "content": "产品 X 的核心功能：...",
    "memory_type": "fact",
    "importance": 0.9,
    "tags": ["产品信息", "共享"]
  }'
```

**性能优化**:

```yaml
# 生产环境配置
database:
  pool:
    min: 20
    max: 100
    idle_timeout: 30000
  
vector:
  dimensions: 1536
  similarity_threshold: 0.7
  index_type: "hnsw"  # HNSW 索引
  hnsw_params:
    m: 16
    ef_construction: 64

cache:
  enabled: true
  ttl: 3600  # 1 小时缓存
```

**价值**:
- ✅ 支持百万级记忆
- ✅ 高并发低延迟
- ✅ 数据安全隔离
- ✅ 跨部门协作

---

### 场景 6: 企业培训系统

**用户画像**: 大型企业，员工培训需求

**应用场景**:

```
1. 新员工入职培训
   - 记录学习进度
   - 个性化推荐内容
   - 自动答疑

2. 技能提升培训
   - 记录已掌握技能
   - 推荐进阶内容
   - 跟踪学习效果

3. 合规培训
   - 记录培训历史
   - 到期自动提醒
   - 考试记录管理
```

**实现示例**:

```bash
# 创建员工学习档案
curl -X POST http://localhost:8000/api/v1/agents \
  -d '{
    "name": "员工_李四_学习档案",
    "description": "李四的学习进度跟踪",
    "metadata": {
      "employee_id": "E12345",
      "department": "技术部",
      "hire_date": "2026-01-15"
    }
  }'

# 记录已完成培训
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_employee_lisi",
    "content": "已完成：信息安全培训（2026-02-01，得分 95）",
    "memory_type": "experience",
    "importance": 0.8,
    "tags": ["培训记录", "已完成"]
  }'

# 记录待培训项目
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_employee_lisi",
    "content": "待完成：数据隐私培训（截止日期：2026-04-01）",
    "memory_type": "fact",
    "importance": 0.9,
    "tags": ["培训记录", "待完成", "紧急"]
  }'

# 记录技能掌握情况
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_employee_lisi",
    "content": "已掌握：TypeScript(熟练), React(中级), Node.js(入门)",
    "memory_type": "fact",
    "importance": 0.85,
    "tags": ["技能", "技术栈"]
  }'
```

**使用效果**:

```
HR：李四还需要完成哪些培训？

AI：李四待完成培训：
1. 数据隐私培训（截止：2026-04-01）⚠️ 即将到期
2. 领导力基础（截止：2026-06-01）

已完成培训：
- 信息安全培训（95 分）
- 企业文化培训（100 分）

建议优先安排数据隐私培训。
```

**价值**:
- ✅ 培训记录自动化
- ✅ 个性化学习路径
- ✅ 合规风险降低

---

## 特殊场景

### 场景 7: 多语言支持

**需求**: 服务全球用户，多语言记忆管理

**解决方案**:

```bash
# 添加语言偏好记忆
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_global",
    "content": "用户偏好中文交流",
    "memory_type": "preference",
    "importance": 0.95,
    "tags": ["语言偏好"]
  }'

# 添加翻译记忆
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_global",
    "content": "用户常用术语：Memory Hub=记忆中枢，Agent=智能体",
    "memory_type": "fact",
    "importance": 0.7,
    "tags": ["术语", "翻译"]
  }'
```

---

### 场景 8: 隐私保护

**需求**: 敏感数据保护，合规要求

**解决方案**:

```bash
# 添加敏感标记
curl -X POST http://localhost:8000/api/v1/memories \
  -d '{
    "agent_id": "agent_secure",
    "content": "用户手机号：138****1234",
    "memory_type": "fact",
    "importance": 0.8,
    "tags": ["个人信息", "敏感"],
    "encryption": true,  # 加密存储
    "access_level": "admin"  # 访问权限控制
  }'
```

**权限控制**:

```yaml
# 配置访问权限
security:
  encryption_at_rest: true
  access_control:
    - role: admin
      permissions: [read, write, delete]
    - role: user
      permissions: [read, write]
    - role: guest
      permissions: [read]
```

---

## 📊 场景对比总结

| 场景 | 用户规模 | 记忆量 | 并发 | 关键需求 |
|------|---------|--------|------|---------|
| 个人助手 | 1 人 | <100 条 | 低 | 个性化 |
| 多智能体 | 1 人 | <500 条 | 低 | 共享 |
| 客服机器人 | 1000+ 客户 | 1 万 + 条 | 中 | 客户体验 |
| 团队知识 | 20-50 人 | 1000+ 条 | 中 | 知识沉淀 |
| 企业客服 | 10 万 + 客户 | 百万 + 条 | 高 | 性能 + 安全 |
| 企业培训 | 1000+ 员工 | 10 万 + 条 | 中 | 合规 |

---

## 🎯 选择你的场景

**个人开发者** → 场景 1、2
**小团队** → 场景 3、4
**企业** → 场景 5、6
**特殊需求** → 场景 7、8

---

*场景示例持续更新中... 欢迎贡献你的使用案例！*
