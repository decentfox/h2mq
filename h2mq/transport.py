import asyncio

from .protocol import H2mqProtocol
from .utils import parse_endpoint


class H2mqTransport:
    def __init__(self, protocol: H2mqProtocol, *, loop=None):
        self._protocol = protocol
        self._listeners = {}
        self._connectors = {}
        self._peers = []
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop

    @property
    def loop(self):
        return self._loop

    @property
    def protocol(self):
        return self._protocol

    def connection_made(self, h2conn):
        self._peers.append(h2conn)
        self._loop.call_soon(self._protocol.connection_made, h2conn)

    def connection_lost(self, h2conn):
        self._peers.remove(h2conn)
        self._protocol.connection_lost(h2conn)

    def event_received(self, event):
        self._protocol.frame_received(event)

    async def bind(self, endpoint: str):
        proto, address = parse_endpoint(endpoint)
        listener = self._listeners[endpoint] = \
            self._protocol.listener_factory(proto)(self, address)
        await listener.open()

    async def unbind(self, endpoint: str):
        listener = self._listeners.pop(endpoint, None)
        if listener is not None:
            await listener.close()

    async def connect(self, endpoint):
        proto, address = parse_endpoint(endpoint)
        connector = self._connectors[endpoint] = \
            self._protocol.connector_factory(proto)(self, address)
        await connector.open()

    async def disconnect(self, endpoint):
        connector = self._connectors.pop(endpoint, None)
        if connector is not None:
            await connector.close()

    # async def send(self, frame):
    #     self._peers[0].
    #     pass
