"""Orchestrator Agent for coordinating between Weather, Event, and Flight agents."""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from weather_agent import WeatherAgent
from event_agent import EventAgent  
from flight_agent import FlightAgent

logger = logging.getLogger(__name__)


class QueryContext(BaseModel):
    """Context for complex queries."""
    cities: List[str] = []
    dates: List[str] = []
    routes: List[Dict[str, str]] = []  # origin, destination pairs
    query_type: str = "general"  # "pricing", "impact", "recommendation", etc.
    user_intent: str = ""


class OrchestratorAgent:
    """
    Orchestrator agent that coordinates between Weather, Event, and Flight agents
    to answer complex queries about correlations between weather, events, and flight pricing.
    """
    
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0.2)
        self.agent_id = "orchestrator_agent"
        
        # Initialize specialist agents
        self.weather_agent = WeatherAgent()
        self.event_agent = EventAgent()
        self.flight_agent = FlightAgent()
        
        self.agents = {
            "weather": self.weather_agent,
            "event": self.event_agent,
            "flight": self.flight_agent
        }
        
    async def parse_complex_query(self, query: str) -> QueryContext:
        """Parse a complex user query to extract context and intent."""
        try:
            parsing_prompt = f"""
            Parse this travel/flight query and extract the following information:
            
            Query: "{query}"
            
            Extract:
            1. Cities mentioned (departure/arrival/destination)
            2. Dates or date ranges mentioned
            3. Routes (origin-destination pairs)
            4. Query type: "pricing", "impact", "recommendation", "comparison", "general"
            5. User intent in one sentence
            
            Return in this format:
            Cities: [list of cities]
            Dates: [list of dates in YYYY-MM-DD format]
            Routes: [list of origin->destination]
            Query Type: [type]
            Intent: [intent description]
            """
            
            response = await self.model.ainvoke([HumanMessage(content=parsing_prompt)])
            
            # Parse the LLM response (simplified - real implementation would use structured output)
            # For now, using basic keyword extraction
            cities = []
            dates = []
            routes = []
            query_type = "general"
            
            query_lower = query.lower()
            
            # Simple keyword-based extraction
            if any(word in query_lower for word in ["expensive", "price", "cost", "pricing"]):
                query_type = "pricing"
            elif any(word in query_lower for word in ["impact", "affect", "influence"]):
                query_type = "impact"
            elif any(word in query_lower for word in ["recommend", "best", "should"]):
                query_type = "recommendation"
            
            # Extract common city names (simplified)
            common_cities = ["new york", "los angeles", "chicago", "miami", "denver", "seattle", "boston"]
            for city in common_cities:
                if city in query_lower:
                    cities.append(city.title())
            
            return QueryContext(
                cities=cities,
                dates=dates,
                routes=routes,
                query_type=query_type,
                user_intent=response.content[:200]  # First 200 chars
            )
            
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            return QueryContext(user_intent=query)
    
    async def coordinate_agents(self, context: QueryContext) -> Dict[str, Any]:
        """Coordinate between agents to gather comprehensive information."""
        try:
            # Prepare shared context for all agents
            shared_context = {
                "cities": context.cities,
                "dates": context.dates,
                "routes": context.routes,
                "query_type": context.query_type
            }
            
            # Gather information from all agents concurrently
            tasks = []
            
            # Weather agent tasks
            if context.cities:
                for city in context.cities:
                    weather_context = shared_context.copy()
                    weather_context.update({"city": city, "context": "travel_planning"})
                    tasks.append(
                        self.weather_agent.process_message(
                            f"Get weather impact analysis for {city}", 
                            weather_context
                        )
                    )
            
            # Event agent tasks
            if context.cities:
                for city in context.cities:
                    event_context = shared_context.copy()
                    event_context.update({"city": city, "categories": ["music", "sports", "arts"]})
                    tasks.append(
                        self.event_agent.process_message(
                            f"Search events and analyze impact for {city}",
                            event_context
                        )
                    )
            
            # Flight agent tasks
            if context.routes or len(context.cities) >= 2:
                routes_to_check = context.routes
                if not routes_to_check and len(context.cities) >= 2:
                    # Create routes from cities
                    routes_to_check = [{"origin": context.cities[0], "destination": context.cities[1]}]
                
                for route in routes_to_check:
                    flight_context = shared_context.copy()
                    flight_context.update({
                        "origin": route.get("origin", ""),
                        "destination": route.get("destination", ""),
                        "external_factors": {}  # Will be populated with weather/event data
                    })
                    tasks.append(
                        self.flight_agent.process_message(
                            "Analyze flight pricing and trends",
                            flight_context
                        )
                    )
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Organize results by agent type
            organized_results = {
                "weather_data": [],
                "event_data": [],
                "flight_data": [],
                "errors": []
            }
            
            for result in results:
                if isinstance(result, Exception):
                    organized_results["errors"].append(str(result))
                    continue
                
                agent_id = result.get("agent_id", "unknown")
                if agent_id == "weather_agent":
                    organized_results["weather_data"].append(result)
                elif agent_id == "event_agent":
                    organized_results["event_data"].append(result)
                elif agent_id == "flight_agent":
                    organized_results["flight_data"].append(result)
            
            return organized_results
            
        except Exception as e:
            logger.error(f"Error coordinating agents: {e}")
            return {"error": str(e)}
    
    async def cross_analyze_data(self, agent_results: Dict[str, Any], 
                               context: QueryContext) -> Dict[str, Any]:
        """Perform cross-analysis between weather, events, and flight data."""
        try:
            weather_data = agent_results.get("weather_data", [])
            event_data = agent_results.get("event_data", [])
            flight_data = agent_results.get("flight_data", [])
            
            # Extract key metrics for correlation analysis
            correlations = {
                "weather_flight_correlation": {},
                "event_flight_correlation": {},
                "combined_impact": {},
                "insights": []
            }
            
            # Analyze weather-flight correlations
            if weather_data and flight_data:
                for weather_result in weather_data:
                    weather_impact = weather_result.get("impact_analysis", {}).get("impact_score", 0)
                    
                    for flight_result in flight_data:
                        pricing_analysis = flight_result.get("pricing_analysis", {})
                        price_volatility = pricing_analysis.get("price_volatility", 0)
                        
                        correlation_strength = min(weather_impact * price_volatility / 50, 10)
                        
                        correlations["weather_flight_correlation"] = {
                            "strength": correlation_strength,
                            "weather_impact": weather_impact,
                            "price_volatility": price_volatility,
                            "explanation": f"Weather impact score of {weather_impact} correlates with price volatility of {price_volatility}"
                        }
            
            # Analyze event-flight correlations
            if event_data and flight_data:
                for event_result in event_data:
                    event_impact = event_result.get("impact_analysis", {}).get("impact_score", 0)
                    
                    for flight_result in flight_data:
                        pricing_analysis = flight_result.get("pricing_analysis", {})
                        avg_price = pricing_analysis.get("avg_price", 0)
                        
                        correlation_strength = min(event_impact * avg_price / 1000, 10)
                        
                        correlations["event_flight_correlation"] = {
                            "strength": correlation_strength,
                            "event_impact": event_impact,
                            "avg_price": avg_price,
                            "explanation": f"Event impact score of {event_impact} may influence average flight price of ${avg_price}"
                        }
            
            # Generate insights
            insights = []
            
            if correlations["weather_flight_correlation"].get("strength", 0) > 5:
                insights.append("Strong weather-flight price correlation detected")
            
            if correlations["event_flight_correlation"].get("strength", 0) > 5:
                insights.append("Major events significantly impact flight pricing")
            
            if len(insights) == 0:
                insights.append("No significant correlations detected in current data")
            
            correlations["insights"] = insights
            
            return correlations
            
        except Exception as e:
            logger.error(f"Error in cross-analysis: {e}")
            return {"error": str(e)}
    
    async def generate_comprehensive_response(self, query: str, context: QueryContext, 
                                            agent_results: Dict[str, Any], 
                                            correlations: Dict[str, Any]) -> str:
        """Generate a comprehensive response combining all agent insights."""
        try:
            synthesis_prompt = f"""
            User Query: "{query}"
            
            Weather Data Summary:
            {self._summarize_weather_data(agent_results.get("weather_data", []))}
            
            Event Data Summary:
            {self._summarize_event_data(agent_results.get("event_data", []))}
            
            Flight Data Summary:
            {self._summarize_flight_data(agent_results.get("flight_data", []))}
            
            Correlations Found:
            {correlations.get("insights", [])}
            
            Weather-Flight Correlation: {correlations.get("weather_flight_correlation", {})}
            Event-Flight Correlation: {correlations.get("event_flight_correlation", {})}
            
            Please provide a comprehensive response that:
            1. Directly answers the user's question
            2. Explains the relationships between weather, events, and flight pricing
            3. Provides actionable recommendations
            4. Cites specific data points from the analysis
            5. Maintains a helpful and informative tone
            
            Focus on how external factors (weather and events) influence flight pricing patterns.
            """
            
            response = await self.model.ainvoke([HumanMessage(content=synthesis_prompt)])
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I encountered an error while analyzing your query: {str(e)}"
    
    def _summarize_weather_data(self, weather_data: List[Dict[str, Any]]) -> str:
        """Summarize weather data for synthesis."""
        if not weather_data:
            return "No weather data available"
        
        summary_parts = []
        for data in weather_data:
            impact = data.get("impact_analysis", {})
            score = impact.get("impact_score", 0)
            summary_parts.append(f"Weather impact score: {score}/10")
        
        return "; ".join(summary_parts)
    
    def _summarize_event_data(self, event_data: List[Dict[str, Any]]) -> str:
        """Summarize event data for synthesis."""
        if not event_data:
            return "No event data available"
        
        summary_parts = []
        for data in event_data:
            events = data.get("events", [])
            impact = data.get("impact_analysis", {})
            summary_parts.append(f"Found {len(events)} events, impact score: {impact.get('impact_score', 0)}/10")
        
        return "; ".join(summary_parts)
    
    def _summarize_flight_data(self, flight_data: List[Dict[str, Any]]) -> str:
        """Summarize flight data for synthesis."""
        if not flight_data:
            return "No flight data available"
        
        summary_parts = []
        for data in flight_data:
            flights = data.get("flights", [])
            pricing = data.get("pricing_analysis", {})
            avg_price = pricing.get("avg_price", 0)
            volatility = pricing.get("price_volatility", 0)
            summary_parts.append(f"Found {len(flights)} flights, avg price: ${avg_price:.2f}, volatility: {volatility:.1f}")
        
        return "; ".join(summary_parts)
    
    async def process_complex_query(self, query: str) -> Dict[str, Any]:
        """Main method to process complex queries involving multiple agents."""
        try:
            # Step 1: Parse the query
            context = await self.parse_complex_query(query)
            logger.info(f"Parsed query context: {context}")
            
            # Step 2: Coordinate agents to gather data
            agent_results = await self.coordinate_agents(context)
            logger.info(f"Agent coordination completed")
            
            # Step 3: Perform cross-analysis
            correlations = await self.cross_analyze_data(agent_results, context)
            logger.info(f"Cross-analysis completed")
            
            # Step 4: Generate comprehensive response
            response = await self.generate_comprehensive_response(
                query, context, agent_results, correlations
            )
            
            return {
                "response": response,
                "context": context.dict(),
                "agent_results": agent_results,
                "correlations": correlations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing complex query: {e}")
            return {
                "error": str(e),
                "response": "I apologize, but I encountered an error while processing your query. Please try rephrasing your question or contact support."
            }
    
    async def agent_to_agent_communication(self, from_agent: str, to_agent: str, 
                                         message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Facilitate communication between specific agents."""
        try:
            if from_agent not in self.agents or to_agent not in self.agents:
                return {"error": "Invalid agent specified"}
            
            source_agent = self.agents[from_agent]
            target_agent = self.agents[to_agent]
            
            # Send message from source to target
            collaboration_result = await source_agent.collaborate_with_agent(
                to_agent, message, context
            )
            
            # Process the message at the target agent
            target_response = await target_agent.process_message(
                message, collaboration_result.get("context", {})
            )
            
            return {
                "communication": collaboration_result,
                "response": target_response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in agent communication: {e}")
            return {"error": str(e)}
