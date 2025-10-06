"""Main entry point for GitHub backup"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

from .backup import GitHubTeamsBackup
from .cli import create_config_from_args, parse_args
from .exporters import (
    export_to_csv,
    export_to_excel,
    export_to_json,
    export_to_multiple_csvs,
    export_to_structured_json,
)


def create_output_directory(org_name: str, limit_users: int = None) -> Path:
    """Create organized output directory structure"""
    test_suffix = "_test" if limit_users else ""

    # Create main backup directory
    backup_dir = Path(f"github_backup_{org_name}{test_suffix}")

    # If directory exists, remove it completely and recreate
    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    backup_dir.mkdir(exist_ok=True)

    # Create subdirectories
    (backup_dir / "json").mkdir(exist_ok=True)
    (backup_dir / "csv").mkdir(exist_ok=True)
    (backup_dir / "excel").mkdir(exist_ok=True)

    print(f"📁 Created output directory: {backup_dir.absolute()}")
    return backup_dir


def main(args=None) -> int:
    """Main function for GitHub backup"""
    try:
        # Parse command line arguments
        parsed_args = parse_args(args)

        # Create configuration
        config = create_config_from_args(parsed_args)

        # Create organized output directory
        output_dir = create_output_directory(parsed_args.org, parsed_args.limit_users)

        # Create backup tool
        backup_tool = GitHubTeamsBackup(config)

        # Perform backup
        backup = backup_tool.backup_organization()

        # Generate base filename with directory
        if not parsed_args.output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_suffix = "_test" if parsed_args.limit_users else ""
            base_filename = f"{parsed_args.org}_teams_backup_{timestamp}{test_suffix}"
        else:
            base_filename = Path(parsed_args.output).stem

        # Export to different formats in organized folders
        print("\n📤 Exporting backup data...")
        print("=" * 50)

        # JSON exports
        json_file = output_dir / "json" / f"{base_filename}.json"
        export_to_json(backup, str(json_file))

        if parsed_args.structured_json:
            structured_json_file = output_dir / "json" / f"{base_filename}_structured.json"
            export_to_structured_json(backup, str(structured_json_file))

        # CSV exports
        if parsed_args.csv:
            csv_file = output_dir / "csv" / f"{base_filename}.csv"
            export_to_csv(backup, str(csv_file))

        if parsed_args.multi_csv:
            # Pass the base path for multiple CSV files
            csv_base_path = output_dir / "csv" / base_filename
            export_to_multiple_csvs(backup, str(csv_base_path))

        # Excel export
        if parsed_args.excel:
            excel_file = output_dir / "excel" / f"{base_filename}.xlsx"
            export_to_excel(backup, str(excel_file))

        # Default to Excel if no export option specified
        if not (
            parsed_args.csv
            or parsed_args.multi_csv
            or parsed_args.excel
            or parsed_args.structured_json
        ):
            print("\n💡 No export format specified, using --excel by default...")
            excel_file = output_dir / "excel" / f"{base_filename}.xlsx"
            export_to_excel(backup, str(excel_file))

        # Print summary of created files
        print("\n📋 Backup Summary")
        print("=" * 50)
        print(f"Organization: {parsed_args.org}")
        print(f"Total Users: {len(backup.users)}")
        print(f"Output Directory: {output_dir.absolute()}")
        print("\n📁 Created Files:")

        # List all created files
        for subdir in ["json", "csv", "excel"]:
            subdir_path = output_dir / subdir
            if subdir_path.exists():
                files = list(subdir_path.glob("*"))
                if files:
                    print(f"\n  📂 {subdir.upper()} Files:")
                    for file in sorted(files):
                        file_size = file.stat().st_size
                        size_str = (
                            f"{file_size:,} bytes"
                            if file_size < 1024 * 1024
                            else f"{file_size/(1024*1024):.1f} MB"
                        )
                        print(f"     📄 {file.name} ({size_str})")

        print(f"\n🎉 All done! Teams backup for '{parsed_args.org}' completed.")
        print("\n📋 Next steps after SSO enforcement:")
        print("   1. Use the Excel file or CSV files to recreate team memberships")
        print("   2. The Excel file provides the best formatted view of your team structure")
        print("   3. Direct repository access should be preserved automatically")

        return 0

    except KeyboardInterrupt:
        print("\n❌ Backup cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
