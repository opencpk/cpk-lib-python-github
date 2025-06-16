# -*- coding: utf-8 -*-
"""Unit tests for GitHubAPIClient - All methods."""
from unittest.mock import patch

import pytest  # pylint: disable=import-error
import requests
import responses  # pylint: disable=import-error

from ..github_app_token_generator.github_api import GitHubAPIClient


class TestGetInstallationAccessToken:
    """Test cases for get_installation_access_token method."""

    @responses.activate
    def test_get_installation_access_token_success(
        self,
        github_api_client,
        sample_jwt_token,
        sample_installation_id,
        sample_access_token_response,
        sample_expected_token,
    ):  # pylint: disable=too-many-positional-arguments
        """Test successful installation access token retrieval with MOCK response."""
        expected_url = (
            f"https://api.github.com/app/installations/"
            f"{sample_installation_id}/access_tokens"
        )

        responses.add(
            responses.POST, expected_url, json=sample_access_token_response, status=201
        )

        result_token = github_api_client.get_installation_access_token(
            sample_jwt_token, sample_installation_id
        )

        assert result_token == sample_expected_token
        assert len(responses.calls) == 1

        request = responses.calls[0].request
        assert request.method == "POST"
        assert request.url == expected_url
        assert request.headers["Authorization"] == f"Bearer {sample_jwt_token}"
        assert request.headers["Accept"] == "application/vnd.github.v3+json"

    @responses.activate
    def test_get_installation_access_token_http_401_unauthorized(
        self, github_api_client, sample_jwt_token, sample_installation_id
    ):
        """Test HTTP 401 error (unauthorized/bad credentials)."""
        expected_url = (
            f"https://api.github.com/app/installations/"
            f"{sample_installation_id}/access_tokens"
        )

        responses.add(
            responses.POST,
            expected_url,
            json={"message": "Bad credentials"},
            status=401,
        )

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            github_api_client.get_installation_access_token(
                sample_jwt_token, sample_installation_id
            )

        assert exc_info.value.response.status_code == 401

    @responses.activate
    def test_get_installation_access_token_http_404_not_found(
        self, github_api_client, sample_jwt_token, sample_installation_id
    ):
        """Test HTTP 404 error (installation not found)."""
        expected_url = (
            f"https://api.github.com/app/installations/"
            f"{sample_installation_id}/access_tokens"
        )

        responses.add(
            responses.POST, expected_url, json={"message": "Not Found"}, status=404
        )

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            github_api_client.get_installation_access_token(
                sample_jwt_token, sample_installation_id
            )

        assert exc_info.value.response.status_code == 404

    @responses.activate
    def test_get_installation_access_token_missing_token_field(
        self, github_api_client, sample_jwt_token, sample_installation_id
    ):
        """Test response missing 'token' field."""
        expected_url = (
            f"https://api.github.com/app/installations/"
            f"{sample_installation_id}/access_tokens"
        )

        invalid_response = {
            "expires_at": "2023-12-31T23:59:59Z",
            "permissions": {"contents": "read"},
        }

        responses.add(responses.POST, expected_url, json=invalid_response, status=201)

        with pytest.raises(ValueError) as exc_info:
            github_api_client.get_installation_access_token(
                sample_jwt_token, sample_installation_id
            )

        assert "Invalid response: token not found in response" in str(exc_info.value)

    @responses.activate
    def test_get_installation_access_token_empty_response(
        self, github_api_client, sample_jwt_token, sample_installation_id
    ):
        """Test empty JSON response."""
        expected_url = (
            f"https://api.github.com/app/installations/"
            f"{sample_installation_id}/access_tokens"
        )

        responses.add(responses.POST, expected_url, json={}, status=201)

        with pytest.raises(ValueError) as exc_info:
            github_api_client.get_installation_access_token(
                sample_jwt_token, sample_installation_id
            )

        assert "Invalid response: token not found in response" in str(exc_info.value)

    @responses.activate
    def test_get_installation_access_token_malformed_json(
        self, github_api_client, sample_jwt_token, sample_installation_id
    ):
        """Test malformed JSON response."""
        expected_url = (
            f"https://api.github.com/app/installations/"
            f"{sample_installation_id}/access_tokens"
        )

        responses.add(
            responses.POST,
            expected_url,
            body="invalid json response",
            status=201,
            content_type="application/json",
        )

        with pytest.raises(requests.exceptions.RequestException):
            github_api_client.get_installation_access_token(
                sample_jwt_token, sample_installation_id
            )

    def test_get_installation_access_token_timeout(
        self, sample_jwt_token, sample_installation_id
    ):
        """Test network timeout."""
        # Create client with very short timeout
        github_api_client = GitHubAPIClient(timeout=0.001)

        with pytest.raises(requests.exceptions.RequestException):
            github_api_client.get_installation_access_token(
                sample_jwt_token, sample_installation_id
            )

    @responses.activate
    def test_get_installation_access_token_connection_error(
        self, github_api_client, sample_jwt_token, sample_installation_id
    ):
        """Test connection error (no mock response registered)."""
        # Don't register any mock response to simulate connection error

        with pytest.raises(requests.exceptions.RequestException):
            github_api_client.get_installation_access_token(
                sample_jwt_token, sample_installation_id
            )


