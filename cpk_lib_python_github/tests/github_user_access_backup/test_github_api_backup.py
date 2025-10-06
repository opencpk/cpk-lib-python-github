"""Simple test cases for github_api.py - API functionality and error handling"""

# pylint: disable=no-member
import time
from unittest.mock import Mock, patch

import pytest  # pylint: disable=import-error
import requests  # pylint: disable=import-error

from cpk_lib_python_github.github_user_access_backup.github_api import GitHubAPIClient


@pytest.fixture
def api_client():
    """Create a GitHubAPIClient instance for testing"""
    return GitHubAPIClient(token="test_token", max_workers=1)


@pytest.fixture
def mock_session():
    """Create a mock session"""
    session = Mock()
    return session


@pytest.fixture
def mock_response():
    """Create a mock response"""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"test": "data"}
    response.headers = {}
    return response


@pytest.fixture
def rate_limit_response():
    """Create a mock rate limit response to avoid duplicate code"""
    response = Mock()
    response.status_code = 403
    response.headers = {
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(int(time.time()) + 60),
    }
    return response


class TestGitHubAPIClientInit:
    """Test GitHubAPIClient initialization"""

    def test_init_sets_token_and_workers(self):
        """Test that initialization sets token and max_workers correctly"""
        client = GitHubAPIClient(token="test_token", max_workers=3)
        assert client.token == "test_token"
        assert client.max_workers == 3

    def test_init_default_max_workers(self):
        """Test default max_workers value"""
        client = GitHubAPIClient(token="test_token")
        assert client.max_workers == 5


class TestGetSession:
    """Test get_session method"""

    def test_get_session_creates_session_with_headers(
        self, api_client
    ):  # pylint: disable=redefined-outer-name
        """Test that get_session creates a session with correct headers"""
        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            api_client.get_session()

            # Verify session creation and header setup
            mock_session_class.assert_called_once()
            mock_session.headers.update.assert_called_once()

            # Check headers content
            headers_call = mock_session.headers.update.call_args[0][0]
            assert "Authorization" in headers_call
            assert headers_call["Authorization"] == "token test_token"
            assert headers_call["Accept"] == "application/vnd.github.v3+json"

    def test_get_session_reuses_existing_session(
        self, api_client
    ):  # pylint: disable=redefined-outer-name
        """Test that get_session reuses existing session"""
        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # First call
            session1 = api_client.get_session()
            # Second call
            session2 = api_client.get_session()

            # Should only create session once
            mock_session_class.assert_called_once()
            assert session1 == session2


class TestHandleRateLimit:
    """Test handle_rate_limit method"""

    def test_handle_rate_limit_not_403(self, api_client):  # pylint: disable=redefined-outer-name
        """Test rate limit handling for non-403 responses"""
        response = Mock()
        response.status_code = 200

        result = api_client.handle_rate_limit(response)
        assert result is False

    def test_handle_rate_limit_403_with_remaining(
        self, api_client
    ):  # pylint: disable=redefined-outer-name
        """Test rate limit handling for 403 with remaining requests"""
        response = Mock()
        response.status_code = 403
        response.headers = {"X-RateLimit-Remaining": "10"}

        result = api_client.handle_rate_limit(response)
        assert result is False

    def test_handle_rate_limit_403_no_remaining(
        self, api_client, rate_limit_response
    ):  # pylint: disable=redefined-outer-name
        """Test rate limit handling for 403 with no remaining requests"""
        with patch("time.sleep") as mock_sleep:
            result = api_client.handle_rate_limit(rate_limit_response)

        assert result is True
        mock_sleep.assert_called_once()


