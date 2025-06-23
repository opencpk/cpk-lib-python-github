# -*- coding: utf-8 -*-
"""Configuration management for GitHub App Token Generator."""
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import toml

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration container for the application."""

    app_id: Optional[str] = None
    private_key_path: Optional[str] = None
    private_key_content: Optional[str] = None
    timeout: int = 30
    debug: bool = False

    @property
    def has_private_key(self) -> bool:
        """Check if private key is configured."""
        return bool(self.private_key_path or self.private_key_content)

    @property
    def has_required_config(self) -> bool:
        """Check if all required configuration is present."""
        return bool(self.app_id and self.has_private_key)


def requires_app_config(args) -> bool:
    """Check if the operation requires App ID and private key."""
    # Operations that work with tokens only
    token_only_operations = [
        args.validate_token,
        args.revoke_token,
    ]

    # If any token-only operation is specified, we don't need app config
    if any(token_only_operations):
        return False

    # All other operations require app config
    return True


def get_config_from_env(args) -> Config:
    """Get configuration from environment variables and command line arguments."""
    config = Config()

    # Check if this operation requires app configuration
    needs_app_config = requires_app_config(args)
    # Handle app_id with proper type conversion
    if args.app_id:
        config.app_id = args.app_id  # Already int from parser
    elif os.getenv("APP_ID"):
        try:
            config.app_id = int(os.getenv("APP_ID"))  # Convert env var to int
        except ValueError as exc:
            raise ValueError(f"Invalid APP_ID environment variable: {os.getenv('APP_ID')}") from exc

    if needs_app_config and not config.app_id:
        logger.error(
            "App ID is required for this operation. "
            "Set APP_ID environment variable or use --app-id"
        )
        raise ValueError(
            "App ID is required for this operation. "
            "Set APP_ID environment variable or use --app-id"
        )

    # Private key configuration
    config.private_key_path = args.private_key_path or os.getenv("PRIVATE_KEY_PATH")
    config.private_key_content = args.private_key or os.getenv("PRIVATE_KEY")

    if needs_app_config and not config.has_private_key:
        logger.debug(
            "Private key is required for this operation. "
            "Set PRIVATE_KEY or PRIVATE_KEY_PATH environment variable "
            "or use --private-key/--private-key-path"
        )
        raise ValueError(
            "Private key is required for this operation. "
            "Set PRIVATE_KEY or PRIVATE_KEY_PATH environment variable "
            "or use --private-key/--private-key-path"
        )

    # Optional configuration
    config.debug = args.debug if hasattr(args, "debug") else False
    config.timeout = int(os.getenv("TIMEOUT", "30"))

    logger.debug("Configuration loaded successfully")
    if config.app_id:
        logger.debug("App ID: %s", config.app_id)
        logger.debug(
            "Private key source: %s",
            "content" if config.private_key_content else "file",
        )
    else:
        logger.debug("Operating in token-only mode")
    logger.debug("Timeout: %s seconds", config.timeout)

    return config


def get_environment_info() -> Dict[str, Any]:
    """Get environment information for debugging."""
    return {
        "app_id_set": bool(os.getenv("APP_ID")),
        "private_key_path_set": bool(os.getenv("PRIVATE_KEY_PATH")),
        "private_key_content_set": bool(os.getenv("PRIVATE_KEY")),
        "timeout": os.getenv("TIMEOUT", "30"),
        "python_version": os.sys.version,
        "platform": os.sys.platform,
    }


def validate_environment() -> bool:
    """Validate that the environment has minimum required configuration."""
    try:
        app_id = os.getenv("APP_ID")
        private_key_path = os.getenv("PRIVATE_KEY_PATH")
        private_key_content = os.getenv("PRIVATE_KEY")

        if not app_id:
            logger.warning("APP_ID environment variable not set")
            return False

        if not (private_key_path or private_key_content):
            logger.warning("Neither PRIVATE_KEY_PATH nor PRIVATE_KEY environment variable set")
            return False

        # Validate app_id is a number
        try:
            int(app_id)
        except ValueError:
            logger.error("APP_ID must be a valid number, got: %s", app_id)
            return False

        # If private_key_path is set, check if file exists
        if private_key_path and not os.path.isfile(private_key_path):
            logger.error("Private key file not found: %s", private_key_path)
            return False

        logger.info("Environment validation successful")
        return True

    except Exception as error:
        logger.error("Environment validation failed: %s", error)
        return False


def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from a file (for future use)."""
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            config_data = toml.load(config_file)
            logger.info("Configuration loaded from file: %s", config_path)
            return config_data
    except FileNotFoundError:
        logger.warning("Configuration file not found: %s", config_path)
        return {}
    except Exception as error:
        logger.error("Error loading configuration file: %s", error)
        return {}
