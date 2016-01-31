class Stream:
    def __init__(self, h2_protocol, headers=None, stream_id=None):
        self._h2_protocol = h2_protocol
        self._conn = h2_protocol.h2_conn
        if stream_id is None:
            stream_id = self._conn.get_next_available_stream_id()
        self._stream_id = stream_id
        if headers is not None:
            self.send_headers(headers)

    def send_headers(self, headers):
        self._conn.send_headers(self._stream_id, headers)
        self._h2_protocol.send_data_to_send()

    def send_data(self, data, end_stream=False):
        self._conn.send_data(self._stream_id, data, end_stream=end_stream)
        self._h2_protocol.send_data_to_send()
