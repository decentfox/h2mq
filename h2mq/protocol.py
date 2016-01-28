from . import connectors
from . import listeners


class H2mqProtocol:
    def connection_made(self, h2conn):
        pass

    def connection_lost(self, h2conn):
        pass

    def pause_writing(self):
        pass

    def resume_writing(self):
        pass

    def frame_received(self, frame):
        pass

    @classmethod
    def listener_factory(cls, proto):
        if proto == 'tcp':
            return listeners.TcpListener
        elif proto == 'ipc':
            return listeners.UnixListener

    @classmethod
    def connector_factory(cls, proto):
        if proto == 'tcp':
            return connectors.TcpConnector
        elif proto == 'ipc':
            return connectors.UnixConnector