class TestListInstallations:
    """Test cases for list_installations method."""

    @responses.activate
    def test_list_installations_success(
        self, github_api_client, sample_jwt_token, sample_installations
    ):
        """Test successful installations listing."""
        expected_url = "https://api.github.com/app/installations"

        responses.add(
            responses.GET, expected_url, json=sample_installations, status=200
        )

        installations = github_api_client.list_installations(sample_jwt_token)

        assert installations == sample_installations
        assert len(installations) == 2
        assert len(responses.calls) == 1

        request = responses.calls[0].request
        assert request.method == "GET"
        assert request.url == expected_url
        assert request.headers["Authorization"] == f"Bearer {sample_jwt_token}"
        assert request.headers["Accept"] == "application/vnd.github.v3+json"

    @responses.activate
    def test_list_installations_empty_list(self, github_api_client, sample_jwt_token):
        """Test empty installations list."""
        expected_url = "https://api.github.com/app/installations"

        responses.add(responses.GET, expected_url, json=[], status=200)

        installations = github_api_client.list_installations(sample_jwt_token)

        assert installations == []
        assert len(installations) == 0

    @responses.activate
    def test_list_installations_http_401_error(
        self, github_api_client, sample_jwt_token
    ):
        """Test installations listing with 401 error."""
        expected_url = "https://api.github.com/app/installations"

        responses.add(
            responses.GET, expected_url, json={"message": "Bad credentials"}, status=401
        )

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            github_api_client.list_installations(sample_jwt_token)

        assert exc_info.value.response.status_code == 401

    @responses.activate
    def test_list_installations_http_403_error(
        self, github_api_client, sample_jwt_token
    ):
        """Test installations listing with 403 error."""
        expected_url = "https://api.github.com/app/installations"

        responses.add(
            responses.GET, expected_url, json={"message": "Forbidden"}, status=403
        )

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            github_api_client.list_installations(sample_jwt_token)

        assert exc_info.value.response.status_code == 403

    @responses.activate
    def test_list_installations_network_error(
        self, github_api_client, sample_jwt_token
    ):
        """Test installations listing with network error."""
        # Don't add any responses to simulate network error

        with pytest.raises(requests.exceptions.RequestException):
            github_api_client.list_installations(sample_jwt_token)


