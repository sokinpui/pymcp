# mcp_server/sender.py

import asyncio

from .commands import ResponseCommand
from .connection_manager import ConnectionManager


class SenderWorker:
    """
    A worker that pulls response commands from a queue and sends
    them to the appropriate client using the ConnectionManager.
    """

    def __init__(
        self,
        worker_id: int,
        connection_manager: ConnectionManager,
        response_queue: asyncio.Queue[ResponseCommand],
    ):
        self.worker_id = worker_id
        self.connection_manager = connection_manager
        self.response_queue = response_queue

    async def start(self):
        """Starts the worker's main loop to process commands."""
        print(f"[Sender-{self.worker_id}] Started and waiting for responses to send.")
        while True:
            try:
                command = await self.response_queue.get()
                await self._process_command(command)
            except asyncio.CancelledError:
                print(f"[Sender-{self.worker_id}] Shutting down.")
                break
            except Exception as e:
                print(
                    f"[Sender-{self.worker_id}] CRITICAL ERROR: Unhandled exception: {e}"
                )

    async def _process_command(self, command: ResponseCommand):
        """Sends the message from the command to the specified client."""
        await self.connection_manager.send_message(
            connection_id=command.connection_id, message=command.message
        )
        self.response_queue.task_done()
