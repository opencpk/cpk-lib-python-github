"""Command line interface for GitHub backup"""

import argparse
import os
from datetime import datetime
from typing import Optional

from .config import DEFAULT_BATCH_SIZE, DEFAULT_MAX_WORKERS, BackupConfig


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="🔒 GitHub Teams Backup - Capture team memberships before SSO enforcement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script focuses on team memberships since.


Export Options:
- --csv: Single CSV file (original format, can be messy)
- --multi-csv: Multiple focused CSV files
- --excel: Rich formatted Excel file with multiple sheets (recommended)
- --structured-json: Clean, team-focused JSON format

Examples:
  # Basic teams backup with Excel export
  python -m cpk_lib_python_github.github_user_access_backup --org myorg --token ghp_xxxxx --excel

  # Test with limited users
  python -m cpk_lib_python_github.github_user_access_backup --org myorg --token ghp_xxxxx --limit-users 10 --excel

  # Full backup with all export formats
  python -m cpk_lib_python_github.github_user_access_backup --org myorg --token ghp_xxxxx --multi-csv --excel --structured-json

  # Custom output directory
  python -m cpk_lib_python_github.github_user_access_backup --org myorg --token ghp_xxxxx --excel --output-dir ./backups
        """,
    )

    parser.add_argument("--org", required=True, help="Organization name to backup")
    parser.add_argument("--token", required=False, help="GitHub token with admin:org permissions")
    parser.add_argument(
        "--output", help="Output JSON file (default: {org}_teams_backup_{timestamp}.json)"
    )
    parser.add_argument(
        "--output-dir", help="Output directory (default: ./github_backup_{org}_{timestamp})"
    )
    parser.add_argument(
        "--csv", action="store_true", help="Export to single CSV format (can be messy)"
    )
    parser.add_argument(
        "--multi-csv", action="store_true", help="Export to multiple focused CSV files"
    )
    parser.add_argument(
        "--excel", action="store_true", help="Export to rich formatted Excel file (recommended)"
    )
    parser.add_argument(
        "--structured-json", action="store_true", help="Export to clean, structured JSON format"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Number of users to process per batch (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f"Maximum number of worker threads (default: {DEFAULT_MAX_WORKERS})",
    )
    parser.add_argument(
        "--limit-users", type=int, help="Limit number of users to process (for testing)"
    )

    return parser


def parse_args(args=None) -> argparse.Namespace:
    """Parse command line arguments"""
    parser = create_parser()
    return parser.parse_args(args)


def create_config_from_args(args: argparse.Namespace) -> BackupConfig:
    """Create BackupConfig from parsed arguments"""
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError(
            "GitHub token must be provided via --token or GITHUB_TOKEN environment variable"
        )
    return BackupConfig(
        token=token,
        org_name=args.org,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        limit_users=args.limit_users,
    )


def generate_output_filename(org_name: str, limit_users: Optional[int] = None) -> str:
    """Generate output filename if not provided"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_suffix = "_test" if limit_users else ""
    return f"{org_name}_teams_backup_{timestamp}{test_suffix}.json"
