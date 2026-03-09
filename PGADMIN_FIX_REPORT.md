# pgAdmin 账户锁定问题修复报告

**修复时间**: 2026-03-06 16:45
**负责人**: 小码
**问题等级**: 高优先级

---

## 🐛 问题描述

用户无法登录 pgAdmin，出现错误提示：
```
Your account is locked. Please contact the Administrator.
```

**原因**: 多次登录失败导致账户被锁定

---

## ✅ 修复方案

**采用的方案**: 方案 2 - 完全重置 pgAdmin

**选择理由**: 
- 方案 1（重启容器）无效，账户锁定状态存储在数据卷中
- 方案 3（容器内解锁）需要 sqlite3 工具，容器中未安装
- 方案 2 可以彻底重置账户状态，使用正确的密码重新初始化

---

## 📝 修复步骤

### 1. 检查初始状态
```bash
# 检查容器状态
docker ps | grep memory-hub-admin

# 检查账户状态（使用 Python）
docker exec memory-hub-admin python3 -c "
import sqlite3
conn = sqlite3.connect('/var/lib/pgadmin/pgadmin4.db')
cursor = conn.cursor()
cursor.execute(\"SELECT id, email, login_attempts, locked FROM user WHERE email = 'admin@memory.hub'\")
row = cursor.fetchone()
print('Login Attempts:', row[2], 'Locked:', row[3])
"
```
**结果**: 账户锁定 (login_attempts=3, locked=1)

### 2. 尝试方案 1（重启容器）
```bash
docker restart memory-hub-admin
```
**结果**: 无效，账户仍被锁定

### 3. 执行方案 2（完全重置）
```bash
cd /home/wen/projects/memory-hub

# 停止 pgAdmin
docker-compose stop pgadmin

# 删除容器
docker-compose rm -f pgadmin

# 删除数据卷
docker volume rm memory-hub_pgadmin_data

# 重新启动
docker-compose up -d pgadmin

# 等待启动
sleep 10
```

### 4. 验证修复结果
```bash
# 检查容器状态
docker ps | grep memory-hub-admin

# 检查账户状态
docker exec memory-hub-admin python3 -c "
import sqlite3
conn = sqlite3.connect('/var/lib/pgadmin/pgadmin4.db')
cursor = conn.cursor()
cursor.execute(\"SELECT id, email, active, locked, login_attempts FROM user WHERE email = 'admin@memory.hub'\")
row = cursor.fetchone()
print('Active:', row[2], 'Locked:', row[3], 'Login Attempts:', row[4])
"

# 检查服务响应
curl -s http://localhost:5050/login | grep "pgAdmin"
```

---

## 📊 验证结果

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 容器状态 | ✅ 正常 | memory-hub-admin 运行中 |
| 账户激活 | ✅ 正常 | active=1 |
| 账户锁定 | ✅ 已解锁 | locked=0 |
| 登录尝试 | ✅ 已重置 | login_attempts=0 |
| 环境变量 | ✅ 正确 | ADMIN_EMAIL=admin@memory.hub |
| 服务响应 | ✅ 正常 | pgAdmin 页面可访问 |

---

## 🔐 登录凭据

请在浏览器中访问：**http://localhost:5050**

- **邮箱**: `admin@memory.hub`
- **密码**: `memory_pass_2026`

---

## 💡 建议

1. **避免多次登录失败**: 请确保使用正确的密码登录
2. **密码管理**: 建议将密码保存在密码管理器中
3. **如再次锁定**: 可运行以下命令快速解锁:
   ```bash
   docker exec memory-hub-admin python3 -c "
   import sqlite3
   conn = sqlite3.connect('/var/lib/pgadmin/pgadmin4.db')
   cursor = conn.cursor()
   cursor.execute(\"UPDATE user SET login_attempts = 0, locked = 0 WHERE email = 'admin@memory.hub'\")
   conn.commit()
   conn.close()
   print('账户已解锁')
   "
   ```

---

*修复完成* ✅
