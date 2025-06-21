#!/usr/bin/env python3
"""
Quick test script to verify the MCP client fix.
Run this after starting the MCP server to test the basic functionality.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_basic_functionality():
    """Test basic MCP client functionality with the fixed approach."""
    print("🧪 Testing Basic MCP Client Functionality")
    print("=" * 50)
    
    try:
        async with MultiServerMCPClient({
            "travel": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }) as client:
            
            print("✅ Successfully connected to MCP server")
            
            # Get tools - not awaitable, returns list directly
            tools = client.get_tools()
            print(f"✅ Retrieved {len(tools)} tools from server")
            
            # List available tools
            print("\n📋 Available Tools:")
            for tool in tools:
                print(f"   • {tool.name}: {tool.description}")
            
            # Create agent
            model = ChatOpenAI(model="gpt-4o", temperature=0)
            memory = MemorySaver()
            agent = create_react_agent(model, tools, checkpointer=memory)
            print("✅ Created LangGraph agent with MCP tools")
            
            # Test a simple weather query
            print("\n🌦️  Testing Weather Query:")
            config: RunnableConfig = {'configurable': {'thread_id': 'test-session'}}
            
            result = await agent.ainvoke({
                'messages': [('user', 'Get weather information for New York using the get_weather_by_city tool')]
            }, config)
            
            if result and 'messages' in result:
                last_message = result['messages'][-1]
                if hasattr(last_message, 'content'):
                    response = last_message.content
                else:
                    response = str(last_message)
                
                print(f"✅ Weather query successful:")
                print(f"   Response: {response[:200]}...")
                
                if "impact score:" in response:
                    impact = response.split("impact score: ")[1].split("/")[0]
                    print(f"   📊 Impact Score: {impact}/10")
                
                return True
            else:
                print("❌ No response received")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Run the basic functionality test."""
    print("🚀 Quick Test for MCP Client Fix")
    print("Make sure the MCP server is running on port 8000")
    print("Run: ./scripts/start.sh")
    print()
    
    # Check environment
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key.startswith('your_'):
        print("❌ OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
        return
    
    print("✅ OpenAI API key configured")
    print()
    
    success = await test_basic_functionality()
    
    print()
    if success:
        print("🎉 Test PASSED! The MCP client fix is working correctly.")
        print("You can now run the full test suite: python tests/test_real_apis.py")
    else:
        print("❌ Test FAILED. Check the error messages above.")
        print("Troubleshooting steps:")
        print("1. Ensure MCP server is running: ./scripts/start.sh")
        print("2. Check that port 8000 is not blocked")
        print("3. Verify .env file has correct API keys")

if __name__ == "__main__":
    asyncio.run(main())
