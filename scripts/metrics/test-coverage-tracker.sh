#!/bin/bash
# Test Coverage Tracker
# Specialized analysis for test files and coverage

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="${SCRIPT_DIR}/reports"

mkdir -p "${REPORTS_DIR}"

# Date range (default: last 30 days)
START_DATE="${1:-$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d '30 days ago' +%Y-%m-%d)}"
END_DATE="${2:-$(date +%Y-%m-%d)}"

echo -e "${BLUE}🧪 Test Coverage Analysis${NC}"
echo -e "${BLUE}Period: ${START_DATE} to ${END_DATE}${NC}"
echo "═══════════════════════════════════════════════════════════"

# Test file patterns by language
declare -A test_patterns=(
    ["Python"]="*test*.py"
    ["JavaScript"]="*.test.js *.spec.js"
    ["TypeScript"]="*.test.ts *.spec.ts"
    ["Go"]="*_test.go"
    ["Java"]="*Test.java"
    ["Ruby"]="*_spec.rb *_test.rb"
)

# Analyze test files by language
echo -e "\n${CYAN}📊 Test Files by Language${NC}"
echo "─────────────────────────────────────────────────────────────"

for lang in "${!test_patterns[@]}"; do
    patterns="${test_patterns[$lang]}"
    count=0
    
    for pattern in $patterns; do
        files=$(git log --since="${START_DATE}" --until="${END_DATE}" \
            --name-only --pretty=format: -- "$pattern" | \
            grep -E "${pattern//\*/.*}" | sort -u | wc -l | tr -d ' ')
        count=$((count + files))
    done
    
    if [ $count -gt 0 ]; then
        printf "  %-15s: ${GREEN}%3d${NC} files\n" "$lang" "$count"
    fi
done

# New vs Modified test files
echo -e "\n${CYAN}📈 Test File Changes${NC}"
echo "─────────────────────────────────────────────────────────────"

new_tests=$(git log --since="${START_DATE}" --until="${END_DATE}" \
    --name-status --diff-filter=A --pretty=format: -- \
    "*test*.py" "*.test.js" "*.spec.js" "*_test.go" | \
    grep "^A" | wc -l | tr -d ' ')

modified_tests=$(git log --since="${START_DATE}" --until="${END_DATE}" \
    --name-status --diff-filter=M --pretty=format: -- \
    "*test*.py" "*.test.js" "*.spec.js" "*_test.go" | \
    grep "^M" | wc -l | tr -d ' ')

echo -e "  New test files:      ${GREEN}+${new_tests}${NC}"
echo -e "  Modified test files: ${YELLOW}~${modified_tests}${NC}"

# Test categories
echo -e "\n${CYAN}🏷️  Test Categories${NC}"
echo "─────────────────────────────────────────────────────────────"

# Count by test type (heuristic based on file names)
unit_tests=$(git log --since="${START_DATE}" --until="${END_DATE}" \
    --name-only --pretty=format: -- "*unit*test*" "*test_unit*" | \
    grep -v "^$" | sort -u | wc -l | tr -d ' ')

integration_tests=$(git log --since="${START_DATE}" --until="${END_DATE}" \
    --name-only --pretty=format: -- "*integration*test*" "*test_integration*" | \
    grep -v "^$" | sort -u | wc -l | tr -d ' ')

e2e_tests=$(git log --since="${START_DATE}" --until="${END_DATE}" \
    --name-only --pretty=format: -- "*e2e*test*" "*test_e2e*" "*end*to*end*" | \
    grep -v "^$" | sort -u | wc -l | tr -d ' ')

echo -e "  Unit tests:        ${GREEN}${unit_tests}${NC}"
echo -e "  Integration tests: ${GREEN}${integration_tests}${NC}"
echo -e "  E2E tests:         ${GREEN}${e2e_tests}${NC}"

# Test lines of code
echo -e "\n${CYAN}📏 Test Code Volume${NC}"
echo "─────────────────────────────────────────────────────────────"

test_stats=$(git log --since="${START_DATE}" --until="${END_DATE}" \
    --numstat --pretty=format: -- "*test*.py" "*.test.js" "*.spec.js" | \
    awk 'NF==3 {add+=$1; del+=$2; files[$3]++} END {print add " " del " " length(files)}')

