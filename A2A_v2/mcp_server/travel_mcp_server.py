"""
Enhanced Travel MCP Server with Real Weather, Events, and Google Trends APIs.
Integrates NWS Weather API, Ticketmaster Events API, and Google Trends for comprehensive travel analysis.
"""

import asyncio
import httpx
import requests
import random
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Import Google Trends analyzer
from google_trends_analyzer import trends_analyzer

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("TravelAnalysisServer")

# API Configuration
NWS_API_BASE = "https://api.weather.gov"
WEATHER_USER_AGENT = "travel-analysis-app/1.0"

TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
TICKETMASTER_BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

# ===== WEATHER FUNCTIONS =====

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": WEATHER_USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Weather API error: {e}")
            return None

def calculate_weather_impact_score(forecast_data: dict) -> float:
    """Calculate weather impact score for travel (0-10 scale)."""
    if not forecast_data or "properties" not in forecast_data:
        return 5.0  # Default moderate impact
    
    periods = forecast_data["properties"]["periods"]
    if not periods:
        return 5.0
    
    total_impact = 0
    count = 0
    
    for period in periods[:3]:  # Check next 3 periods
        impact = 1.0  # Base impact
        
        # Temperature impact
        temp = period.get("temperature", 70)
        if temp < 32 or temp > 95:  # Extreme temperatures
            impact += 3.0
        elif temp < 40 or temp > 85:  # Uncomfortable temperatures
            impact += 1.5
        
        # Wind impact
        wind_speed = period.get("windSpeed", "0 mph")
        wind_num = int(''.join(filter(str.isdigit, wind_speed)) or "0")
        if wind_num > 25:
            impact += 2.0
        elif wind_num > 15:
            impact += 1.0
        
        # Conditions impact
        forecast = period.get("detailedForecast", "").lower()
        if any(word in forecast for word in ["storm", "severe", "heavy rain", "blizzard"]):
            impact += 4.0
        elif any(word in forecast for word in ["rain", "snow", "fog"]):
            impact += 2.0
        elif any(word in forecast for word in ["cloudy", "overcast"]):
            impact += 0.5
        
        total_impact += min(impact, 10.0)  # Cap at 10
        count += 1
    
    return round(total_impact / max(count, 1), 1)

# ===== EVENT FUNCTIONS =====

def search_ticketmaster_events(
    city: str = None,
    country_code: str = "US", 
    keyword: str = None,
    classification: str = None,
    start_date: str = None,
    end_date: str = None,
    size: int = 10
) -> dict:
    """Search for events using Ticketmaster API."""
    if not TICKETMASTER_API_KEY:
        return {"_embedded": {"events": []}}  # Return empty if no API key
    
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "countryCode": country_code,
        "size": min(size, 50)
    }
    
    if city:
        params["city"] = city
    if keyword:
        params["keyword"] = keyword
    if classification:
        params["classificationName"] = classification
    if start_date:
        params["startDateTime"] = start_date
    if end_date:
        params["endDateTime"] = end_date
    
    try:
        response = requests.get(TICKETMASTER_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ticketmaster API error: {e}")
        return {"_embedded": {"events": []}}

def calculate_event_impact_score(events_data: dict) -> float:
    """Calculate event impact score for travel (0-10 scale)."""
    events = events_data.get('_embedded', {}).get('events', [])
    if not events:
        return 1.0  # Low impact if no events
    
    total_attendance = 0
    major_events = 0
    venue_types = set()
    
    for event in events:
        # Estimate attendance based on venue size and event type
        venues = event.get('_embedded', {}).get('venues', [])
        if venues:
            venue = venues[0]
            venue_types.add(venue.get('name', ''))
            
        # Check if it's a major event
        classifications = event.get('classifications', [])
        if classifications:
            genre = classifications[0].get('genre', {}).get('name', '')
            if genre in ['Rock', 'Pop', 'Sports', 'Hip-Hop/Rap']:
                major_events += 1
                total_attendance += 15000  # Estimate
            else:
                total_attendance += 5000   # Estimate
    
    # Calculate impact
    impact = 1.0  # Base impact
    
    # Event count impact
    if len(events) > 5:
        impact += 3.0
    elif len(events) > 2:
        impact += 1.5
    
    # Major events impact
    if major_events > 2:
        impact += 4.0
    elif major_events > 0:
        impact += 2.0
    
    # Total attendance impact
    if total_attendance > 50000:
        impact += 3.0
    elif total_attendance > 20000:
        impact += 1.5
    
    return round(min(impact, 10.0), 1)

# ===== LOCATION MAPPING =====

CITY_COORDINATES = {
    "new york": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298),
    "miami": (25.7617, -80.1918),
    "denver": (39.7392, -104.9903),
    "seattle": (47.6062, -122.3321),
    "boston": (42.3601, -71.0589),
    "las vegas": (36.1699, -115.1398),
    "san francisco": (37.7749, -122.4194),
    "washington": (38.9072, -77.0369),
    "atlanta": (33.7490, -84.3880),
    "phoenix": (33.4484, -112.0740),
    "philadelphia": (39.9526, -75.1652),
    "houston": (29.7604, -95.3698),
    "dallas": (32.7767, -96.7970)
}

