#!/bin/bash
# Feature Development Tracker
# Track feature lifecycle from PR to deployment

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="${SCRIPT_DIR}/reports"

mkdir -p "${REPORTS_DIR}"

# Date range
START_DATE="${1:-$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d '30 days ago' +%Y-%m-%d)}"
END_DATE="${2:-$(date +%Y-%m-%d)}"

echo -e "${BLUE}🚀 Feature Development Tracker${NC}"
echo -e "${BLUE}Period: ${START_DATE} to ${END_DATE}${NC}"
echo "═══════════════════════════════════════════════════════════"

# Feature PRs by status
echo -e "\n${CYAN}📊 Feature Pull Requests${NC}"
echo "─────────────────────────────────────────────────────────────"

# Merged features
merged_features=$(gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
    --json title,number,mergedAt,author,labels --limit 1000 \
    --jq '[.[] | select(.title | test("^feat:|^feature:"; "i"))] | length')

# Open features
open_features=$(gh pr list --state open \
    --json title,number,createdAt,author,labels --limit 1000 \
    --jq '[.[] | select(.title | test("^feat:|^feature:"; "i"))] | length')

# Closed without merge
closed_features=$(gh pr list --state closed --search "closed:${START_DATE}..${END_DATE}" \
    --json title,number,closedAt,mergedAt --limit 1000 \
    --jq '[.[] | select(.title | test("^feat:|^feature:"; "i")) | select(.mergedAt == null)] | length')

echo -e "  Merged:             ${GREEN}${merged_features}${NC}"
echo -e "  Currently Open:     ${YELLOW}${open_features}${NC}"
echo -e "  Closed (not merged): ${RED}${closed_features}${NC}"

# Feature velocity
echo -e "\n${CYAN}📈 Feature Velocity${NC}"
echo "─────────────────────────────────────────────────────────────"

# Calculate weekly velocity
weeks=$(( ($(date -d "$END_DATE" +%s) - $(date -d "$START_DATE" +%s)) / 604800 + 1 ))
if [ $weeks -gt 0 ]; then
    velocity=$(awk "BEGIN {printf \"%.1f\", $merged_features / $weeks}")
    echo -e "  Features per week: ${GREEN}${velocity}${NC}"
fi

# Average time to merge
echo -e "\n${CYAN}⏱️  Development Timeline${NC}"
echo "─────────────────────────────────────────────────────────────"

# Get merge times for features
gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
    --json title,createdAt,mergedAt --limit 100 \
    --jq '.[] | select(.title | test("^feat:|^feature:"; "i")) |
    {created: .createdAt, merged: .mergedAt}' | \
    jq -s 'map(((.merged | fromdateiso8601) - (.created | fromdateiso8601)) / 86400) |
    {avg: (add/length), min: min, max: max}' 2>/dev/null | \
    jq -r '"  Average time to merge: \(.avg | floor) days\n  Fastest feature: \(.min | floor) days\n  Slowest feature: \(.max | floor) days"' || \
    echo "  Unable to calculate merge times"

# Feature branches
echo -e "\n${CYAN}🌿 Feature Branches${NC}"
echo "─────────────────────────────────────────────────────────────"

# Active feature branches
active_branches=$(git branch -r | grep -E "feat(ure)?/" | wc -l | tr -d ' ')
echo -e "  Active feature branches: ${GREEN}${active_branches}${NC}"

# Stale branches (no commits in 30 days)
if [ $active_branches -gt 0 ]; then
    stale_branches=$(git for-each-ref --format='%(refname:short) %(committerdate:iso)' refs/remotes | \
        grep -E "feat(ure)?/" | \
        awk -v cutoff="$(date -d '30 days ago' +%Y-%m-%d)" '$2 < cutoff' | \
        wc -l | tr -d ' ')
    echo -e "  Stale branches (>30 days): ${YELLOW}${stale_branches}${NC}"
fi

# Feature categories
echo -e "\n${CYAN}🏷️  Feature Categories${NC}"
echo "─────────────────────────────────────────────────────────────"

# Analyze feature titles for common patterns
gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
    --json title --limit 1000 \
    --jq '.[] | select(.title | test("^feat:|^feature:"; "i")) | .title' | \
    sed -E 's/^(feat|feature):\s*//i' | \
    awk '{print tolower($1)}' | \
    sort | uniq -c | sort -rn | head -10 | \
    awk '{printf "  %-20s: %d features\n", $2, $1}'

# Recent features
echo -e "\n${CYAN}🆕 Recent Features${NC}"
echo "─────────────────────────────────────────────────────────────"

gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
    --json title,number,mergedAt,author --limit 10 \
    --jq '.[] | select(.title | test("^feat:|^feature:"; "i")) |
    "  #\(.number) \(.title) (@\(.author.login))"' | head -5

# Feature contributors
echo -e "\n${CYAN}👥 Feature Contributors${NC}"
echo "─────────────────────────────────────────────────────────────"

gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
    --json author,title --limit 1000 \
    --jq '.[] | select(.title | test("^feat:|^feature:"; "i")) | .author.login' | \
    sort | uniq -c | sort -rn | head -5 | \
    awk '{printf "  %-20s: %d features\n", $2, $1}'

# Feature impact (files changed)
echo -e "\n${CYAN}📁 Feature Impact${NC}"
echo "─────────────────────────────────────────────────────────────"

# Get file change statistics for feature PRs
total_files=0
total_additions=0
total_deletions=0
count=0

# This is a simplified version - ideally would query PR diff stats
echo "  Analyzing feature impact..."
feature_prs=$(gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
    --json number,title --limit 20 \
    --jq '.[] | select(.title | test("^feat:|^feature:"; "i")) | .number')

for pr in $feature_prs; do
    stats=$(gh pr view $pr --json additions,deletions,changedFiles 2>/dev/null || echo "{}")
    if [ -n "$stats" ] && [ "$stats" != "{}" ]; then
        additions=$(echo "$stats" | jq '.additions // 0')
        deletions=$(echo "$stats" | jq '.deletions // 0')
        files=$(echo "$stats" | jq '.changedFiles // 0')

        total_additions=$((total_additions + additions))
        total_deletions=$((total_deletions + deletions))
        total_files=$((total_files + files))
        count=$((count + 1))
    fi
done

if [ $count -gt 0 ]; then
    avg_files=$((total_files / count))
    avg_additions=$((total_additions / count))
    echo -e "  Average files per feature: ${GREEN}${avg_files}${NC}"
    echo -e "  Average lines added:       ${GREEN}+${avg_additions}${NC}"
fi

# Generate report
REPORT_FILE="${REPORTS_DIR}/feature-tracker-${START_DATE}-to-${END_DATE}.md"
cat > "$REPORT_FILE" << EOF
# Feature Development Report
**Period:** ${START_DATE} to ${END_DATE}

## Summary
- Features Merged: ${merged_features}
- Features Open: ${open_features}
- Features Closed: ${closed_features}
- Velocity: ${velocity:-0} features/week

## Branches
- Active Feature Branches: ${active_branches}
- Stale Branches: ${stale_branches:-0}

## Impact
- Average Files per Feature: ${avg_files:-N/A}
- Average Lines Added: ${avg_additions:-N/A}

---
*Generated on $(date)*
EOF

echo -e "\n${GREEN}✅ Report saved to: ${REPORT_FILE}${NC}"
echo "═══════════════════════════════════════════════════════════"
