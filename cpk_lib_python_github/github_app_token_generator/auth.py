# -*- coding: utf-8 -*-
"""GitHub App authentication utilities."""
import logging
import time
from typing import Optional

import jwt

logger = logging.getLogger(__name__)


class GitHubAppAuth:
    """Handle GitHub App authentication."""

    def __init__(self, app_id: int, private_key: str):
        self.app_id = str(app_id)
        self.private_key = private_key

    def generate_jwt(self) -> str:
        """Generate JWT token for GitHub App."""
        try:
            payload = {
                "iat": int(time.time()),
                "exp": int(time.time()) + (10 * 60),  # 10 minutes expiration
                "iss": self.app_id,
            }
            token = jwt.encode(payload, self.private_key, algorithm="RS256")
            logger.debug("Successfully generated JWT for app ID: %s", self.app_id)
            return token
        except Exception as error:
            logger.error("Failed to generate JWT: %s", error)
            raise ValueError(f"Failed to generate JWT: {error}") from error

    @staticmethod
    def read_private_key(private_key_path: str) -> str:
        """Read private key from file."""
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

    @staticmethod
    def get_private_key_content(
        private_key_path: Optional[str] = None,
        private_key_content: Optional[str] = None,
    ) -> str:
        """Get private key content from file or direct input."""
        if private_key_path and private_key_content:
            raise ValueError("Cannot specify both --private-key-path and --private-key")

        if not private_key_path and not private_key_content:
            raise ValueError("Must specify either --private-key-path or --private-key")

        if private_key_content:
            logger.debug("Using private key content provided directly")
            return private_key_content

        # If we reach here, private_key_path must be truthy
        logger.debug("Reading private key from file: %s", private_key_path)
        return GitHubAppAuth.read_private_key(private_key_path)