lines_added=$(echo $test_stats | cut -d' ' -f1)
lines_removed=$(echo $test_stats | cut -d' ' -f2)
files_changed=$(echo $test_stats | cut -d' ' -f3)

echo -e "  Lines added:    ${GREEN}+${lines_added}${NC}"
echo -e "  Lines removed:  ${RED}-${lines_removed}${NC}"
echo -e "  Net change:     ${YELLOW}$((lines_added - lines_removed))${NC}"
echo -e "  Files affected: ${BLUE}${files_changed}${NC}"

# Test commits
echo -e "\n${CYAN}💻 Test Commits${NC}"
echo "─────────────────────────────────────────────────────────────"

test_commits=$(git log --since="${START_DATE}" --until="${END_DATE}" \
    --grep="test" -i --oneline | wc -l | tr -d ' ')

ci_commits=$(git log --since="${START_DATE}" --until="${END_DATE}" \
    --grep="ci\|test\|spec" -i --oneline | wc -l | tr -d ' ')

echo -e "  Commits with 'test':     ${GREEN}${test_commits}${NC}"
echo -e "  CI/Test related commits: ${GREEN}${ci_commits}${NC}"

# Most tested areas
echo -e "\n${CYAN}🎯 Most Tested Areas${NC}"
echo "─────────────────────────────────────────────────────────────"

git log --since="${START_DATE}" --until="${END_DATE}" \
    --name-only --pretty=format: -- "*test*.py" "*.test.js" "*.spec.js" | \
    grep -E '\.(py|js|ts)$' | \
    sed 's|/[^/]*$||' | \
    sort | uniq -c | sort -rn | head -10 | \
    awk '{printf "  %4d tests in %s/\n", $1, $2}'

# Test to code ratio
echo -e "\n${CYAN}📊 Test to Code Ratio${NC}"
echo "─────────────────────────────────────────────────────────────"

# All code changes
all_code=$(git log --since="${START_DATE}" --until="${END_DATE}" \
    --numstat --pretty=format: -- "*.py" "*.js" "*.ts" "*.go" "*.java" | \
    awk 'NF==3 {add+=$1} END {print add}')

# Test code changes
test_code=$(git log --since="${START_DATE}" --until="${END_DATE}" \
    --numstat --pretty=format: -- "*test*.py" "*.test.js" "*.spec.js" "*_test.go" | \
    awk 'NF==3 {add+=$1} END {print add}')

if [ -n "$all_code" ] && [ "$all_code" -gt 0 ]; then
    ratio=$(awk "BEGIN {printf \"%.1f\", $test_code * 100 / $all_code}")
    echo -e "  Test lines added:     ${GREEN}${test_code}${NC}"
    echo -e "  Total lines added:    ${BLUE}${all_code}${NC}"
    echo -e "  Test percentage:      ${YELLOW}${ratio}%${NC}"
fi

# Coverage report (if available)
if command -v coverage &> /dev/null || command -v pytest-cov &> /dev/null; then
    echo -e "\n${CYAN}📈 Coverage Trend${NC}"
    echo "─────────────────────────────────────────────────────────────"
    echo "  Note: Run 'pytest --cov' or 'coverage report' for actual coverage data"
fi

# Generate report
REPORT_FILE="${REPORTS_DIR}/test-coverage-${START_DATE}-to-${END_DATE}.md"
cat > "$REPORT_FILE" << EOF
# Test Coverage Report
**Period:** ${START_DATE} to ${END_DATE}

## Summary
- New test files: ${new_tests}
- Modified test files: ${modified_tests}
- Test lines added: ${lines_added}
- Test commits: ${test_commits}

## Test Categories
- Unit tests: ${unit_tests}
- Integration tests: ${integration_tests}
- E2E tests: ${e2e_tests}

## Test to Code Ratio
- Test code: ${test_code:-0} lines
- Total code: ${all_code:-0} lines
- Percentage: ${ratio:-0}%

---
*Generated on $(date)*
EOF

echo -e "\n${GREEN}✅ Report saved to: ${REPORT_FILE}${NC}"
echo "═══════════════════════════════════════════════════════════"