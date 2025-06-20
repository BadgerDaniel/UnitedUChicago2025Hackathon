import asyncio
import os

# --- MCP Configuration ---
HOST = '127.0.0.1'
PORT = 1234

async def send_mcp_message(writer, package, content):
    """Send an MCP message to the server."""
    message = f"#$#{package} {content}\n"
    writer.write(message.encode())
    await writer.drain()

async def receive_mcp_response(reader):
    """Receive and parse MCP response from server."""
    data = await reader.readline()
    if data:
        message = data.decode().strip()
        print(f"📨 Server → {message}")
        return message
    return None

async def test_trends_tools():
    """Test the new trends scraping tools."""
    reader, writer = await asyncio.open_connection(HOST, PORT)
    
    try:
        # 1. Get available locations
        print("\n🔍 Step 1: Getting available locations...")
        await send_mcp_message(writer, "get-available-locations", "")
        response = await receive_mcp_response(reader)
        
        if response and response.startswith("#$#available-locations"):
            print("✅ Available locations received!")
            
            # Parse the locations (simplified parsing)
            locations_data = response[3:].strip()  # Remove #$#
            print(f"📋 Locations: {locations_data}")
            
            # 2. Scrape trends for a specific location (Chicago as example)
            print("\n🔥 Step 2: Scraping trends for Chicago...")
            await send_mcp_message(writer, "scrape-trends", ":dma_code=602 :dma_name=\"Chicago (ORD)\"")
            
            # This might take a while, so we'll wait for the response
            print("⏳ Waiting for trends data...")
            trends_response = await receive_mcp_response(reader)
            
            if trends_response and trends_response.startswith("#$#trends-result"):
                if ":error=" in trends_response:
                    print("❌ Error occurred during scraping")
                else:
                    print("✅ Trends data received successfully!")
                    print(f"📊 Data: {trends_response}")
            else:
                print("❌ Unexpected response format")
        
        else:
            print("❌ Failed to get available locations")
    
    except Exception as e:
        print(f"❌ Error during test: {e}")
    
    finally:
        writer.close()
        await writer.wait_closed()

def main():
    print("🧪 Testing Trends Scraping Tools")
    print("Make sure the MCP server is running on localhost:1234")
    print("=" * 50)
    
    asyncio.run(test_trends_tools())

if __name__ == "__main__":
    main() 