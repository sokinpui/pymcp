# src/pymcp/config.py
"""
MCP Server Configuration Management.

This module uses pydantic-settings to provide a robust configuration system
that loads settings from environment variables and/or a .env file. This allows
users to configure the server without modifying the source code.

The hierarchy of configuration is:
1. Arguments passed directly to functions (e.g., `start_server(host=...)`).
2. Command-line arguments (e.g., `pymcp --host ...`).
3. Environment variables (e.g., `export PYMCP_HOST=...`).
4. Values in a `.env` file in the project's root directory.
5. Default values defined in the `Settings` class below.
"""
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Path to the directory containing built-in framework tools.
# This is an internal constant and not user-configurable.
CORE_TOOL_REPOS_PATH = Path(__file__).parent / "core_tools"


class Settings(BaseSettings):
    """
    Manages server configuration.
    Reads from environment variables (prefixed with 'PYMCP_') or a .env file.
    """

    model_config = SettingsConfigDict(
        env_prefix="PYMCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server network settings
    host: str = "localhost"
    port: int = 8765

    # List of paths to user-defined tool directories.
    # In .env or environment variable, this can be a comma-separated string:
    # PYMCP_USER_TOOL_REPOS="/path/to/tools1,/path/to/tools2"
    tool_repos: List[str] = []

    # Logging level
    log_level: str = "INFO"


# A single, importable instance of the settings.
settings = Settings()
