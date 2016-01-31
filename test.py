import asyncio
import uuid

from h2.events import RequestReceived, DataReceived, ResponseReceived, \
    StreamEnded
from h2.exceptions import StreamClosedError

import h2mq


async def main():
    endpoint = 'ipc:///tmp/{}'.format(uuid.uuid4().hex)
    waiter = asyncio.Future()

    class MyProtocol(h2mq.H2mqProtocol):
        def __init__(self, label):
            self.label = label

        def event_received(self, frame, stream=None):
            print(frame)
            if isinstance(frame, RequestReceived):
                print(self.label, 'REQ', frame.stream_id, frame.headers)
            elif isinstance(frame, DataReceived):
                print(self.label, 'DATA', frame.stream_id, frame.data)
            elif isinstance(frame, StreamEnded):
                print(self.label, 'END', frame.stream_id)
                try:
                    stream.send_headers({':status': '200'})
                    stream.send_data(b'yes')
                    stream.send_data(b'sir', end_stream=True)
                except StreamClosedError:
                    if not waiter.done():
                        waiter.set_result(None)
            elif isinstance(frame, ResponseReceived):
                print(self.label, 'RESP', frame.stream_id, frame.headers)

    server = h2mq.create_h2mq_connection(lambda: MyProtocol('S'))
    await server.bind(endpoint)

    conn = h2mq.create_h2mq_connection(lambda: MyProtocol('C'))
    await conn.connect(endpoint)

    s2 = await server.create_stream({':method': 'get'})
    s2.send_data(b'2 hello')
    s2.send_data(b'2 world', end_stream=True)

    await waiter

    await conn.disconnect(endpoint)
    await server.unbind(endpoint)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