class TestValidateToken:
    """Test cases for validate_token method."""

    @responses.activate
    def test_validate_token_success(
        self, github_api_client, sample_installation_token, sample_repositories
    ):
        """Test successful token validation."""
        expected_url = "https://api.github.com/installation/repositories"

        responses.add(
            responses.GET,
            expected_url,
            json=sample_repositories,
            status=200,
            headers={
                "X-OAuth-Scopes": "repo, user",
                "X-RateLimit-Remaining": "4999",
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Reset": "1639629600",
            },
        )

        result = github_api_client.validate_token(sample_installation_token)

        assert result["valid"] is True
        assert result["type"] == "GitHub App Installation Token"
        assert result["repositories_count"] == 3
        assert result["scopes"] == ["repo", "user"]
        assert result["rate_limit"]["remaining"] == "4999"
        assert result["rate_limit"]["limit"] == "5000"
        assert result["rate_limit"]["reset"] == "1639629600"

        request = responses.calls[0].request
        assert request.headers["Authorization"] == f"token {sample_installation_token}"

    @responses.activate
    def test_validate_token_no_scopes(
        self, github_api_client, sample_installation_token, sample_repositories
    ):
        """Test token validation with no scopes header."""
        expected_url = "https://api.github.com/installation/repositories"

        responses.add(
            responses.GET,
            expected_url,
            json=sample_repositories,
            status=200,
            headers={"X-RateLimit-Remaining": "4999", "X-RateLimit-Limit": "5000"},
        )

        result = github_api_client.validate_token(sample_installation_token)

        assert result["valid"] is True
        assert result["scopes"] == []

    @responses.activate
    def test_validate_token_401_invalid(
        self, github_api_client, sample_installation_token
    ):
        """Test token validation with 401 (invalid token)."""
        expected_url = "https://api.github.com/installation/repositories"

        responses.add(
            responses.GET, expected_url, json={"message": "Bad credentials"}, status=401
        )

        result = github_api_client.validate_token(sample_installation_token)

        assert result["valid"] is False
        assert result["status_code"] == 401
        assert result["reason"] == "Invalid or expired token"

    @responses.activate
    def test_validate_token_403_insufficient_permissions(
        self, github_api_client, sample_installation_token
    ):
        """Test token validation with 403 (insufficient permissions)."""
        expected_url = "https://api.github.com/installation/repositories"

        responses.add(
            responses.GET, expected_url, json={"message": "Forbidden"}, status=403
        )

        result = github_api_client.validate_token(sample_installation_token)

        assert result["valid"] is False
        assert result["status_code"] == 403
        assert result["reason"] == "Insufficient permissions"

    @responses.activate
    def test_validate_token_404_not_found(
        self, github_api_client, sample_installation_token
    ):
        """Test token validation with 404 (not found)."""
        expected_url = "https://api.github.com/installation/repositories"

        responses.add(
            responses.GET, expected_url, json={"message": "Not Found"}, status=404
        )

        result = github_api_client.validate_token(sample_installation_token)

        assert result["valid"] is False
        assert result["status_code"] == 404
        assert result["reason"] == "HTTP 404"

    @responses.activate
    def test_validate_token_network_error(
        self, github_api_client, sample_installation_token
    ):
        """Test token validation with network error."""
        # Don't add any responses to simulate network error

        result = github_api_client.validate_token(sample_installation_token)

        assert result["valid"] is False
        assert "error" in result


class TestRevokeInstallationToken:
    """Test cases for revoke_installation_token method."""

    @responses.activate
    def test_revoke_installation_token_success(
        self, github_api_client, sample_installation_token
    ):
        """Test successful token revocation."""
        expected_url = "https://api.github.com/installation/token"

        responses.add(responses.DELETE, expected_url, status=204)

        result = github_api_client.revoke_installation_token(sample_installation_token)

        assert result is True
        assert len(responses.calls) == 1

        request = responses.calls[0].request
        assert request.method == "DELETE"
        assert request.url == expected_url
        assert request.headers["Authorization"] == f"token {sample_installation_token}"

    @responses.activate
    def test_revoke_installation_token_404_not_found(
        self, github_api_client, sample_installation_token
    ):
        """Test token revocation when token not found."""
        expected_url = "https://api.github.com/installation/token"

        responses.add(
            responses.DELETE, expected_url, json={"message": "Not Found"}, status=404
        )

        result = github_api_client.revoke_installation_token(sample_installation_token)

        assert result is False

    @responses.activate
    def test_revoke_installation_token_401_error(
        self, github_api_client, sample_installation_token
    ):
        """Test token revocation with 401 error."""
        expected_url = "https://api.github.com/installation/token"

        responses.add(
            responses.DELETE,
            expected_url,
            json={"message": "Bad credentials"},
            status=401,
        )

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            github_api_client.revoke_installation_token(sample_installation_token)

        assert exc_info.value.response.status_code == 401

    @responses.activate
    def test_revoke_installation_token_403_error(
        self, github_api_client, sample_installation_token
    ):
        """Test token revocation with 403 error."""
        expected_url = "https://api.github.com/installation/token"

        responses.add(
            responses.DELETE, expected_url, json={"message": "Forbidden"}, status=403
        )

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            github_api_client.revoke_installation_token(sample_installation_token)

        assert exc_info.value.response.status_code == 403

    @responses.activate
    def test_revoke_installation_token_network_error(
        self, github_api_client, sample_installation_token
    ):
        """Test token revocation with network error."""
        # Don't add any responses to simulate network error

        with pytest.raises(requests.exceptions.RequestException):
            github_api_client.revoke_installation_token(sample_installation_token)


