from asyncio import Queue

from aiohttp import CIMultiDict
from h2.events import ResponseReceived, DataReceived, TrailersReceived, StreamEnded


class H2mqMessage:
    def __init__(self, *, stream_id=None, **kwargs):
        self._headers = CIMultiDict()
        self._parts = Queue()
        self._stream_id = stream_id
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def headers(self):
        return self._headers

    def get_ordered_headers(self):
        pseudos = []
        headers = []
        for k, v in self._headers.items():
            if k.startswith(':'):
                pseudos.append((k, v))
            else:
                headers.append((k, v))
        return pseudos + headers

    @property
    def stream_id(self):
        return self._stream_id


class H2mqRequest(H2mqMessage):
    PSEUDO_METHOD = ':method'
    PSEUDO_SCHEME = ':scheme'
    PSEUDO_PATH = ':path'
    PSEUDO_AUTHORITY = ':authority'

    response_factory = NotImplemented

    def __init__(self, **kwargs):
        kwargs.setdefault('method', 'GET')
        kwargs.setdefault('scheme', 'http')
        kwargs.setdefault('path', '/')
        super().__init__(**kwargs)
        self._response = None

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

    async def get_response(self):
        if self._response is None:
            self._response = self.response_factory(stream_id=self.stream_id)
        return self._response

    def _update_stream_id(self, stream_id):
        if self._response:
            self._response.stream_id = stream_id

    def __repr__(self):
        return 'H2mqRequest <{} {}>'.format(self.method, self.path)


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


class IncomingMixin:
    def feed_event(self, event):
        if isinstance(event, (ResponseReceived, TrailersReceived)):
            self.headers.update(event.headers)
        elif isinstance(event, DataReceived):
            self._parts.put_nowait(event.data)
        elif isinstance(event, StreamEnded):
            pass


class OutgoingMixin:
    pass


class IncomingResponse(H2mqResponse, IncomingMixin):
    pass


class OutgoingResponse(H2mqResponse, OutgoingMixin):
    pass


class IncomingRequest(H2mqRequest, IncomingMixin):
    response_factory = OutgoingResponse


class OutgoingRequest(H2mqRequest, OutgoingMixin):
    response_factory = IncomingResponse

    def __init__(self, socket, **kwargs):
        super().__init__(**kwargs)
        self._socket = socket

    async def _emit(self, *, end_stream=False):
        conn = await self._socket.next_connection()
        response = IncomingResponse()
        conn.start_request(self.headers, response, end_stream=end_stream)
        return response

    async def get_response(self):
        response = await self._emit(end_stream=True)

    async def get_stream(self):
        response = await self._emit()
