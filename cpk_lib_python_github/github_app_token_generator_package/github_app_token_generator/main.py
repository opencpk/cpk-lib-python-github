# -*- coding: utf-8 -*-
"""
GitHub App Token Generator

This module provides functionality to generate GitHub App installation tokens
for CLI use and automation scripts.
"""
import argparse
import logging
import os
import sys
import time

import jwt
import requests
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("github_app_token.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def read_private_key(private_key_path):
    """
    Read the private key from a file.

    Args:
        private_key_path (str): The path to the private key file.

    Returns:
        str: The content of the private key file.

    Raises:
        FileNotFoundError: If the private key file is not found.
        IOError: If there's an error reading the file.
    """
    try:
        with open(private_key_path, "r", encoding="utf-8") as key_file:
            content = key_file.read()
            logger.debug("Successfully read private key from: %s", private_key_path)
            return content
    except FileNotFoundError as error:
        logger.error("Private key file not found: %s", private_key_path)
        raise error
    except IOError as error:
        logger.error("Error reading private key file: %s", error)
        raise error


def get_private_key_content(private_key_path=None, private_key_content=None):
    """
    Get private key content from either file path or direct content.

    Args:
        private_key_path (str, optional): Path to private key file.
        private_key_content (str, optional): Direct private key content.

    Returns:
        str: The private key content.

    Raises:
        ValueError: If neither or both options are provided.
        FileNotFoundError: If the private key file is not found.
        IOError: If there's an error reading the file.
    """
    if private_key_path and private_key_content:
        raise ValueError("Cannot specify both --private-key-path and --private-key")

    if not private_key_path and not private_key_content:
        raise ValueError("Must specify either --private-key-path or --private-key")

    if private_key_content:
        logger.debug("Using private key content provided directly")
        return private_key_content

    if private_key_path:
        logger.debug("Reading private key from file: %s", private_key_path)
        return read_private_key(private_key_path)

    # This shouldn't be reached, but just in case
    raise ValueError("No private key source provided")


def generate_jwt(app_id, private_key):
    """
    Generate a JWT for the GitHub App to provide the app identity to Github
    (will be used to generate installation token).

    Args:
        app_id (str): The GitHub App ID.
        private_key (str): The private key for the GitHub App.

    Returns:
        str: The generated JWT.

    Raises:
        ValueError: If the JWT generation fails.
    """
    try:
        payload = {
            "iat": int(time.time()),
            "exp": int(time.time()) + (10 * 60),  # JWT expiration time (10 minutes)
            "iss": app_id,
        }
        token = jwt.encode(payload, private_key, algorithm="RS256")
        logger.debug("Successfully generated JWT for app ID: %s", app_id)
        return token
    except Exception as error:
        logger.error("Failed to generate JWT: %s", error)
        raise ValueError(f"Failed to generate JWT: {error}") from error


def get_installation_access_token(jwt_token, installation_id):
    """
    Get an installation access token for the GitHub App.

    Args:
        jwt_token (str): The JWT for the GitHub App.
        installation_id (int): The installation ID of the GitHub App.

    Returns:
        str: The installation access token.

    Raises:
        requests.exceptions.HTTPError: If an HTTP error occurs.
        requests.exceptions.RequestException: If a request error occurs.
        ValueError: If the response is invalid.
    """
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        logger.debug("Requesting access token for installation ID: %s", installation_id)
        response = requests.post(url, headers=headers, timeout=30)
        response.raise_for_status()

        token_data = response.json()
        if "token" not in token_data:
            raise ValueError("Invalid response: token not found in response")

        logger.info(
            "Successfully obtained access token for installation: %s", installation_id
        )
        return token_data["token"]

    except requests.exceptions.HTTPError as http_error:
        logger.error("HTTP error occurred while getting access token: %s", http_error)
        raise http_error
    except requests.exceptions.RequestException as req_error:
        logger.error("Request error occurred while getting access token: %s", req_error)
        raise req_error
    except ValueError as val_error:
        logger.error("Invalid response format: %s", val_error)
        raise val_error


def list_installations(jwt_token):
    """
    List installations of the GitHub App
    (which org the app is installed with other details such as installation id).

    Args:
        jwt_token (str): The JWT for the GitHub App.

    Returns:
        list: A list of installations.

    Raises:
        requests.exceptions.HTTPError: If an HTTP error occurs.
        requests.exceptions.RequestException: If a request error occurs.
    """
    url = "https://api.github.com/app/installations"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        logger.debug("Fetching GitHub App installations")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        installations = response.json()
        logger.info("Found %d installations", len(installations))
        return installations

    except requests.exceptions.HTTPError as http_error:
        logger.error("HTTP error occurred while listing installations: %s", http_error)
        raise http_error
    except requests.exceptions.RequestException as req_error:
        logger.error(
            "Request error occurred while listing installations: %s", req_error
        )
        raise req_error


def revoke_installation_token(token):
    """
    Revoke an installation access token.

    Args:
        token (str): The installation access token to revoke.

    Returns:
        bool: True if revocation was successful, False otherwise.

    Raises:
        requests.exceptions.HTTPError: If an HTTP error occurs.
        requests.exceptions.RequestException: If a request error occurs.
    """
    url = "https://api.github.com/installation/token"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        logger.debug("Attempting to revoke installation token")
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()

        logger.info("Successfully revoked installation token")
        return True

    except requests.exceptions.HTTPError as http_error:
        if response.status_code == 404:
            logger.warning("Token not found or already revoked")
            return False
        logger.error("HTTP error occurred while revoking token: %s", http_error)
        raise http_error
    except requests.exceptions.RequestException as req_error:
        logger.error("Request error occurred while revoking token: %s", req_error)
        raise req_error


def validate_token(token):
    """
    Validate if a token is still active by checking installation info.

    Args:
        token (str): The token to validate.

    Returns:
        dict: Token info if valid, error info if invalid.
    """
    url = "https://api.github.com/installation/repositories"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        logger.debug("Validating GitHub App installation token")
        response = requests.get(url, headers=headers, timeout=30)

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
        if response.status_code == 401:
            logger.info("Token validation failed: 401 - Token is invalid or expired")
            return {
                "valid": False,
                "status_code": response.status_code,
                "reason": "Invalid or expired token",
            }
        if response.status_code == 403:
            logger.info("Token validation failed: 403 - Insufficient permissions")
            return {
                "valid": False,
                "status_code": response.status_code,
                "reason": "Insufficient permissions",
            }

        logger.info("Token validation failed: %s", response.status_code)
        return {"valid": False, "status_code": response.status_code}

    except requests.exceptions.RequestException as req_error:
        logger.error("Error validating token: %s", req_error)
        return {"valid": False, "error": str(req_error)}


def _fetch_installation_repos(jwt_token, installation):
    """
    Helper function to fetch repositories for a single installation.

    Args:
        jwt_token (str): JWT token for the GitHub App
        installation (dict): Installation information

    Returns:
        tuple: (repos_list, repo_count, permissions_set, events_set)
    """
    installation_id = installation["id"]
    result_data = {
        "repos": [],
        "repo_count": 0,
        "permissions_set": set(),
        "events_set": set(),
    }

    try:
        install_token = get_installation_access_token(jwt_token, installation_id)

        # Get repositories for this installation
        repo_response = requests.get(
            "https://api.github.com/installation/repositories",
            headers={
                "Authorization": f"token {install_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=30,
        )

        if repo_response.status_code == 200:
            repo_data = repo_response.json()
            result_data["repo_count"] = repo_data.get("total_count", 0)

            # Add ALL repositories (just names and installation)
            for repo in repo_data.get("repositories", []):
                result_data["repos"].append(
                    {
                        "name": repo["full_name"],
                        "installation": installation["account"]["login"],
                    }
                )

            # Track permissions and events
            result_data["permissions_set"].update(
                installation.get("permissions", {}).keys()
            )
            result_data["events_set"].update(installation.get("events", []))

    except Exception as e:
        logger.warning(
            "Could not fetch repos for installation %s: %s",
            installation_id,
            e,
        )

    return (
        result_data["repos"],
        result_data["repo_count"],
        result_data["permissions_set"],
        result_data["events_set"],
    )


def get_github_app_details(jwt_token):
    """
    Get detailed information about the GitHub App.

    Args:
        jwt_token (str): JWT token for the GitHub App

    Returns:
        dict: Comprehensive app information
    """
    logger.info("Fetching GitHub App details")

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-App-Token-Generator/1.2.0",
    }

    app_details = {
        "valid": False,
        "app_info": None,
        "installations": [],
        "total_repositories": 0,
        "repository_sample": [],
        "permissions_summary": {},
        "events_summary": [],
        "error": None,
    }

    try:
        # 1. Get the GitHub App information
        app_response = requests.get(
            "https://api.github.com/app", headers=headers, timeout=30
        )

        if app_response.status_code == 200:
            app_details["valid"] = True
            app_data = app_response.json()

            app_details["app_info"] = {
                "id": app_data.get("id"),
                "name": app_data.get("name"),
                "slug": app_data.get("slug"),
                "description": app_data.get("description"),
                "owner": app_data.get("owner", {}),
                "external_url": app_data.get("external_url"),
                "html_url": app_data.get("html_url"),
                "created_at": app_data.get("created_at"),
                "updated_at": app_data.get("updated_at"),
                "permissions": app_data.get("permissions", {}),
                "events": app_data.get("events", []),
            }

            # 2. Get installations and process repository data
            app_details["installations"] = list_installations(jwt_token)

            # 3. Aggregate data from all installations
            repo_aggregation = {
                "total_repos": 0,
                "all_repos": [],
                "permissions_used": set(),
                "events_used": set(),
            }

            for installation in app_details["installations"]:
                repos, count, perms, events = _fetch_installation_repos(
                    jwt_token, installation
                )
                repo_aggregation["all_repos"].extend(repos)
                repo_aggregation["total_repos"] += count
                repo_aggregation["permissions_used"].update(perms)
                repo_aggregation["events_used"].update(events)

            # 4. Update app_details with aggregated data
            app_details["total_repositories"] = repo_aggregation["total_repos"]
            app_details["repository_sample"] = repo_aggregation["all_repos"]
            app_details["permissions_summary"] = dict(app_data.get("permissions", {}))
            app_details["events_summary"] = list(repo_aggregation["events_used"])

        elif app_response.status_code == 401:
            app_details["error"] = "Invalid JWT token"
        elif app_response.status_code == 403:
            app_details["error"] = "Insufficient permissions"
        else:
            app_details["error"] = f"HTTP {app_response.status_code}"

    except requests.exceptions.RequestException as e:
        app_details["error"] = f"Request failed: {str(e)}"

    return app_details


def _print_app_info(app_info):
    """Helper function to print app information section."""
    print(f"\n{Fore.YELLOW}🤖 App Information{Style.RESET_ALL}")
    print(
        f"  {Style.DIM}ID:{Style.RESET_ALL} "
        f"{Fore.CYAN}{app_info['id']}{Style.RESET_ALL}"
    )
    print(
        f"  {Style.DIM}Name:{Style.RESET_ALL} "
        f"{Fore.CYAN}{app_info['name']}{Style.RESET_ALL}"
    )
    print(
        f"  {Style.DIM}Slug:{Style.RESET_ALL} "
        f"{Fore.CYAN}{app_info['slug']}{Style.RESET_ALL}"
    )

    if app_info["description"]:
        print(
            f"  {Style.DIM}Description:{Style.RESET_ALL} "
            f"{Fore.CYAN}{app_info['description']}{Style.RESET_ALL}"
        )

    owner = app_info["owner"]
    if owner:
        print(
            f"  {Style.DIM}Owner:{Style.RESET_ALL} "
            f"{Fore.CYAN}{owner.get('login', 'Unknown')}{Style.RESET_ALL}"
        )
        print(
            f"  {Style.DIM}Owner Type:{Style.RESET_ALL} "
            f"{Fore.CYAN}{owner.get('type', 'Unknown')}{Style.RESET_ALL}"
        )

    if app_info["html_url"]:
        print(
            f"  {Style.DIM}URL:{Style.RESET_ALL} "
            f"{Fore.CYAN}{app_info['html_url']}{Style.RESET_ALL}"
        )

    print(
        f"  {Style.DIM}Created:{Style.RESET_ALL} "
        f"{Fore.CYAN}{app_info['created_at'][:10]}{Style.RESET_ALL}"
    )


def _print_installations(installations, total_repositories):
    """Helper function to print installations section."""
    print(f"\n{Fore.YELLOW}📍 Installation Summary{Style.RESET_ALL}")
    print(
        f"  {Style.DIM}Total Installations:{Style.RESET_ALL} "
        f"{Fore.CYAN}{len(installations)}{Style.RESET_ALL}"
    )
    print(
        f"  {Style.DIM}Total Repositories:{Style.RESET_ALL} "
        f"{Fore.CYAN}{total_repositories}{Style.RESET_ALL}"
    )

    if installations:
        print(f"  {Style.DIM}Installed On:{Style.RESET_ALL}")
        for installation in installations:
            account = installation["account"]
            target_type = installation["target_type"]
            created = installation["created_at"][:10]
            status_icon = "✅" if not installation.get("suspended_at") else "⚠️"

            print(
                f"    {status_icon} {Fore.CYAN}{account['login']}{Style.RESET_ALL} "
                f"({target_type}) - {created}"
            )


def _print_permissions(permissions):
    """Helper function to print permissions section."""
    if permissions:
        print(f"\n{Fore.YELLOW}🔐 App Permissions{Style.RESET_ALL}")
        for perm, level in permissions.items():
            color = (
                Fore.GREEN
                if level == "write"
                else Fore.YELLOW if level == "read" else Fore.BLUE
            )
            icon = "✏️" if level == "write" else "👁️" if level == "read" else "🔧"
            print(f"  {icon} {color}{perm}: {level}{Style.RESET_ALL}")


def _print_events(events):
    """Helper function to print events section."""
    if events:
        print(f"\n{Fore.YELLOW}📡 Subscribed Events{Style.RESET_ALL}")
        for event in sorted(events):
            print(f"  📨 {Fore.CYAN}{event}{Style.RESET_ALL}")


def _print_repositories(repos, total_repositories):
    """Helper function to print repositories section."""
    if repos:
        print(
            f"\n{Fore.YELLOW}📚 Accessible Repositories ({total_repositories} total)"
            f"{Style.RESET_ALL}"
        )

        # Group repositories by installation for better organization
        repos_by_installation = {}
        for repo in repos:
            installation = repo["installation"]
            if installation not in repos_by_installation:
                repos_by_installation[installation] = []
            repos_by_installation[installation].append(repo["name"])

        # Print repositories grouped by installation
        for installation, repo_names in repos_by_installation.items():
            print(f"  {Style.DIM}{installation}:{Style.RESET_ALL}")
            for repo_name in repo_names:
                print(f"    • {Fore.CYAN}{repo_name}{Style.RESET_ALL}")

        # Show remaining count if there are more repos
        if total_repositories > len(repos):
            remaining = total_repositories - len(repos)
            print(
                f"    {Style.DIM}... and {remaining} more repositories"
                f"{Style.RESET_ALL}"
            )


def print_app_analysis(app_details):
    """
    Print comprehensive GitHub App analysis.

    Args:
        app_details (dict): App analysis results
    """
    print(f"\n{Fore.CYAN}{Style.BRIGHT}=== GitHub App Analysis ==={Style.RESET_ALL}")

    if not app_details["valid"]:
        print(f"{Fore.RED}❌ Unable to analyze app{Style.RESET_ALL}")
        if app_details["error"]:
            print(
                f"  {Style.DIM}Error:{Style.RESET_ALL} "
                f"{Fore.RED}{app_details['error']}{Style.RESET_ALL}"
            )
        return

    app_info = app_details["app_info"]
    installations = app_details["installations"]
    permissions = app_details["permissions_summary"]
    events = app_details["events_summary"]
    repos = app_details["repository_sample"]
    total_repos = app_details["total_repositories"]

    # Print each section using helper functions
    _print_app_info(app_info)
    _print_installations(installations, total_repos)
    _print_permissions(permissions)
    _print_events(events)
    _print_repositories(repos, total_repos)


def handle_app_analysis(app_id, private_key_path=None, private_key_content=None):
    """
    Handle GitHub App analysis command.

    Args:
        app_id (str): GitHub App ID
        private_key_path (str, optional): Path to private key file
        private_key_content (str, optional): Private key content directly
    """
    logger.info("Starting GitHub App analysis")

    try:
        private_key = get_private_key_content(private_key_path, private_key_content)
        jwt_token = generate_jwt(app_id, private_key)

        app_details = get_github_app_details(jwt_token)
        print_app_analysis(app_details)

    except Exception as e:
        print(f"{Fore.RED}❌ Error analyzing app: {e}{Style.RESET_ALL}")
        logger.error("App analysis failed: %s", e)


def revoke_with_confirmation(token, force=False):
    """
    Revoke token with user confirmation and validation.

    Args:
        token (str): The token to revoke.
        force (bool): Skip confirmation if True.

    Returns:
        bool: True if revocation was successful.
    """
    # First validate the token
    token_info = validate_token(token)

    if not token_info["valid"]:
        print(f"{Fore.RED}❌ Token is already invalid or expired{Style.RESET_ALL}")
        if "reason" in token_info:
            reason = token_info["reason"]
            print(
                f"  {Style.DIM}Reason:{Style.RESET_ALL}"
                f" {Fore.RED}{reason}{Style.RESET_ALL}"
            )
        return False

    print(f"\n{Fore.CYAN}{Style.BRIGHT}=== Token Information ==={Style.RESET_ALL}")
    token_type = token_info.get("type", "Unknown")
    repo_count = token_info.get("repositories_count", "N/A")
    print(
        f"  {Style.DIM}Type:{Style.RESET_ALL} {Fore.CYAN}{token_type}{Style.RESET_ALL}"
    )
    print(
        f"  {Style.DIM}Repositories:{Style.RESET_ALL}"
        f" {Fore.CYAN}{repo_count}{Style.RESET_ALL}"
    )

    scopes = token_info.get("scopes", [])
    scopes_text = (
        ", ".join(scopes) if scopes and scopes != [""] else "GitHub App permissions"
    )
    print(
        f"  {Style.DIM}Scopes:{Style.RESET_ALL}"
        f" {Fore.CYAN}{scopes_text}{Style.RESET_ALL}"
    )

    rate_limit = token_info["rate_limit"]
    rate_limit_text = f"{rate_limit['remaining']}/{rate_limit['limit']}"
    print(
        f"  {Style.DIM}Rate limit:{Style.RESET_ALL}"
        f" {Fore.CYAN}{rate_limit_text}{Style.RESET_ALL}"
    )

    if not force:
        prompt = (
            f"\n{Fore.YELLOW}⚠️  Are you sure you want to revoke this token? (y/N): "
            f"{Style.RESET_ALL}"
        )
        confirmation = input(prompt)
        if confirmation.lower() not in ["y", "yes"]:
            print(f"{Fore.RED}🚫 Token revocation cancelled{Style.RESET_ALL}")
            return False

    try:
        success = revoke_installation_token(token)
        if success:
            print(f"{Fore.GREEN}🗑️ ✅ Token revoked successfully{Style.RESET_ALL}")
            return True
        print(f"{Fore.RED}❌ Failed to revoke token{Style.RESET_ALL}")
        return False
    except Exception as error:
        print(f"{Fore.RED}❌ Error revoking token: {error}{Style.RESET_ALL}")
        return False


def print_installation_table(installations):
    """
    Print installations in a formatted table.

    Args:
        installations (list): List of installation dictionaries.
    """
    print(
        f"\n{Fore.CYAN}{Style.BRIGHT}=== Available"
        f" GitHub App Installations ==={Style.RESET_ALL}"
    )

    if not installations:
        print(f"{Fore.YELLOW}⚠️  No installations found{Style.RESET_ALL}")
        return

    # Table header
    header = (
        f"{Style.BRIGHT}{'Installation ID':<20} | {'Account':<20} | "
        f"{'Target Type':<15}{Style.RESET_ALL}"
    )
    print(header)
    print(f"{Style.DIM}{'-' * 60}{Style.RESET_ALL}")

    # Table rows
    for installation in installations:
        installation_id = installation["id"]
        account_name = installation["account"]["login"]
        target_type = installation["target_type"]

        row = (
            f"{Fore.CYAN}{installation_id:<20}{Style.RESET_ALL} | "
            f"{Fore.CYAN}{account_name:<20}{Style.RESET_ALL} | "
            f"{Fore.CYAN}{target_type:<15}{Style.RESET_ALL}"
        )
        print(row)

    # Footer info
    count_msg = f"{len(installations)} installation(s)"
    print(f"\n{Fore.BLUE}ℹ️  Found {count_msg}{Style.RESET_ALL}")
    print(
        f"{Fore.BLUE}💡 Use --org <org-name> or"
        f" --installation-id <id> to get a token{Style.RESET_ALL}"
    )


def handle_token_validation(token):
    """
    Handle token validation command.

    Args:
        token (str): The token to validate.
    """
    logger.info("Validating token")
    token_info = validate_token(token)

    if token_info["valid"]:
        print(f"{Fore.GREEN}✅ Token is valid{Style.RESET_ALL}")
        token_type = token_info.get("type", "Unknown")
        repo_count = token_info.get("repositories_count", "N/A")

        print(
            f"  {Style.DIM}Type:{Style.RESET_ALL}"
            f" {Fore.CYAN}{token_type}{Style.RESET_ALL}"
        )
        print(
            f"  {Style.DIM}Repositories:{Style.RESET_ALL}"
            f" {Fore.CYAN}{repo_count}{Style.RESET_ALL}"
        )

        scopes = token_info.get("scopes", [])
        scopes_text = (
            ", ".join(scopes) if scopes and scopes != [""] else "GitHub App permissions"
        )
        print(
            f"  {Style.DIM}Scopes:{Style.RESET_ALL}"
            f" {Fore.CYAN}{scopes_text}{Style.RESET_ALL}"
        )

        rate_limit = token_info["rate_limit"]
        rate_limit_text = f"{rate_limit['remaining']}/{rate_limit['limit']}"
        print(
            f"  {Style.DIM}Rate limit:{Style.RESET_ALL}"
            f" {Fore.CYAN}{rate_limit_text}{Style.RESET_ALL}"
        )
        return

    print(f"{Fore.RED}❌ Token is invalid or expired{Style.RESET_ALL}")
    if "reason" in token_info:
        reason = token_info["reason"]
        print(
            f"  {Style.DIM}Reason:{Style.RESET_ALL} {Fore.RED}{reason}{Style.RESET_ALL}"
        )
    elif "error" in token_info:
        error_msg = token_info["error"]
        print(
            f"  {Style.DIM}Error:{Style.RESET_ALL} "
            f" {Fore.RED}{error_msg}{Style.RESET_ALL}"
        )


def handle_organization_token(org, installations, jwt_token):
    """
    Handle organization token generation.

    Args:
        org (str): Organization name.
        installations (list): List of installations.
        jwt_token (str): JWT token for GitHub App.

    Returns:
        bool: True if successful, False if organization not found.
    """
    logger.info("Looking for installation for organization: %s", org)
    org_installation = next(
        (inst for inst in installations if inst["account"]["login"] == org),
        None,
    )

    if org_installation:
        installation_id = org_installation["id"]
        logger.info(
            "Found installation ID %s for organization: %s",
            installation_id,
            org,
        )
        installation_token = get_installation_access_token(jwt_token, installation_id)
        print(installation_token)
        success_msg = f"Token generated for organization '{org}'"
        print(f"{Fore.GREEN}🔑 ✅ {success_msg}{Style.RESET_ALL}", file=sys.stderr)
        return True

    logger.error("App is not installed in organization: %s", org)
    error_msg = f"App is not installed in organization: {org}"
    print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}", file=sys.stderr)
    info_msg = "Run with --list-installations to see available organizations"
    print(f"{Fore.BLUE}ℹ️  {info_msg}{Style.RESET_ALL}", file=sys.stderr)
    return False