class TestGetAppInfo:
    """Test cases for get_app_info method."""

    @responses.activate
    def test_get_app_info_success(
        self, github_api_client, sample_jwt_token, sample_app_info
    ):
        """Test successful app info retrieval."""
        expected_url = "https://api.github.com/app"

        responses.add(responses.GET, expected_url, json=sample_app_info, status=200)

        app_info = github_api_client.get_app_info(sample_jwt_token)

        assert app_info == sample_app_info
        assert app_info["name"] == "Test GitHub App"
        assert app_info["id"] == 123456
        assert len(responses.calls) == 1

        request = responses.calls[0].request
        assert request.method == "GET"
        assert request.url == expected_url
        assert request.headers["Authorization"] == f"Bearer {sample_jwt_token}"

    @responses.activate
    def test_get_app_info_401_error(self, github_api_client, sample_jwt_token):
        """Test app info retrieval with 401 error."""
        expected_url = "https://api.github.com/app"

        responses.add(
            responses.GET, expected_url, json={"message": "Bad credentials"}, status=401
        )

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            github_api_client.get_app_info(sample_jwt_token)

        assert exc_info.value.response.status_code == 401

    @responses.activate
    def test_get_app_info_404_error(self, github_api_client, sample_jwt_token):
        """Test app info retrieval with 404 error."""
        expected_url = "https://api.github.com/app"

        responses.add(
            responses.GET, expected_url, json={"message": "Not Found"}, status=404
        )

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            github_api_client.get_app_info(sample_jwt_token)

        assert exc_info.value.response.status_code == 404

    @responses.activate
    def test_get_app_info_403_error(self, github_api_client, sample_jwt_token):
        """Test app info retrieval with 403 error."""
        expected_url = "https://api.github.com/app"

        responses.add(
            responses.GET, expected_url, json={"message": "Forbidden"}, status=403
        )

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            github_api_client.get_app_info(sample_jwt_token)

        assert exc_info.value.response.status_code == 403

    @responses.activate
    def test_get_app_info_network_error(self, github_api_client, sample_jwt_token):
        """Test app info retrieval with network error."""
        # Don't add any responses to simulate network error

        with pytest.raises(requests.exceptions.RequestException):
            github_api_client.get_app_info(sample_jwt_token)


class TestGetInstallationRepositories:
    """Test cases for get_installation_repositories method."""

    @patch.object(GitHubAPIClient, "get_installation_access_token")
    @responses.activate
    def test_get_installation_repositories_success(
        self,
        mock_get_token,
        github_api_client,
        sample_jwt_token,
        sample_installation_id,
        sample_installation_token,
        sample_repositories,
    ):  # pylint: disable=too-many-positional-arguments
        """Test successful installation repositories retrieval."""
        # Mock the access token retrieval
        mock_get_token.return_value = sample_installation_token

        expected_url = "https://api.github.com/installation/repositories"
        responses.add(responses.GET, expected_url, json=sample_repositories, status=200)

        repos = github_api_client.get_installation_repositories(
            sample_jwt_token, sample_installation_id
        )

        assert repos == sample_repositories
        assert repos["total_count"] == 3
        assert len(repos["repositories"]) == 3
        mock_get_token.assert_called_once_with(sample_jwt_token, sample_installation_id)

        request = responses.calls[0].request
        assert request.headers["Authorization"] == f"token {sample_installation_token}"

    @patch.object(GitHubAPIClient, "get_installation_access_token")
    def test_get_installation_repositories_token_error(
        self,
        mock_get_token,
        github_api_client,
        sample_jwt_token,
        sample_installation_id,
    ):
        """Test installation repositories retrieval with token error."""
        # Mock the access token retrieval to raise an exception
        mock_get_token.side_effect = requests.exceptions.RequestException(
            "Network error"
        )

        repos = github_api_client.get_installation_repositories(
            sample_jwt_token, sample_installation_id
        )

        assert repos["total_count"] == 0
        assert repos["repositories"] == []
        assert "error" in repos
        assert "Network error" in repos["error"]

    @patch.object(GitHubAPIClient, "get_installation_access_token")
    @responses.activate
    def test_get_installation_repositories_api_error(
        self,
        mock_get_token,
        github_api_client,
        sample_jwt_token,
        sample_installation_id,
        sample_installation_token,
    ):  # pylint: disable=too-many-positional-arguments
        """Test installation repositories retrieval with API error."""
        # Mock successful token retrieval
        mock_get_token.return_value = sample_installation_token

        expected_url = "https://api.github.com/installation/repositories"
        responses.add(
            responses.GET, expected_url, json={"message": "Forbidden"}, status=403
        )

        repos = github_api_client.get_installation_repositories(
            sample_jwt_token, sample_installation_id
        )

        assert repos["total_count"] == 0
        assert repos["repositories"] == []
        assert "error" in repos

    @patch.object(GitHubAPIClient, "get_installation_access_token")
    @responses.activate
    def test_get_installation_repositories_empty_response(
        self,
        mock_get_token,
        github_api_client,
        sample_jwt_token,
        sample_installation_id,
        sample_installation_token,
    ):  # pylint: disable=too-many-positional-arguments
        """Test installation repositories with empty response."""
        # Mock successful token retrieval
        mock_get_token.return_value = sample_installation_token

        expected_url = "https://api.github.com/installation/repositories"
        empty_repos = {"total_count": 0, "repositories": []}
        responses.add(responses.GET, expected_url, json=empty_repos, status=200)

        repos = github_api_client.get_installation_repositories(
            sample_jwt_token, sample_installation_id
        )

        assert repos["total_count"] == 0
        assert repos["repositories"] == []


