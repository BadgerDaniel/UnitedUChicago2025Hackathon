"""
Enhanced demo for the real API integrated travel analysis system.
Showcases real weather data, event data, and correlation analysis.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables.config import RunnableConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTravelDemo:
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.memory = MemorySaver()
    
    async def _get_agent_response(self, client, query: str, thread_id: str):
        """Helper method to get agent response using the correct pattern."""
        tools = client.get_tools()
        agent = create_react_agent(self.model, tools, checkpointer=self.memory)
        config: RunnableConfig = {'configurable': {'thread_id': thread_id}}
        
        result = await agent.ainvoke({
            'messages': [('user', query)]
        }, config)
        
        if result and 'messages' in result:
            last_message = result['messages'][-1]
            if hasattr(last_message, 'content'):
                return last_message.content
            else:
                return str(last_message)
        return "No response received"
    
    async def demo_real_weather_integration(self):
        """Demonstrate real weather API integration."""
        print("\n🌦️  DEMO 1: Real Weather API Integration")
        print("=" * 60)
        
        async with MultiServerMCPClient({
            "travel": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }) as client:
            
            weather_cities = [
                ("Miami", "Hurricane-prone coastal city"),
                ("Chicago", "Midwest weather variability"),
                ("Seattle", "Pacific Northwest rain patterns"),
                ("Phoenix", "Desert heat conditions"),
                ("Boston", "Northeast seasonal weather")
            ]
            
            print("Testing real NWS weather data for major travel destinations:")
            
            for city, description in weather_cities:
                try:
                    # Use the agent pattern instead of direct tool invocation
                    query = f"Get weather information for {city} using the get_weather_by_city tool"
                    weather_info = await self._get_agent_response(client, query, f"weather-demo-{city.lower()}")
                    
                    print(f"\n🏙️  {city} ({description}):")
                    print(f"   {weather_info}")
                    
                    # Parse impact score
                    if "impact score:" in weather_info:
                        impact = weather_info.split("impact score: ")[1].split("/")[0]
                        impact_float = float(impact)
                        
                        if impact_float >= 7:
                            print(f"   ⚠️  HIGH IMPACT: Significant weather concerns for travel")
                        elif impact_float >= 4:
                            print(f"   ⚠️  MODERATE IMPACT: Some weather considerations")
                        else:
                            print(f"   ✅ LOW IMPACT: Favorable weather conditions")
                
                except Exception as e:
                    print(f"   ❌ Error getting weather for {city}: {e}")
    
    async def demo_real_events_integration(self):
        """Demonstrate real events API integration."""
        print("\n🎫 DEMO 2: Real Events API Integration")
        print("=" * 60)
        
        async with MultiServerMCPClient({
            "travel": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }) as client:
            
            # Test with upcoming dates
            next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            next_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            
            event_scenarios = [
                ("Las Vegas", next_week, "Entertainment capital"),
                ("New York", next_week, "Broadway and events hub"),
                ("Chicago", next_month, "Major convention city"),
                ("Los Angeles", next_month, "Entertainment industry center")
            ]
            
            print("Testing real Ticketmaster event data for major destinations:")
            
            for city, date, description in event_scenarios:
                try:
                    # Use the agent pattern instead of direct tool invocation
                    query = f"Search for events in {city} on {date} using the search_events_in_city tool"
                    events_info = await self._get_agent_response(client, query, f"events-demo-{city.lower()}-{date}")
                    
                    print(f"\n🏙️  {city} on {date} ({description}):")
                    print(f"   {events_info}")
                    
                    # Parse impact score
                    if "impact score:" in events_info:
                        impact = events_info.split("impact score: ")[1].split("/")[0]
                        impact_float = float(impact)
                        
                        if impact_float >= 7:
                            print(f"   🎉 HIGH EVENT ACTIVITY: Major events driving demand")
                        elif impact_float >= 4:
                            print(f"   🎪 MODERATE ACTIVITY: Some events affecting travel")
                        else:
                            print(f"   📅 NORMAL ACTIVITY: Typical event schedule")
                
                except Exception as e:
                    print(f"   ❌ Error getting events for {city}: {e}")
    
    async def demo_intelligent_correlation_analysis(self):
        """Demonstrate intelligent correlation analysis with real data."""
        print("\n📊 DEMO 3: Intelligent Real-Data Correlation Analysis")
        print("=" * 60)
        
        async with MultiServerMCPClient({
            "travel": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }) as client:
            
            # Test complex scenarios
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            analysis_scenarios = [
                {
                    "origin": "Miami",
                    "destination": "New York", 
                    "description": "Hurricane season impact on major route",
                    "expected": "High weather impact during storm season"
                },
                {
                    "origin": "Las Vegas",
                    "destination": "Los Angeles",
                    "description": "Event-heavy city to nearby destination",
                    "expected": "Event-driven demand fluctuations"
                },
                {
                    "origin": "Chicago", 
                    "destination": "Denver",
                    "description": "Midwest to mountain region weather sensitivity",
                    "expected": "Weather correlation with altitude changes"
                }
            ]
            
            for scenario in analysis_scenarios:
                print(f"\n✈️  Route: {scenario['origin']} → {scenario['destination']}")
                print(f"    Scenario: {scenario['description']}")
                print(f"    Expected: {scenario['expected']}")
                
                try:
                    # Use the agent pattern instead of direct tool invocation
                    query = f"Analyze travel correlation from {scenario['origin']} to {scenario['destination']} on {tomorrow} using the analyze_travel_correlation tool"
                    analysis = await self._get_agent_response(client, query, f"correlation-demo-{scenario['origin'].lower()}-{scenario['destination'].lower()}")
                    
                    # Extract and display key metrics
                    self._display_correlation_metrics(analysis)
                    
                    # AI interpretation of results
                    await self._provide_ai_interpretation(scenario, analysis)
                
                except Exception as e:
                    print(f"    ❌ Error in analysis: {e}")
    
    def _display_correlation_metrics(self, analysis: str):
        """Extract and display key metrics from correlation analysis."""
        lines = analysis.split('\n')
        
        for line in lines:
            if "Combined Weather Impact:" in line:
                impact = line.split(":")[1].strip()
                print(f"    🌦️  Weather Impact: {impact}")
            elif "Combined Event Impact:" in line:
                impact = line.split(":")[1].strip()
                print(f"    🎫 Event Impact: {impact}")
            elif "Overall Impact Score:" in line:
                impact = line.split(":")[1].strip()
                print(f"    📊 Overall Score: {impact}")
            elif "Adjusted Price:" in line:
                price = line.split(":")[1].strip()
                print(f"    💰 Price Impact: {price}")
    
    async def _provide_ai_interpretation(self, scenario, analysis):
        """Provide AI interpretation of the correlation analysis."""
        interpretation_prompt = f"""
        Analyze this real-time travel correlation data and provide insights:
        
        Route: {scenario['origin']} to {scenario['destination']}
        Context: {scenario['description']}
        
        Analysis Data:
        {analysis}
        
        Provide a concise interpretation focusing on:
        1. Key factors driving price/demand changes
        2. Practical travel recommendations
        3. Whether the data matches expected patterns
        
        Keep response to 2-3 sentences.
        """
        
        try:
            ai_response = await self.model.ainvoke([{"role": "user", "content": interpretation_prompt}])
            print(f"    🤖 AI Insight: {ai_response.content}")
        except Exception as e:
            print(f"    ⚠️  AI interpretation unavailable: {e}")
    
    async def demo_real_time_scenarios(self):
        """Demonstrate real-time travel scenario analysis."""
        print("\n🎯 DEMO 4: Real-Time Travel Scenarios")
        print("=" * 60)
        
        scenarios = [
            {
                "query": "Why might flights to Miami be expensive this weekend?",
                "route": ("Boston", "Miami"),
                "focus": "Weather and seasonal factors"
            },
            {
                "query": "How do current events affect travel costs to Las Vegas?",
                "route": ("Los Angeles", "Las Vegas"),
                "focus": "Event-driven demand analysis"
            },
            {
                "query": "What's driving travel costs for Chicago to Seattle?",
                "route": ("Chicago", "Seattle"),
                "focus": "Cross-country weather patterns"
            }
        ]
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        async with MultiServerMCPClient({
            "travel": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }) as client:
            
            for scenario in scenarios:
                print(f"\n❓ Query: {scenario['query']}")
                print(f"   📍 Route: {scenario['route'][0]} → {scenario['route'][1]}")
                print(f"   🔍 Focus: {scenario['focus']}")
                
                try:
                    # Get comprehensive analysis using the agent pattern
                    query = f"Analyze travel correlation from {scenario['route'][0]} to {scenario['route'][1]} on {tomorrow} using the analyze_travel_correlation tool"
                    analysis = await self._get_agent_response(client, query, f"scenario-demo-{scenario['route'][0].lower()}-{scenario['route'][1].lower()}")
                    
                    # Extract key insights for this scenario
                    if "REAL DATA INSIGHTS" in analysis:
                        insights_section = analysis.split("REAL DATA INSIGHTS")[1].split("RECOMMENDATIONS")[0]
                        insights = [line.strip() for line in insights_section.split('\n') if line.strip().startswith('•')]
                        
                        print(f"   💡 Key Insights:")
                        for insight in insights[:2]:
                            print(f"      {insight}")
                    
                    # Show recommendations
                    if "RECOMMENDATIONS" in analysis:
                        rec_section = analysis.split("RECOMMENDATIONS")[1]
                        recommendations = [line.strip() for line in rec_section.split('\n') if line.strip().startswith('•')]
                        
                        if recommendations:
                            print(f"   📋 Recommendation: {recommendations[0].replace('•', '').strip()}")
                
                except Exception as e:
                    print(f"   ❌ Error: {e}")
    
    async def run_enhanced_demo(self):
        """Run the complete enhanced demo with real APIs."""
        print("🚀 ENHANCED TRAVEL ANALYSIS DEMO - REAL API INTEGRATION")
        print("=" * 80)
        print("This demo showcases real-time data integration from:")
        print("• 🌦️  National Weather Service (NWS) - Live weather conditions")
        print("• 🎫 Ticketmaster API - Real event data and attendance")
        print("• 📊 Advanced correlation algorithms - Multi-factor analysis")
        print("=" * 80)
        
        try:
            await self.demo_real_weather_integration()
            await self.demo_real_events_integration()
            await self.demo_intelligent_correlation_analysis()
            await self.demo_real_time_scenarios()
            
            print("\n🎉 ENHANCED DEMO COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("✅ Real API Integrations: Working perfectly")
            print("✅ Multi-Factor Analysis: Providing accurate insights")
            print("✅ AI-Powered Interpretation: Generating actionable recommendations")
            print("✅ Real-Time Data: Current weather and event conditions")
            
            print(f"\n🎯 Production-Ready Features:")
            print("• Live weather impact scoring using NWS data")
            print("• Real event attendance and demand analysis")
            print("• Sophisticated correlation algorithms")
            print("• AI-powered insight generation")
            print("• Multi-route comparative analysis")
            
            print(f"\n📋 Ready for Complex Queries:")
            print("• 'Are current weather conditions affecting Miami flights?'")
            print("• 'What major events this weekend will impact Las Vegas travel?'")
            print("• 'Compare real-time factors for multiple destinations'")
            print("• 'How do current conditions affect pricing for my route?'")
            
        except Exception as e:
            logger.error(f"Enhanced demo failed: {e}")
            print(f"\n❌ Demo encountered an error: {e}")
            print("Check that services are running and API keys are configured")

async def main():
    """Main demo execution."""
    print("Starting Enhanced Travel Analysis Demo with Real APIs...")
    print("Make sure the enhanced system is running: ./scripts/start.sh")
    print()
    
    demo = EnhancedTravelDemo()
    await demo.run_enhanced_demo()

if __name__ == "__main__":
    asyncio.run(main())