class TestMakeRequest:
    """Test make_request method"""

    def test_make_request_success(
        self, api_client, mock_response
    ):  # pylint: disable=redefined-outer-name
        """Test successful API request"""
        with patch.object(api_client, "get_session") as mock_get_session:
            session_mock = Mock()
            session_mock.get.return_value = mock_response
            mock_get_session.return_value = session_mock

            result = api_client.make_request("https://api.github.com/test")

            assert result == {"test": "data"}
            session_mock.get.assert_called_once_with("https://api.github.com/test")
            mock_response.raise_for_status.assert_called_once()

    def test_make_request_404_silent(self, api_client):  # pylint: disable=redefined-outer-name
        """Test 404 handling with silent_404=True"""
        response_mock = Mock()
        response_mock.status_code = 404

        with patch.object(api_client, "get_session") as mock_get_session:
            session_mock = Mock()
            session_mock.get.return_value = response_mock
            mock_get_session.return_value = session_mock

            result = api_client.make_request("https://api.github.com/test", silent_404=True)

            assert result is None

    def test_make_request_404_not_silent(self, api_client):  # pylint: disable=redefined-outer-name
        """Test 404 handling with silent_404=False"""
        response_mock = Mock()
        response_mock.status_code = 404
        response_mock.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response_mock
        )

        with patch.object(api_client, "get_session") as mock_get_session:
            session_mock = Mock()
            session_mock.get.return_value = response_mock
            mock_get_session.return_value = session_mock

            with pytest.raises(requests.exceptions.HTTPError):
                api_client.make_request("https://api.github.com/test", silent_404=False)

    def test_make_request_http_error_with_retries(
        self, api_client
    ):  # pylint: disable=redefined-outer-name
        """Test HTTP error handling with retries"""
        response_mock = Mock()
        response_mock.status_code = 500
        http_error = requests.exceptions.HTTPError(response=response_mock)
        response_mock.raise_for_status.side_effect = http_error

        with patch.object(api_client, "get_session") as mock_get_session:
            session_mock = Mock()
            session_mock.get.return_value = response_mock
            mock_get_session.return_value = session_mock

            with patch("time.sleep") as mock_sleep:
                with pytest.raises(requests.exceptions.HTTPError):
                    api_client.make_request("https://api.github.com/test")

                # Should retry 3 times (sleep called for first 2 retries)
                assert mock_sleep.call_count == 2

    def test_make_request_request_exception(
        self, api_client
    ):  # pylint: disable=redefined-outer-name
        """Test request exception handling"""
        with patch.object(api_client, "get_session") as mock_get_session:
            session_mock = Mock()
            session_mock.get.side_effect = requests.exceptions.RequestException("Network error")
            mock_get_session.return_value = session_mock

            with patch("time.sleep") as mock_sleep:
                with pytest.raises(requests.exceptions.RequestException):
                    api_client.make_request("https://api.github.com/test")

                # Should retry 3 times
                assert mock_sleep.call_count == 2

    def test_make_request_with_custom_session(
        self, api_client, mock_response
    ):  # pylint: disable=redefined-outer-name
        """Test make_request with custom session"""
        custom_session = Mock()
        custom_session.get.return_value = mock_response

        result = api_client.make_request("https://api.github.com/test", session=custom_session)

        assert result == {"test": "data"}
        custom_session.get.assert_called_once_with("https://api.github.com/test")

    def test_make_request_with_rate_limit(
        self, api_client, rate_limit_response
    ):  # pylint: disable=redefined-outer-name
        """Test make_request handling rate limit"""
        with patch.object(api_client, "get_session") as mock_get_session:
            session_mock = Mock()
            session_mock.get.return_value = rate_limit_response
            mock_get_session.return_value = session_mock

            with patch.object(api_client, "handle_rate_limit", return_value=True):
                with patch("time.sleep"):
                    # Should continue after rate limit
                    api_client.make_request("https://api.github.com/test")