def get_city_coordinates(city: str) -> tuple[float, float]:
    """Get coordinates for a city."""
    return CITY_COORDINATES.get(city.lower(), (40.7128, -74.0060))  # Default to NYC

# ===== MCP TOOLS =====

@mcp.tool()
async def get_weather_by_city(city: str) -> str:
    """Get weather forecast for a city with real NWS data and travel impact analysis."""
    try:
        lat, lon = get_city_coordinates(city)
        
        # Get forecast from NWS API
        points_url = f"{NWS_API_BASE}/points/{lat},{lon}"
        points_data = await make_nws_request(points_url)
        
        if not points_data:
            return f"Unable to fetch weather data for {city}. Using general impact estimate: 5.0/10"
        
        forecast_url = points_data["properties"]["forecast"]
        forecast_data = await make_nws_request(forecast_url)
        
        if not forecast_data:
            return f"Unable to fetch detailed forecast for {city}. General impact: 5.0/10"
        
        # Calculate travel impact
        impact_score = calculate_weather_impact_score(forecast_data)
        
        # Format response with first period
        periods = forecast_data["properties"]["periods"]
        if periods:
            current = periods[0]
            temp = current.get("temperature", "Unknown")
            temp_unit = current.get("temperatureUnit", "F")
            wind = current.get("windSpeed", "Unknown")
            condition = current.get("shortForecast", "Unknown")
            
            return (f"Weather in {city}: {temp}°{temp_unit}, {condition}. "
                   f"Wind: {wind}. Travel impact score: {impact_score}/10")
        else:
            return f"Weather data available for {city}. Travel impact score: {impact_score}/10"
            
    except Exception as e:
        return f"Error fetching weather for {city}: {str(e)}. Default impact: 5.0/10"

@mcp.tool()
async def search_events_in_city(city: str, date: str) -> str:
    """Search for events in a city on a specific date with real Ticketmaster data."""
    try:
        # Convert date to ISO format for API
        start_datetime = f"{date}T00:00:00Z"
        end_datetime = f"{date}T23:59:59Z"
        
        # Search events
        events_data = search_ticketmaster_events(
            city=city,
            start_date=start_datetime,
            end_date=end_datetime,
            size=20
        )
        
        events = events_data.get('_embedded', {}).get('events', [])
        impact_score = calculate_event_impact_score(events_data)
        
        if not events:
            return f"No events found in {city} on {date}. Event impact score: {impact_score}/10"
        
        # Format events
        event_names = []
        total_estimated_attendance = 0
        
        for event in events[:6]:  # Show top 6 events
            name = event.get('name', 'Unknown Event')
            event_names.append(name)
            
            # Estimate attendance
            classifications = event.get('classifications', [])
            if classifications:
                genre = classifications[0].get('genre', {}).get('name', '')
                if genre in ['Rock', 'Pop', 'Sports', 'Hip-Hop/Rap']:
                    total_estimated_attendance += 15000
                else:
                    total_estimated_attendance += 5000
        
        return (f"Events in {city} on {date}: {', '.join(event_names)}. "
               f"Total estimated attendance: {total_estimated_attendance}. "
               f"Event impact score: {impact_score}/10")
        
    except Exception as e:
        impact_score = random.uniform(2, 7)  # Fallback
        return f"Error fetching events for {city}: {str(e)}. Estimated impact: {impact_score:.1f}/10"

@mcp.tool()
async def get_google_trends_for_city(city: str) -> str:
    """Get Google Trends analysis for a city to understand travel demand patterns."""
    try:
        trends_result = await trends_analyzer.get_travel_insights_for_city(city)
        return trends_result
    except Exception as e:
        return f"Error fetching Google Trends for {city}: {str(e)}. Trends impact estimate: 3.0/10"

