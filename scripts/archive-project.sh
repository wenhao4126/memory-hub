#!/bin/bash
# ============================================================
# 手动归档脚本 - 按项目归档任务数据
# ============================================================
# 功能：
#   - 接收项目 ID 作为参数
#   - 导出项目所有任务到 CSV
#   - 从主表删除已归档的任务
#   - 压缩归档文件
#   - 记录归档历史
# 作者：小码 🟡
# 日期：2026-03-16
# 
# 用法：
#   bash scripts/archive-project.sh <project_id> [--dry-run]
#
# 示例：
#   bash scripts/archive-project.sh memory-hub-phase1
#   bash scripts/archive-project.sh memory-hub-phase1 --dry-run
# ============================================================

set -e  # 遇到错误立即退出

# ============================================================
# 配置变量
# ============================================================

# 数据库连接信息（从环境变量读取或使用默认值）
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-memory_hub}"
DB_USER="${DB_USER:-memory_user}"
DB_PASSWORD="${DB_PASSWORD:-memory_pass_2026}"

# 归档目录
ARCHIVE_DIR="${ARCHIVE_DIR:-/home/wen/archives/projects}"

# ============================================================
# 颜色输出
# ============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# 辅助函数
# ============================================================

# 打印带颜色的消息
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印使用帮助
show_usage() {
    echo ""
    echo "用法: $0 <project_id> [--dry-run]"
    echo ""
    echo "参数:"
    echo "  project_id  要归档的项目 ID（必需）"
    echo "  --dry-run   模拟运行，不实际删除数据"
    echo ""
    echo "示例:"
    echo "  $0 memory-hub-phase1              # 归档 memory-hub-phase1 项目"
    echo "  $0 memory-hub-phase1 --dry-run    # 模拟归档，不删除数据"
    echo ""
    echo "环境变量:"
    echo "  DB_HOST      数据库主机（默认: localhost）"
    echo "  DB_PORT      数据库端口（默认: 5432）"
    echo "  DB_NAME      数据库名称（默认: memory_hub）"
    echo "  DB_USER      数据库用户（默认: memory_user）"
    echo "  DB_PASSWORD  数据库密码（默认: memory_pass_2026）"
    echo "  ARCHIVE_DIR  归档目录（默认: /home/wen/archives/projects）"
    echo ""
}

# 执行 SQL 查询
run_sql() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -c "$1"
}

# 执行 SQL 命令（带输出）
run_sql_verbose() {
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$1"
}

# 检查数据库连接
check_db_connection() {
    if ! run_sql "SELECT 1" > /dev/null 2>&1; then
        log_error "无法连接到数据库"
        log_error "请检查数据库连接信息: $DB_HOST:$DB_PORT/$DB_NAME"
        exit 1
    fi
    log_success "数据库连接成功"
}

# ============================================================
# 主流程
# ============================================================

