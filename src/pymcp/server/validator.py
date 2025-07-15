# src/pymcp/server/validator.py
"""
Component responsible for validating incoming client messages.
"""

import asyncio
from uuid import UUID

from pydantic import ValidationError

from pymcp.protocols.base_msg import Error
from pymcp.protocols.requests import ClientMessage
from pymcp.protocols.responses import ErrorResponse

from .commands import ResponseCommand


class Validator:
    """
    Parses and validates raw client messages against the MCP protocol.
    If validation fails, it sends an error response back to the client.
    """

    def __init__(self, response_queue: asyncio.Queue[ResponseCommand]):
        self.response_queue = response_queue

    async def validate_message(
        self, message_json: str, connection_id: UUID
    ) -> ClientMessage | None:
        """
        Parses and validates a raw client message from a WebSocket.

        Args:
            message_json: The raw JSON string received from the client.
            connection_id: The unique identifier for the client connection.

        Returns:
            A parsed `ClientMessage` object if validation is successful,
            otherwise `None`. If validation fails, an error response is
            automatically queued to be sent to the client.
        """
        try:
            # The `model_validate_json` on the Union type will dispatch
            # to the correct Pydantic model based on the 'type' field.
            message = ClientMessage.model_validate_json(message_json)
            return message
        except ValidationError as e:
            # For Pydantic validation errors, we cannot reliably extract a correlation_id
            # as the header itself might be invalid. We use a "null" UUID.
            error_response = ErrorResponse(
                header={
                    "correlation_id": "00000000-0000-0000-0000-000000000000",
                    "status": "error",
                },
                error=Error(code="validation_error", message=str(e)),
            )
            await self._queue_error_response(connection_id, error_response)
            return None
        except Exception as e:
            # Catch other potential parsing errors (e.g., invalid JSON).
            error_response = ErrorResponse(
                header={
                    "correlation_id": "00000000-0000-0000-0000-000000000000",
                    "status": "error",
                },
                error=Error(code="invalid_json", message=f"Could not parse message: {e}"),
            )
            await self._queue_error_response(connection_id, error_response)
            return None

    async def _queue_error_response(
        self, connection_id: UUID, error_response: ErrorResponse
    ):
        """Helper to create and queue a ResponseCommand for an error."""
        command = ResponseCommand(connection_id=connection_id, message=error_response)
        await self.response_queue.put(command)
