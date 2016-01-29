import asyncio
from asyncio.locks import Event
from collections import deque

from .protocol import H2mqProtocol
from .utils import parse_endpoint


class H2mqTransport:
    def __init__(self, protocol: H2mqProtocol, *, loop=None):
        self._protocol = protocol
        self._listeners = {}
        self._connectors = {}
        self._peers = deque()
        self._peers_not_empty = Event()
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop

    @property
    def loop(self):
        return self._loop

    @property
    def protocol(self):
        return self._protocol

    def connection_made(self, h2_protocol):
        self._peers.append(h2_protocol)
        self._peers_not_empty.set()
        self._loop.call_soon(self._protocol.connection_made, h2_protocol)

    def connection_lost(self, h2_protocol):
        self._peers.remove(h2_protocol)
        if not self._peers:
            self._peers_not_empty.clear()
        self._protocol.connection_lost(h2_protocol)

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

    async def borrow_stream(self, headers):
        await self._peers_not_empty.wait()
        peer = self._peers.popleft()
        self._peers.append(peer)
        return peer.borrow_stream(headers)
