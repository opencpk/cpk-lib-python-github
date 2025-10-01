# -*- coding: utf-8 -*-
"""Command line interface for GitHub App Token Generator."""
import argparse

from colorama import Fore, Style


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            f"{Fore.GREEN}{Style.BRIGHT}Generate and manage GitHub App "
            f"installation tokens{Style.RESET_ALL}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Fore.GREEN}{Style.BRIGHT}Examples:{Style.RESET_ALL}
  {Fore.CYAN}# Generate tokens (using private key file){Style.RESET_ALL}
  {Fore.YELLOW}%(prog)s{Style.RESET_ALL} {Fore.CYAN}--app-id{Style.RESET_ALL} $APP_ID \\
    {Fore.CYAN}--private-key-path{Style.RESET_ALL} /path/to/key.pem \\
    {Fore.CYAN}--org{Style.RESET_ALL} myorg

  {Fore.CYAN}# Generate tokens (using private key content){Style.RESET_ALL}
  {Fore.YELLOW}%(prog)s{Style.RESET_ALL} {Fore.CYAN}--app-id{Style.RESET_ALL} $APP_ID \\
    {Fore.CYAN}--private-key{Style.RESET_ALL} "$(cat /path/to/key.pem)" \\
    {Fore.CYAN}--org{Style.RESET_ALL} myorg

  {Fore.CYAN}# Using environment variables{Style.RESET_ALL}
  {Fore.YELLOW}export APP_ID=$APP_ID{Style.RESET_ALL}
  {Fore.YELLOW}export PRIVATE_KEY_PATH=/path/to/key.pem{Style.RESET_ALL}
  {Fore.YELLOW}%(prog)s{Style.RESET_ALL} {Fore.CYAN}--org{Style.RESET_ALL} myorg

{Fore.BLUE}{Style.BRIGHT}Environment Variables:{Style.RESET_ALL}
  {Fore.MAGENTA}APP_ID{Style.RESET_ALL}                    GitHub App ID
  {Fore.MAGENTA}PRIVATE_KEY_PATH{Style.RESET_ALL}          Path to private key file
  {Fore.MAGENTA}PRIVATE_KEY{Style.RESET_ALL}               Private key content directly
        """,
    )

    # Add arguments
    parser.add_argument(
        "--app-id", type=int, help="(REQUIRED) GitHub App ID (or set APP_ID env var)", metavar="ID"
    )

    # Private key group
    key_group = parser.add_mutually_exclusive_group()
    key_group.add_argument(
        "--private-key-path",
        help="(REQUIRED if private-key not present) Path to private key file",
        metavar="PATH",
    )
    key_group.add_argument(
        "--private-key",
        help="(REQUIRED if private-key-path not present) Private key content directly",
        metavar="KEY_CONTENT",
    )

    # Operations
    parser.add_argument("--org", help="Organization name to get token for", metavar="ORG")
    parser.add_argument("--installation-id", help="Installation ID (if known)", metavar="ID")
    parser.add_argument("--list-installations", action="store_true", help="List all installations")
    parser.add_argument("--analyze-app", action="store_true", help="Analyze GitHub App details")
    parser.add_argument("--validate-token", help="Validate an existing token", metavar="TOKEN")
    parser.add_argument("--revoke-token", help="Revoke an existing token", metavar="TOKEN")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser


def print_banner():
    """Print colorful banner."""
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════╗
║               🔑 GitHub App Token Generator              ║
║                      GitHub Tools                        ║
╚══════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
{Fore.GREEN}A powerful CLI tool for generating, managing,{Style.RESET_ALL}
{Fore.GREEN}and analyzing GitHub App tokens{Style.RESET_ALL}
"""
    print(banner)
