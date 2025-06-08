#!/bin/bash
# GitHub Metrics Tracking System
# Comprehensive metrics for project health and development velocity

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="${SCRIPT_DIR}/logs"
REPORTS_DIR="${SCRIPT_DIR}/reports"

# Create directories if they don't exist
mkdir -p "${LOGS_DIR}" "${REPORTS_DIR}"

# Default date range (last 7 days)
START_DATE="${1:-$(date -v-7d +%Y-%m-%d 2>/dev/null || date -d '7 days ago' +%Y-%m-%d)}"
END_DATE="${2:-$(date +%Y-%m-%d)}"

# Output format (text/json)
OUTPUT_FORMAT="${3:-text}"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}          GitHub Metrics Report (${START_DATE} to ${END_DATE})${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Function to check if gh is available
check_gh() {
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}Error: GitHub CLI (gh) is not installed.${NC}"
        echo "Install it from: https://cli.github.com/"
        exit 1
    fi
    
    if ! gh auth status &>/dev/null; then
        echo -e "${RED}Error: Not authenticated with GitHub.${NC}"
        echo "Run: gh auth login"
        exit 1
    fi
}

# Get repository info
get_repo_info() {
    gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null || echo "unknown/unknown"
}

# Features Completed (Pull Requests)
track_features() {
    echo -e "\n${CYAN}📦 Features Completed${NC}"
    echo "─────────────────────────────────────────────────────────"
    
    local count=$(gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
        --json title,number,mergedAt,author,labels --limit 1000 \
        --jq '[.[] | select(.title | test("^feat:|^feature:|^Feature:"; "i"))] | length')
    
    echo -e "Total features merged: ${GREEN}${count}${NC}"
    
    # List features
    gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
        --json title,number,mergedAt,author,labels --limit 1000 \
        --jq '.[] | select(.title | test("^feat:|^feature:|^Feature:"; "i")) | 
        "  #\(.number) \(.title) (@\(.author.login))"' | head -10
    
    if [ "$count" -gt 10 ]; then
        echo "  ... and $((count - 10)) more"
    fi
}

# Issues Resolved
track_issues() {
    echo -e "\n${CYAN}✅ Issues Resolved${NC}"
    echo "─────────────────────────────────────────────────────────"
    
    local count=$(gh issue list --state closed --search "closed:${START_DATE}..${END_DATE}" \
        --json number --limit 1000 --jq '. | length')
    
    echo -e "Total issues closed: ${GREEN}${count}${NC}"
    
    # List recent issues
    gh issue list --state closed --search "closed:${START_DATE}..${END_DATE}" \
        --json number,title,closedAt,assignees --limit 10 \
        --jq '.[] | "  #\(.number) \(.title)"'
}

# Tests Written
track_tests() {
    echo -e "\n${CYAN}🧪 Test Coverage${NC}"
    echo "─────────────────────────────────────────────────────────"
    
    # Count test files changed
    local test_files=$(git log --since="${START_DATE}" --until="${END_DATE}" \
        --name-only --pretty=format: -- "*test*.py" "*.test.js" "*.spec.js" "*test*.ts" \
        | grep -E '\.(py|js|ts)$' | sort | uniq | wc -l | tr -d ' ')
    
    # Count test lines added/removed
    local test_stats=$(git log --since="${START_DATE}" --until="${END_DATE}" \
        --numstat --pretty=format: -- "*test*.py" "*.test.js" "*.spec.js" "*test*.ts" \
        | awk 'NF==3 {add+=$1; del+=$2} END {print add " " del}')
    
    local lines_added=$(echo $test_stats | cut -d' ' -f1)
    local lines_removed=$(echo $test_stats | cut -d' ' -f2)
    
    echo -e "Test files modified: ${GREEN}${test_files}${NC}"
    echo -e "Test lines added: ${GREEN}+${lines_added}${NC}"
    echo -e "Test lines removed: ${RED}-${lines_removed}${NC}"
    
    # New test files
    echo -e "\nNew test files:"
    git log --since="${START_DATE}" --until="${END_DATE}" \
        --name-status --diff-filter=A --pretty=format: -- "*test*.py" "*.test.js" "*.spec.js" \
        | grep "^A" | cut -f2 | head -5 | sed 's/^/  /'
}

