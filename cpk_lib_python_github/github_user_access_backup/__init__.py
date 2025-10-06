"""GitHub User Access Backup Library

A library for backing up GitHub organization team memberships before SSO enforcement.
"""

from .backup import GitHubTeamsBackup
from .exporters import (
    export_to_csv,
    export_to_excel,
    export_to_json,
    export_to_multiple_csvs,
    export_to_structured_json,
)
from .main import main
from .models import OrganizationBackup, TeamAccess, UserAccess

__version__ = "1.0.0"
__all__ = [
    "TeamAccess",
    "UserAccess",
    "OrganizationBackup",
    "GitHubTeamsBackup",
    "export_to_json",
    "export_to_csv",
    "export_to_multiple_csvs",
    "export_to_excel",
    "export_to_structured_json",
    "main",
]
