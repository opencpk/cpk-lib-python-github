# -*- coding: utf-8 -*-
"""Token management operations."""
import logging

from .auth import GitHubAppAuth
from .config import Config
from .formatters import OutputFormatter
from .github_api import GitHubAPIClient

logger = logging.getLogger(__name__)


class TokenManager:
    """Manage GitHub App token operations."""

    def __init__(self, api_client: GitHubAPIClient, formatter: OutputFormatter):
        self.api_client = api_client
        self.formatter = formatter

    def validate_token(self, token: str):
        """Validate a GitHub token - no app config needed."""
        self.formatter.print_info("Validating token...")
        result = self.api_client.validate_token(token)
        formatted_result = self.formatter.format_token_validation(result)
        print(formatted_result)

    def revoke_token(self, token: str, force: bool = False):
        """Revoke a GitHub token - no app config needed."""
        if not self.formatter.confirm_action(
            "Are you sure you want to revoke this token?", force
        ):
            self.formatter.print_info("Token revocation cancelled")
            return

        self.formatter.print_info("Revoking token...")
        success = self.api_client.revoke_installation_token(token)

        if success:
            self.formatter.print_success("Token revoked successfully")
        else:
            self.formatter.print_warning("Token was already revoked or not found")

    def list_installations(self, config: Config):
        """List GitHub App installations - requires app config."""
        if not config.has_required_config:
            self.formatter.print_error(
                "App ID and private key are required for listing installations"
            )
            return

        # Get private key content
        private_key = GitHubAppAuth.get_private_key_content(
            config.private_key_path, config.private_key_content
        )

        # Create auth instance and generate JWT
        auth = GitHubAppAuth(config.app_id, private_key)
        jwt_token = auth.generate_jwt()

        # List installations
        installations = self.api_client.list_installations(jwt_token)

        # Format and display
        formatted_output = self.formatter.format_installations_table(installations)
        print(formatted_output)

    def generate_org_token(self, config: Config, org_name: str):
        """Generate token for a specific organization - requires app config."""
        if not config.has_required_config:
            self.formatter.print_error(
                "App ID and private key are required for token generation"
            )
            return

        # Get private key content
        private_key = GitHubAppAuth.get_private_key_content(
            config.private_key_path, config.private_key_content
        )

        # Create auth instance and generate JWT
        auth = GitHubAppAuth(config.app_id, private_key)
        jwt_token = auth.generate_jwt()

        # Find installation for organization
        installations = self.api_client.list_installations(jwt_token)

        installation_id = None
        for installation in installations:
            if installation.get("account", {}).get("login").lower() == org_name.lower():
                installation_id = installation.get("id")
                break

        if not installation_id:
            self.formatter.print_error(
                f"No installation found for organization: {org_name}"
            )
            return

        # Generate access token
        access_token = self.api_client.get_installation_access_token(
            jwt_token, installation_id
        )

        # Output token
        self.formatter.print_token(access_token)
        self.formatter.print_success(f"Token generated for organization '{org_name}'")

    def generate_installation_token(self, config: Config, installation_id: str):
        """Generate token for a specific installation ID - requires app config."""
        if not config.has_required_config:
            self.formatter.print_error(
                "App ID and private key are required for token generation"
            )
            return

        # Get private key content
        private_key = GitHubAppAuth.get_private_key_content(
            config.private_key_path, config.private_key_content
        )

        # Create auth instance and generate JWT
        auth = GitHubAppAuth(config.app_id, private_key)
        jwt_token = auth.generate_jwt()

        # Generate access token
        try:
            access_token = self.api_client.get_installation_access_token(
                jwt_token, int(installation_id)
            )

            # Output token
            self.formatter.print_token(access_token)
            self.formatter.print_success(
                f"Token generated for installation ID: {installation_id}"
            )

        except ValueError as error:
            self.formatter.print_error(
                f"Invalid installation ID: {installation_id} - {error}"
            )
        except Exception as error:
            self.formatter.print_error(f"Failed to generate token: {error}")

    def analyze_app(self, config: Config):
        """Perform comprehensive GitHub App analysis - requires app config."""
        if not config.has_required_config:
            self.formatter.print_error(
                "App ID and private key are required for app analysis"
            )
            return

        self.formatter.print_info("Analyzing GitHub App...")

        # Get private key content
        private_key = GitHubAppAuth.get_private_key_content(
            config.private_key_path, config.private_key_content
        )

        # Create auth instance and generate JWT
        auth = GitHubAppAuth(config.app_id, private_key)
        jwt_token = auth.generate_jwt()

        try:
            # Get app information
            app_info = self.api_client.get_app_info(jwt_token)

            # Get installations
            installations = self.api_client.list_installations(jwt_token)

            # Get repositories for each installation
            installation_repos = {}
            for installation in installations:
                install_id = installation.get("id")
                if install_id:
                    try:
                        repos = self.api_client.get_installation_repositories(
                            jwt_token, install_id
                        )
                        installation_repos[install_id] = repos
                    except Exception as error:
                        logger.warning(
                            "Could not fetch repos for installation %s: %s",
                            install_id,
                            error,
                        )

            # Format and display comprehensive analysis
            analysis = self.formatter.format_app_analysis(
                app_info, installations, installation_repos
            )
            print(analysis)

        except Exception as error:
            self.formatter.print_error(f"Failed to analyze app: {error}")
            # Fallback to basic installation list
            self.list_installations(config)