def setup_argument_parser():
    """
    Set up and return the argument parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Generate and manage GitHub App installation tokens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate tokens (using private key file)
  %(prog)s --org myorg --app-id 12345 --private-key-path /path/to/key.pem

  # Generate tokens (using private key content)
  %(prog)s --org myorg --app-id 12345 --private-key "Content of the private Key"

  %(prog)s --installation-id 98765 --app-id 12345 --private-key-path /path/to/key.pem

  # List installations
  %(prog)s --list-installations --app-id 12345 --private-key-path /path/to/key.pem

  # Analyze GitHub App
  %(prog)s --analyze-app --app-id 12345 --private-key "Content of the private Key"

  # Token management
  %(prog)s --validate-token ghs_xxxxxxxxxxxxx
  %(prog)s --revoke-token ghs_xxxxxxxxxxxxx
  %(prog)s --revoke-token ghs_xxxxxxxxxxxxx --force

Environment Variables:
  APP_ID                    GitHub App ID
  PRIVATE_KEY_PATH          Path to private key file
  PRIVATE_KEY               Private key content directly
        """,
    )

    # Existing arguments
    parser.add_argument(
        "--app-id",
        help="GitHub App ID (or set APP_ID env var)",
        metavar="ID",
    )

    # Create mutually exclusive group for private key options
    key_group = parser.add_mutually_exclusive_group()
    key_group.add_argument(
        "--private-key-path",
        help="Path to private key file (or set PRIVATE_KEY_PATH env var)",
        metavar="PATH",
    )
    key_group.add_argument(
        "--private-key",
        help="Private key content directly (or set PRIVATE_KEY env var)",
        metavar="KEY_CONTENT",
    )

    parser.add_argument(
        "--org",
        help="Organization name to get token for",
        metavar="ORG",
    )
    parser.add_argument(
        "--installation-id",
        help="Installation ID (if known)",
        metavar="ID",
    )
    parser.add_argument(
        "--list-installations",
        action="store_true",
        help="List all installations",
    )

    # App analysis argument
    parser.add_argument(
        "--analyze-app",
        action="store_true",
        help="Analyze GitHub App details, permissions, and repositories",
    )

    # Token management arguments
    parser.add_argument(
        "--validate-token",
        help="Validate an existing token",
        metavar="TOKEN",
    )
    parser.add_argument(
        "--revoke-token",
        help="Revoke an existing token",
        metavar="TOKEN",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    return parser


def validate_credentials(app_id, private_key_path=None, private_key_content=None):
    """Validate required credentials are provided."""
    if not app_id:
        logger.error("GitHub App ID is required")
        error_msg = (
            "GitHub App ID required. Use --app-id or set APP_ID environment variable"
        )
        print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}", file=sys.stderr)
        sys.exit(1)

    if not private_key_path and not private_key_content:
        logger.error("Private key is required")
        error_msg = (
            "Private key required. Use --private-key-path, --private-key, or set "
            "PRIVATE_KEY_PATH/PRIVATE_KEY environment variable"
        )
        print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}", file=sys.stderr)
        sys.exit(1)


