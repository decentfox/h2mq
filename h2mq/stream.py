class Stream:
    def __init__(self, h2_protocol, headers):
        self._h2_protocol = h2_protocol
        self._conn = h2_protocol.h2_conn
        self._headers = headers

    async def __aenter__(self):
        self._stream_id = await self._h2_protocol.borrow_stream_id()
        self.send_headers(self._headers)
        del self._headers
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._h2_protocol.return_stream_id(self._stream_id)
        del self._h2_protocol
        del self._conn
        del self._stream_id

    def send_headers(self, headers):
        self._conn.send_headers(self._stream_id, headers)

    def send_data(self, data):
        self._conn.send_data(self._stream_id, data)
