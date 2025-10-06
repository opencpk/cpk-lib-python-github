"""Test cases for backup.py"""

from unittest.mock import Mock, patch  # pylint: disable=import-error

import pytest  # pylint: disable=import-error

from cpk_lib_python_github.github_user_access_backup.backup import GitHubTeamsBackup
from cpk_lib_python_github.github_user_access_backup.config import BackupConfig
from cpk_lib_python_github.github_user_access_backup.models import (
    OrganizationBackup,
    TeamAccess,
    UserAccess,
)


@pytest.fixture
def mock_config():
    """Create a mock backup configuration"""
    return BackupConfig(
        token="test_token", org_name="test_org", batch_size=5, max_workers=2, limit_users=None
    )


@pytest.fixture
def backup_instance(mock_config):  # pylint: disable=redefined-outer-name
    """Create a GitHubTeamsBackup instance with mocked API client"""
    with patch("cpk_lib_python_github.github_user_access_backup.backup.GitHubAPIClient"):
        backup = GitHubTeamsBackup(mock_config)
        backup.api_client = Mock()
        return backup


@pytest.fixture
def sample_teams_data():
    """Sample teams data for testing"""
    return [
        {"slug": "team1", "name": "Team One", "description": "First team", "privacy": "closed"},
        {"slug": "team2", "name": "Team Two", "description": "Second team", "privacy": "secret"},
    ]


@pytest.fixture
def sample_members_data():
    """Sample members data for testing"""
    return [{"login": "user1", "id": 1}, {"login": "user2", "id": 2}, {"login": "user3", "id": 3}]


class TestGitHubTeamsBackupInit:  # pylint: disable=too-few-public-methods
    """Test GitHubTeamsBackup initialization"""

    def test_init_creates_api_client(self, mock_config):  # pylint: disable=redefined-outer-name
        """Test that initialization creates API client with correct config"""
        with patch(
            "cpk_lib_python_github.github_user_access_backup.backup.GitHubAPIClient"
        ) as mock_api:
            backup = GitHubTeamsBackup(mock_config)

            mock_api.assert_called_once_with(mock_config.token, mock_config.max_workers)
            assert backup.config == mock_config
            assert not backup.team_members_cache
            assert not backup.team_repos_cache


class TestBuildTeamsCache:  # pylint: disable=too-few-public-methods
    """Test build_teams_cache method"""

    def test_build_teams_cache_success(
        self, backup_instance, sample_teams_data
    ):  # pylint: disable=redefined-outer-name
        """Test successful team cache building"""
        # Mock API responses
        backup_instance.api_client.get_team_members.side_effect = [
            [{"login": "user1"}, {"login": "user2"}],  # team1 members
            [{"login": "user2"}, {"login": "user3"}],  # team2 members
        ]

        backup_instance.api_client.get_team_repositories.side_effect = [
            [{"full_name": "org/repo1"}],  # team1 repos
            [{"full_name": "org/repo2"}, {"full_name": "org/repo3"}],  # team2 repos
        ]

        backup_instance.build_teams_cache(sample_teams_data)

        # Verify cache is populated
        assert backup_instance.team_members_cache["team1"] == {"user1", "user2"}
        assert backup_instance.team_members_cache["team2"] == {"user2", "user3"}
        assert backup_instance.team_repos_cache["team1"] == ["org/repo1"]
        assert backup_instance.team_repos_cache["team2"] == ["org/repo2", "org/repo3"]

    def test_build_teams_cache_empty_responses(
        self, backup_instance, sample_teams_data
    ):  # pylint: disable=redefined-outer-name
        """Test team cache building with empty API responses"""
        backup_instance.api_client.get_team_members.return_value = None
        backup_instance.api_client.get_team_repositories.return_value = None

        backup_instance.build_teams_cache(sample_teams_data)

        # Verify empty responses are handled
        assert backup_instance.team_members_cache["team1"] == set()
        assert backup_instance.team_members_cache["team2"] == set()
        assert backup_instance.team_repos_cache["team1"] == []
        assert backup_instance.team_repos_cache["team2"] == []


class TestGetUserDetails:
    """Test get_user_details method"""

    def test_get_user_details_success(
        self, backup_instance
    ):  # pylint: disable=redefined-outer-name
        """Test successful user details retrieval"""
        backup_instance.api_client.get_user_org_membership.return_value = {"role": "admin"}
        backup_instance.api_client.get_user_details.return_value = {"email": "user@test.com"}

        result = backup_instance.get_user_details("testuser")

        assert result == {"role": "admin", "email": "user@test.com"}

    def test_get_user_details_no_membership(
        self, backup_instance
    ):  # pylint: disable=redefined-outer-name
        """Test user details when no org membership found"""
        backup_instance.api_client.get_user_org_membership.return_value = None
        backup_instance.api_client.get_user_details.return_value = {"email": "user@test.com"}

        result = backup_instance.get_user_details("testuser")

        assert result == {"role": "member", "email": "user@test.com"}

    def test_get_user_details_no_user_info(
        self, backup_instance
    ):  # pylint: disable=redefined-outer-name
        """Test user details when no user info found"""
        backup_instance.api_client.get_user_org_membership.return_value = {"role": "admin"}
        backup_instance.api_client.get_user_details.return_value = None

        result = backup_instance.get_user_details("testuser")

        assert result == {"role": "admin", "email": None}

    def test_get_user_details_api_exception(
        self, backup_instance
    ):  # pylint: disable=redefined-outer-name
        """Test user details with API exception"""
        backup_instance.api_client.get_user_org_membership.side_effect = Exception("API Error")

        result = backup_instance.get_user_details("testuser")

        assert result == {"role": "member", "email": None}


