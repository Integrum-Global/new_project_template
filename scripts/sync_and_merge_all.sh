#!/bin/bash

# One-command script to trigger template syncs and merge PRs
# This combines the workflow trigger and PR merge operations

set -euo pipefail

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}Template Sync and Merge - Complete Workflow${NC}\n"

# Step 1: Trigger template syncs
echo -e "${BOLD}Step 1: Triggering template sync workflows...${NC}"
if python scripts/trigger_template_sync.py; then
    echo -e "${GREEN}✓ Successfully triggered sync workflows${NC}\n"
else
    echo -e "${YELLOW}⚠️  Some workflows may have failed to trigger${NC}\n"
fi

# Step 2: Wait for workflows to complete
echo -e "${BOLD}Step 2: Waiting for workflows to complete...${NC}"
echo -e "${YELLOW}This typically takes 2-5 minutes. You can check progress at:${NC}"
echo -e "${BLUE}https://github.com/Integrum-Global?tab=repositories${NC}"
echo -e "Look for the Actions tab in each repository\n"

# Countdown timer
for i in {180..1}; do
    printf "\rWaiting... %3d seconds remaining" $i
    sleep 1
done
printf "\r${GREEN}✓ Wait period complete                    ${NC}\n\n"

# Step 3: Merge PRs
echo -e "${BOLD}Step 3: Merging template sync PRs...${NC}"
if python scripts/merge_specific_repos_prs.py; then
    echo -e "\n${GREEN}✓ PR merge process completed${NC}"
else
    echo -e "\n${YELLOW}⚠️  Some PRs may require manual intervention${NC}"
fi

echo -e "\n${BOLD}${GREEN}Template sync and merge workflow completed!${NC}"
echo -e "${YELLOW}Check the summary above for any repos requiring manual attention.${NC}"