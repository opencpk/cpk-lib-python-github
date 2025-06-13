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


def main():
    """Main entry point."""
    print_banner()

    parser = create_parser()
    args = parser.parse_args()

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Get configuration
    config = get_config_from_env(args)

    # Initialize components
    api_client = GitHubAPIClient()
    formatter = OutputFormatter()

    # Create token manager
    token_manager = TokenManager(api_client, formatter)

    try:
        # Handle different operations
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

    except KeyboardInterrupt:
        formatter.print_error("Operation cancelled by user")
        sys.exit(1)
    except Exception as error:
        formatter.print_error(f"Unexpected error: {error}")
        logger.error("Unexpected error occurred: %s", error)
        sys.exit(1)


if __name__ == "__main__":
    main()
