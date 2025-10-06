"""Shared test fixtures for GitHub User Access Backup"""

import time
from unittest.mock import Mock

import pytest  # pylint: disable=import-error


@pytest.fixture
def mock_github_response():
    """Create a mock GitHub API response"""
    response = Mock()
    response.status_code = 200
    response.headers = {
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Reset": str(int(time.time()) + 3600),
        "X-RateLimit-Limit": "5000",
    }
    response.json.return_value = {"test": "data"}
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def mock_404_response():
    """Create a mock 404 response"""
    response = Mock()
    response.status_code = 404
    response.headers = {}
    response.text = "Not Found"
    return response


@pytest.fixture
def sample_org_members():
    """Sample organization members data"""
    return [
        {
            "login": "johndoe",
            "id": 12345,
            "avatar_url": "https://github.com/images/error/johndoe_happy.gif",
            "type": "User",
            "site_admin": False,
        },
        {
            "login": "janedoe",
            "id": 12346,
            "avatar_url": "https://github.com/images/error/janedoe_happy.gif",
            "type": "User",
            "site_admin": False,
        },
    ]


@pytest.fixture
def sample_org_teams():
    """Sample organization teams data"""
    return [
        {
            "id": 1,
            "name": "Backend Team",
            "slug": "backend-team",
            "description": "Backend development team",
            "privacy": "closed",
            "permission": "pull",
            "members_count": 5,
            "repos_count": 3,
        },
        {
            "id": 2,
            "name": "Frontend Team",
            "slug": "frontend-team",
            "description": "Frontend development team",
            "privacy": "closed",
            "permission": "push",
            "members_count": 8,
            "repos_count": 2,
        },
    ]


@pytest.fixture
def sample_team_members():
    """Sample team members data"""
    return [
        {
            "login": "johndoe",
            "id": 12345,
            "avatar_url": "https://github.com/images/error/johndoe_happy.gif",
            "type": "User",
        },
        {
            "login": "alice",
            "id": 12347,
            "avatar_url": "https://github.com/images/error/alice_happy.gif",
            "type": "User",
        },
    ]


@pytest.fixture
def sample_team_repos():
    """Sample team repositories data"""
    return [
        {
            "id": 1296269,
            "name": "Hello-World",
            "full_name": "octocat/Hello-World",
            "private": False,
            "html_url": "https://github.com/octocat/Hello-World",
            "description": "This your first repo!",
            "permissions": {"admin": True, "push": True, "pull": True},
        }
    ]


@pytest.fixture
def sample_user_details():
    """Sample user details data"""
    return {
        "login": "johndoe",
        "id": 12345,
        "email": "john@example.com",
        "name": "John Doe",
        "company": "Test Company",
        "location": "Test City",
        "two_factor_authentication": True,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_org_membership():
    """Sample organization membership data"""
    return {
        "role": "member",
        "state": "active",
        "organization": {"login": "testorg", "id": 1},
        "user": {"login": "johndoe", "id": 12345},
    }


@pytest.fixture
def sample_team_membership():
    """Sample team membership data"""
    return {"role": "maintainer", "state": "active"}
