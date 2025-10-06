"""Configuration for GitHub backup"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BackupConfig:
    """Configuration for GitHub team backup"""

    token: str
    org_name: str
    batch_size: int = 20
    max_workers: int = 5
    limit_users: Optional[int] = None

    def __post_init__(self):
        """Validate configuration"""
        if not self.token:
            raise ValueError("GitHub token is required")
        if not self.org_name:
            raise ValueError("Organization name is required")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        if self.max_workers <= 0:
            raise ValueError("Max workers must be positive")
        if self.limit_users is not None and self.limit_users <= 0:
            raise ValueError("Limit users must be positive")


# Default configuration values
DEFAULT_BATCH_SIZE = 20
DEFAULT_MAX_WORKERS = 5
DEFAULT_USER_AGENT = "GitHub-Teams-Backup-Script/1.0"
GITHUB_API_BASE_URL = "https://api.github.com"
