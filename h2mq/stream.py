class Stream:
    def __init__(self, h2_protocol, headers=None, stream_id=None,
                 end_stream=False):
        self._h2_protocol = h2_protocol
        self._conn = h2_protocol.h2_conn
        if stream_id is None:
            stream_id = self._conn.get_next_available_stream_id()
        self._stream_id = stream_id
        if headers is not None:
            self.send_headers(headers, end_stream=end_stream)

    def send_headers(self, headers, end_stream=False):
        self._conn.send_headers(self._stream_id, headers,
                                end_stream=end_stream)
        self._h2_protocol.send_data_to_send()

    def send_data(self, data, end_stream=False):
        self._conn.send_data(self._stream_id, data, end_stream=end_stream)
        self._h2_protocol.send_data_to_send()

    def send_eof(self):
        self._conn.end_stream(self._stream_id)
        self._h2_protocol.send_data_to_send()

    @property
    def context(self):
        return self._h2_protocol.get_context(self._stream_id)

    @property
    def stream_id(self):
        return self._stream_id
