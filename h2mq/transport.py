from .protocol import H2mqProtocol
from .utils import parse_endpoint


class H2mqTransport:
    def __init__(self, protocol: H2mqProtocol):
        self._protocol = protocol
        self._listeners = {}
        self._connectors = {}

    def bind(self, endpoint: str):
        proto, address = parse_endpoint(endpoint)
        listener = self._listeners[endpoint] = \
            self._protocol.listener_factory(proto)(self)
        listener.open(address)

    def unbind(self, endpoint: str):
        listener = self._listeners.pop(endpoint, None)
        if listener is not None:
            listener.close()

    async def connect(self, endpoint):
        pass

    async def disconnect(self, endpoint):
        pass

    async def send(self, frame):
        pass
