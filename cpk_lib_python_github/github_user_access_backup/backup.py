"""Main backup functionality"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Set

import requests  # pylint: disable=import-error

from .config import BackupConfig
from .github_api import GitHubAPIClient
from .models import OrganizationBackup, TeamAccess, UserAccess


class GitHubTeamsBackup:
    """GitHub organization team backup utility - focused on teams only"""

    def __init__(self, config: BackupConfig):
        self.config = config
        self.api_client = GitHubAPIClient(config.token, config.max_workers)

        # Cache for team memberships only
        self.team_members_cache: Dict[str, Set[str]] = {}
        self.team_repos_cache: Dict[str, List[str]] = {}

    def build_teams_cache(self, teams_data: List[Dict[str, Any]]) -> None:
        """Build cache of team memberships and repositories"""
        print(f"🔄 Building team cache for {len(teams_data)} teams...")

        def fetch_team_data(team):
            team_slug = team["slug"]
            try:
                # Get team members
                members = self.api_client.get_team_members(self.config.org_name, team_slug)
                member_usernames = {member["login"] for member in members} if members else set()

                # Get team repositories
                repos = self.api_client.get_team_repositories(self.config.org_name, team_slug)
                repo_names = [repo["full_name"] for repo in repos] if repos else []

                return team_slug, member_usernames, repo_names
            except Exception as e:
                print(f"⚠️  Error fetching data for team {team_slug}: {e}")
                return team_slug, set(), []

        # Use threading to fetch team data in parallel
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_team = {executor.submit(fetch_team_data, team): team for team in teams_data}

            for i, future in enumerate(as_completed(future_to_team), 1):
                team_slug, members, repos = future.result()
                self.team_members_cache[team_slug] = members
                self.team_repos_cache[team_slug] = repos

                if i % 20 == 0:
                    print(f"  📊 Processed {i}/{len(teams_data)} teams")

        total_memberships = sum(len(members) for members in self.team_members_cache.values())
        total_repo_assignments = sum(len(repos) for repos in self.team_repos_cache.values())
        print(
            f"✅ Team cache built: {total_memberships} memberships, "
            f"{total_repo_assignments} repo assignments"
        )

    def get_user_details(self, username: str) -> Dict[str, Any]:
        """Get detailed user information"""
        try:
            response = self.api_client.get_user_org_membership(self.config.org_name, username)
            user_info = self.api_client.get_user_details(username)

            return {
                "role": response.get("role", "member") if response else "member",
                "email": user_info.get("email") if user_info else None,
            }
        except Exception:
            return {"role": "member", "email": None}

    def get_user_teams(self, username: str, teams_data: List[Dict[str, Any]]) -> List[TeamAccess]:
        """Get user's team memberships using cache"""
        user_teams = []

        for team in teams_data:
            team_slug = team["slug"]

            # Check if user is in this team
            if team_slug in self.team_members_cache:
                if username in self.team_members_cache[team_slug]:
                    # Get user's role in team
                    response = self.api_client.get_team_membership(
                        self.config.org_name, team_slug, username
                    )

                    if response:
                        team_access = TeamAccess(
                            name=team["name"],
                            slug=team["slug"],
                            description=team.get("description"),
                            privacy=team.get("privacy", "secret"),
                            role=response.get("role", "member"),
                            repositories=self.team_repos_cache.get(team_slug, []),
                        )
                        user_teams.append(team_access)

        return user_teams

    def process_user_batch(
        self,
        user_batch: List[Dict[str, Any]],
        teams_data: List[Dict[str, Any]],
        batch_num: int,
        total_batches: int,
    ) -> List[UserAccess]:
        """Process a batch of users"""
        print(f"🔄 Processing batch {batch_num}/{total_batches} ({len(user_batch)} users)")

        batch_results = []

        for i, member in enumerate(user_batch):
            username = member["login"]
            print(f"  Processing user {i+1:2d}/{len(user_batch)}: {username}")

            # Get user details
            user_details = self.get_user_details(username)

            # Get team memberships only
            teams = self.get_user_teams(username, teams_data)

            team_count = len(teams)
            if team_count > 0:
                print(f"    └─ {team_count} teams")

            user_access = UserAccess(
                username=username,
                user_id=member["id"],
                email=user_details.get("email"),
                role=user_details.get("role", "member"),
                teams=teams,
            )
            batch_results.append(user_access)

        print(f"✅ Batch {batch_num}/{total_batches} completed")
        return batch_results

    def backup_organization(self) -> OrganizationBackup:
        """Backup team memberships for the organization"""
        print(f"🚀 Starting TEAMS-ONLY backup for organization: {self.config.org_name}")
        print(f"📦 Batch size: {self.config.batch_size}, Max workers: {self.config.max_workers}")
        print("🎯 Focus: Team memberships (direct repo access preserved during SSO)")

        if self.config.limit_users:
            print(f"🧪 TEST MODE: Users limited to {self.config.limit_users}")

        print("=" * 60)

        backup = OrganizationBackup(
            org_name=self.config.org_name,
            backup_timestamp=datetime.now().isoformat(),
            backup_type="teams_only",
        )

        try:
            # Get organization data
            print(f"🔍 Fetching organization members for {self.config.org_name}...")
            members = self.api_client.get_organization_members(self.config.org_name)

            if self.config.limit_users:
                original_count = len(members)
                members = members[: self.config.limit_users]
                print(
                    f"🧪 Limited to first {len(members)} users for testing "
                    f"(original: {original_count})"
                )
            else:
                print(f"✅ Found {len(members)} members")

            print(f"👥 Fetching teams for {self.config.org_name}...")
            teams_data = self.api_client.get_organization_teams(self.config.org_name)
            print(f"✅ Found {len(teams_data)} teams")

            # Build team cache (much faster - no repo collaborators)
            print("\n🔧 Building team cache...")
            print("-" * 40)
            self.build_teams_cache(teams_data)

            print(f"\n👤 Processing {len(members)} users in batches of {self.config.batch_size}...")
            print("-" * 40)

            # Process users in batches
            total_batches = (len(members) + self.config.batch_size - 1) // self.config.batch_size

            for batch_num in range(total_batches):
                start_idx = batch_num * self.config.batch_size
                end_idx = min(start_idx + self.config.batch_size, len(members))
                user_batch = members[start_idx:end_idx]

                batch_results = self.process_user_batch(
                    user_batch, teams_data, batch_num + 1, total_batches
                )
                backup.users.extend(batch_results)

                processed = len(backup.users)
                print(
                    f"📊 Progress: {processed}/{len(members)} users processed "
                    f"({processed/len(members)*100:.1f}%)\n"
                )

            # Calculate summary
            backup.summary = {
                "total_users": len(backup.users),
                "total_teams": len(teams_data),
                "total_team_memberships": sum(len(user.teams) for user in backup.users),
                "users_with_teams": len([user for user in backup.users if user.teams]),
                "backup_type": "teams_only",
            }

            print("=" * 60)
            print("✅ Teams backup completed successfully!")
            self.print_summary(backup)

            return backup
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                print(f"\n❌ Organization '{self.config.org_name}' not found or not accessible")
            elif e.response is not None and e.response.status_code == 401:
                print("\n❌ Authentication failed - Invalid or expired GitHub token")
                print("\n❌ Please regenerate your token")
            elif e.response is not None and e.response.status_code == 403:
                print("\n❌ Access forbidden - Insufficient permissions")
                print("   • Update token at: https://github.com/settings/tokens")
            else:
                print(f"\n❌ HTTP Error {e.response.status_code if e.response else 'Unknown'}: {e}")
            raise
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            raise

    def print_summary(self, backup: OrganizationBackup):
        """Print backup summary"""
        print(f"\n📊 Teams Backup Summary for {backup.org_name}")
        print("-" * 40)
        print(f"Backup Type: {backup.backup_type}")
        print(f"Backup Time: {backup.backup_timestamp}")
        print(f"Total Users: {backup.summary['total_users']}")
        print(f"Total Teams: {backup.summary['total_teams']}")
        print(f"Total Team Memberships: {backup.summary['total_team_memberships']}")
        print(f"Users with Teams: {backup.summary['users_with_teams']}")
