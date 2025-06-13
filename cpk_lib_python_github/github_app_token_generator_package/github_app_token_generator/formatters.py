# -*- coding: utf-8 -*-
"""Output formatting utilities."""
import logging
from typing import Any, Dict, List

from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Handle formatted output for the CLI."""

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors

    def print_success(self, message: str):
        """Print success message with green color."""
        if self.use_colors:
            print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        else:
            print(f"✅ {message}")

    def print_error(self, message: str):
        """Print error message with red color."""
        if self.use_colors:
            print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
        else:
            print(f"❌ {message}")

    def print_warning(self, message: str):
        """Print warning message with yellow color."""
        if self.use_colors:
            print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
        else:
            print(f"⚠️  {message}")

    def print_info(self, message: str):
        """Print info message with blue color."""
        if self.use_colors:
            print(f"{Fore.CYAN}ℹ️  {message}{Style.RESET_ALL}")
        else:
            print(f"ℹ️  {message}")

    def print_token(self, token: str):
        """Print token with highlighting."""
        if self.use_colors:
            print(f"{Fore.GREEN}{Style.BRIGHT}{token}{Style.RESET_ALL}")
        else:
            print(token)

    def format_installations_table(self, installations: List[Dict[str, Any]]) -> str:
        """Format installations as a table."""
        if not installations:
            return f"{Fore.YELLOW}No installations found{Style.RESET_ALL}"

        lines = [
            "",
            f"{Fore.CYAN}{Style.BRIGHT}=== Available GitHub ",
            f"App Installations ==={Style.RESET_ALL}",
            "",
            f"{Fore.BLUE}{'Installation ID':<20}{Style.RESET_ALL}"
            f" | {Fore.BLUE}{'Account':<20}{Style.RESET_ALL}"
            f" | {Fore.BLUE}{'Target Type':<15}{Style.RESET_ALL}",
            f"{'-' * 60}",
        ]

        # Add rows
        for installation in installations:
            install_id = str(installation.get("id", "N/A"))
            account = installation.get("account", {}).get("login", "N/A")
            target_type = installation.get("target_type", "N/A")

            if self.use_colors:
                row = (
                    f"{Fore.YELLOW}{install_id:<20}{Style.RESET_ALL} | "
                    f"{Fore.GREEN}{account:<20}{Style.RESET_ALL} | "
                    f"{target_type:<15}"
                )
            else:
                row = f"{install_id:<20} | {account:<20} | {target_type:<15}"

            lines.append(row)

        # Add footer
        count = len(installations)
        lines.extend(
            [
                "",
                f"{Fore.CYAN}ℹ️  Found {count} installation(s){Style.RESET_ALL}",
                f"{Fore.BLUE}💡 Use --org <org-name> or{Style.RESET_ALL}",
                f"{Fore.BLUE}   --installation-id <id> to get a token{Style.RESET_ALL}",
            ]
        )

        return "\n".join(lines)

    def format_token_validation(self, validation_result: Dict[str, Any]) -> str:
        """Format token validation results."""
        lines = []

        if validation_result.get("valid"):
            lines.append(f"{Fore.GREEN}✅ Token is valid{Style.RESET_ALL}")
            lines.append(f"Type: {validation_result.get('type', 'Unknown')}")

            if "repositories_count" in validation_result:
                count = validation_result["repositories_count"]
                lines.append(
                    f"Accessible repositories: {Fore.CYAN}{count}{Style.RESET_ALL}"
                )

            if "rate_limit" in validation_result:
                rate_limit = validation_result["rate_limit"]
                remaining = rate_limit.get("remaining", "Unknown")
                limit = rate_limit.get("limit", "Unknown")
                lines.append(
                    f"Rate limit: {Fore.YELLOW}{remaining}/{limit}{Style.RESET_ALL}"
                )

            if "scopes" in validation_result and validation_result["scopes"]:
                scopes = ", ".join(validation_result["scopes"])
                lines.append(f"Scopes: {Fore.MAGENTA}{scopes}{Style.RESET_ALL}")
        else:
            lines.append(f"{Fore.RED}❌ Token is invalid{Style.RESET_ALL}")
            if "reason" in validation_result:
                lines.append(f"Reason: {validation_result['reason']}")
            if "error" in validation_result:
                lines.append(f"Error: {validation_result['error']}")

        return "\n".join(lines)

    def _format_basic_app_info(self, app_info: Dict[str, Any]) -> str:
        """Format basic app information section."""
        lines = [
            f"{Fore.GREEN}{Style.BRIGHT}🤖 App Information{Style.RESET_ALL}",
            f"  ID: {Fore.YELLOW}{app_info.get('id', 'Unknown')}{Style.RESET_ALL}",
            f"  Name: {Fore.GREEN}{app_info.get('name', 'Unknown')}{Style.RESET_ALL}",
            f"  Slug: {Fore.CYAN}{app_info.get('slug', 'Unknown')}{Style.RESET_ALL}",
            f"  Description: {app_info.get('description', 'No description')}",
        ]

        owner = app_info.get("owner", {})
        lines.extend(
            [
                f"  Owner: {Fore.MAGENTA}",
                f"{owner.get('login', 'Unknown')}{Style.RESET_ALL}",
                f"  Owner Type: {owner.get('type', 'Unknown')}",
                f"  URL: {Fore.BLUE}"
                f"{app_info.get('html_url', 'Unknown')}{Style.RESET_ALL}",
                f"  Created: {Fore.BLUE}",
                f"{app_info.get('created_at', 'Unknown')}{Style.RESET_ALL}",
                "",  # Empty line
            ]
        )

        return "\n".join(lines)

    def format_app_analysis(
        self,
        app_info: Dict[str, Any],
        installations: List[Dict[str, Any]],
        installation_repos: Dict[int, Dict[str, Any]],
    ) -> str:
        """Format comprehensive GitHub App analysis."""
        lines = [
            f"{Fore.CYAN}{Style.BRIGHT}=== GitHub App Analysis ==={Style.RESET_ALL}",
            "",
        ]

        # Basic app info
        lines.append(self._format_basic_app_info(app_info))

        # Installation summary
        lines.extend(
            [
                f"{Fore.BLUE}{Style.BRIGHT}📍 Installation Summary{Style.RESET_ALL}",
                f"  Total Installations: {Fore.YELLOW}",
                f"{len(installations)}{Style.RESET_ALL}",
            ]
        )

        total_repos = sum(
            repos.get("total_count", 0) for repos in installation_repos.values()
        )

        lines.extend(
            [
                f"  Total Repositories: {Fore.YELLOW}{total_repos}{Style.RESET_ALL}",
                "  Installed On:",
            ]
        )

        for installation in installations:
            account = installation.get("account", {}).get("login", "Unknown")
            target_type = installation.get("target_type", "Unknown")
            created_at = installation.get("created_at", "")
            created = created_at[:10] if created_at else "Unknown"
            lines.append(
                f"    {Fore.GREEN}✅{Style.RESET_ALL} "
                f"{Fore.CYAN}{account}{Style.RESET_ALL} ({target_type}) - {created}"
            )

        lines.append("")  # Empty line

        # Permissions
        if "permissions" in app_info:
            lines.append(self._format_permissions(app_info["permissions"]))

        # Events
        if "events" in app_info:
            lines.append(self._format_events(app_info["events"]))

        # Repository details
        if installation_repos:
            lines.append(
                self._format_repo_details(
                    installations, installation_repos, total_repos
                )
            )

        return "\n".join(lines)

    def _format_permissions(self, permissions: Dict[str, str]) -> str:
        """Format permissions section."""
        lines = [f"{Fore.MAGENTA}{Style.BRIGHT}🔐 App Permissions{Style.RESET_ALL}"]

        for perm, level in permissions.items():
            if level == "write":
                color = Fore.RED
                icon = "✏️"
            elif level == "read":
                color = Fore.GREEN
                icon = "👁️"
            else:
                color = Fore.YELLOW
                icon = "🔧"

            lines.append(f"  {icon} {perm}: {color}{level}{Style.RESET_ALL}")

        lines.append("")  # Empty line
        return "\n".join(lines)

    def _format_events(self, events: List[str]) -> str:
        """Format events section."""
        lines = [f"{Fore.BLUE}{Style.BRIGHT}📡 Subscribed Events{Style.RESET_ALL}"]

        for event in events:
            lines.append(f"  📨 {Fore.CYAN}{event}{Style.RESET_ALL}")

        lines.append("")  # Empty line
        return "\n".join(lines)

    def _format_repo_details(
        self,
        installations: List[Dict[str, Any]],
        installation_repos: Dict[int, Dict[str, Any]],
        total_repos: int,
    ) -> str:
        """Format repository details section."""
        lines = [
            f"{Fore.GREEN}{Style.BRIGHT}📚 Accessible Repositories "
            f"({total_repos} total){Style.RESET_ALL}"
        ]

        threshold = 100

        for installation in installations:
            install_id = installation.get("id")
            account = installation.get("account", {}).get("login", "Unknown")

            if install_id in installation_repos:
                repos = installation_repos[install_id]
                repo_count = repos.get("total_count", 0)

                # Add installation header
                lines.append(f"  {Fore.CYAN}{account}:{Style.RESET_ALL}")

                # Add repository lines
                for repo in repos.get("repositories", [])[:threshold]:
                    repo_name = repo.get("full_name", "Unknown")
                    lines.append(f"    • {repo_name}")

                # Add "more repositories" line if needed
                if repo_count > threshold:
                    lines.append(
                        f"    ... and {repo_count - threshold} more repositories"
                    )

        return "\n".join(lines)

    def print_progress(self, message: str, success: bool = True):
        """Print progress indicator."""
        if success:
            if self.use_colors:
                print(f"{Fore.GREEN}✓{Style.RESET_ALL} {message}")
            else:
                print(f"✓ {message}")
        else:
            if self.use_colors:
                print(f"{Fore.RED}✗{Style.RESET_ALL} {message}")
            else:
                print(f"✗ {message}")

    def confirm_action(self, message: str, force: bool = False) -> bool:
        """Ask for user confirmation."""
        if force:
            self.print_info(f"Force mode enabled - {message}")
            return True

        response = input(f"{Fore.YELLOW}⚠️  {message} (y/N): {Style.RESET_ALL}")
        return response.lower() in ["y", "yes"]
