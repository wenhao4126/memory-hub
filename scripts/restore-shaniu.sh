#!/bin/bash

# ============================================================
# 傻妞恢复脚本 - restore-shaniu.sh
# 功能：从备份文件恢复 OpenClaw workspace 和 PostgreSQL 数据库
# 作者：小码（傻妞的手下）
# 创建时间：2026-03-15
# 更新时间：2026-03-15 - 添加 PostgreSQL 数据库恢复
#          2026-03-15 - 更新备份文件匹配规则
#                       匹配格式：shaniu-full-backup-YYYYMMDD-HHMMSS.tar.gz
# ============================================================

set -e  # 遇到错误立即退出

# ============ 配置区域 ============
BACKUP_DIR="/home/wen/tools/openclaw"
WORKSPACE_DIR="/home/wen/.openclaw/workspace"
OPENCLAW_DATA_DIR="/home/wen/.openclaw"
CONFIG_FILE="/home/wen/.openclaw/workspace/config/db-backup.conf"

# ============ 日志函数 ============
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# ============ 加载数据库配置 ============
load_db_config() {
    if [ -f "$CONFIG_FILE" ]; then
        # 安全加载配置文件
        source "$CONFIG_FILE"
        log "数据库配置已加载: $DB_HOST:$DB_PORT/$DB_NAME"
    else
        log "警告：数据库配置文件不存在: $CONFIG_FILE"
        log "将跳过数据库恢复"
        SKIP_DB_RESTORE=true
    fi
}

# ============ 检查 PostgreSQL 工具 ============
check_postgres_tools() {
    if ! command -v psql &> /dev/null; then
        log "警告：psql 未安装，跳过数据库恢复"
        SKIP_DB_RESTORE=true
        return 1
    fi
    
    # 检查数据库连接
    if [ -z "$SKIP_DB_RESTORE" ]; then
        log "检查数据库连接..."
        if PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" &> /dev/null; then
            log "数据库连接正常"
            return 0
        else
            log "警告：无法连接到数据库，跳过数据库恢复"
            log "  主机: $DB_HOST:$DB_PORT"
            log "  数据库: $DB_NAME"
            log "  用户: $DB_USER"
            SKIP_DB_RESTORE=true
            return 1
        fi
    fi
    return 1
}

# ============ 恢复数据库 ============
restore_database() {
    local SQL_FILE="$1"
    
    if [ "$SKIP_DB_RESTORE" = true ]; then
        log "跳过数据库恢复"
        return 0
    fi
    
    if [ ! -f "$SQL_FILE" ]; then
        log "警告：数据库备份文件不存在: $SQL_FILE"
        return 1
    fi
    
    log "开始恢复 PostgreSQL 数据库..."
    log "警告：此操作将覆盖数据库 $DB_NAME 的数据！"
    echo ""
    read -p "确认要恢复数据库吗？输入 'yes' 继续，其他任意键跳过: " db_confirm
    
    if [ "$db_confirm" != "yes" ]; then
        log "用户取消数据库恢复，跳过..."
        return 0
    fi
    
    # 执行恢复
    log "正在恢复数据库..."
    
    if PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -f "$SQL_FILE" \
        -v ON_ERROR_STOP=0 \
        > /dev/null 2>&1; then
        
        log "数据库恢复成功！"
        return 0
    else
        log "警告：数据库恢复过程中出现错误（可能包含可忽略的警告）"
        log "请检查数据库数据是否正确恢复"
        return 0
    fi
}

# ============ 步骤 1：检查备份目录 ============
log "步骤 1：检查备份目录..."
if [ ! -d "$BACKUP_DIR" ]; then
    log "错误：备份目录不存在: $BACKUP_DIR"
    exit 1
fi

# ============ 步骤 2：列出可用备份 ============
log "步骤 2：扫描可用备份文件..."
cd "$BACKUP_DIR"

# 检查是否有备份文件
BACKUP_FILES=($(ls -1t shaniu-full-backup-*.tar.gz 2>/dev/null))

