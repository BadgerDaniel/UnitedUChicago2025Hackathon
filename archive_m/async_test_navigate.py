import asyncio

async def test_navigate_tool():
    """Connects to the MCP server and calls the navigate tool."""
    host = '127.0.0.1'
    port = 1234
    
    print(f"Connecting to MCP server at {host}:{port}...")
    
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print("Connection successful.")
        
        # This is a guess based on the other client's message format.
        # It's not clear what the exact message format for calling a tool is.
        # The other client sends data, but doesn't call a tool in the same way.
        # I will construct a plausible message.
        # Based on the other client, messages are newline-terminated.
        
        tool_to_call = "navigate"
        url_to_visit = "https://news.google.com"
        
        # This is a guess at the message format.
        message = f'#$#{tool_to_call} :url="{url_to_visit}"\n'
        
        print(f"Sending message: {message.strip()}")
        writer.write(message.encode())
        await writer.drain()
        
        # Wait for a response
        try:
            response = await asyncio.wait_for(reader.read(1024), timeout=10.0)
            print(f"Received response: {response.decode().strip()}")
        except asyncio.TimeoutError:
            print("Timed out waiting for a response from the server.")
            
        writer.close()
        await writer.wait_closed()
        
    except ConnectionRefusedError:
        print("Connection refused. Is the server running?")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_navigate_tool()) 