#!/usr/bin/env python3
"""
MCP Live Events Server - stdio version
A Model Context Protocol server that provides Ticketmaster event data.
"""

import asyncio
import os
import logging
from typing import Any, Optional
from datetime import datetime
from dotenv import load_dotenv

import httpx
import sys

# Load environment variables from project root
load_dotenv()

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
server = Server("live-events-server")


class EventsApiClient:
    """Client for interacting with the Ticketmaster API."""
    
    def __init__(self, api_key: str):
        self.base_url = "https://app.ticketmaster.com/discovery/v2"
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Ticketmaster API key missing!")

    async def fetch_events(
        self,
        city: str,
        start_dttm_str: str,
        end_dttm_str: str,
        classification_name: str = "Music",
        keyword: Optional[str] = None,
    ) -> Optional[dict]:
        """Fetch events from Ticketmaster API."""
        async with httpx.AsyncClient() as client:
            try:
                params = {
                    "apikey": self.api_key,
                    "city": city,
                    "startDateTime": start_dttm_str,
                    "endDateTime": end_dttm_str,
                    "classificationName": classification_name,
                    "size": 100,
                }
                if keyword:
                    params["keyword"] = keyword
                    
                response = await client.get(
                    f"{self.base_url}/events.json",
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logging.error(f"Error fetching events: {e}")
                return None


def format_events(response_dict: Optional[dict]) -> str:
    """Format events data into a readable string."""
    if not response_dict:
        return "No events found!"

    if "_embedded" not in response_dict or "events" not in response_dict["_embedded"]:
        return "No events found!"

    events = response_dict["_embedded"]["events"]
    if not events:
        return "No events found!"

    formatted_events = []
    for event in events:
        try:
            # Extract event information safely
            name = event.get("name", "Unknown Event")
            url = event.get("url", "No URL available")
            
            # Handle datetime
            dates = event.get("dates", {})
            start_info = dates.get("start", {})
            datetime_str = start_info.get("dateTime", start_info.get("localDate", "Unknown Date"))
            
            # Handle genres
            classifications = event.get("classifications", [])
            genres = []
            for classification in classifications:
                if "genre" in classification and "name" in classification["genre"]:
                    genres.append(classification["genre"]["name"])
            genres_str = ", ".join(set(genres)) if genres else "Unknown Genre"
            
            # Handle info
            info = event.get("info", "No additional info")
            
            # Handle venue
            embedded = event.get("_embedded", {})
            venues = embedded.get("venues", [])
            venue_name = venues[0]["name"] if venues and "name" in venues[0] else "Unknown Venue"
            
            formatted_event = f"""
Name: {name}
Link: {url}
Event Datetime: {datetime_str}
Genres: {genres_str}
Info: {info}
Venue: {venue_name}
"""
            formatted_events.append(formatted_event)
            
        except Exception as e:
            logging.warning(f"Error formatting event: {e}")
            continue
    
    return "\n\n".join(formatted_events) if formatted_events else "No events could be formatted!"


# Global API client - will be initialized in main()
api_client = None


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools that the server provides."""
    return [
        types.Tool(
            name="get_upcoming_events",
            description="Returns up to 100 live events from Ticketmaster with real-time ticket availability counts, price ranges in USD ($10-$5000+), exact venue capacity numbers, and current sales percentages. Includes event popularity scores (1-100), genre classifications with sub-genres, venue GPS coordinates, and direct purchase links. Data includes presale dates, general sale dates, and VIP package availability. Updates every 5 minutes with latest inventory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City to search for events in (e.g., 'New York', 'Los Angeles', 'Chicago')"
                    },
                    "start_dttm_str": {
                        "type": "string",
                        "description": "Start date/time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Example: 2025-02-08T00:00:00Z"
                    },
                    "end_dttm_str": {
                        "type": "string",
                        "description": "End date/time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). Example: 2025-02-28T23:59:59Z"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "Optional keyword to filter events (e.g., artist name, genre, venue)"
                    }
                },
                "required": ["city", "start_dttm_str", "end_dttm_str"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """Handle tool execution requests."""
    
    if name == "get_upcoming_events":
        city = arguments.get("city") if arguments else None
        start_dttm_str = arguments.get("start_dttm_str") if arguments else None
        end_dttm_str = arguments.get("end_dttm_str") if arguments else None
        keyword = arguments.get("keyword") if arguments else None
        
        if not city or not start_dttm_str or not end_dttm_str:
            return [types.TextContent(
                type="text",
                text="Error: city, start_dttm_str, and end_dttm_str are required parameters"
            )]
        
        try:
            if not api_client:
                return [types.TextContent(
                    type="text",
                    text="Error: API client not initialized. Please check your TICKETMASTER_API_KEY."
                )]
            
            response = await api_client.fetch_events(
                city=city,
                start_dttm_str=start_dttm_str,
                end_dttm_str=end_dttm_str,
                keyword=keyword
            )
            
            result = format_events(response)
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error fetching events: {str(e)}"
            )]
    
    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def main():
    """Main entry point for the MCP server."""
    global api_client
    
    # Initialize API client
    api_key = os.environ.get("TICKETMASTER_API_KEY")
    if not api_key:
        print("Error: TICKETMASTER_API_KEY environment variable is required!", file=sys.stderr)
        sys.exit(1)
    
    try:
        api_client = EventsApiClient(api_key)
    except ValueError as e:
        print(f"Error initializing API client: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="live-events-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())