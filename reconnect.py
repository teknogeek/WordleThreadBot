from interactions import Extension, Client
from interactions.ext.tasks import IntervalTrigger, create_task
import logging
from threading import Lock

class ReconnectExt(Extension):
    def __init__(self, client):
        self.client: Client = client
        self.check_disconnect.start(self)
        self.lock = Lock()

    @create_task(IntervalTrigger(1))
    async def check_disconnect(self):
        logging.debug('Checking disconnect status...')
        if not self.client._websocket._WebSocketClient__started:
            logging.debug('Websocket not started yet')
            return

        if self.client._websocket._client is not None and not self.client._websocket._closed:
            logging.debug('Still connected')
            return

        if self.lock.acquire(blocking=False):
            logging.warning("Disconnected, attempting reconnect...")
            await self.client._websocket.restart()
            self.lock.release()

def setup(client):
    ReconnectExt(client)
