#!/bin/bash
# ============================================================
# 小码池停止脚本 - Worker Pool Stopper
# ============================================================
# 功能：停止所有运行中的小码 Worker 进程
# 作者：小码 🟡
# 日期：2026-03-16
# ============================================================
# 使用方法：
#   bash stop-worker-pool.sh [--force]
#   --force: 强制停止（使用 kill -9）
# ============================================================

set -e  # 遇到错误立即退出

# ==================== 参数解析 ====================
FORCE_KILL=false
if [ "$1" == "--force" ]; then
    FORCE_KILL=true
fi

# ==================== 配置 ====================
PID_DIR="/tmp/memory-hub-workers"

# ==================== 颜色输出 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 查找运行中的小码 ====================
echo -e "${BLUE}🛑 停止小码池...${NC}"
echo ""

# 查找所有 agent_worker 进程
PIDS=$(ps aux | grep "agent_worker.py" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo -e "${YELLOW}❌ 没有运行中的小码${NC}"
    
    # 清理 PID 文件
    if [ -d "$PID_DIR" ]; then
        rm -f "$PID_DIR"/*.pid 2>/dev/null || true
    fi
    
    exit 0
fi

# 统计数量
WORKER_COUNT=$(echo "$PIDS" | wc -l)
echo -e "发现 ${BLUE}$WORKER_COUNT${NC} 个运行中的小码"
echo ""

# ==================== 停止进程 ====================
STOPPED_COUNT=0
FAILED_COUNT=0

for PID in $PIDS; do
    # 获取进程信息
    PROCESS_INFO=$(ps -p $PID -o pid,cmd --no-headers 2>/dev/null || echo "")
    
    if [ -z "$PROCESS_INFO" ]; then
        echo -e "  ${YELLOW}⚠️  进程 $PID 已不存在${NC}"
        continue
    fi
    
    # 提取 agent-id（从命令行参数中）
    AGENT_ID=$(echo "$PROCESS_INFO" | grep -oP '(?<=--agent-id\s)\S+' || echo "unknown")
    
    echo -e "停止进程 $PID ($AGENT_ID)..."
    
    # 发送停止信号
    if [ "$FORCE_KILL" = true ]; then
        kill -9 $PID 2>/dev/null || true
        echo -e "  ${YELLOW}⚡ 强制停止${NC}"
    else
        kill $PID 2>/dev/null || true
    fi
    
    # 等待进程结束（最多 5 秒）
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done
    
    # 检查是否成功停止
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "  ${RED}❌ 停止失败，请尝试 --force${NC}"
        ((FAILED_COUNT++))
    else
        echo -e "  ${GREEN}✅ 已停止${NC}"
        ((STOPPED_COUNT++))
    fi
done

# ==================== 清理 PID 文件 ====================
if [ -d "$PID_DIR" ]; then
    echo ""
    echo "清理 PID 文件..."
    rm -f "$PID_DIR"/*.pid 2>/dev/null || true
fi

# ==================== 停止完成 ====================
echo ""
echo -e "${GREEN}✅ 小码池停止完成！${NC}"
echo -e "  停止: ${GREEN}$STOPPED_COUNT${NC} 个"
if [ "$FAILED_COUNT" -gt 0 ]; then
    echo -e "  失败: ${RED}$FAILED_COUNT${NC} 个"
    echo ""
    echo -e "${YELLOW}提示：使用 --force 强制停止${NC}"
    exit 1
fi