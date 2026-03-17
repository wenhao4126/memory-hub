#!/bin/bash
# ============================================================
# 归档历史查询脚本
# ============================================================
# 功能：
#   - 列出所有已归档的项目
#   - 显示归档时间、文件大小
# 作者：小码 🟡
# 日期：2026-03-16
# 
# 用法：
#   bash scripts/list-archives.sh [--detailed]
#
# 示例：
#   bash scripts/list-archives.sh
#   bash scripts/list-archives.sh --detailed
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

ARCHIVE_DIR="${ARCHIVE_DIR:-/home/wen/archives/projects}"

# ============================================================
# 颜色输出
# ============================================================
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ============================================================
# 辅助函数
# ============================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

run_sql() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "$1"
}

run_sql_table() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$1"
}

# 格式化文件大小
format_size() {
    local bytes=$1
    if [ $bytes -ge 1073741824 ]; then
        echo "$(echo "scale=2; $bytes / 1073741824" | bc) GB"
    elif [ $bytes -ge 1048576 ]; then
        echo "$(echo "scale=2; $bytes / 1048576" | bc) MB"
    elif [ $bytes -ge 1024 ]; then
        echo "$(echo "scale=2; $bytes / 1024" | bc) KB"
    else
        echo "$bytes B"
    fi
}

# ============================================================
# 主流程
# ============================================================

DETAILED=false
if [ "$1" == "--detailed" ] || [ "$1" == "-d" ]; then
    DETAILED=true
fi

echo ""
echo "========================================"
echo "  归档历史"
echo "========================================"
echo ""

# 检查数据库连接
if ! run_sql "SELECT 1" > /dev/null 2>&1; then
    echo -e "${RED}[ERROR]${NC} 无法连接到数据库"
    exit 1
fi

# 检查归档历史表是否存在
TABLE_EXISTS=$(run_sql "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'archive_history'")

if [ "$TABLE_EXISTS" -eq 0 ]; then
    echo "⚠️  归档历史表不存在"
    echo "   请先执行 database/03_add_project_id.sql 创建表"
    echo ""
    
    # 检查归档目录是否有文件
    if [ -d "$ARCHIVE_DIR" ]; then
        ARCHIVE_FILES=$(ls -1 "$ARCHIVE_DIR"/*.tar.gz 2>/dev/null | wc -l)
        if [ "$ARCHIVE_FILES" -gt 0 ]; then
            echo "📁 归档目录中有 $ARCHIVE_FILES 个归档文件:"
            ls -lh "$ARCHIVE_DIR"/*.tar.gz 2>/dev/null
        else
            echo "📁 归档目录为空: $ARCHIVE_DIR"
        fi
    else
        echo "📁 归档目录不存在: $ARCHIVE_DIR"
    fi
    exit 0
fi

# 查询归档历史
log_info "正在查询归档历史..."
echo ""

if [ "$DETAILED" = true ]; then
    # 详细模式
    run_sql_table "
    SELECT 
        project_id AS 项目ID,
        archive_file AS 归档文件,
        task_count AS 任务数,
        pg_size_pretty(file_size::bigint) AS 文件大小,
        TO_CHAR(archived_at, 'YYYY-MM-DD HH24:MI:SS') AS 归档时间,
        archived_by AS 归档方式
    FROM archive_history
    ORDER BY archived_at DESC
    "
else
    # 简洁模式
    run_sql_table "
    SELECT 
        project_id AS 项目ID,
        task_count AS 任务数,
        pg_size_pretty(file_size::bigint) AS 文件大小,
        TO_CHAR(archived_at, 'YYYY-MM-DD HH24:MI') AS 归档时间
    FROM archive_history
    ORDER BY archived_at DESC
    "
fi

echo ""

# 显示归档文件目录信息
if [ -d "$ARCHIVE_DIR" ]; then
    ARCHIVE_COUNT=$(ls -1 "$ARCHIVE_DIR"/*.tar.gz 2>/dev/null | wc -l)
    if [ "$ARCHIVE_COUNT" -gt 0 ]; then
        TOTAL_SIZE=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1)
        echo "📁 归档目录: $ARCHIVE_DIR"
        echo "   - 归档文件数: $ARCHIVE_COUNT"
        echo "   - 总大小: $TOTAL_SIZE"
        echo ""
        
        if [ "$DETAILED" = true ]; then
            echo "📂 归档文件列表:"
            ls -lh "$ARCHIVE_DIR"/*.tar.gz 2>/dev/null | awk '{print "   " $NF ": " $5}'
            echo ""
        fi
    fi
fi

# 汇总信息
TOTAL_ARCHIVES=$(run_sql "SELECT COUNT(*) FROM archive_history")
TOTAL_TASKS_ARCHIVED=$(run_sql "SELECT COALESCE(SUM(task_count), 0) FROM archive_history")
TOTAL_SIZE_ARCHIVED=$(run_sql "SELECT COALESCE(SUM(file_size), 0) FROM archive_history")

echo "========================================"
echo "  汇总"
echo "========================================"
echo ""
echo "📊 归档统计:"
echo "  - 归档次数: $TOTAL_ARCHIVES"
echo "  - 已归档任务: $TOTAL_TASKS_ARCHIVED"
if [ "$TOTAL_SIZE_ARCHIVED" -gt 0 ]; then
    echo "  - 总文件大小: $(format_size $TOTAL_SIZE_ARCHIVED)"
fi
echo ""
echo "💡 提示:"
echo "  - 使用 --detailed 查看详细信息"
echo "  - 使用 'tar -tzf <归档文件>' 查看归档内容"
echo "  - 使用 'tar -xzf <归档文件> -C <目标目录>' 解压归档"
echo ""