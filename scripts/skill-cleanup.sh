#!/bin/bash
# ============================================================
# 傻妞手下技能清理脚本
# 功能：扫描、检查、清理长期未更新的技能
# 用法：./skill-cleanup.sh [--dry-run] [--force] [--report-only]
# ============================================================

# 不要使用 set -e，避免命令返回非零值时脚本意外退出

# 配置
SKILLS_BASE="$HOME/.openclaw"
REPORT_FILE="$HOME/.openclaw/workspace/memory/skill-cleanup-report.md"
LOG_FILE="$HOME/.openclaw/workspace/memory/skill-cleanup.log"
AGE_THRESHOLD_DAYS=90  # 3 个月

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 参数解析
DRY_RUN=false
FORCE=false
REPORT_ONLY=false

for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --report-only)
            REPORT_ONLY=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --dry-run      仅预览，不执行删除"
            echo "  --force        强制删除，无需确认"
            echo "  --report-only  仅生成报告"
            echo "  -h, --help     显示帮助信息"
            exit 0
            ;;
        *)
            echo "未知参数: $arg"
            exit 1
            ;;
    esac
done

# 日志函数
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    case $level in
        INFO)  echo -e "${BLUE}ℹ${NC} $message" ;;
        WARN)  echo -e "${YELLOW}⚠${NC} $message" ;;
        ERROR) echo -e "${RED}✗${NC} $message" ;;
        SUCCESS) echo -e "${GREEN}✓${NC} $message" ;;
    esac
}

# 检查技能年龄
check_skill_age() {
    local skill_path="$1"
    local skill_name=$(basename "$skill_path")
    
    # 获取最后修改时间（兼容 Linux 和 macOS）
    local last_modified
    if [[ "$OSTYPE" == "darwin"* ]]; then
        last_modified=$(stat -f %m "$skill_path" 2>/dev/null || echo "0")
    else
        last_modified=$(stat -c %Y "$skill_path" 2>/dev/null || echo "0")
    fi
    
    local current_time=$(date +%s)
    local age_days=$(( (current_time - last_modified) / 86400 ))
    local last_modified_date=$(date -d "@$last_modified" '+%Y-%m-%d' 2>/dev/null || date -r "$last_modified" '+%Y-%m-%d' 2>/dev/null || echo "unknown")
    
    echo "$skill_name|$age_days|$last_modified_date"
}

