from mcp.server.fastmcp import FastMCP
import subprocess
import random
from datetime import datetime, timedelta

mcp = FastMCP("TravelAgents")

def run_command(command):
    try:
        result = subprocess.run(
            command, shell=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"

@mcp.tool()
def execute_linux_command(command: str) -> str:
    """Executes linux command"""
    return run_command(command)

@mcp.tool()
def get_weather_by_city(city: str) -> str:
    """Get weather forecast for a city"""
    conditions = ["Clear", "Cloudy", "Rainy", "Stormy"]
    temp = round(20 + random.uniform(-10, 15), 1)
    condition = random.choice(conditions)
    impact = random.uniform(1, 8)
    
    return f"Weather in {city}: {temp}°C, {condition}. Travel impact score: {impact:.1f}/10"

@mcp.tool()
def search_events_in_city(city: str, date: str) -> str:
    """Search for events in a city on a specific date"""
    events = ["Rock Concert", "Basketball Game", "Food Festival", "Theater Show"]
    num_events = random.randint(2, 6)
    event_list = random.sample(events, min(num_events, len(events)))
    impact = random.uniform(2, 9)
    
    return f"Events in {city} on {date}: {', '.join(event_list)}. Event impact score: {impact:.1f}/10"

@mcp.tool()
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for flights between cities"""
    price = random.randint(200, 800)
    airlines = ["American", "Delta", "United"]
    airline = random.choice(airlines)
    
    return f"Flight {origin} to {destination} on {date}: {airline} Airlines, ${price}"

@mcp.tool()
def analyze_travel_correlation(origin: str, destination: str, date: str) -> str:
    """Analyze correlation between weather, events, and flight pricing"""
    weather_impact = random.uniform(1, 8)
    event_impact = random.uniform(2, 9)
    base_price = random.randint(200, 600)
    
    # Simple correlation simulation
    weather_factor = 1 + (weather_impact / 20)
    event_factor = 1 + (event_impact / 15)
    final_price = base_price * weather_factor * event_factor
    
    correlation = (weather_impact + event_impact) / 2
    
    analysis = f"""
Travel Analysis for {origin} to {destination} on {date}:

Weather Impact: {weather_impact:.1f}/10
Event Impact: {event_impact:.1f}/10
Base Flight Price: ${base_price}
Adjusted Price: ${final_price:.2f}

Correlation Analysis:
- Weather-Flight Correlation: {weather_impact * 0.8:.1f}/10
- Event-Flight Correlation: {event_impact * 0.9:.1f}/10
- Overall Impact Score: {correlation:.1f}/10

Recommendations:
"""
    
    if correlation > 7:
        analysis += "- High impact factors detected - consider alternative dates\n"
        analysis += "- Book immediately or expect higher prices\n"
    elif correlation > 4:
        analysis += "- Moderate impact expected - monitor prices\n"
        analysis += "- Consider flexible booking options\n"
    else:
        analysis += "- Normal conditions expected\n"
        analysis += "- Good time to book at regular prices\n"
    
    return analysis

mcp.run(transport="sse")
