class Stream:
    def __init__(self, h2_protocol, headers, stream_id=None):
        self._h2_protocol = h2_protocol
        self._headers = headers
        self._conn = h2_protocol.h2_conn
        if stream_id is None:
            stream_id = self._conn.get_next_available_stream_id()
        self._stream_id = stream_id
        self.send_headers(self._headers)

    def send_headers(self, headers):
        self._conn.send_headers(self._stream_id, headers)

    def send_data(self, data):
        self._conn.send_data(self._stream_id, data)
