import abc
import asyncio

from h2.connection import H2Connection

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
        self._h2mq_transport.connection_made(h2_protocol)

    def connection_lost(self, h2_protocol):
        self._h2mq_transport.connection_lost(h2_protocol)

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

    def event_received(self, event):
        self._h2mq_transport.event_received(event)


class H2Protocol(asyncio.Protocol):
    def __init__(self, supervisor, client_side):
        self._supervisor = supervisor
        self._loop = supervisor.loop
        self._conn = H2Connection(client_side=client_side)
        self._transport = None
        self._last_active = 0

    def connection_made(self, transport: asyncio.Transport):
        self._transport = transport
        self._last_active = self._loop.time()
        self._conn.initiate_connection()
        self._transport.write(self._conn.data_to_send())
        self._supervisor.connection_made(self)

    def connection_lost(self, exc):
        self._conn.close_connection()
        self._supervisor.connection_lost(self)

    def data_received(self, data: bytes):
        self._last_active = self._loop.time()
        events = self._conn.receive_data(data)
        self._transport.write(self._conn.data_to_send())

        for event in events:
            self._supervisor.event_received(event)
            self._transport.write(self._conn.data_to_send())

    @property
    def h2_conn(self):
        return self._conn

    def new_stream(self, headers):
        return Stream(self, headers)
