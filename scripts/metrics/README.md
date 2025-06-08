# GitHub Metrics Tracking System

A comprehensive metrics tracking system for monitoring project health, development velocity, and team productivity.

## 🚀 Quick Start

```bash
# Make scripts executable
chmod +x scripts/metrics/*.sh

# Track today's metrics
./scripts/metrics/daily-metrics.sh

# Generate weekly report
./scripts/metrics/weekly-summary.sh

# Full metrics for custom date range
./scripts/metrics/github-metrics.sh "2024-01-01" "2024-01-31"
```

## 📊 Available Scripts

### 1. **github-metrics.sh** - Comprehensive Metrics Report
The main metrics script that tracks:
- ✅ Features completed (PRs with feat: prefix)
- 🐛 Issues resolved
- 🧪 Tests written
- 📚 Documentation updated
- 👥 Contributor activity
- 🔍 Code quality metrics

**Usage:**
```bash
# Last 7 days (default)
./scripts/metrics/github-metrics.sh

# Custom date range
./scripts/metrics/github-metrics.sh "2024-01-15" "2024-01-31"

# Export as JSON
./scripts/metrics/github-metrics.sh "2024-01-15" "2024-01-31" json
```

### 2. **daily-metrics.sh** - Daily Activity Tracker
Quick daily snapshot with:
- Today's activity summary
- Comparison with yesterday
- Active pull requests
- Recent commits
- CSV logging for trends

**Usage:**
```bash
# Today's metrics
./scripts/metrics/daily-metrics.sh

# Specific date
./scripts/metrics/daily-metrics.sh "2024-01-15"
```

### 3. **weekly-summary.sh** - Weekly Report
Visual weekly summary with:
- Daily activity breakdown
- Bar chart visualizations
- Top contributors
- Week-over-week comparison

**Usage:**
```bash
# This week
./scripts/metrics/weekly-summary.sh

# Last week
./scripts/metrics/weekly-summary.sh lastweek

# Custom week
./scripts/metrics/weekly-summary.sh "2024-01-15"
```

### 4. **test-coverage-tracker.sh** - Test Analysis
Specialized test tracking:
- New vs modified test files
- Test categories (unit, integration, etc.)
- Coverage trends
- Test commit analysis

**Usage:**
```bash
./scripts/metrics/test-coverage-tracker.sh
```

### 5. **feature-tracker.sh** - Feature Development
Track feature lifecycle:
- Feature PR status
- Development timeline
- Feature velocity
- Category breakdown

**Usage:**
```bash
./scripts/metrics/feature-tracker.sh "2024-01-01" "2024-01-31"
```

## 📁 Directory Structure

```
scripts/metrics/
├── README.md               # This file
├── github-metrics.sh       # Main comprehensive report
├── daily-metrics.sh        # Daily tracking
├── weekly-summary.sh       # Weekly visualization
├── test-coverage-tracker.sh # Test analysis
├── feature-tracker.sh      # Feature tracking
├── logs/                   # Historical data
│   ├── daily-metrics.csv   # Daily metrics log
│   └── metrics-*.log       # Report archives
└── reports/                # Generated reports
    └── *.json             # JSON exports
```

## 🔧 Configuration

### Prerequisites
- GitHub CLI (`gh`) - [Install](https://cli.github.com/)
- Git
- Bash 4.0+

### Authentication
```bash
# Authenticate with GitHub
gh auth login
```

### Environment Variables
```bash
# Optional: Set default date format
export METRICS_DATE_FORMAT="%Y-%m-%d"

# Optional: Set report directory
export METRICS_REPORT_DIR="/path/to/reports"
```

## 📈 Integration Ideas

### 1. CI/CD Pipeline
```yaml
# .github/workflows/weekly-metrics.yml
name: Weekly Metrics Report
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
jobs:
  metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: ./scripts/metrics/weekly-summary.sh
      - uses: actions/upload-artifact@v3
        with:
          name: weekly-report
          path: scripts/metrics/reports/
```

### 2. Slack Integration
```bash
# Send daily metrics to Slack
./scripts/metrics/daily-metrics.sh | \
  curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"$(cat)\"}" \
  YOUR_SLACK_WEBHOOK_URL
```

### 3. Dashboard Integration
Export JSON reports for visualization in tools like:
- Grafana
- Datadog
- Custom dashboards

### 4. Git Hooks
```bash
# .git/hooks/pre-push
#!/bin/bash
echo "Today's metrics:"
./scripts/metrics/daily-metrics.sh
```

## 📊 Metrics Explained

### Features Completed
- Tracks PRs with `feat:`, `feature:`, or `Feature:` prefix
- Shows feature velocity and development trends

### Issues Resolved
- Closed issues within date range
- Helps track bug resolution rate

### Tests Written
- New test files added
- Test lines modified
- Test coverage trends

### Documentation Updated
- Documentation files changed
- Knowledge transfer measurement
- Maintenance tracking

## 🎯 Best Practices

1. **Run daily metrics** as part of your standup routine
2. **Review weekly summaries** in team meetings
3. **Export JSON** for long-term trend analysis
4. **Set up alerts** for unusual patterns
5. **Customize scripts** for your team's workflow

## 🤝 Contributing

To add new metrics:

1. Create a new script in `scripts/metrics/`
2. Follow the existing naming convention
3. Use the color variables for consistent output
4. Add documentation to this README
5. Test with various date ranges

## 📝 License

This metrics system is part of the project template and follows the same license.