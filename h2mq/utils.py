def parse_endpoint(endpoint: str) -> tuple:
    proto, addr = endpoint.split('://', 1)
    if proto == 'tcp':
        host, port = addr.split(':', 1)
        return proto, (host, port)
    elif proto == 'ipc':
        return proto, addr
