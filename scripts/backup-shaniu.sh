#!/bin/bash

# ============================================================
# 傻妞备份脚本 - backup-shaniu.sh
# 功能：备份 OpenClaw workspace 和 PostgreSQL 数据库
# 作者：小码（傻妞的手下）
# 创建时间：2026-03-15
# 更新时间：2026-03-15 - 添加 PostgreSQL 数据库备份
#          2026-03-15 - 修改备份文件命名规则
#                       格式：shaniu-full-backup-YYYYMMDD-HHMMSS.tar.gz
#                       说明：shaniu=傻妞, full=完整备份
# ============================================================

set -e  # 遇到错误立即退出

# ============ 配置区域 ============
WORKSPACE_DIR="/home/wen/.openclaw/workspace"
OPENCLAW_DATA_DIR="/home/wen/.openclaw"
BACKUP_DIR="/home/wen/tools/openclaw"
CONFIG_FILE="/home/wen/.openclaw/workspace/config/db-backup.conf"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/shaniu-full-backup-${TIMESTAMP}.tar.gz"
MAX_BACKUPS=4  # 保留最近 4 个备份

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
        log "将跳过数据库备份"
        SKIP_DB_BACKUP=true
    fi
}

# ============ 检查 PostgreSQL 工具 ============
check_postgres_tools() {
    if ! command -v pg_dump &> /dev/null; then
        log "警告：pg_dump 未安装，跳过数据库备份"
        SKIP_DB_BACKUP=true
        return 1
    fi
    
    # 检查数据库连接
    if [ -z "$SKIP_DB_BACKUP" ]; then
        log "检查数据库连接..."
        if PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" &> /dev/null; then
            log "数据库连接正常"
            return 0
        else
            log "警告：无法连接到数据库，跳过数据库备份"
            log "  主机: $DB_HOST:$DB_PORT"
            log "  数据库: $DB_NAME"
            log "  用户: $DB_USER"
            SKIP_DB_BACKUP=true
            return 1
        fi
    fi
    return 1
}

# ============ 备份数据库 ============
backup_database() {
    if [ "$SKIP_DB_BACKUP" = true ]; then
        log "跳过数据库备份"
        return 0
    fi
    
    log "开始备份 PostgreSQL 数据库..."
    
    DB_BACKUP_FILE="${BACKUP_DIR}/db-backup-${TIMESTAMP}.sql"
    
    # 使用 PGPASSWORD 环境变量避免交互式输入密码
    if PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-owner \
        --no-privileges \
        --clean \
        --if-exists \
        > "$DB_BACKUP_FILE" 2>/dev/null; then
        
        DB_SIZE=$(du -h "$DB_BACKUP_FILE" | cut -f1)
        log "数据库备份成功: $DB_BACKUP_FILE ($DB_SIZE)"
        
        # 验证备份文件不为空
        if [ ! -s "$DB_BACKUP_FILE" ]; then
            log "警告：数据库备份文件为空，可能数据库无数据"
        fi
        
        return 0
    else
        log "错误：数据库备份失败！"
        rm -f "$DB_BACKUP_FILE"
        return 1
    fi
}

# ============ 步骤 1：检查并创建备份目录 ============
log "步骤 1：检查备份目录..."
if [ ! -d "$BACKUP_DIR" ]; then
    log "备份目录不存在，正在创建: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    log "备份目录创建成功"
else
    log "备份目录已存在: $BACKUP_DIR"
fi

# ============ 步骤 2：加载数据库配置 ============
log "步骤 2：加载数据库配置..."
load_db_config

# ============ 步骤 3：检查数据库连接 ============
log "步骤 3：检查数据库连接..."
check_postgres_tools

# ============ 步骤 4：备份数据库 ============
log "步骤 4：备份数据库..."
backup_database

# ============ 步骤 5：准备备份内容 ============
log "步骤 5：准备备份内容..."

# 检查要备份的目录是否存在
if [ ! -d "$WORKSPACE_DIR" ]; then
    log "错误：工作区目录不存在: $WORKSPACE_DIR"
    exit 1
fi

if [ ! -d "$OPENCLAW_DATA_DIR" ]; then
    log "错误：OpenClaw 数据目录不存在: $OPENCLAW_DATA_DIR"
    exit 1
fi

log "备份内容："
log "  - 工作区: $WORKSPACE_DIR"
log "  - OpenClaw 数据: $OPENCLAW_DATA_DIR"
if [ "$SKIP_DB_BACKUP" != true ] && [ -f "$DB_BACKUP_FILE" ]; then
    log "  - PostgreSQL 数据库: $DB_NAME"
fi

# 创建临时目录用于组织备份内容
TEMP_BACKUP_DIR="${BACKUP_DIR}/temp-backup-${TIMESTAMP}"
mkdir -p "$TEMP_BACKUP_DIR"

