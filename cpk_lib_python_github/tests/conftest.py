"""Shared test fixtures and configuration for all libraries"""

from unittest.mock import Mock

import pytest  # pylint: disable=import-error


@pytest.fixture
def mock_requests_session():
    """Create a mock requests session"""
    session = Mock()
    session.headers = {}
    return session


@pytest.fixture
def base_mock_response():
    """Create a basic mock response"""
    response = Mock()
    response.status_code = 200
    response.headers = {}
    response.json.return_value = {}
    response.raise_for_status.return_value = None
    return response


# Common test data that might be used across different libraries
@pytest.fixture
def sample_github_user():
    """Sample GitHub user data"""
    return {"login": "testuser", "id": 12345, "email": "test@example.com", "name": "Test User"}


@pytest.fixture
def sample_github_org():
    """Sample GitHub organization data"""
    return {"login": "testorg", "id": 67890, "name": "Test Organization"}


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "github_app_token_generator: tests for GitHub App Token Generator"
    )
    config.addinivalue_line(
        "markers", "github_user_access_backup: tests for GitHub User Access Backup"
    )
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "unit: unit tests")


def pytest_collection_modifyitems(items):
    """Auto-assign markers based on test location"""
    for item in items:
        # Auto-mark tests based on their location
        if "github_app_token_generator" in str(item.fspath):
            item.add_marker(pytest.mark.github_app_token_generator)
        elif "github_user_access_backup" in str(item.fspath):
            item.add_marker(pytest.mark.github_user_access_backup)
