from aiohttp import Request

from .protocol import H2mqProtocol
from .transport import H2mqTransport


class H2mqRequest(Request):
    def __init__(self, conn, method, path):
        super().__init__(None, method, path)
        self.headers[':scheme'] = 'http'
        self._conn = conn
        self._stream = None

    @property
    def method(self):
        return self.headers[':method']

    # noinspection PyMethodOverriding
    @method.setter
    def method(self, val):
        self.headers[':method'] = val

    @property
    def path(self):
        return self.headers[':path']

    # noinspection PyMethodOverriding
    @path.setter
    def path(self, val):
        self.headers[':path'] = val

    async def send_headers(self, **kwargs):
        if self._stream is None:
            self._stream = self._conn.loop.create_task(
                    self._conn.create_stream(self.headers))
        else:
            stream = await self._stream
            stream.send_headers(self.headers)

    async def write(self, data, end_stream=False, **kwargs):
        if self._stream is None:
            self._stream = self._conn.loop.create_task(
                    self._conn.create_stream(self.headers))
        stream = await self._stream
        stream.send_data(data, end_stream=end_stream)

    async def write_eof(self):
        if self._stream is None:
            self._stream = self._conn.loop.create_task(
                    self._conn.create_stream(self.headers))
        stream = await self._stream
        stream.send_eof()


class H2mqConnection(H2mqTransport, H2mqProtocol):
    def __init__(self):
        super().__init__(self)

    def event_received(self, event, stream=None):
        pass

    def create_request(self, method, path):
        return H2mqRequest(self, method, path)

    async def send_request(self, method, path, *parts, headers=None):
        request = self.create_request(method, path)
        if headers:
            request.add_headers(headers)
        for part in parts[:-1]:
            await request.write(part)
        if parts:
            await request.write(parts[-1], end_stream=True)
        else:
            await request.write_eof()
        return request

    async def recv_request(self, request):
        pass
