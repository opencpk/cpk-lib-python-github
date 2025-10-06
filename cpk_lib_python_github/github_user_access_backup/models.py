"""Data models for GitHub team backup"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TeamAccess:
    """Team membership information"""

    name: str
    slug: str
    description: Optional[str]
    privacy: str
    role: str  # maintainer, member
    repositories: List[str] = field(default_factory=list)


@dataclass
class UserAccess:
    """User team access information (no direct repo access)"""

    username: str
    user_id: int
    email: Optional[str]
    role: str  # owner, admin, member
    teams: List[TeamAccess] = field(default_factory=list)


@dataclass
class OrganizationBackup:
    """Team-focused organization backup"""

    org_name: str
    backup_timestamp: str
    backup_type: str = "teams_only"
    users: List[UserAccess] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
