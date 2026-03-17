#!/bin/bash
# ============================================================
# 小码池启动脚本 - Worker Pool Starter
# ============================================================
# 功能：启动多个小码（team-coder1~5）后台 Worker 进程
# 作者：小码 🟡
# 日期：2026-03-16
# 更新：2026-03-16 - 添加 --help 支持
# ============================================================
# 使用方法：
#   bash start-worker-pool.sh [小码数量] [轮询间隔秒数]
#   示例：bash start-worker-pool.sh 5 30
# ============================================================

set -e  # 遇到错误立即退出

# ==================== 帮助信息 ====================
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "============================================================"
    echo "小码池启动脚本 - Worker Pool Starter"
    echo "============================================================"
    echo ""
    echo "用法："
    echo "  $0 [小码数量] [轮询间隔]"
    echo ""
    echo "参数："
    echo "  小码数量     启动的小码数量（默认：5）"
    echo "  轮询间隔     轮询间隔秒数（默认：30）"
    echo ""
    echo "选项："
    echo "  -h, --help   显示此帮助信息"
    echo ""
    echo "示例："
    echo "  $0           # 启动 5 个小码，30 秒轮询（默认）"
    echo "  $0 3         # 启动 3 个小码，30 秒轮询"
    echo "  $0 5 60      # 启动 5 个小码，60 秒轮询"
    echo "  $0 --help    # 显示帮助信息"
    echo ""
    echo "相关脚本："
    echo "  scripts/stop-worker-pool.sh    停止所有小码"
    echo "  scripts/worker-status.sh       查看小码状态"
    echo ""
    echo "日志位置："
    echo "  /home/wen/projects/memory-hub/logs/worker-*.log"
    echo ""
    exit 0
fi

# ==================== 配置 ====================
WORKER_COUNT=${1:-5}       # 默认启动 5 个小码
POLL_INTERVAL=${2:-30}     # 默认 30 秒轮询一次
PROJECT_DIR="/home/wen/projects/memory-hub"
WORKER_SCRIPT="$PROJECT_DIR/worker/worker_cli.py"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="/tmp/memory-hub-workers"

# ==================== 颜色输出 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 前置检查 ====================
echo -e "${BLUE}🔍 前置检查...${NC}"

# 检查项目目录
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ 项目目录不存在: $PROJECT_DIR${NC}"
    exit 1
fi

# 检查 worker 脚本
if [ ! -f "$WORKER_SCRIPT" ]; then
    echo -e "${RED}❌ Worker 脚本不存在: $WORKER_SCRIPT${NC}"
    exit 1
fi

# 创建日志目录
mkdir -p "$LOG_DIR"
echo -e "  ${GREEN}✓${NC} 日志目录: $LOG_DIR"

# 创建 PID 目录
mkdir -p "$PID_DIR"
echo -e "  ${GREEN}✓${NC} PID 目录: $PID_DIR"

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ 未找到 Python 环境${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Python: $(python --version)"

# 检查是否已有小码在运行
RUNNING_COUNT=$(ps aux | grep "worker_cli.py" | grep -v grep | wc -l)
if [ "$RUNNING_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  检测到 $RUNNING_COUNT 个小码已在运行${NC}"
    echo -e "  ${YELLOW}提示：如需重启，请先运行 bash scripts/stop-worker-pool.sh${NC}"
    echo ""
    # 检查是否在交互式终端中运行
    if [ -t 0 ]; then
        read -p "是否继续启动新的小码？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}已取消启动${NC}"
            exit 0
        fi
    else
        echo -e "${YELLOW}非交互模式，跳过确认，直接继续启动${NC}"
    fi
fi

# ==================== 启动小码池 ====================
echo ""
echo -e "${GREEN}🚀 启动小码池...${NC}"
echo -e "  小码数量: ${BLUE}$WORKER_COUNT${NC}"
echo -e "  轮询间隔: ${BLUE}${POLL_INTERVAL}秒${NC}"
echo ""

# 启动计数器
SUCCESS_COUNT=0
FAIL_COUNT=0

for i in $(seq 1 $WORKER_COUNT); do
    AGENT_ID="team-coder$i"
    LOG_FILE="$LOG_DIR/worker-$i.log"
    PID_FILE="$PID_DIR/worker-$i.pid"
    
    echo -e "启动小码$i ($AGENT_ID)..."
    
    # 后台运行 worker（使用 nohup，不使用 --daemon 避免二次 fork）
    nohup python "$WORKER_SCRIPT" \
        --agent-id "$AGENT_ID" \
        --poll-interval "$POLL_INTERVAL" \
        --pid-file "$PID_FILE" \
        > "$LOG_FILE" 2>&1 &
    
    WORKER_PID=$!
    
    # 等待进程启动并检查
    sleep 1
    
    # 检查进程是否成功启动（通过 PID 文件或进程列表）
    if [ -f "$PID_FILE" ]; then
        ACTUAL_PID=$(cat "$PID_FILE")
        if ps -p $ACTUAL_PID > /dev/null 2>&1; then
            echo -e "  ${GREEN}✅ 小码$i 已启动${NC} (PID: $ACTUAL_PID)"
            echo -e "     日志: $LOG_FILE"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo -e "  ${RED}❌ 小码$i 启动失败（进程已退出）${NC}"
            echo -e "     请查看日志: $LOG_FILE"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    elif ps -p $WORKER_PID > /dev/null 2>&1; then
        # 备用：检查 nohup 进程
        echo $WORKER_PID > "$PID_FILE"
        echo -e "  ${GREEN}✅ 小码$i 已启动${NC} (PID: $WORKER_PID)"
        echo -e "     日志: $LOG_FILE"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "  ${RED}❌ 小码$i 启动失败${NC}"
        echo -e "     请查看日志: $LOG_FILE"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

# ==================== 启动完成 ====================
echo ""
echo -e "${GREEN}🎉 小码池启动完成！${NC}"
echo -e "  成功: ${GREEN}$SUCCESS_COUNT${NC} 个"
if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "  失败: ${RED}$FAIL_COUNT${NC} 个"
fi
echo ""
echo -e "${BLUE}📌 常用命令：${NC}"
echo ""
echo "  查看所有小码状态："
echo "    ps aux | grep worker_cli"
echo ""
echo "  查看小码日志："
echo "    tail -f $LOG_DIR/worker-*.log"
echo ""
echo "  查看小码池详细状态："
echo "    bash scripts/worker-status.sh"
echo ""
echo "  停止所有小码："
echo "    bash scripts/stop-worker-pool.sh"
echo ""

# 如果有失败的，返回非零退出码
if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi