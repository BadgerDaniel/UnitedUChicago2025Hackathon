"""Enhanced MCP Server with Weather, Event, and Flight tools."""

from mcp.server.fastmcp import FastMCP
import subprocess
import asyncio
import logging
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("TravelAgents")

def run_command(command):
    """Execute linux command (existing functionality)."""
    try:
        result = subprocess.run(
            command, shell=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing command: {e.stderr.strip()}")
        return None

@mcp.tool()
def execute_linux_command(command: str) -> str:
    """
    Executes linux command
    """
    return run_command(command)

@mcp.tool()
def get_weather_forecast(latitude: float, longitude: float, days: int = 5) -> Dict[str, Any]:
    """
    Get weather forecast for a location using coordinates.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location  
        days: Number of days to forecast (default 5)
    """
    try:
        # This would integrate with a real weather API
        # For now, returning structured mock data
        import random
        
        forecast_data = {
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "name": f"Location_{latitude}_{longitude}"
            },
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
                "humidity": random.randint(30, 90),
                "weather_impact_score": random.uniform(1, 8)
            }
            forecast_data["forecast"].append(day_forecast)
        
        logger.info(f"Retrieved weather forecast for {latitude}, {longitude}")
        return forecast_data
        
    except Exception as e:
        logger.error(f"Error getting weather forecast: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_weather_by_city(city: str, country_code: str = "US", days: int = 5) -> Dict[str, Any]:
    """
    Get weather forecast for a city by name.
    
    Args:
        city: Name of the city
        country_code: Country code (default US)
        days: Number of days to forecast
    """
    try:
        # Mock geocoding - in real implementation would use geocoding API
        city_coords = {
            "new york": (40.7128, -74.0060),
            "los angeles": (34.0522, -118.2437),
            "chicago": (41.8781, -87.6298),
            "miami": (25.7617, -80.1918),
            "denver": (39.7392, -104.9903),
            "seattle": (47.6062, -122.3321),
            "boston": (42.3601, -71.0589)
        }
        
        coords = city_coords.get(city.lower(), (40.0, -74.0))  # Default to NYC area
        
        weather_data = get_weather_forecast(coords[0], coords[1], days)
        weather_data["location"]["name"] = f"{city}, {country_code}"
        
        return weather_data
        
    except Exception as e:
        logger.error(f"Error getting weather for city: {e}")
        return {"error": str(e)}

@mcp.tool()
def analyze_weather_impact(city: str, dates: List[str], impact_type: str = "travel") -> Dict[str, Any]:
    """
    Analyze weather impact on travel, events, or flights.
    
    Args:
        city: City name
        dates: List of dates to analyze
        impact_type: Type of impact analysis (travel, events, flights)
    """
    try:
        weather_data = get_weather_by_city(city, days=len(dates))
        
        if "error" in weather_data:
            return weather_data
        
        impact_analysis = {
            "city": city,
            "dates_analyzed": dates,
            "impact_type": impact_type,
            "overall_impact_score": 0,
            "daily_impacts": [],
            "recommendations": []
        }
        
        total_impact = 0
        for i, forecast_day in enumerate(weather_data.get("forecast", [])[:len(dates)]):
            condition = forecast_day.get("condition", "Clear")
            precipitation = forecast_day.get("precipitation_probability", 0)
            wind_speed = forecast_day.get("wind_speed", 0)
            
            # Calculate impact score based on conditions
            impact_score = 0
            if condition in ["Stormy", "Rainy"]:
                impact_score += 3
            if precipitation > 70:
                impact_score += 2
            if wind_speed > 20:
                impact_score += 1.5
            
            daily_impact = {
                "date": dates[i] if i < len(dates) else forecast_day["date"],
                "weather_condition": condition,
                "impact_score": round(impact_score, 1),
                "factors": []
            }
            
            if precipitation > 50:
                daily_impact["factors"].append(f"High precipitation probability ({precipitation}%)")
            if wind_speed > 15:
                daily_impact["factors"].append(f"Strong winds ({wind_speed} km/h)")
            
            impact_analysis["daily_impacts"].append(daily_impact)
            total_impact += impact_score
        
        impact_analysis["overall_impact_score"] = round(total_impact / len(dates), 1) if dates else 0
        
        # Generate recommendations
        if impact_analysis["overall_impact_score"] > 5:
            impact_analysis["recommendations"].append("High weather impact expected - consider alternative dates")
            impact_analysis["recommendations"].append("Monitor weather updates closely")
        elif impact_analysis["overall_impact_score"] > 3:
            impact_analysis["recommendations"].append("Moderate weather impact - have contingency plans")
        else:
            impact_analysis["recommendations"].append("Low weather impact expected")
        
        return impact_analysis
        
    except Exception as e:
        logger.error(f"Error analyzing weather impact: {e}")
        return {"error": str(e)}

@mcp.tool()
def search_events_by_city(city: str, start_date: str, end_date: str, 
                         categories: Optional[List[str]] = None, size: int = 10) -> Dict[str, Any]:
    """
    Search for events in a city within a date range.
    
    Args:
        city: City name to search
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        categories: Event categories to filter by
        size: Maximum number of results
    """
    try:
        # Mock event data - in real implementation would use Ticketmaster API
        import random
        
        event_categories = categories or ["music", "sports", "arts", "miscellaneous"]
        venues = [f"{city} Arena", f"{city} Stadium", f"{city} Convention Center", f"Downtown {city} Theater"]
        
        events = []
        for i in range(min(size, 8)):  # Generate up to 8 mock events
            event_date = start_date  # Simplified - would randomize within range
            
            event = {
                "event_id": f"evt_{city.lower()}_{i+1}",
                "name": random.choice([
                    "Rock Concert", "Basketball Game", "Art Exhibition", "Food Festival",
                    "Comedy Show", "Theater Performance", "Music Festival", "Sports Championship"
                ]),
                "date": event_date,
                "time": f"{random.randint(18, 22)}:00",
                "venue": random.choice(venues),
                "city": city,
                "category": random.choice(event_categories),
                "price_range": f"${random.randint(20, 200)}-${random.randint(200, 500)}",
                "ticket_availability": random.choice(["Available", "Limited", "Sold Out"]),
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
        
    except Exception as e:
        logger.error(f"Error searching events: {e}")
        return {"error": str(e)}

@mcp.tool()
def analyze_event_impact(city: str, dates: List[str]) -> Dict[str, Any]:
    """
    Analyze the impact of events on city infrastructure and travel.
    
    Args:
        city: City name
        dates: List of dates to analyze
    """
    try:
        # Get events for the date range
        start_date = min(dates) if dates else datetime.now().date().isoformat()
        end_date = max(dates) if dates else start_date
        
        events_data = search_events_by_city(city, start_date, end_date)
        
        if "error" in events_data:
            return events_data
        
        events = events_data.get("events", [])
        
        # Calculate impact metrics
        total_attendance = sum(event.get("expected_attendance", 0) for event in events)
        major_events = [e for e in events if e.get("expected_attendance", 0) > 10000]
        
        impact_score = 0
        if total_attendance > 50000:
            impact_score += 4
        if len(major_events) > 2:
            impact_score += 3
        if any(e.get("category") == "sports" for e in events):
            impact_score += 2
        
        impact_analysis = {
            "city": city,
            "dates_analyzed": dates,
            "total_events": len(events),
            "major_events": len(major_events),
            "total_expected_attendance": total_attendance,
            "impact_score": min(impact_score, 10),
            "impact_factors": [],
            "recommendations": []
        }
        
        # Add impact factors
        if major_events:
            impact_analysis["impact_factors"].append(f"{len(major_events)} major events with >10k attendance")
        if total_attendance > 30000:
            impact_analysis["impact_factors"].append(f"High total attendance: {total_attendance}")
        
        # Generate recommendations
        if impact_score > 7:
            impact_analysis["recommendations"].extend([
                "Book accommodations well in advance",
                "Expect significant traffic and transportation delays",
                "Consider alternative travel dates if possible"
            ])
        elif impact_score > 4:
            impact_analysis["recommendations"].extend([
                "Monitor hotel and flight prices for increases",
                "Plan extra travel time for transportation"
            ])
        else:
            impact_analysis["recommendations"].append("Normal travel conditions expected")
        
        return impact_analysis
        
    except Exception as e:
        logger.error(f"Error analyzing event impact: {e}")
        return {"error": str(e)}

@mcp.tool()
def search_flights(origin: str, destination: str, departure_dates: List[str], 
                  return_dates: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Search for flights between cities.
    
    Args:
        origin: Origin city
        destination: Destination city
        departure_dates: List of departure dates
        return_dates: Optional return dates
    """
    try:
        import random
        
        flights = []
        airlines = ["American Airlines", "Delta", "United", "Southwest", "JetBlue"]
        
        base_price = random.randint(200, 800)
        
        for i, dep_date in enumerate(departure_dates[:5]):  # Limit to 5 flights
            price_variation = random.uniform(0.8, 1.4)
            
            flight = {
                "flight_id": f"FL{1000 + i}",
                "airline": random.choice(airlines),
                "flight_number": f"{random.choice(['AA', 'DL', 'UA', 'WN', 'B6'])}{random.randint(100, 9999)}",
                "origin": origin,
                "destination": destination,
                "departure_date": dep_date,
                "departure_time": f"{random.randint(6, 22):02d}:{random.choice(['00', '15', '30', '45'])}",
                "arrival_time": f"{random.randint(8, 23):02d}:{random.choice(['00', '15', '30', '45'])}",
                "duration": f"{random.randint(2, 8)}h {random.randint(0, 55)}m",
                "price": round(base_price * price_variation, 2),
                "currency": "USD",
                "availability": random.choice(["Available", "Limited", "Waitlist"]),
                "aircraft_type": random.choice(["Boeing 737", "Airbus A320", "Boeing 777", "Airbus A350"])
            }
            flights.append(flight)
        
        return {
            "route": f"{origin} to {destination}",
            "search_dates": departure_dates,
            "total_flights": len(flights),
            "flights": flights
        }
        
    except Exception as e:
        logger.error(f"Error searching flights: {e}")
        return {"error": str(e)}

@mcp.tool()
def analyze_flight_pricing(origin: str, destination: str, dates: List[str], 
                          external_factors: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze flight pricing with consideration of external factors.
    
    Args:
        origin: Origin city
        destination: Destination city  
        dates: List of dates to analyze
        external_factors: Weather and event impact data
    """
    try:
        # Get flight data
        flights_data = search_flights(origin, destination, dates)
        
        if "error" in flights_data:
            return flights_data
        
        flights = flights_data.get("flights", [])
        
        if not flights:
            return {"error": "No flights found"}
        
        # Calculate pricing statistics
        prices = [flight["price"] for flight in flights]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        price_volatility = (max_price - min_price) / avg_price * 10 if avg_price > 0 else 0
        
        # Analyze external factor impacts
        external_impact = 0
        impact_factors = []
        
        if external_factors:
            weather_impact = external_factors.get("weather_impact_score", 0)
            event_impact = external_factors.get("event_impact_score", 0)
            
            if weather_impact > 5:
                external_impact += weather_impact * 0.1
                impact_factors.append(f"Weather impact: {weather_impact}/10")
            
            if event_impact > 5:
                external_impact += event_impact * 0.15
                impact_factors.append(f"Event impact: {event_impact}/10")
        
        # Adjust pricing based on external factors
        adjusted_avg_price = avg_price * (1 + external_impact)
        
        peak_dates = []
        for flight in flights:
            if flight["price"] > avg_price * 1.2:
                peak_dates.append(flight["departure_date"])
        
        pricing_analysis = {
            "route": f"{origin} to {destination}",
            "date_range": dates,
            "pricing_statistics": {
                "average_price": round(avg_price, 2),
                "min_price": min_price,
                "max_price": max_price,
                "price_volatility": round(price_volatility, 1),
                "adjusted_avg_price": round(adjusted_avg_price, 2)
            },
            "external_factors": {
                "impact_score": round(external_impact * 10, 1),
                "factors": impact_factors
            },
            "peak_dates": peak_dates,
            "recommendations": []
        }
        
        # Generate recommendations
        if external_impact > 0.2:
            pricing_analysis["recommendations"].append("Significant price increases expected due to external factors")
            pricing_analysis["recommendations"].append("Book immediately or consider alternative dates")
        elif external_impact > 0.1:
            pricing_analysis["recommendations"].append("Moderate price increases possible")
            pricing_analysis["recommendations"].append("Monitor prices closely")
        else:
            pricing_analysis["recommendations"].append("Normal pricing patterns expected")
        
        if price_volatility > 5:
            pricing_analysis["recommendations"].append("High price volatility - consider flexible booking options")
        
        return pricing_analysis
        
    except Exception as e:
        logger.error(f"Error analyzing flight pricing: {e}")
        return {"error": str(e)}

@mcp.tool()
def cross_analyze_factors(origin: str, destination: str, dates: List[str]) -> Dict[str, Any]:
    """
    Perform comprehensive cross-analysis of weather, events, and flight pricing.
    
    Args:
        origin: Origin city
        destination: Destination city
        dates: List of dates to analyze
    """
    try:
        # Get data from all sources
        weather_origin = analyze_weather_impact(origin, dates, "travel")
        weather_dest = analyze_weather_impact(destination, dates, "travel")
        events_origin = analyze_event_impact(origin, dates)
        events_dest = analyze_event_impact(destination, dates)
        
        # Combine external factors
        combined_external_factors = {
            "weather_impact_score": max(
                weather_origin.get("overall_impact_score", 0),
                weather_dest.get("overall_impact_score", 0)
            ),
            "event_impact_score": max(
                events_origin.get("impact_score", 0),
                events_dest.get("impact_score", 0)
            )
        }
        
        # Analyze flight pricing with external factors
        flight_analysis = analyze_flight_pricing(origin, destination, dates, combined_external_factors)
        
        # Calculate correlation scores
        weather_flight_correlation = 0
        event_flight_correlation = 0
        
        if flight_analysis.get("pricing_statistics"):
            price_volatility = flight_analysis["pricing_statistics"].get("price_volatility", 0)
            
            weather_flight_correlation = min(
                combined_external_factors["weather_impact_score"] * price_volatility / 50, 10
            )
            event_flight_correlation = min(
                combined_external_factors["event_impact_score"] * price_volatility / 50, 10
            )
        
        comprehensive_analysis = {
            "route": f"{origin} to {destination}",
            "analysis_dates": dates,
            "weather_analysis": {
                "origin": weather_origin,
                "destination": weather_dest
            },
            "event_analysis": {
                "origin": events_origin,
                "destination": events_dest
            },
            "flight_analysis": flight_analysis,
            "correlations": {
                "weather_flight_correlation": round(weather_flight_correlation, 2),
                "event_flight_correlation": round(event_flight_correlation, 2),
                "combined_impact": round((weather_flight_correlation + event_flight_correlation) / 2, 2)
            },
            "insights": [],
            "recommendations": []
        }
        
        # Generate insights
        if weather_flight_correlation > 6:
            comprehensive_analysis["insights"].append("Strong correlation between weather conditions and flight pricing")
        if event_flight_correlation > 6:
            comprehensive_analysis["insights"].append("Major events significantly impact flight demand and pricing")
        if comprehensive_analysis["correlations"]["combined_impact"] > 7:
            comprehensive_analysis["insights"].append("Multiple factors creating high price volatility")
        
        # Consolidate recommendations
        all_recommendations = set()
        
        for analysis in [weather_origin, weather_dest, events_origin, events_dest, flight_analysis]:
            if isinstance(analysis, dict) and "recommendations" in analysis:
                all_recommendations.update(analysis["recommendations"])
        
        comprehensive_analysis["recommendations"] = list(all_recommendations)
        
        return comprehensive_analysis
        
    except Exception as e:
        logger.error(f"Error in cross-analysis: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Use uvicorn to run the server on port 8001
    logger.info("Starting Enhanced MCP Server on port 8001...")
    try:
        # Get the FastAPI app from the MCP instance
        app = mcp.create_app()
        
        # Run with uvicorn on port 8001
        uvicorn.run(app, host="0.0.0.0", port=8001)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        logger.info("Trying fallback method...")
        # Fallback to default method if uvicorn approach fails
        mcp.run(transport="sse")