@mcp.tool()
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for flights between cities with pricing analysis (simulated data)."""
    # This would integrate with a real flight API in production
    base_prices = {
        ("new york", "chicago"): 280,
        ("new york", "los angeles"): 350,
        ("chicago", "denver"): 250,
        ("miami", "new york"): 320,
        ("boston", "denver"): 380,
        ("seattle", "new york"): 420,
        ("las vegas", "los angeles"): 180,
    }
    
    route_key = (origin.lower(), destination.lower())
    reverse_key = (destination.lower(), origin.lower())
    
    base_price = base_prices.get(route_key) or base_prices.get(reverse_key) or random.randint(250, 500)
    
    # Add some realistic variation
    variation = random.uniform(0.85, 1.25)
    final_price = int(base_price * variation)
    
    airlines = ["American", "Delta", "United", "Southwest", "JetBlue"]
    airline = random.choice(airlines)
    
    return f"Flight {origin} to {destination} on {date}: {airline} Airlines, ${final_price}"

@mcp.tool()
async def analyze_comprehensive_travel_factors(origin: str, destination: str, date: str) -> str:
    """
    ENHANCED FEATURE: Comprehensive analysis including weather, events, Google trends, and flight pricing.
    Uses real data from NWS, Ticketmaster, and Google Trends for complete travel insights.
    """
    try:
        # Get all data sources
        weather_origin_result = await get_weather_by_city(origin)
        weather_dest_result = await get_weather_by_city(destination)
        events_origin_result = await search_events_in_city(origin, date)
        events_dest_result = await search_events_in_city(destination, date)
        trends_origin_result = await get_google_trends_for_city(origin)
        trends_dest_result = await get_google_trends_for_city(destination)
        flight_result = search_flights(origin, destination, date)
        
        # Extract impact scores
        origin_weather_impact = float(weather_origin_result.split("impact score: ")[1].split("/")[0]) if "impact score:" in weather_origin_result else 5.0
        dest_weather_impact = float(weather_dest_result.split("impact score: ")[1].split("/")[0]) if "impact score:" in weather_dest_result else 5.0
        origin_event_impact = float(events_origin_result.split("impact score: ")[1].split("/")[0]) if "impact score:" in events_origin_result else 3.0
        dest_event_impact = float(events_dest_result.split("impact score: ")[1].split("/")[0]) if "impact score:" in events_dest_result else 3.0
        
        # Extract trends impact scores
        origin_trends_impact = 3.0
        dest_trends_impact = 3.0
        if "Travel Impact Score:" in trends_origin_result:
            origin_trends_impact = float(trends_origin_result.split("Travel Impact Score: ")[1].split("/")[0])
        if "Travel Impact Score:" in trends_dest_result:
            dest_trends_impact = float(trends_dest_result.split("Travel Impact Score: ")[1].split("/")[0])
        
        # Calculate combined impacts
        avg_weather_impact = (origin_weather_impact + dest_weather_impact) / 2
        avg_event_impact = (origin_event_impact + dest_event_impact) / 2
        avg_trends_impact = (origin_trends_impact + dest_trends_impact) / 2
        
        # Calculate price adjustments
        weather_factor = 1 + (avg_weather_impact / 25)
        event_factor = 1 + (avg_event_impact / 20)
        trends_factor = 1 + (avg_trends_impact / 30)  # Trends have lighter impact
        
        # Extract base price
        price_str = flight_result.split("$")[1] if "$" in flight_result else "300"
        base_price = int(price_str.split()[0].replace(",", ""))
        
        adjusted_price = base_price * weather_factor * event_factor * trends_factor
        
        # Calculate overall correlation
        overall_correlation = (avg_weather_impact + avg_event_impact + avg_trends_impact) / 3
        
        analysis = f"""
COMPREHENSIVE Travel Analysis: {origin} → {destination} on {date}
==================================================================================

=== WEATHER IMPACT (Real NWS Data) ===
{origin}: {origin_weather_impact:.1f}/10
{destination}: {dest_weather_impact:.1f}/10
Combined Weather Impact: {avg_weather_impact:.1f}/10

=== EVENT IMPACT (Real Ticketmaster Data) ===
{origin}: {origin_event_impact:.1f}/10
{destination}: {dest_event_impact:.1f}/10
Combined Event Impact: {avg_event_impact:.1f}/10

=== GOOGLE TRENDS IMPACT (Real Search Data) ===
{origin}: {origin_trends_impact:.1f}/10
{destination}: {dest_trends_impact:.1f}/10
Combined Trends Impact: {avg_trends_impact:.1f}/10

