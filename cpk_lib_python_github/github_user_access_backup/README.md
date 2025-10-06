# 📊 GitHub User Access Backup

A powerful CLI tool for backing up GitHub organization team memberships before SSO enforcement. This tool captures team memberships and repository access patterns to help restore them after SSO implementation, when team memberships are lost but direct repository access is preserved.

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
- [Command Reference](#-command-reference)
- [Environment Variables](#-environment-variables)
- [Sample Outputs](#-sample-outputs)
- [Common Use Cases](#-common-use-cases)

## ✨ Features

- 👥 **Team Membership Backup**: Capture complete team memberships before SSO enforcement
- 📚 **Repository Access Mapping**: Document which teams have access to which repositories
- 📊 **Multiple Export Formats**: Excel, CSV, and JSON exports with rich formatting
- 🎯 **SSO-Focused**: Optimized for pre-SSO backup scenarios
- 🔧 **Organized Output**: Clean folder structure with categorized files
- ⚡ **High Performance**: Parallel processing with configurable batch sizes
- 🔐 **Security Aware**: 2FA status tracking and permission validation
- 📈 **Comprehensive Analysis**: Detailed user and team statistics

## 🚀 Installation

### Prerequisites

- GitHub Personal Access Token with `read:org` and `admin:org` permissions
- Python 3.8+
- Access to the GitHub organization you want to backup

### Install from Source

```bash
pip install git+https://github.com/opencpk/cpk-lib-python-github.git@main
```


### Verify Installation

```bash
github-user-access-backup --help
```

## 🎯 Quick Start

### 1. Create a GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. github-app-token-generator --org YOUR_ORG will generate the token for you (your app token needs to have enough access to the org you are trying to generate the report for)
3.


### 2. Basic Backup with Excel Export

```bash
github-user-access-backup --org YOUR_ORG --token ghp_YOUR_TOKEN --excel
```

or

```bash
export GITHUB_TOKEN=ghp_YOUR_TOKEN
github-user-access-backup --org YOUR_ORG  --excel
```


### 3. Test with Limited Users

```bash
github-user-access-backup --org YOUR_ORG --token ghp_YOUR_TOKEN --excel --limit-users 10
```

## 📖 Usage Examples

### 📊 Basic Team Backup

#### Standard backup with Excel export (recommended):
```bash
github-user-access-backup --org myorg --token ghp_xxxxx --excel
```

#### Backup with all export formats:
```bash
github-user-access-backup --org myorg --token ghp_xxxxx --excel --multi-csv --structured-json
```

#### Test mode with limited users:
```bash
github-user-access-backup --org myorg --token ghp_xxxxx --excel --limit-users 25
```


### ⚡ Performance Tuning

#### Adjust batch size and worker threads:
```bash
github-user-access-backup --org myorg --token ghp_xxxxx --excel --batch-size 50 --max-workers 10
```



### 📋 Export Format Options

#### Excel:
```bash
github-user-access-backup --org myorg --token ghp_xxxxx --excel
```

#### Multiple focused CSV files:
```bash
github-user-access-backup --org myorg --token ghp_xxxxx --multi-csv
```

#### Clean structured JSON:
```bash
github-user-access-backup --org myorg --token ghp_xxxxx --structured-json
```

#### All formats combined:
```bash
github-user-access-backup --org myorg --token ghp_xxxxx --excel --multi-csv --structured-json --csv
```

## 📚 Command Reference

| Command | Description | Default |
|---------|-------------|---------|
| `--org <name>` | **Required.** Organization name to backup | - |
| `--token <token>` | **Required.** GitHub PAT with org permissions | - |
| `--excel` | Export to rich formatted Excel file | Enabled by default |
| `--multi-csv` | Export to multiple focused CSV files | - |
| `--structured-json` | Export to clean, team-focused JSON | - |
| `--batch-size <num>` | Users processed per batch | `20` |
| `--max-workers <num>` | Maximum worker threads | `5` |
| `--limit-users <num>` | Limit users for testing | All users |
| `--help` | Show help message | - |

## 🌍 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxxxxxxxxxxxx` |



### ❌ Permission Error Output

```bash
$ github-user-access-backup --org myorg --token ghp_insufficient_perms --excel
```

**Output:**
```
🚀 Starting TEAMS-ONLY backup for organization: myorg
🔐 Testing permissions for organization: myorg
✅ Authenticated as: myusername
❌ Cannot access organization 'myorg'. Please check:
  - Organization name is correct
  - You are a member of the organization
  - Your token has 'read:org' permissions
❌ Backup failed: Cannot access organization 'myorg'
```

### 🧪 Test Mode Output

```bash
$ github-user-access-backup --org myorg --token ghp_xxxxx --excel --limit-users 5
```

**Output:**
```
🚀 Starting TEAMS-ONLY backup for organization: myorg
📦 Batch size: 20, Max workers: 5
🎯 Focus: Team memberships (direct repo access preserved during SSO)
🧪 TEST MODE: Users limited to 5
============================================================
🔍 Fetching organization members for myorg...
🧪 Limited to first 5 users for testing (original: 127)
👥 Fetching teams for myorg...
✅ Found 45 teams
...
📁 Created output directory: /path/to/github_backup_myorg_20241001_143022_test
```

### 📊 Excel File Sheets Preview

The Excel export contains these formatted sheets:

**Teams Overview:**
| Team Name | Team Slug | Privacy | Members | Repositories |
|-----------|-----------|---------|---------|--------------|
| Backend Team | backend-team | closed | 12 | 8 |
| Frontend Team | frontend-team | closed | 15 | 6 |

**Team Memberships (grouped by team):**
```
Backend Team
12 members
Username    | Email           | Team Role | Org Role | 2FA
john.doe    | john@company.com| member    | member   | YES
jane.smith  | jane@company.com| maintainer| member   | YES
```

**Team Repositories (grouped by team):**
```
Backend Team
8 repositories
Repository Name | Full Path        | Organization
api-service     | myorg/api-service| myorg
user-service    | myorg/user-svc   | myorg
```

## 🎯 Common Use Cases

### 1. **Pre-SSO Backup (Primary Use Case)**

```bash
# Complete backup before SSO enforcement
github-user-access-backup --org myorg --token ghp_xxxxx --excel --multi-csv

# Store the backup safely
mv github_backup_myorg_* ./sso-preparation-backups/
```

### 2. **Large Organization Backup**

```bash
# Conservative settings for large orgs (1000+ users)
github-user-access-backup \
  --org large-org \
  --token ghp_xxxxx \
  --excel \
  --batch-size 10 \
  --max-workers 3
```

### 3. **Testing and Validation**

```bash
# Test with a small subset first
github-user-access-backup --org myorg --token ghp_xxxxx --excel --limit-users 50

# Validate results before full backup
github-user-access-backup --org myorg --token ghp_xxxxx --excel
```

### 4. **Team Audit and Analysis**

```bash
# Export all formats for comprehensive analysis
github-user-access-backup \
  --org myorg \
  --token ghp_xxxxx \
  --excel \
  --multi-csv \
  --structured-json
```

### 5. **CI/CD Integration**

```bash
#!/bin/bash
# Automated backup script
export GITHUB_TOKEN=$BACKUP_TOKEN
export GITHUB_ORG=myorg

# Create timestamped backup
github-user-access-backup \
  --org $GITHUB_ORG \
  --token $GITHUB_TOKEN \
  --excel \
  --structured-json \
  --output-dir "./backups/$(date +%Y%m%d)"

# Archive and store
tar -czf "github-backup-$(date +%Y%m%d).tar.gz" ./backups/$(date +%Y%m%d)
```

### 6. **Post-SSO Team Restoration**

After SSO enforcement, use the backup files to restore team memberships:

1. **Excel Method** (Recommended):
   - Open the `.xlsx` file
   - Use the "Team Memberships" sheet
   - Manually recreate teams and add members

2. **CSV Method**:
   - Use `team_memberships.csv` for systematic restoration
   - Script the restoration using GitHub API

3. **JSON Method**:
   - Parse the structured JSON for automated restoration
   - Use GitHub CLI or API scripts

## 📋 Export Formats Explained

### 📊 Excel Export (Recommended)
- **Teams Overview**: Summary of all teams with member/repo counts
- **Team Memberships**: Users grouped by team with roles and 2FA status
- **Team Repositories**: Repository access grouped by team
- **Users Summary**: All users with their team information
- **Users Without Teams**: Users not in any teams

### 📄 Multiple CSV Export
- **teams_overview.csv**: Team summary data
- **team_memberships.csv**: All team memberships
- **team_repositories.csv**: Team repository access
- **users_summary.csv**: User overview
- **users_without_teams.csv**: Orphaned users

### 🗂️ JSON Exports
- **Standard JSON**: Complete raw backup data
- **Structured JSON**: Clean, team-centric format for processing

## ⚠️ Important Notes

### SSO Impact
- **Team memberships will be lost** during SSO enforcement
- **Direct repository access is preserved**
- This tool captures the team structure for restoration

### Rate Limiting
- Uses GitHub's REST API with built-in rate limiting
- Adjust `--batch-size` and `--max-workers` for large organizations
- The tool automatically handles rate limits

### Token Requirements
- **Personal Access Token** (ghp_) required
- **GitHub App tokens** (ghs_) are not supported
- Requires `read:org` and `admin:org` scopes

## 🐍 Python Usage

If you prefer to use this tool as a Python library:

### Basic Usage

```python
from cpk_lib_python_github.github_user_access_backup import GitHubTeamsBackup, BackupConfig
from cpk_lib_python_github.github_user_access_backup import export_to_excel, export_to_structured_json

# Configure backup
config = BackupConfig(
    token='ghp_your_token',
    org_name='myorg',
    batch_size=20,
    max_workers=5
)

# Perform backup
backup_tool = GitHubTeamsBackup(config)
backup = backup_tool.backup_organization()

# Export results
export_to_excel(backup, 'myorg_backup.xlsx')
export_to_structured_json(backup, 'myorg_backup.json')

print(f"Backed up {len(backup.users)} users across {backup.summary['total_teams']} teams")
```

### Advanced Usage

```python
from cpk_lib_python_github.github_user_access_backup import *

# Custom configuration
config = BackupConfig(
    token='ghp_your_token',
    org_name='myorg',
    batch_size=50,
    max_workers=10,
    limit_users=100  # For testing
)

# Perform backup with error handling
try:
    backup_tool = GitHubTeamsBackup(config)
    backup = backup_tool.backup_organization()

    # Export all formats
    export_to_excel(backup, 'backup.xlsx')
    export_to_multiple_csvs(backup, 'backup')
    export_to_structured_json(backup, 'backup_structured.json')

    print("✅ Backup completed successfully!")

except Exception as e:
    print(f"❌ Backup failed: {e}")
```

## 📄 License

This project is licensed under the GPLv3 License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 🔗 Related Tools

- [GitHub App Token Generator](./github_app_token_generator/) - Generate GitHub App installation tokens
- [GitHub CLI](https://cli.github.com/) - Official GitHub command line tool

## 📞 Support

For issues and questions:
1. Check the command help: `github-user-access-backup --help`
2. Review the sample outputs above
3. Submit an issue on GitHub
