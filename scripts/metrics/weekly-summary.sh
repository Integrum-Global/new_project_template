#!/bin/bash
# Weekly Summary with Visualizations
# Generates a visual weekly report with charts

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="${SCRIPT_DIR}/reports"
LOGS_DIR="${SCRIPT_DIR}/logs"

mkdir -p "${REPORTS_DIR}" "${LOGS_DIR}"

# Parse arguments
if [ $# -eq 0 ] || [ "$1" = "thisweek" ]; then
    # This week (Monday to today)
    START_DATE=$(date -v-monday +%Y-%m-%d 2>/dev/null || date -d 'last monday' +%Y-%m-%d)
    END_DATE=$(date +%Y-%m-%d)
elif [ "$1" = "lastweek" ]; then
    # Last week (Monday to Sunday)
    START_DATE=$(date -v-monday -v-7d +%Y-%m-%d 2>/dev/null || date -d 'last monday - 7 days' +%Y-%m-%d)
    END_DATE=$(date -v-sunday -v-7d +%Y-%m-%d 2>/dev/null || date -d 'last sunday' +%Y-%m-%d)
else
    # Custom start date (assumes Monday, goes for 7 days)
    START_DATE="$1"
    END_DATE=$(date -d "${START_DATE} + 6 days" +%Y-%m-%d 2>/dev/null || \
               date -v+6d -jf "%Y-%m-%d" "${START_DATE}" +%Y-%m-%d 2>/dev/null || \
               echo "${START_DATE}")
fi

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Weekly Summary Report                            ║${NC}"
echo -e "${BLUE}║              ${START_DATE} to ${END_DATE}                     ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"

# Function to draw a bar chart
draw_bar() {
    local value=$1
    local max=$2
    local width=30
    local filled=$((value * width / max))

    printf "["
    for ((i=0; i<filled; i++)); do printf "█"; done
    for ((i=filled; i<width; i++)); do printf "░"; done
    printf "]"
}

# Collect daily data
echo -e "\n${CYAN}📊 Daily Activity Breakdown${NC}"
echo "─────────────────────────────────────────────────────────────"

declare -A daily_commits
declare -A daily_prs
declare -A daily_issues
max_commits=0

# Loop through each day
current_date="$START_DATE"
while [[ "$current_date" < "$END_DATE" ]] || [[ "$current_date" == "$END_DATE" ]]; do
    day_name=$(date -d "$current_date" +%a 2>/dev/null || date -jf "%Y-%m-%d" "$current_date" +%a 2>/dev/null)

    # Get metrics for this day
    commits=$(git log --since="${current_date} 00:00" --until="${current_date} 23:59" --oneline 2>/dev/null | wc -l | tr -d ' ')
    prs=$(gh pr list --state merged --search "merged:${current_date}" --json number --jq '. | length' 2>/dev/null || echo "0")
    issues=$(gh issue list --state closed --search "closed:${current_date}" --json number --jq '. | length' 2>/dev/null || echo "0")

    daily_commits["$current_date"]=$commits
    daily_prs["$current_date"]=$prs
    daily_issues["$current_date"]=$issues

    # Track max for scaling
    [ $commits -gt $max_commits ] && max_commits=$commits

    # Move to next day
    current_date=$(date -d "$current_date + 1 day" +%Y-%m-%d 2>/dev/null || \
                   date -v+1d -jf "%Y-%m-%d" "$current_date" +%Y-%m-%d 2>/dev/null)
done

# Display daily chart
current_date="$START_DATE"
while [[ "$current_date" < "$END_DATE" ]] || [[ "$current_date" == "$END_DATE" ]]; do
    day_name=$(date -d "$current_date" +%a 2>/dev/null || date -jf "%Y-%m-%d" "$current_date" +%a 2>/dev/null)
    commits=${daily_commits["$current_date"]}
    prs=${daily_prs["$current_date"]}
    issues=${daily_issues["$current_date"]}

    printf "${PURPLE}%s %s${NC} " "$day_name" "$current_date"

    if [ $max_commits -gt 0 ]; then
        draw_bar $commits $max_commits
    else
        printf "[No activity]"
    fi

    printf " ${GREEN}%2d${NC} commits, ${BLUE}%d${NC} PRs, ${YELLOW}%d${NC} issues\n" \
           "$commits" "$prs" "$issues"

    # Move to next day
    current_date=$(date -d "$current_date + 1 day" +%Y-%m-%d 2>/dev/null || \
                   date -v+1d -jf "%Y-%m-%d" "$current_date" +%Y-%m-%d 2>/dev/null)
done

# Week totals
echo -e "\n${CYAN}📈 Week Totals${NC}"
echo "─────────────────────────────────────────────────────────────"

total_commits=$(git log --since="${START_DATE}" --until="${END_DATE}" --oneline 2>/dev/null | wc -l | tr -d ' ')
total_prs=$(gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" --json number --jq '. | length' 2>/dev/null || echo "0")
total_issues=$(gh issue list --state closed --search "closed:${START_DATE}..${END_DATE}" --json number --jq '. | length' 2>/dev/null || echo "0")
total_contributors=$(git log --since="${START_DATE}" --until="${END_DATE}" --pretty=format:"%an" | sort -u | wc -l | tr -d ' ')

echo -e "  Total Commits:      ${GREEN}${total_commits}${NC}"
echo -e "  PRs Merged:         ${GREEN}${total_prs}${NC}"
echo -e "  Issues Closed:      ${GREEN}${total_issues}${NC}"
echo -e "  Active Contributors: ${GREEN}${total_contributors}${NC}"

# Top contributors
echo -e "\n${CYAN}🏆 Top Contributors${NC}"
echo "─────────────────────────────────────────────────────────────"

git log --since="${START_DATE}" --until="${END_DATE}" --pretty=format:"%an" | \
    sort | uniq -c | sort -rn | head -5 | \
    awk '{printf "  %-20s %s commits\n", substr($0, index($0,$2)), $1}'

# Activity by file type
echo -e "\n${CYAN}📁 Activity by File Type${NC}"
echo "─────────────────────────────────────────────────────────────"

git log --since="${START_DATE}" --until="${END_DATE}" --name-only --pretty=format: | \
    grep -E '\.[a-zA-Z]+$' | \
    sed 's/.*\.//' | \
    sort | uniq -c | sort -rn | head -10 | \
    awk '{printf "  .%-10s %4d files changed\n", $2, $1}'

# Feature velocity
echo -e "\n${CYAN}🚀 Feature Velocity${NC}"
echo "─────────────────────────────────────────────────────────────"

features=$(gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
    --json title --jq '[.[] | select(.title | test("^feat:|^feature:"; "i"))] | length' 2>/dev/null || echo "0")
bugs=$(gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
    --json title --jq '[.[] | select(.title | test("^fix:|^bug:"; "i"))] | length' 2>/dev/null || echo "0")
docs=$(gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
    --json title --jq '[.[] | select(.title | test("^docs:|^doc:"; "i"))] | length' 2>/dev/null || echo "0")

echo -e "  Features:      ${GREEN}${features}${NC}"
echo -e "  Bug Fixes:     ${YELLOW}${bugs}${NC}"
echo -e "  Documentation: ${BLUE}${docs}${NC}"

# Generate markdown report
REPORT_FILE="${REPORTS_DIR}/weekly-summary-${START_DATE}.md"
cat > "$REPORT_FILE" << EOF
# Weekly Summary Report
**Period:** ${START_DATE} to ${END_DATE}

## 📊 Overview
- **Total Commits:** ${total_commits}
- **PRs Merged:** ${total_prs}
- **Issues Closed:** ${total_issues}
- **Active Contributors:** ${total_contributors}

## 🚀 Feature Velocity
- Features: ${features}
- Bug Fixes: ${bugs}
- Documentation: ${docs}

## 📈 Daily Activity
$(current_date="$START_DATE"
while [[ "$current_date" < "$END_DATE" ]] || [[ "$current_date" == "$END_DATE" ]]; do
    day_name=$(date -d "$current_date" +%a 2>/dev/null || date -jf "%Y-%m-%d" "$current_date" +%a 2>/dev/null)
    echo "- **${day_name} ${current_date}:** ${daily_commits["$current_date"]} commits, ${daily_prs["$current_date"]} PRs, ${daily_issues["$current_date"]} issues"
    current_date=$(date -d "$current_date + 1 day" +%Y-%m-%d 2>/dev/null || date -v+1d -jf "%Y-%m-%d" "$current_date" +%Y-%m-%d 2>/dev/null)
done)

## 🏆 Top Contributors
$(git log --since="${START_DATE}" --until="${END_DATE}" --pretty=format:"%an" | \
    sort | uniq -c | sort -rn | head -5 | \
    awk '{printf "1. %s - %d commits\n", substr($0, index($0,$2)), $1}')

---
*Generated on $(date)*
EOF

echo -e "\n${GREEN}✅ Report saved to: ${REPORT_FILE}${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
