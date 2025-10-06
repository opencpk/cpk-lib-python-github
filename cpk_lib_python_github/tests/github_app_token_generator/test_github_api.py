# pylint: disable=redefined-outer-name
"""Unit tests for GitHubAPIClient - All methods using responses and pytest fixtures."""

from unittest.mock import patch

import pytest  # pylint: disable=import-error
import requests  # pylint: disable=import-error
import responses  # pylint: disable=import-error

from cpk_lib_python_github.github_app_token_generator.github_api import GitHubAPIClient

# --- Fixtures ---


@pytest.fixture
def github_api_client():
    """Fixture that returns a GitHubAPIClient instance for testing."""
    return GitHubAPIClient(timeout=30)


@pytest.fixture
def sample_jwt_token():
    """Fixture that returns a sample JWT token."""
    return "fake_jwt_token"


@pytest.fixture
def sample_installation_id():
    """Fixture that returns a sample installation ID."""
    return 12345


@pytest.fixture
def sample_access_token_response():
    """Fixture that returns a sample access token response."""
    return {"token": "ghs_test_token", "expires_at": "2024-10-01T16:00:00Z"}


@pytest.fixture
def sample_expected_token():
    """Fixture that returns a sample expected token."""
    return "ghs_test_token"


@pytest.fixture
def sample_installations():
    """Fixture that returns sample installations data."""
    return [
        {"id": 1, "account": {"login": "testorg", "type": "Organization"}},
        {"id": 2, "account": {"login": "anotherorg", "type": "Organization"}},
    ]


@pytest.fixture
def sample_installation_token():
    """Fixture that returns a sample installation token."""
    return "ghs_installation_token"


@pytest.fixture
def sample_repositories():
    """Fixture that returns sample repositories data."""
    return {
        "total_count": 3,
        "repositories": [
            {"id": 1, "name": "repo1", "full_name": "org/repo1"},
            {"id": 2, "name": "repo2", "full_name": "org/repo2"},
            {"id": 3, "name": "repo3", "full_name": "org/repo3"},
        ],
    }


@pytest.fixture
def sample_app_info():
    """Fixture that returns sample app info data."""
    return {"id": 123456, "name": "Test GitHub App", "description": "A test app"}


# Create pytest fixture aliases for the test parameters
@pytest.fixture
def api_client(github_api_client):
    """Alias fixture for github_api_client."""
    return github_api_client


@pytest.fixture
def jwt_token(sample_jwt_token):
    """Alias fixture for sample_jwt_token."""
    return sample_jwt_token


@pytest.fixture
def installation_id(sample_installation_id):
    """Alias fixture for sample_installation_id."""
    return sample_installation_id


@pytest.fixture
def access_token_response(sample_access_token_response):
    """Alias fixture for sample_access_token_response."""
    return sample_access_token_response


@pytest.fixture
def expected_token(sample_expected_token):
    """Alias fixture for sample_expected_token."""
    return sample_expected_token


@pytest.fixture
def installations(sample_installations):
    """Alias fixture for sample_installations."""
    return sample_installations


@pytest.fixture
def installation_token(sample_installation_token):
    """Alias fixture for sample_installation_token."""
    return sample_installation_token


@pytest.fixture
def repositories(sample_repositories):
    """Alias fixture for sample_repositories."""
    return sample_repositories


@pytest.fixture
def app_info(sample_app_info):
    """Alias fixture for sample_app_info."""
    return sample_app_info


# --- Tests ---