# Documentation Updated
track_documentation() {
    echo -e "\n${CYAN}📚 Documentation Updates${NC}"
    echo "─────────────────────────────────────────────────────────"
    
    # Count documentation files changed
    local doc_files=$(git log --since="${START_DATE}" --until="${END_DATE}" \
        --name-only --pretty=format: -- "*.md" "*.rst" "docs/**" "*.txt" \
        | grep -E '\.(md|rst|txt)$' | sort | uniq | wc -l | tr -d ' ')
    
    # Count documentation lines
    local doc_stats=$(git log --since="${START_DATE}" --until="${END_DATE}" \
        --numstat --pretty=format: -- "*.md" "*.rst" "docs/**" \
        | awk 'NF==3 {add+=$1; del+=$2} END {print add " " del}')
    
    local lines_added=$(echo $doc_stats | cut -d' ' -f1)
    local lines_removed=$(echo $doc_stats | cut -d' ' -f2)
    
    echo -e "Documentation files modified: ${GREEN}${doc_files}${NC}"
    echo -e "Lines added: ${GREEN}+${lines_added}${NC}"
    echo -e "Lines removed: ${RED}-${lines_removed}${NC}"
    
    # Most updated docs
    echo -e "\nMost updated documentation:"
    git log --since="${START_DATE}" --until="${END_DATE}" \
        --name-only --pretty=format: -- "*.md" "*.rst" "docs/**" \
        | grep -E '\.(md|rst)$' | sort | uniq -c | sort -rn | head -5 | \
        awk '{printf "  %s updates: %s\n", $1, $2}'
}

# Code Quality Metrics
track_code_quality() {
    echo -e "\n${CYAN}🔍 Code Quality${NC}"
    echo "─────────────────────────────────────────────────────────"
    
    # PRs with review comments
    local reviewed_prs=$(gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
        --json number,reviewComments --limit 100 \
        --jq '[.[] | select(.reviewComments > 0)] | length')
    
    echo -e "PRs with review comments: ${YELLOW}${reviewed_prs}${NC}"
    
    # Check for linting/CI status if available
    local failed_checks=$(gh pr list --state all --search "created:${START_DATE}..${END_DATE}" \
        --json number,statusCheckRollup --limit 100 \
        --jq '[.[] | select(.statusCheckRollup | length > 0) | 
        select(.statusCheckRollup | any(.conclusion == "FAILURE"))] | length' 2>/dev/null || echo "N/A")
    
    echo -e "PRs with failed checks: ${RED}${failed_checks}${NC}"
}

# Contributors Activity
track_contributors() {
    echo -e "\n${CYAN}👥 Contributor Activity${NC}"
    echo "─────────────────────────────────────────────────────────"
    
    # Unique contributors
    local contributors=$(git log --since="${START_DATE}" --until="${END_DATE}" \
        --pretty=format:"%an" | sort | uniq | wc -l | tr -d ' ')
    
    echo -e "Active contributors: ${GREEN}${contributors}${NC}"
    
    # Top contributors by commits
    echo -e "\nTop contributors by commits:"
    git log --since="${START_DATE}" --until="${END_DATE}" \
        --pretty=format:"%an" | sort | uniq -c | sort -rn | head -5 | \
        awk '{$1=sprintf("  %-3s commits:", $1); print}'
}

# Generate JSON output if requested
generate_json_output() {
    local repo=$(get_repo_info)
    local features=$(gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" \
        --json title,number,mergedAt,author,labels --limit 1000 \
        --jq '[.[] | select(.title | test("^feat:|^feature:|^Feature:"; "i"))] | length')
    local issues=$(gh issue list --state closed --search "closed:${START_DATE}..${END_DATE}" \
        --json number --limit 1000 --jq '. | length')
    
    cat > "${REPORTS_DIR}/metrics-${START_DATE}-to-${END_DATE}.json" <<EOF
{
    "repository": "${repo}",
    "date_range": {
        "start": "${START_DATE}",
        "end": "${END_DATE}"
    },
    "metrics": {
        "features_completed": ${features:-0},
        "issues_resolved": ${issues:-0},
        "test_files_changed": $(git log --since="${START_DATE}" --until="${END_DATE}" \
            --name-only --pretty=format: -- "*test*.py" | sort | uniq | wc -l | tr -d ' '),
        "documentation_files_changed": $(git log --since="${START_DATE}" --until="${END_DATE}" \
            --name-only --pretty=format: -- "*.md" "*.rst" | sort | uniq | wc -l | tr -d ' ')
    },
    "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    echo -e "\n${GREEN}JSON report saved to: ${REPORTS_DIR}/metrics-${START_DATE}-to-${END_DATE}.json${NC}"
}

# Main execution
main() {
    check_gh
    
    track_features
    track_issues
    track_tests
    track_documentation
    track_code_quality
    track_contributors
    
    if [ "$OUTPUT_FORMAT" = "json" ]; then
        generate_json_output
    fi
    
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Report generated: $(date)${NC}"
    
    # Save a copy to logs
    local log_file="${LOGS_DIR}/metrics-$(date +%Y%m%d-%H%M%S).log"
    echo "Report saved to: ${log_file}"
}

# Run main function
main