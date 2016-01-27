import asyncio

from .listener import TcpListener


class H2mqProtocol(asyncio.Protocol):
    def data_received(self, data):
        super().data_received(data)

    def eof_received(self):
        super().eof_received()

    def connection_made(self, transport):
        super().connection_made(transport)

    def pause_writing(self):
        super().pause_writing()

    def connection_lost(self, exc):
        super().connection_lost(exc)

    def resume_writing(self):
        super().resume_writing()

    def frame_received(self, frame):
        pass

    def listener_factory(self, proto):
        if proto == 'tcp':
            return TcpListener