class TestGetUserTeams:
    """Test get_user_teams method"""

    def test_get_user_teams_success(
        self, backup_instance, sample_teams_data
    ):  # pylint: disable=redefined-outer-name
        """Test successful user teams retrieval"""
        # Set up cache
        backup_instance.team_members_cache = {
            "team1": {"user1", "user2"},
            "team2": {"user2", "user3"},
        }
        backup_instance.team_repos_cache = {"team1": ["org/repo1"], "team2": ["org/repo2"]}

        # Mock team membership API
        backup_instance.api_client.get_team_membership.side_effect = [
            {"role": "maintainer"},  # user2 in team1
            {"role": "member"},  # user2 in team2
        ]

        result = backup_instance.get_user_teams("user2", sample_teams_data)

        assert len(result) == 2
        assert result[0].name == "Team One"
        assert result[0].slug == "team1"
        assert result[0].role == "maintainer"
        assert result[0].repositories == ["org/repo1"]
        assert result[1].name == "Team Two"
        assert result[1].slug == "team2"
        assert result[1].role == "member"
        assert result[1].repositories == ["org/repo2"]

    def test_get_user_teams_not_in_any_team(
        self, backup_instance, sample_teams_data
    ):  # pylint: disable=redefined-outer-name
        """Test user not in any teams"""
        backup_instance.team_members_cache = {"team1": {"user1"}, "team2": {"user3"}}

        result = backup_instance.get_user_teams("user2", sample_teams_data)

        assert result == []

    def test_get_user_teams_membership_api_fails(
        self, backup_instance, sample_teams_data
    ):  # pylint: disable=redefined-outer-name
        """Test when team membership API fails"""
        backup_instance.team_members_cache = {"team1": {"user1"}}
        backup_instance.team_repos_cache = {"team1": ["org/repo1"]}
        backup_instance.api_client.get_team_membership.return_value = None

        result = backup_instance.get_user_teams("user1", sample_teams_data)

        assert result == []


class TestProcessUserBatch:  # pylint: disable=too-few-public-methods
    """Test process_user_batch method"""

    def test_process_user_batch_success(
        self, backup_instance, sample_teams_data
    ):  # pylint: disable=redefined-outer-name
        """Test successful user batch processing"""
        user_batch = [{"login": "user1", "id": 1}, {"login": "user2", "id": 2}]

        # Mock get_user_details
        backup_instance.get_user_details = Mock(
            side_effect=[
                {"role": "admin", "email": "user1@test.com"},
                {"role": "member", "email": "user2@test.com"},
            ]
        )

        # Mock get_user_teams
        team_access = TeamAccess(
            name="Team One",
            slug="team1",
            description="Test team",
            privacy="closed",
            role="member",
            repositories=["org/repo1"],
        )
        backup_instance.get_user_teams = Mock(
            side_effect=[[team_access], []]  # user1 teams  # user2 teams
        )

        result = backup_instance.process_user_batch(user_batch, sample_teams_data, 1, 1)

        assert len(result) == 2
        assert result[0].username == "user1"
        assert result[0].user_id == 1
        assert result[0].email == "user1@test.com"
        assert result[0].role == "admin"
        assert len(result[0].teams) == 1

        assert result[1].username == "user2"
        assert result[1].user_id == 2
        assert len(result[1].teams) == 0