# 复制工作区（排除临时文件和缓存）
log "复制工作区文件..."
rsync -a --exclude='*.log' --exclude='node_modules' --exclude='.git' \
    "$WORKSPACE_DIR/" "$TEMP_BACKUP_DIR/workspace/" 2>/dev/null || \
    cp -r "$WORKSPACE_DIR" "$TEMP_BACKUP_DIR/workspace"

# 复制 OpenClaw 数据目录中的关键文件
log "复制 OpenClaw 数据文件..."
mkdir -p "$TEMP_BACKUP_DIR/openclaw-data"

# 备份 openclaw.json 配置文件
if [ -f "$OPENCLAW_DATA_DIR/openclaw.json" ]; then
    cp "$OPENCLAW_DATA_DIR/openclaw.json" "$TEMP_BACKUP_DIR/openclaw-data/"
    log "  - openclaw.json 已备份"
fi

# 备份 sessions 目录（会话数据）
if [ -d "$OPENCLAW_DATA_DIR/sessions" ]; then
    cp -r "$OPENCLAW_DATA_DIR/sessions" "$TEMP_BACKUP_DIR/openclaw-data/"
    log "  - sessions 目录已备份"
fi

# 备份 agent 目录（如果有）
if [ -d "$OPENCLAW_DATA_DIR/agent" ]; then
    cp -r "$OPENCLAW_DATA_DIR/agent" "$TEMP_BACKUP_DIR/openclaw-data/"
    log "  - agent 目录已备份"
fi

# 备份 db 目录（如果有数据库文件）
if [ -d "$OPENCLAW_DATA_DIR/db" ]; then
    cp -r "$OPENCLAW_DATA_DIR/db" "$TEMP_BACKUP_DIR/openclaw-data/"
    log "  - db 目录已备份"
fi

# 备份其他可能的配置文件
for file in "$OPENCLAW_DATA_DIR"/*.json "$OPENCLAW_DATA_DIR"/*.yaml "$OPENCLAW_DATA_DIR"/*.yml; do
    if [ -f "$file" ]; then
        cp "$file" "$TEMP_BACKUP_DIR/openclaw-data/" 2>/dev/null || true
        log "  - $(basename "$file") 已备份"
    fi
done

# ============ 步骤 6：复制数据库备份文件 ============
if [ "$SKIP_DB_BACKUP" != true ] && [ -f "$DB_BACKUP_FILE" ]; then
    log "复制数据库备份文件到临时目录..."
    mkdir -p "$TEMP_BACKUP_DIR/database"
    cp "$DB_BACKUP_FILE" "$TEMP_BACKUP_DIR/database/"
    log "  - $(basename "$DB_BACKUP_FILE") 已添加到备份"
fi

# ============ 步骤 7：打包压缩 ============
log "步骤 7：打包压缩备份文件..."
tar -czf "$BACKUP_FILE" -C "$TEMP_BACKUP_DIR" .

# 计算备份文件大小
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "备份文件创建成功: $BACKUP_FILE"
log "备份文件大小: $BACKUP_SIZE"

# 清理临时目录
rm -rf "$TEMP_BACKUP_DIR"
log "临时文件已清理"

# 清理数据库备份文件（已经打包进 tar.gz）
if [ "$SKIP_DB_BACKUP" != true ] && [ -f "$DB_BACKUP_FILE" ]; then
    rm -f "$DB_BACKUP_FILE"
    log "数据库备份临时文件已清理"
fi

# ============ 步骤 8：清理旧备份 ============
log "步骤 8：清理旧备份文件..."
cd "$BACKUP_DIR"

# 列出所有备份文件（按时间排序，旧的在前）
BACKUP_COUNT=$(ls -1 shaniu-full-backup-*.tar.gz 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    # 计算需要删除的数量
    DELETE_COUNT=$((BACKUP_COUNT - MAX_BACKUPS))
    log "当前有 $BACKUP_COUNT 个备份，保留最近 $MAX_BACKUPS 个"
    log "将删除 $DELETE_COUNT 个旧备份..."
    
    # 删除最旧的备份
    ls -1t shaniu-full-backup-*.tar.gz | tail -n "$DELETE_COUNT" | while read old_backup; do
        rm "$old_backup"
        log "已删除旧备份: $old_backup"
    done
else
    log "当前备份数量: $BACKUP_COUNT，无需清理"
fi

# ============ 步骤 9：输出备份列表 ============
log "步骤 9：当前备份列表："
ls -lh shaniu-full-backup-*.tar.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}' || log "  暂无备份文件"

# ============ 完成 ============
log "=========================================="
log "备份完成！"
log "备份文件: $BACKUP_FILE"
log "文件大小: $BACKUP_SIZE"
if [ "$SKIP_DB_BACKUP" = true ]; then
    log "⚠️  注意：数据库备份已跳过（连接失败或工具未安装）"
fi
log "=========================================="