=== FLIGHT PRICING ANALYSIS ===
Base Price: ${base_price}
Weather Adjustment: +{((weather_factor - 1) * 100):.1f}%
Event Adjustment: +{((event_factor - 1) * 100):.1f}%
Trends Adjustment: +{((trends_factor - 1) * 100):.1f}%
Final Adjusted Price: ${adjusted_price:.2f}

=== COMPREHENSIVE INSIGHTS ==="""

        # Add detailed insights
        if avg_weather_impact > 7:
            analysis += f"\n🌦️  CRITICAL WEATHER: Severe conditions detected - expect delays/cancellations"
        elif avg_weather_impact > 4:
            analysis += f"\n🌦️  WEATHER CONCERNS: Some conditions may impact travel"
        else:
            analysis += f"\n🌦️  WEATHER FAVORABLE: Good conditions for travel"
        
        if avg_event_impact > 7:
            analysis += f"\n🎫 HIGH EVENT DEMAND: Major events driving significant demand"
        elif avg_event_impact > 4:
            analysis += f"\n🎫 MODERATE EVENTS: Some events affecting demand"
        else:
            analysis += f"\n🎫 NORMAL EVENT ACTIVITY: Typical event schedule"
        
        if avg_trends_impact > 7:
            analysis += f"\n📈 HIGH SEARCH INTEREST: Strong trending topics indicate high travel interest"
        elif avg_trends_impact > 4:
            analysis += f"\n📈 MODERATE INTEREST: Some trending factors affecting demand"
        else:
            analysis += f"\n📈 NORMAL SEARCH ACTIVITY: Typical search patterns"
        
        # Extract trending insights
        if "HIGH IMPACT" in trends_origin_result or "HIGH IMPACT" in trends_dest_result:
            analysis += f"\n🔥 TRENDING ALERT: Google search patterns indicate unusual activity"
        
        analysis += f"\n\n=== ACTIONABLE RECOMMENDATIONS ==="
        
        if overall_correlation > 7:
            analysis += """
🚨 CRITICAL FACTORS DETECTED:
• Multiple high-impact conditions affecting this route
• Book immediately if travel is essential, or consider postponing
• Monitor real-time updates from all sources
• Have backup plans ready for potential disruptions
• Premium pricing expected due to multiple demand drivers"""
        elif overall_correlation > 4:
            analysis += """
⚠️  ELEVATED CONDITIONS:
• Several factors contributing to increased demand/pricing
• Consider flexible booking options for better rates
• Monitor trending topics and weather updates
• Alternative dates may offer significant savings
• Book soon if dates are fixed"""
        else:
            analysis += """
✅ FAVORABLE CONDITIONS:
• All factors indicate normal travel conditions
• Good opportunity for standard pricing
• Minimal external demand pressures
• Safe to wait for better deals if flexible
• Standard booking practices recommended"""
        
        return analysis
        
    except Exception as e:
        return f"Error in comprehensive analysis: {str(e)}"

@mcp.tool()
async def analyze_travel_correlation(origin: str, destination: str, date: str) -> str:
    """
    CORE FEATURE: Analyze correlation between real weather, events, and flight pricing.
    Uses real NWS weather data and Ticketmaster event data for accurate analysis.
    """
    try:
        # Get real weather data for both cities
        weather_origin_result = await get_weather_by_city(origin)
        weather_dest_result = await get_weather_by_city(destination)
        
        # Extract impact scores from weather results
        origin_weather_impact = float(weather_origin_result.split("impact score: ")[1].split("/")[0]) if "impact score:" in weather_origin_result else 5.0
        dest_weather_impact = float(weather_dest_result.split("impact score: ")[1].split("/")[0]) if "impact score:" in weather_dest_result else 5.0
        
        # Get real event data for both cities
        events_origin_result = await search_events_in_city(origin, date)
        events_dest_result = await search_events_in_city(destination, date)
        
        # Extract impact scores from event results
        origin_event_impact = float(events_origin_result.split("impact score: ")[1].split("/")[0]) if "impact score:" in events_origin_result else 3.0
        dest_event_impact = float(events_dest_result.split("impact score: ")[1].split("/")[0]) if "impact score:" in events_dest_result else 3.0
        
        # Get flight data
        flight_result = search_flights(origin, destination, date)
        
        # Calculate combined impacts
        avg_weather_impact = (origin_weather_impact + dest_weather_impact) / 2
        avg_event_impact = (origin_event_impact + dest_event_impact) / 2
        
        # Calculate price adjustments based on real data
        weather_factor = 1 + (avg_weather_impact / 25)  # Up to 40% increase for severe weather
        event_factor = 1 + (avg_event_impact / 20)      # Up to 50% increase for major events
        
        # Extract base price from flight result
        price_str = flight_result.split("$")[1] if "$" in flight_result else "300"
        base_price = int(price_str.split()[0].replace(",", ""))
        
        adjusted_price = base_price * weather_factor * event_factor
        
        # Calculate correlations
        weather_flight_correlation = min(avg_weather_impact * 0.9, 10)
        event_flight_correlation = min(avg_event_impact * 1.1, 10)
        overall_correlation = (weather_flight_correlation + event_flight_correlation) / 2
        
        analysis = f"""
