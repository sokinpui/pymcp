# src/pymcp/lib.py
"""
Library interface for programmatically controlling the PyMCP server.
"""
import asyncio
import logging
from typing import List, Optional

from . import config
from .server.server import MCPServer
from .tools.loader import ToolLoader
from .tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ServerHandle:
    """
    A handle to a running MCP server instance, providing control over its lifecycle.
    This handle manages both the server task and the tool watcher task.
    """

    def __init__(self, server_task: asyncio.Task, watcher_task: asyncio.Task):
        self._server_task = server_task
        self._watcher_task = watcher_task
        self._tasks = [self._server_task, self._watcher_task]

    async def stop(self):
        """
        Requests a graceful shutdown of the server and the tool watcher.
        """
        logger.info("Shutdown requested via library handle.")
        for task in self._tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("Server and watcher have been stopped.")

    async def wait_closed(self):
        """
        Waits until the server and tool watcher tasks have completed.
        This is useful for running the server until it stops due to an
        internal error or external signal.
        """
        try:
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            # This can happen if the task group is cancelled from the outside.
            # Ensure a clean stop.
            await self.stop()


async def start_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    user_tool_repos: Optional[List[str]] = None,
) -> ServerHandle:
    """
    Starts the MCP server and tool watcher as a library call.

    This function sets up and runs the server in the background, returning
    a `ServerHandle` object to manage its lifecycle.

    Args:
        host: The network host to bind the server to. If None, uses the value
              from config/environment variables (defaults to 'localhost').
        port: The port to listen on. If None, uses the value from config/environment
              variables (defaults to 8765).
        user_tool_repos: A list of directory paths to search for user tools.
                         If provided, this list REPLACES any repos defined in
                         configuration (env/.env file). If None, repos from
                         configuration are used. The core tools repository is
                         always included.

    Returns:
        A `ServerHandle` instance for controlling the running server.
    """
    server_host = host if host is not None else config.settings.host
    server_port = port if port is not None else config.settings.port

    # If user_tool_repos is explicitly passed, it takes precedence over settings.
    # Otherwise, use the repos from the settings (env/.env file).
    repos_to_load = (
        user_tool_repos if user_tool_repos is not None else config.settings.tool_repos
    )

    # Use dict.fromkeys to remove duplicates while preserving order.
    tool_repo_paths = list(
        dict.fromkeys([str(config.CORE_TOOL_REPOS_PATH)] + repos_to_load)
    )

    tool_loader = ToolLoader(repo_paths=tool_repo_paths)
    initial_registry = tool_loader.load_registry()

    server = MCPServer(
        host=server_host,
        port=server_port,
        tool_registry=initial_registry,
    )

    async def on_registry_update(new_registry: ToolRegistry):
        server.update_tool_registry(new_registry)

    server_task = asyncio.create_task(server.start(), name="MCPServer_Lib")
    watcher_task = asyncio.create_task(
        tool_loader.watch(on_registry_update), name="ToolWatcher_Lib"
    )

    logger.info(
        "MCP Server and Tool Watcher started programmatically on ws://%s:%s",
        server_host,
        server_port,
    )

    return ServerHandle(server_task=server_task, watcher_task=watcher_task)