class TestGetInstallationAccessToken:
    """Test cases for get_installation_access_token method."""

    # pylint: disable=too-many-positional-arguments
    @responses.activate
    def test_get_installation_access_token_success(
        self,
        api_client,
        jwt_token,
        installation_id,
        access_token_response,
        expected_token,
    ):
        """Test successful installation access token retrieval."""
        expected_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        responses.add(responses.POST, expected_url, json=access_token_response, status=201)

        result_token = api_client.get_installation_access_token(jwt_token, installation_id)

        assert result_token == expected_token
        assert len(responses.calls) == 1

        request = responses.calls[0].request
        assert request.method == "POST"
        assert request.url == expected_url
        assert request.headers["Authorization"] == f"Bearer {jwt_token}"
        assert request.headers["Accept"] == "application/vnd.github.v3+json"

    @responses.activate
    def test_get_installation_access_token_http_401_unauthorized(
        self, api_client, jwt_token, installation_id
    ):
        """Test 401 unauthorized error for installation access token."""
        expected_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        responses.add(responses.POST, expected_url, json={"message": "Bad credentials"}, status=401)

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.get_installation_access_token(jwt_token, installation_id)
        assert exc_info.value.response.status_code == 401

    @responses.activate
    def test_get_installation_access_token_http_404_not_found(
        self, api_client, jwt_token, installation_id
    ):
        """Test 404 not found error for installation access token."""
        expected_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        responses.add(responses.POST, expected_url, json={"message": "Not Found"}, status=404)

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.get_installation_access_token(jwt_token, installation_id)
        assert exc_info.value.response.status_code == 404

    @responses.activate
    def test_get_installation_access_token_missing_token_field(
        self, api_client, jwt_token, installation_id
    ):
        """Test missing token field in response."""
        expected_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        invalid_response = {
            "expires_at": "2023-12-31T23:59:59Z",
            "permissions": {"contents": "read"},
        }
        responses.add(responses.POST, expected_url, json=invalid_response, status=201)

        with pytest.raises(ValueError) as exc_info:
            api_client.get_installation_access_token(jwt_token, installation_id)
        assert "Invalid response: token not found in response" in str(exc_info.value)

    @responses.activate
    def test_get_installation_access_token_empty_response(
        self, api_client, jwt_token, installation_id
    ):
        """Test empty response for installation access token."""
        expected_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        responses.add(responses.POST, expected_url, json={}, status=201)

        with pytest.raises(ValueError) as exc_info:
            api_client.get_installation_access_token(jwt_token, installation_id)
        assert "Invalid response: token not found in response" in str(exc_info.value)

    @responses.activate
    def test_get_installation_access_token_malformed_json(
        self, api_client, jwt_token, installation_id
    ):
        """Test malformed JSON response."""
        expected_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        responses.add(
            responses.POST,
            expected_url,
            body="invalid json response",
            status=201,
            content_type="application/json",
        )

        with pytest.raises(requests.exceptions.RequestException):
            api_client.get_installation_access_token(jwt_token, installation_id)

    def test_get_installation_access_token_timeout(self, jwt_token, installation_id):
        """Test timeout error for installation access token."""
        client = GitHubAPIClient(timeout=0.001)
        with pytest.raises(requests.exceptions.RequestException):
            client.get_installation_access_token(jwt_token, installation_id)

    @responses.activate
    def test_get_installation_access_token_connection_error(
        self, api_client, jwt_token, installation_id
    ):
        """Test connection error for installation access token."""
        with pytest.raises(requests.exceptions.RequestException):
            api_client.get_installation_access_token(jwt_token, installation_id)


class TestListInstallations:
    """Test cases for list_installations method."""

    @responses.activate
    def test_list_installations_success(self, api_client, jwt_token, installations):
        """Test successful installations listing."""
        expected_url = "https://api.github.com/app/installations"
        responses.add(responses.GET, expected_url, json=installations, status=200)

        result = api_client.list_installations(jwt_token)

        assert result == installations
        assert len(result) == 2
        assert len(responses.calls) == 1

        request = responses.calls[0].request
        assert request.method == "GET"
        assert request.url == expected_url
        assert request.headers["Authorization"] == f"Bearer {jwt_token}"
        assert request.headers["Accept"] == "application/vnd.github.v3+json"

    @responses.activate
    def test_list_installations_empty_list(self, api_client, jwt_token):
        """Test empty installations list."""
        expected_url = "https://api.github.com/app/installations"
        responses.add(responses.GET, expected_url, json=[], status=200)

        result_installations = api_client.list_installations(jwt_token)
        assert result_installations == []
        assert len(result_installations) == 0

    @responses.activate
    def test_list_installations_http_401_error(self, api_client, jwt_token):
        """Test 401 error for list installations."""
        expected_url = "https://api.github.com/app/installations"
        responses.add(responses.GET, expected_url, json={"message": "Bad credentials"}, status=401)

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.list_installations(jwt_token)
        assert exc_info.value.response.status_code == 401

    @responses.activate
    def test_list_installations_http_403_error(self, api_client, jwt_token):
        """Test 403 error for list installations."""
        expected_url = "https://api.github.com/app/installations"
        responses.add(responses.GET, expected_url, json={"message": "Forbidden"}, status=403)

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.list_installations(jwt_token)
        assert exc_info.value.response.status_code == 403

    @responses.activate
    def test_list_installations_network_error(self, api_client, jwt_token):
        """Test network error for list installations."""
        with pytest.raises(requests.exceptions.RequestException):
            api_client.list_installations(jwt_token)


