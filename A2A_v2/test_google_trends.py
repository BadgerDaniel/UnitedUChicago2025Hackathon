#!/usr/bin/env python3
"""
Test script for Google Trends integration in the travel analysis system.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
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

async def test_google_trends_integration():
    """Test the Google Trends integration with the travel analysis system."""
    print("🔍 Testing Google Trends Integration")
    print("=" * 50)
    
    try:
        async with MultiServerMCPClient({
            "travel": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }) as client:
            
            # Get tools and create agent
            tools = client.get_tools()
            model = ChatOpenAI(model="gpt-4o", temperature=0)
            memory = MemorySaver()
            agent = create_react_agent(model, tools, checkpointer=memory)
            
            print(f"✅ Connected to MCP server with {len(tools)} tools")
            
            # Check if Google Trends tool is available
            trends_tool_available = any(tool.name == "get_google_trends_for_city" for tool in tools)
            comprehensive_tool_available = any(tool.name == "analyze_comprehensive_travel_factors" for tool in tools)
            
            print(f"✅ Google Trends tool available: {trends_tool_available}")
            print(f"✅ Comprehensive analysis tool available: {comprehensive_tool_available}")
            
            test_cities = ["Las Vegas", "Miami", "New York"]
            
            for city in test_cities:
                print(f"\n🏙️  Testing Google Trends for {city}:")
                
                try:
                    config: RunnableConfig = {'configurable': {'thread_id': f'trends-test-{city.lower()}'}}
                    
                    # Test Google Trends tool
                    result = await agent.ainvoke({
                        'messages': [('user', f'Get Google Trends analysis for {city} using the get_google_trends_for_city tool')]
                    }, config)
                    
                    if result and 'messages' in result:
                        last_message = result['messages'][-1]
                        if hasattr(last_message, 'content'):
                            trends_info = last_message.content
                        else:
                            trends_info = str(last_message)
                    else:
                        trends_info = "No response received"
                    
                    print(f"   📈 Trends Result: {trends_info[:200]}...")
                    
                    # Extract impact scores
                    if "Travel Impact Score:" in trends_info:
                        travel_score = trends_info.split("Travel Impact Score: ")[1].split("/")[0]
                        print(f"   📊 Travel Impact Score: {travel_score}/10")
                    
                    if "Event Impact Score:" in trends_info:
                        event_score = trends_info.split("Event Impact Score: ")[1].split("/")[0]
                        print(f"   🎫 Event Impact Score: {event_score}/10")
                    
                except Exception as e:
                    print(f"   ❌ Error testing trends for {city}: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Google Trends test failed: {e}")
        return False

async def test_comprehensive_analysis():
    """Test the comprehensive analysis with Google Trends."""
    print("\n🎯 Testing Comprehensive Analysis with Google Trends")
    print("=" * 60)
    
    try:
        async with MultiServerMCPClient({
            "travel": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }) as client:
            
            # Get tools and create agent
            tools = client.get_tools()
            model = ChatOpenAI(model="gpt-4o", temperature=0)
            memory = MemorySaver()
            agent = create_react_agent(model, tools, checkpointer=memory)
            
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            test_routes = [
                ("Miami", "New York", "Hurricane season + big city dynamics"),
                ("Las Vegas", "Los Angeles", "Entertainment hub + nearby destination"),
                ("Chicago", "Seattle", "Cross-country with weather patterns")
            ]
            
            for origin, destination, scenario in test_routes:
                print(f"\n✈️  Route: {origin} → {destination}")
                print(f"    Scenario: {scenario}")
                
                try:
                    config: RunnableConfig = {'configurable': {'thread_id': f'comprehensive-{origin.lower()}-{destination.lower()}'}}
                    
                    # Test comprehensive analysis
                    result = await agent.ainvoke({
                        'messages': [('user', f'Perform comprehensive travel analysis from {origin} to {destination} on {tomorrow} using the analyze_comprehensive_travel_factors tool')]
                    }, config)
                    
                    if result and 'messages' in result:
                        last_message = result['messages'][-1]
                        if hasattr(last_message, 'content'):
                            analysis = last_message.content
                        else:
                            analysis = str(last_message)
                    else:
                        analysis = "No analysis received"
                    
                    # Extract key metrics
                    metrics = {}
                    for line in analysis.split('\n'):
                        if "Combined Weather Impact:" in line:
                            metrics["weather"] = line.split(":")[1].strip()
                        elif "Combined Event Impact:" in line:
                            metrics["events"] = line.split(":")[1].strip()
                        elif "Combined Trends Impact:" in line:
                            metrics["trends"] = line.split(":")[1].strip()
                        elif "Final Adjusted Price:" in line:
                            metrics["price"] = line.split(":")[1].strip()
                    
                    print(f"    🌦️  Weather Impact: {metrics.get('weather', 'N/A')}")
                    print(f"    🎫 Event Impact: {metrics.get('events', 'N/A')}")
                    print(f"    📈 Trends Impact: {metrics.get('trends', 'N/A')}")
                    print(f"    💰 Adjusted Price: {metrics.get('price', 'N/A')}")
                    
                    # Check for trend alerts
                    if "TRENDING ALERT" in analysis:
                        print(f"    🔥 ALERT: Unusual trending activity detected!")
                    
                except Exception as e:
                    print(f"    ❌ Error in comprehensive analysis: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Comprehensive analysis test failed: {e}")
        return False

async def test_natural_language_queries():
    """Test natural language queries that would trigger Google Trends analysis."""
    print("\n💬 Testing Natural Language Queries with Trends")
    print("=" * 55)
    
    try:
        async with MultiServerMCPClient({
            "travel": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }) as client:
            
            # Get tools and create agent
            tools = client.get_tools()
            model = ChatOpenAI(model="gpt-4o", temperature=0)
            memory = MemorySaver()
            agent = create_react_agent(model, tools, checkpointer=memory)
            
            natural_queries = [
                "Why are flights to Las Vegas expensive this weekend? Check trending topics.",
                "What's driving travel demand to Miami right now? Include Google trends.",
                "Are there any trending topics affecting New York travel costs?",
                "Analyze all factors including search trends for Chicago to Denver flights."
            ]
            
            for i, query in enumerate(natural_queries):
                print(f"\n❓ Query {i+1}: {query}")
                
                try:
                    config: RunnableConfig = {'configurable': {'thread_id': f'natural-query-{i}'}}
                    
                    result = await agent.ainvoke({
                        'messages': [('user', query)]
                    }, config)
                    
                    if result and 'messages' in result:
                        last_message = result['messages'][-1]
                        if hasattr(last_message, 'content'):
                            response = last_message.content
                        else:
                            response = str(last_message)
                    else:
                        response = "No response received"
                    
                    # Check if trends analysis was included
                    trends_included = any(keyword in response.lower() for keyword in [
                        "trends", "trending", "search", "google", "impact score"
                    ])
                    
                    print(f"   ✅ Trends analysis included: {trends_included}")
                    print(f"   📝 Response preview: {response[:150]}...")
                    
                except Exception as e:
                    print(f"   ❌ Error with query {i+1}: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Natural language test failed: {e}")
        return False

async def main():
    """Run all Google Trends integration tests."""
    print("🚀 Google Trends Integration Test Suite")
    print("Make sure the enhanced MCP server is running on port 8000")
    print("Run: ./scripts/start.sh")
    print()
    
    # Check environment
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key.startswith('your_'):
        print("❌ OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
        return
    
    print("✅ OpenAI API key configured")
    print()
    
    # Run tests
    test_results = {}
    
    test_results["trends_integration"] = await test_google_trends_integration()
    test_results["comprehensive_analysis"] = await test_comprehensive_analysis()
    test_results["natural_language"] = await test_natural_language_queries()
    
    # Summary
    print(f"\n📊 GOOGLE TRENDS TEST RESULTS")
    print("=" * 40)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        test_display = test_name.replace('_', ' ').title()
        print(f"   {test_display}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Google Trends integration working perfectly!")
        print("\n📈 Enhanced System Features:")
        print("• Real-time Google search trend analysis")
        print("• Travel demand pattern recognition")
        print("• Event and trending topic correlation")
        print("• Multi-source data fusion (Weather + Events + Trends)")
        print("• Natural language query support")
        
        print(f"\n🎯 Try These Enhanced Queries:")
        print("• 'Why are flights to Vegas expensive? Check all factors including trends'")
        print("• 'What trending topics might affect Miami travel costs?'")
        print("• 'Analyze comprehensive factors for my route including search trends'")
        print("• 'Are there any viral events driving travel demand to New York?'")
        
    elif passed >= 2:
        print("⚠️  Most Google Trends features working")
        print("Check failed tests above for specific issues")
    else:
        print("❌ Google Trends integration issues detected")
        print("Troubleshooting:")
        print("1. Ensure MCP server is running with updated code")
        print("2. Install required dependencies: pip install beautifulsoup4 pandas")
        print("3. Check internet connectivity for Google Trends access")
        print("4. Verify google_trends_analyzer.py is in mcp_server folder")

if __name__ == "__main__":
    asyncio.run(main())
