# src/pymcp/tools/loader.py
"""
Service for discovering, loading, and hot-reloading tools.
"""
import asyncio
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Awaitable, Callable, Dict, List

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .decorators import TOOL_METADATA_ATTR
from .registry import Tool, ToolRegistry


class ToolChangeHandler(FileSystemEventHandler):
    """Handles file system events to trigger tool reloads with debouncing."""

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        reload_callback: Callable[[], Awaitable[None]],
    ):
        self._loop = loop
        self._reload_callback = reload_callback
        self._debounce_timer: asyncio.TimerHandle | None = None
        self._stopping = False  # Flag to prevent reloads during shutdown

    def on_any_event(self, event: FileSystemEvent):
        """
        Called by the watchdog observer thread.
        Schedules the debouncing logic to run on the main event loop.
        """
        if self._stopping or event.is_directory or not event.src_path.endswith(".py"):
            return

        print(f"Change detected in '{Path(event.src_path).name}'. Scheduling reload...")
        # Use call_soon_threadsafe to delegate to the event loop thread
        self._loop.call_soon_threadsafe(self._handle_debounce)

    def _handle_debounce(self):
        """
        This method is executed by the asyncio event loop and handles the
        debouncing logic safely.
        """
        # Cancel any previously scheduled reload
        if self._debounce_timer:
            self._debounce_timer.cancel()

        # Schedule the reload to happen after a short delay
        self._debounce_timer = self._loop.call_later(
            1.0,  # 1-second debounce window
            lambda: asyncio.create_task(self._reload_callback()),
        )

    def stop(self):
        """
        Prevents any further reload scheduling. This method is called from
        the main event loop thread during shutdown.
        """
        self._stopping = True
        if self._debounce_timer:
            # Since stop() is called from the loop, we can cancel directly.
            self._debounce_timer.cancel()


class ToolLoader:
    """
    Discovers, loads, and monitors tools from specified repository paths.
    """

    def __init__(self, repo_paths: List[str]):
        self._repo_paths = [Path(p).resolve() for p in repo_paths]
        self._loaded_module_paths: Dict[str, Path] = {}

    def load_registry(self) -> ToolRegistry:
        """
        Scans tool repositories, loads modules, and builds a new ToolRegistry.
        """
        print("Building new tool registry...")
        registry = ToolRegistry()
        self._invalidate_module_cache()

        for repo_path in self._repo_paths:
            if not repo_path.is_dir():
                print(f"Warning: Tool repository path not found: {repo_path}")
                continue

            for file_path in repo_path.glob("**/*.py"):
                self._load_tools_from_file(file_path, registry)

        print(
            f"Registry build complete. {len(registry.get_all_definitions())} tools loaded."
        )
        return registry

    def _invalidate_module_cache(self):
        """Removes previously loaded tool modules from sys.modules."""
        for module_name in list(self._loaded_module_paths.keys()):
            if module_name in sys.modules:
                del sys.modules[module_name]
        self._loaded_module_paths.clear()

    def _load_tools_from_file(self, file_path: Path, registry: ToolRegistry):
        """Loads a module from a file and registers any discovered tools."""
        try:
            # Create a unique module name to avoid collisions and allow reloading
            module_name = (
                f"mcp_dynamic_tools.{file_path.stem}_{file_path.stat().st_mtime_ns}"
            )
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                return

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module  # Required for inspect to work correctly
            spec.loader.exec_module(module)
            self._loaded_module_paths[module_name] = file_path

            for _, member in inspect.getmembers(module):
                if callable(member) and hasattr(member, TOOL_METADATA_ATTR):
                    meta = getattr(member, TOOL_METADATA_ATTR)
                    tool_instance = Tool(
                        name=meta["name"],
                        func=member,
                        description=meta["description"],
                    )
                    registry.register(tool_instance)
        except Exception as e:
            print(f"Error loading tools from {file_path}: {e}")

    async def watch(self, on_update: Callable[[ToolRegistry], Awaitable[None]]):
        """
        Starts watching the tool repositories for changes.

        Args:
            on_update: An async callback function to be invoked with the new
                       ToolRegistry when changes are detected.
        """
        loop = asyncio.get_running_loop()

        async def _reload_and_notify():
            print("Starting tool reload...")
            new_registry = self.load_registry()
            await on_update(new_registry)
            print("Tool reload complete. Server is using updated tools.")

        event_handler = ToolChangeHandler(loop, _reload_and_notify)
        observer = Observer()

        for path in self._repo_paths:
            if path.is_dir():
                observer.schedule(event_handler, str(path), recursive=True)
                print(f"Watching for tool changes in: {path}")

        observer.start()
        try:
            # Run the watcher thread until this task is cancelled
            await asyncio.Future()
        except asyncio.CancelledError:
            print("Stopping tool watcher...")
        finally:
            # Prevent new reloads and stop the observer thread
            event_handler.stop()
            observer.stop()
            # Run the blocking join() in an executor to avoid stalling the event loop
            await loop.run_in_executor(None, observer.join)
            print("Tool watcher stopped.")
