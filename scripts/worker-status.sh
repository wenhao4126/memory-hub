#!/bin/bash
# ============================================================
# 小码池状态查看脚本 - Worker Pool Status
# ============================================================
# 功能：查看小码池运行状态、任务队列、数据库状态
# 作者：小码 🟡
# 日期：2026-03-16
# ============================================================
# 使用方法：
#   bash worker-status.sh [--full]
#   --full: 显示完整信息（包括最近完成的任务详情）
# ============================================================

set -e  # 遇到错误立即退出

# ==================== 参数解析 ====================
FULL_MODE=false
if [ "$1" == "--full" ]; then
    FULL_MODE=true
fi

# ==================== 配置 ====================
PROJECT_DIR="/home/wen/projects/memory-hub"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="/tmp/memory-hub-workers"
DB_CONTAINER="memory-hub-db"
DB_USER="memory_user"
DB_NAME="memory_hub"

# ==================== 颜色输出 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ==================== 标题 ====================
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║       📊 小码池状态监控面板              ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

# ==================== 1. 运行状态 ====================
echo -e "${BOLD}${BLUE}🤖 运行中的小码${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 获取运行中的进程
RUNNING_WORKERS=$(ps aux | grep "agent_worker.py" | grep -v grep)

if [ -z "$RUNNING_WORKERS" ]; then
    echo -e "  ${YELLOW}⚠️  没有运行中的小码${NC}"
else
    # 格式化输出
    echo "$RUNNING_WORKERS" | while read -r line; do
        PID=$(echo "$line" | awk '{print $2}')
        CPU=$(echo "$line" | awk '{print $3}')
        MEM=$(echo "$line" | awk '{print $4}')
        AGENT_ID=$(echo "$line" | grep -oP '(?<=--agent-id\s)\S+' || echo "unknown")
        
        # 根据资源使用情况设置颜色
        if (( $(echo "$CPU > 50" | bc -l 2>/dev/null || echo 0) )); then
            CPU_COLOR=$RED
        elif (( $(echo "$CPU > 20" | bc -l 2>/dev/null || echo 0) )); then
            CPU_COLOR=$YELLOW
        else
            CPU_COLOR=$GREEN
        fi
        
        if (( $(echo "$MEM > 50" | bc -l 2>/dev/null || echo 0) )); then
            MEM_COLOR=$RED
        elif (( $(echo "$MEM > 20" | bc -l 2>/dev/null || echo 0) )); then
            MEM_COLOR=$YELLOW
        else
            MEM_COLOR=$GREEN
        fi
        
        echo -e "  ${GREEN}●${NC} ${BOLD}$AGENT_ID${NC}"
        echo -e "    PID: ${CYAN}$PID${NC}  CPU: ${CPU_COLOR}${CPU}%${NC}  MEM: ${MEM_COLOR}${MEM}%${NC}"
    done
fi

echo ""

# ==================== 2. 数据库连接检查 ====================
echo -e "${BOLD}${BLUE}🗄️  数据库状态${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查 Docker 容器是否运行
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo -e "  ${RED}❌ 数据库容器未运行: $DB_CONTAINER${NC}"
    echo -e "  ${YELLOW}提示：请先启动数据库${NC}"
    DB_AVAILABLE=false
else
    echo -e "  ${GREEN}✓${NC} 数据库容器运行中"
    DB_AVAILABLE=true
fi

echo ""

