# 🔑 GitHub App Token Generator

A powerful CLI tool for generating, managing, and analyzing GitHub App installation tokens. This tool simplifies the process of working with GitHub Apps by providing easy token generation, validation, and comprehensive app analysis.

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
- [Command Reference](#-command-reference)
- [Environment Variables](#-environment-variables)
- [Sample Outputs](#-sample-outputs)
- [Common Use Cases](#-common-use-cases)
- [Python SDK Usage](#-python-sdk-usage)

## ✨ Features

- 🔐 **Token Generation**: Generate GitHub App installation tokens for organizations or specific installations
- ✅ **Token Validation**: Validate existing tokens and check their permissions
- 🗑️ **Token Revocation**: Safely revoke tokens with confirmation prompts
- 📊 **App Analysis**: Comprehensive analysis of GitHub App permissions, installations, and repositories
- 🔧 **Flexible Authentication**: Support for both private key files and direct key content
- 🌍 **Environment Variables**: Full support for environment-based configuration
- 🎨 **Rich Output**: Colorized, well-formatted output with emojis and clear sections
- 📝 **Debug Mode**: Detailed logging for troubleshooting

## 🚀 Installation

### Prerequisites

- A GitHub App with appropriate permissions
- GitHub App private key

### Install from Source (later on this will be published to pypi)

```bash
pip install git+https://github.com/opencpk/cpk-lib-python-github.git@main
```

### Verify Installation

```bash
github-app-token-generator --help
```

## 🎯 Quick Start

### 1. Set up Environment Variables (or pass it by param)

```bash
export APP_ID=${{YOUR_APP_ID}}
export PRIVATE_KEY_PATH=bot.pem
```

### 2. Generate a Token for Your Organization

```bash
github-app-token-generator --org orginc
```

### 3. List All Available Installations

```bash
github-app-token-generator --list-installations
```

## 📖 Usage Examples

### 🔑 Token Generation

#### Generate token by organization name:
```bash
github-app-token-generator --org orginc --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

#### Generate token by installation ID:
```bash
github-app-token-generator --installation-id ${{YOUR_INST_ID}} --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

#### Using private key content directly:
```bash
github-app-token-generator --org orginc --app-id ${{YOUR_APP_ID}} --private-key "$(cat /path/to/bot.pem)"
```

### 📋 Installation Management

#### List all installations:
```bash
github-app-token-generator --list-installations --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

#### Show installations (default behavior):
```bash
github-app-token-generator --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

### 🔍 App Analysis

#### Comprehensive app analysis:
```bash
github-app-token-generator --analyze-app --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

### 🔐 Token Management

#### Validate an existing token:
```bash
github-app-token-generator --validate-token ghs_TOKEN
```

#### Revoke a token (with confirmation):
```bash
github-app-token-generator --revoke-token ghs_TOKEN
```

#### Force revoke a token (no confirmation):
```bash
github-app-token-generator --revoke-token ghs_TOKEN --force
```

### 🐛 Debug & Help

#### Enable debug logging:
```bash
github-app-token-generator --debug --org orginc --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

#### Show help:
```bash
github-app-token-generator --help
```

## 📚 Command Reference

| Command | Description | Required Arguments |
|---------|-------------|-------------------|
| `--org <name>` | Generate token for organization | `--app-id`, `--private-key-path` or `--private-key` |
| `--installation-id <id>` | Generate token for installation ID | `--app-id`, `--private-key-path` or `--private-key` |
| `--list-installations` | List all app installations | `--app-id`, `--private-key-path` or `--private-key` |
| `--analyze-app` | Comprehensive app analysis | `--app-id`, `--private-key-path` or `--private-key` |
| `--validate-token <token>` | Validate existing token | None |
| `--revoke-token <token>` | Revoke existing token | None |
| `--force` | Skip confirmation prompts | Used with `--revoke-token` |
| `--debug` | Enable debug logging | None |
| `--help` | Show help message | None |

## 🌍 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_ID` | GitHub App ID | `${{YOUR_APP_ID}}` |
| `PRIVATE_KEY_PATH` | Path to private key file | `bot.pem` |
| `PRIVATE_KEY` | Private key content directly  | `"$(cat /path/to/bot.pem)"` |

### Setting Environment Variables

```bash
# Using file path (recommended)
export APP_ID=${{YOUR_APP_ID}}
export PRIVATE_KEY_PATH=bot.pem

# Using key content from file
export APP_ID=${{YOUR_APP_ID}}
export PRIVATE_KEY="$(cat /path/to/bot.pem)"

# Then use shorter commands
github-app-token-generator --org orginc
github-app-token-generator --list-installations
github-app-token-generator --analyze-app
```

## 🎨 Sample Outputs

### 📋 List Installations Output

```bash
$ github-app-token-generator --list-installations --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

**Output:**
```
=== Available GitHub App Installations ===

Installation ID      | Account              | Target Type
------------------------------------------------------------
${{YOUR_INST_ID}}    | orginc               | Organization
87654321             | mycompany            | Organization
12345678             | individual-user      | User

ℹ️  Found 3 installation(s)
💡 Use --org <org-name> or --installation-id <id> to get a token
```

### 🔑 Token Generation Output

```bash
$ github-app-token-generator --org orginc --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

**Output:**
```
ghs_TOKEN
🔑 ✅ Token generated for organization 'orginc'
```

### ✅ Token Validation Output

```bash
$ github-app-token-generator --validate-token ghs_TOKEN
```

**Output:**
```
✅ Token is valid
  Type: GitHub App Installation Token
  Repositories: 25
  Scopes: GitHub App permissions
  Rate limit: 4847/5000
```

### ❌ Invalid Token Output

```bash
$ github-app-token-generator --validate-token ghs_InvalidToken123456789
```

**Output:**
```
❌ Token is invalid or expired
  Reason: Invalid or expired token
```

### 📊 App Analysis Output

```bash
$ github-app-token-generator --analyze-app --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

**Output:**
```
=== GitHub App Analysis ===

🤖 App Information
  ID: ${{YOUR_APP_ID}}
  Name: Your org GitHub Bot
  Slug: org-github-bot
  Description: Automated GitHub operations for Your org
  Owner: orginc
  Owner Type: Organization
  URL: https://github.com/apps/org-github-bot
  Created: 2024-01-15

📍 Installation Summary
  Total Installations: 2
  Total Repositories: 47
  Installed On:
    ✅ orginc (Organization) - 2024-01-15
    ✅ org-dev (Organization) - 2024-02-01

🔐 App Permissions
  ✏️ contents: write
  👁️ metadata: read
  ✏️ pull_requests: write
  👁️ issues: read
  🔧 actions: write

📡 Subscribed Events
  📨 issues
  📨 pull_request
  📨 push
  📨 release

📚 Accessible Repositories (47 total)
  orginc:
    • orginc/main-website
    • orginc/api-backend
    • orginc/mobile-app
    • orginc/infrastructure
  org-dev:
    • org-dev/test-repo
    • org-dev/experimental-features
    ... and 41 more repositories
```

### 🗑️ Token Revocation Output

```bash
$ github-app-token-generator --revoke-token ghs_TOKEN
```

**Output:**
```
⚠️  Are you sure you want to revoke this token? (y/N): y
✅ Token revoked successfully
```

### 🚫 Organization Not Found Output

```bash
$ github-app-token-generator --org nonexistent-org --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

**Output:**
```
❌ No installation found for organization: nonexistent-org
```

### 🐛 Debug Mode Output

```bash
$ github-app-token-generator --debug --org orginc --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

**Output:**
```
2024-06-10 14:30:15,123 - __main__ - DEBUG - Debug logging enabled
2024-06-10 14:30:15,124 - __main__ - INFO - Starting GitHub App token generation
2024-06-10 14:30:15,124 - __main__ - INFO - App ID: ${{YOUR_APP_ID}}
2024-06-10 14:30:15,124 - __main__ - INFO - Private key path: bot.pem
2024-06-10 14:30:15,125 - __main__ - DEBUG - Reading private key from file: bot.pem
2024-06-10 14:30:15,126 - __main__ - DEBUG - Successfully read private key from: bot.pem
2024-06-10 14:30:15,127 - __main__ - DEBUG - Successfully generated JWT for app ID: ${{YOUR_APP_ID}}
2024-06-10 14:30:15,128 - __main__ - DEBUG - Fetching GitHub App installations
2024-06-10 14:30:15,456 - __main__ - INFO - Found 2 installations
2024-06-10 14:30:15,457 - __main__ - INFO - Looking for installation for organization: orginc
2024-06-10 14:30:15,458 - __main__ - INFO - Found installation ID ${{YOUR_INST_ID}} for organization: orginc
2024-06-10 14:30:15,459 - __main__ - DEBUG - Requesting access token for installation ID: ${{YOUR_INST_ID}}
2024-06-10 14:30:15,678 - __main__ - INFO - Successfully obtained access token for installation: ${{YOUR_INST_ID}}
ghs_TOKEN
🔑 ✅ Token generated for organization 'orginc'
```

## 🎯 Common Use Cases

### 1. **CI/CD Pipeline Token Generation**

```bash
# In your CI/CD script
export APP_ID=${{YOUR_APP_ID}}
export PRIVATE_KEY="$GITHUB_APP_PRIVATE_KEY"  # From secrets

TOKEN=$(github-app-token-generator --org orginc)
# Use $TOKEN for GitHub API calls
curl -H "Authorization: token $TOKEN" https://api.github.com/repos/orginc/myrepo
```

### 2. **Development Environment Setup**

```bash
# Set up environment
export APP_ID=${{YOUR_APP_ID}}
export PRIVATE_KEY_PATH=bot.pem

# Generate token for development
TOKEN=$(github-app-token-generator --org orginc)
echo "Your token: $TOKEN"
```

### 3. **Token Lifecycle Management**

```bash
# Generate token
TOKEN=$(github-app-token-generator --org orginc --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem)

# Validate token before using
github-app-token-generator --validate-token $TOKEN

# Use token for operations
# ... your work ...

# Clean up - revoke token
github-app-token-generator --revoke-token $TOKEN --force
```

### 4. **App Analysis **

```bash
# Check app installations and permissions
github-app-token-generator --analyze-app --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem

# List all installations
github-app-token-generator --list-installations --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem

# Validate existing tokens
github-app-token-generator --validate-token ghs_TOKEN
```

### 5. **Quick Token for Specific Installation**

```bash
# If you know the installation ID
github-app-token-generator --installation-id ${{YOUR_INST_ID}} --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
github-app-token-generator --debug --org orginc --app-id ${{YOUR_APP_ID}} --private-key-path bot.pem
```

This will show:
- 📝 Detailed API requests and responses
- 🔍 JWT generation details
- 📊 Installation lookup process
- ⚠️ Warning messages and errors


### Log Files

The tool automatically creates log files:
- **Location**: `github_app_token.log` (in current directory)
- **Content**: All operations, errors, and debug information
- **Rotation**: Append mode (consider rotating large files)

## 📄 License

This project is licensed under the GPLv3 License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.
