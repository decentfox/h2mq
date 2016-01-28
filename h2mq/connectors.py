from .h2_impl import H2Protocol, Supervisor


class StreamConnector(Supervisor):
    async def _close(self, transport):
        transport.close()

    def connection_lost(self, h2_protocol):
        super().connection_lost(h2_protocol)
        self._reopen()


class TcpConnector(StreamConnector):
    def __init__(self, h2mq_transport, address):
        super().__init__(h2mq_transport)
        self._host, self._port = address

    async def _open(self):
        return await self._loop.create_connection(
            lambda: H2Protocol(self, True), self._host, self._port)[1]


class UnixConnector(StreamConnector):
    def __init__(self, h2mq_transport, address):
        super().__init__(h2mq_transport)
        self._path = address

    async def _open(self):
        return await self._loop.create_unix_connection(
            lambda: H2Protocol(self, True), self._path)[1]
