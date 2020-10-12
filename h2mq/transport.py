import asyncio
from asyncio.locks import Event
from collections import deque

from .protocol import H2mqProtocol
from .utils import parse_endpoint


class H2mqTransport:
    def __init__(self, protocol: H2mqProtocol, *, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._protocol = protocol
        self._listeners = {}
        self._connectors = {}
        self._conns = deque()
        self._conns_not_empty = Event(loop=loop)
        self._requests = asyncio.Queue(loop=loop)

    @property
    def loop(self):
        return self._loop

    @property
    def protocol(self):
        return self._protocol

    def add_protocol(self, h2_protocol):
        self._conns.append(h2_protocol)
        self._conns_not_empty.set()
        self._loop.call_soon(self._protocol.connection_made, h2_protocol)

    def del_protocol(self, h2_protocol):
        try:
            self._conns.remove(h2_protocol)
        except ValueError:
            pass
        if not self._conns:
            self._conns_not_empty.clear()
        self._protocol.connection_lost(h2_protocol)

    def feed_event(self, event):
        self._protocol.event_received(event)

    def feed_request(self, request):
        self._requests.put_nowait(request)

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

    async def create_stream(self, headers, end_stream=False):
        await self._conns_not_empty.wait()
        conn = self._conns.popleft()
        self._conns.append(conn)
        # TODO: handle NoAvailableStreamIDError here
        return conn.get_stream(headers, end_stream=end_stream)

    async def next_connection(self):
        await self._conns_not_empty.wait()
        conn = self._conns.popleft()
        self._conns.append(conn)
        return conn

    async def recv_request(self):
        return await self._requests.get()
