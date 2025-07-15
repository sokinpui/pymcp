import asyncio

from pymcp.server.server import MCPServer
from pymcp.tools.registry import ToolRegistry


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Start the MCP WebSocket server.")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    args = parser.parse_args()

    # In a real app, you would register your tools here.
    tool_registry = ToolRegistry()

    server = MCPServer(
        host=args.host,
        port=args.port,
        tool_registry=tool_registry,
    )

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("MCP Server stopped.")


if __name__ == "__main__":
    main()
