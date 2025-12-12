#!/bin/bash
# CourseElection 内存监控脚本

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           CourseElection 内存状态监控                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# 1. 系统整体内存
echo "📊 系统整体内存使用:"
echo "─────────────────────────────────────────────────────────────"
free -h
echo ""

# 2. CourseElection 服务内存
echo "🎓 CourseElection 服务内存:"
echo "─────────────────────────────────────────────────────────────"
systemctl status course-election --no-pager | grep -E "(Memory|CPU)" || echo "服务未运行"
echo ""

# 3. Streamlit 进程详细信息
echo "🐍 Streamlit 进程详细信息:"
echo "─────────────────────────────────────────────────────────────"
ps aux | grep "[s]treamlit run app.py" | awk '{printf "PID: %s\nCPU: %s%%\n内存: %s%%\nRSS: %s KB\nVSZ: %s KB\n运行时间: %s\n", $2, $3, $4, $6, $5, $10}'
echo ""

# 4. 内存占用Top 5
echo "🔝 系统内存占用 Top 5:"
echo "─────────────────────────────────────────────────────────────"
ps aux --sort=-%mem | head -6 | awk 'NR==1 {print "进程\t\t\tCPU%\t内存%\t内存(RSS)"} NR>1 {printf "%-30s\t%.1f%%\t%.1f%%\t%s KB\n", substr($11,1,30), $3, $4, $6}'
echo ""

# 5. 内存使用趋势（如果有记录）
LOG_FILE="/home/ubuntu/work/sites/CourseElection/memory.log"
if [ -f "$LOG_FILE" ]; then
    echo "📈 最近5次内存记录:"
    echo "─────────────────────────────────────────────────────────────"
    tail -5 "$LOG_FILE"
    echo ""
fi

# 记录当前内存使用（追加到日志）
CURRENT_MEM=$(systemctl status course-election --no-pager 2>/dev/null | grep Memory | awk '{print $2}')
if [ ! -z "$CURRENT_MEM" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - CourseElection 内存: $CURRENT_MEM" >> "$LOG_FILE"
fi

# 6. 内存警告
TOTAL_MEM=$(free -m | awk 'NR==2 {print $2}')
USED_MEM=$(free -m | awk 'NR==2 {print $3}')
AVAILABLE_MEM=$(free -m | awk 'NR==2 {print $7}')
USAGE_PERCENT=$((USED_MEM * 100 / TOTAL_MEM))

echo "⚠️  内存警告检查:"
echo "─────────────────────────────────────────────────────────────"
if [ $USAGE_PERCENT -gt 90 ]; then
    echo "🔴 警告: 内存使用率 ${USAGE_PERCENT}% - 严重不足！"
elif [ $USAGE_PERCENT -gt 80 ]; then
    echo "🟡 注意: 内存使用率 ${USAGE_PERCENT}% - 可用内存较少"
elif [ $USAGE_PERCENT -gt 70 ]; then
    echo "🟢 正常: 内存使用率 ${USAGE_PERCENT}% - 内存充足"
else
    echo "🟢 良好: 内存使用率 ${USAGE_PERCENT}% - 内存充裕"
fi
echo "可用内存: ${AVAILABLE_MEM} MB"
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  提示: 运行 'watch -n 5 ./check_memory.sh' 可实时监控        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

