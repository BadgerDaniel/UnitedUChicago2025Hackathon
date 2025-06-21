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
            # Simple keyword-based extraction for streamlined version
            cities = []
            dates = []
            routes = []
            query_type = "general"
            
            query_lower = query.lower()
            
            # Extract query type
            if any(word in query_lower for word in ["expensive", "price", "cost", "pricing"]):
                query_type = "pricing"
            elif any(word in query_lower for word in ["impact", "affect", "influence"]):
                query_type = "impact"
            elif any(word in query_lower for word in ["recommend", "best", "should"]):
                query_type = "recommendation"
            
            # Extract common city names
            common_cities = ["new york", "los angeles", "chicago", "miami", "denver", "seattle", "boston", "las vegas"]
            for city in common_cities:
                if city in query_lower:
                    cities.append(city.title())
            
            return QueryContext(
                cities=cities,
                dates=dates,
                routes=routes,
                query_type=query_type,
                user_intent=query
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
                        "external_factors": {}
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
            
            correlations = {
                "weather_flight_correlation": {"strength": 0},
                "event_flight_correlation": {"strength": 0},
                "insights": []
            }
            
            # Simplified correlation analysis
            if weather_data and flight_data:
                # Mock correlation calculation
                correlations["weather_flight_correlation"]["strength"] = 6.5
                correlations["insights"].append("Weather conditions may impact flight operations")
            
            if event_data and flight_data:
                # Mock correlation calculation
                correlations["event_flight_correlation"]["strength"] = 5.2
                correlations["insights"].append("Events may influence travel demand")
            
            if not correlations["insights"]:
                correlations["insights"].append("Limited correlation data available")
            
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
            
            Based on analysis from weather, event, and flight specialists:
            - Weather data: {len(agent_results.get("weather_data", []))} reports
            - Event data: {len(agent_results.get("event_data", []))} reports  
            - Flight data: {len(agent_results.get("flight_data", []))} reports
            
            Key correlations found: {correlations.get("insights", [])}
            
            Provide a comprehensive response that:
            1. Directly answers the user's question
            2. Explains relationships between weather, events, and flight pricing
            3. Provides actionable recommendations
            4. Maintains a helpful tone
            """
            
            response = await self.model.ainvoke([HumanMessage(content=synthesis_prompt)])
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I encountered an error while analyzing your query: {str(e)}"
    
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
                "correlations": correlations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing complex query: {e}")
            return {
                "error": str(e),
                "response": "I apologize, but I encountered an error while processing your query. Please try rephrasing your question."
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