def handle_token_operations(args):
    """Handle token validation and revocation operations."""
    # Handle token validation (no app-id/private-key required)
    if args.validate_token:
        handle_token_validation(args.validate_token)
        return True

    # Handle token revocation (no app-id/private-key required)
    if args.revoke_token:
        logger.info("Revoking token")
        success = revoke_with_confirmation(args.revoke_token, args.force)
        sys.exit(0 if success else 1)

    return False


def handle_main_operations(args, app_id, private_key_path, private_key_content):
    """Handle the main token generation operations."""
    try:
        logger.info("Starting GitHub App token generation")
        logger.info("App ID: %s", app_id)

        if private_key_path:
            logger.info("Private key path: %s", private_key_path)
        else:
            logger.info("Private key provided directly")

        private_key = get_private_key_content(private_key_path, private_key_content)
        jwt_token = generate_jwt(app_id, private_key)
        installations = list_installations(jwt_token)

        if args.list_installations:
            logger.info("Listing available installations")
            print_installation_table(installations)
            return

        # Handle specific installation ID
        if args.installation_id:
            logger.info("Getting token for installation ID: %s", args.installation_id)
            installation_token = get_installation_access_token(
                jwt_token, args.installation_id
            )
            print(installation_token)
            return

        # Handle organization lookup
        if args.org:
            success = handle_organization_token(args.org, installations, jwt_token)
            sys.exit(0 if success else 1)

        # Default behavior - show all installations
        logger.info("No specific organization or installation ID provided")
        print_installation_table(installations)

    except FileNotFoundError:
        logger.error("Private key file not found: %s", private_key_path)
        error_msg = f"Private key file not found: {private_key_path}"
        print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as req_error:
        logger.error("API request failed: %s", req_error)
        print(
            f"{Fore.RED}❌ Error making API request: {req_error}{Style.RESET_ALL}",
            file=sys.stderr,
        )
        sys.exit(1)
    except (ValueError, jwt.InvalidTokenError) as error:
        logger.error("Token/validation error: %s", error)
        print(f"{Fore.RED}❌ Error: {error}{Style.RESET_ALL}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print(
            f"\n{Fore.YELLOW}⚠️  Operation cancelled by user{Style.RESET_ALL}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as error:
        logger.error("Unexpected error occurred: %s", error)
        print(
            f"{Fore.RED}❌ Unexpected error: {error}{Style.RESET_ALL}",
            file=sys.stderr,
        )
        print(
            f"{Fore.BLUE}ℹ️  Please report this issue with the above "
            f"error message{Style.RESET_ALL}",
            file=sys.stderr,
        )
        sys.exit(1)


def main():
    """Main function to handle CLI arguments and generate GitHub App tokens."""
    parser = setup_argument_parser()
    args = parser.parse_args()

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Handle token operations first (don't need app credentials)
    if handle_token_operations(args):
        return

    # For other operations, app-id and private-key are required
    app_id = args.app_id or os.getenv("APP_ID")
    private_key_path = args.private_key_path or os.getenv("PRIVATE_KEY_PATH")
    private_key_content = args.private_key or os.getenv("PRIVATE_KEY")

    # Handle app analysis
    if args.analyze_app:
        validate_credentials(app_id, private_key_path, private_key_content)
        handle_app_analysis(app_id, private_key_path, private_key_content)
        return

    validate_credentials(app_id, private_key_path, private_key_content)
    handle_main_operations(args, app_id, private_key_path, private_key_content)


if __name__ == "__main__":
    main()
