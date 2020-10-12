import asyncio
import uuid

import h2mq

endpoint = 'ipc:///tmp/{}'.format(uuid.uuid4().hex)
loop = asyncio.get_event_loop()


async def server(socket):
    while True:
        req = await socket.recv_request()
        print(req)
        req.response.status = '200'
        await req.response.emit()


async def main():
    serv = h2mq.H2mqSocket()
    conn = h2mq.H2mqSocket()

    await serv.bind(endpoint)
    await conn.connect(endpoint)

    loop.create_task(server(serv))

    req = conn.new_request('POST', '/index.html')
    await req.emit()
    await req.response.

    await conn.disconnect(endpoint)


if __name__ == '__main__':
    loop.run_until_complete(main())
