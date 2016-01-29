class Stream:
    def __init__(self, h2_protocol, headers):
        self._h2_protocol = h2_protocol
        self._conn = h2_protocol.h2_conn
        self._headers = headers

    async def __aenter__(self):
        self._stream_id = await self._h2_protocol.borrow_stream_id()
        self._conn.send_headers(self._stream_id, self._headers)
        self._headers = None
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._h2_protocol.return_stream_id(self._stream_id)
        self._h2_protocol = None
        self._conn = None
        self._stream_id = None

    def send_data(self, data):
        self._conn.send_data(self._stream_id, data)
