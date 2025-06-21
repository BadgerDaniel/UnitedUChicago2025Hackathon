"""Event Agent for handling event-related queries and bookings."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import asyncio

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EventData(BaseModel):
    """Event data structure."""
    event_id: str
    name: str
    date: str
    time: Optional[str] = None
    venue: str
    city: str
    category: str  # music, sports, arts, etc.
    price_range: Optional[str] = None
    ticket_availability: Optional[str] = None
    expected_attendance: Optional[int] = None
    event_impact_score: Optional[float] = None  # 0-10 scale for city/flight impact


class EventAgent:
    """Agent responsible for event-related queries and analysis."""
    
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.agent_id = "event_agent"
        
    async def search_events(self, city: str, date_range: List[str], 
                           categories: Optional[List[str]] = None) -> List[EventData]:
        """Search for events in a city within a date range."""
        try:
            # This would integrate with the Ticketmaster MCP tool
            # For now, using mock data structure
            events = []
            
            # Mock event data - real implementation would use MCP tools
            mock_events = [
                EventData(
                    event_id="evt_001",
                    name="Rock Concert",
                    date=date_range[0] if date_range else datetime.now().date().isoformat(),
                    time="20:00",
                    venue="City Arena",
                    city=city,
                    category="music",
                    price_range="$50-$150",
                    ticket_availability="Available",
                    expected_attendance=15000,
                    event_impact_score=7.5
                ),
                EventData(
                    event_id="evt_002",
                    name="Food Festival",
                    date=date_range[0] if date_range else datetime.now().date().isoformat(),
                    time="12:00",
                    venue="Downtown Park",
                    city=city,
                    category="miscellaneous",
                    price_range="$20-$40",
                    ticket_availability="Available",
                    expected_attendance=5000,
                    event_impact_score=4.0
                )
            ]
            
            # Filter by categories if specified
            if categories:
                mock_events = [e for e in mock_events if e.category in categories]
            
            events.extend(mock_events)
            logger.info(f"Found {len(events)} events for {city}")
            return events
            
        except Exception as e:
            logger.error(f"Error searching events: {e}")
            return []
    
    async def analyze_event_impact(self, events: List[EventData], 
                                 analysis_type: str = "city_impact") -> Dict[str, Any]:
        """Analyze the impact of events on city infrastructure, flights, etc."""
        try:
            if not events:
                return {"impact_score": 0, "analysis": "No events found"}
            
            total_attendance = sum(e.expected_attendance or 0 for e in events)
            major_events = [e for e in events if (e.expected_attendance or 0) > 10000]
            
            analysis_prompt = f"""
            Analyze the impact of these events on {analysis_type}:
            
            Total events: {len(events)}
            Major events (>10k attendance): {len(major_events)}
            Total expected attendance: {total_attendance}
            
            Event details:
            {chr(10).join([f"- {e.name} ({e.category}): {e.expected_attendance} attendees" for e in events[:5]])}
            
            Consider impact on:
            - Transportation and traffic
            - Hotel availability and pricing
            - Flight demand and pricing
            - City infrastructure
            
            Provide an impact score (0-10) and detailed analysis.
            """
            
            response = await self.model.ainvoke([HumanMessage(content=analysis_prompt)])
            
            # Calculate impact score based on attendance and event types
            impact_score = min(10, (total_attendance / 10000) + len(major_events))
            
            return {
                "impact_score": impact_score,
                "analysis": response.content,
                "total_events": len(events),
                "major_events": len(major_events),
                "total_attendance": total_attendance,
                "recommendations": self._generate_recommendations(events, impact_score)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing event impact: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, events: List[EventData], impact_score: float) -> List[str]:
        """Generate recommendations based on event impact."""
        recommendations = []
        
        if impact_score > 7:
            recommendations.append("Book flights and hotels well in advance")
            recommendations.append("Expect significant price increases")
            recommendations.append("Consider alternative travel dates")
        elif impact_score > 4:
            recommendations.append("Monitor prices closely")
            recommendations.append("Book accommodations early")
        else:
            recommendations.append("Normal booking practices should suffice")
        
        return recommendations
    
    async def get_event_pricing_trends(self, city: str, event_types: List[str], 
                                     date_range: List[str]) -> Dict[str, Any]:
        """Analyze event pricing trends for a city and date range."""
        try:
            # This would analyze historical pricing data
            # Mock implementation
            trends = {
                "music": {"avg_price": 85, "trend": "increasing", "peak_dates": date_range[:2]},
                "sports": {"avg_price": 120, "trend": "stable", "peak_dates": []},
                "arts": {"avg_price": 45, "trend": "decreasing", "peak_dates": []}
            }
            
            relevant_trends = {k: v for k, v in trends.items() if k in event_types}
            
            return {
                "city": city,
                "date_range": date_range,
                "pricing_trends": relevant_trends,
                "recommendations": "Prices typically increase closer to event dates"
            }
            
        except Exception as e:
            logger.error(f"Error getting pricing trends: {e}")
            return {"error": str(e)}
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a message from another agent or orchestrator."""
        try:
            # Parse the message and determine what event information is needed
            if "search" in message.lower() or "find" in message.lower():
                # Search for events
                city = context.get("city", "Unknown") if context else "Unknown"
                dates = context.get("dates", []) if context else []
                categories = context.get("categories", []) if context else None
                
                events = await self.search_events(city, dates, categories)
                return {
                    "events": [event.dict() for event in events],
                    "agent_id": self.agent_id,
                    "type": "event_search_results"
                }
            
            elif "impact" in message.lower():
                # Analyze event impact
                city = context.get("city", "Unknown") if context else "Unknown"
                dates = context.get("dates", []) if context else []
                
                events = await self.search_events(city, dates)
                impact_analysis = await self.analyze_event_impact(events)
                
                return {
                    "impact_analysis": impact_analysis,
                    "agent_id": self.agent_id,
                    "type": "event_impact_analysis"
                }
            
            else:
                # General event query
                response = await self.model.ainvoke([
                    HumanMessage(content=f"Provide event information for: {message}")
                ])
                return {
                    "response": response.content,
                    "agent_id": self.agent_id,
                    "type": "event_info"
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {"error": str(e), "agent_id": self.agent_id}
    
    async def collaborate_with_agent(self, target_agent: str, message: str, 
                                   shared_context: Dict[str, Any]) -> Dict[str, Any]:
        """Collaborate with another agent by sharing event context."""
        try:
            event_context = {
                "major_events": shared_context.get("events", []),
                "event_impact": shared_context.get("event_impact", {}),
                "pricing_trends": shared_context.get("pricing_trends", {}),
                "recommendations": "Major events may affect travel and accommodation pricing"
            }
            
            return {
                "from_agent": self.agent_id,
                "to_agent": target_agent,
                "message": message,
                "context": event_context,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error collaborating with agent {target_agent}: {e}")
            return {"error": str(e)}