class TestBackupOrganization:
    """Test backup_organization method"""

    def test_backup_organization_success(
        self, backup_instance, sample_members_data, sample_teams_data
    ):  # pylint: disable=redefined-outer-name
        """Test successful organization backup"""
        # Mock API calls
        backup_instance.api_client.get_organization_members.return_value = sample_members_data
        backup_instance.api_client.get_organization_teams.return_value = sample_teams_data

        # Mock build_teams_cache
        backup_instance.build_teams_cache = Mock()

        # Mock process_user_batch
        user_access = UserAccess(
            username="user1", user_id=1, email="user1@test.com", role="member", teams=[]
        )
        backup_instance.process_user_batch = Mock(return_value=[user_access])

        result = backup_instance.backup_organization()

        assert isinstance(result, OrganizationBackup)
        assert result.org_name == "test_org"
        assert result.backup_type == "teams_only"
        assert len(result.users) == 1
        assert result.summary["total_users"] == 1
        assert result.summary["total_teams"] == 2

    def test_backup_organization_with_limit_users(
        self, backup_instance, sample_members_data, sample_teams_data
    ):  # pylint: disable=redefined-outer-name
        """Test organization backup with user limit"""
        backup_instance.config.limit_users = 2

        backup_instance.api_client.get_organization_members.return_value = sample_members_data
        backup_instance.api_client.get_organization_teams.return_value = sample_teams_data
        backup_instance.build_teams_cache = Mock()
        backup_instance.process_user_batch = Mock(return_value=[])

        backup_instance.backup_organization()

        # Should only process first 2 users
        backup_instance.process_user_batch.assert_called()
        call_args = backup_instance.process_user_batch.call_args[0]
        assert len(call_args[0]) == 2  # user batch size

    def test_backup_organization_api_error(
        self, backup_instance
    ):  # pylint: disable=redefined-outer-name
        """Test organization backup with API error"""
        backup_instance.api_client.get_organization_members.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            backup_instance.backup_organization()

    def test_backup_organization_multiple_batches(
        self, backup_instance
    ):  # pylint: disable=redefined-outer-name
        """Test organization backup with multiple batches"""
        # Create enough members to require multiple batches
        large_members_list = [{"login": f"user{i}", "id": i} for i in range(12)]
        backup_instance.config.batch_size = 5

        backup_instance.api_client.get_organization_members.return_value = large_members_list
        backup_instance.api_client.get_organization_teams.return_value = []
        backup_instance.build_teams_cache = Mock()

        # Mock process_user_batch to return different results for each batch
        batch_results = [
            [UserAccess("user1", 1, None, "member", [])],
            [UserAccess("user6", 6, None, "member", [])],
            [UserAccess("user11", 11, None, "member", [])],
        ]
        backup_instance.process_user_batch = Mock(side_effect=batch_results)

        result = backup_instance.backup_organization()

        # Should call process_user_batch 3 times (12 users / 5 batch_size = 3 batches)
        assert backup_instance.process_user_batch.call_count == 3
        assert len(result.users) == 3


class TestPrintSummary:  # pylint: disable=too-few-public-methods
    """Test print_summary method"""

    def test_print_summary(self, backup_instance, capsys):  # pylint: disable=redefined-outer-name
        """Test print summary functionality"""
        backup = OrganizationBackup(
            org_name="test_org", backup_timestamp="2023-01-01T00:00:00", backup_type="teams_only"
        )
        backup.summary = {
            "total_users": 10,
            "total_teams": 5,
            "total_team_memberships": 15,
            "users_with_teams": 8,
            "backup_type": "teams_only",
        }

        backup_instance.print_summary(backup)

        captured = capsys.readouterr()
        assert "Teams Backup Summary for test_org" in captured.out
        assert "Total Users: 10" in captured.out
        assert "Total Teams: 5" in captured.out
        assert "Total Team Memberships: 15" in captured.out
        assert "Users with Teams: 8" in captured.out


class TestIntegration:  # pylint: disable=too-few-public-methods
    """Integration tests"""

    @patch("cpk_lib_python_github.github_user_access_backup.backup.GitHubAPIClient")
    def test_full_backup_workflow(
        self, mock_api_class, mock_config
    ):  # pylint: disable=redefined-outer-name
        """Test complete backup workflow integration"""
        # Set up mock API client
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # Mock API responses
        mock_api.get_organization_members.return_value = [
            {"login": "user1", "id": 1},
            {"login": "user2", "id": 2},
        ]

        mock_api.get_organization_teams.return_value = [
            {"slug": "team1", "name": "Team One", "description": "Test", "privacy": "closed"}
        ]

        mock_api.get_team_members.return_value = [{"login": "user1"}]
        mock_api.get_team_repositories.return_value = [{"full_name": "org/repo1"}]
        mock_api.get_user_org_membership.return_value = {"role": "member"}
        mock_api.get_user_details.return_value = {"email": "user@test.com"}
        mock_api.get_team_membership.return_value = {"role": "member"}

        # Create backup instance and run
        backup_instance = GitHubTeamsBackup(mock_config)
        result = backup_instance.backup_organization()

        # Verify results
        assert isinstance(result, OrganizationBackup)
        assert result.org_name == "test_org"
        assert len(result.users) >= 1
        assert result.summary["total_users"] >= 1


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_api_client_initialization_error(
        self, mock_config
    ):  # pylint: disable=redefined-outer-name
        """Test handling of API client initialization errors"""
        with patch(
            "cpk_lib_python_github.github_user_access_backup.backup.GitHubAPIClient"
        ) as mock_api:
            mock_api.side_effect = Exception("Failed to initialize API client")

            with pytest.raises(Exception, match="Failed to initialize API client"):
                GitHubTeamsBackup(mock_config)

    def test_concurrent_execution_error(
        self, backup_instance, sample_teams_data
    ):  # pylint: disable=redefined-outer-name
        """Test handling of concurrent execution errors"""
        # Mock ThreadPoolExecutor to raise exception
        with patch(
            "cpk_lib_python_github.github_user_access_backup.backup.ThreadPoolExecutor"
        ) as mock_executor:
            mock_executor.side_effect = Exception("Thread pool error")

            with pytest.raises(Exception, match="Thread pool error"):
                backup_instance.build_teams_cache(sample_teams_data)
