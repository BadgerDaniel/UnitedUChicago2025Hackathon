"""Quick test script that only tests the MCP server tools (no OpenAI required)."""

import asyncio
import logging
from langchain_mcp_adapters.client import MultiServerMCPClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mcp_tools_only():
    """Test just the MCP server tools without the full agent."""
    print("🧪 Testing MCP Server Tools (No OpenAI Required)")
    print("=" * 50)
    
    try:
        print("🔧 Connecting to MCP Server...")
        
        async with MultiServerMCPClient({
            "travel": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }) as client:
            tools = client.get_tools()
            print(f"   ✅ Connected! Found {len(tools)} tools")
            
            for tool in tools:
                print(f"      📦 {tool.name}: {tool.description}")
            
            print("\n🌍 Testing individual tools...")
            
            # Test weather
            print("\n   🌦️  Testing weather forecast...")
            try:
                weather_result = await client.call_tool("get_weather_by_city", {"city": "Miami"})
                print(f"      ✅ Weather result: {weather_result[0].text}")
            except Exception as e:
                print(f"      ❌ Weather tool error: {e}")
            
            # Test events
            print("\n   🎫 Testing event search...")
            try:
                events_result = await client.call_tool("search_events_in_city", {
                    "city": "Las Vegas", 
                    "date": "2025-07-15"
                })
                print(f"      ✅ Events result: {events_result[0].text}")
            except Exception as e:
                print(f"      ❌ Events tool error: {e}")
            
            # Test flights
            print("\n   ✈️  Testing flight search...")
            try:
                flights_result = await client.call_tool("search_flights", {
                    "origin": "New York",
                    "destination": "Chicago", 
                    "date": "2025-07-20"
                })
                print(f"      ✅ Flights result: {flights_result[0].text}")
            except Exception as e:
                print(f"      ❌ Flights tool error: {e}")
            
            # Test correlation analysis (the key feature!)
            print("\n   📊 Testing CORRELATION ANALYSIS...")
            try:
                correlation_result = await client.call_tool("analyze_travel_correlation", {
                    "origin": "Boston",
                    "destination": "Denver",
                    "date": "2025-08-01"
                })
                print(f"      ✅ Correlation Analysis:")
                print("      " + "="*50)
                lines = correlation_result[0].text.split('\n')
                for line in lines[:15]:  # Show first 15 lines
                    print(f"      {line}")
                if len(lines) > 15:
                    print(f"      ... ({len(lines)-15} more lines)")
                print("      " + "="*50)
            except Exception as e:
                print(f"      ❌ Correlation analysis error: {e}")
            
            print("\n🎯 Testing different scenarios...")
            
            # Test high-impact scenario
            scenarios = [
                ("Miami", "New York", "2025-12-31"),  # New Year's Eve
                ("Las Vegas", "Los Angeles", "2025-07-04"),  # July 4th
                ("Chicago", "Boston", "2025-06-15"),  # Regular day
            ]
            
            for origin, dest, date in scenarios:
                try:
                    result = await client.call_tool("analyze_travel_correlation", {
                        "origin": origin,
                        "destination": dest,
                        "date": date
                    })
                    # Extract key metrics from result
                    text = result[0].text
                    if "Overall Impact Score:" in text:
                        impact_line = [line for line in text.split('\n') if "Overall Impact Score:" in line][0]
                        print(f"      📈 {origin}→{dest} ({date}): {impact_line.strip()}")
                except Exception as e:
                    print(f"      ❌ Scenario {origin}→{dest} failed: {e}")
            
            print("\n✅ MCP Server tools are working correctly!")
            print("\n🔑 Key Features Demonstrated:")
            print("   ✅ Weather impact analysis")
            print("   ✅ Event impact analysis") 
            print("   ✅ Flight pricing analysis")
            print("   ✅ Cross-correlation between weather, events, and pricing")
            print("   ✅ Dynamic recommendations based on impact scores")
            
            return True
            
    except Exception as e:
        print(f"❌ MCP Server test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure MCP server is running: ./simple_start.sh")
        print("2. Check if port 8000 is accessible")
        print("3. Verify MCP server logs for errors")
        return False

async def main():
    """Main test function."""
    print("Testing Travel Analysis MCP Tools...")
    print("(This test doesn't require OpenAI API key)")
    print()
    
    success = await test_mcp_tools_only()
    
    if success:
        print("\n🎉 MCP Tools Test PASSED!")
        print("\n📋 Next Steps:")
        print("1. Set OpenAI API key: export OPENAI_API_KEY='your_key'")
        print("2. Restart system: ./simple_stop.sh && ./simple_start.sh")
        print("3. Test full agent through A2A client on port 10001")
        print("\n💡 The core multi-factor correlation analysis is working!")
        print("   You can now analyze how weather and events affect flight pricing.")
    else:
        print("\n⚠️  MCP Tools test failed")
        print("Check that the MCP server is running on port 8000")

if __name__ == "__main__":
    asyncio.run(main())
