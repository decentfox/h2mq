import asyncio
import uuid

from h2.events import RequestReceived, DataReceived

import h2mq


async def main():
    endpoint = 'ipc:///tmp/{}'.format(uuid.uuid4().hex)
    waiter = asyncio.Future()

    class MyProtocol(h2mq.H2mqProtocol):
        def frame_received(self, frame):
            if isinstance(frame, RequestReceived):
                print(frame.headers)
                if not waiter.done():
                    waiter.set_result(None)
            elif isinstance(frame, DataReceived):
                print(frame.data)

    server = h2mq.create_h2mq_connection(lambda: MyProtocol())
    await server.bind(endpoint)

    conn = h2mq.create_h2mq_connection(lambda: MyProtocol())
    await conn.connect(endpoint)

    async with await conn.borrow_stream({'A': 1}) as s1:
        async with await conn.borrow_stream({'B': 2}) as s2:
            s1.send_data(b'hello')
            s2.send_data(b'hello')
            s1.send_data(b'world')
            s2.send_data(b'world')

    await waiter

    await conn.disconnect(endpoint)
    await server.unbind(endpoint)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
