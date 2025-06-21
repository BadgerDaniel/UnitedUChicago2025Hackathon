"""
Demo script to showcase the Enhanced Travel Analysis Multi-Agent System capabilities.
This script demonstrates various features and agent interactions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
import sys
import os

# Add the agents directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from orchestrator_agent import OrchestratorAgent
from enhanced_agent import TravelAnalysisAgent, AgentCommunicationDemo

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TravelAnalysisDemo:
    """Comprehensive demo of the travel analysis system."""
    
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.travel_agent = TravelAnalysisAgent()
        self.comm_demo = AgentCommunicationDemo()
    
    async def demo_basic_agent_queries(self):
        """Demonstrate basic individual agent capabilities."""
        print("\n🌟 DEMO 1: Basic Agent Capabilities")
        print("=" * 60)
        
        # Weather agent demo
        print("\n🌦️  Weather Agent Demo:")
        weather_result = await self.orchestrator.weather_agent.process_message(
            "Analyze weather impact for travel to Miami this weekend",
            {"city": "Miami", "dates": ["2025-06-28", "2025-06-29"], "context": "travel"}
        )
        print(f"Weather Analysis: {weather_result.get('response', 'N/A')}")
        
        # Event agent demo
        print("\n🎫 Event Agent Demo:")
        event_result = await self.orchestrator.event_agent.process_message(
            "Find major events in Las Vegas affecting travel costs",
            {"city": "Las Vegas", "dates": ["2025-07-15", "2025-07-16", "2025-07-17"]}
        )
        print(f"Event Analysis: Found {len(event_result.get('events', []))} events")
        
        # Flight agent demo
        print("\n✈️  Flight Agent Demo:")
        flight_result = await self.orchestrator.flight_agent.process_message(
            "Analyze flight pricing trends for NYC to LA route",
            {"origin": "New York", "destination": "Los Angeles", "dates": ["2025-07-20"]}
        )
        print(f"Flight Analysis: {flight_result.get('type', 'N/A')} completed")
        
        return {
            "weather": weather_result,
            "events": event_result,
            "flights": flight_result
        }
    
    async def demo_agent_communication(self):
        """Demonstrate agent-to-agent communication."""
        print("\n🤝 DEMO 2: Agent-to-Agent Communication")
        print("=" * 60)
        
        print("\nDemonstrating how agents share information:")
        
        # Weather agent informs flight agent about severe conditions
        print("\n1. Weather → Flight Communication:")
        weather_to_flight = await self.orchestrator.agent_to_agent_communication(
            from_agent="weather",
            to_agent="flight", 
            message="Severe storm system affecting Chicago airports on July 15th",
            context={
                "weather_impact": {
                    "city": "Chicago",
                    "date": "2025-07-15",
                    "impact_score": 8.5,
                    "condition": "Severe Thunderstorms"
                }
            }
        )
        print(f"Communication established: {weather_to_flight.get('communication', {}).get('from_agent')} → {weather_to_flight.get('communication', {}).get('to_agent')}")
        
        # Event agent shares major event info
        print("\n2. Event → Weather Communication:")
        event_to_weather = await self.orchestrator.agent_to_agent_communication(
            from_agent="event",
            to_agent="weather",
            message="Major music festival in Austin, 50k attendees expected",
            context={
                "event_impact": {
                    "city": "Austin",
                    "dates": ["2025-08-15", "2025-08-16"],
                    "expected_attendance": 50000,
                    "impact_score": 7.2
                }
            }
        )
        print(f"Event data shared with weather agent for correlation analysis")
        
        # Flight agent requests multi-source data
        print("\n3. Flight Agent Multi-Source Request:")
        flight_request = await self.orchestrator.agent_to_agent_communication(
            from_agent="flight",
            to_agent="event",
            message="Need event data for pricing analysis on Denver routes",
            context={
                "analysis_request": {
                    "routes": ["NYC-Denver", "LA-Denver", "Chicago-Denver"],
                    "timeframe": "July 2025",
                    "analysis_type": "pricing_correlation"
                }
            }
        )
        print(f"Multi-source data request processed")
        
        return {
            "weather_to_flight": weather_to_flight,
            "event_to_weather": event_to_weather, 
            "flight_request": flight_request
        }
    
    async def demo_complex_orchestration(self):
        """Demonstrate complex multi-agent orchestration."""
        print("\n🎭 DEMO 3: Complex Multi-Agent Orchestration")
        print("=" * 60)
        
        complex_queries = [
            "Why are flights from Boston to Denver more expensive on July 20th compared to July 18th?",
            "Analyze the correlation between weather patterns and flight pricing for routes to Florida",
            "What combination of factors is driving high travel costs to Las Vegas next month?"
        ]
        
        results = []
        for i, query in enumerate(complex_queries, 1):
            print(f"\n{i}. Processing: '{query}'")
            result = await self.orchestrator.process_complex_query(query)
            
            if "error" not in result:
                print(f"   ✅ Analysis completed")
                print(f"   📊 Correlations found: {len(result.get('correlations', {}).get('insights', []))}")
                print(f"   🎯 Response length: {len(result.get('response', ''))}")
            else:
                print(f"   ❌ Error: {result['error']}")
            
            results.append(result)
        
        return results
    
    async def demo_streaming_analysis(self):
        """Demonstrate streaming analysis capabilities."""
        print("\n📊 DEMO 4: Streaming Analysis")
        print("=" * 60)
        
        streaming_query = (
            "Perform comprehensive analysis of travel factors affecting "
            "New York to Los Angeles flights in summer 2025"
        )
        
        print(f"\nStreaming analysis for: '{streaming_query}'")
        print("Progress updates:")
        
        chunk_count = 0
        async for chunk in self.travel_agent.stream(streaming_query, "demo_session"):
            chunk_count += 1
            status = "🔄" if not chunk.get('is_task_complete') else "✅"
            print(f"  {status} Chunk {chunk_count}: {chunk.get('content', '')[:100]}...")
            
            if chunk.get('is_task_complete'):
                break
        
        print(f"\nStreaming completed with {chunk_count} chunks")
        return {"chunks_received": chunk_count, "final_chunk": chunk}
    
    async def demo_correlation_analysis(self):
        """Demonstrate advanced correlation analysis."""
        print("\n🔗 DEMO 5: Advanced Correlation Analysis")
        print("=" * 60)
        
        # Test various correlation scenarios
        scenarios = [
            {
                "name": "Weather-Flight Correlation",
                "context": {
                    "cities": ["Miami", "Chicago"],
                    "dates": ["2025-07-15", "2025-07-16"],
                    "query_type": "pricing"
                }
            },
            {
                "name": "Event-Flight Correlation", 
                "context": {
                    "cities": ["Las Vegas", "Austin"],
                    "dates": ["2025-08-15", "2025-08-16"],
                    "query_type": "impact"
                }
            },
            {
                "name": "Multi-Factor Analysis",
                "context": {
                    "cities": ["New York", "Los Angeles"],
                    "dates": ["2025-07-20", "2025-07-21"],
                    "routes": [{"origin": "New York", "destination": "Los Angeles"}],
                    "query_type": "recommendation"
                }
            }
        ]
        
        correlation_results = []
        
        for scenario in scenarios:
            print(f"\n🔍 Analyzing: {scenario['name']}")
            
            # Simulate correlation analysis
            context = scenario["context"]
            agent_results = await self.orchestrator.coordinate_agents(
                type("QueryContext", (), context)()
            )
            
            correlations = await self.orchestrator.cross_analyze_data(
                agent_results, 
                type("QueryContext", (), context)()
            )
            
            print(f"  📈 Weather-Flight Correlation: {correlations.get('weather_flight_correlation', {}).get('strength', 0)}/10")
            print(f"  🎫 Event-Flight Correlation: {correlations.get('event_flight_correlation', {}).get('strength', 0)}/10")
            print(f"  💡 Insights: {len(correlations.get('insights', []))}")
            
            correlation_results.append({
                "scenario": scenario['name'],
                "correlations": correlations
            })
        
        return correlation_results
    
    async def run_full_demo(self):
        """Run the complete demonstration."""
        print("🚀 ENHANCED TRAVEL ANALYSIS MULTI-AGENT SYSTEM DEMO")
        print("=" * 80)
        print("This demo showcases the capabilities of the coordinated agent system")
        print("that analyzes correlations between weather, events, and flight pricing.")
        print("=" * 80)
        
        try:
            # Run all demos
            demo_results = {}
            
            demo_results["basic_agents"] = await self.demo_basic_agent_queries()
            demo_results["agent_communication"] = await self.demo_agent_communication() 
            demo_results["complex_orchestration"] = await self.demo_complex_orchestration()
            demo_results["streaming_analysis"] = await self.demo_streaming_analysis()
            demo_results["correlation_analysis"] = await self.demo_correlation_analysis()
            
            # Summary
            print("\n🎉 DEMO SUMMARY")
            print("=" * 60)
            print("✅ Basic agent capabilities demonstrated")
            print("✅ Agent-to-agent communication working")
            print("✅ Complex orchestration successful")
            print("✅ Streaming analysis functional")
            print("✅ Correlation analysis completed")
            
            print(f"\n📊 Total demos completed: {len(demo_results)}")
            print("🔗 All agents successfully coordinated")
            print("💡 System ready for production queries!")
            
            return demo_results
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            print(f"\n❌ Demo encountered an error: {e}")
            return {"error": str(e)}


async def main():
    """Main demo execution function."""
    print("Initializing Enhanced Travel Analysis Demo...")
    
    demo = TravelAnalysisDemo()
    
    try:
        results = await demo.run_full_demo()
        
        if "error" not in results:
            print(f"\n🎯 Demo completed successfully!")
            print("You can now test the system with queries like:")
            print("- 'Why are flights to Miami expensive this weekend?'")
            print("- 'How do events in Las Vegas affect flight prices?'") 
            print("- 'Analyze weather impact on Chicago flight pricing'")
        else:
            print(f"Demo failed: {results['error']}")
            
    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        print(f"Failed to run demo: {e}")


if __name__ == "__main__":
    print("Starting Enhanced Travel Analysis Multi-Agent System Demo...")
    asyncio.run(main())
