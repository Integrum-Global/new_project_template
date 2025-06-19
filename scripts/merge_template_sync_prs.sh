#!/bin/bash

# Script to merge template sync PRs across specific repositories
# Handles merge conflicts gracefully and provides detailed reporting

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# List of repositories to process
REPOS=(
    "talentverse"
    "pg"
    "corpsec"
    "tpc_shipping_migration"
    "tpc-migration"
    "ESG-report"
    "ai-coaching"
    "cdl_kailash_migration"
    "decisiontrackerfe"
    "GIC_update"
    "mcp_server"
    "cbm"
    "tpc_shipping_fe"
    "tpc_shipping"
    "market-insights"
    "narrated_derivations"
    "deal_sourcing"
    "tpc_core"
    "ai_coaching_demo"
)

# Organization name
ORG="Integrum-Global"

# Results tracking
declare -A results
successful_merges=0
failed_merges=0
no_prs=0
closed_prs=0

# Function to print section headers
print_header() {
    echo -e "\n${BOLD}${BLUE}========================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}========================================${NC}\n"
}

# Function to check if gh CLI is installed and authenticated
check_prerequisites() {
    print_header "Checking prerequisites"
    
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
        echo "Please install it from: https://cli.github.com/"
        exit 1
    fi
    
    if ! gh auth status &> /dev/null; then
        echo -e "${RED}Error: Not authenticated with GitHub CLI${NC}"
        echo "Please run: gh auth login"
        exit 1
    fi
    
    echo -e "${GREEN}✓ GitHub CLI is installed and authenticated${NC}"
}

# Function to get template sync PRs for a repository
get_template_sync_prs() {
    local repo=$1
    
    gh pr list \
        --repo "${ORG}/${repo}" \
        --state open \
        --json number,title,author,createdAt,headRefName,body,mergeable,mergeStateStatus \
        --limit 100 2>/dev/null | \
    jq -r '.[] | select(
        (.title | contains("Sync template updates")) or
        (.headRefName | contains("template-sync-")) or
        (.body | contains("Automated template sync from")) or
        (.body | contains("What was synced (always replaced)")) or
        (.body | contains("This PR automatically syncs updates from the template repository"))
    )'
}

# Function to merge a PR
merge_pr() {
    local repo=$1
    local pr_number=$2
    
    # First check if PR is mergeable
    local pr_status=$(gh pr view "${pr_number}" --repo "${ORG}/${repo}" --json mergeable,mergeStateStatus 2>/dev/null)
    local mergeable=$(echo "$pr_status" | jq -r '.mergeable')
    local merge_state=$(echo "$pr_status" | jq -r '.mergeStateStatus')
    
    if [[ "$mergeable" == "CONFLICTING" ]]; then
        echo -e "    ${YELLOW}⚠️  PR has merge conflicts - skipping${NC}"
        return 1
    fi
    
    if [[ "$merge_state" == "BLOCKED" ]]; then
        echo -e "    ${YELLOW}⚠️  PR is blocked (likely by status checks) - attempting merge anyway${NC}"
    fi
    
    # Attempt to merge
    if gh pr merge "${pr_number}" \
        --repo "${ORG}/${repo}" \
        --merge \
        --delete-branch \
        --admin 2>/dev/null; then
        echo -e "    ${GREEN}✓ Successfully merged PR #${pr_number}${NC}"
        return 0
    else
        # Try without admin flag if first attempt fails
        if gh pr merge "${pr_number}" \
            --repo "${ORG}/${repo}" \
            --merge \
            --delete-branch 2>/dev/null; then
            echo -e "    ${GREEN}✓ Successfully merged PR #${pr_number}${NC}"
            return 0
        else
            echo -e "    ${RED}✗ Failed to merge PR #${pr_number}${NC}"
            return 1
        fi
    fi
}

# Function to close a PR
close_pr() {
    local repo=$1
    local pr_number=$2
    
    if gh pr close "${pr_number}" \
        --repo "${ORG}/${repo}" \
        --comment "Closing outdated template sync PR. A newer sync is available." 2>/dev/null; then
        echo -e "    ${GREEN}✓ Successfully closed PR #${pr_number}${NC}"
        return 0
    else
        echo -e "    ${RED}✗ Failed to close PR #${pr_number}${NC}"
        return 1
    fi
}

