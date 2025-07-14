import asyncio

from pymcp.server.server import MCPServer
from pymcp.tools.registry import ToolRegistry


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Start the MCP WebSocket server.")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    args = parser.parse_args()

    # Initialize tool registry (this should be defined in your application)
    tool_registry = ToolRegistry()

    server = MCPServer(
        host=args.host,
        port=args.port,
        tool_registry=tool_registry,
        num_executors=2,
        num_senders=1,
    )
    asyncio.run(server.start())


if __name__ == "__main__":
    main()
