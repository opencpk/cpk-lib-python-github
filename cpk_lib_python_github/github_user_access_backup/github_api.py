"""GitHub API client for team backup"""

import threading
import time
from typing import Any, Dict, List, Optional

import requests  # pylint: disable=import-error

from .config import DEFAULT_USER_AGENT, GITHUB_API_BASE_URL


class GitHubAPIClient:
    """GitHub API client with rate limiting and thread safety"""

    def __init__(self, token: str, max_workers: int = 5):
        self.token = token
        self.max_workers = max_workers

        self._thread_local = threading.local()
        self.rate_limit_lock = threading.Lock()

    def get_session(self):
        """Get thread-local session"""
        if not hasattr(self._thread_local, "session"):
            self._thread_local.session = requests.Session()
            self._thread_local.session.headers.update(
                {
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": DEFAULT_USER_AGENT,
                }
            )
        return self._thread_local.session

    def handle_rate_limit(self, response):
        """Handle GitHub API rate limiting"""
        if response.status_code == 403:
            remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            if remaining == 0:
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                current_time = int(time.time())
                sleep_time = max(0, reset_time - current_time + 60)

                with self.rate_limit_lock:
                    print(f"⏰ Rate limit hit. Sleeping for {sleep_time//60} minutes...")
                    time.sleep(sleep_time)
                return True
        return False

    def make_request(
        self, url: str, silent_404: bool = False, session=None
    ) -> Optional[Dict[str, Any]]:
        """Make a request to GitHub API with rate limiting"""
        if session is None:
            session = self.get_session()

        max_retries = 3
        for retry in range(max_retries):
            try:
                response = session.get(url)

                if self.handle_rate_limit(response):
                    continue

                if response.status_code == 404 and silent_404:
                    return None

                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404 and silent_404:
                    return None
                if retry == max_retries - 1:
                    raise
                time.sleep(2**retry)

            except requests.exceptions.RequestException:
                if retry == max_retries - 1:
                    raise
                time.sleep(2**retry)

        return None

    def paginated_request(
        self, url: str, per_page: int = 100, silent_404: bool = False
    ) -> List[Dict[str, Any]]:
        """Make paginated requests to GitHub API"""
        all_items = []
        page = 1

        while True:
            paginated_url = f"{url}?per_page={per_page}&page={page}"
            try:
                items = self.make_request(paginated_url, silent_404=silent_404)

                if not items:
                    break

                all_items.extend(items)

                if len(items) < per_page:
                    break

                page += 1
                if page % 5 == 0:
                    print(f"  📄 Fetched page {page-1}, total items so far: {len(all_items)}")

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404 and silent_404:
                    break
                raise

        return all_items

    def get_organization_members(self, org_name: str) -> List[Dict[str, Any]]:
        """Get all organization members"""
        url = f"{GITHUB_API_BASE_URL}/orgs/{org_name}/members"
        return self.paginated_request(url)

    def get_organization_teams(self, org_name: str) -> List[Dict[str, Any]]:
        """Get all organization teams"""
        url = f"{GITHUB_API_BASE_URL}/orgs/{org_name}/teams"
        return self.paginated_request(url)

    def get_team_members(self, org_name: str, team_slug: str) -> List[Dict[str, Any]]:
        """Get team members"""
        url = f"{GITHUB_API_BASE_URL}/orgs/{org_name}/teams/{team_slug}/members"
        return self.paginated_request(url, silent_404=True)

    def get_team_repositories(self, org_name: str, team_slug: str) -> List[Dict[str, Any]]:
        """Get team repositories"""
        url = f"{GITHUB_API_BASE_URL}/orgs/{org_name}/teams/{team_slug}/repos"
        return self.paginated_request(url, silent_404=True)

    def get_user_org_membership(self, org_name: str, username: str) -> Optional[Dict[str, Any]]:
        """Get user's organization membership details"""
        url = f"{GITHUB_API_BASE_URL}/orgs/{org_name}/memberships/{username}"
        return self.make_request(url, silent_404=True)

    def get_user_details(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user details"""
        url = f"{GITHUB_API_BASE_URL}/users/{username}"
        return self.make_request(url, silent_404=True)

    def get_team_membership(
        self, org_name: str, team_slug: str, username: str
    ) -> Optional[Dict[str, Any]]:
        """Get user's team membership details"""
        url = f"{GITHUB_API_BASE_URL}/orgs/{org_name}/teams/{team_slug}/memberships/{username}"
        return self.make_request(url, silent_404=True)