class TestValidateToken:
    """Test cases for validate_token method."""

    @responses.activate
    def test_validate_token_success(self, api_client, installation_token, repositories):
        """Test successful token validation."""
        expected_url = "https://api.github.com/installation/repositories"
        responses.add(
            responses.GET,
            expected_url,
            json=repositories,
            status=200,
            headers={
                "X-OAuth-Scopes": "repo, user",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Reset": "1639629600",
            },
        )

        result = api_client.validate_token(installation_token)

        assert result["valid"] is True
        assert result["type"] == "GitHub App Installation Token"
        assert result["repositories_count"] == 3
        assert result["scopes"] == ["repo", "user"]
        assert result["rate_limit"]["remaining"] == "4999"
        assert result["rate_limit"]["limit"] == "5000"
        assert result["rate_limit"]["reset"] == "1639629600"

        request = responses.calls[0].request
        assert request.headers["Authorization"] == f"token {installation_token}"

    @responses.activate
    def test_validate_token_no_scopes(self, api_client, installation_token, repositories):
        """Test token validation with no scopes."""
        expected_url = "https://api.github.com/installation/repositories"
        responses.add(
            responses.GET,
            expected_url,
            json=repositories,
            status=200,
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Limit": "5000"},
        )

        result = api_client.validate_token(installation_token)
        assert result["valid"] is True
        assert result["scopes"] == []

    @responses.activate
    def test_validate_token_401_invalid(self, api_client, installation_token):
        """Test 401 invalid token."""
        expected_url = "https://api.github.com/installation/repositories"
        responses.add(responses.GET, expected_url, json={"message": "Bad credentials"}, status=401)

        result = api_client.validate_token(installation_token)
        assert result["valid"] is False
        assert result["status_code"] == 401
        assert result["reason"] == "Invalid or expired token"

    @responses.activate
    def test_validate_token_403_insufficient_permissions(self, api_client, installation_token):
        """Test 403 insufficient permissions."""
        expected_url = "https://api.github.com/installation/repositories"
        responses.add(responses.GET, expected_url, json={"message": "Forbidden"}, status=403)

        result = api_client.validate_token(installation_token)
        assert result["valid"] is False
        assert result["status_code"] == 403
        assert result["reason"] == "Insufficient permissions"

    @responses.activate
    def test_validate_token_404_not_found(self, api_client, installation_token):
        """Test 404 not found for token validation."""
        expected_url = "https://api.github.com/installation/repositories"
        responses.add(responses.GET, expected_url, json={"message": "Not Found"}, status=404)

        result = api_client.validate_token(installation_token)
        assert result["valid"] is False
        assert result["status_code"] == 404
        assert result["reason"] == "HTTP 404"

    @responses.activate
    def test_validate_token_network_error(self, api_client, installation_token):
        """Test network error for token validation."""
        result = api_client.validate_token(installation_token)
        assert result["valid"] is False
        assert "error" in result


class TestRevokeInstallationToken:
    """Test cases for revoke_installation_token method."""

    @responses.activate
    def test_revoke_installation_token_success(self, api_client, installation_token):
        """Test successful token revocation."""
        expected_url = "https://api.github.com/installation/token"
        responses.add(responses.DELETE, expected_url, status=204)

        result = api_client.revoke_installation_token(installation_token)

        assert result is True
        assert len(responses.calls) == 1

        request = responses.calls[0].request
        assert request.method == "DELETE"
        assert request.url == expected_url
        assert request.headers["Authorization"] == f"token {installation_token}"

    @responses.activate
    def test_revoke_installation_token_404_not_found(self, api_client, installation_token):
        """Test 404 not found for token revocation."""
        expected_url = "https://api.github.com/installation/token"
        responses.add(responses.DELETE, expected_url, json={"message": "Not Found"}, status=404)

        result = api_client.revoke_installation_token(installation_token)
        assert result is False

    @responses.activate
    def test_revoke_installation_token_401_error(self, api_client, installation_token):
        """Test 401 error for token revocation."""
        expected_url = "https://api.github.com/installation/token"
        responses.add(
            responses.DELETE,
            expected_url,
            json={"message": "Bad credentials"},
            status=401,
        )

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.revoke_installation_token(installation_token)
        assert exc_info.value.response.status_code == 401

    @responses.activate
    def test_revoke_installation_token_403_error(self, api_client, installation_token):
        """Test 403 error for token revocation."""
        expected_url = "https://api.github.com/installation/token"
        responses.add(responses.DELETE, expected_url, json={"message": "Forbidden"}, status=403)

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.revoke_installation_token(installation_token)
        assert exc_info.value.response.status_code == 403

    @responses.activate
    def test_revoke_installation_token_network_error(self, api_client, installation_token):
        """Test network error for token revocation."""
        with pytest.raises(requests.exceptions.RequestException):
            api_client.revoke_installation_token(installation_token)


