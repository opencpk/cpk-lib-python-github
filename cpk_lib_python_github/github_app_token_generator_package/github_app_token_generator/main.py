# -*- coding: utf-8 -*-
"""GitHub App Token Generator - Main entry point."""
import logging
import sys

from colorama import init

from .cli import create_parser, print_banner
from .config import get_config_from_env
from .formatters import OutputFormatter
from .github_api import GitHubAPIClient
from .token_manager import TokenManager

# Initialize colorama
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("github_app_token.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def handle_operations(args, config, token_manager):
    """Handle different operations based on command line arguments."""
    if args.validate_token:
        token_manager.validate_token(args.validate_token)
    elif args.revoke_token:
        token_manager.revoke_token(args.revoke_token, args.force)
    elif args.analyze_app:
        token_manager.analyze_app(config)
    elif args.list_installations:
        token_manager.list_installations(config)
    elif args.org:
        token_manager.generate_org_token(config, args.org)
    elif args.installation_id:
        token_manager.generate_installation_token(config, args.installation_id)
    else:
        # Default: show installations
        token_manager.list_installations(config)


def handle_error(error, args=None):
    """Handle different types of errors with appropriate messages."""
    if isinstance(error, ValueError):
        # Configuration/validation errors - clean user-friendly message
        print(f"Error: {error}", file=sys.stderr)
        return 1
    if isinstance(error, FileNotFoundError):
        # File not found errors - specific guidance
        print(f"Error: {error}", file=sys.stderr)
        print("Please check that the specified file exists and is readable.", file=sys.stderr)
        return 1
    if isinstance(error, PermissionError):
        # Permission errors - specific guidance
        print(f"Error: {error}", file=sys.stderr)
        print("Please check file permissions.", file=sys.stderr)
        return 1
    if isinstance(error, KeyboardInterrupt):
        # User pressed Ctrl+C - clean exit
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130

    # Unexpected errors - show minimal info, suggest debug mode
    print(f"Unexpected error: {error}", file=sys.stderr)

    # Only show stack trace in debug mode
    if args and hasattr(args, "debug") and args.debug:
        logger.exception("Full error details:")
    else:
        print("Run with --debug for more details.", file=sys.stderr)

    return 1


def main():
    """Main entry point."""
    args = None
    try:
        print_banner()

        parser = create_parser()
        args = parser.parse_args()

        # Set debug logging if requested
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")

        # Get configuration - this can raise ValueError for user errors
        config = get_config_from_env(args)

        # Initialize components
        api_client = GitHubAPIClient()
        formatter = OutputFormatter()

        # Create token manager
        token_manager = TokenManager(api_client, formatter)

        # Handle different operations
        handle_operations(args, config, token_manager)

    except Exception as error:
        exit_code = handle_error(error, args)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
