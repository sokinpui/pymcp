# src/pymcp/server/connection_manager.py
import asyncio
import logging
from typing import Dict
from uuid import UUID, uuid4

import websockets
from websockets.server import ServerConnection

from pymcp.protocols.responses import ServerMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[UUID, ServerConnection] = {}

    async def connect(self, websocket: ServerConnection) -> UUID:
        """Registers a new connection."""
        connection_id = uuid4()
        self.active_connections[connection_id] = websocket
        remote_addr = websocket.remote_address
        logger.info(
            "Connection %s accepted from %s:%s",
            connection_id,
            remote_addr[0],
            remote_addr[1],
        )
        return connection_id

    def disconnect(self, connection_id: UUID):
        """Removes a connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            # Logging is handled by the server handler for more context (clean vs. unclean shutdown)

    async def send_message(self, connection_id: UUID, message: ServerMessage):
        """Sends a JSON-serializable message to a specific client."""
        websocket = self.active_connections.get(connection_id)
        if websocket:
            try:
                await websocket.send(message.model_dump_json())
            except websockets.exceptions.ConnectionClosed:
                # Disconnect will be handled by the reading task in the main server handler
                pass

