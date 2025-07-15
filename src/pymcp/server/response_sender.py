# src/pymcp/server/response_sender.py
"""
Service responsible for sending responses to clients.
"""
from uuid import UUID

from pymcp.protocols.responses import ServerMessage

from .connection_manager import ConnectionManager


class ResponseSender:
    """
    A service that encapsulates the logic for sending messages
    to clients via the ConnectionManager.
    """

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    async def send(self, connection_id: UUID, message: ServerMessage):
        """
        Sends a message to a specific client.
        """
        await self.connection_manager.send_message(
            connection_id=connection_id, message=message
        )
