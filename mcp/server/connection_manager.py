# server/connection_manager.py

import asyncio
from typing import Dict
from uuid import UUID, uuid4

import websockets

# TODO: this is legacy
from websockets.server import WebSocketServerProtocol

from protocols.responses import ServerMessage


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[UUID, WebSocketServerProtocol] = {}

    async def connect(self, websocket: WebSocketServerProtocol) -> UUID:
        """Registers a new connection."""
        await websocket.accept()
        connection_id = uuid4()
        self.active_connections[connection_id] = websocket
        print(f"New connection established: {connection_id}")
        return connection_id

    def disconnect(self, connection_id: UUID):
        """Removes a connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            print(f"Connection closed: {connection_id}")

    async def send_message(self, connection_id: UUID, message: ServerMessage):
        """Sends a JSON-serializable message to a specific client."""
        websocket = self.active_connections.get(connection_id)
        if websocket:
            try:
                await websocket.send(message.model_dump_json())
            except websockets.exceptions.ConnectionClosed:
                self.disconnect(connection_id)