class TestGetAccessibleRepositoriesViaToken:
    """Test cases for get_accessible_repositories_via_token method."""

    @responses.activate
    def test_get_accessible_repositories_via_token_success(
        self, github_api_client, sample_installation_token, sample_repositories
    ):
        """Test successful repositories retrieval via token."""
        expected_url = "https://api.github.com/installation/repositories"

        responses.add(responses.GET, expected_url, json=sample_repositories, status=200)

        repos = github_api_client.get_accessible_repositories_via_token(
            sample_installation_token
        )

        assert repos == sample_repositories
        assert repos["total_count"] == 3
        assert len(repos["repositories"]) == 3
        assert len(responses.calls) == 1

        request = responses.calls[0].request
        assert request.method == "GET"
        assert request.url == expected_url
        assert request.headers["Authorization"] == f"token {sample_installation_token}"

    @responses.activate
    def test_get_accessible_repositories_via_token_empty(
        self, github_api_client, sample_installation_token
    ):
        """Test empty repositories list."""
        expected_url = "https://api.github.com/installation/repositories"

        empty_repos = {"total_count": 0, "repositories": []}
        responses.add(responses.GET, expected_url, json=empty_repos, status=200)

        repos = github_api_client.get_accessible_repositories_via_token(
            sample_installation_token
        )

        assert repos["total_count"] == 0
        assert repos["repositories"] == []

    @responses.activate
    def test_get_accessible_repositories_via_token_401_error(
        self, github_api_client, sample_installation_token
    ):
        """Test repositories retrieval via token with 401 error."""
        expected_url = "https://api.github.com/installation/repositories"

        responses.add(
            responses.GET, expected_url, json={"message": "Bad credentials"}, status=401
        )

        repos = github_api_client.get_accessible_repositories_via_token(
            sample_installation_token
        )

        assert repos["total_count"] == 0
        assert repos["repositories"] == []
        assert "error" in repos

    @responses.activate
    def test_get_accessible_repositories_via_token_403_error(
        self, github_api_client, sample_installation_token
    ):
        """Test repositories retrieval via token with 403 error."""
        expected_url = "https://api.github.com/installation/repositories"

        responses.add(
            responses.GET, expected_url, json={"message": "Forbidden"}, status=403
        )

        repos = github_api_client.get_accessible_repositories_via_token(
            sample_installation_token
        )

        assert repos["total_count"] == 0
        assert repos["repositories"] == []
        assert "error" in repos

    @responses.activate
    def test_get_accessible_repositories_via_token_404_error(
        self, github_api_client, sample_installation_token
    ):
        """Test repositories retrieval via token with 404 error."""
        expected_url = "https://api.github.com/installation/repositories"

        responses.add(
            responses.GET, expected_url, json={"message": "Not Found"}, status=404
        )

        repos = github_api_client.get_accessible_repositories_via_token(
            sample_installation_token
        )

        assert repos["total_count"] == 0
        assert repos["repositories"] == []
        assert "error" in repos

    @responses.activate
    def test_get_accessible_repositories_via_token_network_error(
        self, github_api_client, sample_installation_token
    ):
        """Test repositories retrieval via token with network error."""
        # Don't add any responses to simulate network error

        repos = github_api_client.get_accessible_repositories_via_token(
            sample_installation_token
        )

        assert repos["total_count"] == 0
        assert repos["repositories"] == []
        assert "error" in repos


