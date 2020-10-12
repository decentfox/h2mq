import abc
import asyncio

from h2.connection import H2Connection
from h2.events import RequestReceived

from h2mq.message import IncomingRequest
from .stream import Stream


class Supervisor(metaclass=abc.ABCMeta):
    def __init__(self, h2mq_transport):
        self._h2mq_transport = h2mq_transport
        self._loop = h2mq_transport.loop
        self._impl = None
        self._opening = False

    @property
    def loop(self):
        return self._loop

    @property
    def h2mq_transport(self):
        return self._h2mq_transport

    async def open(self):
        if not self._opening:
            self._opening = True
            impl = await self._open()
            if self._opening:
                self._impl = impl
            else:
                self._close(impl)

    async def close(self):
        if self._opening:
            self._opening = False
            impl, self._impl = self._impl, None
            if impl:
                await self._close(impl)

    def connection_made(self, h2_protocol):
        self._h2mq_transport.add_protocol(h2_protocol)

    def connection_lost(self, h2_protocol):
        self._h2mq_transport.del_protocol(h2_protocol)

    @abc.abstractmethod
    async def _open(self):
        pass

    @abc.abstractmethod
    async def _close(self, impl):
        pass

    def _reopen(self, *args, **kwargs):
        if self._opening:
            self._loop.create_task(self._reopen_task(
                *args, **kwargs))._log_destroy_pending = False

    async def _reopen_task(self, *args, **kwargs):
        while self._opening:
            # noinspection PyBroadException
            try:
                await self.open()
                break
            except Exception:
                await asyncio.sleep(0.618)

    def feed_event(self, event):
        self._h2mq_transport.feed_event(event)

    def feed_request(self, request):
        self._h2mq_transport.feed_request(request)


class H2Protocol(asyncio.Protocol):
    def __init__(self, supervisor, client_side):
        self._supervisor = supervisor
        self._loop = supervisor.loop
        self._conn = H2Connection(client_side=client_side)
        self._transport = None
        self._last_active = 0
        self._protocols = {}

    def connection_made(self, transport: asyncio.Transport):
        self._transport = transport
        self._last_active = self._loop.time()
        self._conn.initiate_connection()
        self._supervisor.connection_made(self)
        self.send_data_to_send()

    def connection_lost(self, exc):
        self._conn.close_connection()
        self._supervisor.connection_lost(self)

    def data_received(self, data: bytes):
        self._last_active = self._loop.time()
        events = self._conn.receive_data(data)
        self.send_data_to_send()

        for event in events:
            stream_id = getattr(event, 'stream_id', None)
            protocol = self._protocols.get(stream_id)
            if protocol is None:
                if isinstance(event, RequestReceived):
                    protocol = IncomingRequest(stream_id=stream_id)
                    protocol.headers.update(event.headers)
                    self.register_incoming(stream_id, protocol)
                    self._supervisor.feed_request(protocol)
                else:
                    self._supervisor.feed_event(event)
                    self.send_data_to_send()
                    continue
            protocol.feed_event(event)
            self.send_data_to_send()

    @property
    def h2_conn(self):
        return self._conn

    def get_stream(self, headers=None, stream_id=None, end_stream=False):
        ret = Stream(self, headers=headers, stream_id=stream_id,
                     end_stream=end_stream)

        self._contexts.setdefault(ret.stream_id, {})

        to_delete = []

        for stream_id in self._contexts:
            if stream_id not in self._conn.streams:
                to_delete.append(stream_id)

        for stream_id in to_delete:
            self._contexts.pop(stream_id, None)

        return ret

    def start_request(self, headers, protocol, end_stream=False):
        stream_id = self._conn.get_next_available_stream_id()
        self._protocols[stream_id] = protocol
        self.send_headers(stream_id, headers, end_stream=end_stream)
        return stream_id

    def send_headers(self, stream_id, headers, end_stream=False):
        self._conn.send_headers(stream_id, headers, end_stream=end_stream)
        self.send_data_to_send()

    def send_data(self, stream_id, data, end_stream=False):
        self._conn.send_data(stream_id, data, end_stream=end_stream)
        self.send_data_to_send()

    def send_data_to_send(self):
        self._transport.write(self._conn.data_to_send())

    def get_context(self, stream_id):
        return self._contexts[stream_id]
