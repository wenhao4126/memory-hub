#!/bin/bash
# ============================================================
# 项目列表查询脚本
# ============================================================
# 功能：
#   - 列出所有有任务的项目
#   - 显示每个项目的任务数、完成状态
#   - 帮助决定归档哪个项目
# 作者：小码 🟡
# 日期：2026-03-16
# 
# 用法：
#   bash scripts/list-projects.sh [--verbose]
#
# 示例：
#   bash scripts/list-projects.sh
#   bash scripts/list-projects.sh --verbose
# ============================================================

set -e

# ============================================================
# 配置变量
# ============================================================

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-memory_hub}"
DB_USER="${DB_USER:-memory_user}"
DB_PASSWORD="${DB_PASSWORD:-memory_pass_2026}"

# ============================================================
# 颜色输出
# ============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================
# 辅助函数
# ============================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

run_sql() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "$1"
}

run_sql_table() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$1"
}

# ============================================================
# 主流程
# ============================================================

VERBOSE=false
if [ "$1" == "--verbose" ] || [ "$1" == "-v" ]; then
    VERBOSE=true
fi

echo ""
echo "========================================"
echo "  项目列表"
echo "========================================"
echo ""

# 检查数据库连接
if ! run_sql "SELECT 1" > /dev/null 2>&1; then
    echo -e "${RED}[ERROR]${NC} 无法连接到数据库"
    exit 1
fi

# 查询项目统计
log_info "正在查询项目数据..."
echo ""

# 使用视图查询（如果视图存在）
VIEW_EXISTS=$(run_sql "SELECT COUNT(*) FROM information_schema.views WHERE table_name = 'project_statistics'")

if [ "$VIEW_EXISTS" -gt 0 ]; then
    # 使用视图
    run_sql_table "SELECT * FROM project_statistics"
else
    # 直接查询
    run_sql_table "
    SELECT 
        COALESCE(project_id, '未分配') AS 项目ID,
        COUNT(*) AS 总任务数,
        COUNT(*) FILTER (WHERE status = 'completed') AS 已完成,
        COUNT(*) FILTER (WHERE status = 'failed') AS 已失败,
        COUNT(*) FILTER (WHERE status IN ('pending', 'queued', 'running')) AS 活跃中,
        TO_CHAR(MIN(created_at), 'YYYY-MM-DD HH24:MI') AS 首个任务,
        TO_CHAR(MAX(created_at), 'YYYY-MM-DD HH24:MI') AS 最后任务
    FROM parallel_tasks
    GROUP BY project_id
    ORDER BY COUNT(*) DESC
    "
fi

echo ""

# 显示归档建议
if [ "$VERBOSE" = true ]; then
    echo "========================================"
    echo "  归档建议"
    echo "========================================"
    echo ""
    
    # 查询可归档的项目（已完成任务超过 10 个）
    ARCHIVABLE=$(run_sql_table "
    SELECT 
        project_id AS 项目ID,
        COUNT(*) FILTER (WHERE status = 'completed') AS 已完成,
        COUNT(*) FILTER (WHERE status IN ('pending', 'queued', 'running')) AS 活跃中
    FROM parallel_tasks
    WHERE project_id IS NOT NULL
    GROUP BY project_id
    HAVING COUNT(*) FILTER (WHERE status = 'completed') >= 1
       AND COUNT(*) FILTER (WHERE status IN ('pending', 'queued', 'running')) = 0
    ORDER BY COUNT(*) FILTER (WHERE status = 'completed') DESC
    ")
    
    if [ -n "$ARCHIVABLE" ]; then
        echo "✅ 建议归档的项目（所有任务已完成）："
        echo "$ARCHIVABLE"
        echo ""
        echo "💡 归档命令："
        echo "   bash scripts/archive-project.sh <项目ID>"
    else
        echo "ℹ️  暂无可归档的项目"
        echo "   可归档条件：项目有已完成的任务，且无活跃任务"
    fi
    
    echo ""
    
    # 显示未分配项目的任务数
    UNASSIGNED=$(run_sql "SELECT COUNT(*) FROM parallel_tasks WHERE project_id IS NULL")
    if [ "$UNASSIGNED" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  有 $UNASSIGNED 个任务未分配项目${NC}"
        echo "   建议为这些任务分配 project_id"
        echo ""
        echo "   更新命令示例："
        echo "   UPDATE parallel_tasks SET project_id = 'your-project-id' WHERE project_id IS NULL;"
    fi
fi

# 显示汇总信息
TOTAL_TASKS=$(run_sql "SELECT COUNT(*) FROM parallel_tasks")
TOTAL_PROJECTS=$(run_sql "SELECT COUNT(DISTINCT project_id) FROM parallel_tasks WHERE project_id IS NOT NULL")
TOTAL_UNASSIGNED=$(run_sql "SELECT COUNT(*) FROM parallel_tasks WHERE project_id IS NULL")

echo "========================================"
echo "  汇总"
echo "========================================"
echo ""
echo "📊 统计信息:"
echo "  - 总任务数: $TOTAL_TASKS"
echo "  - 项目数量: $TOTAL_PROJECTS"
echo "  - 未分配任务: $TOTAL_UNASSIGNED"
echo ""
echo "💡 提示:"
echo "  - 使用 --verbose 参数查看归档建议"
echo "  - 使用 archive-project.sh <项目ID> 归档项目"
echo ""