class TestGitHubAPIClientEdgeCases:
    """Test edge cases and error scenarios."""

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
        self, github_api_client, sample_jwt_token, sample_installations, sample_app_info
    ):
        """Test multiple method calls using the same client instance."""
        # Mock installations endpoint
        responses.add(
            responses.GET,
            "https://api.github.com/app/installations",
            json=sample_installations,
            status=200,
        )

        # Mock app info endpoint
        responses.add(
            responses.GET,
            "https://api.github.com/app",
            json=sample_app_info,
            status=200,
        )

        # Call multiple methods
        installations = github_api_client.list_installations(sample_jwt_token)
        app_info = github_api_client.get_app_info(sample_jwt_token)

        assert len(installations) == 2
        assert app_info["name"] == "Test GitHub App"
        assert len(responses.calls) == 2

    @responses.activate
    def test_request_headers_consistency(self, github_api_client, sample_jwt_token):
        """Test that all methods use consistent headers."""
        # Mock multiple endpoints
        responses.add(
            responses.GET,
            "https://api.github.com/app/installations",
            json=[],
            status=200,
        )
        responses.add(responses.GET, "https://api.github.com/app", json={}, status=200)

        # Call methods
        github_api_client.list_installations(sample_jwt_token)
        github_api_client.get_app_info(sample_jwt_token)

        # Verify headers
        for call in responses.calls:
            assert call.request.headers["Accept"] == "application/vnd.github.v3+json"
            assert call.request.headers["Authorization"] == f"Bearer {sample_jwt_token}"

    @responses.activate
    def test_different_installation_ids(
        self, github_api_client, sample_jwt_token, sample_access_token_response
    ):
        """Test with different installation IDs."""
        test_cases = [123, 456789, 999999999]

        for installation_id in test_cases:
            expected_url = (
                f"https://api.github.com/app/installations/"
                f"{installation_id}/access_tokens"
            )

            responses.add(
                responses.POST,
                expected_url,
                json=sample_access_token_response,
                status=201,
            )

        # Test each installation ID
        for installation_id in test_cases:
            token = github_api_client.get_installation_access_token(
                sample_jwt_token, installation_id
            )
            assert token == sample_access_token_response["token"]

    @responses.activate
    def test_rate_limiting_headers(
        self, github_api_client, sample_installation_token, sample_repositories
    ):
        """Test handling of rate limiting headers."""
        expected_url = "https://api.github.com/installation/repositories"

        responses.add(
            responses.GET,
            expected_url,
            json=sample_repositories,
            status=200,
            headers={
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Remaining": "100",
                "X-RateLimit-Reset": "1640995200",
                "X-RateLimit-Used": "4900",
                "X-RateLimit-Resource": "core",
            },
        )

        result = github_api_client.validate_token(sample_installation_token)

        assert result["valid"] is True
        assert result["rate_limit"]["limit"] == "5000"
        assert result["rate_limit"]["remaining"] == "100"
        assert result["rate_limit"]["reset"] == "1640995200"

    @responses.activate
    def test_large_repository_count(self, github_api_client, sample_installation_token):
        """Test handling of large repository counts."""
        large_repo_response = {
            "total_count": 1000,
            "repositories": [
                {
                    "id": i,
                    "full_name": f"testorg/repo{i}",
                    "name": f"repo{i}",
                    "private": i % 2 == 0,
                }
                for i in range(100)  # First 100 repos
            ],
        }

        expected_url = "https://api.github.com/installation/repositories"
        responses.add(responses.GET, expected_url, json=large_repo_response, status=200)

        repos = github_api_client.get_accessible_repositories_via_token(
            sample_installation_token
        )

        assert repos["total_count"] == 1000
        assert len(repos["repositories"]) == 100

    def test_str_representation(self):
        """Test string representation of client."""
        client = GitHubAPIClient(timeout=45)
        str_repr = str(client)
        # Basic check that string representation exists
        assert "GitHubAPIClient" in str_repr or "timeout" in str_repr

    def test_client_immutability(self):
        """Test that BASE_URL cannot be changed accidentally."""
        client = GitHubAPIClient()
        original_url = getattr(client, "BASE_URL")

        # This should not change the class attribute
        setattr(client, "BASE_URL", "https://evil.api.com")

        # Create new client to verify class attribute unchanged
        new_client = GitHubAPIClient()
        new_url = getattr(new_client, "BASE_URL")
        assert new_url == original_url