class TestPaginatedRequest:
    """Test paginated_request method"""

    def test_paginated_request_single_page(
        self, api_client
    ):  # pylint: disable=redefined-outer-name
        """Test paginated request with single page"""
        mock_data = [{"id": 1}, {"id": 2}]

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.return_value = mock_data

            result = api_client.paginated_request("https://api.github.com/test")

            assert result == mock_data
            mock_make_request.assert_called_once_with(
                "https://api.github.com/test?per_page=100&page=1", silent_404=False
            )

    def test_paginated_request_multiple_pages(
        self, api_client
    ):  # pylint: disable=redefined-outer-name
        """Test paginated request with multiple pages"""
        page1_data = [{"id": i} for i in range(100)]  # Full page
        page2_data = [{"id": i} for i in range(100, 150)]  # Partial page

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.side_effect = [page1_data, page2_data]

            result = api_client.paginated_request("https://api.github.com/test")

            assert len(result) == 150
            assert result[:100] == page1_data
            assert result[100:] == page2_data
            assert mock_make_request.call_count == 2

    def test_paginated_request_empty_response(
        self, api_client
    ):  # pylint: disable=redefined-outer-name
        """Test paginated request with empty response"""
        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.return_value = None

            result = api_client.paginated_request("https://api.github.com/test")

            assert result == []

    def test_paginated_request_404_silent(self, api_client):  # pylint: disable=redefined-outer-name
        """Test paginated request with 404 and silent_404=True"""
        with patch.object(api_client, "make_request") as mock_make_request:
            http_error = requests.exceptions.HTTPError()
            http_error.response = Mock()
            http_error.response.status_code = 404
            mock_make_request.side_effect = http_error

            result = api_client.paginated_request("https://api.github.com/test", silent_404=True)

            assert result == []

    def test_paginated_request_custom_per_page(
        self, api_client
    ):  # pylint: disable=redefined-outer-name
        """Test paginated request with custom per_page"""
        mock_data = [{"id": 1}]

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.return_value = mock_data

            api_client.paginated_request("https://api.github.com/test", per_page=50)

            mock_make_request.assert_called_once_with(
                "https://api.github.com/test?per_page=50&page=1", silent_404=False
            )


class TestOrganizationMethods:
    """Test organization-related API methods"""

    def test_get_organization_members(self, api_client):  # pylint: disable=redefined-outer-name
        """Test get_organization_members"""
        mock_data = [{"login": "user1"}, {"login": "user2"}]

        with patch.object(api_client, "paginated_request") as mock_paginated:
            mock_paginated.return_value = mock_data

            result = api_client.get_organization_members("testorg")

            assert result == mock_data
            mock_paginated.assert_called_once_with("https://api.github.com/orgs/testorg/members")

    def test_get_organization_teams(self, api_client):  # pylint: disable=redefined-outer-name
        """Test get_organization_teams"""
        mock_data = [{"slug": "team1"}, {"slug": "team2"}]

        with patch.object(api_client, "paginated_request") as mock_paginated:
            mock_paginated.return_value = mock_data

            result = api_client.get_organization_teams("testorg")

            assert result == mock_data
            mock_paginated.assert_called_once_with("https://api.github.com/orgs/testorg/teams")


class TestTeamMethods:
    """Test team-related API methods"""

    def test_get_team_members(self, api_client):  # pylint: disable=redefined-outer-name
        """Test get_team_members"""
        mock_data = [{"login": "user1"}, {"login": "user2"}]

        with patch.object(api_client, "paginated_request") as mock_paginated:
            mock_paginated.return_value = mock_data

            result = api_client.get_team_members("testorg", "team1")

            assert result == mock_data
            mock_paginated.assert_called_once_with(
                "https://api.github.com/orgs/testorg/teams/team1/members", silent_404=True
            )

    def test_get_team_repositories(self, api_client):  # pylint: disable=redefined-outer-name
        """Test get_team_repositories"""
        mock_data = [{"full_name": "org/repo1"}, {"full_name": "org/repo2"}]

        with patch.object(api_client, "paginated_request") as mock_paginated:
            mock_paginated.return_value = mock_data

            result = api_client.get_team_repositories("testorg", "team1")

            assert result == mock_data
            mock_paginated.assert_called_once_with(
                "https://api.github.com/orgs/testorg/teams/team1/repos", silent_404=True
            )

    def test_get_team_membership(self, api_client):  # pylint: disable=redefined-outer-name
        """Test get_team_membership"""
        mock_data = {"role": "member"}

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.return_value = mock_data

            result = api_client.get_team_membership("testorg", "team1", "user1")

            assert result == mock_data
            mock_make_request.assert_called_once_with(
                "https://api.github.com/orgs/testorg/teams/team1/memberships/user1", silent_404=True
            )