# Function to process a single repository
process_repo() {
    local repo=$1
    echo -e "\n${BOLD}📦 Processing: ${repo}${NC}"
    
    # Get all template sync PRs
    local prs=$(get_template_sync_prs "$repo")
    
    if [[ -z "$prs" ]]; then
        echo -e "  ${YELLOW}No template sync PRs found${NC}"
        results["$repo"]="no_prs"
        ((no_prs++))
        return
    fi
    
    # Count PRs
    local pr_count=$(echo "$prs" | jq -s 'length')
    echo -e "  Found ${BOLD}${pr_count}${NC} template sync PR(s)"
    
    # Sort PRs by creation date (newest first) and process
    local sorted_prs=$(echo "$prs" | jq -s 'sort_by(.createdAt) | reverse')
    local latest_merged=false
    
    echo "$sorted_prs" | jq -c '.[]' | while IFS= read -r pr; do
        local pr_number=$(echo "$pr" | jq -r '.number')
        local pr_title=$(echo "$pr" | jq -r '.title')
        local pr_created=$(echo "$pr" | jq -r '.createdAt')
        local pr_branch=$(echo "$pr" | jq -r '.headRefName')
        
        echo -e "\n  ${BOLD}PR #${pr_number}:${NC} ${pr_title}"
        echo -e "    Created: ${pr_created}"
        echo -e "    Branch: ${pr_branch}"
        
        if [[ "$latest_merged" == "false" ]]; then
            # Try to merge the most recent PR
            echo -e "    ${BLUE}→ Attempting to merge (most recent PR)...${NC}"
            if merge_pr "$repo" "$pr_number"; then
                results["$repo"]="merged"
                ((successful_merges++))
                latest_merged=true
            else
                results["$repo"]="failed"
                ((failed_merges++))
                # Don't try to merge older PRs if the latest one failed
                echo -e "    ${YELLOW}Skipping older PRs since latest merge failed${NC}"
                break
            fi
        else
            # Close older PRs
            echo -e "    ${BLUE}→ Closing older PR...${NC}"
            if close_pr "$repo" "$pr_number"; then
                ((closed_prs++))
            fi
        fi
    done
}

# Function to print summary
print_summary() {
    print_header "Summary Report"
    
    echo -e "${BOLD}Overall Statistics:${NC}"
    echo -e "  ${GREEN}✓ Successful merges: ${successful_merges}${NC}"
    echo -e "  ${RED}✗ Failed merges: ${failed_merges}${NC}"
    echo -e "  ${YELLOW}○ Repositories with no PRs: ${no_prs}${NC}"
    echo -e "  ${BLUE}◉ Total older PRs closed: ${closed_prs}${NC}"
    echo -e "  ${BOLD}  Total repositories processed: ${#REPOS[@]}${NC}"
    
    echo -e "\n${BOLD}Detailed Results:${NC}"
    for repo in "${REPOS[@]}"; do
        case "${results[$repo]:-unknown}" in
            "merged")
                echo -e "  ${GREEN}✓${NC} ${repo}: Successfully merged latest PR"
                ;;
            "failed")
                echo -e "  ${RED}✗${NC} ${repo}: Failed to merge (conflicts or other issues)"
                ;;
            "no_prs")
                echo -e "  ${YELLOW}○${NC} ${repo}: No template sync PRs found"
                ;;
            *)
                echo -e "  ${RED}?${NC} ${repo}: Unknown status"
                ;;
        esac
    done
    
    if [[ $failed_merges -gt 0 ]]; then
        echo -e "\n${YELLOW}⚠️  Action Required:${NC}"
        echo -e "Some PRs failed to merge due to conflicts or other issues."
        echo -e "Please review and resolve these manually."
    fi
}

# Main execution
main() {
    print_header "Template Sync PR Merger"
    echo "This script will merge the latest template sync PR in each repository"
    echo "and close any older template sync PRs."
    
    check_prerequisites
    
    print_header "Processing Repositories"
    
    for repo in "${REPOS[@]}"; do
        process_repo "$repo"
    done
    
    print_summary
}

# Run main function
main