from aiohttp import ClientConnectorError
from interactions import Extension, Client, WebSocketClient
from interactions.ext.tasks import IntervalTrigger, create_task
import logging

class ReconnectExt(Extension):
    def __init__(self, client):
        self.client: Client = client
        self.check_disconnect.start(self)

    @create_task(IntervalTrigger(1))
    async def check_disconnect(self):
        logging.debug('Checking disconnect status...')
        if not self.client._websocket._WebSocketClient__started:
            logging.debug('Websocket not started yet')
            return

        if not self.client._websocket._closed:
            logging.debug('Still connected')
            return

        logging.warning("Disconnected, attempting reconnect...")
        await self.client._websocket.restart()

def setup(client):
    ReconnectExt(client)