if [ ${#BACKUP_FILES[@]} -eq 0 ]; then
    log "错误：未找到任何备份文件！"
    log "请先运行备份脚本创建备份。"
    exit 1
fi

log "找到 ${#BACKUP_FILES[@]} 个备份文件："
echo ""
echo "序号 | 备份文件                              | 大小    | 修改时间"
echo "-----|---------------------------------------|---------|------------------"

i=1
for backup in "${BACKUP_FILES[@]}"; do
    SIZE=$(du -h "$backup" | cut -f1)
    MTIME=$(stat -c '%y' "$backup" | cut -d'.' -f1)
    printf "  %2d | %-37s | %-7s | %s\n" "$i" "$backup" "$SIZE" "$MTIME"
    ((i++))
done

echo ""

# ============ 步骤 3：用户选择备份 ============
log "步骤 3：选择要恢复的备份"
echo ""
read -p "请输入要恢复的备份序号（1-${#BACKUP_FILES[@]}），或输入 q 退出: " choice

# 检查是否退出
if [ "$choice" = "q" ] || [ "$choice" = "Q" ]; then
    log "用户取消操作，退出。"
    exit 0
fi

# 验证输入
if ! [[ "$choice" =~ ^[0-9]+$ ]]; then
    log "错误：请输入有效的数字！"
    exit 1
fi

if [ "$choice" -lt 1 ] || [ "$choice" -gt ${#BACKUP_FILES[@]} ]; then
    log "错误：序号超出范围，请输入 1-${#BACKUP_FILES[@]} 之间的数字！"
    exit 1
fi

# 获取选中的备份文件（数组索引从 0 开始）
SELECTED_INDEX=$((choice - 1))
SELECTED_BACKUP="${BACKUP_FILES[$SELECTED_INDEX]}"

log "您选择了: $SELECTED_BACKUP"

# ============ 步骤 4：加载数据库配置 ============
log "步骤 4：加载数据库配置..."
load_db_config

# ============ 步骤 5：确认恢复操作 ============
log "步骤 5：确认恢复操作"
echo ""
echo "=========================================="
echo "⚠️  警告：此操作将覆盖以下内容："
echo "  - 工作区目录: $WORKSPACE_DIR"
echo "  - OpenClaw 数据: $OPENCLAW_DATA_DIR"
if [ "$SKIP_DB_RESTORE" != true ]; then
    echo "  - PostgreSQL 数据库: $DB_NAME"
fi
echo ""
echo "备份文件: $SELECTED_BACKUP"
echo "=========================================="
echo ""

read -p "确认要恢复吗？输入 'yes' 继续，其他任意键取消: " confirm

if [ "$confirm" != "yes" ]; then
    log "用户取消操作，退出。"
    exit 0
fi

# ============ 步骤 6：创建当前数据的安全备份 ============
log "步骤 6：创建当前数据的安全备份..."
SAFETY_BACKUP="${BACKUP_DIR}/pre-restore-$(date +%Y%m%d-%H%M%S).tar.gz"

if [ -d "$WORKSPACE_DIR" ] || [ -d "$OPENCLAW_DATA_DIR" ]; then
    TEMP_SAFETY="${BACKUP_DIR}/temp-safety-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$TEMP_SAFETY"
    
    # 备份当前工作区
    if [ -d "$WORKSPACE_DIR" ]; then
        cp -r "$WORKSPACE_DIR" "$TEMP_SAFETY/workspace" 2>/dev/null || true
    fi
    
    # 备份当前 OpenClaw 数据
    if [ -d "$OPENCLAW_DATA_DIR" ]; then
        mkdir -p "$TEMP_SAFETY/openclaw-data"
        for item in "$OPENCLAW_DATA_DIR"/*.json "$OPENCLAW_DATA_DIR"/sessions "$OPENCLAW_DATA_DIR"/agent "$OPENCLAW_DATA_DIR"/db; do
            if [ -e "$item" ]; then
                cp -r "$item" "$TEMP_SAFETY/openclaw-data/" 2>/dev/null || true
            fi
        done
    fi
    
    # 备份当前数据库
    if [ "$SKIP_DB_RESTORE" != true ]; then
        if PGPASSWORD="$DB_PASSWORD" pg_dump \
            -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            --no-owner --no-privileges --clean --if-exists \
            > "$TEMP_SAFETY/database-backup.sql" 2>/dev/null; then
            log "当前数据库已备份到安全备份"
        fi
    fi
    
    tar -czf "$SAFETY_BACKUP" -C "$TEMP_SAFETY" .
    rm -rf "$TEMP_SAFETY"
    log "安全备份已创建: $SAFETY_BACKUP"
else
    log "当前无可备份的数据，跳过安全备份。"
fi

# ============ 步骤 7：执行恢复 ============
log "步骤 7：开始恢复数据..."

# 创建临时解压目录
TEMP_RESTORE="${BACKUP_DIR}/temp-restore-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$TEMP_RESTORE"

# 解压备份文件
log "解压备份文件..."
tar -xzf "$SELECTED_BACKUP" -C "$TEMP_RESTORE"

# 恢复工作区
if [ -d "$TEMP_RESTORE/workspace" ]; then
    log "恢复工作区目录..."
    # 如果目标目录存在，先备份后删除
    if [ -d "$WORKSPACE_DIR" ]; then
        log "清理旧工作区目录..."
    fi
    mkdir -p "$WORKSPACE_DIR"
    rsync -a --delete "$TEMP_RESTORE/workspace/" "$WORKSPACE_DIR/" 2>/dev/null || \
        cp -r "$TEMP_RESTORE/workspace/"* "$WORKSPACE_DIR/"
    log "工作区恢复完成"
fi

# 恢复 OpenClaw 数据
if [ -d "$TEMP_RESTORE/openclaw-data" ]; then
    log "恢复 OpenClaw 数据..."
    
    # 恢复 JSON 配置文件
    for json_file in "$TEMP_RESTORE/openclaw-data"/*.json; do
        if [ -f "$json_file" ]; then
            cp "$json_file" "$OPENCLAW_DATA_DIR/"
            log "  - $(basename "$json_file") 已恢复"
        fi
    done
    
    # 恢复 sessions 目录
    if [ -d "$TEMP_RESTORE/openclaw-data/sessions" ]; then
        mkdir -p "$OPENCLAW_DATA_DIR/sessions"
        rsync -a "$TEMP_RESTORE/openclaw-data/sessions/" "$OPENCLAW_DATA_DIR/sessions/" 2>/dev/null || \
            cp -r "$TEMP_RESTORE/openclaw-data/sessions/"* "$OPENCLAW_DATA_DIR/sessions/"
        log "  - sessions 目录已恢复"
    fi
    
    # 恢复 agent 目录
    if [ -d "$TEMP_RESTORE/openclaw-data/agent" ]; then
        mkdir -p "$OPENCLAW_DATA_DIR/agent"
        rsync -a "$TEMP_RESTORE/openclaw-data/agent/" "$OPENCLAW_DATA_DIR/agent/" 2>/dev/null || \
            cp -r "$TEMP_RESTORE/openclaw-data/agent/"* "$OPENCLAW_DATA_DIR/agent/"
        log "  - agent 目录已恢复"
    fi
    
    # 恢复 db 目录
    if [ -d "$TEMP_RESTORE/openclaw-data/db" ]; then
        mkdir -p "$OPENCLAW_DATA_DIR/db"
        rsync -a "$TEMP_RESTORE/openclaw-data/db/" "$OPENCLAW_DATA_DIR/db/" 2>/dev/null || \
            cp -r "$TEMP_RESTORE/openclaw-data/db/"* "$OPENCLAW_DATA_DIR/db/"
        log "  - db 目录已恢复"
    fi
fi

# ============ 步骤 8：恢复数据库 ============
log "步骤 8：检查数据库备份..."
DB_BACKUP_FILE=""

# 查找数据库备份文件
if [ -d "$TEMP_RESTORE/database" ]; then
    DB_BACKUP_FILE=$(find "$TEMP_RESTORE/database" -name "db-backup-*.sql" | head -n 1)
fi

if [ -n "$DB_BACKUP_FILE" ] && [ -f "$DB_BACKUP_FILE" ]; then
    log "发现数据库备份文件: $(basename "$DB_BACKUP_FILE")"
    DB_SIZE=$(du -h "$DB_BACKUP_FILE" | cut -f1)
    log "数据库备份大小: $DB_SIZE"
    
    # 检查数据库连接
    check_postgres_tools
    
    # 恢复数据库
    restore_database "$DB_BACKUP_FILE"
else
    log "未发现数据库备份文件，跳过数据库恢复"
fi

# 清理临时目录
rm -rf "$TEMP_RESTORE"
log "临时文件已清理"

# ============ 完成 ============
log "=========================================="
log "恢复完成！"
log ""
log "恢复的备份: $SELECTED_BACKUP"
log "工作区目录: $WORKSPACE_DIR"
log "OpenClaw 数据: $OPENCLAW_DATA_DIR"
if [ -n "$DB_BACKUP_FILE" ] && [ "$SKIP_DB_RESTORE" != true ]; then
    log "数据库: $DB_HOST:$DB_PORT/$DB_NAME"
fi
log ""
if [ -f "$SAFETY_BACKUP" ]; then
    log "恢复前的安全备份: $SAFETY_BACKUP"
    log "（如需回滚，可使用此备份恢复）"
fi
log "=========================================="
log ""
log "⚠️  建议：请重启 OpenClaw 服务以使更改生效"
log "    命令: openclaw gateway restart"