# mcp_server.py

import asyncio

clients = []

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    clients.append(writer)
    print(f"🟢 Client connected: {addr}")

    while True:
        data = await reader.readline()
        if not data:
            break

        message = data.decode().strip()
        print(f"📨 {addr} → {message}")

        if message.startswith("#$#"):
            await handle_mcp(message, writer)
        else:
            for client in clients:
                if client != writer:
                    client.write(f"{addr}: {message}\n".encode())
                    await client.drain()

    print(f"🔴 Client disconnected: {addr}")
    clients.remove(writer)
    writer.close()

async def handle_mcp(message, writer):
    parts = message[3:].split(" ", 1)
    package = parts[0]
    params = parts[1] if len(parts) > 1 else ""

    if package == "oil-data":
        fields = {}
        for pair in params.strip().split(" :"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                fields[k.strip(":")] = v
        print(f"🛢️ Received oil data: {fields}")
    else:
        print(f"📦 MCP Package: {package} | Params: {params}")

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 1234)
    addr = server.sockets[0].getsockname()
    print(f"🌐 MCP Server running on {addr}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
