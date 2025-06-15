import streamlit as st
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import asyncio
from datetime import datetime
from mcp.server.fastmcp import FastMCP
import threading
import time

# Initialize FastMCP server
mcp = FastMCP("open_meteo_weather_server")

# Page configuration
st.set_page_config(
    page_title="Open-Meteo Weather MCP Server Dashboard",
    page_icon="🌤️",
    layout="wide"
)

# Title and description
st.title("🌤️ Open-Meteo Weather MCP Server Dashboard")
st.markdown("MCP Server for weather data using Open-Meteo API with Streamlit interface")


# Setup the Open-Meteo API client with cache and retry on error
@st.cache_resource
def get_openmeteo_client():
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)


def get_coordinates_for_city(city: str) -> tuple:
    """
    Simple coordinate lookup for major cities.
    In production, you'd use a geocoding service.
    """
    city_coords = {
        "london": (51.5074, -0.1278),
        "new york": (40.7128, -74.0060),
        "tokyo": (35.6762, 139.6503),
        "paris": (48.8566, 2.3522),
        "sydney": (-33.8688, 151.2093),
        "mumbai": (19.0760, 72.8777),
        "berlin": (52.5200, 13.4050),
        "moscow": (55.7558, 37.6176),
        "beijing": (39.9042, 116.4074),
        "los angeles": (34.0522, -118.2437),
        "chicago": (41.8781, -87.6298),
        "toronto": (43.6532, -79.3832),
        "rome": (41.9028, 12.4964),
        "madrid": (40.4168, -3.7038),
        "amsterdam": (52.3676, 4.9041),
        "stockholm": (59.3293, 18.0686)
    }

    city_lower = city.lower().strip()
    if city_lower in city_coords:
        return city_coords[city_lower]
    else:
        # Default to London if city not found
        return city_coords["london"]


