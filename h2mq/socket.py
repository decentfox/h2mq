import asyncio
from aiohttp import CIMultiDict
from h2.events import ResponseReceived, DataReceived, RequestReceived

from h2mq.message import OutgoingRequest
from .protocol import H2mqProtocol
from .transport import H2mqTransport


class H2mqMessage:
    def __init__(self, **kwargs):
        self._headers = CIMultiDict()
        self._parts = []
        for k, v in kwargs:
            setattr(self, k, v)

    @property
    def headers(self):
        return self._headers

    @classmethod
    def load(cls, headers):
        rv = cls()
        rv.headers.update(headers)
        return rv


class H2mqRequest(H2mqMessage):
    PSEUDO_METHOD = ':method'
    PSEUDO_SCHEME = ':scheme'
    PSEUDO_PATH = ':path'
    PSEUDO_AUTHORITY = ':authority'

    def __init__(self, **kwargs):
        kwargs.setdefault('method', 'GET')
        kwargs.setdefault('scheme', 'http')
        kwargs.setdefault('path', '/')
        super().__init__(**kwargs)
        self._response = H2mqResponse()

    @property
    def method(self):
        return self.headers[self.PSEUDO_METHOD]

    @method.setter
    def method(self, val):
        self.headers[self.PSEUDO_METHOD] = val

    @property
    def scheme(self):
        return self.headers[self.PSEUDO_SCHEME]

    @scheme.setter
    def scheme(self, val):
        self.headers[self.PSEUDO_SCHEME] = val

    @property
    def path(self):
        return self.headers[self.PSEUDO_PATH]

    @path.setter
    def path(self, val):
        self.headers[self.PSEUDO_PATH] = val

    @property
    def authority(self):
        return self.headers[self.PSEUDO_AUTHORITY]

    @authority.setter
    def authority(self, val):
        self.headers[self.PSEUDO_AUTHORITY] = val

    @authority.deleter
    def authority(self):
        del self.headers[self.PSEUDO_AUTHORITY]

    @property
    def response(self):
        return self._response


class H2mqResponse(H2mqMessage):
    PSEUDO_STATUS = ':status'

    def __init__(self, **kwargs):
        kwargs.setdefault('status', '404')
        super().__init__(**kwargs)

    @property
    def status(self):
        return self.headers[self.PSEUDO_STATUS]

    @status.setter
    def status(self, val):
        self.headers[self.PSEUDO_STATUS] = val


        # rv._conn = conn
        # self._stream = None
        # self._response = H2mqResponse()

    # async def get_stream(self):
    #     if self._stream is None:
    #         self._stream = self._conn.loop.create_task(
    #             self._conn.create_stream(self.headers))
    #     rv = await self._stream
    #     rv.context['request'] = self
    #     return rv
    #
    # async def send_headers(self, **kwargs):
    #     if self._stream is None:
    #         await self.get_stream()
    #     else:
    #         stream = await self.get_stream()
    #         stream.send_headers(self.headers)
    #
    # async def write(self, data, end_stream=False, **kwargs):
    #     stream = await self.get_stream()
    #     stream.send_data(data, end_stream=end_stream)
    #
    # async def write_eof(self):
    #     stream = await self.get_stream()
    #     stream.send_eof()
    #


class H2mqSocket(H2mqTransport, H2mqProtocol):
    def __init__(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        super().__init__(self, loop=loop)

    def event_received(self, event, stream=None):
        if stream:
            resp = stream.context['request'].response
            if isinstance(event, RequestReceived):
                pass
            elif isinstance(event, ResponseReceived):
                resp.headers.update(event.headers)
            elif isinstance(event, DataReceived):
                pass

    def new_request(self, method, path):
        return OutgoingRequest(self, method=method, path=path)

    async def request(self, method, path, *parts, headers=None):
        request = H2mqRequest(method=method, path=path)
        if headers:
            request.headers.update(headers)

        if parts:
            stream = await self.create_stream(request.headers)
            for part in parts[:-1]:
                await stream.send_data(part)
            await stream.send_data(parts[-1], end_stream=True)
        else:
            stream = await self.create_stream(request.headers, end_stream=True)
        return request

