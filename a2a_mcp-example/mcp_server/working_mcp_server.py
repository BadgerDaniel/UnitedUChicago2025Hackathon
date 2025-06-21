"""Simple Enhanced MCP Server for Travel Analysis."""

import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.session import ServerSession
from mcp.types import Tool, TextContent
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
server = Server("travel-analysis-server")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_weather_by_city",
            description="Get weather forecast for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "country_code": {"type": "string", "description": "Country code", "default": "US"},
                    "days": {"type": "integer", "description": "Number of days", "default": 5}
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="search_events_by_city",
            description="Search for events in a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                },
                "required": ["city", "start_date", "end_date"]
            }
        ),
        Tool(
            name="search_flights",
            description="Search for flights between cities",
            inputSchema={
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Origin city"},
                    "destination": {"type": "string", "description": "Destination city"},
                    "departure_dates": {"type": "array", "items": {"type": "string"}, "description": "Departure dates"}
                },
                "required": ["origin", "destination", "departure_dates"]
            }
        ),
        Tool(
            name="analyze_travel_factors",
            description="Comprehensive analysis of weather, events, and flight pricing",
            inputSchema={
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Origin city"},
                    "destination": {"type": "string", "description": "Destination city"},
                    "dates": {"type": "array", "items": {"type": "string"}, "description": "Travel dates"}
                },
                "required": ["origin", "destination", "dates"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_weather_by_city":
            result = await get_weather_by_city(**arguments)
        elif name == "search_events_by_city":
            result = await search_events_by_city(**arguments)
        elif name == "search_flights":
            result = await search_flights(**arguments)
        elif name == "analyze_travel_factors":
            result = await analyze_travel_factors(**arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]

async def get_weather_by_city(city: str, country_code: str = "US", days: int = 5) -> Dict[str, Any]:
    """Get weather forecast for a city."""
    import random
    
    forecast_data = {
        "location": {"name": f"{city}, {country_code}"},
        "forecast": []
    }
    
    base_temp = 20 + random.uniform(-10, 15)
    
    for i in range(days):
        date = (datetime.now() + timedelta(days=i)).isoformat()
        temp_variation = random.uniform(-5, 5)
        
        day_forecast = {
            "date": date,
            "temperature": round(base_temp + temp_variation, 1),
            "condition": random.choice(["Clear", "Cloudy", "Rainy", "Partly Cloudy", "Stormy"]),
            "precipitation_probability": random.randint(0, 100),
            "wind_speed": random.randint(5, 25),
            "weather_impact_score": random.uniform(1, 8)
        }
        forecast_data["forecast"].append(day_forecast)
    
    logger.info(f"Retrieved weather forecast for {city}")
    return forecast_data

async def search_events_by_city(city: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Search for events in a city."""
    import random
    
    venues = [f"{city} Arena", f"{city} Stadium", f"{city} Convention Center"]
    events = []
    
    for i in range(random.randint(3, 8)):
        event = {
            "event_id": f"evt_{city.lower()}_{i+1}",
            "name": random.choice([
                "Rock Concert", "Basketball Game", "Art Exhibition", "Food Festival",
                "Comedy Show", "Theater Performance", "Music Festival"
            ]),
            "date": start_date,
            "venue": random.choice(venues),
            "city": city,
            "category": random.choice(["music", "sports", "arts", "miscellaneous"]),
            "expected_attendance": random.randint(1000, 50000),
            "event_impact_score": random.uniform(2, 9)
        }
        events.append(event)
    
    return {
        "city": city,
        "date_range": f"{start_date} to {end_date}",
        "total_events": len(events),
        "events": events
    }

async def search_flights(origin: str, destination: str, departure_dates: List[str]) -> Dict[str, Any]:
    """Search for flights between cities."""
    import random
    
    flights = []
    airlines = ["American Airlines", "Delta", "United", "Southwest", "JetBlue"]
    base_price = random.randint(200, 800)
    
    for i, dep_date in enumerate(departure_dates[:5]):
        price_variation = random.uniform(0.8, 1.4)
        
        flight = {
            "flight_id": f"FL{1000 + i}",
            "airline": random.choice(airlines),
            "origin": origin,
            "destination": destination,
            "departure_date": dep_date,
            "price": round(base_price * price_variation, 2),
            "currency": "USD"
        }
        flights.append(flight)
    
    return {
        "route": f"{origin} to {destination}",
        "total_flights": len(flights),
        "flights": flights
    }

async def analyze_travel_factors(origin: str, destination: str, dates: List[str]) -> Dict[str, Any]:
    """Comprehensive analysis of weather, events, and flight pricing."""
    # Get data from all sources
    weather_origin = await get_weather_by_city(origin)
    weather_dest = await get_weather_by_city(destination)
    
    start_date = dates[0] if dates else datetime.now().date().isoformat()
    end_date = dates[-1] if len(dates) > 1 else start_date
    
    events_origin = await search_events_by_city(origin, start_date, end_date)
    events_dest = await search_events_by_city(destination, start_date, end_date)
    flights = await search_flights(origin, destination, dates)
    
    # Simple correlation analysis
    weather_impact = (
        weather_origin.get("forecast", [{}])[0].get("weather_impact_score", 0) +
        weather_dest.get("forecast", [{}])[0].get("weather_impact_score", 0)
    ) / 2
    
    event_impact = (
        sum(e.get("event_impact_score", 0) for e in events_origin.get("events", [])) +
        sum(e.get("event_impact_score", 0) for e in events_dest.get("events", []))
    ) / max(len(events_origin.get("events", [])) + len(events_dest.get("events", [])), 1)
    
    flight_prices = [f.get("price", 0) for f in flights.get("flights", [])]
    avg_price = sum(flight_prices) / len(flight_prices) if flight_prices else 0
    
    analysis = {
        "route": f"{origin} to {destination}",
        "analysis_dates": dates,
        "weather_analysis": {
            "origin": weather_origin,
            "destination": weather_dest,
            "combined_impact": round(weather_impact, 2)
        },
        "event_analysis": {
            "origin": events_origin,
            "destination": events_dest,
            "combined_impact": round(event_impact, 2)
        },
        "flight_analysis": flights,
        "correlation_summary": {
            "weather_flight_correlation": round(weather_impact * avg_price / 1000, 2),
            "event_flight_correlation": round(event_impact * avg_price / 1000, 2),
            "overall_impact": round((weather_impact + event_impact) / 2, 2)
        },
        "recommendations": []
    }
    
    # Generate recommendations
    if weather_impact > 6:
        analysis["recommendations"].append("High weather impact expected - consider alternative dates")
    if event_impact > 6:
        analysis["recommendations"].append("Major events may increase travel costs and congestion")
    if avg_price > 500:
        analysis["recommendations"].append("Flight prices are high - consider flexible dates")
    
    if not analysis["recommendations"]:
        analysis["recommendations"].append("Normal travel conditions expected")
    
    return analysis

async def main():
    """Main server function."""
    logger.info("Starting Travel Analysis MCP Server...")
    logger.info("Available tools:")
    logger.info("- get_weather_by_city: Get weather forecast")
    logger.info("- search_events_by_city: Search for events")
    logger.info("- search_flights: Search for flights")
    logger.info("- analyze_travel_factors: Comprehensive analysis")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, ServerSession.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