async def get_weather_data(city: str) -> str:
    """
    Fetch weather data from Open-Meteo API.

    Args:
        city: City name

    Returns:
        str: Formatted weather data or error message
    """
    try:
        # Get coordinates for the city
        latitude, longitude = get_coordinates_for_city(city)

        # Get Open-Meteo client
        openmeteo = get_openmeteo_client()

        # API parameters for current and forecast weather
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "weather_code"],
            "hourly": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"],
            "daily": ["temperature_2m_max", "temperature_2m_min", "weather_code"],
            "timezone": "auto"
        }

        # Make API request
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        # Get current weather
        current = response.Current()
        current_temp = current.Variables(0).Value()
        current_humidity = current.Variables(1).Value()
        current_wind_speed = current.Variables(2).Value()
        current_weather_code = current.Variables(3).Value()

        # Get daily data
        daily = response.Daily()
        daily_temp_max = daily.Variables(0).ValuesAsNumpy()[0]
        daily_temp_min = daily.Variables(1).ValuesAsNumpy()[0]

        # Weather code interpretation (simplified)
        weather_descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }

        weather_desc = weather_descriptions.get(int(current_weather_code), "Unknown")

        # Format the weather data
        formatted_weather = f"""
Weather Report for {city.title()}:
📍 Coordinates: {response.Latitude():.2f}°N {response.Longitude():.2f}°E
🏔️ Elevation: {response.Elevation()} m above sea level
🕐 Timezone: {response.Timezone()} ({response.TimezoneAbbreviation()})

Current Weather:
🌡️ Temperature: {current_temp:.1f}°C
🌤️ Conditions: {weather_desc}
💧 Humidity: {current_humidity:.0f}%
🌪️ Wind Speed: {current_wind_speed:.1f} km/h

Today's Forecast:
🌡️ Max Temperature: {daily_temp_max:.1f}°C
🌡️ Min Temperature: {daily_temp_min:.1f}°C

Data provided by Open-Meteo API
Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return formatted_weather

    except Exception as e:
        return f"Error fetching weather data: {str(e)}"


async def get_detailed_forecast(city: str, days: int = 3) -> str:
    """
    Get detailed forecast data for multiple days.

    Args:
        city: City name
        days: Number of days to forecast (1-7)

    Returns:
        str: Formatted forecast data
    """
    try:
        # Limit days to reasonable range
        days = max(1, min(days, 7))

        # Get coordinates for the city
        latitude, longitude = get_coordinates_for_city(city)

        # Get Open-Meteo client
        openmeteo = get_openmeteo_client()

        # API parameters for detailed forecast
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ["temperature_2m_max", "temperature_2m_min", "weather_code", "precipitation_sum",
                      "wind_speed_10m_max"],
            "timezone": "auto",
            "forecast_days": days
        }

        # Make API request
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        # Process daily data
        daily = response.Daily()
        daily_temp_max = daily.Variables(0).ValuesAsNumpy()
        daily_temp_min = daily.Variables(1).ValuesAsNumpy()
        daily_weather_code = daily.Variables(2).ValuesAsNumpy()
        daily_precipitation = daily.Variables(3).ValuesAsNumpy()
        daily_wind_speed = daily.Variables(4).ValuesAsNumpy()

        # Create date range
        daily_data = {"date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left"
        )}

        # Weather code interpretation
        weather_descriptions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
            55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }

        # Format forecast
        forecast_text = f"\n{days}-Day Weather Forecast for {city.title()}:\n"
        forecast_text += f"📍 Location: {response.Latitude():.2f}°N {response.Longitude():.2f}°E\n\n"

        for i in range(days):
            date = daily_data["date"][i].strftime('%A, %B %d')
            weather_desc = weather_descriptions.get(int(daily_weather_code[i]), "Unknown")

            forecast_text += f"📅 {date}:\n"
            forecast_text += f"   🌡️ High: {daily_temp_max[i]:.1f}°C | Low: {daily_temp_min[i]:.1f}°C\n"
            forecast_text += f"   🌤️ Conditions: {weather_desc}\n"
            forecast_text += f"   🌧️ Precipitation: {daily_precipitation[i]:.1f} mm\n"
            forecast_text += f"   💨 Max Wind: {daily_wind_speed[i]:.1f} km/h\n\n"

        return forecast_text

    except Exception as e:
        return f"Error fetching forecast data: {str(e)}"


# MCP Server Tool Definitions
@mcp.tool()
async def get_current_weather(city: str) -> str:
    """
    Get current weather information for a specified city using Open-Meteo API.

    Args:
        city: The name of the city to get weather for

    Returns:
        Formatted current weather information for the city
    """
    return await get_weather_data(city)


@mcp.tool()
async def get_weather_forecast(city: str, days: int = 3) -> str:
    """
    Get weather forecast for a specified city using Open-Meteo API.

    Args:
        city: The name of the city to get weather forecast for
        days: Number of days to forecast (1-7, default: 3)

    Returns:
        Formatted weather forecast information for the city
    """
    return await get_detailed_forecast(city, days)


def parse_weather_data(weather_text: str) -> dict:
    """Parse the formatted weather text back into a dictionary for display"""
    if "Error" in weather_text:
        return {"error": weather_text}

    # Simple parsing for display
    lines = weather_text.strip().split('\n')
    data = {}

    for line in lines:
        if "Temperature:" in line and "Current Weather" in weather_text:
            temp_part = line.split("Temperature: ")[1].split("°C")[0]
            data["temperature"] = f"{temp_part}°C"
        elif "Conditions:" in line:
            data["conditions"] = line.split("Conditions: ")[1]
        elif "Humidity:" in line:
            data["humidity"] = line.split("Humidity: ")[1]
        elif "Wind Speed:" in line:
            data["wind_speed"] = line.split("Wind Speed: ")[1]
        elif "Max Temperature:" in line:
            data["max_temp"] = line.split("Max Temperature: ")[1]
        elif "Min Temperature:" in line:
            data["min_temp"] = line.split("Min Temperature: ")[1]

    return data


def display_weather_data(weather_text: str):
    """Display weather data in Streamlit format"""
    parsed_data = parse_weather_data(weather_text)

    if "error" in parsed_data:
        st.error(parsed_data["error"])
        return

    # Display raw MCP server response
    with st.expander("📡 Raw MCP Server Response"):
        st.code(weather_text)

    # Display formatted data
    if parsed_data:
        col1, col2, col3 = st.columns(3)

        with col1:
            if "temperature" in parsed_data:
                st.metric("🌡️ Current Temperature", parsed_data["temperature"])

        with col2:
            if "humidity" in parsed_data:
                st.metric("💧 Humidity", parsed_data["humidity"])

        with col3:
            if "wind_speed" in parsed_data:
                st.metric("🌪️ Wind Speed", parsed_data["wind_speed"])

        if "conditions" in parsed_data:
            st.subheader(f"Current Conditions: {parsed_data['conditions']}")

        # Today's forecast
        if "max_temp" in parsed_data and "min_temp" in parsed_data:
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"🌡️ Today's High: {parsed_data['max_temp']}")
            with col2:
                st.info(f"🌡️ Today's Low: {parsed_data['min_temp']}")


# Streamlit Interface
st.sidebar.header("🔧 MCP Server Configuration")

# Show MCP server status
if 'mcp_server_running' not in st.session_state:
    st.session_state.mcp_server_running = True

server_status = "🟢 Running" if st.session_state.mcp_server_running else "🔴 Not Running"
st.sidebar.write(f"**MCP Server Status:** {server_status}")
st.sidebar.write("**API Used:** Open-Meteo (No API key required)")

# Show available cities
st.sidebar.subheader("📍 Available Cities")
available_cities = [
    "London", "New York", "Tokyo", "Paris", "Sydney", "Mumbai",
    "Berlin", "Moscow", "Beijing", "Los Angeles", "Chicago",
    "Toronto", "Rome", "Madrid", "Amsterdam", "Stockholm"
]
st.sidebar.write(", ".join(available_cities))

# Main interface
st.subheader("🌍 Test MCP Weather Tools")

# Create tabs for different tools
tab1, tab2 = st.tabs(["Current Weather", "Weather Forecast"])

with tab1:
    st.write("**MCP Tool:** `get_current_weather(city)`")

    # City input
    city = st.text_input(
        "Enter city name:",
        value="London",
        placeholder="e.g., London, New York, Tokyo",
        key="current_weather_city"
    )

    # Test current weather MCP tool
    if st.button("🔍 Get Current Weather", type="primary"):
        if city:
            with st.spinner(f"Calling MCP server for current weather in {city}..."):
                weather_result = asyncio.run(get_current_weather(city))
                st.subheader("MCP Tool Response:")
                display_weather_data(weather_result)
        else:
            st.warning("Please enter a city name")

    # Quick test cities
    st.subheader("🚀 Quick Current Weather Tests")
    sample_cities = ["London", "New York", "Tokyo", "Paris", "Sydney", "Mumbai"]

    cols = st.columns(3)
    for i, sample_city in enumerate(sample_cities):
        with cols[i % 3]:
            if st.button(f"📍 {sample_city}", key=f"current_{sample_city}"):
                with st.spinner(f"MCP server processing {sample_city}..."):
                    weather_result = asyncio.run(get_current_weather(sample_city))
                    st.subheader(f"Current Weather - {sample_city}:")
                    display_weather_data(weather_result)

with tab2:
    st.write("**MCP Tool:** `get_weather_forecast(city, days)`")

    col1, col2 = st.columns([2, 1])
    with col1:
        forecast_city = st.text_input(
            "Enter city name:",
            value="London",
            placeholder="e.g., London, New York, Tokyo",
            key="forecast_city"
        )
    with col2:
        forecast_days = st.selectbox(
            "Forecast days:",
            options=[1, 2, 3, 4, 5, 6, 7],
            index=2
        )

    # Test forecast MCP tool
    if st.button("📅 Get Weather Forecast", type="primary"):
        if forecast_city:
            with st.spinner(f"Calling MCP server for {forecast_days}-day forecast in {forecast_city}..."):
                forecast_result = asyncio.run(get_weather_forecast(forecast_city, forecast_days))
                st.subheader("MCP Tool Response:")
                with st.expander("📡 Raw MCP Server Response", expanded=True):
                    st.code(forecast_result)
        else:
            st.warning("Please enter a city name")

# Information about MCP server
st.markdown("---")
st.subheader("📡 About this MCP Server")
st.markdown("""
This application demonstrates an MCP (Model Context Protocol) server that provides weather data functionality using the **Open-Meteo API**:

### MCP Tools Available:
- **`get_current_weather(city)`** - Returns current weather conditions
- **`get_weather_forecast(city, days)`** - Returns multi-day weather forecast

### Features:
- **No API Key Required** - Open-Meteo provides free weather data
- **Cached Requests** - Responses are cached for 1 hour to improve performance
- **Retry Logic** - Automatic retry on failed requests
- **Multiple Cities** - Support for major cities worldwide
- **Detailed Data** - Temperature, humidity, wind speed, precipitation, and more

### Data Sources:
- **API**: Open-Meteo (https://open-meteo.com/)
- **Weather Models**: Various meteorological models
- **Update Frequency**: Hourly updates
- **Forecast Range**: Up to 7 days
""")

st.markdown("---")
st.markdown("Made with ❤️ using Streamlit and FastMCP | Weather data from [Open-Meteo](https://open-meteo.com)")
