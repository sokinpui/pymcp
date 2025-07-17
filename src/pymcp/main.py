# src/pymcp/main.py
"""
Main entry point and CLI for the PyMCP application.
"""
import argparse
import asyncio
import logging
from typing import List

from pymcp import config
from pymcp.logger import setup_logging
from pymcp.server.server import MCPServer
from pymcp.tools.loader import ToolLoader
from pymcp.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


async def main(host: str, port: int, tool_repos: List[str]):
    """
    Sets up and runs the MCP server and its related services.

    Args:
        host: The network host to bind the server to.
        port: The port to listen on.
        tool_repos: A list of directory paths to search for tools.
    """
    tool_loader = ToolLoader(repo_paths=tool_repos)
    initial_registry = tool_loader.load_registry()

    server = MCPServer(
        host=host,
        port=port,
        tool_registry=initial_registry,
    )

    async def on_registry_update(new_registry: ToolRegistry):
        server.update_tool_registry(new_registry)

    server_task = asyncio.create_task(server.start(), name="MCPServer_CLI")
    watcher_task = asyncio.create_task(
        tool_loader.watch(on_registry_update), name="ToolWatcher_CLI"
    )

    tasks = [server_task, watcher_task]
    logger.info(
        "MCP Server and Tool Watcher are running on ws://%s:%s. Press Ctrl+C to stop.",
        host,
        port,
    )

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Shutdown signal received. Gracefully stopping...")
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Application has shut down gracefully.")


def run_cli():
    """
    Parses command-line arguments and runs the main server function.
    """
    parser = argparse.ArgumentParser(description="PyMCP - Modern Context Protocol Server")
    parser.add_argument(
        "--host",
        type=str,
        default=config.settings.host,
        help=f"Server host. Env: PYMCP_HOST (default: {config.settings.host})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=config.settings.port,
        help=f"Server port. Env: PYMCP_PORT (default: {config.settings.port})",
    )
    parser.add_argument(
        "--tool-repo",
        action="append",
        dest="cli_tool_repos",
        default=[],
        help="Path to a user tool repository. Can be specified multiple times. "
        "Adds to repos from PYMCP_USER_TOOL_REPOS.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=config.settings.log_level,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=f"Set the logging level. Env: PYMCP_LOG_LEVEL (default: {config.settings.log_level})",
    )

    args = parser.parse_args()

    # Combine tool repositories: Core + Configured (env/file) + CLI.
    # config.settings.user_tool_repos has repos from .env or env vars.
    # args.cli_tool_repos has repos from the command line.
    all_user_repos = config.settings.user_tool_repos + args.cli_tool_repos

    # The final list always includes the core tools path first.
    # Use dict.fromkeys to remove duplicates while preserving order.
    final_tool_repos = list(
        dict.fromkeys([str(config.CORE_TOOL_REPOS_PATH)] + all_user_repos)
    )

    # Configure logging for the entire application. The CLI arg takes precedence.
    log_level_value = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level_value)

    try:
        asyncio.run(main(host=args.host, port=args.port, tool_repos=final_tool_repos))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_cli()
