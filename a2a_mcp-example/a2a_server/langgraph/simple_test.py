"""Simple test script for the working travel analysis system."""

import asyncio
import logging
from langchain_mcp_adapters.client import MultiServerMCPClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_travel_system():
    """Test the travel analysis system."""
    print("🧪 Testing Travel Analysis System")
    print("=" * 40)
    
    try:
        print("🔧 Testing MCP Server connection...")
        
        async with MultiServerMCPClient({
            "travel": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }) as client:
            tools = client.get_tools()
            print(f"   ✅ Connected! Found {len(tools)} tools:")
            
            for tool in tools:
                print(f"      - {tool.name}: {tool.description}")
            
            # Test each tool
            print("\n🌍 Testing travel analysis tools...")
            
            # Test weather tool
            print("\n   🌦️  Testing weather analysis...")
            weather_result = await client.call_tool("get_weather_by_city", {"city": "Miami"})
            print(f"      Result: {weather_result[0].text[:100]}...")
            
            # Test events tool
            print("\n   🎫 Testing event search...")
            events_result = await client.call_tool("search_events_in_city", {
                "city": "Las Vegas", 
                "date": "2025-07-15"
            })
            print(f"      Result: {events_result[0].text[:100]}...")
            
            # Test flights tool
            print("\n   ✈️  Testing flight search...")
            flights_result = await client.call_tool("search_flights", {
                "origin": "New York",
                "destination": "Chicago", 
                "date": "2025-07-20"
            })
            print(f"      Result: {flights_result[0].text[:100]}...")
            
            # Test correlation analysis
            print("\n   📊 Testing correlation analysis...")
            correlation_result = await client.call_tool("analyze_travel_correlation", {
                "origin": "Boston",
                "destination": "Denver",
                "date": "2025-08-01"
            })
            print(f"      Analysis preview:")
            print(f"      {correlation_result[0].text[:200]}...")
            
            print("\n✅ All tools working correctly!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("Starting travel analysis system test...")
    print("Make sure the system is running: ./simple_start.sh")
    print()
    
    success = await test_travel_system()
    
    if success:
        print("\n🎉 System test passed!")
        print("\nYou can now:")
        print("1. Test queries through your A2A client on port 10001")
        print("2. Try example queries like:")
        print("   - 'Why are flights from NYC to Miami expensive?'")
        print("   - 'Analyze weather and events affecting Boston travel'")
        print("   - 'How do events in Las Vegas impact flight pricing?'")
    else:
        print("\n⚠️  System test failed")
        print("Check that services are running: ./simple_start.sh")

if __name__ == "__main__":
    asyncio.run(main())
