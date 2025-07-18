# src/pymcp/tools/registry.py
import asyncio
import inspect
import logging
from typing import Any, Callable, Dict, List, final

from pymcp.protocols.tools_def import ToolArgument, ToolDefinition

logger = logging.getLogger(__name__)


@final
class Tool:
    """
    A wrapper for a callable tool that can be either sync or async.
    It introspects the function signature to build its public definition.
    """

    # Define a constant for the special parameter name for dependency injection.
    # This makes the mechanism clear and avoids magic strings.
    INJECTED_REGISTRY_PARAM = "tool_registry"

    def __init__(self, name: str, func: Callable, description: str):
        self.name = name
        self.func = func
        self.description = description
        # Introspect arguments upon initialization.
        self.arguments = self._introspect_args(func)

    def _introspect_args(self, func: Callable) -> List[ToolArgument]:
        """
        Inspects a function's signature to build the list of public arguments.
        It explicitly ignores 'self' and the special dependency-injected
        'tool_registry' parameter.
        """
        sig = inspect.signature(func)
        args = []
        for param in sig.parameters.values():
            # Skip parameters that are not part of the public tool API.
            if param.name in ("self", self.INJECTED_REGISTRY_PARAM):
                continue

            # Determine type from annotation, defaulting to 'any'.
            param_type = (
                str(param.annotation.__name__)
                if hasattr(param.annotation, "__name__")
                else "any"
            )
            if param.annotation == inspect.Parameter.empty:
                param_type = "any"

            args.append(
                ToolArgument(
                    name=param.name,
                    type=param_type,
                    required=param.default is inspect.Parameter.empty,
                )
            )
        return args

    async def execute(self, **kwargs: Any) -> Any:
        """
        Executes the tool with the given keyword arguments.
        Runs synchronous functions in a separate thread to avoid blocking
        the asyncio event loop.
        """
        if inspect.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        else:
            # `asyncio.to_thread` is the modern way to run blocking IO-bound
            # or short-running CPU-bound code in an async application.
            return await asyncio.to_thread(self.func, **kwargs)

    def get_definition(self) -> ToolDefinition:
        """Returns the serializable definition of the tool."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            args=self.arguments,
        )


class ToolRegistry:
    """Manages the registration and lookup of available tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Registers a new tool."""
        if tool.name in self._tools:
            # Raise a more specific error for developers.
            raise ValueError(
                f"Tool name collision: A tool named '{tool.name}' is already registered."
            )
        logger.debug("Registering tool: %s", tool.name)
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool | None:
        """Retrieves a tool by its name."""
        return self._tools.get(name)

    def get_all_definitions(self) -> List[ToolDefinition]:
        """Returns a list of all tool definitions."""
        return sorted(
            [tool.get_definition() for tool in self._tools.values()],
            key=lambda t: t.name,
        )
