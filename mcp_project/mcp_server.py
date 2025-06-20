import asyncio
import sqlite3
import os

clients = []

oil_db_path = os.path.join(os.path.dirname(__file__), '..', 'MCP_ds', 'oil_prices.db')

def get_latest_oil_price(code):
    try:
        conn = sqlite3.connect(oil_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT price, created_at FROM oil_prices
            WHERE code = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (code,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0], row[1]
        else:
            return None, None
    except Exception as e:
        print(f"DB error: {e}")
        return None, None

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
    # Remove #$# prefix and split package from params
    parts = message[3:].strip().split(" ", 1)
    package = parts[0]
    params_str = parts[1] if len(parts) > 1 else ""

    if package in ["mcp", "mcp-auth"]:
        # Acknowledge control messages
        print(f"📦 MCP control message: {package} | {params_str}")

    elif package in ["oil-data", "trend-data"]:
        # Handle ":key=value" format, which is more complex
        fields = {}
        # A simple parsing logic for this specific format
        # It splits by space and then by '='
        pairs = params_str.strip().split(" ")
        for pair in pairs:
            if '=' in pair:
                # remove leading colon if it exists
                if pair.startswith(':'):
                    pair = pair[1:]
                key, value = pair.split('=', 1)
                # Remove quotes from value if they exist
                fields[key] = value.strip('"')

        if package == "oil-data":
            print(f"🛢️ OIL → {fields}")
        elif package == "trend-data":
            print(f"🔥 TREND → {fields}")

    elif package == "get-oil-price":
        # Parse params for code
        code = None
        pairs = params_str.strip().split(" ")
        for pair in pairs:
            if pair.startswith(":code="):
                code = pair.split("=", 1)[1]
        if code:
            price, timestamp = get_latest_oil_price(code)
            if price is not None:
                response = f"#$#oil-price-result :code={code} :price={price} :timestamp={timestamp}\n"
            else:
                response = f"#$#oil-price-result :code={code} :error=not_found\n"
            writer.write(response.encode())
            await writer.drain()
        else:
            response = f"#$#oil-price-result :error=missing_code\n"
            writer.write(response.encode())
            await writer.drain()
    else:
        print(f"❓ Unrecognized MCP package: {package} | Params: {params_str}")

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 1234)
    addr = server.sockets[0].getsockname()
    print(f"🌐 MCP Server running on {addr}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main()) 