class TestGetAppInfo:
    """Test cases for get_app_info method."""

    @responses.activate
    def test_get_app_info_success(self, api_client, jwt_token, app_info):
        """Test successful app info retrieval."""
        expected_url = "https://api.github.com/app"
        responses.add(responses.GET, expected_url, json=app_info, status=200)

        result = api_client.get_app_info(jwt_token)

        assert result == app_info
        assert result["name"] == "Test GitHub App"
        assert result["id"] == 123456
        assert len(responses.calls) == 1

        request = responses.calls[0].request
        assert request.method == "GET"
        assert request.url == expected_url
        assert request.headers["Authorization"] == f"Bearer {jwt_token}"

    @responses.activate
    def test_get_app_info_401_error(self, api_client, jwt_token):
        """Test 401 error for app info."""
        expected_url = "https://api.github.com/app"
        responses.add(responses.GET, expected_url, json={"message": "Bad credentials"}, status=401)

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.get_app_info(jwt_token)
        assert exc_info.value.response.status_code == 401

    @responses.activate
    def test_get_app_info_404_error(self, api_client, jwt_token):
        """Test 404 error for app info."""
        expected_url = "https://api.github.com/app"
        responses.add(responses.GET, expected_url, json={"message": "Not Found"}, status=404)

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.get_app_info(jwt_token)
        assert exc_info.value.response.status_code == 404

    @responses.activate
    def test_get_app_info_403_error(self, api_client, jwt_token):
        """Test 403 error for app info."""
        expected_url = "https://api.github.com/app"
        responses.add(responses.GET, expected_url, json={"message": "Forbidden"}, status=403)

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            api_client.get_app_info(jwt_token)
        assert exc_info.value.response.status_code == 403

    @responses.activate
    def test_get_app_info_network_error(self, api_client, jwt_token):
        """Test network error for app info."""
        with pytest.raises(requests.exceptions.RequestException):
            api_client.get_app_info(jwt_token)


class TestGetInstallationRepositories:
    """Test cases for get_installation_repositories method."""

    # pylint: disable=too-many-positional-arguments
    @patch.object(GitHubAPIClient, "get_installation_access_token")
    @responses.activate
    def test_get_installation_repositories_success(
        self,
        mock_get_token,
        api_client,
        jwt_token,
        installation_id,
        installation_token,
        repositories,
    ):
        """Test successful installation repositories retrieval."""
        mock_get_token.return_value = installation_token

        expected_url = "https://api.github.com/installation/repositories"
        responses.add(responses.GET, expected_url, json=repositories, status=200)

        repos = api_client.get_installation_repositories(jwt_token, installation_id)

        assert repos == repositories
        assert repos["total_count"] == 3
        assert len(repos["repositories"]) == 3
        mock_get_token.assert_called_once_with(jwt_token, installation_id)

        request = responses.calls[0].request
        assert request.headers["Authorization"] == f"token {installation_token}"

    @patch.object(GitHubAPIClient, "get_installation_access_token")
    def test_get_installation_repositories_token_error(
        self,
        mock_get_token,
        api_client,
        jwt_token,
        installation_id,
    ):
        """Test token error for installation repositories."""
        mock_get_token.side_effect = requests.exceptions.RequestException("Network error")

        repos = api_client.get_installation_repositories(jwt_token, installation_id)

        assert repos["total_count"] == 0
        assert repos["repositories"] == []
        assert "error" in repos
        assert "Network error" in repos["error"]

    # pylint: disable=too-many-positional-arguments
    @patch.object(GitHubAPIClient, "get_installation_access_token")
    @responses.activate
    def test_get_installation_repositories_api_error(
        self,
        mock_get_token,
        api_client,
        jwt_token,
        installation_id,
        installation_token,
    ):
        """Test API error for installation repositories."""
        mock_get_token.return_value = installation_token

        expected_url = "https://api.github.com/installation/repositories"
        responses.add(responses.GET, expected_url, json={"message": "Forbidden"}, status=403)

        repos = api_client.get_installation_repositories(jwt_token, installation_id)

        assert repos["total_count"] == 0
        assert repos["repositories"] == []
        assert "error" in repos

    # pylint: disable=too-many-positional-arguments
    @patch.object(GitHubAPIClient, "get_installation_access_token")
    @responses.activate
    def test_get_installation_repositories_empty_response(
        self,
        mock_get_token,
        api_client,
        jwt_token,
        installation_id,
        installation_token,
    ):
        """Test empty response for installation repositories."""
        mock_get_token.return_value = installation_token

        expected_url = "https://api.github.com/installation/repositories"
        empty_repos = {"total_count": 0, "repositories": []}
        responses.add(responses.GET, expected_url, json=empty_repos, status=200)

        repos = api_client.get_installation_repositories(jwt_token, installation_id)

        assert repos["total_count"] == 0
        assert repos["repositories"] == []


