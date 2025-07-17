# PyMCP

PyMCP is a simple, tiny, and asynchronous server and client implementation for the Modern Context Protocol (MCP).

## Features

- **Simple Tool Definition**: Easily expose functions as remote tools using a simple `@tool` decorator.
- **Hot-Reloading**: Tools can be added, removed, or modified on the fly, and the server will hot-reload them without a restart.

## Quick Start

### Running the Server

1.  **Installation (from source)**:

    ```bash
    git clone <repository-url>
    cd pymcp
    pip install -r requirements.txt
    pip install -e .
    ```

2.  **Run the Server**:

    - run with default settings:

    ```bash
    pymcp
    ```

    - run with custom settings:

    ```bash
    pymcp --host 0.0.0.0 --port 9000 --tool-repo ./my_tools --log-level DEBUG
    ```

### Using the Client

```python
import asyncio
import pymcp

async def main():
    try:
        async with pymcp.Client("localhost", 8765) as client:
            # Ping the server
            pong = await client.call("ping")

            # Call the custom 'add' tool
            result = await client.call("add", a=5, b=7)
            print(f"5 + 7 = {result}")

            # Discover available tools
            tools = await client.call("list_tools_available")
            print("Available tools:", tools)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Configuration

- Arguments passed to start_server().
- Command-line arguments (e.g., --port).
- Environment variables (e.g., PYMCP_PORT=9000).
- Values in a .env file in your project's root.
- Default values in the Settings class.

all configuration options:

```sh
# .env
# Server network settings
# PYMCP_HOST=<your_host_address>
PYMCP_HOST=127.0.0.1

# PYMCP_PORT=<your_port_number>
PYMCP_PORT=8765

# List of paths to user-defined tool directories.
# Paths should be separated by commas.
# absolute or relative paths
# Example: /path/to/my_tools,/another/path/for_tools
PYMCP_USER_TOOL_REPOS=./my_custom_tools,../shared_tools,/home/user/tools

# Logging level
# Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL
PYMCP_LOG_LEVEL=INFO
```

---

### Server

#### request->response flow

```
client -> connection manager -> validator -> router -> tool executor -> return result -> client
```

#### create a tool

```python
import pymcp

@pymcp.tool
def add(a: int, b: int) -> int:
    """
    Add two integer numbers.
    argument a: First integer number.
    argument b: Second integer number.

    return: The sum of the two numbers.

    """
    return a + b

@pymcp.tool
def retrieve_data() -> str:
    """
    Retrieve user data from source

    no arguments is needed
    """
    return data
```

---

### Tool Repository discovery

The server discovers tools by scanning all `.py` files within the directories specified by the `--tool-repo` CLI argument or the `PYMCP_TOOL_REPOS` environment variable.

You can organize your tools into multiple files and directories. The loader will scan them recursively.

example directory structure:

```
my_tools/
├── __init__.py
├── math_tools.py
├── string_tools.py
└── data_tools/
    ├── __init__.py
    ├── user_data.py
    └── system_data.py
second_tools/
├── __init__.py
├── network_tools.py
└── file_tools.py
```

#### Hot-Reloading

The server watches the tool repositories for file changes. If you **add, modify, or delete a Python file** in a tool directory, the server will automatically perform a reload:

1.  It rebuilds the entire tool registry from scratch.
2.  It atomically swaps the old registry with the new one.

This allows you to update tool logic on a live server without a restart.

PyMCP supports a simple form of dependency injection. If a tool function's signature includes a parameter named `tool_registry`, the server will automatically provide the `ToolRegistry` instance to it at execution time.

---

### Client

#### Connect to the server

```python
import pymcp

async def main():
    async with pymcp.Client("localhost", 8765) as client:
        result = await client.call("ping")
        print(result)
```

#### request execute tools

```python
import pymcp
async def main():
    async with pymcp.Client("localhost", 8765) as client:
        result = await client.call("add", a=5, b=7)
        print(f"5 + 7 = {result}")

        tools = await client.call("list_tools_available")
        print("Available tools:", tools)
```

---

### Protocol

PyMCP uses a simple, JSON-based messaging protocol over a standard WebSocket connection.

- Client-to-Server: Requests

```json
{
  "header": {
    "correlation_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
  },
  "body": {
    "tool": "add",
    "args": {
      "a": 5,
      "b": 10
    }
  }
}
```

- Server-to-Client: Responses (Success)

```json
{
  "status": "success",
  "header": {
    "correlation_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
  },
  "body": {
    "tool": "add",
    "result": 15
  },
  "error": null
}
```

- Server-to-Client: Responses (Error)

```json
{
  "status": "error",
  "header": {
    "correlation_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
  },
  "body": null,
  "error": {
    "code": "execution_error",
    "message": "An unexpected error occurred while executing tool 'add'."
  }
}
```

---

## Design

PyMCP is designed to be simple, extensible, and easy to use. The server itself is just a WebSocket server that handles incoming requests, validates them, routes them to the appropriate tool executor, and returns the results.

No concept like "resources", "tools", or "prompts", since all of them are just a function that input something and return something. Everything is a tool. It leaves to user defining the scope of the tools.

The internal tools like `list_tools_available` and `ping`, are also some type of "tools". Tools and Server are decoupled. core tools are like extension of the server.
