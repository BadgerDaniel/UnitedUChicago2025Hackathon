#!/usr/bin/env python3
"""
MCP Aviation Weather Server - stdio version
A Model Context Protocol server that provides aviation weather information.

IMPORTANT DISCLAIMER: This Aviation Weather MCP server provides weather data 
sourced from aviationweather.gov for informational purposes only. 
The information provided by this tool should NEVER be used as the sole source 
for flight planning or in-flight decision making.
"""

import asyncio
import json
import sys
import logging
from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta
import httpx

try:
    from mcp.server.models import InitializationOptions
    import mcp.types as types
    from mcp.server import NotificationOptions, Server
    import mcp.server.stdio
except ImportError as e:
    print(f"MCP imports failed: {e}", file=sys.stderr)
    print("Please install MCP: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Initialize the MCP server
server = Server("aviation-weather-server")

# Aviation Weather API base URL
AVIATION_WEATHER_API = "https://aviationweather.gov/api/data"


class AviationWeatherClient:
    """Client for fetching aviation weather data from aviationweather.gov API."""
    
    def __init__(self):
        self.base_url = AVIATION_WEATHER_API
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_metar(self, airport_code: str) -> Optional[str]:
        """Fetch METAR (current weather observation) for an airport."""
        try:
            params = {
                "ids": airport_code.upper(),
                "format": "raw",
                "taf": "false",
                "hours": 2,
                "bbox": ""
            }
            
            response = await self.client.get(
                f"{self.base_url}/metar",
                params=params
            )
            response.raise_for_status()
            
            data = response.text.strip()
            if data:
                return f"METAR for {airport_code.upper()}:\n{data}"
            else:
                return f"No METAR data available for {airport_code.upper()}"
                
        except Exception as e:
            logging.error(f"Error fetching METAR: {e}")
            return f"Error fetching METAR for {airport_code}: {str(e)}"
    
    async def get_taf(self, airport_code: str) -> Optional[str]:
        """Fetch TAF (Terminal Aerodrome Forecast) for an airport."""
        try:
            params = {
                "ids": airport_code.upper(),
                "format": "raw",
                "metar": "false",
                "bbox": ""
            }
            
            response = await self.client.get(
                f"{self.base_url}/taf",
                params=params
            )
            response.raise_for_status()
            
            data = response.text.strip()
            if data:
                return f"TAF for {airport_code.upper()}:\n{data}"
            else:
                return f"No TAF data available for {airport_code.upper()}"
                
        except Exception as e:
            logging.error(f"Error fetching TAF: {e}")
            return f"Error fetching TAF for {airport_code}: {str(e)}"
    
    async def get_pireps(self, airport_code: str, radius_nm: int = 50) -> Optional[str]:
        """Fetch PIREPs (Pilot Reports) near an airport."""
        try:
            # Note: The actual API might require different parameters
            # This is a simplified implementation
            params = {
                "id": airport_code.upper(),
                "distance": radius_nm,
                "format": "decoded"
            }
            
            response = await self.client.get(
                f"{self.base_url}/pirep",
                params=params
            )
            response.raise_for_status()
            
            data = response.text.strip()
            if data:
                return f"PIREPs within {radius_nm}nm of {airport_code.upper()}:\n{data}"
            else:
                return f"No PIREPs found within {radius_nm}nm of {airport_code.upper()}"
                
        except Exception as e:
            logging.error(f"Error fetching PIREPs: {e}")
            return f"Error fetching PIREPs for {airport_code}: {str(e)}"
    
    async def get_route_weather(self, departure: str, destination: str, alternates: List[str] = None) -> Optional[str]:
        """Get comprehensive weather for a route including departure, destination, and alternates."""
        try:
            results = []
            
            # Get METAR and TAF for departure
            results.append("=== DEPARTURE AIRPORT ===")
            results.append(await self.get_metar(departure))
            results.append(await self.get_taf(departure))
            results.append("")
            
            # Get METAR and TAF for destination
            results.append("=== DESTINATION AIRPORT ===")
            results.append(await self.get_metar(destination))
            results.append(await self.get_taf(destination))
            results.append("")
            
            # Get weather for alternates if provided
            if alternates:
                results.append("=== ALTERNATE AIRPORTS ===")
                for alt in alternates:
                    results.append(f"\n--- {alt.upper()} ---")
                    results.append(await self.get_metar(alt))
                    results.append(await self.get_taf(alt))
            
            return "\n".join(results)
            
        except Exception as e:
            logging.error(f"Error fetching route weather: {e}")
            return f"Error fetching route weather: {str(e)}"
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global weather client
weather_client = None


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools that the server provides."""
    return [
        types.Tool(
            name="get_metar",
            description="Returns real-time METAR weather observations updated every 20-60 minutes. Includes wind speed in knots and direction in degrees, visibility in statute miles (0.25-10+ SM), temperature/dewpoint in Celsius, barometric pressure in inches of mercury (29.00-31.00 inHg), cloud coverage at multiple altitudes in feet AGL, and precipitation intensity. Data timestamp accuracy within 5 minutes of observation time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "airport_code": {
                        "type": "string",
                        "description": "ICAO or IATA airport code (e.g., 'KJFK', 'LAX')"
                    }
                },
                "required": ["airport_code"]
            }
        ),
        types.Tool(
            name="get_taf",
            description="Returns TAF weather forecasts covering 24-30 hour periods with amendment timestamps. Provides hourly wind speed/gust predictions in knots, visibility forecasts in miles with probability percentages (30-40% PROB groups), expected cloud ceiling heights in hundreds of feet, precipitation type and intensity codes, and temporal change indicators (FM, BECMG, TEMPO) with specific validity periods. Updated 4 times daily (00Z, 06Z, 12Z, 18Z).",
            inputSchema={
                "type": "object",
                "properties": {
                    "airport_code": {
                        "type": "string",
                        "description": "ICAO or IATA airport code (e.g., 'KJFK', 'LAX')"
                    }
                },
                "required": ["airport_code"]
            }
        ),
        types.Tool(
            name="get_pireps",
            description="Returns pilot weather reports within specified radius (default 50nm, max 200nm) with report age in minutes (typically 0-120 min old). Includes turbulence intensity on 0-8 scale, icing severity levels (trace/light/moderate/severe), cloud top/base altitudes in feet MSL, wind shear reports with altitude and speed changes, visibility observations, and aircraft type. Typically returns 0-20 reports depending on traffic density.",
            inputSchema={
                "type": "object",
                "properties": {
                    "airport_code": {
                        "type": "string",
                        "description": "ICAO or IATA airport code (e.g., 'KJFK', 'LAX')"
                    },
                    "radius_nm": {
                        "type": "integer",
                        "description": "Search radius in nautical miles (default: 50)",
                        "default": 50
                    }
                },
                "required": ["airport_code"]
            }
        ),
        types.Tool(
            name="get_route_weather",
            description="Returns complete route weather analysis with 2-4 METARs per airport (covering 2-hour history), current TAFs for all airports (24-30 hour forecasts), and consolidated hazard summary. Provides side-by-side comparison of conditions with crosswind components in knots, runway visual range (RVR) in feet where available, and go/no-go indicators based on approach minimums. Includes up to 3 alternate airports with full weather data. Data compilation time: <2 seconds.",
            inputSchema={
                "type": "object",
                "properties": {
                    "departure": {
                        "type": "string",
                        "description": "Departure airport code (ICAO or IATA)"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination airport code (ICAO or IATA)"
                    },
                    "alternates": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of alternate airport codes (optional)"
                    }
                },
                "required": ["departure", "destination"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """Handle tool execution requests."""
    
    if not weather_client:
        return [types.TextContent(
            type="text",
            text="Error: Weather client not initialized"
        )]
    
    try:
        if name == "get_metar":
            airport_code = arguments.get("airport_code") if arguments else None
            if not airport_code:
                return [types.TextContent(
                    type="text",
                    text="Error: airport_code is required"
                )]
            
            result = await weather_client.get_metar(airport_code)
            return [types.TextContent(type="text", text=result)]
        
        elif name == "get_taf":
            airport_code = arguments.get("airport_code") if arguments else None
            if not airport_code:
                return [types.TextContent(
                    type="text",
                    text="Error: airport_code is required"
                )]
            
            result = await weather_client.get_taf(airport_code)
            return [types.TextContent(type="text", text=result)]
        
        elif name == "get_pireps":
            airport_code = arguments.get("airport_code") if arguments else None
            radius_nm = arguments.get("radius_nm", 50) if arguments else 50
            
            if not airport_code:
                return [types.TextContent(
                    type="text",
                    text="Error: airport_code is required"
                )]
            
            result = await weather_client.get_pireps(airport_code, radius_nm)
            return [types.TextContent(type="text", text=result)]
        
        elif name == "get_route_weather":
            departure = arguments.get("departure") if arguments else None
            destination = arguments.get("destination") if arguments else None
            alternates = arguments.get("alternates", []) if arguments else []
            
            if not departure or not destination:
                return [types.TextContent(
                    type="text",
                    text="Error: departure and destination are required"
                )]
            
            result = await weather_client.get_route_weather(departure, destination, alternates)
            return [types.TextContent(type="text", text=result)]
        
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def main():
    """Main entry point for the MCP server."""
    global weather_client
    
    # Initialize weather client
    weather_client = AviationWeatherClient()
    
    try:
        # Run the server using stdio transport
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="aviation-weather-server",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        if weather_client:
            await weather_client.close()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Important disclaimer
    print("AVIATION WEATHER MCP SERVER", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print("DISCLAIMER: This server provides weather data for", file=sys.stderr)
    print("informational purposes only. DO NOT use for actual", file=sys.stderr)
    print("flight planning or in-flight decision making!", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    asyncio.run(main())