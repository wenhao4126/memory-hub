#!/bin/bash
# ============================================================
# 多智能体记忆中枢 - 数据库备份脚本
# ============================================================
# 用法: ./scripts/backup.sh [操作]
# 操作: create | restore | list | clean
# 作者：小码
# 日期：2026-03-06
# ============================================================

set -e

# ============================================================
# 颜色定义
# ============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================
# 项目根目录
# ============================================================
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# ============================================================
# 配置
# ============================================================
BACKUP_DIR="./backups"
DB_CONTAINER="memory-hub-db"
DB_USER="memory_user"
DB_NAME="memory_hub"

# ============================================================
# 打印函数
# ============================================================
print_info() { echo -e "${BLUE}ℹ ${NC}$1"; }
print_success() { echo -e "${GREEN}✓ ${NC}$1"; }
print_warning() { echo -e "${YELLOW}⚠ ${NC}$1"; }
print_error() { echo -e "${RED}✗ ${NC}$1"; }

# ============================================================
# 创建备份
# ============================================================
create_backup() {
    print_info "创建数据库备份..."
    
    # 创建备份目录
    mkdir -p "$BACKUP_DIR"
    
    # 生成备份文件名
    BACKUP_FILE="$BACKUP_DIR/memory_hub_$(date +%Y%m%d_%H%M%S).sql"
    
    # 检查数据库是否运行
    if ! docker ps | grep -q "$DB_CONTAINER"; then
        print_error "数据库容器未运行"
        print_info "请先启动服务: ./scripts/start.sh start"
        exit 1
    fi
    
    # 执行备份
    print_info "正在备份数据库..."
    docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"
    
    # 压缩备份
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    # 显示备份信息
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    print_success "备份完成: $BACKUP_FILE ($BACKUP_SIZE)"
}

# ============================================================
# 恢复备份
# ============================================================
restore_backup() {
    print_info "恢复数据库备份..."
    
    # 列出可用备份
    list_backups
    
    # 选择备份文件
    echo ""
    read -p "请输入备份文件名（不含路径）: " BACKUP_NAME
    
    BACKUP_FILE="$BACKUP_DIR/$BACKUP_NAME"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "备份文件不存在: $BACKUP_FILE"
        exit 1
    fi
    
    # 确认恢复
    print_warning "⚠️  这将覆盖当前数据库！"
    read -p "确定要恢复吗？(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_info "操作已取消"
        exit 0
    fi
    
    # 检查数据库是否运行
    if ! docker ps | grep -q "$DB_CONTAINER"; then
        print_error "数据库容器未运行"
        exit 1
    fi
    
    # 解压（如果是压缩文件）
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        print_info "解压备份文件..."
        gunzip -c "$BACKUP_FILE" > /tmp/restore.sql
        SQL_FILE="/tmp/restore.sql"
    else
        SQL_FILE="$BACKUP_FILE"
    fi
    
    # 恢复数据库
    print_info "正在恢复数据库..."
    cat "$SQL_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" "$DB_NAME"
    
    # 清理临时文件
    if [ -f /tmp/restore.sql ]; then
        rm /tmp/restore.sql
    fi
    
    print_success "数据库恢复完成"
}

# ============================================================
# 列出备份
# ============================================================
list_backups() {
    print_info "可用备份列表:"
    echo ""
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_warning "备份目录不存在"
        return
    fi
    
    # 列出备份文件
    if ls "$BACKUP_DIR"/*.sql.gz 1> /dev/null 2>&1; then
        echo -e "${CYAN}文件名                              大小    日期${NC}"
        echo "------------------------------------------------------------"
        for file in "$BACKUP_DIR"/*.sql.gz; do
            SIZE=$(du -h "$file" | cut -f1)
            DATE=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
            NAME=$(basename "$file")
            printf "%-36s %-7s %s\n" "$NAME" "$SIZE" "$DATE"
        done
    else
        print_warning "没有找到备份文件"
    fi
}

# ============================================================
# 清理旧备份
# ============================================================
clean_backups() {
    print_info "清理旧备份..."
    
    # 保留最近 N 个备份
    KEEP_COUNT=${1:-5}
    
    print_info "将保留最近 $KEEP_COUNT 个备份"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_warning "备份目录不存在"
        exit 0
    fi
    
    # 计算要删除的数量
    TOTAL=$(ls -1 "$BACKUP_DIR"/*.sql.gz 2>/dev/null | wc -l)
    DELETE_COUNT=$((TOTAL - KEEP_COUNT))
    
    if [ $DELETE_COUNT -le 0 ]; then
        print_success "无需清理，当前备份数量: $TOTAL"
        exit 0
    fi
    
    print_warning "将删除 $DELETE_COUNT 个旧备份"
    read -p "确认清理？(yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "操作已取消"
        exit 0
    fi
    
    # 删除旧备份
    ls -1t "$BACKUP_DIR"/*.sql.gz | tail -n $DELETE_COUNT | xargs rm -f
    
    print_success "清理完成，保留 $KEEP_COUNT 个备份"
}

# ============================================================
# 显示帮助
# ============================================================
show_help() {
    echo "多智能体记忆中枢 - 备份脚本"
    echo ""
    echo "用法: $0 [操作]"
    echo ""
    echo "操作:"
    echo "  create      创建备份"
    echo "  restore     恢复备份"
    echo "  list        列出备份"
    echo "  clean [N]   清理旧备份（保留最近 N 个，默认 5）"
    echo "  help        显示帮助"
    echo ""
    echo "示例:"
    echo "  $0 create       # 创建备份"
    echo "  $0 restore      # 恢复备份"
    echo "  $0 list         # 列出所有备份"
    echo "  $0 clean 10     # 清理旧备份，保留最近 10 个"
}

# ============================================================
# 主入口
# ============================================================
case "${1:-help}" in
    create)
        create_backup
        ;;
    restore)
        restore_backup
        ;;
    list)
        list_backups
        ;;
    clean)
        clean_backups "${2:-5}"
        ;;
    help|*)
        show_help
        ;;
esac