class TestGetAccessibleRepositoriesViaToken:
    """Test cases for get_accessible_repositories_via_token method."""

    @responses.activate
    def test_get_accessible_repositories_via_token_success(
        self, api_client, installation_token, repositories
    ):
        """Test successful accessible repositories retrieval."""
        expected_url = "https://api.github.com/installation/repositories"
        responses.add(responses.GET, expected_url, json=repositories, status=200)

        repos = api_client.get_accessible_repositories_via_token(installation_token)

        assert repos == repositories
        assert repos["total_count"] == 3
        assert len(repos["repositories"]) == 3
        assert len(responses.calls) == 1

        request = responses.calls[0].request
        assert request.method == "GET"
        assert request.url == expected_url
        assert request.headers["Authorization"] == f"token {installation_token}"

    @responses.activate
    def test_get_accessible_repositories_via_token_empty(self, api_client, installation_token):
        """Test empty accessible repositories."""
        expected_url = "https://api.github.com/installation/repositories"
        empty_repos = {"total_count": 0, "repositories": []}
        responses.add(responses.GET, expected_url, json=empty_repos, status=200)

        repos = api_client.get_accessible_repositories_via_token(installation_token)

        assert repos["total_count"] == 0
        assert repos["repositories"] == []

    @responses.activate
    def test_get_accessible_repositories_via_token_401_error(self, api_client, installation_token):
        """Test 401 error for accessible repositories."""
        expected_url = "https://api.github.com/installation/repositories"
        responses.add(responses.GET, expected_url, json={"message": "Bad credentials"}, status=401)

        repos = api_client.get_accessible_repositories_via_token(installation_token)

        assert repos["total_count"] == 0
        assert repos["repositories"] == []
        assert "error" in repos

    @responses.activate
    def test_get_accessible_repositories_via_token_403_error(self, api_client, installation_token):
        """Test 403 error for accessible repositories."""
        expected_url = "https://api.github.com/installation/repositories"
        responses.add(responses.GET, expected_url, json={"message": "Forbidden"}, status=403)

        repos = api_client.get_accessible_repositories_via_token(installation_token)

        assert repos["total_count"] == 0
        assert repos["repositories"] == []
        assert "error" in repos

    @responses.activate
    def test_get_accessible_repositories_via_token_404_error(self, api_client, installation_token):
        """Test 404 error for accessible repositories."""
        expected_url = "https://api.github.com/installation/repositories"
        responses.add(responses.GET, expected_url, json={"message": "Not Found"}, status=404)

        repos = api_client.get_accessible_repositories_via_token(installation_token)

        assert repos["total_count"] == 0
        assert repos["repositories"] == []
        assert "error" in repos

    @responses.activate
    def test_get_accessible_repositories_via_token_network_error(
        self, api_client, installation_token
    ):
        """Test network error for accessible repositories."""
        repos = api_client.get_accessible_repositories_via_token(installation_token)

        assert repos["total_count"] == 0
        assert repos["repositories"] == []
        assert "error" in repos


