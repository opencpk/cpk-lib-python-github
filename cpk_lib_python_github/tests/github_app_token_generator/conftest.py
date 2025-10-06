# -*- coding: utf-8 -*-
"""Pytest configuration and fixtures for github_app_token_generator_package."""
import pytest  # pylint: disable=import-error

from cpk_lib_python_github.github_app_token_generator.github_api import GitHubAPIClient


@pytest.fixture
def github_api_client():
    """Create a GitHubAPIClient instance for testing."""
    return GitHubAPIClient(timeout=30)


@pytest.fixture
def sample_jwt_token():
    """Sample JWT token for testing."""
    return (
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9."
        "eyJpc3MiOiIxMjM0NTY3ODkwIiwiaWF0IjoxNjM5NjI2MDAwLCJleHAiOjE2Mzk2Mjk2MDB9."
        "sample_jwt_token"
    )


@pytest.fixture
def sample_installation_id():
    """Sample installation ID for testing."""
    return 12345678


@pytest.fixture
def sample_installation_token():
    """Sample installation token for testing."""
    return "ghs_1234567890abcdef1234567890abcdef12345678"


@pytest.fixture
def sample_access_token_response():
    """Sample access token response from GitHub API."""
    return {
        "token": "ghs_1234567890abcdef1234567890abcdef12345678",
        "expires_at": "2023-12-31T23:59:59Z",
        "permissions": {
            "contents": "read",
            "metadata": "read",
            "pull_requests": "write",
        },
        "repository_selection": "selected",
    }


@pytest.fixture
def sample_expected_token():
    """Expected token from the response."""
    return "ghs_1234567890abcdef1234567890abcdef12345678"


@pytest.fixture
def sample_installations():
    """Sample installations list."""
    return [
        {
            "id": 12345678,
            "account": {"login": "testorg", "type": "Organization"},
            "target_type": "Organization",
            "created_at": "2023-01-01T00:00:00Z",
        },
        {
            "id": 87654321,
            "account": {"login": "testuser", "type": "User"},
            "target_type": "User",
            "created_at": "2023-02-01T00:00:00Z",
        },
    ]


@pytest.fixture
def sample_repositories():
    """Sample repositories response."""
    return {
        "total_count": 3,
        "repositories": [
            {
                "id": 123,
                "full_name": "testorg/repo1",
                "name": "repo1",
                "private": False,
            },
            {
                "id": 124,
                "full_name": "testorg/repo2",
                "name": "repo2",
                "private": True,
            },
            {
                "id": 125,
                "full_name": "testorg/repo3",
                "name": "repo3",
                "private": False,
            },
        ],
    }


@pytest.fixture
def sample_app_info():
    """Sample GitHub App information."""
    return {
        "id": 123456,
        "name": "Test GitHub App",
        "slug": "test-github-app",
        "description": "A test GitHub App for unit testing",
        "owner": {"login": "testorg", "type": "Organization"},
        "html_url": "https://github.com/apps/test-github-app",
        "created_at": "2023-01-01T00:00:00Z",
        "permissions": {
            "contents": "read",
            "metadata": "read",
            "pull_requests": "write",
        },
        "events": ["push", "pull_request"],
    }
