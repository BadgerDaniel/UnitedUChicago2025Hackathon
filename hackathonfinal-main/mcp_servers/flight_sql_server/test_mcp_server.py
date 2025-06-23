#!/usr/bin/env python3
"""Test the MCP server functionality."""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Test the MCP server by connecting and calling tools."""
    
    # Server parameters
    server_params = StdioServerParameters(
        command="/Users/u404027/.local/bin/uv",
        args=[
            "--directory", "/Users/u404027/Desktop/multiagentmcp/mcp_servers/flight_sql_server",
            "run", 
            "python",
            "flight_sql_server_stdio.py"
        ],
        env={"GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", "")}
    )
    
    # Test the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            init_result = await session.initialize()
            
            print("1. Server initialized successfully!")
            if hasattr(init_result, 'server_info'):
                print(f"   Server: {init_result.server_info.name}")
                print(f"   Version: {init_result.server_info.version}")
            else:
                print("   Server info not available")
            
            # List available tools
            tools_result = await session.list_tools()
            print("\n2. Available tools:")
            if hasattr(tools_result, 'tools'):
                for tool in tools_result.tools:
                    print(f"   - {tool.name}: {tool.description}")
            else:
                print("   No tools found")
            
            # Test 1: Simple SQL question
            print("\n3. Testing analyze-flight-sql tool:")
            try:
                result = await session.call_tool(
                    "analyze-flight-sql",
                    {"question": "What cities are in the database?"}
                )
                if hasattr(result, 'content'):
                    print(f"   Result: {result.content[0].text if result.content else 'No content'}")
                else:
                    print(f"   Result: {result}")
            except Exception as e:
                print(f"   Error: {e}")
            
            # Test 2: Route prices
            print("\n4. Testing get-route-prices tool:")
            try:
                result = await session.call_tool(
                    "get-route-prices",
                    {
                        "origin_city": "los angeles",
                        "destination_city": "chicago"
                    }
                )
                if hasattr(result, 'content'):
                    text = result.content[0].text if result.content else 'No content'
                    print(f"   Result: {text[:200]}...")
                else:
                    print(f"   Result: {str(result)[:200]}...")
            except Exception as e:
                print(f"   Error: {e}")
            
            print("\n✅ MCP server is running!")

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(test_mcp_server())