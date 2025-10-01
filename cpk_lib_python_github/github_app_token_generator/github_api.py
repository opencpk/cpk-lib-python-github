# -*- coding: utf-8 -*-
"""GitHub API client."""
import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """GitHub API client for GitHub App operations."""

    BASE_URL = "https://api.github.com"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def get_installation_access_token(self, jwt_token: str, installation_id: int) -> str:
        """Get installation access token."""
        url = f"{self.BASE_URL}/app/installations/{installation_id}/access_tokens"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            logger.debug("Requesting access token for installation ID: %s", installation_id)
            response = requests.post(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            token_data = response.json()
            if "token" not in token_data:
                raise ValueError("Invalid response: token not found in response")

            logger.info(
                "Successfully obtained access token for installation: %s",
                installation_id,
            )
            return token_data["token"]

        except requests.exceptions.HTTPError as http_error:
            logger.error("HTTP error occurred while getting access token: %s", http_error)
            raise http_error
        except requests.exceptions.RequestException as req_error:
            logger.error("Request error occurred while getting access token: %s", req_error)
            raise req_error

    def list_installations(self, jwt_token: str) -> List[Dict[str, Any]]:
        """List GitHub App installations."""
        url = f"{self.BASE_URL}/app/installations"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            logger.debug("Fetching GitHub App installations")
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            installations = response.json()
            logger.info("Found %d installations", len(installations))
            return installations

        except requests.exceptions.HTTPError as http_error:
            logger.error("HTTP error occurred while listing installations: %s", http_error)
            raise http_error
        except requests.exceptions.RequestException as req_error:
            logger.error("Request error occurred while listing installations: %s", req_error)
            raise req_error

    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate a GitHub token."""
        url = f"{self.BASE_URL}/installation/repositories"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            logger.debug("Validating GitHub App installation token")
            response = requests.get(url, headers=headers, timeout=self.timeout)

            if response.status_code == 200:
                repo_info = response.json()
                scopes_header = response.headers.get("X-OAuth-Scopes", "")
                scopes = scopes_header.split(", ") if scopes_header else []

                rate_limit = {
                    "remaining": response.headers.get("X-RateLimit-Remaining"),
                    "limit": response.headers.get("X-RateLimit-Limit"),
                    "reset": response.headers.get("X-RateLimit-Reset"),
                }

                return {
                    "valid": True,
                    "type": "GitHub App Installation Token",
                    "repositories_count": repo_info.get("total_count", 0),
                    "scopes": scopes,
                    "rate_limit": rate_limit,
                }

            # Handle error cases
            error_messages = {
                401: "Invalid or expired token",
                403: "Insufficient permissions",
            }

            return {
                "valid": False,
                "status_code": response.status_code,
                "reason": error_messages.get(response.status_code, f"HTTP {response.status_code}"),
            }

        except requests.exceptions.RequestException as req_error:
            logger.error("Error validating token: %s", req_error)
            return {"valid": False, "error": str(req_error)}

    def revoke_installation_token(self, token: str) -> bool:
        """Revoke an installation access token."""
        url = f"{self.BASE_URL}/installation/token"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            logger.debug("Attempting to revoke installation token")
            response = requests.delete(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            logger.info("Successfully revoked installation token")
            return True

        except requests.exceptions.HTTPError as http_error:
            if http_error.response is not None and http_error.response.status_code == 404:
                logger.warning("Token not found or already revoked")
                return False
            logger.error("HTTP error occurred while revoking token: %s", http_error)
            raise http_error
        except requests.exceptions.RequestException as req_error:
            logger.error("Request error occurred while revoking token: %s", req_error)
            raise req_error

    def get_app_info(self, jwt_token: str) -> Dict[str, Any]:
        """Get GitHub App information."""
        url = f"{self.BASE_URL}/app"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            logger.debug("Fetching GitHub App information")
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            app_info = response.json()
            logger.info("Successfully retrieved app information")
            return app_info

        except requests.exceptions.RequestException as error:
            logger.error("Error fetching app info: %s", error)
            raise error

    def get_installation_repositories(self, jwt_token: str, installation_id: int) -> Dict[str, Any]:
        """Get repositories accessible by installation."""
        try:
            # First get an installation access token
            installation_token = self.get_installation_access_token(jwt_token, installation_id)

            # Use the installation token to get repositories
            url = f"{self.BASE_URL}/installation/repositories"
            headers = {
                "Authorization": f"token {installation_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            logger.debug("Fetching repositories for installation: %s", installation_id)
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as error:
            logger.error("Error fetching installation repositories: %s", error)
            # Return empty result instead of raising
            return {"total_count": 0, "repositories": [], "error": str(error)}

    def get_accessible_repositories_via_token(self, installation_token: str) -> Dict[str, Any]:
        """Get repositories using installation token instead of JWT."""
        url = f"{self.BASE_URL}/installation/repositories"
        headers = {
            "Authorization": f"token {installation_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        try:
            logger.debug("Fetching repositories via installation token")
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as error:
            logger.error("Error fetching repositories via token: %s", error)
            return {"total_count": 0, "repositories": [], "error": str(error)}
