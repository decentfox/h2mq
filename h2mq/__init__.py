from .protocol import H2mqProtocol
from .transport import H2mqTransport


def create_h2mq_connection(protocol_factory, loop=None):
    return H2mqTransport(protocol_factory(), loop=loop)