# 生成报告
generate_report() {
    local output_file="$1"
    local report_date=$(date '+%Y-%m-%d %H:%M:%S')
    
    cat > "$output_file" << EOF
# 技能清理报告

**生成时间**: $report_date
**检查阈值**: ${AGE_THRESHOLD_DAYS} 天（3 个月）

---

## 📊 扫描结果总览

| 团队 | 技能总数 | 需清理 | 状态 |
|------|---------|--------|------|
EOF

    local total_skills=0
    local total_to_clean=0
    local team_stats=""
    
    for team_dir in "$SKILLS_BASE"/workspace-team-*/skills; do
        if [ -d "$team_dir" ]; then
            local team_name=$(basename $(dirname "$team_dir"))
            local skill_count=0
            local clean_count=0
            
            for skill_path in "$team_dir"/*/; do
                if [ -d "$skill_path" ] && [ ! -L "$skill_path" ]; then
                    ((skill_count++))
                    local result=$(check_skill_age "$skill_path")
                    local age=$(echo "$result" | cut -d'|' -f2)
                    if [ "$age" -gt "$AGE_THRESHOLD_DAYS" ]; then
                        ((clean_count++))
                    fi
                fi
            done
            
            local status="✅ 正常"
            if [ "$clean_count" -gt 0 ]; then
                status="⚠️ 需清理"
            fi
            
            echo "| $team_name | $skill_count | $clean_count | $status |" >> "$output_file"
            ((total_skills += skill_count))
            ((total_to_clean += clean_count))
        fi
    done
    
    echo "" >> "$output_file"
    echo "**总计**: $total_skills 个技能，$total_to_clean 个需要清理" >> "$output_file"
    
    # 详细列表
    echo "" >> "$output_file"
    echo "---" >> "$output_file"
    echo "" >> "$output_file"
    echo "## 🔍 详细列表" >> "$output_file"
    echo "" >> "$output_file"
    
    for team_dir in "$SKILLS_BASE"/workspace-team-*/skills; do
        if [ -d "$team_dir" ]; then
            local team_name=$(basename $(dirname "$team_dir"))
            local has_old_skills=false
            
            for skill_path in "$team_dir"/*/; do
                if [ -d "$skill_path" ] && [ ! -L "$skill_path" ]; then
                    local result=$(check_skill_age "$skill_path")
                    local skill_name=$(echo "$result" | cut -d'|' -f1)
                    local age=$(echo "$result" | cut -d'|' -f2)
                    local last_date=$(echo "$result" | cut -d'|' -f3)
                    
                    if [ "$age" -gt "$AGE_THRESHOLD_DAYS" ]; then
                        if [ "$has_old_skills" = false ]; then
                            echo "### $team_name" >> "$output_file"
                            echo "" >> "$output_file"
                            echo "| 技能名 | 未更新天数 | 最后修改 |" >> "$output_file"
                            echo "|--------|-----------|----------|" >> "$output_file"
                            has_old_skills=true
                        fi
                        echo "| $skill_name | $age 天 | $last_date |" >> "$output_file"
                    fi
                fi
            done
            
            if [ "$has_old_skills" = true ]; then
                echo "" >> "$output_file"
            fi
        fi
    done
    
    echo "" >> "$output_file"
    echo "---" >> "$output_file"
    echo "*报告由 skill-cleanup.sh 自动生成*" >> "$output_file"
}

# 清理技能
cleanup_skill() {
    local skill_path="$1"
    local skill_name=$(basename "$skill_path")
    local team_name=$(basename $(dirname $(dirname "$skill_path")))
    
    if [ "$FORCE" = true ]; then
        rm -rf "$skill_path"
        log SUCCESS "已删除: $team_name/$skill_name"
        return 0
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log INFO "[预览] 将删除: $team_name/$skill_name"
        return 0
    fi
    
    # 交互式确认
    read -p "$(echo -e ${YELLOW}确认删除 $team_name/$skill_name ? [y/N]:${NC} )" confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        rm -rf "$skill_path"
        log SUCCESS "已删除: $team_name/$skill_name"
        return 0
    else
        log INFO "跳过: $team_name/$skill_name"
        return 1
    fi
}

# 主逻辑
main() {
    log INFO "开始扫描技能目录..."
    log INFO "检查阈值: ${AGE_THRESHOLD_DAYS} 天"
    
    # 确保目录存在
    mkdir -p "$(dirname "$REPORT_FILE")"
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # 扫描统计
    local scanned=0
    local to_clean=0
    local cleaned=0
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${BLUE}         傻妞手下技能清理工具${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[预览模式] 仅显示将被清理的技能${NC}"
        echo ""
    fi
    
    # 扫描各团队
    for team_dir in "$SKILLS_BASE"/workspace-team-*/skills; do
        if [ -d "$team_dir" ]; then
            local team_name=$(basename $(dirname "$team_dir"))
            echo -e "${BLUE}📁 $team_name${NC}"
            
            for skill_path in "$team_dir"/*/; do
                # 跳过符号链接和非目录
                if [ ! -d "$skill_path" ] || [ -L "$skill_path" ]; then
                    continue
                fi
                
                ((scanned++))
                local result=$(check_skill_age "$skill_path")
                local skill_name=$(echo "$result" | cut -d'|' -f1)
                local age=$(echo "$result" | cut -d'|' -f2)
                local last_date=$(echo "$result" | cut -d'|' -f3)
                
                if [ "$age" -gt "$AGE_THRESHOLD_DAYS" ]; then
                    ((to_clean++))
                    echo -e "  ${RED}✗${NC} $skill_name (${age}天未更新, 最后修改: $last_date)"
                    
                    # 执行清理（如果不是仅报告模式）
                    if [ "$REPORT_ONLY" = false ]; then
                        if cleanup_skill "$skill_path"; then
                            ((cleaned++))
                        fi
                    fi
                else
                    echo -e "  ${GREEN}✓${NC} $skill_name (${age}天, 最后修改: $last_date)"
                fi
            done
            echo ""
        fi
    done
    
    # 生成报告
    generate_report "$REPORT_FILE"
    
    # 总结
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${GREEN}📊 扫描完成${NC}"
    echo ""
    echo "  扫描技能数: $scanned"
    echo "  需清理数: $to_clean"
    
    if [ "$REPORT_ONLY" = false ] && [ "$DRY_RUN" = false ]; then
        echo "  已清理数: $cleaned"
    fi
    
    echo ""
    echo "  📄 报告已生成: $REPORT_FILE"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    
    log INFO "扫描完成: $scanned 个技能, $to_clean 个需清理"
}

# 运行
main