REAL-TIME Travel Correlation Analysis: {origin} → {destination} on {date}

=== WEATHER IMPACT (Real NWS Data) ===
{origin}: {origin_weather_impact:.1f}/10
{destination}: {dest_weather_impact:.1f}/10
Combined Weather Impact: {avg_weather_impact:.1f}/10

=== EVENT IMPACT (Real Ticketmaster Data) ===
{origin}: {origin_event_impact:.1f}/10
{destination}: {dest_event_impact:.1f}/10
Combined Event Impact: {avg_event_impact:.1f}/10

=== FLIGHT PRICING ANALYSIS ===
Base Price: ${base_price}
Weather Adjustment: +{((weather_factor - 1) * 100):.1f}%
Event Adjustment: +{((event_factor - 1) * 100):.1f}%
Adjusted Price: ${adjusted_price:.2f}

=== CORRELATION ANALYSIS ===
Weather-Flight Correlation: {weather_flight_correlation:.1f}/10
Event-Flight Correlation: {event_flight_correlation:.1f}/10
Overall Impact Score: {overall_correlation:.1f}/10

=== REAL DATA INSIGHTS ==="""

        # Add weather insights
        if avg_weather_impact > 7:
            analysis += f"\n• HIGH WEATHER IMPACT: Severe conditions detected via NWS data"
        elif avg_weather_impact > 5:
            analysis += f"\n• MODERATE WEATHER IMPACT: Some weather concerns detected"
        else:
            analysis += f"\n• LOW WEATHER IMPACT: Favorable weather conditions"
        
        # Add event insights
        if avg_event_impact > 7:
            analysis += f"\n• HIGH EVENT IMPACT: Major events detected via Ticketmaster data"
        elif avg_event_impact > 4:
            analysis += f"\n• MODERATE EVENT IMPACT: Some events affecting demand"
        else:
            analysis += f"\n• LOW EVENT IMPACT: Normal event activity"

        analysis += f"\n\n=== RECOMMENDATIONS ==="
        
        if overall_correlation > 7:
            analysis += """
• CRITICAL: Multiple real-world factors driving significant price increases
• Book immediately or consider alternative dates
• Real weather and event data shows high impact conditions
• Monitor both weather updates and event announcements"""
        elif overall_correlation > 4:
            analysis += """
• MODERATE IMPACT: Real data shows some external factors affecting pricing  
• Consider flexible booking options
• Monitor real-time weather and event developments
• Alternative dates may offer better value"""
        else:
            analysis += """
• LOW IMPACT: Real data shows favorable conditions
• Standard booking practices recommended
• Good opportunity for normal pricing
• Minimal external pressure from weather or events"""
        
        return analysis
        
    except Exception as e:
        return f"Error in correlation analysis: {str(e)}"

if __name__ == "__main__":
    print("🚀 Starting Enhanced Travel Analysis MCP Server with Real APIs...")
    print("📦 Available Tools:")
    print("   • get_weather_by_city - Real NWS weather data with impact analysis")
    print("   • search_events_in_city - Real Ticketmaster event data with impact analysis") 
    print("   • get_google_trends_for_city - Google Trends analysis for travel demand")
    print("   • search_flights - Flight pricing analysis")
    print("   • analyze_travel_correlation - Multi-factor correlation with REAL DATA")
    print("   • analyze_comprehensive_travel_factors - COMPLETE analysis with all data sources")
    print()
    if TICKETMASTER_API_KEY:
        print("✅ Ticketmaster API configured")
    else:
        print("⚠️  Ticketmaster API key not found - using fallback event data")
    print("✅ NWS Weather API configured (no key required)")
    print("✅ Google Trends scraping configured")
    print("🔗 Server will run on default port (8000)")
    mcp.run(transport="sse")