class TestUserMethods:
    """Test user-related API methods"""

    def test_get_user_org_membership(self, api_client):  # pylint: disable=redefined-outer-name
        """Test get_user_org_membership"""
        mock_data = {"role": "admin"}

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.return_value = mock_data

            result = api_client.get_user_org_membership("testorg", "user1")

            assert result == mock_data
            mock_make_request.assert_called_once_with(
                "https://api.github.com/orgs/testorg/memberships/user1", silent_404=True
            )

    def test_get_user_details(self, api_client):  # pylint: disable=redefined-outer-name
        """Test get_user_details"""
        mock_data = {"login": "user1", "email": "user1@example.com"}

        with patch.object(api_client, "make_request") as mock_make_request:
            mock_make_request.return_value = mock_data

            result = api_client.get_user_details("user1")

            assert result == mock_data
            mock_make_request.assert_called_once_with(
                "https://api.github.com/users/user1", silent_404=True
            )


class TestErrorScenarios:
    """Test various error scenarios"""

    def test_network_timeout(self, api_client):  # pylint: disable=redefined-outer-name
        """Test network timeout handling"""
        with patch.object(api_client, "get_session") as mock_get_session:
            session_mock = Mock()
            session_mock.get.side_effect = requests.exceptions.Timeout("Timeout")
            mock_get_session.return_value = session_mock

            with pytest.raises(requests.exceptions.Timeout):
                api_client.make_request("https://api.github.com/test")

    def test_connection_error(self, api_client):  # pylint: disable=redefined-outer-name
        """Test connection error handling"""
        with patch.object(api_client, "get_session") as mock_get_session:
            session_mock = Mock()
            session_mock.get.side_effect = requests.exceptions.ConnectionError("Connection failed")
            mock_get_session.return_value = session_mock

            with pytest.raises(requests.exceptions.ConnectionError):
                api_client.make_request("https://api.github.com/test")

    def test_json_decode_error(self, api_client):  # pylint: disable=redefined-outer-name
        """Test JSON decode error handling"""
        response_mock = Mock()
        response_mock.status_code = 200
        response_mock.json.side_effect = ValueError("Invalid JSON")

        with patch.object(api_client, "get_session") as mock_get_session:
            session_mock = Mock()
            session_mock.get.return_value = response_mock
            mock_get_session.return_value = session_mock

            with pytest.raises(ValueError):
                api_client.make_request("https://api.github.com/test")

    def test_unauthorized_error(self, api_client):  # pylint: disable=redefined-outer-name
        """Test unauthorized error handling"""
        response_mock = Mock()
        response_mock.status_code = 401
        response_mock.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response_mock
        )

        with patch.object(api_client, "get_session") as mock_get_session:
            session_mock = Mock()
            session_mock.get.return_value = response_mock
            mock_get_session.return_value = session_mock

            with pytest.raises(requests.exceptions.HTTPError):
                api_client.make_request("https://api.github.com/test")

    def test_server_error_with_retries(self, api_client):  # pylint: disable=redefined-outer-name
        """Test server error with retry logic"""
        response_mock = Mock()
        response_mock.status_code = 500
        response_mock.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=response_mock
        )

        with patch.object(api_client, "get_session") as mock_get_session:
            session_mock = Mock()
            session_mock.get.return_value = response_mock
            mock_get_session.return_value = session_mock

            with patch("time.sleep") as mock_sleep:
                with pytest.raises(requests.exceptions.HTTPError):
                    api_client.make_request("https://api.github.com/test")

                # Should have retried with exponential backoff
                expected_sleeps = [1, 2]  # 2^0, 2^1 for first 2 retries
                actual_sleeps = [call[0][0] for call in mock_sleep.call_args_list]
                assert actual_sleeps == expected_sleeps
