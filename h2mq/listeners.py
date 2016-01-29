import os

from .h2_impl import H2Protocol, Supervisor


class StreamListener(Supervisor):
    async def _close(self, server):
        server.close()
        await server.wait_closed()

    async def _reopen_task(self, server):
        await server.wait_closed()
        await super()._reopen_task()


class TcpListener(StreamListener):
    def __init__(self, h2mq_transport, address):
        super().__init__(h2mq_transport)
        self._host, self._port = address

    async def _open(self):
        server = await self._loop.create_server(
            lambda: H2Protocol(self, False), self._host, self._port)
        self._reopen(server)
        return server


class UnixListener(StreamListener):
    def __init__(self, h2mq_transport, address):
        super().__init__(h2mq_transport)
        self._path = address

    async def _open(self):
        server = await self._loop.create_unix_server(
            lambda: H2Protocol(self, False), self._path)
        self._reopen(server)
        return server

    def __del__(self):
        os.remove(self._path)
