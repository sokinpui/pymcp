```py
# response type
# ==============================================================
# list tool
server_to_client = {
    "header": {
        "id": "12345",
        "status": "success/error",
        "type": "list_tool"
    },
    "body": {
      "tools": [
        {
            "name": "tool_name",
            "description": "tool_description",
            "args_list": [
                {
                    "name": "arg1",
                    "type": "string",
                },
                {
                    "name": "arg2",
                    "type": "integer",
                }
            ]

        }
      ]

    },
    "error": {
        "code": "error_code",
        "message": "error_message"
    }
}

# tool call response
server_to_client = {
    "header": {
        "id": "12345",
        "status": "success/error",
        "type": "tool_call_response"
    },
    "body": {
        "tool_name": "tool_name",
        "result": "value",
    "error": {
        "code": "error_code",
        "message": "error_message"
    }
}



# ==============================================================

# request type
# ==============================================================
# request
client_to_server = {
    "header": {
        "id": "12345",
        "status": "success",
        "type": "request"
    },
    "body": {
        "request_type": "list_tool",
    }
}

# tool call
client_to_server = {
    "header": {
        "id": "12345",
        "status": "success/error",
        "type": "tool_call"
    },
    "body": {
        "tool_name": "tool_name",
        "args": {
            "arg1": "value1",
            "arg2": "value2"
        }
    }
}

# ==============================================================
```
