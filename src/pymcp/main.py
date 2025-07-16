# src/pymcp/main.py
"""
Main entry point for the PyMCP application.
"""
import asyncio

from pymcp import config
from pymcp.server.server import MCPServer
from pymcp.tools.loader import ToolLoader
from pymcp.tools.registry import ToolRegistry


async def main():
    """Main entry point for starting the MCP server and services."""
    # 1. Initialize the Tool Loader from configuration
    tool_loader = ToolLoader(repo_paths=config.TOOL_REPOS)

    # 2. Perform the initial load of the tool registry
    initial_registry = tool_loader.load_registry()

    # 3. Initialize the MCP Server from configuration
    server = MCPServer(
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        tool_registry=initial_registry,
    )

    # 4. Define the callback for when tools are updated
    async def on_registry_update(new_registry: ToolRegistry):
        server.update_tool_registry(new_registry)

    # 5. Create and manage the main application tasks
    server_task = asyncio.create_task(server.start(), name="MCPServer")
    watcher_task = asyncio.create_task(
        tool_loader.watch(on_registry_update), name="ToolWatcher"
    )

    tasks = [server_task, watcher_task]
    print("MCP Server and Tool Watcher are running. Press Ctrl+C to stop.")

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        # This is the correct exception to catch when asyncio.run() cancels the task.
        print("\nShutdown requested by user.")
    finally:
        print("Cancelling main tasks...")
        for task in tasks:
            if not task.done():
                task.cancel()
        # Wait for all tasks to acknowledge cancellation and clean up
        await asyncio.gather(*tasks, return_exceptions=True)
        print("Application has shut down gracefully.")


def run():
    # To use the dynamic loader, you may need to: pip install watchdog
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # asyncio.run() propagates KeyboardInterrupt after its own cleanup.
        # We catch it here to prevent a traceback on normal Ctrl+C shutdown.
        # The graceful shutdown logic is handled within main().
        pass


if __name__ == "__main__":
    run()