class TestGitHubAPIClientEdgeCases:
    """Test edge cases for GitHubAPIClient."""

    def test_client_initialization_default_timeout(self):
        """Test client initialization with default timeout."""
        client = GitHubAPIClient()
        assert client.timeout == 30
        assert client.BASE_URL == "https://api.github.com"

    def test_client_initialization_custom_timeout(self):
        """Test client initialization with custom timeout."""
        custom_timeout = 120
        client = GitHubAPIClient(timeout=custom_timeout)
        assert client.timeout == custom_timeout

    def test_client_initialization_zero_timeout(self):
        """Test client initialization with zero timeout."""
        client = GitHubAPIClient(timeout=0)
        assert client.timeout == 0

    def test_client_initialization_negative_timeout(self):
        """Test client initialization with negative timeout."""
        client = GitHubAPIClient(timeout=-1)
        assert client.timeout == -1

    @responses.activate
    def test_multiple_method_calls_same_client(
        self, api_client, jwt_token, installations, app_info
    ):
        """Test multiple method calls on same client instance."""
        responses.add(
            responses.GET,
            "https://api.github.com/app/installations",
            json=installations,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://api.github.com/app",
            json=app_info,
            status=200,
        )
        result_installations = api_client.list_installations(jwt_token)
        result_app_info = api_client.get_app_info(jwt_token)
        assert len(result_installations) == 2
        assert result_app_info["name"] == "Test GitHub App"
        assert len(responses.calls) == 2

    @responses.activate
    def test_request_headers_consistency(self, api_client, jwt_token):
        """Test request headers consistency across calls."""
        responses.add(
            responses.GET,
            "https://api.github.com/app/installations",
            json=[],
            status=200,
        )
        responses.add(responses.GET, "https://api.github.com/app", json={}, status=200)
        api_client.list_installations(jwt_token)
        api_client.get_app_info(jwt_token)
        for call in responses.calls:
            assert call.request.headers["Accept"] == "application/vnd.github.v3+json"
            assert call.request.headers["Authorization"] == f"Bearer {jwt_token}"

    @responses.activate
    def test_different_installation_ids(self, api_client, jwt_token, access_token_response):
        """Test different installation IDs."""
        test_cases = [123, 456789, 999999999]
        for install_id in test_cases:
            expected_url = f"https://api.github.com/app/installations/{install_id}/access_tokens"
            responses.add(
                responses.POST,
                expected_url,
                json=access_token_response,
                status=201,
            )
        for install_id in test_cases:
            token = api_client.get_installation_access_token(jwt_token, install_id)
            assert token == access_token_response["token"]

    @responses.activate
    def test_rate_limiting_headers(self, api_client, installation_token, repositories):
        """Test rate limiting headers."""
        expected_url = "https://api.github.com/installation/repositories"
        responses.add(
            responses.GET,
            expected_url,
            json=repositories,
            status=200,
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "100",
                "X-RateLimit-Reset": "1640995200",
                "X-RateLimit-Used": "4900",
                "X-RateLimit-Resource": "core",
            },
        )
        result = api_client.validate_token(installation_token)
        assert result["valid"] is True
        assert result["rate_limit"]["limit"] == "5000"
        assert result["rate_limit"]["remaining"] == "100"
        assert result["rate_limit"]["reset"] == "1640995200"

    @responses.activate
    def test_large_repository_count(self, api_client, installation_token):
        """Test large repository count handling."""
        large_repo_response = {
            "total_count": 1000,
            "repositories": [
                {
                    "id": i,
                    "full_name": f"testorg/repo{i}",
                    "name": f"repo{i}",
                    "private": i % 2 == 0,
                }
                for i in range(100)
            ],
        }
        expected_url = "https://api.github.com/installation/repositories"
        responses.add(responses.GET, expected_url, json=large_repo_response, status=200)
        repos = api_client.get_accessible_repositories_via_token(installation_token)
        assert repos["total_count"] == 1000
        assert len(repos["repositories"]) == 100

    def test_str_representation(self):
        """Test string representation of client."""
        client = GitHubAPIClient(timeout=45)
        str_repr = str(client)
        assert "GitHubAPIClient" in str_repr or "timeout" in str_repr

    def test_client_immutability(self):
        """Test client immutability."""
        client = GitHubAPIClient()
        original_url = getattr(client, "BASE_URL")
        setattr(client, "BASE_URL", "https://evil.api.com")
        new_client = GitHubAPIClient()
        new_url = getattr(new_client, "BASE_URL")
        assert new_url == original_url
