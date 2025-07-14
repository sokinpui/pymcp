import inspect
from typing import Any, Callable, Dict, List

from pymcp.protocols.tools_def import ToolArgument, ToolDefinition

# TODO: the tools registry should be a configurable file?


class Tool:
    """A wrapper for a callable tool."""

    def __init__(self, name: str, func: Callable, description: str):
        if not inspect.iscoroutinefunction(func):
            # NOTE: I think this should be handle by the executor, not here
            raise TypeError("Tool function must be an async function.")
        self.name = name
        self.func = func
        self.description = description
        self.arguments = self._introspect_args(func)

    def _introspect_args(self, func: Callable) -> List[ToolArgument]:
        """Inspects a function's signature to build ToolArgument list."""
        sig = inspect.signature(func)
        args = []
        for param in sig.parameters.values():
            if param.name == "self":
                continue

            # Basic type mapping; can be expanded
            param_type = (
                str(param.annotation)
                if param.annotation != inspect.Parameter.empty
                else "any"
            )

            args.append(
                ToolArgument(
                    name=param.name,
                    type=param_type,
                    required=param.default is inspect.Parameter.empty,
                )
            )
        return args

    async def execute(self, **kwargs: Any) -> Any:
        """Executes the tool with the given keyword arguments."""
        return await self.func(**kwargs)

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
            raise ValueError(f"Tool with name '{tool.name}' is already registered.")
        print(f"Registering tool: {tool.name}")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool | None:
        """Retrieves a tool by its name."""
        return self._tools.get(name)

    def get_all_definitions(self) -> List[ToolDefinition]:
        """Returns a list of all tool definitions."""
        return [tool.get_definition() for tool in self._tools.values()]