# 检查参数
if [ $# -lt 1 ]; then
    log_error "缺少参数：project_id"
    show_usage
    exit 1
fi

PROJECT_ID="$1"
DRY_RUN=false

# 检查是否是模拟运行
if [ "$2" == "--dry-run" ]; then
    DRY_RUN=true
    log_warning "🔍 模拟运行模式：不会实际删除数据"
fi

# 打印开始信息
echo ""
echo "========================================"
echo "  手动归档工具"
echo "========================================"
echo ""
log_info "项目 ID: $PROJECT_ID"
log_info "归档目录: $ARCHIVE_DIR"
echo ""

# 检查数据库连接
check_db_connection

# 检查项目是否存在
TASK_COUNT=$(run_sql "SELECT COUNT(*) FROM parallel_tasks WHERE project_id = '$PROJECT_ID'")
if [ "$TASK_COUNT" -eq 0 ]; then
    log_error "项目 '$PROJECT_ID' 没有任何任务"
    log_info "使用 list-projects.sh 查看所有项目"
    exit 1
fi

# 获取任务统计
log_info "获取任务统计..."
STATS=$(run_sql "
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    COUNT(*) FILTER (WHERE status IN ('pending', 'queued', 'running')) as active
FROM parallel_tasks 
WHERE project_id = '$PROJECT_ID'
")

TOTAL=$(echo "$STATS" | cut -d'|' -f1)
COMPLETED=$(echo "$STATS" | cut -d'|' -f2)
FAILED=$(echo "$STATS" | cut -d'|' -f3)
ACTIVE=$(echo "$STATS" | cut -d'|' -f4)

echo ""
echo "📊 项目任务统计:"
echo "  - 总任务数: $TOTAL"
echo "  - 已完成: $COMPLETED"
echo "  - 已失败: $FAILED"
echo "  - 活跃中: $ACTIVE"
echo ""

# 检查是否有活跃任务
if [ "$ACTIVE" -gt 0 ]; then
    log_warning "项目有 $ACTIVE 个活跃任务（pending/queued/running）"
    read -p "是否继续归档？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "归档已取消"
        exit 0
    fi
fi

# 创建归档目录
mkdir -p "$ARCHIVE_DIR"

# 生成归档文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CSV_FILE="$ARCHIVE_DIR/${PROJECT_ID}_${TIMESTAMP}.csv"
ARCHIVE_FILE="$ARCHIVE_DIR/${PROJECT_ID}_${TIMESTAMP}.tar.gz"

# ============================================================
# 步骤 1：导出任务到 CSV
# ============================================================
log_info "正在导出任务数据到 CSV..."

# 导出 parallel_tasks 表
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\COPY (
    SELECT * FROM parallel_tasks WHERE project_id = '$PROJECT_ID'
) TO '$CSV_FILE' WITH CSV HEADER"

log_success "CSV 文件已创建: $CSV_FILE"

# 导出任务进度历史（如果有）
HISTORY_FILE="$ARCHIVE_DIR/${PROJECT_ID}_${TIMESTAMP}_history.csv"
HISTORY_COUNT=$(run_sql "
SELECT COUNT(*) FROM task_progress_history 
WHERE task_id IN (SELECT id FROM parallel_tasks WHERE project_id = '$PROJECT_ID')
")

if [ "$HISTORY_COUNT" -gt 0 ]; then
    log_info "正在导出任务进度历史..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\COPY (
        SELECT tph.* FROM task_progress_history tph
        JOIN parallel_tasks pt ON tph.task_id = pt.id
        WHERE pt.project_id = '$PROJECT_ID'
    ) TO '$HISTORY_FILE' WITH CSV HEADER"
    log_success "历史文件已创建: $HISTORY_FILE"
fi

# ============================================================
# 步骤 2：压缩归档文件
# ============================================================
log_info "正在压缩归档文件..."

if [ "$HISTORY_COUNT" -gt 0 ]; then
    tar -czf "$ARCHIVE_FILE" -C "$ARCHIVE_DIR" \
        "$(basename "$CSV_FILE")" \
        "$(basename "$HISTORY_FILE")"
    # 删除原始 CSV 文件
    rm "$CSV_FILE" "$HISTORY_FILE"
else
    tar -czf "$ARCHIVE_FILE" -C "$ARCHIVE_DIR" \
        "$(basename "$CSV_FILE")"
    # 删除原始 CSV 文件
    rm "$CSV_FILE"
fi

ARCHIVE_SIZE=$(stat -c%s "$ARCHIVE_FILE" 2>/dev/null || stat -f%z "$ARCHIVE_FILE" 2>/dev/null)
ARCHIVE_SIZE_MB=$(awk "BEGIN {printf \"%.2f\", $ARCHIVE_SIZE / 1024 / 1024}")

log_success "归档文件已创建: $ARCHIVE_FILE ($ARCHIVE_SIZE_MB MB)"

# ============================================================
# 步骤 3：删除已归档的任务
# ============================================================
if [ "$DRY_RUN" = true ]; then
    log_warning "🔍 模拟运行：跳过删除操作"
else
    log_info "正在从数据库删除已归档的任务..."
    
    # 先删除任务进度历史（外键约束）
    run_sql_verbose "
    DELETE FROM task_progress_history 
    WHERE task_id IN (SELECT id FROM parallel_tasks WHERE project_id = '$PROJECT_ID')
    "
    
    # 删除任务锁（外键约束）
    run_sql_verbose "
    DELETE FROM task_locks 
    WHERE task_id IN (SELECT id FROM parallel_tasks WHERE project_id = '$PROJECT_ID')
    "
    
    # 删除任务
    run_sql_verbose "
    DELETE FROM parallel_tasks WHERE project_id = '$PROJECT_ID'
    "
    
    log_success "已从数据库删除 $TOTAL 个任务"
fi

# ============================================================
# 步骤 4：记录归档历史
# ============================================================
if [ "$DRY_RUN" = false ]; then
    log_info "正在记录归档历史..."
    
    run_sql "
    INSERT INTO archive_history (project_id, archive_file, task_count, file_size, archived_by)
    VALUES ('$PROJECT_ID', '$ARCHIVE_FILE', $TOTAL, $ARCHIVE_SIZE, 'manual')
    "
    
    log_success "归档历史已记录"
fi

# ============================================================
# 输出归档摘要
# ============================================================
echo ""
echo "========================================"
echo "  归档完成！"
echo "========================================"
echo ""
echo "📁 归档信息:"
echo "  - 项目 ID: $PROJECT_ID"
echo "  - 归档文件: $ARCHIVE_FILE"
echo "  - 文件大小: $ARCHIVE_SIZE_MB MB"
echo "  - 任务数量: $TOTAL"
echo "  - 归档时间: $(date '+%Y-%m-%d %H:%M:%S')"
if [ "$DRY_RUN" = true ]; then
    echo "  - 模式: 模拟运行（数据未删除）"
fi
echo ""
echo "💡 提示:"
echo "  - 使用 'tar -tzf $ARCHIVE_FILE' 查看归档内容"
echo "  - 使用 'list-archives.sh' 查看归档历史"
echo ""

log_success "归档完成！"