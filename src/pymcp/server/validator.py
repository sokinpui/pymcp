# src/pymcp/server/validator.py
"""
Component responsible for validating incoming client messages.
"""

from pydantic import ValidationError

from pymcp.protocols.base_msg import Error
from pymcp.protocols.requests import ClientMessage
from pymcp.protocols.responses import ErrorResponse


class Validator:
    """
    Parses and validates raw client messages against the MCP protocol.
    If validation fails, it returns an error response to be sent to the client.
    """

    def validate_message(
        self, message_json: str
    ) -> ClientMessage | ErrorResponse:
        """
        Parses and validates a raw client message from a WebSocket.

        Args:
            message_json: The raw JSON string received from the client.

        Returns:
            A parsed `ClientMessage` object if validation is successful,
            or an `ErrorResponse` if validation fails.
        """
        try:
            # The `model_validate_json` on the Union type will dispatch
            # to the correct Pydantic model based on the 'type' field.
            return ClientMessage.model_validate_json(message_json)
        except ValidationError as e:
            # For Pydantic validation errors, we cannot reliably extract a correlation_id
            # as the header itself might be invalid. We use a "null" UUID.
            return ErrorResponse(
                header={
                    "correlation_id": "00000000-0000-0000-0000-000000000000",
                    "status": "error",
                },
                error=Error(code="validation_error", message=str(e)),
            )
        except Exception as e:
            # Catch other potential parsing errors (e.g., invalid JSON).
            return ErrorResponse(
                header={
                    "correlation_id": "00000000-0000-0000-0000-000000000000",
                    "status": "error",
                },
                error=Error(code="invalid_json", message=f"Could not parse message: {e}"),
            )