# ==================== 3. 任务队列状态 ====================
if [ "$DB_AVAILABLE" = true ]; then
    echo -e "${BOLD}${BLUE}📋 任务队列${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 待处理任务
    PENDING_COUNT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT COUNT(*) FROM parallel_tasks WHERE status='pending';" 2>/dev/null | tr -d ' ')
    echo -e "  待处理: ${YELLOW}$PENDING_COUNT${NC} 个任务"
    
    # 运行中任务
    RUNNING_COUNT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT COUNT(*) FROM parallel_tasks WHERE status='running';" 2>/dev/null | tr -d ' ')
    echo -e "  运行中: ${BLUE}$RUNNING_COUNT${NC} 个任务"
    
    # 已完成（今天）
    COMPLETED_TODAY=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT COUNT(*) FROM parallel_tasks WHERE status='completed' AND completed_at >= CURRENT_DATE;" 2>/dev/null | tr -d ' ')
    echo -e "  今日完成: ${GREEN}$COMPLETED_TODAY${NC} 个任务"
    
    # 失败任务
    FAILED_COUNT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT COUNT(*) FROM parallel_tasks WHERE status='failed';" 2>/dev/null | tr -d ' ')
    if [ "$FAILED_COUNT" -gt 0 ]; then
        echo -e "  失败: ${RED}$FAILED_COUNT${NC} 个任务"
    else
        echo -e "  失败: ${GREEN}0${NC} 个任务"
    fi
    
    echo ""
    
    # ==================== 4. 最近完成的任务 ====================
    if [ "$FULL_MODE" = true ]; then
        echo -e "${BOLD}${BLUE}✅ 最近完成的任务${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
            "SELECT 
                LEFT(title, 40) as title,
                agent_id,
                TO_CHAR(completed_at, 'MM-DD HH24:MI') as time
            FROM parallel_tasks 
            WHERE status='completed' 
            ORDER BY completed_at DESC 
            LIMIT 5;" 2>/dev/null || echo -e "  ${YELLOW}无完成任务记录${NC}"
        
        echo ""
    fi
    
    # ==================== 5. 当前运行的任务详情 ====================
    if [ "$RUNNING_COUNT" -gt 0 ]; then
        echo -e "${BOLD}${BLUE}🔄 运行中任务详情${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
            "SELECT 
                LEFT(title, 30) as title,
                agent_id,
                progress || '%' as progress,
                status_message,
                TO_CHAR(started_at, 'HH24:MI:SS') as started
            FROM parallel_tasks 
            WHERE status='running' 
            ORDER BY started_at DESC;" 2>/dev/null || echo -e "  ${YELLOW}无运行中任务${NC}"
        
        echo ""
    fi
fi

# ==================== 6. 日志文件信息 ====================
echo -e "${BOLD}${BLUE}📝 日志文件${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "$LOG_DIR" ]; then
    LOG_FILES=$(ls -1 "$LOG_DIR"/worker-*.log 2>/dev/null || true)
    
    if [ -z "$LOG_FILES" ]; then
        echo -e "  ${YELLOW}无日志文件${NC}"
    else
        echo "$LOG_FILES" | while read -r log_file; do
            FILENAME=$(basename "$log_file")
            SIZE=$(du -h "$log_file" | cut -f1)
            MODIFIED=$(stat -c %y "$log_file" 2>/dev/null | cut -d'.' -f1)
            
            echo -e "  ${CYAN}$FILENAME${NC} (${SIZE}, 更新: ${MODIFIED})"
        done
        
        echo ""
        echo -e "  ${YELLOW}查看日志:${NC} tail -f $LOG_DIR/worker-*.log"
    fi
else
    echo -e "  ${YELLOW}日志目录不存在: $LOG_DIR${NC}"
fi

echo ""

# ==================== 7. 快捷命令 ====================
echo -e "${BOLD}${BLUE}📌 快捷命令${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  启动小码池: ${CYAN}bash scripts/start-worker-pool.sh 5 30${NC}"
echo -e "  停止小码池: ${CYAN}bash scripts/stop-worker-pool.sh${NC}"
echo -e "  查看完整状态: ${CYAN}bash scripts/worker-status.sh --full${NC}"
echo -e "  查看日志: ${CYAN}tail -f $LOG_DIR/worker-*.log${NC}"
echo ""

# ==================== 返回退出码 ====================
# 如果没有运行中的小码，返回非零
if [ -z "$RUNNING_WORKERS" ]; then
    exit 1
fi