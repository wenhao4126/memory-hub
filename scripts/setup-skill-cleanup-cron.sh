#!/bin/bash
# ============================================================
# 技能清理定时任务配置脚本
# 功能：添加 crontab 任务，每月 1 号执行清理检查
# 用法：./setup-skill-cleanup-cron.sh [--install] [--uninstall] [--status]
# ============================================================

set -e

# 配置
SCRIPT_PATH="$HOME/.openclaw/workspace/scripts/skill-cleanup.sh"
CRON_JOB="0 9 1 * * $SCRIPT_PATH --dry-run >> $HOME/.openclaw/workspace/memory/skill-cleanup.log 2>&1"
CRON_COMMENT="# 傻妞技能清理 - 每月1号上午9点"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 参数解析
ACTION="status"

for arg in "$@"; do
    case $arg in
        --install|-i)
            ACTION="install"
            shift
            ;;
        --uninstall|-u)
            ACTION="uninstall"
            shift
            ;;
        --status|-s)
            ACTION="status"
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --install, -i    安装定时任务"
            echo "  --uninstall, -u  卸载定时任务"
            echo "  --status, -s     查看状态（默认）"
            echo "  -h, --help       显示帮助信息"
            exit 0
            ;;
        *)
            echo "未知参数: $arg"
            exit 1
            ;;
    esac
done

# 检查脚本是否存在
check_script() {
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo -e "${RED}✗ 清理脚本不存在: $SCRIPT_PATH${NC}"
        echo -e "${YELLOW}  请先创建脚本文件${NC}"
        exit 1
    fi
    
    if [ ! -x "$SCRIPT_PATH" ]; then
        echo -e "${YELLOW}⚠ 脚本未设置执行权限，正在添加...${NC}"
        chmod +x "$SCRIPT_PATH"
    fi
    
    echo -e "${GREEN}✓ 清理脚本就绪${NC}"
}

# 安装定时任务
install_cron() {
    echo -e "${BLUE}📦 安装技能清理定时任务...${NC}"
    
    check_script
    
    # 检查是否已存在
    if crontab -l 2>/dev/null | grep -q "skill-cleanup.sh"; then
        echo -e "${YELLOW}⚠ 定时任务已存在，跳过安装${NC}"
        echo -e "${YELLOW}  如需重新安装，请先卸载${NC}"
        return 0
    fi
    
    # 添加定时任务
    (crontab -l 2>/dev/null; echo "$CRON_COMMENT"; echo "$CRON_JOB") | crontab -
    
    echo -e "${GREEN}✓ 定时任务安装成功${NC}"
    echo ""
    echo -e "${BLUE}执行计划:${NC}"
    echo "  每月 1 号上午 9:00"
    echo ""
    echo -e "${BLUE}日志位置:${NC}"
    echo "  $HOME/.openclaw/workspace/memory/skill-cleanup.log"
    echo ""
    echo -e "${BLUE}查看定时任务:${NC}"
    echo "  crontab -l"
}

# 卸载定时任务
uninstall_cron() {
    echo -e "${BLUE}🗑️ 卸载技能清理定时任务...${NC}"
    
    # 删除相关行
    crontab -l 2>/dev/null | grep -v "skill-cleanup.sh" | grep -v "傻妞技能清理" | crontab - 2>/dev/null || true
    
    echo -e "${GREEN}✓ 定时任务已卸载${NC}"
}

# 查看状态
show_status() {
    echo -e "${BLUE}📊 技能清理定时任务状态${NC}"
    echo ""
    
    # 检查脚本
    echo -e "${BLUE}清理脚本:${NC}"
    if [ -f "$SCRIPT_PATH" ]; then
        echo -e "  ${GREEN}✓${NC} 存在: $SCRIPT_PATH"
        if [ -x "$SCRIPT_PATH" ]; then
            echo -e "  ${GREEN}✓${NC} 可执行"
        else
            echo -e "  ${YELLOW}⚠${NC} 不可执行（需要 chmod +x）"
        fi
    else
        echo -e "  ${RED}✗${NC} 不存在: $SCRIPT_PATH"
    fi
    
    echo ""
    
    # 检查定时任务
    echo -e "${BLUE}定时任务:${NC}"
    if crontab -l 2>/dev/null | grep -q "skill-cleanup.sh"; then
        echo -e "  ${GREEN}✓${NC} 已安装"
        echo ""
        echo -e "  ${BLUE}当前配置:${NC}"
        crontab -l 2>/dev/null | grep -A1 "傻妞技能清理" | while read line; do
            echo "    $line"
        done
    else
        echo -e "  ${YELLOW}○${NC} 未安装"
        echo ""
        echo -e "  ${BLUE}安装命令:${NC}"
        echo "    $0 --install"
    fi
    
    echo ""
    
    # 检查日志
    echo -e "${BLUE}日志文件:${NC}"
    LOG_FILE="$HOME/.openclaw/workspace/memory/skill-cleanup.log"
    if [ -f "$LOG_FILE" ]; then
        echo -e "  ${GREEN}✓${NC} 存在: $LOG_FILE"
        echo -e "  ${BLUE}最后 5 条记录:${NC}"
        tail -5 "$LOG_FILE" | while read line; do
            echo "    $line"
        done
    else
        echo -e "  ${YELLOW}○${NC} 不存在: $LOG_FILE"
    fi
    
    # 检查报告
    echo ""
    echo -e "${BLUE}清理报告:${NC}"
    REPORT_FILE="$HOME/.openclaw/workspace/memory/skill-cleanup-report.md"
    if [ -f "$REPORT_FILE" ]; then
        echo -e "  ${GREEN}✓${NC} 存在: $REPORT_FILE"
        echo -e "  ${BLUE}生成时间:${NC}"
        head -5 "$REPORT_FILE" | grep "生成时间" | while read line; do
            echo "    $line"
        done
    else
        echo -e "  ${YELLOW}○${NC} 不存在: $REPORT_FILE"
    fi
}

# 主逻辑
case $ACTION in
    install)
        install_cron
        ;;
    uninstall)
        uninstall_cron
        ;;
    status)
        show_status
        ;;
esac