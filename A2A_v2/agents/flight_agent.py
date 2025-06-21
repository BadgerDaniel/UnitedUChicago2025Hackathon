"""Flight Agent for handling flight-related queries and pricing analysis."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import asyncio

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class FlightData(BaseModel):
    """Flight data structure."""
    flight_id: str
    airline: str
    flight_number: str
    departure_city: str
    arrival_city: str
    departure_date: str
    departure_time: str
    arrival_time: str
    duration: str
    price: float
    currency: str = "USD"
    availability: str
    aircraft_type: Optional[str] = None
    price_trend: Optional[str] = None  # "increasing", "decreasing", "stable"


class FlightPricingAnalysis(BaseModel):
    """Flight pricing analysis structure."""
    route: str
    date_range: List[str]
    avg_price: float
    min_price: float
    max_price: float
    price_volatility: float  # 0-10 scale
    peak_dates: List[str]
    best_booking_window: str
    external_factors: List[str]  # weather, events, etc.


class FlightAgent:
    """Agent responsible for flight-related queries and pricing analysis."""
    
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.agent_id = "flight_agent"
        
    async def search_flights(self, origin: str, destination: str, 
                           departure_dates: List[str], 
                           return_dates: Optional[List[str]] = None) -> List[FlightData]:
        """Search for flights between cities on specific dates."""
        try:
            # This would integrate with flight search APIs
            # For now, using mock data structure
            flights = []
            
            # Mock flight data - real implementation would use flight APIs
            base_price = 300
            for i, dep_date in enumerate(departure_dates[:3]):  # Limit to 3 for demo
                mock_flight = FlightData(
                    flight_id=f"FL{1000 + i}",
                    airline="Airlines Inc",
                    flight_number=f"AI{100 + i}",
                    departure_city=origin,
                    arrival_city=destination,
                    departure_date=dep_date,
                    departure_time="10:30",
                    arrival_time="14:45",
                    duration="4h 15m",
                    price=base_price + (i * 50),  # Increasing prices
                    availability="Available",
                    aircraft_type="Boeing 737",
                    price_trend="increasing"
                )
                flights.append(mock_flight)
            
            logger.info(f"Found {len(flights)} flights from {origin} to {destination}")
            return flights
            
        except Exception as e:
            logger.error(f"Error searching flights: {e}")
            return []
    
    async def analyze_flight_pricing(self, origin: str, destination: str, 
                                   date_range: List[str], 
                                   external_factors: Optional[Dict[str, Any]] = None) -> FlightPricingAnalysis:
        """Analyze flight pricing patterns and external factor impacts."""
        try:
            # Get flight data for the route and dates
            flights = await self.search_flights(origin, destination, date_range)
            
            if not flights:
                return FlightPricingAnalysis(
                    route=f"{origin} to {destination}",
                    date_range=date_range,
                    avg_price=0,
                    min_price=0,
                    max_price=0,
                    price_volatility=0,
                    peak_dates=[],
                    best_booking_window="Unknown",
                    external_factors=[]
                )
            
            # Calculate pricing statistics
            prices = [f.price for f in flights]
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            price_volatility = (max_price - min_price) / avg_price * 10 if avg_price > 0 else 0
            
            # Analyze external factors
            external_factor_list = []
            if external_factors:
                weather_impact = external_factors.get("weather_impact", {})
                event_impact = external_factors.get("event_impact", {})
                
                if weather_impact.get("impact_score", 0) > 5:
                    external_factor_list.append("Severe weather conditions")
                
                if event_impact.get("impact_score", 0) > 6:
                    external_factor_list.append("Major events increasing demand")
            
            # Determine peak dates (simplified logic)
            peak_dates = [f.departure_date for f in flights if f.price > avg_price * 1.2]
            
            return FlightPricingAnalysis(
                route=f"{origin} to {destination}",
                date_range=date_range,
                avg_price=avg_price,
                min_price=min_price,
                max_price=max_price,
                price_volatility=price_volatility,
                peak_dates=peak_dates,
                best_booking_window="2-8 weeks in advance",
                external_factors=external_factor_list
            )
            
        except Exception as e:
            logger.error(f"Error analyzing flight pricing: {e}")
            return None
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a message from another agent or orchestrator."""
        try:
            # Parse the message and determine what flight information is needed
            if "search" in message.lower() or "find" in message.lower():
                # Search for flights
                origin = context.get("origin", "Unknown") if context else "Unknown"
                destination = context.get("destination", "Unknown") if context else "Unknown"
                dates = context.get("dates", []) if context else []
                
                flights = await self.search_flights(origin, destination, dates)
                return {
                    "flights": [flight.dict() for flight in flights],
                    "agent_id": self.agent_id,
                    "type": "flight_search_results"
                }
            
            elif "pricing" in message.lower() or "analyze" in message.lower():
                # Analyze flight pricing
                origin = context.get("origin", "Unknown") if context else "Unknown"
                destination = context.get("destination", "Unknown") if context else "Unknown"
                dates = context.get("dates", []) if context else []
                external_factors = context.get("external_factors", {}) if context else {}
                
                analysis = await self.analyze_flight_pricing(origin, destination, dates, external_factors)
                
                return {
                    "pricing_analysis": analysis.dict() if analysis else {},
                    "agent_id": self.agent_id,
                    "type": "flight_pricing_analysis"
                }
            
            else:
                # General flight query
                response = await self.model.ainvoke([
                    HumanMessage(content=f"Provide flight information for: {message}")
                ])
                return {
                    "response": response.content,
                    "agent_id": self.agent_id,
                    "type": "flight_info"
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {"error": str(e), "agent_id": self.agent_id}
    
    async def collaborate_with_agent(self, target_agent: str, message: str, 
                                   shared_context: Dict[str, Any]) -> Dict[str, Any]:
        """Collaborate with another agent by sharing flight context."""
        try:
            flight_context = {
                "pricing_trends": shared_context.get("pricing_analysis", {}),
                "recommendations": "Flight prices may be affected by external factors"
            }
            
            return {
                "from_agent": self.agent_id,
                "to_agent": target_agent,
                "message": message,
                "context": flight_context,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error collaborating with agent {target_agent}: {e}")
            return {"error": str(e)}
