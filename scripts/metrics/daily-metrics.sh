#!/bin/bash
# Daily Metrics Tracker
# Quick daily snapshot of development activity

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="${SCRIPT_DIR}/logs"
DAILY_CSV="${LOGS_DIR}/daily-metrics.csv"

mkdir -p "${LOGS_DIR}"

# Date handling
TODAY="${1:-$(date +%Y-%m-%d)}"
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d 'yesterday' +%Y-%m-%d)

echo -e "${BLUE}📊 Daily Metrics for ${TODAY}${NC}"
echo "═══════════════════════════════════════════════════════════"

# Initialize CSV if doesn't exist
if [ ! -f "$DAILY_CSV" ]; then
    echo "date,commits,prs_merged,issues_closed,test_files,doc_files,contributors" > "$DAILY_CSV"
fi

# Today's commits
commits_today=$(git log --since="${TODAY} 00:00" --until="${TODAY} 23:59" --oneline 2>/dev/null | wc -l | tr -d ' ')

# PRs merged today
prs_today=$(gh pr list --state merged --search "merged:${TODAY}" --json number --jq '. | length' 2>/dev/null || echo "0")

# Issues closed today
issues_today=$(gh issue list --state closed --search "closed:${TODAY}" --json number --jq '. | length' 2>/dev/null || echo "0")

# Test files changed
test_files=$(git log --since="${TODAY} 00:00" --until="${TODAY} 23:59" \
    --name-only --pretty=format: -- "*test*.py" "*.test.js" "*.spec.js" \
    | grep -E '\.(py|js)$' | sort | uniq | wc -l | tr -d ' ')

# Documentation files changed
doc_files=$(git log --since="${TODAY} 00:00" --until="${TODAY} 23:59" \
    --name-only --pretty=format: -- "*.md" "*.rst" "docs/**" \
    | grep -E '\.(md|rst)$' | sort | uniq | wc -l | tr -d ' ')

# Contributors today
contributors=$(git log --since="${TODAY} 00:00" --until="${TODAY} 23:59" \
    --pretty=format:"%an" | sort | uniq | wc -l | tr -d ' ')

# Display metrics
echo -e "\n${CYAN}Today's Activity:${NC}"
echo -e "  Commits:          ${GREEN}${commits_today}${NC}"
echo -e "  PRs Merged:       ${GREEN}${prs_today}${NC}"
echo -e "  Issues Closed:    ${GREEN}${issues_today}${NC}"
echo -e "  Test Files:       ${GREEN}${test_files}${NC}"
echo -e "  Doc Files:        ${GREEN}${doc_files}${NC}"
echo -e "  Contributors:     ${GREEN}${contributors}${NC}"

# Compare with yesterday
echo -e "\n${CYAN}Comparison with Yesterday:${NC}"

# Yesterday's data from CSV
yesterday_data=$(grep "^${YESTERDAY}," "$DAILY_CSV" 2>/dev/null || echo "")

if [ -n "$yesterday_data" ]; then
    IFS=',' read -r _ y_commits y_prs y_issues y_tests y_docs y_contrib <<< "$yesterday_data"
    
    # Calculate differences
    diff_commits=$((commits_today - y_commits))
    diff_prs=$((prs_today - y_prs))
    diff_issues=$((issues_today - y_issues))
    
    # Display with color coding
    [ $diff_commits -ge 0 ] && color=$GREEN || color=$YELLOW
    echo -e "  Commits:     ${color}$(printf "%+d" $diff_commits)${NC} (Yesterday: $y_commits)"
    
    [ $diff_prs -ge 0 ] && color=$GREEN || color=$YELLOW
    echo -e "  PRs:         ${color}$(printf "%+d" $diff_prs)${NC} (Yesterday: $y_prs)"
    
    [ $diff_issues -ge 0 ] && color=$GREEN || color=$YELLOW
    echo -e "  Issues:      ${color}$(printf "%+d" $diff_issues)${NC} (Yesterday: $y_issues)"
else
    echo "  No data available for yesterday"
fi

# Recent activity
if [ $commits_today -gt 0 ]; then
    echo -e "\n${CYAN}Recent Commits:${NC}"
    git log --since="${TODAY} 00:00" --until="${TODAY} 23:59" \
        --pretty=format:"  %h %s (%an)" | head -5
    
    if [ $commits_today -gt 5 ]; then
        echo -e "  ... and $((commits_today - 5)) more"
    fi
fi

# Active PRs
active_prs=$(gh pr list --state open --json number --jq '. | length' 2>/dev/null || echo "0")
if [ "$active_prs" -gt 0 ]; then
    echo -e "\n${CYAN}Active Pull Requests: ${active_prs}${NC}"
    gh pr list --state open --limit 3 --json number,title,author \
        --jq '.[] | "  #\(.number) \(.title) (@\(.author.login))"'
fi

# Save to CSV
echo "${TODAY},${commits_today},${prs_today},${issues_today},${test_files},${doc_files},${contributors}" >> "$DAILY_CSV"

echo -e "\n${PURPLE}Metrics logged to: ${DAILY_CSV}${NC}"
echo "═══════════════════════════════════════════════════════════"