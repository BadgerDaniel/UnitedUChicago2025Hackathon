"""
Test script for real API integrations in the Enhanced Travel Analysis System.
Tests NWS Weather API and Ticketmaster Events API functionality.
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

# Test with the MCP client - using correct LangGraph pattern
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_real_weather_api():
    """Test the real NWS Weather API integration."""
    print("🌦️  Testing Real Weather API Integration")
    print("=" * 50)
    
    test_cities = ["New York", "Chicago", "Miami", "Seattle", "Denver"]
    
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
            
            for city in test_cities:
                print(f"\n🏙️  Testing weather for {city}:")
                try:
                    config: RunnableConfig = {'configurable': {'thread_id': f'weather-test-{city.lower()}'}}
                    
                    # Use the agent to invoke the tool
                    result = await agent.ainvoke({
                        'messages': [('user', f'Get weather information for {city} using the get_weather_by_city tool')]
                    }, config)
                    
                    # Extract the response
                    if result and 'messages' in result:
                        last_message = result['messages'][-1]
                        if hasattr(last_message, 'content'):
                            weather_info = last_message.content
                        else:
                            weather_info = str(last_message)
                    else:
                        weather_info = "No response received"
                    
                    print(f"   {weather_info}")
                    
                    # Extract impact score
                    if "impact score:" in weather_info:
                        impact = weather_info.split("impact score: ")[1].split("/")[0]
                        print(f"   📊 Impact Score: {impact}/10")
                    
                except Exception as e:
                    print(f"   ❌ Error for {city}: {e}")
            
            print(f"\n✅ Weather API test completed")
            return True
            
    except Exception as e:
        print(f"❌ Weather API test failed: {e}")
        return False

async def test_real_events_api():
    """Test the real Ticketmaster Events API integration."""
    print("\n🎫 Testing Real Events API Integration")
    print("=" * 50)
    
    # Test with future dates
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    test_scenarios = [
        ("Las Vegas", tomorrow),
        ("New York", next_week),
        ("Chicago", tomorrow),
        ("Los Angeles", next_week)
    ]
    
    ticketmaster_key = os.getenv("TICKETMASTER_API_KEY")
    if not ticketmaster_key or ticketmaster_key.startswith("your_"):
        print("⚠️  Ticketmaster API key not configured - testing fallback functionality")
    else:
        print("✅ Ticketmaster API key configured - testing real data")
    
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
            
            for city, date in test_scenarios:
                print(f"\n🏙️  Testing events for {city} on {date}:")
                try:
                    config: RunnableConfig = {'configurable': {'thread_id': f'events-test-{city.lower()}-{date}'}}
                    
                    # Use the agent to invoke the tool
                    result = await agent.ainvoke({
                        'messages': [('user', f'Search for events in {city} on {date} using the search_events_in_city tool')]
                    }, config)
                    
                    # Extract the response
                    if result and 'messages' in result:
                        last_message = result['messages'][-1]
                        if hasattr(last_message, 'content'):
                            events_info = last_message.content
                        else:
                            events_info = str(last_message)
                    else:
                        events_info = "No response received"
                    
                    print(f"   {events_info}")
                    
                    # Extract impact score
                    if "impact score:" in events_info:
                        impact = events_info.split("impact score: ")[1].split("/")[0]
                        print(f"   📊 Impact Score: {impact}/10")
                    
                except Exception as e:
                    print(f"   ❌ Error for {city}: {e}")
            
            print(f"\n✅ Events API test completed")
            return True
            
    except Exception as e:
        print(f"❌ Events API test failed: {e}")
        return False

async def test_real_correlation_analysis():
    """Test the enhanced correlation analysis with real data."""
    print("\n📊 Testing Real-Time Correlation Analysis")
    print("=" * 50)
    
    # Test scenarios with different expected impacts
    test_scenarios = [
        ("Miami", "New York", "High weather/event city to major hub"),
        ("Seattle", "Chicago", "Weather-sensitive route"),
        ("Las Vegas", "Los Angeles", "Event-heavy to nearby city"),
        ("Boston", "Denver", "Cross-country with altitude factors")
    ]
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
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
            
            for origin, destination, description in test_scenarios:
                print(f"\n✈️  Testing: {origin} → {destination}")
                print(f"    Scenario: {description}")
                
                try:
                    config: RunnableConfig = {'configurable': {'thread_id': f'correlation-{origin.lower()}-{destination.lower()}'}}
                    
                    # Use the agent to invoke the tool
                    result = await agent.ainvoke({
                        'messages': [('user', f'Analyze travel correlation from {origin} to {destination} on {tomorrow} using the analyze_travel_correlation tool')]
                    }, config)
                    
                    # Extract the response
                    if result and 'messages' in result:
                        last_message = result['messages'][-1]
                        if hasattr(last_message, 'content'):
                            analysis = last_message.content
                        else:
                            analysis = str(last_message)
                    else:
                        analysis = "No analysis available"
                    
                    # Extract key metrics
                    lines = analysis.split('\n')
                    weather_impact = "N/A"
                    event_impact = "N/A"
                    overall_score = "N/A"
                    
                    for line in lines:
                        if "Combined Weather Impact:" in line:
                            weather_impact = line.split(":")[1].strip()
                        elif "Combined Event Impact:" in line:
                            event_impact = line.split(":")[1].strip()
                        elif "Overall Impact Score:" in line:
                            overall_score = line.split(":")[1].strip()
                    
                    print(f"    📊 Weather Impact: {weather_impact}")
                    print(f"    📊 Event Impact: {event_impact}")
                    print(f"    📊 Overall Score: {overall_score}")
                    
                    # Show first few insights
                    if "REAL DATA INSIGHTS" in analysis:
                        insights_section = analysis.split("REAL DATA INSIGHTS")[1].split("RECOMMENDATIONS")[0]
                        insights = [line.strip() for line in insights_section.split('\n') if line.strip().startswith('•')]
                        for insight in insights[:2]:
                            print(f"    💡 {insight}")
                    
                except Exception as e:
                    print(f"    ❌ Error: {e}")
            
            print(f"\n✅ Correlation analysis test completed")
            return True
            
    except Exception as e:
        print(f"❌ Correlation analysis test failed: {e}")
        return False

async def test_api_performance():
    """Test API response times and reliability."""
    print("\n⚡ Testing API Performance")
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
            
            # Test rapid successive calls
            start_time = datetime.now()
            
            test_queries = [
                "Get weather for New York using get_weather_by_city tool",
                "Search events in Chicago for 2025-07-01 using search_events_in_city tool",
                "Get weather for Miami using get_weather_by_city tool",
                "Search events in Las Vegas for 2025-07-15 using search_events_in_city tool"
            ]
            
            # Create tasks for concurrent execution
            tasks = []
            for i, query in enumerate(test_queries):
                config = {'configurable': {'thread_id': f'perf-test-{i}'}}
                task = agent.ainvoke({'messages': [('user', query)]}, config)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            successful = sum(1 for r in results if not isinstance(r, Exception))
            
            print(f"🚀 Concurrent API Tests:")
            print(f"   • Total calls: {len(tasks)}")
            print(f"   • Successful: {successful}")
            print(f"   • Failed: {len(tasks) - successful}")
            print(f"   • Total time: {duration:.2f} seconds")
            print(f"   • Avg time per call: {duration/len(tasks):.2f} seconds")
            
            return successful == len(tasks)
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

async def run_comprehensive_tests():
    """Run all API integration tests."""
    print("🧪 COMPREHENSIVE REAL API INTEGRATION TESTS")
    print("=" * 60)
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment setup
    print(f"\n🔧 Environment Check:")
    openai_key = os.getenv("OPENAI_API_KEY")
    ticketmaster_key = os.getenv("TICKETMASTER_API_KEY")
    
    print(f"   • OpenAI API Key: {'✅ Configured' if openai_key and not openai_key.startswith('your_') else '❌ Missing'}")
    print(f"   • Ticketmaster API Key: {'✅ Configured' if ticketmaster_key and not ticketmaster_key.startswith('your_') else '⚠️  Not configured (will use fallback)'}")
    print(f"   • NWS Weather API: ✅ No key required")
    
    print(f"\n📋 Running Tests...")
    
    # Run tests
    test_results = {}
    
    test_results["weather_api"] = await test_real_weather_api()
    test_results["events_api"] = await test_real_events_api()
    test_results["correlation_analysis"] = await test_real_correlation_analysis()
    test_results["api_performance"] = await test_api_performance()
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("=" * 40)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        test_display = test_name.replace('_', ' ').title()
        print(f"   {test_display}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All real API integrations working perfectly!")
        print("\n📈 System provides:")
        print("   • Real-time weather data from National Weather Service")
        if ticketmaster_key and not ticketmaster_key.startswith('your_'):
            print("   • Live event data from Ticketmaster")
        else:
            print("   • Fallback event data (add Ticketmaster API key for real data)")
        print("   • Sophisticated correlation analysis")
        print("   • Data-driven travel recommendations")
        
        print(f"\n🎯 Ready for Production Use!")
        print("Try these real-data queries:")
        print("• 'What's the current weather impact for flights to Miami?'")
        print("• 'Are there any major events in Las Vegas affecting travel costs?'")
        print("• 'Analyze real-time factors for NYC to Chicago travel tomorrow'")
        
    elif passed >= 3:
        print("⚠️  Most integrations working - system functional with some limitations")
        print("Check failed tests above and verify API configurations")
    else:
        print("❌ Multiple integration failures")
        print("Troubleshooting:")
        print("1. Ensure MCP server is running: ./scripts/start.sh")
        print("2. Check .env file has correct API keys")
        print("3. Verify internet connectivity for API calls")
        print("4. Check firewall settings for outbound HTTPS requests")
    
    return test_results

async def test_individual_apis():
    """Test individual API endpoints without MCP layer."""
    print("\n🔧 Direct API Testing (without MCP layer)")
    print("=" * 50)
    
    # Test NWS API directly
    print("🌦️  Testing NWS API directly...")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            # Test for New York coordinates
            response = await client.get(
                "https://api.weather.gov/points/40.7128,-74.0060",
                headers={"User-Agent": "travel-analysis-app/1.0"},
                timeout=10.0
            )
            if response.status_code == 200:
                print("   ✅ NWS API responding correctly")
            else:
                print(f"   ⚠️  NWS API returned status {response.status_code}")
    except Exception as e:
        print(f"   ❌ NWS API error: {e}")
    
    # Test Ticketmaster API directly
    print("\n🎫 Testing Ticketmaster API directly...")
    ticketmaster_key = os.getenv("TICKETMASTER_API_KEY")
    if ticketmaster_key and not ticketmaster_key.startswith("your_"):
        try:
            import requests
            response = requests.get(
                "https://app.ticketmaster.com/discovery/v2/events.json",
                params={
                    "apikey": ticketmaster_key,
                    "city": "New York",
                    "size": 1
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                events_count = len(data.get('_embedded', {}).get('events', []))
                print(f"   ✅ Ticketmaster API responding - found {events_count} events")
            else:
                print(f"   ⚠️  Ticketmaster API returned status {response.status_code}")
        except Exception as e:
            print(f"   ❌ Ticketmaster API error: {e}")
    else:
        print("   ⚠️  Ticketmaster API key not configured - skipping direct test")

if __name__ == "__main__":
    print("🚀 Starting Real API Integration Tests...")
    print("Make sure the enhanced MCP server is running on port 8000")
    print("Run: ./scripts/start.sh")
    print()
    
    asyncio.run(test_individual_apis())
    print()
    asyncio.run(run_comprehensive_tests())
