#!/usr/bin/env python3
"""
Diagnostic test script to identify exactly where the await error is occurring.
"""

import asyncio
import os
import sys
import traceback
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

async def diagnose_mcp_client():
    """Diagnostic test to identify the exact issue."""
    print("🔍 Diagnostic Test for MCP Client")
    print("=" * 50)
    
    try:
        print("Step 1: Creating MCP client...")
        client_config = {
            "travel": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }
        
        print("Step 2: Connecting to MCP server...")
        async with MultiServerMCPClient(client_config) as client:
            print("✅ Successfully connected to MCP server")
            
            print("Step 3: Getting tools...")
            try:
                # Try to get tools without await first
                tools = client.get_tools()
                print(f"✅ Retrieved {len(tools)} tools (sync)")
                print(f"   Tools type: {type(tools)}")
                
                # Check if tools is a list
                if isinstance(tools, list):
                    print("✅ Tools is a list as expected")
                    if tools:
                        print(f"   First tool: {tools[0].name if hasattr(tools[0], 'name') else 'Unknown'}")
                else:
                    print(f"⚠️  Tools is not a list: {type(tools)}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error getting tools: {e}")
                print("Full traceback:")
                traceback.print_exc()
                return False
            
            print("Step 4: Creating LLM model...")
            try:
                model = ChatOpenAI(model="gpt-4o", temperature=0)
                print("✅ Created ChatOpenAI model")
            except Exception as e:
                print(f"❌ Error creating model: {e}")
                return False
            
            print("Step 5: Creating memory...")
            try:
                memory = MemorySaver()
                print("✅ Created MemorySaver")
            except Exception as e:
                print(f"❌ Error creating memory: {e}")
                return False
            
            print("Step 6: Creating react agent...")
            try:
                agent = create_react_agent(model, tools, checkpointer=memory)
                print("✅ Created react agent")
            except Exception as e:
                print(f"❌ Error creating agent: {e}")
                print("Full traceback:")
                traceback.print_exc()
                return False
            
            print("Step 7: Testing simple agent invocation...")
            try:
                config: RunnableConfig = {'configurable': {'thread_id': 'diagnostic-test'}}
                
                result = await agent.ainvoke({
                    'messages': [('user', 'List the available tools')]
                }, config)
                
                print("✅ Agent invocation successful")
                return True
                
            except Exception as e:
                print(f"❌ Error in agent invocation: {e}")
                print("Full traceback:")
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

async def main():
    """Run diagnostic test."""
    print("🚀 MCP Client Diagnostic Test")
    print("Make sure the MCP server is running on port 8000")
    print()
    
    # Check environment
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key.startswith('your_'):
        print("❌ OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
        return
    
    print("✅ OpenAI API key configured")
    print()
    
    success = await diagnose_mcp_client()
    
    print()
    if success:
        print("🎉 Diagnostic PASSED! MCP client is working correctly.")
    else:
        print("❌ Diagnostic FAILED. Check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())
